"""Use typed MCP client identities and queryable activity label arrays."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261118_0006"
down_revision = "20261118_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("activity_events", "labels", existing_type=sa.Text(), type_=JSONB(),
                    postgresql_using="labels::jsonb")
    op.alter_column(
        "activity_events", "client_id", existing_type=sa.String(256), type_=sa.Uuid(),
        postgresql_using=(
            "CASE WHEN client_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' "
            "THEN client_id::uuid ELSE NULL END"
        ),
    )


def downgrade():
    op.alter_column("activity_events", "client_id", existing_type=sa.Uuid(), type_=sa.String(256),
                    postgresql_using="client_id::text")
    op.alter_column("activity_events", "labels", existing_type=JSONB(), type_=sa.Text(),
                    postgresql_using="labels::text")
