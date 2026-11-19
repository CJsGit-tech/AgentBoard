import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261118_0003"
down_revision = "20261118_0002"
branch_labels = None
depends_on = None


def artifact_columns():
    return (
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fields", JSONB(), nullable=False),
        sa.UniqueConstraint("project_id", "id"),
    )


def upgrade():
    op.create_table(
        "tickets", *artifact_columns(), sa.Column("role_id", sa.Uuid()),
        sa.ForeignKeyConstraint(["project_id", "role_id"], ["agent_roles.project_id", "agent_roles.id"]),
    )
    op.create_index("ix_tickets_project_id", "tickets", ["project_id"])
    op.create_table(
        "documents", *artifact_columns(),
        sa.Column("current_version_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    )
    op.create_index("ix_documents_project_id", "documents", ["project_id"])
    op.create_table(
        "document_versions", sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("fields", JSONB(), nullable=False),
        sa.Column("author_client_id", sa.Uuid()),
        sa.Column("source", sa.String(12), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id", "document_id"], ["documents.project_id", "documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("document_id", "version"),
    )
    op.create_table(
        "ticket_documents",
        sa.Column("project_id", sa.Uuid(), primary_key=True),
        sa.Column("ticket_id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), primary_key=True),
        sa.Column("relationship", sa.String(12), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id", "ticket_id"], ["tickets.project_id", "tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id", "document_id"], ["documents.project_id", "documents.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "artifact_operations",
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("scope", sa.String(128), primary_key=True),
        sa.Column("key", sa.String(256), primary_key=True),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("result", JSONB(), nullable=False),
    )


def downgrade():
    for table in ("artifact_operations", "ticket_documents", "document_versions", "documents", "tickets"):
        op.drop_table(table)
