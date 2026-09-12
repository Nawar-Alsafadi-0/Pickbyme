"""Add attribution tracking and conversion idempotency.

Revision ID: 0002_attribution_tracking
Revises: 0001_initial
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_attribution_tracking"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "creator_offers",
        sa.Column("tracking_code", sa.String(length=48), nullable=True),
    )
    op.execute(
        "UPDATE creator_offers "
        "SET tracking_code = substr(md5(random()::text || id::text), 1, 24) "
        "WHERE tracking_code IS NULL"
    )
    op.alter_column("creator_offers", "tracking_code", nullable=False)
    op.create_index(
        op.f("ix_creator_offers_tracking_code"),
        "creator_offers",
        ["tracking_code"],
        unique=True,
    )
    op.create_unique_constraint(
        "uq_conversion_external_reference",
        "conversions",
        ["external_reference"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_conversion_external_reference", "conversions", type_="unique")
    op.drop_index(op.f("ix_creator_offers_tracking_code"), table_name="creator_offers")
    op.drop_column("creator_offers", "tracking_code")
