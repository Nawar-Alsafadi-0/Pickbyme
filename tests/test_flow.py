import os
os.environ["DATABASE_URL"] = "sqlite:///./test_pickbyme.db"
os.environ["SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app

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


def test_full_creator_commerce_flow():
    brand = client.post("/api/auth/register", json={
        "email":"brand@example.com","password":"password123","display_name":"Demo Brand","role":"brand","business_name":"Demo Brand"
    })
    assert brand.status_code == 201
    brand_headers = {"Authorization": f"Bearer {brand.json()['access_token']}"}

    creator = client.post("/api/auth/register", json={
        "email":"creator@example.com","password":"password123","display_name":"Nawar Picks","role":"creator","slug":"nawar-picks","city":"Muscat"
    })
    assert creator.status_code == 201
    creator_headers = {"Authorization": f"Bearer {creator.json()['access_token']}"}

    offer = client.post("/api/offers", headers=brand_headers, json={
        "title":"Dinner for Two","description":"Creator-exclusive dinner package","price_minor":25000,"currency":"OMR","creator_commission_bps":1000,"platform_fee_bps":1000
    })
    assert offer.status_code == 201
    offer_id = offer.json()["id"]

    joined = client.post(f"/api/offers/{offer_id}/join", headers=creator_headers)
    assert joined.status_code == 201
    tracking_code = joined.json()["tracking_code"]

    order = client.post("/api/orders", json={"tracking_code":tracking_code,"buyer_name":"Buyer One","buyer_email":"buyer@example.com"})
    assert order.status_code == 201
    assert order.json()["amount_minor"] == 25000
    assert order.json()["status"] == "pending"

    confirmed = client.post(f"/api/orders/{order.json()['order_id']}/confirm", headers=brand_headers)
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "completed"

    creator_dash = client.get("/api/creator/dashboard", headers=creator_headers)
    assert creator_dash.status_code == 200
    assert creator_dash.json()["sales_minor"] == 25000
    assert creator_dash.json()["earnings_minor"] == 2500

    brand_dash = client.get("/api/brand/dashboard", headers=brand_headers)
    assert brand_dash.status_code == 200
    assert brand_dash.json()["gross_sales_minor"] == 25000
    assert brand_dash.json()["brand_net_minor"] == 20000
