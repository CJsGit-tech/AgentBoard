from difflib import unified_diff
import re
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Header, Query, Response
from sqlalchemy import ARRAY, String, cast, func, select
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.api.routes import _page
from app.artifacts import service
from app.artifacts.contracts import validate
from app.artifacts.models import Document, DocumentVersion, Ticket, TicketDocument
from app.db.models import utcnow
from app.db.session import get_db
from app.mcp.models import MutationRequest

router = APIRouter(prefix="/api/v1/projects/{project_id}")
Db = Annotated[Session, Depends(get_db)]
Key = Annotated[str, Header(alias="Idempotency-Key")]
Limit = Annotated[int, Query(ge=1, le=100)]
Tags = Annotated[list[str] | None, Query()]


def pending_requests(project_id: UUID):
    return select(MutationRequest).where(
        MutationRequest.project_id == project_id, MutationRequest.status == "pending",
        MutationRequest.expires_at > utcnow(),
    )


def ticket_view(row: Ticket, pending: set[UUID]) -> dict:
    return {**service.serialize(row), "needs_approval": row.id in pending}


def pending_ticket_ids(db: Session, project_id: UUID) -> set[UUID]:
    statement = pending_requests(project_id).with_only_columns(MutationRequest.ticket_id)
    return set(db.scalars(statement.where(MutationRequest.ticket_id.is_not(None))))


def filter_tags(db, project_id, statement, model, features, concerns):
    for tags, prefix in ((features, "feature:"), (concerns, "concern:")):
        if tags:
            pattern = rf"{prefix}[a-z0-9]+(?:-[a-z0-9]+)*"
            if len(tags) > 30 or len(set(tags)) != len(tags) or any(not re.fullmatch(pattern, tag) for tag in tags):
                raise ApiError(422, "invalid_tags", f"Expected up to 30 unique {prefix} tags")
            statement = statement.where(model.fields["tags"].has_any(
                cast(tags, ARRAY(String))
            ))
    service.ensure_tags(db, project_id, {"tags": [*(features or []), *(concerns or [])]})
    return statement


def page(db, model, statement, limit, cursor, serialize):
    result = _page(db, statement, limit, cursor, model)
    return {"items": [serialize(row) for row in result["items"]], "next_cursor": result["next_cursor"]}


@router.get("/tickets")
def list_tickets(
    project_id: UUID, db: Db, limit: Limit = 50, cursor: str | None = None,
    feature_tags: Tags = None, concern_tags: Tags = None, status: Literal["planned", "in_progress", "blocked", "done"] | None = None,
    priority: Literal["high", "normal", "low"] | None = None,
    owner_kind: Literal["unassigned", "builder", "role"] | None = None,
):
    service.project(db, project_id)
    statement = select(Ticket).where(Ticket.project_id == project_id)
    for field, value in (("status", status), ("priority", priority), ("owner_kind", owner_kind)):
        if value:
            statement = statement.where(Ticket.fields[field].astext == value)
    pending = pending_ticket_ids(db, project_id)
    return page(db, Ticket, filter_tags(db, project_id, statement, Ticket, feature_tags, concern_tags),
                limit, cursor, lambda row: ticket_view(row, pending))


@router.post("/tickets", status_code=201)
def create_ticket(project_id: UUID, db: Db, key: Key, body: dict = Body()):
    validate("TicketCreate", body)
    return {**service.create(db, Ticket, project_id, body, key), "needs_approval": False}


@router.get("/tickets/{ticket_id}")
def get_ticket(project_id: UUID, ticket_id: UUID, db: Db):
    return ticket_view(service.artifact(db, Ticket, project_id, ticket_id), pending_ticket_ids(db, project_id))


@router.patch("/tickets/{ticket_id}")
def update_ticket(project_id: UUID, ticket_id: UUID, db: Db, body: dict = Body()):
    validate("TicketUpdate", body)
    service.project(db, project_id, lock=True)
    row = service.artifact(db, Ticket, project_id, ticket_id)
    service.revision(row, body["expected_revision"])
    result = service.update(db, row, body["changes"])
    return {**result, "needs_approval": row.id in pending_ticket_ids(db, project_id)}


def delete_record(db, model, project_id, record_id, expected_revision):
    service.project(db, project_id, lock=True)
    row = service.artifact(db, model, project_id, record_id)
    service.revision(row, expected_revision)
    kind = model.__name__.lower()
    service.invalidate_pending(db, project_id, kind, row.id)
    service.audit(db, project_id, "delete", kind, row.id)
    db.delete(row)
    db.commit()
    return Response(status_code=204)


@router.delete("/tickets/{ticket_id}", status_code=204)
def delete_ticket(project_id: UUID, ticket_id: UUID, db: Db, expected_revision: Annotated[int, Query(ge=1)]):
    return delete_record(db, Ticket, project_id, ticket_id, expected_revision)


@router.get("/documents")
def list_documents(
    project_id: UUID, db: Db, limit: Limit = 50, cursor: str | None = None,
    feature_tags: Tags = None, concern_tags: Tags = None,
):
    service.project(db, project_id)
    statement = select(Document).where(Document.project_id == project_id)
    return page(db, Document, filter_tags(db, project_id, statement, Document, feature_tags, concern_tags),
                limit, cursor, service.serialize)


@router.post("/documents", status_code=201)
def create_document(project_id: UUID, db: Db, key: Key, body: dict = Body()):
    validate("DocumentCreate", body)
    return service.create(db, Document, project_id, body, key)


@router.get("/documents/{document_id}")
def get_document(project_id: UUID, document_id: UUID, db: Db):
    return service.serialize(service.artifact(db, Document, project_id, document_id))


@router.patch("/documents/{document_id}")
def update_document(project_id: UUID, document_id: UUID, db: Db, body: dict = Body()):
    validate("DocumentUpdate", body)
    service.project(db, project_id, lock=True)
    row = service.artifact(db, Document, project_id, document_id)
    service.revision(row, body["expected_revision"])
    return service.update(db, row, body["changes"])


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(project_id: UUID, document_id: UUID, db: Db, expected_revision: Annotated[int, Query(ge=1)]):
    return delete_record(db, Document, project_id, document_id, expected_revision)


def serialize_version(row: DocumentVersion) -> dict:
    fields = {key: val for key, val in row.fields.items() if key != "title"}
    return {**fields, "id": str(row.id), "project_id": str(row.project_id),
            "document_id": str(row.document_id), "version": row.version,
            "author_client_id": str(row.author_client_id) if row.author_client_id else None,
            "source": row.source, "created_at": service.timestamp(row.created_at)}


def get_version(db: Session, project_id: UUID, document_id: UUID, version_id: UUID) -> DocumentVersion:
    row = db.scalar(select(DocumentVersion).where(
        DocumentVersion.project_id == project_id, DocumentVersion.document_id == document_id,
        DocumentVersion.id == version_id,
    ))
    if row is None:
        raise ApiError(404, "not_found", "Document revision is unavailable")
    return row


@router.get("/documents/{document_id}/versions")
def list_versions(project_id: UUID, document_id: UUID, db: Db, limit: Limit = 50, cursor: str | None = None):
    service.artifact(db, Document, project_id, document_id)
    statement = select(DocumentVersion).where(
        DocumentVersion.project_id == project_id, DocumentVersion.document_id == document_id
    ).order_by(DocumentVersion.version.desc())
    if cursor:
        try:
            before = int(cursor)
        except ValueError as exc:
            raise ApiError(422, "invalid_cursor", "Invalid document revision cursor") from exc
        statement = statement.where(DocumentVersion.version < before)
    rows = list(db.scalars(statement.limit(limit + 1)))
    return {"items": [serialize_version(row) for row in rows[:limit]],
            "next_cursor": str(rows[limit - 1].version) if len(rows) > limit else None}


@router.get("/documents/{document_id}/versions/compare")
def compare_versions(project_id: UUID, document_id: UUID, from_version_id: UUID, to_version_id: UUID, db: Db):
    old = get_version(db, project_id, document_id, from_version_id)
    new = get_version(db, project_id, document_id, to_version_id)
    diff = unified_diff(old.fields["content"].splitlines(), new.fields["content"].splitlines(),
                        fromfile=f"v{old.version}", tofile=f"v{new.version}", lineterm="")
    return {"document_id": str(document_id), "from_version_id": str(old.id), "to_version_id": str(new.id),
            "unified_diff": "\n".join(diff)}


@router.get("/documents/{document_id}/versions/{version_id}")
def read_version(project_id: UUID, document_id: UUID, version_id: UUID, db: Db):
    return serialize_version(get_version(db, project_id, document_id, version_id))


@router.post("/documents/{document_id}/versions/restore")
def restore_version(project_id: UUID, document_id: UUID, db: Db, body: dict = Body()):
    validate("Restore", body)
    service.project(db, project_id, lock=True)
    row = service.artifact(db, Document, project_id, document_id)
    service.revision(row, body["expected_revision"])
    version = get_version(db, project_id, document_id, UUID(body["version_id"]))
    return service.update(db, row, version.fields)


def serialize_link(row):
    return {"project_id": str(row.project_id), "ticket_id": str(row.ticket_id),
            "document_id": str(row.document_id), "relationship": row.relationship,
            "created_at": service.timestamp(row.created_at)}


@router.get("/tickets/{ticket_id}/documents")
def list_links(project_id: UUID, ticket_id: UUID, db: Db, limit: Limit = 50, cursor: str | None = None):
    service.artifact(db, Ticket, project_id, ticket_id)
    statement = select(TicketDocument).where(
        TicketDocument.project_id == project_id, TicketDocument.ticket_id == ticket_id)
    if cursor:
        try:
            document_id, relationship = cursor.split("_")
            document_id = UUID(document_id)
        except ValueError as exc:
            raise ApiError(422, "invalid_cursor", "Invalid document link cursor") from exc
        statement = statement.where((TicketDocument.document_id > document_id) | (
            (TicketDocument.document_id == document_id) & (TicketDocument.relationship > relationship)))
    rows = list(db.scalars(statement.order_by(TicketDocument.document_id, TicketDocument.relationship).limit(limit + 1)))
    last = rows[limit - 1] if len(rows) > limit else None
    return {"items": [serialize_link(row) for row in rows[:limit]],
            "next_cursor": f"{last.document_id}_{last.relationship}" if last else None}


@router.post("/tickets/{ticket_id}/documents", status_code=201)
def create_link(project_id: UUID, ticket_id: UUID, db: Db, key: Key, body: dict = Body()):
    validate("LinkCreate", body)
    service.project(db, project_id, lock=True)
    ticket = service.artifact(db, Ticket, project_id, ticket_id)
    document_id = UUID(body["document_id"])
    service.artifact(db, Document, project_id, document_id)
    scope = f"browser:link:{ticket_id}"
    saved, digest = service.replay(db, project_id, scope, key, body)
    if saved is not None:
        return saved
    relationship = body["relationship"]
    row = db.get(TicketDocument, (project_id, ticket_id, document_id, relationship))
    if row is None:
        row = TicketDocument(project_id=project_id, ticket_id=ticket_id,
                             document_id=document_id, relationship=relationship)
        db.add(row)
        ticket.revision += 1
        ticket.updated_at = utcnow()
        db.flush()
        service.invalidate_pending(db, project_id, "ticket", ticket_id)
        service.audit(db, project_id, "link", "ticket", ticket_id)
    result = serialize_link(row)
    service.save_result(db, project_id, scope, key, digest, result)
    db.commit()
    return result


@router.delete("/tickets/{ticket_id}/documents/{document_id}/{relationship}", status_code=204)
def delete_link(project_id: UUID, ticket_id: UUID, document_id: UUID, relationship: Literal["context", "output"],
                db: Db, expected_revision: Annotated[int, Query(ge=1)]):
    service.project(db, project_id, lock=True)
    ticket = service.artifact(db, Ticket, project_id, ticket_id)
    service.revision(ticket, expected_revision)
    link = db.get(TicketDocument, (project_id, ticket_id, document_id, relationship))
    if link is None:
        raise ApiError(404, "not_found", "Document link not found")
    db.delete(link)
    ticket.revision += 1
    ticket.updated_at = utcnow()
    service.invalidate_pending(db, project_id, "ticket", ticket_id)
    service.audit(db, project_id, "unlink", "ticket", ticket_id)
    db.commit()
    return Response(status_code=204)


@router.get("/progress")
def progress(project_id: UUID, db: Db):
    service.project(db, project_id)
    status = Ticket.fields["status"].astext
    counts = dict.fromkeys(("planned", "in_progress", "blocked", "done"), 0)
    counts.update(dict(db.execute(select(status, func.count()).where(Ticket.project_id == project_id)
                               .group_by(status)).all()))
    total = sum(counts.values())
    pending = db.scalar(select(func.count()).select_from(pending_requests(project_id).subquery()))
    return {"project_id": str(project_id), "counts": counts, "total": total,
            "pending_approval_count": pending, "has_tasks": total > 0}


@router.get("/tags")
def list_tags(project_id: UUID, db: Db):
    service.project(db, project_id)
    return {"items": sorted(service.project_tags(db, project_id))}


approval_router = APIRouter(prefix="/api/v1")


@approval_router.get("/mutation-requests/{request_id}")
def read_mutation_request(request_id: UUID, db: Db):
    row = db.get(MutationRequest, request_id)
    if row is None:
        raise ApiError(404, "not_found", "Mutation request not found")
    return serialize_mutation_request(row)


def serialize_mutation_request(row: MutationRequest):
    status = "expired" if row.status == "pending" and row.expires_at <= utcnow() else row.status
    return {
        "id": str(row.id), "project_id": str(row.project_id),
        "ticket_id": str(row.ticket_id) if row.ticket_id else None,
        "target_kind": row.target_kind, "target_id": str(row.target_id), "operation": row.operation,
        "proposed_changes": row.proposed_changes if status == "pending" else {},
        "base_revision": row.base_revision, "payload_hash": row.payload_hash,
        "requester_client_id": str(row.requester_client_id), "status": status,
        "created_at": service.timestamp(row.created_at), "expires_at": service.timestamp(row.expires_at),
        "decided_at": service.timestamp(row.decided_at) if row.decided_at else None,
    }


@router.get("/tickets/{ticket_id}/mutation-requests")
def list_ticket_mutation_requests(project_id: UUID, ticket_id: UUID, db: Db, limit: Limit = 50, cursor: str | None = None):
    service.artifact(db, Ticket, project_id, ticket_id)
    statement = select(MutationRequest).where(
        MutationRequest.project_id == project_id, MutationRequest.ticket_id == ticket_id)
    return page(db, MutationRequest, statement, limit, cursor, serialize_mutation_request)
