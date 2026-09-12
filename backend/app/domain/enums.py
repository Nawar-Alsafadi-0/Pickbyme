from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "customer"
    CREATOR = "creator"
    PROVIDER = "provider"
    ADMIN = "admin"


class OfferType(StrEnum):
    PRODUCT = "product"
    SERVICE = "service"
    RESERVATION = "reservation"
    STAY = "stay"
    TICKET = "ticket"
    EXPERIENCE = "experience"
    OTHER = "other"


class OfferStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ConversionStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class CommissionStatus(StrEnum):
    PENDING = "pending"
    EARNED = "earned"
    PAID = "paid"
    REVERSED = "reversed"
