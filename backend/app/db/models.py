from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums import CommissionStatus, ConversionStatus, OfferStatus, OfferType, UserRole


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AuthSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auth_sessions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[object] = mapped_column(index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class CreatorProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "creator_profiles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProviderProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provider_profiles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    business_name: Mapped[str] = mapped_column(String(160), index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)


class Offer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "offers"

    provider_id: Mapped[UUID] = mapped_column(ForeignKey("provider_profiles.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(180), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    offer_type: Mapped[OfferType] = mapped_column(Enum(OfferType, name="offer_type"), index=True)
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus, name="offer_status"), default=OfferStatus.DRAFT, index=True
    )
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="OMR")
    default_creator_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("10.00"))


class CreatorOffer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "creator_offers"
    __table_args__ = (UniqueConstraint("creator_id", "offer_id", name="uq_creator_offer"),)

    creator_id: Mapped[UUID] = mapped_column(ForeignKey("creator_profiles.id", ondelete="CASCADE"), index=True)
    offer_id: Mapped[UUID] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"), index=True)
    creator_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tracking_code: Mapped[str] = mapped_column(String(48), unique=True, index=True)


class Conversion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversions"
    __table_args__ = (UniqueConstraint("external_reference", name="uq_conversion_external_reference"),)

    offer_id: Mapped[UUID] = mapped_column(ForeignKey("offers.id", ondelete="RESTRICT"), index=True)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("creator_profiles.id", ondelete="RESTRICT"), index=True)
    customer_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    external_reference: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    currency: Mapped[str] = mapped_column(String(3), default="OMR")
    status: Mapped[ConversionStatus] = mapped_column(
        Enum(ConversionStatus, name="conversion_status"), default=ConversionStatus.PENDING, index=True
    )


class Commission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commissions"
    __table_args__ = (UniqueConstraint("conversion_id", name="uq_commission_conversion"),)

    conversion_id: Mapped[UUID] = mapped_column(ForeignKey("conversions.id", ondelete="CASCADE"), index=True)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("creator_profiles.id", ondelete="RESTRICT"), index=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    currency: Mapped[str] = mapped_column(String(3), default="OMR")
    status: Mapped[CommissionStatus] = mapped_column(
        Enum(CommissionStatus, name="commission_status"), default=CommissionStatus.PENDING, index=True
    )
