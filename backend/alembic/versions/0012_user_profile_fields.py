"""add user profile and login fields

Revision ID: 0012_user_profile_fields
Revises: 0011_refresh_token_version
"""
import sqlalchemy as sa
from alembic import op
revision, down_revision, branch_labels, depends_on = "0012_user_profile_fields", "0011_refresh_token_version", None, None
def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("two_factor_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.create_index("ix_users_username", "users", ["username"])
def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "two_factor_enabled")
    op.drop_column("users", "phone")
    op.drop_column("users", "username")
