"""Initial PickByMe production schema."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "brand_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("business_name", sa.String(length=160), nullable=False),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("verification_note", sa.Text(), nullable=False),
    )
    op.create_index("ix_brand_profiles_user_id", "brand_profiles", ["user_id"], unique=True)
    op.create_index("ix_brand_profiles_verification_status", "brand_profiles", ["verification_status"], unique=False)

    op.create_table(
        "creator_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("bio", sa.Text(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("verification_note", sa.Text(), nullable=False),
    )
    op.create_index("ix_creator_profiles_user_id", "creator_profiles", ["user_id"], unique=True)
    op.create_index("ix_creator_profiles_slug", "creator_profiles", ["slug"], unique=True)
    op.create_index("ix_creator_profiles_verification_status", "creator_profiles", ["verification_status"], unique=False)

    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brand_profiles.id"), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("creator_commission_bps", sa.Integer(), nullable=False),
        sa.Column("platform_fee_bps", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_offers_brand_id", "offers", ["brand_id"], unique=False)
    op.create_index("ix_offers_title", "offers", ["title"], unique=False)
    op.create_index("ix_offers_status", "offers", ["status"], unique=False)

    op.create_table(
        "creator_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("creator_profiles.id"), nullable=False),
        sa.Column("offer_id", sa.Integer(), sa.ForeignKey("offers.id"), nullable=False),
        sa.Column("tracking_code", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("creator_id", "offer_id", name="uq_creator_offer"),
    )
    op.create_index("ix_creator_offers_creator_id", "creator_offers", ["creator_id"], unique=False)
    op.create_index("ix_creator_offers_offer_id", "creator_offers", ["offer_id"], unique=False)
    op.create_index("ix_creator_offers_tracking_code", "creator_offers", ["tracking_code"], unique=True)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creator_offer_id", sa.Integer(), sa.ForeignKey("creator_offers.id"), nullable=False),
        sa.Column("offer_id", sa.Integer(), sa.ForeignKey("offers.id"), nullable=False),
        sa.Column("buyer_name", sa.String(length=120), nullable=False),
        sa.Column("buyer_email", sa.String(length=255), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payment_provider", sa.String(length=40), nullable=False),
        sa.Column("payment_reference", sa.String(length=160), nullable=False),
        sa.Column("checkout_key", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("refunded_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_orders_creator_offer_id", "orders", ["creator_offer_id"], unique=False)
    op.create_index("ix_orders_offer_id", "orders", ["offer_id"], unique=False)
    op.create_index("ix_orders_status", "orders", ["status"], unique=False)
    op.create_index("ix_orders_checkout_key", "orders", ["checkout_key"], unique=True)

    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_reference", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("checkout_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_payment_attempts_order_id", "payment_attempts", ["order_id"], unique=False)
    op.create_index("ix_payment_attempts_provider", "payment_attempts", ["provider"], unique=False)
    op.create_index("ix_payment_attempts_provider_reference", "payment_attempts", ["provider_reference"], unique=True)
    op.create_index("ix_payment_attempts_status", "payment_attempts", ["status"], unique=False)

    op.create_table(
        "payouts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("creator_profiles.id"), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payout_method", sa.String(length=40), nullable=False),
        sa.Column("payout_reference", sa.String(length=160), nullable=False),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_payouts_creator_id", "payouts", ["creator_id"], unique=False)
    op.create_index("ix_payouts_status", "payouts", ["status"], unique=False)

    op.create_table(
        "commissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("creator_profiles.id"), nullable=False),
        sa.Column("payout_id", sa.Integer(), sa.ForeignKey("payouts.id"), nullable=True),
        sa.Column("creator_amount_minor", sa.Integer(), nullable=False),
        sa.Column("platform_amount_minor", sa.Integer(), nullable=False),
        sa.Column("brand_net_minor", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_commissions_order_id", "commissions", ["order_id"], unique=True)
    op.create_index("ix_commissions_creator_id", "commissions", ["creator_id"], unique=False)
    op.create_index("ix_commissions_payout_id", "commissions", ["payout_id"], unique=False)
    op.create_index("ix_commissions_status", "commissions", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("commissions")
    op.drop_table("payouts")
    op.drop_table("payment_attempts")
    op.drop_table("orders")
    op.drop_table("creator_offers")
    op.drop_table("offers")
    op.drop_table("creator_profiles")
    op.drop_table("brand_profiles")
    op.drop_table("users")
