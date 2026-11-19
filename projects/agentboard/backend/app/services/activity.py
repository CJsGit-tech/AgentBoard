from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.db.models import ActivityEvent, AuditEvent, Project, utcnow
from app.mcp.models import MutationRequest

RETENTION_DAYS = 30


def record_activity(
    db: Session, *, project_id: UUID, agent_name: str, action: str, event_type: str,
    outcome: str, dedupe_key: str, ticket_id: UUID | None = None,
    summary: str = "", labels: list[str] | None = None,
    occurred_at: datetime | None = None, provenance: str = "agent_reported",
    client_id: UUID | None = None,
) -> ActivityEvent:
    """Append a redacted event. Call inside the caller's transaction."""
    if db.get(Project, project_id) is None:
        raise ValueError("Project not found")
    if len(summary.encode("utf-8")) > 2048:
        raise ValueError("Activity summary exceeds 2048 bytes")
    if len(dedupe_key) > 256 or len(labels or []) > 16 or any(len(item) > 64 for item in (labels or [])):
        raise ValueError("Activity key or labels exceed configured limits")
    existing = db.scalar(select(ActivityEvent).where(ActivityEvent.project_id == project_id, ActivityEvent.dedupe_key == dedupe_key))
    if existing:
        return existing
    row = ActivityEvent(
        project_id=project_id, ticket_id=ticket_id, dedupe_key=dedupe_key,
        agent_name=agent_name, client_id=client_id, action=action,
        event_type=event_type, outcome=outcome, summary=summary,
        labels=labels or [], provenance=provenance,
        occurred_at=occurred_at or utcnow(), received_at=utcnow(),
    )
    db.add(row)
    db.flush()
    return row


def expire_activity(db: Session, batch_size: int = 500, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=RETENTION_DAYS)

    def batch(model, condition, timestamp):
        return list(db.scalars(
            select(model.id).where(condition).order_by(timestamp).limit(batch_size).with_for_update(skip_locked=True)
        ))

    event_ids = batch(ActivityEvent, ActivityEvent.received_at <= cutoff, ActivityEvent.received_at)
    audit_ids = batch(AuditEvent, AuditEvent.created_at <= cutoff, AuditEvent.created_at)
    expired_ids = batch(
        MutationRequest, (MutationRequest.status == "pending") & (MutationRequest.expires_at <= now),
        MutationRequest.expires_at,
    )
    old_request_ids = batch(
        MutationRequest, (MutationRequest.status != "pending") & (MutationRequest.decided_at <= cutoff),
        MutationRequest.decided_at,
    )
    if expired_ids:
        db.execute(update(MutationRequest).where(MutationRequest.id.in_(expired_ids)).values(
            status="expired", decided_at=now, proposed_changes={}, result=None,
        ))
    for model, ids in ((ActivityEvent, event_ids), (AuditEvent, audit_ids), (MutationRequest, old_request_ids)):
        if ids:
            db.execute(delete(model).where(model.id.in_(ids)))
    count = len(event_ids) + len(audit_ids) + len(expired_ids) + len(old_request_ids)
    if count:
        db.commit()
    return count


def serialize_activity(row: ActivityEvent) -> dict:
    def z(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "id": str(row.id), "project_id": str(row.project_id),
        "ticket_id": str(row.ticket_id) if row.ticket_id else None,
        "agent_client_id": str(row.client_id) if row.client_id else None,
        "agent_name": row.agent_name, "action": row.action, "event_type": row.event_type,
        "outcome": row.outcome, "summary": row.summary, "labels": row.labels,
        "occurred_at": z(row.occurred_at), "received_at": z(row.received_at),
        "provenance": row.provenance,
    }
