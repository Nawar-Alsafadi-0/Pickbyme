from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CreatorOffer, CreatorProfile, Offer, User
from app.db.session import get_db
from app.domain.enums import OfferStatus
from app.schemas import PublicCreatorOffer, PublicCreatorPage

router = APIRouter(prefix="/creators", tags=["creators"])


@router.get("/{slug}", response_model=PublicCreatorPage)
def public_creator_page(slug: str, db: Session = Depends(get_db)) -> PublicCreatorPage:
    creator = db.scalar(select(CreatorProfile).where(CreatorProfile.slug == slug.lower()))
    if creator is None:
        raise HTTPException(status_code=404, detail="Creator not found")

    user = db.get(User, creator.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=404, detail="Creator not found")

    rows = db.execute(
        select(CreatorOffer, Offer)
        .join(Offer, CreatorOffer.offer_id == Offer.id)
        .where(
            CreatorOffer.creator_id == creator.id,
            Offer.status == OfferStatus.ACTIVE,
        )
        .order_by(CreatorOffer.is_featured.desc(), CreatorOffer.created_at.desc())
    ).all()

    offers = [
        PublicCreatorOffer(
            id=offer.id,
            title=offer.title,
            description=offer.description,
            offer_type=offer.offer_type,
            price=offer.price,
            currency=offer.currency,
            is_featured=selection.is_featured,
        )
        for selection, offer in rows
    ]

    return PublicCreatorPage(
        creator_id=creator.id,
        slug=creator.slug,
        display_name=user.display_name,
        bio=creator.bio,
        offers=offers,
    )
