from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import CreatorProfile, ProviderProfile, User
from app.db.session import get_db
from app.domain.enums import UserRole
from app.schemas import ProfileRegistrationResponse, RegisterAccountRequest

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    "/register",
    response_model=ProfileRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_account(
    payload: RegisterAccountRequest,
    db: Session = Depends(get_db),
) -> ProfileRegistrationResponse:
    if payload.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin accounts cannot be self-registered")

    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")

    if payload.role in {UserRole.CREATOR, UserRole.PROVIDER} and payload.slug is None:
        raise HTTPException(status_code=422, detail="slug is required for creator/provider accounts")

    if payload.role == UserRole.PROVIDER and payload.business_name is None:
        raise HTTPException(status_code=422, detail="business_name is required for providers")

    normalized_slug = payload.slug.lower() if payload.slug else None
    if normalized_slug is not None:
        creator_slug = db.scalar(select(CreatorProfile).where(CreatorProfile.slug == normalized_slug))
        provider_slug = db.scalar(select(ProviderProfile).where(ProviderProfile.slug == normalized_slug))
        if creator_slug is not None or provider_slug is not None:
            raise HTTPException(status_code=409, detail="Slug is already in use")

    user = User(
        email=payload.email.lower(),
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()

    profile_id = None
    if payload.role == UserRole.CREATOR:
        profile = CreatorProfile(user_id=user.id, slug=normalized_slug, bio=payload.bio)
        db.add(profile)
        db.flush()
        profile_id = profile.id
    elif payload.role == UserRole.PROVIDER:
        profile = ProviderProfile(
            user_id=user.id,
            slug=normalized_slug,
            business_name=payload.business_name.strip(),
        )
        db.add(profile)
        db.flush()
        profile_id = profile.id

    db.commit()
    db.refresh(user)
    return ProfileRegistrationResponse(account=user, profile_id=profile_id, slug=normalized_slug)
