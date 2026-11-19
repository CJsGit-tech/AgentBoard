"""Database-backed operations for the checked-in MCP tool catalog."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from difflib import unified_diff
from hashlib import sha256
import json
from typing import Any
from contextvars import ContextVar
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, String, cast, func, or_, select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Bundle, Session

from app.api.errors import ApiError
from app.api.routes import _page
from app.artifacts import service
from app.artifacts.contracts import validate
from app.artifacts.models import Document, DocumentVersion, Ticket, TicketDocument
from app.db.models import ActivityEvent, AgentRole, AuditEvent, Project, utcnow
from app.mcp.auth import McpClient
from app.mcp.models import MutationRequest
from app.services.activity import RETENTION_DAYS, record_activity
from app.services.idempotency import reserve

input_round: ContextVar[tuple[str | None, dict | None]] = ContextVar(
    "agentboard_mcp_input_round", default=(None, None),
)


def _wire_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _cursor_encode_activity(row: ActivityEvent) -> str:
    raw = f"{_wire_datetime(row.received_at)}|{row.id}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def _cursor_decode_activity(cursor: str | None) -> tuple[datetime, UUID] | None:
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
        timestamp, event_id = raw.split("|", 1)
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")), UUID(event_id)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ApiError(422, "invalid_cursor", "Cursor is invalid") from exc


def _audit(db: Session, project_id: UUID, action: str, kind: str, target_id: UUID,
           client: McpClient, *, outcome: str = "success", ticket_id: UUID | None = None) -> None:
    db.add(AuditEvent(project_id=project_id, action=action, target_type=kind, target_id=target_id, actor="agent"))
    record_activity(
        db, project_id=project_id, agent_name=client.name, action=f"{kind}.{action}",
        event_type="ticket_update" if kind == "ticket" else "api_operation", outcome=outcome,
        dedupe_key=f"mcp-audit:{client.id}:{uuid4()}", ticket_id=ticket_id or (target_id if kind == "ticket" else None),
        labels=[kind], provenance="mcp_observed", client_id=client.id,
    )


def _project_record(row: Project) -> dict:
    return {"id": str(row.id), "revision": row.revision, "created_at": _wire_datetime(row.created_at),
            "updated_at": _wire_datetime(row.updated_at), "name": row.name, "purpose": row.purpose}


def _role_record(row: AgentRole) -> dict:
    return {"id": str(row.id), "project_id": str(row.project_id), "revision": row.revision,
            "created_at": _wire_datetime(row.created_at), "updated_at": _wire_datetime(row.updated_at),
            "name": row.name, "responsibilities": row.responsibilities}


def _page_records(db: Session, model, stmt, limit: int, cursor: str | None, serializer) -> dict:
    result = _page(db, stmt, limit, cursor, model)
    return {"items": [serializer(row) for row in result["items"]], "next_cursor": result["next_cursor"]}


_DOCUMENT_SUMMARY = Bundle(
    "document_summary",
    Document.id.label("id"),
    Document.revision.label("revision"),
    Document.created_at.label("created_at"),
    Document.updated_at.label("updated_at"),
    Document.project_id.label("project_id"),
    Document.fields["title"].as_string().label("title"),
    Document.version.label("version"),
    Document.current_version_id.label("current_version_id"),
    Document.fields["description"].as_string().label("description"),
    Document.fields["kind"].as_string().label("kind"),
    Document.fields["tags"].label("tags"),
    Document.fields["source"].as_string().label("source"),
    Document.fields["source_id"].as_string().label("source_id"),
)


def _document_summary(row) -> dict:
    return {
        "id": str(row.id), "revision": row.revision,
        "created_at": _wire_datetime(row.created_at), "updated_at": _wire_datetime(row.updated_at),
        "project_id": str(row.project_id), "title": row.title, "version": row.version,
        "current_version_id": str(row.current_version_id), "description": row.description,
        "kind": row.kind, "tags": row.tags, "source": row.source,
        "source_id": row.source_id,
    }


def _artifact_record(db: Session, model, project_id: UUID, record_id: UUID):
    return service.artifact(db, model, project_id, record_id)


def _role_record_in_project(db: Session, project_id: UUID, role_id: UUID) -> AgentRole:
    row = db.scalar(select(AgentRole).where(AgentRole.project_id == project_id, AgentRole.id == role_id))
    if row is None:
        raise ApiError(404, "not_found", "Role not found")
    return row


def _page_ticket(db: Session, stmt, project_id: UUID, limit: int, cursor: str | None) -> dict:
    result = _page(db, stmt, limit, cursor, Ticket)
    pending = set(db.scalars(select(MutationRequest.target_id).where(
        MutationRequest.project_id == project_id, MutationRequest.target_kind == "ticket",
        MutationRequest.status == "pending", MutationRequest.expires_at > utcnow(),
    )))
    return {"items": [{**service.serialize(row), "needs_approval": row.id in pending} for row in result["items"]],
            "next_cursor": result["next_cursor"]}


def _filter_tags(db, project_id, stmt, model, feature_tags, concern_tags):
    for tags, namespace in ((feature_tags, "feature:"), (concern_tags, "concern:")):
        if tags:
            if len(tags) > 30 or any(not tag.startswith(namespace) for tag in tags):
                raise ApiError(422, "invalid_tags", f"Expected up to 30 {namespace} tags")
            stmt = stmt.where(model.fields["tags"].has_any(cast(tags, ARRAY(String))))
    service.ensure_tags(db, project_id, {"tags": [*(feature_tags or []), *(concern_tags or [])]})
    return stmt


def _timestamp_filter(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ApiError(422, "invalid_timestamp", "Timestamp must be ISO 8601") from exc


def _event_wire(row: ActivityEvent) -> dict:
    return {"id": str(row.id), "project_id": str(row.project_id),
            "ticket_id": str(row.ticket_id) if row.ticket_id else None,
    "agent_client_id": str(row.client_id) if row.client_id else None, "agent_name": row.agent_name, "action": row.action,
            "event_type": row.event_type, "outcome": row.outcome, "summary": row.summary,
            "labels": list(row.labels or []), "occurred_at": _wire_datetime(row.occurred_at),
            "received_at": _wire_datetime(row.received_at), "provenance": row.provenance}


def _mutation_wire(row: MutationRequest) -> dict:
    expired_pending = row.status == "pending" and row.expires_at <= utcnow()
    status = "expired" if expired_pending else row.status
    terminal = status in {"applied", "rejected", "cancelled", "expired", "stale"}
    return {"id": str(row.id), "project_id": str(row.project_id),
            "ticket_id": str(row.ticket_id) if row.ticket_id else None,
            "target_kind": row.target_kind, "target_id": str(row.target_id),
            "operation": row.operation, "proposed_changes": {} if terminal else row.proposed_changes,
            "base_revision": row.base_revision, "payload_hash": row.payload_hash,
            "requester_client_id": str(row.requester_client_id), "status": status,
            "created_at": _wire_datetime(row.created_at), "expires_at": _wire_datetime(row.expires_at),
            "decided_at": _wire_datetime(row.decided_at)}


def _result(data: Any, *, applied: bool = False) -> dict:
    return {"outcome": "success", "applied": applied, "data": data}


def _error(code: str, message: str, fields: dict | None = None, *, outcome: str = "error", request_id: UUID | None = None) -> dict:
    return {"outcome": outcome, "applied": False,
            "error": {"code": code, "message": message, "fields": fields or {}},
            "request_id": str(request_id or uuid4())}


def _get_request(db: Session, request_id: UUID, client: McpClient) -> MutationRequest:
    row = db.get(MutationRequest, request_id)
    if row is None or row.requester_client_id != client.id:
        raise ApiError(404, "not_found", "Mutation request not found")
    return row


def _request_by_key(db: Session, project_id: UUID, client: McpClient, operation_key: str) -> MutationRequest | None:
    return db.scalar(select(MutationRequest).where(
        MutationRequest.project_id == project_id,
        MutationRequest.requester_client_id == client.id,
        MutationRequest.operation_key == operation_key,
    ))


def _request_payload_hash(target_kind: str, target_id: UUID, operation: str, changes: dict,
                          expected_revision: int, ticket_id: UUID | None) -> str:
    effective_ticket_id = ticket_id or (target_id if target_kind == "ticket" else None)
    material = {"target_kind": target_kind, "target_id": str(target_id), "operation": operation,
                "changes": changes, "base_revision": expected_revision,
                "ticket_id": str(effective_ticket_id) if effective_ticket_id else None}
    return sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _target(db: Session, project_id: UUID, target_kind: str, target_id: UUID, ticket_id: UUID | None = None):
    if target_kind == "project":
        return service.project(db, project_id)
    if target_kind == "role":
        return _role_record_in_project(db, project_id, target_id)
    if target_kind == "ticket":
        return _artifact_record(db, Ticket, project_id, target_id)
    if target_kind == "document":
        return _artifact_record(db, Document, project_id, target_id)
    if target_kind == "ticket_document":
        if ticket_id is None:
            raise ApiError(422, "invalid_target", "A ticket ID is required for a document association")
        return _artifact_record(db, Ticket, project_id, ticket_id)
    raise ApiError(422, "invalid_target", "Unsupported mutation target")


def create_mutation_request(
    db: Session, client: McpClient, *, project_id: UUID, target_kind: str, target_id: UUID,
    operation: str, changes: dict, expected_revision: int, operation_key: str,
    ticket_id: UUID | None = None,
) -> MutationRequest:
    payload_hash = _request_payload_hash(target_kind, target_id, operation, changes, expected_revision, ticket_id)
    existing = _request_by_key(db, project_id, client, operation_key)
    if existing:
        if existing.payload_hash != payload_hash:
            raise ApiError(409, "idempotency_conflict", "This key already identifies a different mutation")
        if existing.status == "pending" and existing.expires_at <= utcnow():
            existing.status = "expired"
            existing.decided_at = utcnow()
            existing.proposed_changes = {}
            db.commit()
        return existing
    service.project(db, project_id, lock=True)
    target = _target(db, project_id, target_kind, target_id, ticket_id)
    service.revision(target, expected_revision)
    request = MutationRequest(
        project_id=project_id, ticket_id=ticket_id or (target_id if target_kind == "ticket" else None),
        target_kind=target_kind, target_id=target_id, operation=operation,
        proposed_changes=changes, base_revision=expected_revision, payload_hash=payload_hash,
        requester_client_id=client.id, operation_key=operation_key,
        status="pending", created_at=utcnow(), expires_at=utcnow() + timedelta(hours=24),
    )
    db.add(request)
    db.flush()
    _audit(db, project_id, "approval_requested", target_kind, target_id, client,
           outcome="pending", ticket_id=request.ticket_id)
    db.commit()
    db.refresh(request)
    return request


def _question(request: MutationRequest, target_title: str | None = None) -> tuple[str, dict]:
    label = target_title or f"{request.target_kind} {request.target_id}"
    details = json.dumps(request.proposed_changes, ensure_ascii=False, sort_keys=True, indent=2)
    if len(details) > 6000:
        details = details[:6000] + "\n… truncated in prompt; full payload is bound to the durable request"
    message = (f"Approve this AgentBoard {request.operation} for {label}? "
               f"Base revision: {request.base_revision}. Request ID: {request.id}.\n\n{details}")
    schema = {"type": "object", "properties": {"approved": {"type": "boolean", "description": "Approve this exact change"}},
              "required": ["approved"]}
    return message, schema


async def _ask_client(ctx, request_id: UUID, message: str, schema: dict):
    from mcp.types import ElicitRequest, ElicitRequestFormParams, InputRequiredResult
    from mcp.shared.exceptions import MCPError

    if ctx.protocol_version == "2026-07-28":
        request_state, responses = input_round.get()
        if responses is None:
            return InputRequiredResult(
                input_requests={"approval": ElicitRequest(params=ElicitRequestFormParams(message=message, requested_schema=schema))},
                request_state=str(request_id),
            )
        if request_state != str(request_id):
            return None
        answer = responses.get("approval")
    else:
        if not getattr(ctx.session, "can_send_request", False):
            return None
        try:
            answer = await ctx.session.elicit_form(message, schema, related_request_id=ctx.request_id)
        except MCPError:
            return None
    if answer is None:
        return None
    action = getattr(answer, "action", None)
    content = getattr(answer, "content", None)
    if action != "accept":
        return {"decision": "cancelled" if action == "cancel" else "rejected"}
    if not isinstance(content, dict) or content.get("approved") is not True:
        return {"decision": "rejected"}
    return {"decision": "approved"}


def _status_request(db: Session, request: MutationRequest, decision: str, client: McpClient) -> None:
    request.status = decision
    request.decided_at = utcnow()
    if decision in {"applied", "rejected", "cancelled", "expired", "stale"}:
        request.proposed_changes = {}
    outcome = decision if decision in {"rejected", "cancelled"} else "failed"
    _audit(db, request.project_id, f"approval_{decision}", request.target_kind, request.target_id,
           client, outcome=outcome, ticket_id=request.ticket_id)
    db.commit()


def _replay_result(db: Session, request: MutationRequest) -> dict:
    """Reconstruct an idempotent response without retaining document bodies."""
    reference = request.result or {}
    kind = reference.get("kind")
    if kind == "deleted":
        return {"deleted_id": reference["deleted_id"]}
    if kind == "unlinked":
        return {"project_id": str(request.project_id), "ticket_id": reference["ticket_id"],
                "document_id": reference["document_id"], "relationship": reference["relationship"]}
    if kind == "record":
        try:
            row = _target(db, request.project_id, request.target_kind, request.target_id, request.ticket_id)
        except ApiError:
            return {"deleted_id": str(request.target_id)}
        if isinstance(row, Project):
            return _project_record(row)
        if isinstance(row, AgentRole):
            return _role_record(row)
        return service.serialize(row)
    # Backward-compatible replay for requests written before compact result refs.
    return reference


def _target_label(db: Session, request: MutationRequest) -> str:
    try:
        row = _target(db, request.project_id, request.target_kind, request.target_id, request.ticket_id)
    except ApiError:
        return f"{request.target_kind} {request.target_id}"
    if isinstance(row, Project) or isinstance(row, AgentRole):
        return row.name
    if isinstance(row, (Ticket, Document)):
        return row.fields.get("title", f"{request.target_kind} {request.target_id}")
    return f"{request.target_kind} {request.target_id}"


def _validate_mutation_changes(target_kind: str, operation: str, changes: dict) -> None:
    if operation == "delete" or operation == "unlink":
        if operation == "delete" and changes:
            raise ApiError(422, "invalid_input", "Delete requests cannot include changes")
        if operation == "unlink" and (set(changes) != {"relationship"} or changes["relationship"] not in {"context", "output"}):
            raise ApiError(422, "invalid_input", "Unlink requires a valid relationship")
        return
    schema_name = {"project": "ProjectChanges", "role": "RoleChanges", "ticket": "TicketChanges", "document": "DocumentChanges"}.get(target_kind)
    if schema_name:
        validate(schema_name, changes)


def _apply_mutation(db: Session, request: MutationRequest, client: McpClient) -> dict:
    target = _target(db, request.project_id, request.target_kind, request.target_id, request.ticket_id)
    if getattr(target, "revision", request.base_revision) != request.base_revision:
        request.status = "stale"
        request.decided_at = utcnow()
        request.proposed_changes = {}
        db.commit()
        raise ApiError(409, "stale_revision", "Record changed before the approved mutation could be applied")
    actual_hash = _request_payload_hash(request.target_kind, request.target_id, request.operation,
                                        request.proposed_changes, request.base_revision, request.ticket_id)
    if actual_hash != request.payload_hash:
        raise ApiError(409, "payload_changed", "The approved mutation payload no longer matches")
    if request.status not in {"pending", "approved"} or request.expires_at <= utcnow():
        if request.status == "pending":
            request.status = "expired"
            request.decided_at = utcnow()
            request.proposed_changes = {}
            db.commit()
        raise ApiError(409, "request_unavailable", "Mutation request is no longer pending")

    if request.operation == "update":
        if isinstance(target, Project):
            for key, value in request.proposed_changes.items():
                setattr(target, key, value.strip() if key == "name" else value)
            target.revision += 1
            target.updated_at = utcnow()
            _audit(db, request.project_id, "update", "project", target.id, client)
            data = _project_record(target)
        elif isinstance(target, AgentRole):
            for key, value in request.proposed_changes.items():
                setattr(target, key, value.strip())
            target.revision += 1
            target.updated_at = utcnow()
            _audit(db, request.project_id, "update", "role", target.id, client)
            data = _role_record(target)
        else:
            data = service.update(db, target, request.proposed_changes, client_id=client.id, commit=False)
            if isinstance(target, Ticket):
                pending = db.scalar(select(func.count()).select_from(MutationRequest).where(
                    MutationRequest.project_id == request.project_id, MutationRequest.target_kind == "ticket",
                    MutationRequest.target_id == target.id, MutationRequest.status == "pending",
                    MutationRequest.expires_at > utcnow(), MutationRequest.id != request.id,
                ))
                data["needs_approval"] = bool(pending)
    elif request.operation == "restore":
        version_id = UUID(request.proposed_changes["version_id"])
        version = db.scalar(select(DocumentVersion).where(
            DocumentVersion.project_id == request.project_id,
            DocumentVersion.document_id == request.target_id, DocumentVersion.id == version_id,
        ))
        if version is None:
            raise ApiError(404, "not_found", "Document revision is unavailable")
        data = service.update(db, target, version.fields, client_id=client.id, commit=False)
    elif request.operation == "delete":
        if isinstance(target, Project):
            dependents = any(db.scalar(select(model.id).where(model.project_id == request.project_id).limit(1))
                             for model in (AgentRole, Ticket, Document))
            if dependents:
                raise ApiError(409, "project_not_empty", "Project still has related records")
        if isinstance(target, AgentRole) and db.scalar(select(Ticket.id).where(
                Ticket.project_id == request.project_id, Ticket.role_id == target.id).limit(1)):
            raise ApiError(409, "role_in_use", "Role is assigned to one or more tickets")
        target_id = target.id
        kind = request.target_kind
        _audit(db, request.project_id, "delete", kind, target_id, client)
        db.delete(target)
        data = {"deleted_id": str(target_id)}
    elif request.operation == "unlink":
        ticket_id = request.ticket_id
        relationship = request.proposed_changes.get("relationship")
        link = db.get(TicketDocument, (request.project_id, ticket_id, request.target_id, relationship))
        if link is None:
            raise ApiError(404, "not_found", "Document link not found")
        _audit(db, request.project_id, "unlink", "ticket", ticket_id, client)
        db.delete(link)
        data = {"project_id": str(request.project_id), "ticket_id": str(ticket_id),
                "document_id": str(request.target_id), "relationship": relationship,
                "created_at": _wire_datetime(link.created_at)}
    else:
        raise ApiError(422, "invalid_operation", "Unsupported mutation operation")

    request.status = "applied"
    request.decided_at = utcnow()
    if request.operation == "delete":
        request.result = {"kind": "deleted", "deleted_id": str(target_id)}
    elif request.operation == "unlink":
        request.result = {"kind": "unlinked", "ticket_id": str(request.ticket_id),
                          "document_id": str(request.target_id),
                          "relationship": request.proposed_changes["relationship"]}
    else:
        request.result = {"kind": "record", "target_kind": request.target_kind,
                          "target_id": str(request.target_id)}
    request.proposed_changes = {}
    db.commit()
    return data


async def _approval_flow(ctx, db: Session, client: McpClient, *, project_id: UUID,
                         target_kind: str, target_id: UUID, operation: str, changes: dict,
                         expected_revision: int, operation_key: str, ticket_id: UUID | None = None,
                         retry_request_id: UUID | None = None) -> dict | Any:
    from mcp.types import InputRequiredResult

    if not retry_request_id:
        _validate_mutation_changes(target_kind, operation, changes)
    try:
        if retry_request_id:
            request = _get_request(db, retry_request_id, client)
            if request.status == "applied":
                return {"retry_result": _mutation_wire(request)}
            if request.status not in {"pending", "approved"}:
                raise ApiError(409, "request_unavailable", "Mutation request is not pending")
            _validate_mutation_changes(request.target_kind, request.operation, request.proposed_changes)
            if request.expires_at <= utcnow():
                _status_request(db, request, "expired", client)
                raise ApiError(410, "request_expired", "Mutation request expired")
        else:
            request = create_mutation_request(
                db, client, project_id=project_id, target_kind=target_kind, target_id=target_id,
                operation=operation, changes=changes, expected_revision=expected_revision,
                operation_key=operation_key, ticket_id=ticket_id,
            )
        if request.status == "applied" and request.result is not None:
            return {"already_applied": _replay_result(db, request), "request": _mutation_wire(request)}
        if request.status == "approved":
            # Earlier versions could persist approval before applying the mutation.
            # Require a fresh decision before resuming any such request.
            request.status = "pending"
            request.decided_at = None
            db.commit()
        if request.status != "pending":
            raise ApiError(409, "request_unavailable", "Mutation request is no longer pending")
        if not client.interactive_approval_verified:
            return {"approval_required": request}
        prompt = _question(request, _target_label(db, request))
        request_id, owning_project_id = request.id, request.project_id
        db.commit()
        response = await _ask_client(ctx, request_id, *prompt)
        if isinstance(response, InputRequiredResult):
            return response
        if not isinstance(response, dict):
            return {"approval_required": request}
        decision = response.get("decision")
        if decision not in {"approved", "cancelled", "rejected"}:
            return {"approval_required": request}

        # Serialize competing decisions only after the client has answered.
        service.project(db, owning_project_id, lock=True)
        request = db.scalar(select(MutationRequest).where(MutationRequest.id == request_id)
                            .with_for_update().execution_options(populate_existing=True))
        if request is None:
            raise ApiError(404, "not_found", "Mutation request not found")
        if request.status == "applied" and request.result is not None:
            if retry_request_id:
                return {"retry_result": _mutation_wire(request)}
            return {"already_applied": _replay_result(db, request), "request": _mutation_wire(request)}
        if request.status != "pending":
            raise ApiError(409, "request_unavailable", "Mutation request is no longer pending")
        if request.expires_at <= utcnow():
            _status_request(db, request, "expired", client)
            raise ApiError(410, "request_expired", "Mutation request expired")
        if decision in {"cancelled", "rejected"}:
            _status_request(db, request, decision, client)
            return {"decision": decision, "request": request}
        data = _apply_mutation(db, request, client)
        return {"applied": data, "request": request}
    except ApiError:
        raise
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(409, "conflict", "Mutation conflicts with a related record") from exc


def _mutation_outcome(flow: dict, *, retry: bool = False) -> dict | Any:
    from mcp.types import InputRequiredResult

    if isinstance(flow, InputRequiredResult):
        return flow
    if "approval_required" in flow:
        request = flow["approval_required"]
        return {"outcome": "approval_required", "request_id": str(request.id),
                "ticket_id": str(request.ticket_id) if request.ticket_id else None,
                "applied": False, "message": "Request is saved; use a client that supports user elicitation to approve it."}
    if "decision" in flow:
        request = flow["request"]
        decision = flow["decision"]
        return {"outcome": decision, "applied": False,
                "error": {"code": decision, "message": "The user did not approve this change", "fields": {}},
                "request_id": str(request.id)}
    if "already_applied" in flow:
        return {"outcome": "success", "applied": True,
                "data": flow["request"] if retry else flow["already_applied"]}
    if "retry_result" in flow:
        return {"outcome": "success", "applied": True, "data": flow["retry_result"]}
    if "applied" in flow:
        return {"outcome": "success", "applied": True,
                "data": _mutation_wire(flow["request"]) if retry else flow["applied"]}
    return flow


def _serialize_version(row: DocumentVersion) -> dict:
    fields = {key: val for key, val in row.fields.items() if key != "title"}
    return {**fields, "id": str(row.id), "project_id": str(row.project_id),
            "document_id": str(row.document_id), "version": row.version,
            "author_client_id": str(row.author_client_id) if row.author_client_id else None,
            "source": row.source, "created_at": _wire_datetime(row.created_at)}


def _activity_page(db: Session, args: dict) -> dict:
    project_id = UUID(args["project_id"])
    service.project(db, project_id)
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    stmt = select(ActivityEvent).where(ActivityEvent.project_id == project_id, ActivityEvent.received_at > cutoff)
    if args.get("ticket_id"):
        stmt = stmt.where(ActivityEvent.ticket_id == UUID(args["ticket_id"]))
    if args.get("agent_client_id"):
        stmt = stmt.where(ActivityEvent.client_id == UUID(args["agent_client_id"]))
    for key, column in (("event_type", ActivityEvent.event_type), ("outcome", ActivityEvent.outcome), ("provenance", ActivityEvent.provenance)):
        if args.get(key):
            stmt = stmt.where(column == args[key])
    labels = args.get("labels") or []
    if labels:
        stmt = stmt.where(or_(*(ActivityEvent.labels.contains([label]) for label in labels)))
    since, until = _timestamp_filter(args.get("since")), _timestamp_filter(args.get("until"))
    if since:
        stmt = stmt.where(ActivityEvent.occurred_at >= since)
    if until:
        stmt = stmt.where(ActivityEvent.occurred_at <= until)
    cursor = _cursor_decode_activity(args.get("cursor"))
    if cursor:
        stmt = stmt.where(tuple_(ActivityEvent.received_at, ActivityEvent.id) < tuple_(*cursor))
    limit = args.get("limit", 50)
    rows = list(db.scalars(stmt.order_by(ActivityEvent.received_at.desc(), ActivityEvent.id.desc()).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    return {"items": [_event_wire(row) for row in rows],
            "next_cursor": _cursor_encode_activity(rows[-1]) if more and rows else None}


async def dispatch(ctx, db: Session, tool_name: str, args: dict[str, Any], client: McpClient):
    """Run a validated MCP operation using the same SQLAlchemy services as REST."""
    p = UUID(args["project_id"]) if args.get("project_id") else None
    limit = args.get("limit", 50)
    cursor = args.get("cursor")

    if tool_name == "list_projects":
        return _result(_page_records(db, Project, select(Project), limit, cursor, _project_record))
    if tool_name == "get_project":
        return _result(_project_record(service.project(db, p)))
    if tool_name == "create_project":
        data = args["data"]
        validate("ProjectCreate", data)
        reservation, fresh = reserve(db, f"mcp:{client.id}:projects:create", args["operation_key"], data)
        if not fresh:
            return _result(reservation.result_json, applied=True)
        row = Project(name=data["name"].strip(), purpose=data.get("purpose", ""))
        db.add(row)
        db.flush()
        _audit(db, row.id, "create", "project", row.id, client)
        reservation.result_json = _project_record(row)
        db.commit()
        return _result(_project_record(row), applied=True)
    if tool_name == "update_project":
        result = await _approval_flow(ctx, db, client, project_id=p, target_kind="project", target_id=p,
            operation="update", changes=args["changes"], expected_revision=args["expected_revision"],
            operation_key=args["operation_key"])
        return _mutation_outcome(result)
    if tool_name == "delete_project":
        result = await _approval_flow(ctx, db, client, project_id=p, target_kind="project", target_id=p,
            operation="delete", changes={}, expected_revision=args["expected_revision"],
            operation_key=args["operation_key"])
        return _mutation_outcome(result)

    if tool_name == "list_roles":
        service.project(db, p)
        stmt = select(AgentRole).where(AgentRole.project_id == p)
        return _result(_page_records(db, AgentRole, stmt, limit, cursor, _role_record))
    if tool_name == "get_role":
        return _result(_role_record(_role_record_in_project(db, p, UUID(args["role_id"]))))
    if tool_name == "create_role":
        service.project(db, p, lock=True)
        data = args["data"]
        validate("RoleCreate", data)
        scope = f"mcp:{client.id}:roles:{p}:create"
        reservation, fresh = reserve(db, scope, args["operation_key"], data)
        if not fresh:
            return _result(reservation.result_json, applied=True)
        row = AgentRole(project_id=p, name=data["name"].strip(), responsibilities=data["responsibilities"].strip())
        db.add(row)
        db.flush()
        value = _role_record(row)
        reservation.result_json = value
        _audit(db, p, "create", "role", row.id, client)
        db.commit()
        return _result(value, applied=True)
    if tool_name == "update_role":
        result = await _approval_flow(ctx, db, client, project_id=p, target_kind="role", target_id=UUID(args["role_id"]),
            operation="update", changes=args["changes"], expected_revision=args["expected_revision"],
            operation_key=args["operation_key"])
        return _mutation_outcome(result)
    if tool_name == "delete_role":
        result = await _approval_flow(ctx, db, client, project_id=p, target_kind="role", target_id=UUID(args["role_id"]),
            operation="delete", changes={}, expected_revision=args["expected_revision"],
            operation_key=args["operation_key"])
        return _mutation_outcome(result)

    if tool_name == "list_tickets":
        service.project(db, p)
        stmt = select(Ticket).where(Ticket.project_id == p)
        for field in ("status", "priority", "owner_kind"):
            if args.get(field):
                stmt = stmt.where(Ticket.fields[field].astext == args[field])
        stmt = _filter_tags(db, p, stmt, Ticket, args.get("feature_tags"), args.get("concern_tags"))
        return _result(_page_ticket(db, stmt, p, limit, cursor))
    if tool_name == "get_ticket":
        row = _artifact_record(db, Ticket, p, UUID(args["ticket_id"]))
        pending = db.scalar(select(func.count()).select_from(MutationRequest).where(
            MutationRequest.project_id == p, MutationRequest.target_kind == "ticket",
            MutationRequest.target_id == row.id, MutationRequest.status == "pending",
            MutationRequest.expires_at > utcnow()))
        return _result({**service.serialize(row), "needs_approval": bool(pending)})
    if tool_name == "create_ticket":
        data = args["data"]
        validate("TicketCreate", data)
        return _result({**service.create(db, Ticket, p, data, args["operation_key"], client_id=client.id),
                        "needs_approval": False}, applied=True)
    if tool_name == "update_ticket":
        result = await _approval_flow(ctx, db, client, project_id=p, target_kind="ticket", target_id=UUID(args["ticket_id"]),
            operation="update", changes=args["changes"], expected_revision=args["expected_revision"],
            operation_key=args["operation_key"])
        return _mutation_outcome(result)
    if tool_name == "delete_ticket":
        result = await _approval_flow(ctx, db, client, project_id=p, target_kind="ticket", target_id=UUID(args["ticket_id"]),
            operation="delete", changes={}, expected_revision=args["expected_revision"],
            operation_key=args["operation_key"])
        return _mutation_outcome(result)

    if tool_name == "list_documents":
        service.project(db, p)
        include_content = args.get("include_content", True)
        stmt = select(Document if include_content else _DOCUMENT_SUMMARY).where(Document.project_id == p)
        stmt = _filter_tags(db, p, stmt, Document, args.get("feature_tags"), args.get("concern_tags"))
        serializer = service.serialize if include_content else _document_summary
        return _result(_page_records(db, Document, stmt, limit, cursor, serializer))
    if tool_name == "get_document":
        return _result(service.serialize(_artifact_record(db, Document, p, UUID(args["document_id"]))))
    if tool_name == "create_document":
        data = args["data"]
        validate("DocumentCreate", data)
        return _result(service.create(db, Document, p, data, args["operation_key"], client_id=client.id), applied=True)
    if tool_name == "update_document":
        result = await _approval_flow(ctx, db, client, project_id=p, target_kind="document", target_id=UUID(args["document_id"]),
            operation="update", changes=args["changes"], expected_revision=args["expected_revision"],
            operation_key=args["operation_key"])
        return _mutation_outcome(result)
    if tool_name == "delete_document":
        result = await _approval_flow(ctx, db, client, project_id=p, target_kind="document", target_id=UUID(args["document_id"]),
            operation="delete", changes={}, expected_revision=args["expected_revision"],
            operation_key=args["operation_key"])
        return _mutation_outcome(result)

    if tool_name == "list_document_versions":
        document_id = UUID(args["document_id"])
        _artifact_record(db, Document, p, document_id)
        stmt = select(DocumentVersion).where(DocumentVersion.project_id == p, DocumentVersion.document_id == document_id)
        return _result(_page_records(db, DocumentVersion, stmt, limit, cursor, _serialize_version))
    if tool_name == "get_document_version":
        document_id, version_id = UUID(args["document_id"]), UUID(args["version_id"])
        row = db.scalar(select(DocumentVersion).where(
            DocumentVersion.project_id == p, DocumentVersion.document_id == document_id, DocumentVersion.id == version_id))
        if row is None:
            raise ApiError(404, "not_found", "Document revision is unavailable")
        return _result(_serialize_version(row))
    if tool_name == "compare_document_versions":
        document_id = UUID(args["document_id"])
        versions = []
        for version_id in (UUID(args["from_version_id"]), UUID(args["to_version_id"])):
            row = db.scalar(select(DocumentVersion).where(
                DocumentVersion.project_id == p, DocumentVersion.document_id == document_id, DocumentVersion.id == version_id))
            if row is None:
                raise ApiError(404, "not_found", "Document revision is unavailable")
            versions.append(row)
        diff = unified_diff(versions[0].fields["content"].splitlines(), versions[1].fields["content"].splitlines(),
                            fromfile=f"v{versions[0].version}", tofile=f"v{versions[1].version}", lineterm="")
        return _result({"document_id": str(document_id), "from_version_id": str(versions[0].id),
                        "to_version_id": str(versions[1].id), "unified_diff": "\n".join(diff)})
    if tool_name == "restore_document_version":
        result = await _approval_flow(ctx, db, client, project_id=p, target_kind="document", target_id=UUID(args["document_id"]),
            operation="restore", changes={"version_id": args["version_id"]},
            expected_revision=args["expected_revision"], operation_key=args["operation_key"])
        return _mutation_outcome(result)

    if tool_name == "link_document":
        service.project(db, p, lock=True)
        ticket_id, document_id = UUID(args["ticket_id"]), UUID(args["document_id"])
        _artifact_record(db, Ticket, p, ticket_id)
        _artifact_record(db, Document, p, document_id)
        body = {"document_id": str(document_id), "relationship": args["relationship"]}
        scope = f"{client.id}:link:{ticket_id}"
        saved, digest = service.replay(db, p, scope, args["operation_key"], body)
        if saved is not None:
            return _result(saved, applied=True)
        row = db.get(TicketDocument, (p, ticket_id, document_id, args["relationship"]))
        if row is None:
            row = TicketDocument(project_id=p, ticket_id=ticket_id, document_id=document_id,
                                 relationship=args["relationship"])
            db.add(row)
            db.flush()
            _audit(db, p, "link", "ticket", ticket_id, client)
        value = {"project_id": str(p), "ticket_id": str(ticket_id), "document_id": str(document_id),
                 "relationship": row.relationship, "created_at": _wire_datetime(row.created_at)}
        service.save_result(db, p, scope, args["operation_key"], digest, value)
        db.commit()
        return _result(value, applied=True)
    if tool_name == "unlink_document":
        result = await _approval_flow(ctx, db, client, project_id=p, target_kind="ticket_document",
            target_id=UUID(args["document_id"]), operation="unlink",
            changes={"relationship": args["relationship"]}, expected_revision=args["expected_revision"],
            operation_key=args["operation_key"], ticket_id=UUID(args["ticket_id"]))
        return _mutation_outcome(result)

    if tool_name == "append_activity":
        data = args["data"]
        validate("ActivityCreate", data)
        service.project(db, p)
        ticket_id = UUID(data["ticket_id"]) if data.get("ticket_id") else None
        if ticket_id:
            _artifact_record(db, Ticket, p, ticket_id)
        operation_key = args["operation_key"]
        if not operation_key or len(operation_key) > 128:
            raise ApiError(422, "invalid_idempotency_key", "Supply a valid operation key")
        reservation, fresh = reserve(db, f"mcp:{client.id}:activity:{p}", operation_key, data)
        if not fresh:
            return _result(reservation.result_json, applied=True)
        row = record_activity(db, project_id=p, agent_name=client.name, action=data["action"],
            event_type=data["event_type"], outcome=data["outcome"],
            dedupe_key=f"mcp:{client.id}:{operation_key}", ticket_id=ticket_id,
            summary=data.get("summary", ""), labels=data.get("labels", []),
            occurred_at=_timestamp_filter(data["occurred_at"]), provenance="agent_reported", client_id=client.id)
        reservation.result_json = _event_wire(row)
        db.commit()
        return _result(_event_wire(row), applied=True)
    if tool_name == "list_activity":
        return _result(_activity_page(db, args))
    if tool_name == "get_project_progress":
        service.project(db, p)
        counts = {status: db.scalar(select(func.count()).select_from(Ticket).where(
            Ticket.project_id == p, Ticket.fields["status"].astext == status)) or 0
            for status in ("planned", "in_progress", "blocked", "done")}
        pending = db.scalar(select(func.count()).select_from(MutationRequest).where(
            MutationRequest.project_id == p, MutationRequest.status == "pending",
            MutationRequest.expires_at > utcnow())) or 0
        total = sum(counts.values())
        return _result({"project_id": str(p), "counts": counts, "total": total,
                        "pending_approval_count": pending, "has_tasks": total > 0})

    if tool_name == "get_mutation_request":
        request = _get_request(db, UUID(args["request_id"]), client)
        return _result(_mutation_wire(request))
    if tool_name == "retry_mutation_request":
        request = _get_request(db, UUID(args["request_id"]), client)
        flow = await _approval_flow(ctx, db, client, project_id=request.project_id,
            target_kind=request.target_kind, target_id=request.target_id, operation=request.operation,
            changes=request.proposed_changes, expected_revision=request.base_revision,
            operation_key=request.operation_key, ticket_id=request.ticket_id,
            retry_request_id=request.id)
        return _mutation_outcome(flow, retry=True)

    raise ApiError(404, "unknown_tool", f"Unknown AgentBoard tool: {tool_name}")
