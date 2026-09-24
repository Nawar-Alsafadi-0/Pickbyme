from contextlib import asynccontextmanager
from datetime import datetime
import os
import re
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import BrandProfile, Commission, CreatorOffer, CreatorProfile, Offer, Order, Payout, User
from .security import create_access_token, decode_access_token, hash_password, verify_password


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value or secrets.token_hex(3)


def require_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
        user = db.get(User, int(payload["sub"]))
    except Exception:
        user = None
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="Invalid, expired, or disabled account")
    return user


def require_role(*roles: str):
    def dependency(user: User = Depends(require_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return dependency


def profile_for_user(db: Session, user: User):
    if user.role == "brand":
        return db.scalar(select(BrandProfile).where(BrandProfile.user_id == user.id))
    if user.role == "creator":
        return db.scalar(select(CreatorProfile).where(CreatorProfile.user_id == user.id))
    return None


def require_verified(profile):
    if not profile or profile.verification_status != "approved":
        raise HTTPException(status_code=403, detail="Account verification is required for this action")


def bootstrap_admin():
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not email or len(password) < 8:
        return
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            db.add(User(email=email, password_hash=hash_password(password), role="admin", display_name="PickByMe Admin"))
            db.commit()


class RegisterIn(BaseModel):
    email: str
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=2, max_length=120)
    role: str
    business_name: str | None = None
    slug: str | None = None
    city: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


class OfferIn(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    description: str = ""
    price_minor: int = Field(gt=0)
    currency: str = Field(default="OMR", min_length=3, max_length=3)
    creator_commission_bps: int = Field(default=1000, ge=0, le=9000)
    platform_fee_bps: int = Field(default=1000, ge=0, le=5000)


class OrderIn(BaseModel):
    tracking_code: str
    buyer_name: str = Field(min_length=2, max_length=120)
    buyer_email: str = Field(min_length=3, max_length=255)


class VerificationIn(BaseModel):
    status: str
    note: str = ""


class PayoutRequestIn(BaseModel):
    payout_method: str = Field(default="manual", min_length=2, max_length=40)


class PayoutDecisionIn(BaseModel):
    payout_reference: str = Field(default="", max_length=160)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    bootstrap_admin()
    yield


app = FastAPI(title="PickByMe", version="0.2.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health():
    return {"status": "ok", "product": "PickByMe", "version": "0.2.0"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    offers = db.scalars(select(Offer).where(Offer.status == "active").order_by(Offer.id.desc())).all()
    return templates.TemplateResponse(request=request, name="home.html", context={"offers": offers})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})


@app.get("/c/{slug}", response_class=HTMLResponse)
def creator_store(slug: str, request: Request, db: Session = Depends(get_db)):
    creator = db.scalar(select(CreatorProfile).where(CreatorProfile.slug == slug, CreatorProfile.verification_status == "approved"))
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    rows = db.execute(
        select(CreatorOffer, Offer)
        .join(Offer, Offer.id == CreatorOffer.offer_id)
        .where(CreatorOffer.creator_id == creator.id, CreatorOffer.active.is_(True), Offer.status == "active")
    ).all()
    return templates.TemplateResponse(request=request, name="creator_store.html", context={"creator": creator, "rows": rows})


@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if payload.role not in {"brand", "creator"}:
        raise HTTPException(status_code=400, detail="role must be brand or creator")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=email, password_hash=hash_password(payload.password), role=payload.role, display_name=payload.display_name.strip())
    db.add(user)
    db.flush()
    if payload.role == "brand":
        db.add(BrandProfile(user_id=user.id, business_name=(payload.business_name or payload.display_name).strip()))
    else:
        base_slug = slugify(payload.slug or payload.display_name)
        candidate = base_slug
        n = 1
        while db.scalar(select(CreatorProfile).where(CreatorProfile.slug == candidate)):
            n += 1
            candidate = f"{base_slug}-{n}"
        db.add(CreatorProfile(user_id=user.id, slug=candidate, city=payload.city.strip()))
    db.commit()
    return {
        "access_token": create_access_token(user.id, user.role),
        "token_type": "bearer",
        "role": user.role,
        "verification_status": "pending",
    }


@app.post("/api/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer", "role": user.role}


@app.get("/api/me")
def me(user: User = Depends(require_user), db: Session = Depends(get_db)):
    profile = profile_for_user(db, user)
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "active": user.active,
        "profile_id": profile.id if profile else None,
        "verification_status": getattr(profile, "verification_status", "approved" if user.role == "admin" else None),
        "verification_note": getattr(profile, "verification_note", ""),
    }


@app.post("/api/offers", status_code=201)
def create_offer(payload: OfferIn, user: User = Depends(require_role("brand")), db: Session = Depends(get_db)):
    brand = db.scalar(select(BrandProfile).where(BrandProfile.user_id == user.id))
    require_verified(brand)
    if payload.creator_commission_bps + payload.platform_fee_bps >= 10000:
        raise HTTPException(status_code=400, detail="Combined commission and fee must be below 100%")
    offer = Offer(
        brand_id=brand.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        price_minor=payload.price_minor,
        currency=payload.currency.upper(),
        creator_commission_bps=payload.creator_commission_bps,
        platform_fee_bps=payload.platform_fee_bps,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return {"id": offer.id, "title": offer.title, "status": offer.status}


@app.get("/api/offers")
def list_offers(db: Session = Depends(get_db)):
    offers = db.scalars(select(Offer).where(Offer.status == "active").order_by(Offer.id.desc())).all()
    return [
        {
            "id": x.id,
            "title": x.title,
            "description": x.description,
            "price_minor": x.price_minor,
            "currency": x.currency,
            "creator_commission_bps": x.creator_commission_bps,
            "platform_fee_bps": x.platform_fee_bps,
        }
        for x in offers
    ]


@app.post("/api/offers/{offer_id}/join", status_code=201)
def join_offer(offer_id: int, user: User = Depends(require_role("creator")), db: Session = Depends(get_db)):
    creator = db.scalar(select(CreatorProfile).where(CreatorProfile.user_id == user.id))
    require_verified(creator)
    offer = db.get(Offer, offer_id)
    if not offer or offer.status != "active":
        raise HTTPException(status_code=404, detail="Offer not found")
    existing = db.scalar(select(CreatorOffer).where(CreatorOffer.creator_id == creator.id, CreatorOffer.offer_id == offer.id))
    if existing:
        return {"tracking_code": existing.tracking_code, "store_url": f"/c/{creator.slug}"}
    link = CreatorOffer(
        creator_id=creator.id,
        offer_id=offer.id,
        tracking_code=secrets.token_urlsafe(9).replace("-", "").replace("_", "")[:12],
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return {"tracking_code": link.tracking_code, "store_url": f"/c/{creator.slug}"}


@app.get("/api/creator/dashboard")
def creator_dashboard(user: User = Depends(require_role("creator")), db: Session = Depends(get_db)):
    creator = db.scalar(select(CreatorProfile).where(CreatorProfile.user_id == user.id))
    rows = db.execute(
        select(CreatorOffer, Offer)
        .join(Offer, Offer.id == CreatorOffer.offer_id)
        .where(CreatorOffer.creator_id == creator.id)
        .order_by(CreatorOffer.id.desc())
    ).all()
    total_sales = db.scalar(
        select(func.coalesce(func.sum(Order.amount_minor), 0))
        .join(CreatorOffer, Order.creator_offer_id == CreatorOffer.id)
        .where(CreatorOffer.creator_id == creator.id, Order.status == "completed")
    ) or 0
    available = db.scalar(
        select(func.coalesce(func.sum(Commission.creator_amount_minor), 0))
        .where(Commission.creator_id == creator.id, Commission.status == "available")
    ) or 0
    reserved = db.scalar(
        select(func.coalesce(func.sum(Commission.creator_amount_minor), 0))
        .where(Commission.creator_id == creator.id, Commission.status == "reserved")
    ) or 0
    paid = db.scalar(
        select(func.coalesce(func.sum(Commission.creator_amount_minor), 0))
        .where(Commission.creator_id == creator.id, Commission.status == "paid")
    ) or 0
    return {
        "slug": creator.slug,
        "verification_status": creator.verification_status,
        "offers": len(rows),
        "sales_minor": total_sales,
        "available_balance_minor": available,
        "reserved_balance_minor": reserved,
        "paid_out_minor": paid,
        "earnings_minor": available + reserved + paid,
        "links": [
            {
                "offer_id": offer.id,
                "title": offer.title,
                "tracking_code": link.tracking_code,
                "store_url": f"/c/{creator.slug}",
                "active": link.active,
            }
            for link, offer in rows
        ],
    }


@app.post("/api/orders", status_code=201)
def create_order(payload: OrderIn, db: Session = Depends(get_db)):
    link = db.scalar(select(CreatorOffer).where(CreatorOffer.tracking_code == payload.tracking_code, CreatorOffer.active.is_(True)))
    if not link:
        raise HTTPException(status_code=404, detail="Tracking code not found")
    creator = db.get(CreatorProfile, link.creator_id)
    if not creator or creator.verification_status != "approved":
        raise HTTPException(status_code=409, detail="Creator store is not available")
    offer = db.get(Offer, link.offer_id)
    if not offer or offer.status != "active":
        raise HTTPException(status_code=409, detail="Offer is not available")
    order = Order(
        creator_offer_id=link.id,
        offer_id=offer.id,
        buyer_name=payload.buyer_name.strip(),
        buyer_email=payload.buyer_email.strip().lower(),
        amount_minor=offer.price_minor,
        currency=offer.currency,
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"order_id": order.id, "status": order.status, "amount_minor": order.amount_minor, "currency": order.currency}


@app.post("/api/orders/{order_id}/confirm")
def confirm_order(order_id: int, user: User = Depends(require_role("brand", "admin")), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    offer = db.get(Offer, order.offer_id)
    if user.role == "brand":
        brand = db.scalar(select(BrandProfile).where(BrandProfile.user_id == user.id))
        if not brand or offer.brand_id != brand.id:
            raise HTTPException(status_code=403, detail="Order does not belong to this brand")
    if order.status == "completed":
        return {"order_id": order.id, "status": order.status}
    if order.status != "pending":
        raise HTTPException(status_code=409, detail="Only pending orders can be confirmed")
    link = db.get(CreatorOffer, order.creator_offer_id)
    creator_amount = order.amount_minor * offer.creator_commission_bps // 10000
    platform_amount = order.amount_minor * offer.platform_fee_bps // 10000
    order.status = "completed"
    order.completed_at = datetime.utcnow()
    db.add(Commission(
        order_id=order.id,
        creator_id=link.creator_id,
        creator_amount_minor=creator_amount,
        platform_amount_minor=platform_amount,
        brand_net_minor=order.amount_minor - creator_amount - platform_amount,
        status="available",
    ))
    db.commit()
    return {"order_id": order.id, "status": order.status}


@app.post("/api/orders/{order_id}/refund")
def refund_order(order_id: int, user: User = Depends(require_role("brand", "admin")), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    offer = db.get(Offer, order.offer_id)
    if user.role == "brand":
        brand = db.scalar(select(BrandProfile).where(BrandProfile.user_id == user.id))
        if not brand or offer.brand_id != brand.id:
            raise HTTPException(status_code=403, detail="Order does not belong to this brand")
    if order.status == "refunded":
        return {"order_id": order.id, "status": order.status}
    if order.status != "completed":
        raise HTTPException(status_code=409, detail="Only completed orders can be refunded")
    commission = db.scalar(select(Commission).where(Commission.order_id == order.id))
    if commission and commission.status == "paid":
        raise HTTPException(status_code=409, detail="Creator payout already paid; manual resolution required")
    if commission and commission.status == "reserved" and commission.payout_id:
        payout = db.get(Payout, commission.payout_id)
        if payout and payout.status == "requested":
            payout.amount_minor -= commission.creator_amount_minor
            if payout.amount_minor <= 0:
                payout.amount_minor = 0
                payout.status = "cancelled"
    if commission:
        commission.status = "reversed"
        commission.payout_id = None
    order.status = "refunded"
    order.refunded_at = datetime.utcnow()
    db.commit()
    return {"order_id": order.id, "status": order.status}


@app.post("/api/creator/payouts", status_code=201)
def request_payout(payload: PayoutRequestIn, user: User = Depends(require_role("creator")), db: Session = Depends(get_db)):
    creator = db.scalar(select(CreatorProfile).where(CreatorProfile.user_id == user.id))
    require_verified(creator)
    available = db.scalars(
        select(Commission)
        .where(Commission.creator_id == creator.id, Commission.status == "available")
        .order_by(Commission.id)
    ).all()
    amount = sum(x.creator_amount_minor for x in available)
    if amount <= 0:
        raise HTTPException(status_code=409, detail="No available balance to withdraw")
    payout = Payout(creator_id=creator.id, amount_minor=amount, currency="OMR", payout_method=payload.payout_method, status="requested")
    db.add(payout)
    db.flush()
    for commission in available:
        commission.status = "reserved"
        commission.payout_id = payout.id
    db.commit()
    db.refresh(payout)
    return {"id": payout.id, "amount_minor": payout.amount_minor, "currency": payout.currency, "status": payout.status}


@app.get("/api/creator/payouts")
def creator_payouts(user: User = Depends(require_role("creator")), db: Session = Depends(get_db)):
    creator = db.scalar(select(CreatorProfile).where(CreatorProfile.user_id == user.id))
    rows = db.scalars(select(Payout).where(Payout.creator_id == creator.id).order_by(Payout.id.desc())).all()
    return [
        {
            "id": x.id,
            "amount_minor": x.amount_minor,
            "currency": x.currency,
            "status": x.status,
            "payout_method": x.payout_method,
            "payout_reference": x.payout_reference,
        }
        for x in rows
    ]


@app.get("/api/brand/offers")
def brand_offers(user: User = Depends(require_role("brand")), db: Session = Depends(get_db)):
    brand = db.scalar(select(BrandProfile).where(BrandProfile.user_id == user.id))
    offers = db.scalars(select(Offer).where(Offer.brand_id == brand.id).order_by(Offer.id.desc())).all()
    return [
        {
            "id": offer.id,
            "title": offer.title,
            "price_minor": offer.price_minor,
            "currency": offer.currency,
            "creator_commission_bps": offer.creator_commission_bps,
            "platform_fee_bps": offer.platform_fee_bps,
            "status": offer.status,
        }
        for offer in offers
    ]


@app.get("/api/brand/orders")
def brand_orders(user: User = Depends(require_role("brand")), db: Session = Depends(get_db)):
    brand = db.scalar(select(BrandProfile).where(BrandProfile.user_id == user.id))
    rows = db.execute(
        select(Order, Offer, CreatorProfile)
        .join(Offer, Offer.id == Order.offer_id)
        .join(CreatorOffer, CreatorOffer.id == Order.creator_offer_id)
        .join(CreatorProfile, CreatorProfile.id == CreatorOffer.creator_id)
        .where(Offer.brand_id == brand.id)
        .order_by(Order.id.desc())
    ).all()
    return [
        {
            "id": order.id,
            "offer_title": offer.title,
            "creator_slug": creator.slug,
            "buyer_name": order.buyer_name,
            "buyer_email": order.buyer_email,
            "amount_minor": order.amount_minor,
            "currency": order.currency,
            "status": order.status,
        }
        for order, offer, creator in rows
    ]


@app.get("/api/brand/dashboard")
def brand_dashboard(user: User = Depends(require_role("brand")), db: Session = Depends(get_db)):
    brand = db.scalar(select(BrandProfile).where(BrandProfile.user_id == user.id))
    offer_ids = list(db.scalars(select(Offer.id).where(Offer.brand_id == brand.id)).all())
    if not offer_ids:
        return {"verification_status": brand.verification_status, "offers": 0, "orders": 0, "gross_sales_minor": 0, "brand_net_minor": 0}
    orders = db.scalar(select(func.count(Order.id)).where(Order.offer_id.in_(offer_ids))) or 0
    gross = db.scalar(
        select(func.coalesce(func.sum(Order.amount_minor), 0))
        .where(Order.offer_id.in_(offer_ids), Order.status == "completed")
    ) or 0
    net = db.scalar(
        select(func.coalesce(func.sum(Commission.brand_net_minor), 0))
        .join(Order, Commission.order_id == Order.id)
        .where(Order.offer_id.in_(offer_ids), Commission.status != "reversed")
    ) or 0
    return {
        "verification_status": brand.verification_status,
        "offers": len(offer_ids),
        "orders": orders,
        "gross_sales_minor": gross,
        "brand_net_minor": net,
    }


@app.get("/api/admin/verifications")
def admin_verifications(user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    brands = db.execute(select(BrandProfile, User).join(User, User.id == BrandProfile.user_id).order_by(BrandProfile.id.desc())).all()
    creators = db.execute(select(CreatorProfile, User).join(User, User.id == CreatorProfile.user_id).order_by(CreatorProfile.id.desc())).all()
    return {
        "brands": [
            {"profile_id": p.id, "user_id": u.id, "name": p.business_name, "email": u.email, "status": p.verification_status, "note": p.verification_note}
            for p, u in brands
        ],
        "creators": [
            {"profile_id": p.id, "user_id": u.id, "name": u.display_name, "slug": p.slug, "email": u.email, "status": p.verification_status, "note": p.verification_note}
            for p, u in creators
        ],
    }


@app.post("/api/admin/verifications/{kind}/{profile_id}")
def admin_verify(kind: str, profile_id: int, payload: VerificationIn, user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    if payload.status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid verification status")
    model = BrandProfile if kind == "brand" else CreatorProfile if kind == "creator" else None
    if not model:
        raise HTTPException(status_code=400, detail="kind must be brand or creator")
    profile = db.get(model, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.verification_status = payload.status
    profile.verification_note = payload.note.strip()
    db.commit()
    return {"profile_id": profile.id, "status": profile.verification_status}


@app.get("/api/admin/payouts")
def admin_payouts(user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Payout, CreatorProfile, User)
        .join(CreatorProfile, CreatorProfile.id == Payout.creator_id)
        .join(User, User.id == CreatorProfile.user_id)
        .order_by(Payout.id.desc())
    ).all()
    return [
        {
            "id": payout.id,
            "creator": creator.slug,
            "email": account.email,
            "amount_minor": payout.amount_minor,
            "currency": payout.currency,
            "status": payout.status,
            "method": payout.payout_method,
            "reference": payout.payout_reference,
        }
        for payout, creator, account in rows
    ]


@app.post("/api/admin/payouts/{payout_id}/pay")
def admin_pay_payout(payout_id: int, payload: PayoutDecisionIn, user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    payout = db.get(Payout, payout_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    if payout.status == "paid":
        return {"id": payout.id, "status": payout.status}
    if payout.status != "requested":
        raise HTTPException(status_code=409, detail="Only requested payouts can be paid")
    payout.status = "paid"
    payout.paid_at = datetime.utcnow()
    payout.payout_reference = payload.payout_reference.strip()
    commissions = db.scalars(select(Commission).where(Commission.payout_id == payout.id, Commission.status == "reserved")).all()
    for commission in commissions:
        commission.status = "paid"
    db.commit()
    return {"id": payout.id, "status": payout.status}


@app.post("/api/admin/payouts/{payout_id}/reject")
def admin_reject_payout(payout_id: int, user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    payout = db.get(Payout, payout_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    if payout.status != "requested":
        raise HTTPException(status_code=409, detail="Only requested payouts can be rejected")
    commissions = db.scalars(select(Commission).where(Commission.payout_id == payout.id, Commission.status == "reserved")).all()
    for commission in commissions:
        commission.status = "available"
        commission.payout_id = None
    payout.status = "rejected"
    db.commit()
    return {"id": payout.id, "status": payout.status}


@app.get("/api/admin/stats")
def admin_stats(user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return {
        "users": db.scalar(select(func.count(User.id))) or 0,
        "brands": db.scalar(select(func.count(BrandProfile.id))) or 0,
        "creators": db.scalar(select(func.count(CreatorProfile.id))) or 0,
        "offers": db.scalar(select(func.count(Offer.id))) or 0,
        "orders": db.scalar(select(func.count(Order.id))) or 0,
        "pending_verifications": (
            (db.scalar(select(func.count(BrandProfile.id)).where(BrandProfile.verification_status == "pending")) or 0)
            + (db.scalar(select(func.count(CreatorProfile.id)).where(CreatorProfile.verification_status == "pending")) or 0)
        ),
        "pending_payouts": db.scalar(select(func.count(Payout.id)).where(Payout.status == "requested")) or 0,
        "platform_revenue_minor": db.scalar(
            select(func.coalesce(func.sum(Commission.platform_amount_minor), 0)).where(Commission.status != "reversed")
        ) or 0,
    }
