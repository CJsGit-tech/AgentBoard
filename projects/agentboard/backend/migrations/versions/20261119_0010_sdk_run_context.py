"""Persist optional selected record context for SDK runs."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261119_0010"
down_revision = "20261119_0009"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("agent_runs", sa.Column("selected_context", postgresql.JSONB(), nullable=True))


def downgrade():
    op.drop_column("agent_runs", "selected_context")
