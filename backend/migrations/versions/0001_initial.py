"""Initial PickByMe schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = sa.Enum("CUSTOMER", "CREATOR", "PROVIDER", "ADMIN", name="user_role")
offer_type = sa.Enum(
    "PRODUCT",
    "SERVICE",
    "RESERVATION",
    "STAY",
    "TICKET",
    "EXPERIENCE",
    "OTHER",
    name="offer_type",
)
offer_status = sa.Enum("DRAFT", "ACTIVE", "PAUSED", "ARCHIVED", name="offer_status")
conversion_status = sa.Enum(
    "PENDING",
    "CONFIRMED",
    "CANCELLED",
    "REFUNDED",
    name="conversion_status",
)
commission_status = sa.Enum("PENDING", "EARNED", "PAID", "REVERSED", name="commission_status")


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    offer_type.create(bind, checkfirst=True)
    offer_status.create(bind, checkfirst=True)
    conversion_status.create(bind, checkfirst=True)
    commission_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_auth_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_auth_sessions_token_hash")),
    )
    op.create_index(
        op.f("ix_auth_sessions_expires_at"),
        "auth_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_sessions_token_hash"),
        "auth_sessions",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_auth_sessions_user_id"),
        "auth_sessions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "creator_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_creator_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_creator_profiles")),
        sa.UniqueConstraint("slug", name=op.f("uq_creator_profiles_slug")),
        sa.UniqueConstraint("user_id", name=op.f("uq_creator_profiles_user_id")),
    )
    op.create_index(
        op.f("ix_creator_profiles_slug"),
        "creator_profiles",
        ["slug"],
        unique=True,
    )

    op.create_table(
        "provider_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("business_name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_provider_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_provider_profiles")),
        sa.UniqueConstraint("slug", name=op.f("uq_provider_profiles_slug")),
        sa.UniqueConstraint("user_id", name=op.f("uq_provider_profiles_user_id")),
    )
    op.create_index(
        op.f("ix_provider_profiles_business_name"),
        "provider_profiles",
        ["business_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_provider_profiles_slug"),
        "provider_profiles",
        ["slug"],
        unique=True,
    )

    op.create_table(
        "offers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("offer_type", offer_type, nullable=False),
        sa.Column("status", offer_status, nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("default_creator_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["provider_profiles.id"],
            name=op.f("fk_offers_provider_id_provider_profiles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_offers")),
    )
    op.create_index(op.f("ix_offers_provider_id"), "offers", ["provider_id"], unique=False)
    op.create_index(op.f("ix_offers_status"), "offers", ["status"], unique=False)
    op.create_index(op.f("ix_offers_title"), "offers", ["title"], unique=False)
    op.create_index(op.f("ix_offers_offer_type"), "offers", ["offer_type"], unique=False)

    op.create_table(
        "creator_offers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("creator_id", sa.Uuid(), nullable=False),
        sa.Column("offer_id", sa.Uuid(), nullable=False),
        sa.Column("creator_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("is_featured", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["creator_profiles.id"],
            name=op.f("fk_creator_offers_creator_id_creator_profiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["offer_id"],
            ["offers.id"],
            name=op.f("fk_creator_offers_offer_id_offers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_creator_offers")),
        sa.UniqueConstraint("creator_id", "offer_id", name="uq_creator_offer"),
    )
    op.create_index(
        op.f("ix_creator_offers_creator_id"),
        "creator_offers",
        ["creator_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_creator_offers_offer_id"),
        "creator_offers",
        ["offer_id"],
        unique=False,
    )

    op.create_table(
        "conversions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("offer_id", sa.Uuid(), nullable=False),
        sa.Column("creator_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=True),
        sa.Column("external_reference", sa.String(length=160), nullable=True),
        sa.Column("gross_amount", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", conversion_status, nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["creator_profiles.id"],
            name=op.f("fk_conversions_creator_id_creator_profiles"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["users.id"],
            name=op.f("fk_conversions_customer_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["offer_id"],
            ["offers.id"],
            name=op.f("fk_conversions_offer_id_offers"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversions")),
    )
    op.create_index(
        op.f("ix_conversions_creator_id"),
        "conversions",
        ["creator_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversions_external_reference"),
        "conversions",
        ["external_reference"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversions_offer_id"),
        "conversions",
        ["offer_id"],
        unique=False,
    )
    op.create_index(op.f("ix_conversions_status"), "conversions", ["status"], unique=False)

    op.create_table(
        "commissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversion_id", sa.Uuid(), nullable=False),
        sa.Column("creator_id", sa.Uuid(), nullable=False),
        sa.Column("rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", commission_status, nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["conversion_id"],
            ["conversions.id"],
            name=op.f("fk_commissions_conversion_id_conversions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["creator_profiles.id"],
            name=op.f("fk_commissions_creator_id_creator_profiles"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_commissions")),
        sa.UniqueConstraint("conversion_id", name="uq_commission_conversion"),
    )
    op.create_index(
        op.f("ix_commissions_conversion_id"),
        "commissions",
        ["conversion_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_commissions_creator_id"),
        "commissions",
        ["creator_id"],
        unique=False,
    )
    op.create_index(op.f("ix_commissions_status"), "commissions", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("commissions")
    op.drop_table("conversions")
    op.drop_table("creator_offers")
    op.drop_table("offers")
    op.drop_table("provider_profiles")
    op.drop_table("creator_profiles")
    op.drop_table("auth_sessions")
    op.drop_table("users")

    bind = op.get_bind()
    commission_status.drop(bind, checkfirst=True)
    conversion_status.drop(bind, checkfirst=True)
    offer_status.drop(bind, checkfirst=True)
    offer_type.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
