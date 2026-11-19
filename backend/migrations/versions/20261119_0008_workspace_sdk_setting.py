"""Persist workspace SDK run enablement."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261119_0008"
down_revision = "20261119_0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "workspace_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sdk_runs_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_workspace_settings_singleton"),
    )
    op.execute("INSERT INTO workspace_settings (id, sdk_runs_enabled, updated_at) VALUES (1, false, now())")
    op.add_column("agent_change_approvals", sa.Column("target_label", sa.String(512), nullable=True))
    op.add_column("agent_change_approvals", sa.Column("change_preview", postgresql.JSONB(), nullable=True))
    op.execute("UPDATE agent_change_approvals SET target_label = target_kind || ' ' || left(target_id::text, 8), change_preview = proposed_changes")
    op.alter_column("agent_change_approvals", "target_label", nullable=False)
    op.alter_column("agent_change_approvals", "change_preview", nullable=False)


def downgrade():
    op.drop_column("agent_change_approvals", "change_preview")
    op.drop_column("agent_change_approvals", "target_label")
    op.drop_table("workspace_settings")
