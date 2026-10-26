"""add platform role needed for platform administration

Revision ID: 0007_platform_seed
Revises: 0006_bot_config
Create Date: 2026-10-26
"""
import sqlalchemy as sa
from alembic import op

revision, down_revision, branch_labels, depends_on = "0007_platform_seed", "0006_bot_config", None, None


def upgrade() -> None:
    op.add_column("users", sa.Column("platform_role", sa.String(32), nullable=False, server_default="user"))


def downgrade() -> None:
    op.drop_column("users", "platform_role")
