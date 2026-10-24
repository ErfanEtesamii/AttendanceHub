"""create refresh tokens and otp challenges

Revision ID: 0002_auth_sessions
Revises: 0001_users
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_auth_sessions"
down_revision = "0001_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("refresh_tokens", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("user_id", sa.Uuid(), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True), sa.PrimaryKeyConstraint("id"), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("token_hash"))
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_table("otp_challenges", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("email", sa.String(320), nullable=False), sa.Column("purpose", sa.String(32), nullable=False), sa.Column("code_hash", sa.String(64), nullable=False), sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_otp_challenges_email", "otp_challenges", ["email"])


def downgrade() -> None:
    op.drop_index("ix_otp_challenges_email", table_name="otp_challenges"); op.drop_table("otp_challenges")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens"); op.drop_table("refresh_tokens")
