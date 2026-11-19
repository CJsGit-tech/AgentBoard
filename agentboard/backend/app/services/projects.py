from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.artifacts.models import ArtifactOperation, Document, DocumentVersion, Ticket, TicketDocument
from app.db.models import ActivityEvent, AgentRole


def delete_project_records(db: Session, project_id: UUID) -> None:
    """Delete project-owned records in FK order; caller owns the transaction."""
    # These rows carry composite project-scoped foreign keys and must go first.
    db.execute(delete(TicketDocument).where(TicketDocument.project_id == project_id))
    db.execute(delete(DocumentVersion).where(DocumentVersion.project_id == project_id))
    db.execute(delete(Ticket).where(Ticket.project_id == project_id))
    db.execute(delete(Document).where(Document.project_id == project_id))
    db.execute(delete(AgentRole).where(AgentRole.project_id == project_id))
    db.execute(delete(ArtifactOperation).where(ArtifactOperation.project_id == project_id))
    # Activity is also declared ON DELETE CASCADE; deleting explicitly keeps
    # behavior consistent on databases that do not enforce FK cascades.
    db.execute(delete(ActivityEvent).where(ActivityEvent.project_id == project_id))
