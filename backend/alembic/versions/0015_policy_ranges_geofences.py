"""add normalized policy ranges and geofences

Revision ID: 0015_policy_ranges_geofences
Revises: 0014_company_membership_metadata
"""
import sqlalchemy as sa
from alembic import op
revision, down_revision, branch_labels, depends_on = "0015_policy_ranges_geofences", "0014_company_membership_metadata", None, None
def upgrade() -> None:
    op.add_column("attendance_policies", sa.Column("max_accuracy_meters", sa.Integer(), nullable=False, server_default="50"))
    op.add_column("attendance_policies", sa.Column("max_fix_age_seconds", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("attendance_policies", sa.Column("updated_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.create_table("policy_ip_ranges", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False), sa.Column("policy_id", sa.Uuid(), sa.ForeignKey("attendance_policies.company_id", ondelete="CASCADE"), nullable=False), sa.Column("cidr", sa.String(64), nullable=False), sa.Column("label", sa.String(100)))
    op.create_table("policy_geofences", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False), sa.Column("policy_id", sa.Uuid(), sa.ForeignKey("attendance_policies.company_id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(100), nullable=False), sa.Column("latitude", sa.Float(), nullable=False), sa.Column("longitude", sa.Float(), nullable=False), sa.Column("radius_meters", sa.Integer(), nullable=False))
def downgrade() -> None:
    op.drop_table("policy_geofences"); op.drop_table("policy_ip_ranges"); op.drop_column("attendance_policies", "updated_by"); op.drop_column("attendance_policies", "max_fix_age_seconds"); op.drop_column("attendance_policies", "max_accuracy_meters")
