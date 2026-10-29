"""add company and membership metadata

Revision ID: 0014_company_membership_metadata
Revises: 0013_user_preferences
"""
import sqlalchemy as sa
from alembic import op
revision, down_revision, branch_labels, depends_on = "0014_company_membership_metadata", "0013_user_preferences", None, None
def upgrade() -> None:
    for name, type_ in [("name_en", sa.String(160)), ("industry", sa.String(100)), ("employee_count_range", sa.String(32)), ("city", sa.String(100)), ("phone", sa.String(32)), ("registration_id", sa.String(64)), ("logo_path", sa.String(512))]: op.add_column("companies", sa.Column(name, type_, nullable=True))
    op.add_column("companies", sa.Column("is_system_seeded", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("companies", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("memberships", sa.Column("status", sa.String(16), nullable=False, server_default="active"))
    op.add_column("memberships", sa.Column("manager_id", sa.Uuid(), sa.ForeignKey("memberships.id", ondelete="SET NULL"), nullable=True))
    op.add_column("memberships", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
def downgrade() -> None:
    for name in ["created_at", "manager_id", "status"]: op.drop_column("memberships", name)
    for name in ["updated_at", "is_system_seeded", "logo_path", "registration_id", "phone", "city", "employee_count_range", "industry", "name_en"]: op.drop_column("companies", name)
