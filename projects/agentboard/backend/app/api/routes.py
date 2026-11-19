import base64
from uuid import UUID
from uuid import uuid4

from typing import Annotated
from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.artifacts.models import Document, Ticket
from app.db.models import AgentRole, AuditEvent, Project
from app.db.session import get_db
from app.schemas.common import ActivityCreate, ProjectCreate, ProjectDelete, ProjectRecord, ProjectUpdate, RoleCreate, RoleRecord, RoleUpdate
from app.services.activity import record_activity, serialize_activity
from app.services.idempotency import reserve
from app.services.projects import delete_project_records

router = APIRouter(prefix="/api/v1")


def _cursor_decode(cursor: str | None) -> UUID | None:
    if not cursor:
        return None
    try:
        return UUID(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode())
    except Exception as exc:
        raise ApiError(422, "invalid_cursor", "Cursor is invalid") from exc


def _cursor_encode(record_id: UUID) -> str:
    return base64.urlsafe_b64encode(str(record_id).encode()).decode().rstrip("=")


def _page(db: Session, stmt, limit: int, cursor: str | None, model):
    last = _cursor_decode(cursor)
    if last:
        stmt = stmt.where(model.id > last)
    rows = list(db.scalars(stmt.order_by(model.id).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    return {"items": rows, "next_cursor": _cursor_encode(rows[-1].id) if more and rows else None}


def _event(db: Session, project_id: UUID | None, action: str, kind: str, target_id: UUID | None):
    db.add(AuditEvent(project_id=project_id, action=action, target_type=kind, target_id=target_id, actor="browser"))
    if project_id is not None:
        record_activity(db, project_id=project_id, agent_name="Browser", action=f"{action.title()} {kind}",
                        event_type="api_operation", outcome="success", dedupe_key=str(uuid4()),
                        summary=f"{kind.title()} {action}d" if action in {"create", "update", "delete"} else "",
                        provenance="api_observed")


@router.get("/projects")
def list_projects(limit: int = Query(50, ge=1, le=100), cursor: str | None = None, db: Session = Depends(get_db)):
    return _page(db, select(Project), limit, cursor, Project)


@router.post("/projects", response_model=ProjectRecord, status_code=201)
def create_project(body: ProjectCreate, key: Annotated[str, Header(alias="Idempotency-Key")], db: Session = Depends(get_db)):
    operation, fresh = reserve(db, "projects:create", key, body.model_dump())
    if not fresh:
        return operation.result_json
    row = Project(**body.model_dump())
    db.add(row)
    db.flush()
    _event(db, row.id, "create", "project", row.id)
    operation.result_json = ProjectRecord.model_validate(row).model_dump(mode="json")
    db.commit()
    db.refresh(row)
    return row


@router.get("/projects/{project_id}", response_model=ProjectRecord)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    row = db.get(Project, project_id)
    if row is None:
        raise ApiError(404, "not_found", "Project not found")
    return row


@router.patch("/projects/{project_id}", response_model=ProjectRecord)
def update_project(project_id: UUID, body: ProjectUpdate, db: Session = Depends(get_db)):
    row = db.scalar(select(Project).where(Project.id == project_id).with_for_update())
    if row is None:
        raise ApiError(404, "not_found", "Project not found")
    if row.revision != body.expected_revision:
        raise ApiError(409, "stale_revision", "Project changed since it was read")
    changes = body.changes.model_dump(exclude_unset=True)
    if not changes:
        raise ApiError(422, "empty_update", "At least one field must change")
    if "name" in changes and (changes["name"] is None or not changes["name"].strip()):
        raise ApiError(422, "invalid_name", "Name must contain a non-whitespace character")
    for key, value in changes.items():
        setattr(row, key, value.strip() if key == "name" else value)
    row.revision += 1
    _event(db, row.id, "update", "project", row.id)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: UUID, body: ProjectDelete, db: Session = Depends(get_db)):
    row = db.scalar(select(Project).where(Project.id == project_id).with_for_update())
    if row is None:
        raise ApiError(404, "not_found", "Project not found")
    if row.revision != body.expected_revision:
        raise ApiError(409, "stale_revision", "Project changed since it was read")
    _event(db, row.id, "delete", "project", row.id)
    # Flush the audit row and activity event before deleting project-owned rows.
    db.flush()
    delete_project_records(db, project_id)
    db.delete(row)
    db.commit()
    return Response(status_code=204)


@router.get("/projects/{project_id}/roles")
def list_roles(project_id: UUID, limit: int = Query(50, ge=1, le=100), cursor: str | None = None, db: Session = Depends(get_db)):
    if db.get(Project, project_id) is None:
        raise ApiError(404, "not_found", "Project not found")
    return _page(db, select(AgentRole).where(AgentRole.project_id == project_id), limit, cursor, AgentRole)


@router.post("/projects/{project_id}/roles", response_model=RoleRecord, status_code=201)
def create_role(project_id: UUID, body: RoleCreate, key: Annotated[str, Header(alias="Idempotency-Key")], db: Session = Depends(get_db)):
    if db.get(Project, project_id) is None:
        raise ApiError(404, "not_found", "Project not found")
    operation, fresh = reserve(db, f"projects:{project_id}:roles:create", key, body.model_dump())
    if not fresh:
        return operation.result_json
    row = AgentRole(project_id=project_id, **body.model_dump())
    db.add(row)
    db.flush()
    _event(db, project_id, "create", "role", row.id)
    operation.result_json = RoleRecord.model_validate(row).model_dump(mode="json")
    db.commit()
    db.refresh(row)
    return row


@router.get("/projects/{project_id}/roles/{role_id}", response_model=RoleRecord)
def get_role(project_id: UUID, role_id: UUID, db: Session = Depends(get_db)):
    row = db.scalar(select(AgentRole).where(AgentRole.project_id == project_id, AgentRole.id == role_id))
    if row is None:
        raise ApiError(404, "not_found", "Role not found")
    return row


@router.patch("/projects/{project_id}/roles/{role_id}", response_model=RoleRecord)
def update_role(project_id: UUID, role_id: UUID, body: RoleUpdate, db: Session = Depends(get_db)):
    row = db.scalar(select(AgentRole).where(AgentRole.project_id == project_id, AgentRole.id == role_id).with_for_update())
    if row is None:
        raise ApiError(404, "not_found", "Role not found")
    if row.revision != body.expected_revision:
        raise ApiError(409, "stale_revision", "Role changed since it was read")
    changes = body.changes.model_dump(exclude_unset=True)
    if not changes:
        raise ApiError(422, "empty_update", "At least one field must change")
    for key, value in changes.items():
        if value is None or not value.strip():
            raise ApiError(422, "invalid_field", f"{key} must not be blank", {key: "blank"})
        setattr(row, key, value.strip())
    row.revision += 1
    _event(db, project_id, "update", "role", row.id)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/projects/{project_id}/roles/{role_id}", status_code=204)
def delete_role(project_id: UUID, role_id: UUID, expected_revision: int = Query(ge=1), db: Session = Depends(get_db)):
    parent = db.scalar(select(Project).where(Project.id == project_id).with_for_update())
    if parent is None:
        raise ApiError(404, "not_found", "Project not found")
    row = db.scalar(select(AgentRole).where(AgentRole.project_id == project_id, AgentRole.id == role_id))
    if row is None:
        raise ApiError(404, "not_found", "Role not found")
    if row.revision != expected_revision:
        raise ApiError(409, "stale_revision", "Role changed since it was read")
    if db.scalar(select(Ticket.id).where(Ticket.project_id == project_id, Ticket.role_id == role_id).limit(1)):
        raise ApiError(409, "role_assigned", "Role is assigned to one or more tickets")
    _event(db, project_id, "delete", "role", row.id)
    db.delete(row)
    db.commit()
    return Response(status_code=204)
