"""Distinguish update and delete SDK approval proposals."""
from alembic import op
import sqlalchemy as sa

revision = "20261119_0009"
down_revision = "20261119_0008"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("agent_change_approvals", sa.Column("operation", sa.String(16), nullable=False,
                                                        server_default="update"))
    op.alter_column("agent_change_approvals", "operation", server_default=None)


def downgrade():
    op.drop_column("agent_change_approvals", "operation")
