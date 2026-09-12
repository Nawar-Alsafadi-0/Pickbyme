from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Commission, Conversion, CreatorProfile, Offer, ProviderProfile, User
from app.db.session import get_db
from app.dependencies import get_current_user
from app.domain.enums import UserRole
from app.schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/creator", response_model=DashboardSummary)
def creator_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardSummary:
    if current_user.role != UserRole.CREATOR:
        raise HTTPException(status_code=403, detail="Creator account required")

    creator = db.scalar(select(CreatorProfile).where(CreatorProfile.user_id == current_user.id))
    if creator is None:
        raise HTTPException(status_code=403, detail="Creator profile not found")

    conversions, gross_amount = db.execute(
        select(func.count(Conversion.id), func.coalesce(func.sum(Conversion.gross_amount), 0)).where(
            Conversion.creator_id == creator.id
        )
    ).one()
    commission_amount = db.scalar(
        select(func.coalesce(func.sum(Commission.amount), 0)).where(
            Commission.creator_id == creator.id
        )
    )

    return DashboardSummary(
        conversions=int(conversions or 0),
        gross_amount=Decimal(str(gross_amount or 0)),
        commission_amount=Decimal(str(commission_amount or 0)),
    )


@router.get("/provider", response_model=DashboardSummary)
def provider_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardSummary:
    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Provider account required")

    provider = db.scalar(select(ProviderProfile).where(ProviderProfile.user_id == current_user.id))
    if provider is None:
        raise HTTPException(status_code=403, detail="Provider profile not found")

    conversions, gross_amount, commission_amount = db.execute(
        select(
            func.count(Conversion.id),
            func.coalesce(func.sum(Conversion.gross_amount), 0),
            func.coalesce(func.sum(Commission.amount), 0),
        )
        .join(Offer, Conversion.offer_id == Offer.id)
        .join(Commission, Commission.conversion_id == Conversion.id)
        .where(Offer.provider_id == provider.id)
    ).one()

    return DashboardSummary(
        conversions=int(conversions or 0),
        gross_amount=Decimal(str(gross_amount or 0)),
        commission_amount=Decimal(str(commission_amount or 0)),
    )
