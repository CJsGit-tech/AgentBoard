"""Persist MCP mutation requests for client-mediated approval."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20261118_0004"
down_revision = "20261118_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mutation_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=True),
        sa.Column("target_kind", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("operation", sa.String(length=16), nullable=False),
        sa.Column("proposed_changes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("base_revision", sa.Integer(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("requester_client_id", sa.Uuid(), nullable=False),
        sa.Column("operation_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "requester_client_id", "operation_key", name="uq_mutation_request_key"),
        sa.CheckConstraint("base_revision >= 1", name="ck_mutation_request_revision"),
        sa.CheckConstraint("status IN ('pending','approved','applied','rejected','cancelled','expired','stale')", name="ck_mutation_request_status"),
        sa.CheckConstraint("operation IN ('update','delete','restore','unlink')", name="ck_mutation_request_operation"),
    )
    op.create_index("ix_mutation_requests_project_status", "mutation_requests", ["project_id", "status"])
    op.create_index("ix_mutation_requests_target_status", "mutation_requests", ["project_id", "target_kind", "target_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_mutation_requests_target_status", table_name="mutation_requests")
    op.drop_index("ix_mutation_requests_project_status", table_name="mutation_requests")
    op.drop_table("mutation_requests")
