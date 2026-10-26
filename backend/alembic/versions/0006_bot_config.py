"""create bot configuration

Revision ID: 0006_bot_config
Revises: 0005_invitations
Create Date: 2026-10-26
"""
import sqlalchemy as sa
from alembic import op
revision, down_revision, branch_labels, depends_on = "0006_bot_config", "0005_invitations", None, None
def upgrade() -> None:
    op.create_table("bot_configurations", sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True), sa.Column("mode", sa.String(16), nullable=False), sa.Column("username", sa.String(128)), sa.Column("token_ciphertext", sa.String(1024)), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
def downgrade() -> None:
    op.drop_table("bot_configurations")
