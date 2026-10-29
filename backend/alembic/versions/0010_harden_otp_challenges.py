"""harden OTP lifecycle

Revision ID: 0010_harden_otp_challenges
Revises: 0009_company_status
"""
import sqlalchemy as sa
from alembic import op

revision, down_revision, branch_labels, depends_on = "0010_harden_otp_challenges", "0009_company_status", None, None

def upgrade() -> None:
    op.add_column("otp_challenges", sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("otp_challenges", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_otp_challenges_email_purpose_created", "otp_challenges", ["email", "purpose", "created_at"])

def downgrade() -> None:
    op.drop_index("ix_otp_challenges_email_purpose_created", table_name="otp_challenges")
    op.drop_column("otp_challenges", "created_at")
    op.drop_column("otp_challenges", "invalidated_at")
