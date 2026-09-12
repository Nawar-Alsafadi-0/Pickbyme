from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import OfferStatus, OfferType, UserRole


class RegisterAccountRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    display_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    slug: str | None = Field(default=None, min_length=3, max_length=100, pattern=r"^[a-z0-9-]+$")
    business_name: str | None = Field(default=None, min_length=2, max_length=160)
    bio: str | None = Field(default=None, max_length=1000)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    role: UserRole


class ProfileRegistrationResponse(BaseModel):
    account: AccountResponse
    profile_id: UUID | None = None
    slug: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    account: AccountResponse


class OfferCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=5000)
    offer_type: OfferType
    price: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="OMR", min_length=3, max_length=3)
    default_creator_rate: Decimal = Field(default=Decimal("10.00"), ge=0, le=100)
    publish: bool = False


class OfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    title: str
    description: str | None
    offer_type: OfferType
    status: OfferStatus
    price: Decimal | None
    currency: str
    default_creator_rate: Decimal


class CreatorOfferSelectRequest(BaseModel):
    creator_rate: Decimal | None = Field(default=None, ge=0, le=100)
    is_featured: bool = False


class CreatorOfferResponse(BaseModel):
    id: UUID
    creator_id: UUID
    offer_id: UUID
    creator_rate: Decimal
    is_featured: bool


class PublicCreatorOffer(BaseModel):
    id: UUID
    title: str
    description: str | None
    offer_type: OfferType
    price: Decimal | None
    currency: str
    is_featured: bool


class PublicCreatorPage(BaseModel):
    creator_id: UUID
    slug: str
    display_name: str
    bio: str | None
    offers: list[PublicCreatorOffer]
