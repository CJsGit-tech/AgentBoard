"""Docker-local MCP transport. Launch one standard-I/O process per client."""
import argparse
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from .visuals import attach
from .canvas import publish
from .db import connect
from .models import DocumentType, Kind, MODELS, WorkType
from .store import RECORDS_WITH_EDIT, Problem, activity_row, get_row, public, write
from . import reviews

PageSize = Annotated[int, Field(ge=1, le=200)]
Revision = Annotated[int, Field(ge=1)]


def build_server(actor: str):
    server = FastMCP("AgentBoard", instructions="List projects first. Use record_schema for writable fields. Updates save immediately with history. On feature/screen/document changes, query linked documents and check impact; on ticket changes, compare agreed scope. Read list_change_reviews and assess every snapshot document with evidence. These are agent checks, not a separate user workspace. All findings and decisions are logged in Runs & activity. Ask in chat only when agreed scope changes. Record an explicit user decision with its exact quote and conversation reference; never decide for the user. Check current inputs before editing or resuming. Editing runs need a linked reviewed ticket. Supply current revisions for writes.")

    @server.tool
    def record_schema(kind: Kind) -> dict:
        """Get the writable fields, required properties and allowed statuses for one record type."""
        return MODELS[kind].model_json_schema()

    @server.tool
    def list_records(kind: Kind, project: str | None = None, deleted: bool = False,
                     limit: PageSize = 50, offset: Annotated[int, Field(ge=0)] = 0,
                     document_type: DocumentType | None = None, work_type: WorkType | None = None,
                     tag: str | None = None) -> list[dict]:
        """List records. Filter documents or tickets by exact managed tag ID, document_type or work_type."""
        if (document_type is not None and kind != "documents") or (work_type is not None and kind != "tickets"):
            raise Problem(422, "Type filter does not match the record kind.")
        if tag is not None and kind not in ("tickets", "documents"):
            raise Problem(422, "Tags apply to tickets and documents.")
        with connect() as conn:
            rows = conn.execute(RECORDS_WITH_EDIT + """ WHERE kind=%s AND deleted=%s
                   AND (%s::text IS NULL OR project=%s)
                   AND (%s::text IS NULL OR COALESCE(data->>'document_type','unclassified')=%s)
                   AND (%s::text IS NULL OR COALESCE(data->>'work_type','UNCLASSIFIED')=%s)
                   AND (%s::text IS NULL OR (data->'tags') ? %s)
                   ORDER BY created_at,id LIMIT %s OFFSET %s""",
                   (kind, deleted, project, project, document_type, document_type,
                    work_type, work_type, tag, tag, limit, offset))
            return [public(r) for r in rows]

    @server.tool
    def get_record(kind: Kind, id: str, deleted: bool = False) -> dict:
        """Read a record including its revision."""
        with connect() as conn:
            return public(get_row(conn, kind, id, deleted))

    @server.tool
    def create_record(kind: Kind, fields: dict[str, Any], editor_role_id: str | None = None) -> dict:
        """Create a record. Use record_schema first. Every ticket needs a milestone in its project. Report a new external run with kind=runs."""
        return write(kind, "Created", actor, fields, editor_role_id=editor_role_id)

    @server.tool
    def update_record(kind: Kind, id: str, revision: Revision, changes: dict[str, Any],
                      editor_role_id: str | None = None) -> dict:
        """Apply field changes immediately. Use this tool to report a run's status, note or linked ticket."""
        return write(kind, "Updated", actor, changes, id, revision, editor_role_id)

    @server.tool
    def delete_record(kind: Kind, id: str, revision: Revision) -> dict:
        """Move an unreferenced record to trash."""
        return write(kind, "Deleted", actor, key=id, revision=revision)

    @server.tool
    def restore_record(kind: Kind, id: str, revision: Revision) -> dict:
        """Restore a deleted record. Restore its dependencies first."""
        return write(kind, "Restored", actor, key=id, revision=revision)

    @server.tool
    def attach_visual(document_id: str, revision: Revision, filename: str, png_base64: str) -> dict:
        """Attach a PNG preview to a screen inventory and return the updated inventory."""
        return attach(actor, document_id, revision, filename, png_base64)

    @server.tool
    def publish_canvas(document_id: str, revision: Revision, files: dict[str, str],
                       change_note: str, sources: list[dict[str, Any]],
                       screen_count: Annotated[int, Field(strict=True, gt=0, le=2147483647)] | None = None) -> dict:
        """Publish reviewed HTML on a Design Profile with source revisions and an optional verified screen count."""
        return publish(actor, document_id, revision, files, change_note, sources, screen_count)

    @server.tool
    def list_change_reviews(project: str | None = None, subject: str | None = None,
                            limit: PageSize = 50, offset: Annotated[int, Field(ge=0)] = 0) -> list[dict]:
        """Read impact/scope reviews and immutable input snapshots, including superseded history. Page all results."""
        with connect() as conn:
            return reviews.list_reviews(conn, project, subject, limit, offset)

    @server.tool
    def start_change_review(kind: Kind, id: str, revision: Revision, request: str,
                            operation: str = 'Edit') -> dict:
        """Record a change request before drafting. Reuse automatically generated current reviews when sufficient."""
        return reviews.start(actor, kind, id, revision, request, operation)

    @server.tool
    def assess_change_review(id: str, revision: Revision, assessment: reviews.Assessment) -> dict:
        """Check linked document impact and scope; log one evidence-backed finding per document in Runs & activity. Ask scope-change questions in chat."""
        return reviews.submit(actor, id, revision, assessment.model_dump())

    @server.tool
    def record_user_scope_decision(id: str, revision: Revision, accept: Annotated[bool, Field(strict=True)],
                                   user_quote: Annotated[str, Field(min_length=1, max_length=6000)],
                                   conversation_reference: Annotated[str, Field(min_length=1, max_length=1000)]) -> dict:
        """Record the user's explicit decision on the exact proposed scope after asking in chat. Supply their exact words and conversation reference. Never infer consent or decide for them. This logs the user decision as recorded by this client, not as a direct Human action."""
        if not user_quote.strip() or not conversation_reference.strip():
            raise Problem(422, "Supply the user's exact decision and its conversation reference.")
        return reviews.confirm(id, revision, accept,
            'User decision: ' + user_quote.strip() + '\nConversation: ' + conversation_reference.strip(), recorder=actor)

    @server.tool
    def list_activity(project: str | None = None, record: str | None = None,
                      limit: PageSize = 50, before: int | None = None) -> list[dict]:
        """Read latest changes first, with actor, time and field differences. Use the last event ID for before."""
        with connect() as conn:
            rows = conn.execute("""SELECT * FROM activity WHERE (%s::text IS NULL OR project=%s)
                     AND (%s::text IS NULL OR record=%s) AND (%s::bigint IS NULL OR seq<%s)
                     ORDER BY seq DESC LIMIT %s""",(project,project,record,record,before,before,limit))
            return [activity_row(r) for r in rows]

    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", choices=["Codex","Claude"], required=True)
    build_server(parser.parse_args().client).run(transport="stdio")
