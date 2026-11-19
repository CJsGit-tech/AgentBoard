"""Add retained, deduplicated activity events."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261118_0002"
down_revision = "20261118_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "activity_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("dedupe_key", sa.String(256), nullable=False),
        sa.Column("agent_name", sa.String(256), nullable=False),
        sa.Column("client_id", sa.String(256), nullable=True),
        sa.Column("action", sa.String(256), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("summary", sa.String(2048), nullable=False),
        sa.Column("labels", sa.Text(), nullable=False),
        sa.Column("provenance", sa.String(32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_activity_project", ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "dedupe_key", name="uq_activity_project_dedupe"),
    )
    op.create_index("ix_activity_project_received", "activity_events", ["project_id", "received_at"])
    op.create_index("ix_activity_events_received_at", "activity_events", ["received_at"])


def downgrade():
    op.drop_table("activity_events")
