"""The standalone Canvas viewer needs publication metadata and linked delivery records."""
from psycopg.types.json import Jsonb

from .db import connect
from .models import MODELS
from .store import Problem
from .ticket_evidence import report_heading_lines


def viewer_state(key):
    with connect() as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        profile = conn.execute("""
            SELECT d.id, d.revision, d.project, d.data->>'name' AS name,
                   p.data->>'name' AS project_name, p.revision AS project_revision
              FROM records d JOIN records p ON p.id=d.project AND p.kind='projects' AND NOT p.deleted
             WHERE d.id=%s AND d.kind='documents' AND NOT d.deleted
        """, (key,)).fetchone()
        versions = conn.execute("""
            SELECT version, digest, asset_key, published_at, change_note, sources, publisher, screen_count
              FROM canvas_versions WHERE document_id=%s ORDER BY version DESC
        """, (key,)).fetchall() if profile else []
        if not versions:
            raise Problem(404, "This canvas is unavailable.")
        project = profile["project"]
        result = {kind: [] for kind in MODELS}
        result.update(trash=[], activity=[], reviews=[])
        result["projects"] = [{"id": project, "name": profile.pop("project_name"),
                               "revision": profile.pop("project_revision")}]
        profile["canvas_versions"] = versions
        result["documents"].append(profile)

        proof_ids, sections, filenames = set(), {}, set()
        for row in conn.execute("""
            SELECT id, revision, project, data->>'name' AS name, data->'criteria' AS criteria,
                   data->'documents' AS documents, data->'output_documents' AS output_documents,
                   data->>'description' AS description
              FROM records WHERE kind='tickets' AND NOT deleted AND project=%s
               AND (data->'criteria' @> %s OR
                    (data->'documents' ? %s AND strpos(data->>'description',%s)>0))
             ORDER BY created_at,id
        """, (project, Jsonb([{"design": {"document_id": key}}]), key, f"#canvas/{key}/")):
            designed = [c for c in row.pop("criteria") or [] if c.get("design")]
            if designed:
                # Explicit criteria override historical URLs in ticket descriptions.
                row.pop("description")
                row.pop("documents")
                row["criteria"] = [
                    {"design": c["design"], "evidence": [proof for proof in c.get("evidence", [])
                     if proof["status"] == "verified" and proof["document_id"] in (row["output_documents"] or [])]}
                    for c in designed if c["design"]["document_id"] == key
                ]
                if not row["criteria"]:
                    continue
                for criterion in row["criteria"]:
                    for proof in criterion["evidence"]:
                        proof_id = proof["document_id"]
                        proof_ids.add(proof_id)
                        if proof.get("section_line") is not None:
                            sections.setdefault(proof_id, set()).add(proof["section_line"])
                        if proof["kind"] == "screenshot":
                            filenames.add(proof["filename"])
            else:
                # Keep whole URL-containing words so the client can apply its exact local-link grammar.
                prefix = f"#canvas/{key}/"
                row["description"] = " ".join(word for word in (row["description"] or "").split() if prefix in word)
            result["tickets"].append(row)

        if proof_ids:
            for doc in conn.execute("""
                SELECT r.id, r.revision, r.project, r.data->>'name' AS name,
                       coalesce((SELECT a.at FROM activity a WHERE a.record=r.id
                           AND a.action IN ('Created','Updated') ORDER BY a.seq DESC LIMIT 1),
                           r.created_at) AS updated_at,
                       CASE WHEN r.id=ANY(%s) THEN r.data->>'content' END AS heading_content,
                       (SELECT jsonb_agg(jsonb_build_object('filename',v.filename,'digest',v.digest))
                          FROM visual_assets v WHERE v.document_id=r.id AND v.filename=ANY(%s)) AS previews
                  FROM records r WHERE r.kind='documents' AND NOT r.deleted AND r.project=%s AND r.id=ANY(%s)
            """, (list(sections), list(filenames), project, list(proof_ids))):
                content = doc.pop("heading_content") or ""
                doc["report_heading_lines"] = [line for line in report_heading_lines(content)
                                               if line in sections.get(doc["id"], ())]
                if doc["id"] == key:
                    profile.update(doc)
                else:
                    result["documents"].append(doc)
        return result
