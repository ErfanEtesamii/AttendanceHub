"""add company suspension status

Revision ID: 0009_company_status
Revises: 0008_email_verification
"""
import sqlalchemy as sa
from alembic import op
revision, down_revision, branch_labels, depends_on = "0009_company_status", "0008_email_verification", None, None
def upgrade() -> None:
    op.add_column("companies", sa.Column("status", sa.String(16), nullable=False, server_default="active"))
def downgrade() -> None:
    op.drop_column("companies", "status")
