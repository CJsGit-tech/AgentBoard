"""Revision-pinned design and proof references stored on ticket criteria."""
import re


def _proof_key(proof):
    return tuple(proof.get(field) for field in (
        "kind", "document_id", "revision", "section_line", "filename", "digest"
    ))


def report_heading_lines(content):
    inside_fence = False
    for index, line in enumerate(re.split(r"\r?\n", content)):
        if re.match(r"^\s*```", line):
            inside_fence = not inside_fence
        elif not inside_fence and re.match(r"^#{1,6}\s+\S", line):
            yield index


class Targets:
    """Resolve current targets in batches without reading attachment bytes."""

    def __init__(self, conn, project, designs, proofs):
        ids = list({ref["document_id"] for ref in [*designs, *proofs]})
        self.documents = {
            row["id"]: row for row in conn.execute("""
                SELECT id, revision, data->>'content' AS content FROM records
                WHERE id=ANY(%s) AND project=%s AND kind='documents' AND NOT deleted
            """, (ids, project))
        } if ids else {}
        design_ids = list({ref["document_id"] for ref in designs} & self.documents.keys())
        self.versions = {
            (row["document_id"], row["version"]) for row in conn.execute("""
                SELECT document_id, version FROM canvas_versions WHERE document_id=ANY(%s)
            """, (design_ids,))
        } if design_ids else set()
        screenshot_ids = list({ref["document_id"] for ref in proofs if ref["kind"] == "screenshot"}
                              & self.documents.keys())
        self.screenshots = {
            (row["document_id"], row["filename"]): row["digest"] for row in conn.execute("""
                SELECT document_id, filename, digest FROM visual_assets WHERE document_id=ANY(%s)
            """, (screenshot_ids,))
        } if screenshot_ids else {}

    def has_design(self, design):
        return (design["document_id"], design["version"]) in self.versions

    def has_proof(self, proof):
        document = self.documents.get(proof["document_id"])
        if not document:
            return False
        if proof["kind"] == "screenshot":
            return self.screenshots.get((proof["document_id"], proof["filename"])) == proof["digest"]
        line = proof.get("section_line")
        return document["revision"] == proof["revision"] and (
            line is None or line in report_heading_lines(document["content"] or "")
        )


def validate_references(conn, ticket, old):
    from .store import Problem

    previous = {criterion["id"]: criterion for criterion in old.get("criteria", [])}
    outputs = set(ticket.get("output_documents", []))
    designs = []
    proofs = []
    for criterion in ticket.get("criteria", []):
        earlier = previous.get(criterion["id"], {})
        design = criterion.get("design")
        if design and design != earlier.get("design"):
            designs.append(design)
        earlier_proofs = {_proof_key(proof): proof["status"] for proof in earlier.get("evidence", [])}
        for proof in criterion.get("evidence", []):
            status = proof["status"]
            prior_status = earlier_proofs.get(_proof_key(proof))
            if status == "superseded":
                if prior_status is None:
                    raise Problem(422, "Only previously recorded criterion evidence can be superseded.")
                continue
            if proof["document_id"] not in outputs:
                raise Problem(422, "Link active criterion evidence as a ticket Output document.")
            if prior_status == status or (prior_status == "verified" and status == "unverified"):
                continue  # Keep earlier pins readable if their target later becomes stale.
            proofs.append(proof)
    if not designs and not proofs:
        return

    targets = Targets(conn, ticket["project"], designs, proofs)
    if any(not targets.has_design(design) for design in designs):
        raise Problem(422, "Choose a published Canvas version from this project.")
    if any(not targets.has_proof(proof) for proof in proofs):
        raise Problem(422, "Choose an available ticket Output at its current revision, heading, or screenshot digest.")


def require_for_completion(conn, ticket):
    from .store import Problem

    required = [criterion for criterion in ticket.get("criteria", []) if criterion["evidence_required"]]
    if not required:
        return

    outputs = set(ticket.get("output_documents", []))
    verified = [
        [proof for proof in criterion["evidence"]
         if proof["status"] == "verified" and proof["document_id"] in outputs]
        for criterion in required
    ]
    targets = Targets(conn, ticket["project"], [], [proof for group in verified for proof in group])
    missing = [criterion["id"] for criterion, group in zip(required, verified)
               if not any(targets.has_proof(proof) for proof in group)]
    if missing:
        raise Problem(409, "Link current verified Output evidence before completing these criteria: " + ", ".join(missing) + ".")
