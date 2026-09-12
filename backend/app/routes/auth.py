from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token, issue_token, verify_password
from app.db.models import AuthSession, User
from app.db.session import get_db
from app.dependencies import bearer_scheme, get_current_user
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
SESSION_LIFETIME = timedelta(days=30)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    raw_token = issue_token()
    expires_at = datetime.now(timezone.utc) + SESSION_LIFETIME
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=expires_at,
    )
    db.add(auth_session)
    db.commit()

    return TokenResponse(access_token=raw_token, expires_at=expires_at, account=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    token_hash = hash_token(credentials.credentials)
    auth_session = db.scalar(
        select(AuthSession).where(
            AuthSession.user_id == current_user.id,
            AuthSession.token_hash == token_hash,
            AuthSession.revoked.is_(False),
        )
    )
    if auth_session is not None:
        auth_session.revoked = True
        db.commit()
