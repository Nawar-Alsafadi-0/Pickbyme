from contextlib import asynccontextmanager
import re
import secrets
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import BrandProfile, Commission, CreatorOffer, CreatorProfile, Offer, Order, User
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
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def require_role(*roles: str):
    def dependency(user: User = Depends(require_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return dependency


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="PickByMe", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health():
    return {"status": "ok", "product": "PickByMe"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    offers = db.scalars(select(Offer).where(Offer.status == "active").order_by(Offer.id.desc())).all()
    return templates.TemplateResponse(request=request, name="home.html", context={"offers": offers})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})


@app.get("/c/{slug}", response_class=HTMLResponse)
def creator_store(slug: str, request: Request, db: Session = Depends(get_db)):
    creator = db.scalar(select(CreatorProfile).where(CreatorProfile.slug == slug))
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
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer", "role": user.role}


@app.post("/api/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer", "role": user.role}


@app.get("/api/me")
def me(user: User = Depends(require_user), db: Session = Depends(get_db)):
    profile = None
    if user.role == "brand":
        profile = db.scalar(select(BrandProfile).where(BrandProfile.user_id == user.id))
    elif user.role == "creator":
        profile = db.scalar(select(CreatorProfile).where(CreatorProfile.user_id == user.id))
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "role": user.role, "profile_id": profile.id if profile else None}


@app.post("/api/offers", status_code=201)
def create_offer(payload: OfferIn, user: User = Depends(require_role("brand")), db: Session = Depends(get_db)):
    brand = db.scalar(select(BrandProfile).where(BrandProfile.user_id == user.id))
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
    offer = db.get(Offer, offer_id)
    if not offer or offer.status != "active":
        raise HTTPException(status_code=404, detail="Offer not found")
    existing = db.scalar(select(CreatorOffer).where(CreatorOffer.creator_id == creator.id, CreatorOffer.offer_id == offer.id))
    if existing:
        return {"tracking_code": existing.tracking_code, "store_url": f"/c/{creator.slug}"}
    link = CreatorOffer(creator_id=creator.id, offer_id=offer.id, tracking_code=secrets.token_urlsafe(9).replace("-", "").replace("_", "")[:12])
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
    earnings = db.scalar(select(func.coalesce(func.sum(Commission.creator_amount_minor), 0)).where(Commission.creator_id == creator.id)) or 0
    return {
        "slug": creator.slug,
        "offers": len(rows),
        "sales_minor": total_sales,
        "earnings_minor": earnings,
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
    db.add(Commission(
        order_id=order.id,
        creator_id=link.creator_id,
        creator_amount_minor=creator_amount,
        platform_amount_minor=platform_amount,
        brand_net_minor=order.amount_minor - creator_amount - platform_amount,
    ))
    db.commit()
    return {"order_id": order.id, "status": order.status}


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
        return {"offers": 0, "orders": 0, "gross_sales_minor": 0, "brand_net_minor": 0}
    orders = db.scalar(select(func.count(Order.id)).where(Order.offer_id.in_(offer_ids))) or 0
    gross = db.scalar(
        select(func.coalesce(func.sum(Order.amount_minor), 0))
        .where(Order.offer_id.in_(offer_ids), Order.status == "completed")
    ) or 0
    net = db.scalar(
        select(func.coalesce(func.sum(Commission.brand_net_minor), 0))
        .join(Order, Commission.order_id == Order.id)
        .where(Order.offer_id.in_(offer_ids))
    ) or 0
    return {"offers": len(offer_ids), "orders": orders, "gross_sales_minor": gross, "brand_net_minor": net}


@app.get("/api/admin/stats")
def admin_stats(user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return {
        "users": db.scalar(select(func.count(User.id))) or 0,
        "brands": db.scalar(select(func.count(BrandProfile.id))) or 0,
        "creators": db.scalar(select(func.count(CreatorProfile.id))) or 0,
        "offers": db.scalar(select(func.count(Offer.id))) or 0,
        "orders": db.scalar(select(func.count(Order.id))) or 0,
        "platform_revenue_minor": db.scalar(select(func.coalesce(func.sum(Commission.platform_amount_minor), 0))) or 0,
    }
