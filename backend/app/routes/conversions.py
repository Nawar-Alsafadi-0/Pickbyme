from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    Commission,
    Conversion,
    CreatorOffer,
    Offer,
    ProviderProfile,
    User,
)
from app.db.session import get_db
from app.dependencies import get_current_user
from app.domain.enums import CommissionStatus, ConversionStatus, UserRole
from app.schemas import ConversionCreateRequest, ConversionResponse
from app.services.commission import calculate_commission

router = APIRouter(prefix="/conversions", tags=["conversions"])


@router.post("", response_model=ConversionResponse, status_code=status.HTTP_201_CREATED)
def create_conversion(
    payload: ConversionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversionResponse:
    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Provider account required")

    provider = db.scalar(select(ProviderProfile).where(ProviderProfile.user_id == current_user.id))
    if provider is None:
        raise HTTPException(status_code=403, detail="Provider profile not found")

    selection = db.scalar(
        select(CreatorOffer).where(CreatorOffer.tracking_code == payload.tracking_code)
    )
    if selection is None:
        raise HTTPException(status_code=404, detail="Tracking code not found")

    offer = db.get(Offer, selection.offer_id)
    if offer is None or offer.provider_id != provider.id:
        raise HTTPException(status_code=403, detail="Offer does not belong to this provider")

    currency = payload.currency.upper()
    if currency != offer.currency.upper():
        raise HTTPException(status_code=422, detail="Currency must match offer currency")

    commission_amount = calculate_commission(payload.gross_amount, selection.creator_rate)
    conversion = Conversion(
        offer_id=offer.id,
        creator_id=selection.creator_id,
        gross_amount=payload.gross_amount,
        currency=currency,
        external_reference=payload.external_reference,
        status=ConversionStatus.CONFIRMED,
    )
    db.add(conversion)
    db.flush()

    commission = Commission(
        conversion_id=conversion.id,
        creator_id=selection.creator_id,
        rate=selection.creator_rate,
        amount=commission_amount,
        currency=currency,
        status=CommissionStatus.EARNED,
    )
    db.add(commission)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conversion already recorded") from exc

    return ConversionResponse(
        id=conversion.id,
        offer_id=conversion.offer_id,
        creator_id=conversion.creator_id,
        gross_amount=conversion.gross_amount,
        currency=conversion.currency,
        status=conversion.status,
        commission_amount=commission.amount,
        commission_rate=commission.rate,
        commission_status=commission.status,
    )
