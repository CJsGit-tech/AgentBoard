import os
from uuid import uuid4

from psycopg.types.json import Jsonb
from pydantic import ValidationError

from .catalog import check_catalog, core_name
from .db import connect
from .models import MODELS, PREFIX, timestamp
from . import reviews, ticket_evidence


class Problem(ValueError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def record_data(row):
    defaults = {"checkout_path": ""} if row["kind"] == "projects" else {}
    if row["kind"] == "documents":
        defaults = {"document_type": "unclassified", "description": "", "source_documents": []}
    elif row["kind"] == "tickets":
        defaults = {"work_type": "UNCLASSIFIED", "execution_role": "", "output_documents": [], "criteria": []}
    if row["kind"] in ("tickets", "documents"):
        defaults["tags"] = []
    if row["kind"] == "runs":
        defaults["mode"] = "Edit"
    return {**defaults, **row["data"]}


RECORDS_WITH_EDIT = """
    SELECT records.*, (SELECT id::text FROM assistant_runs ar WHERE ar.board_run_id=records.id) AS assistant_run_id, (SELECT jsonb_agg(jsonb_build_object('filename', a.filename, 'digest', a.digest)
                            ORDER BY a.filename) FROM visual_assets a WHERE a.document_id=records.id) AS previews,
           (SELECT jsonb_agg(jsonb_build_object('version', v.version, 'digest', v.digest,
                     'asset_key', v.asset_key, 'published_at', v.published_at,
                     'change_note', v.change_note, 'sources', v.sources, 'publisher', v.publisher,
                     'screen_count', v.screen_count) ORDER BY v.version DESC)
            FROM canvas_versions v WHERE v.document_id=records.id) AS canvas_versions,
           edit.at AS updated_at, edit.actor AS latest_editor,
           edit.editor_role AS latest_edit_role
    FROM records LEFT JOIN LATERAL (
        SELECT at, actor, editor_role FROM activity
        WHERE record=records.id AND action IN ('Created', 'Updated')
        ORDER BY seq DESC LIMIT 1
    ) edit ON records.kind IN ('tickets', 'documents')
"""


def public(row):
    result = {**record_data(row), "id": row["id"], "revision": row["revision"],
              "record_path": f"/#{row['kind']}/{row['id']}"}
    board_origin = os.environ.get("AGENTBOARD_UI_ORIGIN")
    if board_origin:
        result["record_url"] = board_origin + result["record_path"]
    if row["kind"] in ("tickets", "documents"):
        result.update(created_at=row["created_at"].isoformat(),
                      updated_at=(row["updated_at"] or row["created_at"]).isoformat(),
                      latest_editor=row["latest_editor"],
                      latest_edit_role=row["latest_edit_role"])
    if row["kind"] == "runs" and row.get("assistant_run_id"):
        result["assistant_run_id"] = row["assistant_run_id"]
    if row["kind"] == "documents":
        if row["canvas_versions"]:
            result["canvas_versions"] = row["canvas_versions"]
        result["previews"] = row["previews"] or []
    return result


def get_row(conn, kind, key, deleted=False):
    row = conn.execute(RECORDS_WITH_EDIT + " WHERE id=%s AND kind=%s AND deleted=%s",
                       (key, kind, deleted)).fetchone()
    if not row:
        raise Problem(404, f"Could not find {kind} record {key}.")
    return row


def activity_row(row):
    return dict(id=str(row["seq"]), time=row["at"].isoformat(),
                **{k: row[k] for k in ("project","actor","action","kind","record","name","changes","editor_role")})


def state(previous_etag=None):
    with connect() as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        sequence = conn.execute("SELECT COALESCE(MAX(seq),0) AS n FROM activity").fetchone()["n"]
        purge_version = conn.execute("SELECT version FROM workspace_purge_version").fetchone()["version"]
        etag = f'"workspace-v6-{sequence}-{purge_version}"'
        if previous_etag == etag:
            return etag, None
        result = {k: [] for k in MODELS}
        result["trash"] = []
        for r in conn.execute(RECORDS_WITH_EDIT + " ORDER BY created_at,id"):
            if r["deleted"]:
                result["trash"].append({"k":r["kind"],"r":public(r)})
            else:
                result[r["kind"]].append(public(r))
        result["activity"] = [activity_row(r) for r in conn.execute("SELECT * FROM activity ORDER BY seq DESC")]
        result["reviews"] = reviews.list_reviews(conn)
        return etag, result


def project_activity_version(conn, key):
    return conn.execute(
        "SELECT COALESCE(MAX(seq),0)::text AS version FROM activity WHERE project=%s",
        (key,),
    ).fetchone()["version"]


def project_deletion_preview(key):
    with connect() as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        project = get_row(conn, "projects", key)
        counts = conn.execute(
            "SELECT kind, COUNT(*) AS total FROM records WHERE project=%s AND kind<>'projects' GROUP BY kind",
            (key,),
        )
        previews = conn.execute("""
            SELECT COUNT(*) AS total FROM visual_assets a
            JOIN records r ON r.id=a.document_id WHERE r.project=%s
        """, (key,)).fetchone()["total"]
        return {
            "name": project["data"]["name"],
            "revision": project["revision"],
            "activity_version": project_activity_version(conn, key),
            "counts": {row["kind"]: row["total"] for row in counts},
            "previews": previews,
        }


def purge_project(key, revision, confirmation, activity_version):
    with connect() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(625016)")
        project = get_row(conn, "projects", key)
        if project["revision"] != revision or project_activity_version(conn, key) != activity_version:
            raise Problem(409, "This project changed. Review the latest contents before deleting it.")
        if conn.execute("SELECT 1 FROM assistant_runs WHERE project=%s AND status IN ('Queued','Running') LIMIT 1", (key,)).fetchone():
            raise Problem(409, "Stop active Assistant runs before deleting this project.")
        if confirmation != project["data"]["name"]:
            raise Problem(422, "Enter the exact project name to confirm deletion.")
        conn.execute("""
            DELETE FROM visual_assets a USING records r
            WHERE a.document_id=r.id AND r.project=%s
        """, (key,))
        conn.execute("DELETE FROM records WHERE project=%s", (key,))
        conn.execute("DELETE FROM activity WHERE project=%s", (key,))
        conn.execute("UPDATE workspace_purge_version SET version=version+1")


def check_links(conn, kind, data):
    if kind == "projects":
        return
    project = data["project"]
    get_row(conn, "projects", project)
    links = [("milestones", data.get("milestone")), ("roles", data.get("role")), ("tickets", data.get("ticket"))]
    for field in ("documents", "output_documents", "source_documents"):
        links.extend(("documents", key) for key in data.get(field, []))
    for target, key in links:
        if key and get_row(conn, target, key)["project"] != project:
            raise Problem(422, "Linked records must belong to the same project.")
    if kind == "documents":
        # Reject cycles, including indirect cycles, before persisting a dependency.
        rows = conn.execute("SELECT id,data FROM records WHERE kind='documents' AND project=%s AND NOT deleted", (project,)).fetchall()
        graph = {r['id']: r['data'].get('source_documents', []) for r in rows}
        graph[data.get('_id', '')] = data.get('source_documents', [])
        visited = set()
        def visit(key, path):
            if key in path:
                raise Problem(422, "Document source links cannot form a cycle.")
            if key in visited:
                return
            for source in graph.get(key, []):
                visit(source, path | {key})
            visited.add(key)
        if data.get('_id'):
            visit(data['_id'], set())


def check_unused(conn, row):
    key = row["id"]
    if row["kind"] == "documents" and core_name(row["data"]) == "Tag Catalog":
        check_catalog_in_use(conn, row["project"])
    dependent = conn.execute("""
      SELECT kind, id FROM records WHERE NOT deleted AND id <> %s
      AND (project=%s OR data->>'milestone'=%s OR data->>'role'=%s
           OR data->>'ticket'=%s OR (data->'documents') ? %s
           OR (data->'output_documents') ? %s OR (data->'source_documents') ? %s
           OR EXISTS (
               SELECT 1 FROM jsonb_array_elements(COALESCE(data->'criteria', '[]'::jsonb)) criterion
               WHERE criterion->'design'->>'document_id'=%s
           )) LIMIT 1
    """, (key,)*9).fetchone()
    if dependent:
        raise Problem(409, f"Remove the link from {dependent['kind']} {dependent['id']} first.")


def write(kind, action, actor, data=None, key=None, revision=None, editor_role_id=None):
    with connect() as conn:
        # Cross-record links and soft deletes must be checked against one consistent writer.
        conn.execute("SELECT pg_advisory_xact_lock(625016)")
        return mutate(conn, kind, action, actor, data, key, revision, editor_role_id)


def mutate(conn, kind, action, actor, data=None, key=None, revision=None, editor_role_id=None, *, historical_import=False):
    # Only the packaged, empty-workspace sample importer uses this internal path.
    # HTTP/MCP write() never accepts the flag. Imported history is reviewed after loading.
    if historical_import and action != 'Created':
        raise Problem(422, 'Historical fixtures can only be imported into new records.')
    old = {}
    if action == "Created":
        key = f"{PREFIX[kind]}-{uuid4().hex[:12]}"
    else:
        row = get_row(conn, kind, key, action == "Restored")
        if row["revision"] != revision:
            raise Problem(409, "This record changed. Reload its latest revision and try again.")
        old = record_data(row)
        if kind == 'runs' and row.get('assistant_run_id') and actor != 'InApp Assistant':
            raise Problem(409, 'Use InApp Assistant run details to cancel, continue or restore this managed run.')
    if action in ("Deleted", "Restored"):
        if action == "Deleted":
            check_unused(conn, row)
            if kind == "documents" and (reviews.current(conn, key) or reviews.tracked(row, set())):
                reviews.require_ready(conn, key, deletion=True)
        else:
            check_links(conn, kind, old)
            validate_catalog(conn, kind, old, {"name": "", "tags": old.get("tags", [])}, key)
        saved = conn.execute("UPDATE records SET deleted=%s,revision=revision+1 WHERE id=%s RETURNING *",
                             (action=="Deleted",key)).fetchone()
        changes = [["deleted", action=="Restored", action=="Deleted"]]
    else:
        merged = {k:v for k,v in old.items() if k != "updated"}
        if old and "project" in data and data["project"] != old.get("project"):
            raise Problem(422, "The project of an existing record cannot be changed.")
        merged.update(data)
        try:
            clean = MODELS[kind].model_validate(merged).model_dump()
        except ValidationError as err:
            raise Problem(422, "; ".join(f"{'.'.join(map(str,e['loc']))}: {e['msg']}" for e in err.errors())) from err
        if kind == "documents" and old and core_name(old) == "Tag Catalog" and core_name(clean) != "Tag Catalog":
            check_catalog_in_use(conn, clean["project"])
        check_links(conn, kind, {**clean, '_id': key})
        if kind == "tickets":
            ticket_evidence.validate_references(conn, clean, old)
        validate_catalog(conn, kind, clean, old, key)
        if kind == "runs":
            clean["updated"] = timestamp()
        changes = [[k,old.get(k),v] for k,v in clean.items() if v != old.get(k)]
        if not changes:
            return public(row)
        if action == "Created":
            saved = conn.execute("INSERT INTO records(id,kind,project,data) VALUES (%s,%s,%s,%s) RETURNING *",
                                 (key, kind, clean.get("project", key), Jsonb(clean))).fetchone()
        else:
            saved = conn.execute("UPDATE records SET data=%s,revision=revision+1 WHERE id=%s RETURNING *",
                                 (Jsonb(clean),key)).fetchone()
    editor_role = None
    if editor_role_id is not None:
        if kind not in ("tickets", "documents") or action not in ("Created", "Updated"):
            raise Problem(422, "An editor role can be recorded for ticket and document edits only.")
        role = get_row(conn, "roles", editor_role_id)
        if role["project"] != saved["project"]:
            raise Problem(422, "The editor role must belong to this project.")
        editor_role = role["data"]["name"]
    conn.execute("""INSERT INTO activity(project,actor,action,kind,record,name,changes,editor_role)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                 (saved["project"], actor, action, kind, key, saved["data"]["name"], Jsonb(changes), editor_role))
    if not historical_import and kind in ('documents', 'tickets'):
        if kind == 'documents' and action == 'Restored' and (reviews.current(conn, key) or {}).get('operation') == 'Delete':
            value, signature = reviews.snapshot(conn, saved)
            reviews.new_review(conn, saved, value, signature, actor, 'Review the restored requirements and their document impact.')
        reviews.sync_record_change(conn, saved, old, action, actor)
    if not historical_import and action in ('Created', 'Updated', 'Restored'):
        if kind == 'tickets' and saved['data']['status'] in ('In progress', 'Done') and (
                old.get('status') != saved['data']['status'] or reviews.fields(kind, old) != reviews.fields(kind, saved['data'])):
            reviews.require_ready(conn, key)
            if saved['data']['status'] == 'Done':
                ticket_evidence.require_for_completion(conn, saved['data'])
        if kind == 'runs' and saved['data'].get('mode', 'Edit') == 'Edit' and saved['data']['status'] in ('Running', 'Completed') and (
                action != 'Updated' or any(old.get(field) != saved['data'].get(field) for field in ('status', 'ticket', 'mode'))):
            ticket = saved['data'].get('ticket')
            if not ticket:
                raise Problem(422, 'Editing runs need a linked ticket. Use Read only for questions and inspection.')
            reviews.require_ready(conn, ticket)
            if saved['data']['status'] == 'Completed':
                ticket_evidence.require_for_completion(conn, get_row(conn, 'tickets', ticket)['data'])
    return public(get_row(conn, kind, key, action == "Deleted"))


def validate_catalog(conn, kind, data, old, key):
    try:
        check_catalog(conn, kind, data, old, key)
    except ValueError as err:
        raise Problem(422, str(err)) from err


def check_catalog_in_use(conn, project):
    assigned = conn.execute("""SELECT id FROM records WHERE project=%s AND NOT deleted
                               AND jsonb_array_length(COALESCE(data->'tags','[]'::jsonb)) > 0 LIMIT 1""",
                            (project,)).fetchone()
    if assigned:
        raise Problem(409, f"Project tags are still assigned on {assigned['id']}.")
