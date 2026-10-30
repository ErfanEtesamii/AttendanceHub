"""Copy legacy attendance values into normalized tenant tables.

Revision ID: 0017_backfill_policy_children
Revises: 0016_rate_limit_hits
"""

import sqlalchemy as sa
from alembic import op

revision = "0017_backfill_policy_children"
down_revision = "0016_rate_limit_hits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_policy_ip_ranges_company_id", "policy_ip_ranges", ["company_id"])
    op.create_index("ix_policy_ip_ranges_policy_id", "policy_ip_ranges", ["policy_id"])
    op.create_index("ix_policy_geofences_company_id", "policy_geofences", ["company_id"])
    op.create_index("ix_policy_geofences_policy_id", "policy_geofences", ["policy_id"])
    op.create_check_constraint("ck_policy_ip_ranges_tenant", "policy_ip_ranges", "company_id = policy_id")
    op.create_check_constraint("ck_policy_geofences_tenant", "policy_geofences", "company_id = policy_id")
    op.create_check_constraint("ck_policy_geofences_radius", "policy_geofences", "radius_meters BETWEEN 20 AND 5000")

    op.execute(sa.text("""
        INSERT INTO policy_ip_ranges (id, company_id, policy_id, cidr, label)
        SELECT md5(p.company_id::text || chr(58) || 'legacy-ip')::uuid,
               p.company_id, p.company_id, p.allowed_cidr, 'Migrated network'
        FROM attendance_policies AS p
        WHERE p.allowed_cidr IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM policy_ip_ranges AS r WHERE r.company_id = p.company_id
          )
        ON CONFLICT (id) DO NOTHING
    """))
    op.execute(sa.text("""
        INSERT INTO policy_geofences
            (id, company_id, policy_id, name, latitude, longitude, radius_meters)
        SELECT md5(p.company_id::text || chr(58) || 'legacy-geofence')::uuid,
               p.company_id, p.company_id, 'Migrated location',
               p.latitude::double precision, p.longitude::double precision,
               p.radius_meters
        FROM attendance_policies AS p
        WHERE p.latitude ~ '^[-+]?[0-9]+(\\.[0-9]+)?$'
          AND p.longitude ~ '^[-+]?[0-9]+(\\.[0-9]+)?$'
          AND p.latitude::double precision BETWEEN -90 AND 90
          AND p.longitude::double precision BETWEEN -180 AND 180
          AND p.radius_meters BETWEEN 20 AND 5000
          AND NOT EXISTS (
              SELECT 1 FROM policy_geofences AS g WHERE g.company_id = p.company_id
          )
        ON CONFLICT (id) DO NOTHING
    """))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM policy_geofences WHERE id = md5(company_id::text || chr(58) || 'legacy-geofence')::uuid"))
    op.execute(sa.text("DELETE FROM policy_ip_ranges WHERE id = md5(company_id::text || chr(58) || 'legacy-ip')::uuid"))
    op.drop_constraint("ck_policy_geofences_radius", "policy_geofences", type_="check")
    op.drop_constraint("ck_policy_geofences_tenant", "policy_geofences", type_="check")
    op.drop_constraint("ck_policy_ip_ranges_tenant", "policy_ip_ranges", type_="check")
    op.drop_index("ix_policy_geofences_policy_id", table_name="policy_geofences")
    op.drop_index("ix_policy_geofences_company_id", table_name="policy_geofences")
    op.drop_index("ix_policy_ip_ranges_policy_id", table_name="policy_ip_ranges")
    op.drop_index("ix_policy_ip_ranges_company_id", table_name="policy_ip_ranges")
