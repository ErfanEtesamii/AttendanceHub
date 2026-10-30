"""Persist authentication rate limit hits.

Revision ID: 0016_rate_limit_hits
Revises: 0015_policy_ranges_geofences
"""

import sqlalchemy as sa
from alembic import op

revision = "0016_rate_limit_hits"
down_revision = "0015_policy_ranges_geofences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rate_limit_hits",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("key", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rate_limit_hits_key", "rate_limit_hits", ["key"])
    op.create_index("ix_rate_limit_hits_created_at", "rate_limit_hits", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_rate_limit_hits_created_at", table_name="rate_limit_hits")
    op.drop_index("ix_rate_limit_hits_key", table_name="rate_limit_hits")
    op.drop_table("rate_limit_hits")
