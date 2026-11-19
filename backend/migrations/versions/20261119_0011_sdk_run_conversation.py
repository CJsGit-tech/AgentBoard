"""Persist SDK model selection and parent conversation links."""
from alembic import op
import sqlalchemy as sa


revision = "20261119_0011"
down_revision = "20261119_0010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("agent_runs", sa.Column("model", sa.String(length=128), nullable=True))
    op.add_column("agent_runs", sa.Column("parent_run_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_agent_runs_parent_run_id_agent_runs",
        "agent_runs",
        "agent_runs",
        ["parent_run_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("fk_agent_runs_parent_run_id_agent_runs", "agent_runs", type_="foreignkey")
    op.drop_column("agent_runs", "parent_run_id")
    op.drop_column("agent_runs", "model")
