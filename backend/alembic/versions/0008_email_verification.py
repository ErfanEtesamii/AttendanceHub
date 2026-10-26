"""require verified email for sessions

Revision ID: 0008_email_verification
Revises: 0007_platform_seed
"""
import sqlalchemy as sa
from alembic import op
revision, down_revision, branch_labels, depends_on = "0008_email_verification", "0007_platform_seed", None, None
def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
def downgrade() -> None:
    op.drop_column("users", "email_verified")
