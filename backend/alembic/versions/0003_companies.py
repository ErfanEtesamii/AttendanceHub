"""create companies

Revision ID: 0003_companies
Revises: 0002_auth_sessions
Create Date: 2026-10-25
"""
import sqlalchemy as sa
from alembic import op

revision, down_revision, branch_labels, depends_on = "0003_companies", "0002_auth_sessions", None, None

def upgrade() -> None:
    op.create_table("companies", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("name", sa.String(160), nullable=False), sa.Column("slug", sa.String(80), nullable=False, unique=True), sa.Column("timezone", sa.String(64), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)); op.create_index("ix_companies_slug", "companies", ["slug"])
    op.create_table("memberships", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.UniqueConstraint("company_id", "user_id", name="uq_membership_company_user")); op.create_index("ix_memberships_company_id", "memberships", ["company_id"]); op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    op.create_table("attendance_policies", sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True), sa.Column("mode", sa.String(16), nullable=False), sa.Column("allowed_cidr", sa.String(64)), sa.Column("latitude", sa.String(32)), sa.Column("longitude", sa.String(32)), sa.Column("radius_meters", sa.Integer()))

def downgrade() -> None:
    op.drop_table("attendance_policies"); op.drop_index("ix_memberships_user_id", table_name="memberships"); op.drop_index("ix_memberships_company_id", table_name="memberships"); op.drop_table("memberships"); op.drop_index("ix_companies_slug", table_name="companies"); op.drop_table("companies")
