import asyncio
import hashlib
import json
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header
from jsonschema import Draft202012Validator, FormatChecker
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.artifacts import service
from app.artifacts.contracts import validate
from app.artifacts.models import Document, Ticket
from app.db.models import AgentChangeApproval, AgentRole, AgentRun, AuditEvent, Project, WorkspaceSetting, utcnow
from app.db.session import SessionLocal, get_db
from app.sdk.adapters import OPENAI_TOOLS, ProviderRequestError, adapter_for
from app.services.idempotency import reserve
from app.settings import settings

router = APIRouter(prefix="/api/v1")
_active_run_tasks: dict[UUID, asyncio.Task] = {}


def _workspace_setting(db: Session):
    setting = db.get(WorkspaceSetting, 1)
    if setting is None:
        setting = WorkspaceSetting(id=1, sdk_runs_enabled=False)
        db.add(setting)
        db.flush()
    return setting


def _provider_readiness():
    codex_configured = bool(settings.openai_api_key and settings.openai_api_key.strip())
    claude_configured = bool(settings.anthropic_api_key and settings.anthropic_api_key.strip())
    codex_enabled = settings.codex_sdk_enabled
    claude_enabled = settings.claude_agent_sdk_enabled

    def provider_state(enabled, configured, label, default_model):
        if not enabled:
            return {"available": False, "reason": "Disabled by server configuration", "default_model": default_model}
        if not configured:
            return {"available": False, "reason": f"{label} API credential is not configured", "default_model": default_model}
        return {"available": True, "reason": None, "default_model": default_model}

    return {
        "codex": provider_state(codex_enabled, codex_configured, "OpenAI", _default_model("codex")),
        "claude": provider_state(claude_enabled, claude_configured, "Anthropic", _default_model("claude")),
    }


def _default_model(provider: str) -> str:
    configured = getattr(settings, "codex_default_model" if provider == "codex" else "claude_default_model", None)
    if configured and configured.strip():
        return configured.strip()
    return "gpt-6.1-sol" if provider == "codex" else "claude-sonnet-5-5"


@router.get("/settings/sdk-runs")
def get_sdk_run_settings(db: Session = Depends(get_db)):
    setting = _workspace_setting(db)
    db.commit()
    providers = _provider_readiness()
    return {"enabled": setting.sdk_runs_enabled, "providers": providers,
            "ready": setting.sdk_runs_enabled and any(p["available"] for p in providers.values())}


class SDKRunSettingUpdate(BaseModel):
    enabled: bool


@router.put("/settings/sdk-runs")
def update_sdk_run_settings(body: SDKRunSettingUpdate, db: Session = Depends(get_db)):
    setting = _workspace_setting(db)
    setting.sdk_runs_enabled = body.enabled
    setting.updated_at = utcnow()
    db.commit()
    return get_sdk_run_settings(db)


class RunCreate(BaseModel):
    provider: str
    prompt: str = Field(min_length=1, max_length=20000)
    model: str | None = Field(default=None, max_length=128)
    context_kind: Literal["ticket", "document"] | None = None
    context_id: UUID | None = None
    parent_run_id: UUID | None = None

    @field_validator("prompt")
    @classmethod
    def normalize_prompt(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("prompt must contain a message")
        return value

    @field_validator("provider")
    @classmethod
    def canonical_provider(cls, value: str) -> str:
        aliases = {"openai": "codex", "codex": "codex", "anthropic": "claude", "claude": "claude"}
        provider = aliases.get(value.strip().casefold())
        if provider is None:
            raise ValueError("provider must be openai/codex or anthropic/claude")
        return provider

    @field_validator("model")
    @classmethod
    def normalize_model(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class ChangeProposal(BaseModel):
    model_config = {"extra": "forbid"}
    operation: Literal["update", "delete"]
    target_kind: str
    target_id: UUID
    expected_revision: int = Field(ge=1)
    changes: dict

    @classmethod
    def supported(cls, data: dict):
        kind = data.get("target_kind")
        operation = data.get("operation")
        if kind not in {"ticket", "document"}:
            raise ApiError(422, "unsupported_proposal_kind", f"Unsupported proposal target kind: {kind}")
        if operation not in {"update", "delete"}:
            raise ApiError(422, "unsupported_proposal_operation", f"Unsupported proposal operation: {operation}")
        validated = dict(data)
        validated.pop("type", None)
        return cls.model_validate(validated)


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    change_hash: str = Field(min_length=64, max_length=64)
    expected_revision: int = Field(ge=1)


def _view(run: AgentRun):
    return {"id": str(run.id), "project_id": str(run.project_id), "provider": run.provider,
            "model": getattr(run, "model", None) or _default_model(run.provider),
            "parent_run_id": str(run.parent_run_id) if getattr(run, "parent_run_id", None) else None,
            "prompt": run.prompt,
            "status": run.status, "activity": run.activity, "result": run.result, "error": run.error,
            "created_at": run.created_at.isoformat(), "updated_at": run.updated_at.isoformat()}


def _conversation_history(db: Session, project_id: UUID, parent_run_id: UUID | None) -> list[dict[str, str]]:
    if parent_run_id is None:
        return []
    chain: list[AgentRun] = []
    seen: set[UUID] = set()
    current_id = parent_run_id
    while current_id is not None:
        if current_id in seen or len(chain) >= 32:
            raise ApiError(422, "invalid_run_parent", "Conversation history is too deep or contains a cycle")
        seen.add(current_id)
        row = db.scalar(select(AgentRun).where(AgentRun.id == current_id, AgentRun.project_id == project_id))
        if row is None:
            raise ApiError(404, "not_found", "Parent run not found in this project")
        if row.status != "completed":
            raise ApiError(409, "parent_run_incomplete", "Continue from a completed run")
        chain.append(row)
        current_id = row.parent_run_id
    history: list[dict[str, str]] = []
    for row in reversed(chain):
        prompt = row.prompt
        if row.selected_context:
            prompt += "\n\nSelected project record context:\n" + json.dumps(
                row.selected_context.get("record", {}), ensure_ascii=False, sort_keys=True)
        history.append({"role": "user", "content": prompt})
        result = row.result if isinstance(row.result, str) else json.dumps(row.result, ensure_ascii=False, default=str)
        history.append({"role": "assistant", "content": result or ""})
    return history


def _tool_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, ApiError):
        return {"error": exc.code, "message": exc.message, "fields": exc.fields or {}}
    return {"error": "internal_error", "message": "The project operation could not be completed"}


def _document_summary(row: Document) -> dict[str, Any]:
    fields = row.fields or {}
    return {"id": str(row.id), "revision": row.revision, "version": row.version,
            "title": fields.get("title", ""), "description": fields.get("description", ""),
            "kind": fields.get("kind", "document"), "tags": fields.get("tags", [])}


def _ticket_summary(row: Ticket) -> dict[str, Any]:
    fields = row.fields or {}
    return {"id": str(row.id), "revision": row.revision, "title": fields.get("title", ""),
            "description": (fields.get("description") or "")[:500], "status": fields.get("status", "planned"),
            "priority": fields.get("priority", "normal"), "tags": fields.get("tags", [])}


def _execute_project_tool(db: Session, run: AgentRun, name: str,
                          arguments: dict[str, Any], call_id: str) -> dict[str, Any]:
    definition = next((tool for tool in OPENAI_TOOLS if tool["name"] == name), None)
    if definition is None:
        return {"error": "unknown_tool", "message": "This project tool is not available"}
    validation_error = next(Draft202012Validator(
        definition["parameters"], format_checker=FormatChecker()).iter_errors(arguments), None)
    if validation_error:
        return {"error": "invalid_arguments", "message": "Tool arguments did not match the expected fields"}
    service.project(db, run.project_id)
    if name == "get_project":
        project = db.get(Project, run.project_id)
        return {"id": str(project.id), "name": project.name, "purpose": project.purpose, "revision": project.revision}
    if name == "list_roles":
        rows = db.scalars(select(AgentRole).where(AgentRole.project_id == run.project_id).order_by(AgentRole.name).limit(100))
        return {"items": [{"id": str(row.id), "name": row.name, "responsibilities": row.responsibilities,
                           "revision": row.revision} for row in rows]}
    if name == "list_tickets":
        limit = arguments.get("limit", 50)
        rows = db.scalars(select(Ticket).where(Ticket.project_id == run.project_id)
                          .order_by(Ticket.updated_at.desc()).limit(limit))
        return {"items": [_ticket_summary(row) for row in rows]}
    if name == "get_ticket":
        row = service.artifact(db, Ticket, run.project_id, UUID(arguments["ticket_id"]))
        return service.serialize(row)
    if name == "list_documents":
        limit = arguments.get("limit", 50)
        rows = db.scalars(select(Document).where(Document.project_id == run.project_id)
                          .order_by(Document.updated_at.desc()).limit(limit))
        return {"items": [_document_summary(row) for row in rows]}
    if name == "get_document":
        row = service.artifact(db, Document, run.project_id, UUID(arguments["document_id"]))
        result = service.serialize(row)
        content = str(result.get("content", ""))
        if len(content) > 12000:
            result["content"] = content[:12000]
            result["content_truncated"] = True
        return result
    if name == "create_ticket":
        validate("TicketCreate", arguments)
        key = "sdk-" + hashlib.sha256(f"{run.id}:{call_id}".encode()).hexdigest()
        return service.create(db, Ticket, run.project_id, arguments, key)
    if name == "create_document":
        validate("DocumentCreate", arguments)
        key = "sdk-" + hashlib.sha256(f"{run.id}:{call_id}".encode()).hexdigest()
        return service.create(db, Document, run.project_id, arguments, key)
    if name in {"propose_update", "propose_delete"}:
        proposal = ChangeProposal(
            operation="update" if name == "propose_update" else "delete",
            target_kind=arguments["target_kind"], target_id=UUID(arguments["target_id"]),
            expected_revision=arguments["expected_revision"],
            changes=arguments.get("changes", {}),
        )
        approval = create_change_proposal(db, run, proposal)
        return {"outcome": "approval_required", "applied": False, "status": approval.status,
                "target_kind": approval.target_kind, "target_id": str(approval.target_id),
                "target_label": approval.target_label, "operation": approval.operation,
                "base_revision": approval.base_revision}
    return {"error": "unknown_tool", "message": "This project tool is not available"}


def _append_run_activity(run_id: UUID, kind: str, text: str) -> None:
    db = SessionLocal()
    try:
        run = db.get(AgentRun, run_id)
        if run is None or run.status in {"cancelled", "completed", "failed"}:
            return
        run.activity = [*(run.activity or []), {"type": kind, "text": text[:1000], "at": utcnow().isoformat()}][-200:]
        run.updated_at = utcnow()
        db.commit()
    finally:
        db.close()


async def _schedule_run(run_id: UUID) -> None:
    task = asyncio.create_task(execute_run(run_id))
    _active_run_tasks[run_id] = task

    def clear(_task: asyncio.Task) -> None:
        _active_run_tasks.pop(run_id, None)

    task.add_done_callback(clear)


async def execute_run(run_id: UUID):
    db = SessionLocal()
    try:
        run = db.get(AgentRun, run_id)
        if run is None or run.status != "queued":
            return
        run.status = "running"
        run.updated_at = utcnow()
        db.commit()
        provider = run.provider
        model = getattr(run, "model", None) or _default_model(provider)
        prompt = run.prompt
        selected_context = getattr(run, "selected_context", None)
        parent_run_id = getattr(run, "parent_run_id", None)
        project_id = run.project_id
    finally:
        db.close()

    def execute_tool(name: str, arguments: dict[str, Any], call_id: str) -> dict[str, Any]:
        tool_db = SessionLocal()
        try:
            tool_run = tool_db.get(AgentRun, run_id)
            if tool_run is None or tool_run.status != "running":
                return {"error": "run_cancelled", "message": "This run is no longer active"}
            return _execute_project_tool(tool_db, tool_run, name, arguments, call_id)
        except Exception as exc:
            tool_db.rollback()
            return _tool_error(exc)
        finally:
            tool_db.close()

    try:
        history_db = SessionLocal()
        try:
            history = _conversation_history(history_db, project_id, parent_run_id)
        finally:
            history_db.close()
        readiness = _provider_readiness()[provider]
        if not readiness["available"]:
            raise ProviderRequestError(readiness["reason"] or "Provider is not ready")
        if selected_context:
            prompt += "\n\nSelected project record context (read-only reference):\n" + json.dumps(
                selected_context.get("record", {}), ensure_ascii=False, sort_keys=True)
        response = await adapter_for(provider, settings.openai_api_key if provider == "codex" else settings.anthropic_api_key).run(
            prompt, model=model, history=history, execute_tool=execute_tool,
            activity=lambda kind, text: _append_run_activity(run_id, kind, text),
        )
        db = SessionLocal()
        try:
            run = db.get(AgentRun, run_id)
            if run is None or run.status == "cancelled":
                return
            run.result = _parse_provider_response(db, run, response)
            run.status = "completed"
            run.error = None
            run.activity = [*(run.activity or []), {"type": "run_completed", "text": "Run completed", "at": utcnow().isoformat()}][-200:]
            run.updated_at = utcnow()
            db.commit()
        finally:
            db.close()
    except asyncio.CancelledError:
        db = SessionLocal()
        try:
            run = db.get(AgentRun, run_id)
            if run is not None and run.status in {"queued", "running"}:
                run.status = "cancelled"
                run.updated_at = utcnow()
                run.activity = [*(run.activity or []), {"type": "run_cancelled", "text": "Run cancelled", "at": utcnow().isoformat()}][-200:]
                db.commit()
        finally:
            db.close()
        raise
    except Exception as exc:
        safe_error = str(exc)[:512] if isinstance(exc, ProviderRequestError) else "Provider run failed"
        db = SessionLocal()
        try:
            run = db.get(AgentRun, run_id)
            if run is not None and run.status != "cancelled":
                run.status = "failed"
                run.error = safe_error
                run.updated_at = utcnow()
                run.activity = [*(run.activity or []), {"type": "run_failed", "text": safe_error, "at": utcnow().isoformat()}][-200:]
                db.commit()
        finally:
            db.close()


@router.post("/projects/{project_id}/runs", status_code=202)
def start_run(project_id: UUID, body: RunCreate, background: BackgroundTasks,
              key: str = Header(alias="Idempotency-Key"), db: Session = Depends(get_db)):
    setting = _workspace_setting(db)
    if not setting.sdk_runs_enabled:
        raise ApiError(403, "sdk_runs_disabled", "SDK runs are disabled for this workspace")
    if db.get(Project, project_id) is None:
        raise ApiError(404, "not_found", "Project not found")
    if (body.context_kind is None) != (body.context_id is None):
        raise ApiError(422, "invalid_run_context", "Choose both a record type and record")
    operation, fresh = reserve(db, f"projects:{project_id}:sdk-run", key, body.model_dump(mode="json"))
    if not fresh:
        return operation.result_json
    selected_context = None
    if body.context_id is not None:
        model = Ticket if body.context_kind == "ticket" else Document
        record = db.scalar(select(model).where(model.project_id == project_id, model.id == body.context_id))
        if record is None:
            raise ApiError(404, "not_found", "Selected project record not found")
        record_fields = dict(record.fields)
        if body.context_kind == "document" and isinstance(record_fields.get("content"), str) and len(record_fields["content"]) > 12000:
            record_fields["content"] = record_fields["content"][:12000]
            record_fields["content_truncated"] = True
        selected_context = {"kind": body.context_kind, "id": str(record.id), "revision": record.revision,
                            "record": {"kind": body.context_kind, "id": str(record.id),
                                       "revision": record.revision, "fields": record_fields}}
    parent = None
    if body.parent_run_id:
        parent = db.scalar(select(AgentRun).where(AgentRun.id == body.parent_run_id, AgentRun.project_id == project_id))
        if parent is None:
            raise ApiError(404, "not_found", "Parent run not found in this project")
        if parent.status != "completed":
            raise ApiError(409, "parent_run_incomplete", "Continue from a completed run")
        if selected_context is None:
            selected_context = parent.selected_context
    provider = body.provider
    readiness = _provider_readiness()[provider]
    if not readiness["available"]:
        raise ApiError(403, "provider_disabled", readiness["reason"] or "Provider is unavailable")
    model = body.model or readiness.get("default_model") or _default_model(provider)
    run = AgentRun(project_id=project_id, provider=provider, model=model,
                   parent_run_id=parent.id if parent else None, prompt=body.prompt,
                   selected_context=selected_context, status="queued", activity=[])
    db.add(run)
    db.flush()
    db.refresh(run)
    operation.result_json = _view(run)
    db.commit()
    background.add_task(_schedule_run, run.id)
    return _view(run)


@router.post("/projects/{project_id}/runs/{run_id}/cancel")
async def cancel_run(project_id: UUID, run_id: UUID, db: Session = Depends(get_db)):
    run = db.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.project_id == project_id).with_for_update())
    if run is None:
        raise ApiError(404, "not_found", "Run not found")
    if run.status in {"completed", "failed", "cancelled"}:
        return {"id": str(run.id), "status": run.status}
    run.status = "cancelled"
    run.error = None
    run.updated_at = utcnow()
    run.activity = [*(run.activity or []), {"type": "run_cancelled", "text": "Run cancelled", "at": utcnow().isoformat()}][-200:]
    db.commit()
    task = _active_run_tasks.get(run.id)
    if task is not None and not task.done():
        asyncio.get_running_loop().call_soon_threadsafe(task.cancel)
    return {"id": str(run.id), "status": run.status}


@router.get("/projects/{project_id}/runs")
def list_runs(project_id: UUID, db: Session = Depends(get_db)):
    return {"items": [_view(row) for row in db.scalars(select(AgentRun).where(
        AgentRun.project_id == project_id).order_by(AgentRun.created_at.desc()).limit(100))]}


@router.get("/projects/{project_id}/runs/{run_id}")
def get_run(project_id: UUID, run_id: UUID, db: Session = Depends(get_db)):
    run = db.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.project_id == project_id))
    if run is None:
        raise ApiError(404, "not_found", "Run not found")
    return _view(run)


def create_change_proposal(db: Session, run: AgentRun, body: ChangeProposal):
    """Called by trusted adapter tool plumbing; never exposed as a browser approval path."""
    if body.target_kind == "ticket":
        model = Ticket
    elif body.target_kind == "document":
        model = Document
    else:
        raise ApiError(422, "unsupported_proposal_kind", f"Unsupported proposal target kind: {body.target_kind}")
    selected = getattr(run, "selected_context", None)
    if selected and (selected["kind"] != body.target_kind or selected["id"] != str(body.target_id)
                     or selected["revision"] != body.expected_revision):
        raise ApiError(422, "proposal_target_mismatch", "Proposal must target the selected record at its selected revision")
    service.project(db, run.project_id, lock=True)
    row = db.scalar(select(model).where(model.project_id == run.project_id, model.id == body.target_id).with_for_update())
    if row is None:
        raise ApiError(404, "not_found", f"{model.__name__} not found")
    service.revision(row, body.expected_revision)
    if body.operation == "update":
        if not body.changes:
            raise ApiError(422, "invalid_proposal", "An update proposal must include changes")
        validate("TicketUpdate" if body.target_kind == "ticket" else "DocumentUpdate",
                 {"expected_revision": body.expected_revision, "changes": body.changes})
    elif body.changes:
        raise ApiError(422, "invalid_proposal", "A delete proposal cannot include changes")
    canonical = json.dumps({"operation": body.operation, "kind": body.target_kind, "id": str(row.id), "revision": row.revision,
                            "changes": body.changes}, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    label = row.fields.get("title") or row.fields.get("name") or row.fields.get("filename") or f"Untitled {body.target_kind}"
    preview = ({field: {"current": (row.fields or {}).get(field), "proposed": value}
                for field, value in body.changes.items()} if body.operation == "update"
               else {"consequence": "This record will be permanently deleted."})
    approval = AgentChangeApproval(run_id=run.id, project_id=run.project_id, target_kind=body.target_kind,
        target_id=row.id, target_label=str(label)[:512], operation=body.operation, base_revision=row.revision,
        proposed_changes=body.changes, change_preview=preview, change_hash=digest, status="pending")
    db.add(approval)
    db.flush()
    db.add(AuditEvent(project_id=run.project_id, actor="agent", action="approval_requested",
                      target_type=body.target_kind, target_id=row.id))
    db.commit()
    return approval


def _parse_provider_response(db: Session, run: AgentRun, response: dict) -> str:
    """Return provider text; mutations use typed tools, never text parsing."""
    text = response.get("text", "") if isinstance(response, dict) else str(response)
    if not isinstance(text, str):
        return json.dumps(text, ensure_ascii=False)
    return text


@router.get("/projects/{project_id}/approvals")
def list_approvals(project_id: UUID, db: Session = Depends(get_db)):
    rows = db.scalars(select(AgentChangeApproval).where(AgentChangeApproval.project_id == project_id)
                      .order_by(AgentChangeApproval.created_at.desc()).limit(100))
    result = []
    for a in rows:
        model = Ticket if a.target_kind == "ticket" else Document
        target = db.scalar(select(model).where(model.project_id == project_id, model.id == a.target_id))
        label = a.target_label
        result.append({"id": str(a.id), "run_id": str(a.run_id), "target_kind": a.target_kind,
        "target_id": str(a.target_id), "target_label": label, "base_revision": a.base_revision, "changes": a.proposed_changes,
        "operation": a.operation, "change_preview": a.change_preview, "change_hash": a.change_hash, "status": a.status, "created_at": a.created_at})
    return {"items": result}


@router.post("/projects/{project_id}/approvals/{approval_id}/decision")
def decide_approval(project_id: UUID, approval_id: UUID, body: ApprovalDecision,
                    key: str = Header(alias="Idempotency-Key"), db: Session = Depends(get_db)):
    decision_hash = hashlib.sha256(json.dumps(body.model_dump(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    # Keep the parent lock first, matching proposal creation and project deletion.
    # Cascading deletion then cannot deadlock with an approval holding the child row.
    service.project(db, project_id, lock=True)
    approval = db.scalar(select(AgentChangeApproval).where(
        AgentChangeApproval.id == approval_id, AgentChangeApproval.project_id == project_id).with_for_update())
    if approval is None:
        raise ApiError(404, "not_found", "Approval request not found")
    if approval.decision_key == key and approval.decision_hash == decision_hash:
        return {"id": str(approval.id), "status": approval.status}
    if approval.decision_key == key:
        raise ApiError(409, "idempotency_key_reused", "Idempotency-Key was reused with a different decision")
    if approval.status != "pending":
        raise ApiError(409, "already_decided", "Approval request has already been decided")
    if body.change_hash != approval.change_hash or body.expected_revision != approval.base_revision:
        raise ApiError(409, "approval_mismatch", "Approval does not match the exact proposed change and revision")
    existing = db.scalar(select(AgentChangeApproval).where(
        AgentChangeApproval.decision_key == key, AgentChangeApproval.id != approval_id))
    if existing is not None:
        raise ApiError(409, "idempotency_key_reused", "Idempotency-Key was used for another approval")
    # The only decision route is protected by the local Origin and CSRF middleware.
    if body.decision == "approve":
        model = Ticket if approval.target_kind == "ticket" else Document
        row = db.scalar(select(model).where(model.project_id == project_id, model.id == approval.target_id).with_for_update())
        if row is None:
            approval.status = "stale"
            approval.decision_key = key
            approval.decision_hash = decision_hash
            approval.decided_by = "browser"
            approval.decided_at = utcnow()
            db.commit()
            raise ApiError(409, "stale_revision", "The proposed record no longer exists")
        try:
            service.revision(row, approval.base_revision)
        except ApiError as exc:
            if exc.status == 409 and exc.code == "stale_revision":
                approval.status = "stale"
                approval.decision_key = key
                approval.decision_hash = decision_hash
                approval.decided_by = "browser"
                approval.decided_at = utcnow()
                db.commit()
            raise
        if approval.operation == "update":
            validate("TicketUpdate" if approval.target_kind == "ticket" else "DocumentUpdate",
                     {"expected_revision": approval.base_revision, "changes": approval.proposed_changes})
            service.update(db, row, approval.proposed_changes, commit=False)
        elif approval.operation == "delete":
            service.invalidate_pending(db, project_id, approval.target_kind, row.id)
            db.add(AuditEvent(project_id=project_id, actor="browser", action="delete",
                              target_type=approval.target_kind, target_id=row.id))
            db.delete(row)
        else:
            raise ApiError(422, "unsupported_proposal_operation", "Unsupported proposal operation")
    approval.status = "approved" if body.decision == "approve" else "rejected"
    approval.decision_key = key
    approval.decision_hash = decision_hash
    approval.decided_by = "browser"
    approval.decided_at = utcnow()
    db.add(AuditEvent(project_id=project_id, actor="browser", action=f"approval_{approval.status}",
                      target_type=approval.target_kind, target_id=approval.target_id))
    db.commit()
    return {"id": str(approval.id), "status": approval.status}
