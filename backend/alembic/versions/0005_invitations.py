"""create invitations

Revision ID: 0005_invitations
Revises: 0004_audit_logs
Create Date: 2026-10-26
"""
import sqlalchemy as sa
from alembic import op

revision, down_revision, branch_labels, depends_on = "0005_invitations", "0004_audit_logs", None, None

def upgrade() -> None:
    op.create_table("invitations", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False), sa.Column("email", sa.String(320), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False, unique=True), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("accepted_at", sa.DateTime(timezone=True))); op.create_index("ix_invitations_company_id", "invitations", ["company_id"]); op.create_index("ix_invitations_email", "invitations", ["email"])

def downgrade() -> None:
    op.drop_index("ix_invitations_email", table_name="invitations"); op.drop_index("ix_invitations_company_id", table_name="invitations"); op.drop_table("invitations")
