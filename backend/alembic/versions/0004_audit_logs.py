"""create audit logs

Revision ID: 0004_audit_logs
Revises: 0003_companies
Create Date: 2026-10-26
"""
import sqlalchemy as sa
from alembic import op

revision, down_revision, branch_labels, depends_on = "0004_audit_logs", "0003_companies", None, None

def upgrade() -> None:
    op.create_table("audit_logs", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False), sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("action", sa.String(100), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)); op.create_index("ix_audit_logs_company_id", "audit_logs", ["company_id"])

def downgrade() -> None:
    op.drop_index("ix_audit_logs_company_id", table_name="audit_logs"); op.drop_table("audit_logs")
