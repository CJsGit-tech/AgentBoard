import hashlib
import importlib.util
import json
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.artifacts import service
from app.artifacts.contracts import validate
from app.artifacts.models import Document, Ticket
from app.db.models import AgentChangeApproval, AgentRun, AuditEvent, Project, WorkspaceSetting, utcnow
from app.db.session import SessionLocal, get_db
from app.sdk.adapters import adapter_for
from app.services.idempotency import reserve
from app.settings import settings

router = APIRouter(prefix="/api/v1")


def _workspace_setting(db: Session):
    setting = db.get(WorkspaceSetting, 1)
    if setting is None:
        setting = WorkspaceSetting(id=1, sdk_runs_enabled=False)
        db.add(setting)
        db.flush()
    return setting


def _provider_readiness():
    codex_installed = importlib.util.find_spec("openai_codex") is not None
    claude_installed = importlib.util.find_spec("claude_agent_sdk") is not None
    codex_configured = bool(settings.openai_api_key and settings.openai_api_key.strip())
    claude_configured = bool(settings.anthropic_api_key and settings.anthropic_api_key.strip())
    codex_enabled = settings.codex_sdk_enabled
    claude_enabled = settings.claude_agent_sdk_enabled

    def provider_state(enabled, installed, configured, label):
        if not enabled:
            return {"available": False, "reason": "Disabled by server configuration"}
        if not installed:
            return {"available": False, "reason": f"{label} SDK package is not installed"}
        if not configured:
            return {"available": False, "reason": f"{label} API credential is not configured"}
        return {"available": True, "reason": None}

    return {
        "codex": provider_state(codex_enabled, codex_installed, codex_configured, "Codex"),
        "claude": provider_state(claude_enabled, claude_installed, claude_configured, "Claude Agent"),
    }


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
    provider: Literal["codex", "claude"]
    prompt: str = Field(min_length=1, max_length=20000)
    context_kind: Literal["ticket", "document"] | None = None
    context_id: UUID | None = None


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
            "status": run.status, "activity": run.activity, "result": run.result, "error": run.error,
            "created_at": run.created_at.isoformat(), "updated_at": run.updated_at.isoformat()}


async def execute_run(run_id: UUID):
    db = SessionLocal()
    run = db.get(AgentRun, run_id)
    if run is None or run.status != "queued":
        db.close()
        return
    run.status = "running"
    db.commit()

    def emit(kind: str, text: str):
        run.activity = [*run.activity, {"type": kind, "text": text, "at": utcnow().isoformat()}][-200:]
        db.commit()
    try:
        readiness = _provider_readiness()[run.provider]
        if not readiness["available"]:
            raise RuntimeError(readiness["reason"] or "Provider is not ready")
        prompt = run.prompt
        if run.selected_context:
            prompt += "\n\nSelected project record context (read-only reference):\n" + json.dumps(run.selected_context["record"], ensure_ascii=False, sort_keys=True)
        prompt += (
            "\n\nAgentBoard output protocol: Return ordinary user-facing responses as plain text. "
            "To propose a change to an existing project record, return exactly one JSON object and "
            'no surrounding prose: {"agentboard":{"type":"proposal","operation":"update"|"delete",'
            '"target_kind":"ticket"|"document","target_id":"UUID","expected_revision":1,"changes":{...}}}. '
            "When a selected project record is supplied above, use its id as target_id and its kind and revision. "
            "For update, changes must contain only fields to update. For delete, changes must be {}. "
            "This only requests human approval; never claim it was applied. The server validates and "
            "stores proposals, and only a paired browser can decide."
        )
        response = await adapter_for(run.provider).run(prompt, activity=emit)
        run.result = _parse_provider_response(db, run, response)
        run.status = "completed"
        emit("run_completed", "Run completed")
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)[:512]
        emit("run_failed", run.error)
    finally:
        db.commit()
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
    if not _provider_readiness()[body.provider]["available"]:
        raise ApiError(403, "provider_disabled", _provider_readiness()[body.provider]["reason"] or "Provider is unavailable")
    selected_context = None
    if body.context_id is not None:
        model = Ticket if body.context_kind == "ticket" else Document
        record = db.scalar(select(model).where(model.project_id == project_id, model.id == body.context_id))
        if record is None:
            raise ApiError(404, "not_found", "Selected project record not found")
        selected_context = {"kind": body.context_kind, "id": str(record.id), "revision": record.revision,
                            "record": {"kind": body.context_kind, "id": str(record.id),
                                       "revision": record.revision, "fields": record.fields}}
    run = AgentRun(project_id=project_id, provider=body.provider, prompt=body.prompt, selected_context=selected_context, status="queued", activity=[])
    db.add(run)
    db.flush()
    db.refresh(run)
    operation.result_json = _view(run)
    db.commit()
    background.add_task(execute_run, run.id)
    return _view(run)


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
    """Parse one explicitly marked envelope; all other provider text remains text."""
    text = response.get("text", "") if isinstance(response, dict) else str(response)
    if not isinstance(text, str):
        return json.dumps(text, ensure_ascii=False)
    try:
        envelope = json.loads(text)
    except (ValueError, TypeError):
        return text
    if not isinstance(envelope, dict) or set(envelope) != {"agentboard"}:
        return text
    payload = envelope["agentboard"]
    if not isinstance(payload, dict) or payload.get("type") != "proposal":
        return text
    proposal = ChangeProposal.supported(payload)
    approval = create_change_proposal(db, run, proposal)
    return f"Proposal submitted for browser approval: {proposal.operation} {proposal.target_kind} '{approval.target_label}' (revision {approval.base_revision})."


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
    # The only decision route is protected by the paired browser session and CSRF middleware.
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
