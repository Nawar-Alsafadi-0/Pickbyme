import secrets
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import CreatorOffer, CreatorProfile, Offer, ProviderProfile, User
from app.db.session import get_db
from app.dependencies import get_current_user
from app.domain.enums import OfferStatus, UserRole
from app.schemas import (
    CreatorOfferResponse,
    CreatorOfferSelectRequest,
    OfferCreateRequest,
    OfferResponse,
)

router = APIRouter(tags=["offers"])


@router.post("/offers", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
def create_offer(
    payload: OfferCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Offer:
    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Provider account required")

    provider = db.scalar(select(ProviderProfile).where(ProviderProfile.user_id == current_user.id))
    if provider is None:
        raise HTTPException(status_code=403, detail="Provider profile not found")

    offer = Offer(
        provider_id=provider.id,
        title=payload.title.strip(),
        description=payload.description,
        offer_type=payload.offer_type,
        status=OfferStatus.ACTIVE if payload.publish else OfferStatus.DRAFT,
        price=payload.price,
        currency=payload.currency.upper(),
        default_creator_rate=payload.default_creator_rate,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.get("/offers", response_model=list[OfferResponse])
def list_active_offers(db: Session = Depends(get_db)) -> list[Offer]:
    return list(
        db.scalars(
            select(Offer)
            .where(Offer.status == OfferStatus.ACTIVE)
            .order_by(Offer.created_at.desc())
        )
    )


@router.post(
    "/creator/offers/{offer_id}",
    response_model=CreatorOfferResponse,
    status_code=status.HTTP_201_CREATED,
)
def select_offer(
    offer_id: UUID,
    payload: CreatorOfferSelectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreatorOfferResponse:
    if current_user.role != UserRole.CREATOR:
        raise HTTPException(status_code=403, detail="Creator account required")

    creator = db.scalar(select(CreatorProfile).where(CreatorProfile.user_id == current_user.id))
    if creator is None:
        raise HTTPException(status_code=403, detail="Creator profile not found")

    offer = db.get(Offer, offer_id)
    if offer is None or offer.status != OfferStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Active offer not found")

    rate = payload.creator_rate if payload.creator_rate is not None else offer.default_creator_rate
    if rate < Decimal(0) or rate > Decimal(100):
        raise HTTPException(status_code=422, detail="creator_rate must be between 0 and 100")

    selection = CreatorOffer(
        creator_id=creator.id,
        offer_id=offer.id,
        creator_rate=rate,
        is_featured=payload.is_featured,
        tracking_code=secrets.token_urlsafe(18),
    )
    db.add(selection)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Creator already selected this offer") from exc

    db.refresh(selection)
    return CreatorOfferResponse(
        id=selection.id,
        creator_id=selection.creator_id,
        offer_id=selection.offer_id,
        creator_rate=selection.creator_rate,
        is_featured=selection.is_featured,
        tracking_code=selection.tracking_code,
    )
