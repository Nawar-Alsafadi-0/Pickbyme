import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///./test_pickbyme.db"
os.environ["SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import BrandProfile, CreatorProfile, User
from app.security import create_access_token, hash_password

client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove("test_pickbyme.db")
    except FileNotFoundError:
        pass


def admin_headers():
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == "admin@pickbyme.test"))
        if not admin:
            admin = User(
                email="admin@pickbyme.test",
                password_hash=hash_password("password123"),
                role="admin",
                display_name="Admin",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
        return {"Authorization": f"Bearer {create_access_token(admin.id, 'admin')}"}


def approve_profiles(headers):
    with SessionLocal() as db:
        brand = db.scalar(select(BrandProfile))
        creator = db.scalar(select(CreatorProfile))
        brand_id, creator_id = brand.id, creator.id
    assert client.post(
        f"/api/admin/verifications/brand/{brand_id}",
        headers=headers,
        json={"status": "approved", "note": "test approval"},
    ).status_code == 200
    assert client.post(
        f"/api/admin/verifications/creator/{creator_id}",
        headers=headers,
        json={"status": "approved", "note": "test approval"},
    ).status_code == 200


def test_full_verified_commerce_finance_flow():
    brand = client.post("/api/auth/register", json={
        "email": "brand@example.com",
        "password": "password123",
        "display_name": "Demo Brand",
        "role": "brand",
        "business_name": "Demo Brand",
    })
    assert brand.status_code == 201
    assert brand.json()["verification_status"] == "pending"
    brand_headers = {"Authorization": f"Bearer {brand.json()['access_token']}"}

    creator = client.post("/api/auth/register", json={
        "email": "creator@example.com",
        "password": "password123",
        "display_name": "Nawar Picks",
        "role": "creator",
        "slug": "nawar-picks",
        "city": "Muscat",
    })
    assert creator.status_code == 201
    creator_headers = {"Authorization": f"Bearer {creator.json()['access_token']}"}

    blocked_offer = client.post("/api/offers", headers=brand_headers, json={
        "title": "Blocked",
        "price_minor": 1000,
        "currency": "OMR",
        "creator_commission_bps": 1000,
        "platform_fee_bps": 1000,
    })
    assert blocked_offer.status_code == 403

    admin = admin_headers()
    queue = client.get("/api/admin/verifications", headers=admin)
    assert queue.status_code == 200
    assert len(queue.json()["brands"]) == 1
    assert len(queue.json()["creators"]) == 1
    approve_profiles(admin)

    offer = client.post("/api/offers", headers=brand_headers, json={
        "title": "Dinner for Two",
        "description": "Creator-exclusive dinner package",
        "price_minor": 25000,
        "currency": "OMR",
        "creator_commission_bps": 1000,
        "platform_fee_bps": 1000,
    })
    assert offer.status_code == 201
    offer_id = offer.json()["id"]

    joined = client.post(f"/api/offers/{offer_id}/join", headers=creator_headers)
    assert joined.status_code == 201
    tracking_code = joined.json()["tracking_code"]

    dashboard_page = client.get("/dashboard")
    assert dashboard_page.status_code == 200

    order1 = client.post("/api/orders", json={
        "tracking_code": tracking_code,
        "buyer_name": "Buyer One",
        "buyer_email": "buyer1@example.com",
    })
    assert order1.status_code == 201
    confirmed1 = client.post(f"/api/orders/{order1.json()['order_id']}/confirm", headers=brand_headers)
    assert confirmed1.status_code == 200

    creator_dash = client.get("/api/creator/dashboard", headers=creator_headers).json()
    assert creator_dash["available_balance_minor"] == 2500
    assert creator_dash["paid_out_minor"] == 0

    payout = client.post("/api/creator/payouts", headers=creator_headers, json={"payout_method": "bank"})
    assert payout.status_code == 201
    assert payout.json()["amount_minor"] == 2500

    creator_dash = client.get("/api/creator/dashboard", headers=creator_headers).json()
    assert creator_dash["available_balance_minor"] == 0
    assert creator_dash["reserved_balance_minor"] == 2500

    payouts = client.get("/api/admin/payouts", headers=admin)
    assert payouts.status_code == 200
    payout_id = payouts.json()[0]["id"]

    paid = client.post(
        f"/api/admin/payouts/{payout_id}/pay",
        headers=admin,
        json={"payout_reference": "BANK-001"},
    )
    assert paid.status_code == 200

    creator_dash = client.get("/api/creator/dashboard", headers=creator_headers).json()
    assert creator_dash["paid_out_minor"] == 2500
    assert creator_dash["reserved_balance_minor"] == 0

    cannot_refund_paid = client.post(f"/api/orders/{order1.json()['order_id']}/refund", headers=brand_headers)
    assert cannot_refund_paid.status_code == 409

    order2 = client.post("/api/orders", json={
        "tracking_code": tracking_code,
        "buyer_name": "Buyer Two",
        "buyer_email": "buyer2@example.com",
    })
    assert order2.status_code == 201
    assert client.post(f"/api/orders/{order2.json()['order_id']}/confirm", headers=brand_headers).status_code == 200

    creator_dash = client.get("/api/creator/dashboard", headers=creator_headers).json()
    assert creator_dash["available_balance_minor"] == 2500

    refunded = client.post(f"/api/orders/{order2.json()['order_id']}/refund", headers=brand_headers)
    assert refunded.status_code == 200
    assert refunded.json()["status"] == "refunded"

    creator_dash = client.get("/api/creator/dashboard", headers=creator_headers).json()
    assert creator_dash["available_balance_minor"] == 0
    assert creator_dash["earnings_minor"] == 2500

    brand_dash = client.get("/api/brand/dashboard", headers=brand_headers).json()
    assert brand_dash["gross_sales_minor"] == 25000
    assert brand_dash["brand_net_minor"] == 20000

    stats = client.get("/api/admin/stats", headers=admin).json()
    assert stats["platform_revenue_minor"] == 2500
    assert stats["pending_verifications"] == 0
