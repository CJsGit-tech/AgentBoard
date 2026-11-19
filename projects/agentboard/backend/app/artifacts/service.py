from datetime import UTC, datetime
from hashlib import sha256
import json
import re
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update as update_rows
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.artifacts.models import ArtifactOperation, Document, DocumentVersion, Ticket
from app.db.models import AgentRole, AuditEvent, Project, utcnow
from app.mcp.models import MutationRequest
from app.services.activity import record_activity
from app.settings import settings


def timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def project(db: Session, project_id: UUID, *, lock: bool = False) -> Project:
    query = select(Project).where(Project.id == project_id)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise ApiError(404, "not_found", "Project not found")
    return row


def artifact(db: Session, model, project_id: UUID, record_id: UUID):
    row = db.scalar(select(model).where(model.project_id == project_id, model.id == record_id))
    if row is None:
        raise ApiError(404, "not_found", f"{model.__name__} not found")
    return row


def revision(row, expected: int) -> None:
    if row.revision != expected:
        raise ApiError(409, "stale_revision", "Record changed since it was read")


def serialize(row) -> dict:
    data = dict(row.fields)
    data.update(id=str(row.id), project_id=str(row.project_id), revision=row.revision,
                created_at=timestamp(row.created_at), updated_at=timestamp(row.updated_at))
    if isinstance(row, Document):
        data.update(current_version_id=str(row.current_version_id), version=row.version)
    return data


def snapshot(db: Session, doc: Document, client_id: UUID | None = None) -> None:
    version_fields = {key: doc.fields[key] for key in ("title", "content", "description", "kind", "tags")}
    db.add(DocumentVersion(
        id=doc.current_version_id, project_id=doc.project_id, document_id=doc.id,
        version=doc.version, fields=version_fields, author_client_id=client_id,
        source="agent" if client_id else "builder",
    ))
    db.execute(delete(DocumentVersion).where(
        DocumentVersion.document_id == doc.id, DocumentVersion.version <= doc.version - 4,
    ))


def audit(db: Session, project_id: UUID, action: str, kind: str, target_id: UUID, *, actor: str = "browser", client_id: UUID | None = None) -> None:
    db.add(AuditEvent(project_id=project_id, action=action, target_type=kind, target_id=target_id, actor=actor))
    record_activity(
        db, project_id=project_id, agent_name="Agent" if actor == "agent" else "Builder",
        action=f"{kind}.{action}", event_type="ticket_update" if kind == "ticket" else "api_operation",
        outcome="success", dedupe_key=str(uuid4()), ticket_id=target_id if kind == "ticket" else None,
        labels=[kind], provenance="mcp_observed" if actor == "agent" else "api_observed",
        client_id=client_id,
    )


def parse_catalog(content: str) -> set[str]:
    try:
        data = json.loads(content)
        tags = {
            entry["id"]
            for group, namespace in (("features", "feature"), ("concerns", "concern"))
            for entry in data[group]
            if re.fullmatch(rf"{namespace}:[a-z0-9]+(?:-[a-z0-9]+)*", entry["id"])
        }
        if len(tags) != sum(len(data[group]) for group in ("features", "concerns")):
            raise ValueError("Duplicate or invalid tag IDs")
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ApiError(422, "invalid_tag_catalog", "Register unique, namespaced tag IDs in valid catalog JSON") from exc
    return tags


def project_tags(db: Session, project_id: UUID) -> set[str]:
    catalog = db.scalar(select(Document).where(
        Document.project_id == project_id, Document.fields["kind"].astext == "metadata-catalog",
    ).order_by(Document.updated_at.desc()).limit(1))
    return parse_catalog(catalog.fields["content"]) if catalog else set()


def ensure_tags(db: Session, project_id: UUID, body: dict) -> None:
    if body.get("tags"):
        unknown = set(body["tags"]) - project_tags(db, project_id)
        if unknown:
            raise ApiError(422, "unknown_tags", "Select tags registered in the project tag catalog",
                           {"tags": sorted(unknown)})


def replay(db: Session, project_id: UUID, scope: str, key: str, payload: dict):
    if not key.strip() or len(key) > 128:
        raise ApiError(422, "invalid_idempotency_key", "Supply a valid idempotency key")
    digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    saved = db.get(ArtifactOperation, (project_id, scope, key))
    if saved:
        if saved.digest != digest:
            raise ApiError(409, "idempotency_conflict", "This key already identifies a different request")
        return saved.result, digest
    return None, digest


def save_result(db: Session, project_id: UUID, scope: str, key: str, digest: str, result: dict) -> None:
    db.add(ArtifactOperation(project_id=project_id, scope=scope, key=key, digest=digest, result=result))


ticket_defaults = {
    "description": "", "details": "", "priority": "normal", "status": "planned",
    "owner_kind": "unassigned", "role_id": None, "blocker_reason": None,
    "milestone": None, "source": "manual", "source_id": None, "dependencies": [],
}
document_defaults = {"source": "manual", "source_id": None}


def validate_document_content(fields: dict) -> None:
    content = fields["content"]
    if "\0" in content:
        raise ApiError(422, "invalid_document_content", "Document content must be UTF-8 text")
    byte_count = len(content.encode("utf-8")) + len(fields.get("original_frontmatter", "").encode("utf-8"))
    if byte_count > settings.max_request_bytes:
        raise ApiError(413, "document_too_large", "Document content exceeds the configured byte limit")


def validate_ticket_assignment(db: Session, project_id: UUID, fields: dict) -> UUID | None:
    if (fields["status"] == "blocked") != bool(fields["blocker_reason"]):
        raise ApiError(422, "invalid_blocker", "Only blocked tickets require a blocker reason")
    role_id = fields["role_id"]
    if fields["owner_kind"] == "role":
        role = db.get(AgentRole, UUID(role_id)) if role_id else None
        if role is None or role.project_id != project_id:
            raise ApiError(422, "invalid_role", "Select a role in the current project")
        return role.id
    if role_id is not None:
        raise ApiError(422, "invalid_role", "Only role-owned tickets can have a role ID")
    return None


def create(db: Session, model, project_id: UUID, body: dict, key: str, *, client_id: UUID | None = None) -> dict:
    project(db, project_id, lock=True)
    kind = model.__name__.lower()
    scope = f"{client_id or 'browser'}:{kind}:create"
    saved, digest = replay(db, project_id, scope, key, body)
    if saved is not None:
        return serialize(artifact(db, model, project_id, UUID(saved["id"])))
    if body.get("source") == "agentbuild" and body.get("source_id"):
        existing = db.scalar(select(model.id).where(
            model.project_id == project_id, model.fields["source"].astext == "agentbuild",
            model.fields["source_id"].astext == body["source_id"],
        ).limit(1))
        if existing:
            raise ApiError(409, "source_id_conflict", "This AgentBuild record already exists",
                           {"id": str(existing)})
    if model is Document:
        validate_document_content(body)
    if model is Document and body.get("kind") == "metadata-catalog":
        parse_catalog(body["content"])
    else:
        ensure_tags(db, project_id, body)
    if model is Document and "original_frontmatter" in body and body.get("source") != "upload":
        raise ApiError(422, "invalid_upload_source", "Original frontmatter applies only to a Markdown upload")
    if model is Document and body.get("source") == "upload" and client_id:
        raise ApiError(403, "upload_review_required", "Review and confirm Markdown uploads in the browser")
    if model is Document and body.get("source") == "upload":
        filename = body.get("source_id")
        if not filename or not re.fullmatch(r"[^/\\\x00-\x1f]+\.(?:md|markdown)", filename, re.IGNORECASE):
            raise ApiError(422, "invalid_upload_source", "Supply the original Markdown filename")
    if model is Ticket:
        fields = {**ticket_defaults, **body}
        role_id = validate_ticket_assignment(db, project_id, fields)
        row = Ticket(project_id=project_id, fields=fields, role_id=role_id)
    else:
        row = Document(project_id=project_id, fields={**document_defaults, **body}, current_version_id=uuid4())
    db.add(row)
    db.flush()
    if model is Document:
        snapshot(db, row, client_id)
    result = serialize(row)
    save_result(db, project_id, scope, key, digest, {"id": result["id"]})
    audit(db, project_id, "create", kind, row.id, actor="agent" if client_id else "browser", client_id=client_id)
    db.commit()
    return result


def invalidate_pending(db: Session, project_id: UUID, kind: str, target_id: UUID) -> None:
    statement = update_rows(MutationRequest).where(
        MutationRequest.project_id == project_id, MutationRequest.status == "pending",
        MutationRequest.target_kind == kind, MutationRequest.target_id == target_id,
    )
    if kind == "ticket":
        statement = update_rows(MutationRequest).where(
            MutationRequest.project_id == project_id, MutationRequest.status == "pending",
            MutationRequest.ticket_id == target_id,
        )
    db.execute(statement.values(status="stale", decided_at=utcnow(), proposed_changes={}))


def update(db: Session, row, changes: dict, *, client_id: UUID | None = None, commit: bool = True) -> dict:
    fields = {**row.fields, **changes}
    if isinstance(row, Document):
        validate_document_content(fields)
    if fields.get("kind") == "metadata-catalog":
        parse_catalog(fields["content"])
    else:
        ensure_tags(db, row.project_id, changes)
    if isinstance(row, Ticket):
        row.role_id = validate_ticket_assignment(db, row.project_id, fields)
    row.fields = fields
    row.revision += 1
    row.updated_at = utcnow()
    if isinstance(row, Document):
        row.current_version_id = uuid4()
        row.version += 1
        snapshot(db, row, client_id)
    kind = type(row).__name__.lower()
    if client_id is None:
        invalidate_pending(db, row.project_id, kind, row.id)
    audit(db, row.project_id, "update", kind, row.id,
          actor="agent" if client_id else "browser", client_id=client_id)
    if commit:
        db.commit()
    else:
        db.flush()
    return serialize(row)
