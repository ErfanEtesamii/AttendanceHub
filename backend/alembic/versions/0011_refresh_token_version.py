"""track user token version on refresh sessions

Revision ID: 0011_refresh_token_version
Revises: 0010_harden_otp_challenges
"""
import sqlalchemy as sa
from alembic import op
revision, down_revision, branch_labels, depends_on = "0011_refresh_token_version", "0010_harden_otp_challenges", None, None
def upgrade() -> None:
    op.add_column("refresh_tokens", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
def downgrade() -> None:
    op.drop_column("refresh_tokens", "token_version")
