from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import Base, utcnow


class ArtifactRecord:
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"), index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    fields: Mapped[dict] = mapped_column(JSONB)


class Ticket(ArtifactRecord, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("project_id", "id"),
        ForeignKeyConstraint(["project_id", "role_id"], ["agent_roles.project_id", "agent_roles.id"]),
    )

    role_id: Mapped[UUID | None] = mapped_column(Uuid)


class Document(ArtifactRecord, Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("project_id", "id"),)

    current_version_id: Mapped[UUID] = mapped_column(Uuid)
    version: Mapped[int] = mapped_column(Integer, default=1)


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        ForeignKeyConstraint(["project_id", "document_id"], ["documents.project_id", "documents.id"], ondelete="CASCADE"),
        UniqueConstraint("document_id", "version"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[UUID] = mapped_column(Uuid)
    document_id: Mapped[UUID] = mapped_column(Uuid)
    version: Mapped[int] = mapped_column(Integer)
    fields: Mapped[dict] = mapped_column(JSONB)
    author_client_id: Mapped[UUID | None] = mapped_column(Uuid)
    source: Mapped[str] = mapped_column(String(12))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TicketDocument(Base):
    __tablename__ = "ticket_documents"
    __table_args__ = (
        ForeignKeyConstraint(["project_id", "ticket_id"], ["tickets.project_id", "tickets.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["project_id", "document_id"], ["documents.project_id", "documents.id"], ondelete="CASCADE"),
    )

    project_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    ticket_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    document_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    relationship: Mapped[str] = mapped_column(String(12), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ArtifactOperation(Base):
    __tablename__ = "artifact_operations"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    scope: Mapped[str] = mapped_column(String(128), primary_key=True)
    key: Mapped[str] = mapped_column(String(256), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSONB)
