"""add user preferences

Revision ID: 0013_user_preferences
Revises: 0012_user_profile_fields
"""
import sqlalchemy as sa
from alembic import op
revision, down_revision, branch_labels, depends_on = "0013_user_preferences", "0012_user_profile_fields", None, None
def upgrade() -> None:
    op.add_column("users", sa.Column("locale", sa.String(8), nullable=False, server_default="fa"))
    op.add_column("users", sa.Column("theme", sa.String(16), nullable=False, server_default="system"))
def downgrade() -> None:
    op.drop_column("users", "theme")
    op.drop_column("users", "locale")
