from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AgentRole(Base):
    __tablename__ = "agent_roles"
    __table_args__ = (
        ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT", name="fk_roles_project"),
        UniqueConstraint("project_id", "id", name="uq_roles_project_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    responsibilities: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    project_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False, default="browser")
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class ActivityEvent(Base):
    __tablename__ = "activity_events"
    __table_args__ = (
        ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE", name="fk_activity_project"),
        UniqueConstraint("project_id", "dedupe_key", name="uq_activity_project_dedupe"),
        Index("ix_activity_project_received", "project_id", "received_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    ticket_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(256), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(256), nullable=False)
    client_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    action: Mapped[str] = mapped_column(String(256), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    labels: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    provenance: Mapped[str] = mapped_column(String(32), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("scope", "key", name="uq_idempotency_scope_key"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    scope: Mapped[str] = mapped_column(String(256), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
                      Index("ix_agent_runs_project_created", "project_id", "created_at"))
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    provider: Mapped[str] = mapped_column(String(24), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128))
    parent_run_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("agent_runs.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued")
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    selected_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    activity: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    result: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class WorkspaceSetting(Base):
    __tablename__ = "workspace_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    sdk_runs_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AgentChangeApproval(Base):
    __tablename__ = "agent_change_approvals"
    __table_args__ = (ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="CASCADE"),
                      Index("ix_agent_change_approvals_project_status", "project_id", "status"))
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    project_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    target_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    target_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    target_label: Mapped[str] = mapped_column(String(512), nullable=False)
    operation: Mapped[str] = mapped_column(String(16), nullable=False, default="update")
    base_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    proposed_changes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    change_preview: Mapped[dict] = mapped_column(JSONB, nullable=False)
    change_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    decision_key: Mapped[str | None] = mapped_column(String(128), unique=True)
    decision_hash: Mapped[str | None] = mapped_column(String(64))
    decided_by: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
