"""Add creator and offer attribution events."""

from alembic import op
import sqlalchemy as sa

revision = "0002_tracking_events"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tracking_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("creator_profiles.id"), nullable=False),
        sa.Column("creator_offer_id", sa.Integer(), sa.ForeignKey("creator_offers.id"), nullable=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("visitor_id", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tracking_events_creator_id", "tracking_events", ["creator_id"], unique=False)
    op.create_index("ix_tracking_events_creator_offer_id", "tracking_events", ["creator_offer_id"], unique=False)
    op.create_index("ix_tracking_events_order_id", "tracking_events", ["order_id"], unique=False)
    op.create_index("ix_tracking_events_event_type", "tracking_events", ["event_type"], unique=False)
    op.create_index("ix_tracking_events_visitor_id", "tracking_events", ["visitor_id"], unique=False)


def downgrade() -> None:
    op.drop_table("tracking_events")
