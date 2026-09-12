from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_provider_to_creator_conversion_and_dashboard_flow(client: TestClient) -> None:
    provider_response = client.post(
        "/api/v1/accounts/register",
        json={
            "email": "provider@example.com",
            "display_name": "Local Brand",
            "password": "very-secure-password",
            "role": "provider",
            "slug": "local-brand",
            "business_name": "Local Brand LLC",
        },
    )
    assert provider_response.status_code == 201

    provider_headers = auth_headers(client, "provider@example.com", "very-secure-password")
    offer_response = client.post(
        "/api/v1/offers",
        headers=provider_headers,
        json={
            "title": "Signature Experience",
            "description": "A creator-selected experience.",
            "offer_type": "experience",
            "price": "25.000",
            "currency": "OMR",
            "default_creator_rate": "10.00",
            "publish": True,
        },
    )
    assert offer_response.status_code == 201
    offer_id = offer_response.json()["id"]

    creator_response = client.post(
        "/api/v1/accounts/register",
        json={
            "email": "creator@example.com",
            "display_name": "Nawar Picks",
            "password": "another-secure-password",
            "role": "creator",
            "slug": "nawar-picks",
            "bio": "Things I genuinely pick.",
        },
    )
    assert creator_response.status_code == 201

    creator_headers = auth_headers(client, "creator@example.com", "another-secure-password")
    selection_response = client.post(
        f"/api/v1/creator/offers/{offer_id}",
        headers=creator_headers,
        json={"is_featured": True},
    )
    assert selection_response.status_code == 201
    selection = selection_response.json()
    assert selection["creator_rate"] == "10.00"
    tracking_code = selection["tracking_code"]
    assert tracking_code

    page_response = client.get("/api/v1/creators/nawar-picks")
    assert page_response.status_code == 200
    page = page_response.json()
    assert page["display_name"] == "Nawar Picks"
    assert page["slug"] == "nawar-picks"
    assert len(page["offers"]) == 1
    assert page["offers"][0]["title"] == "Signature Experience"
    assert page["offers"][0]["tracking_code"] == tracking_code

    conversion_response = client.post(
        "/api/v1/conversions",
        headers=provider_headers,
        json={
            "tracking_code": tracking_code,
            "gross_amount": "25.000",
            "currency": "OMR",
            "external_reference": "ORDER-1001",
        },
    )
    assert conversion_response.status_code == 201
    conversion = conversion_response.json()
    assert conversion["commission_amount"] == "2.500"
    assert conversion["commission_status"] == "earned"

    creator_dashboard = client.get("/api/v1/dashboard/creator", headers=creator_headers)
    assert creator_dashboard.status_code == 200
    creator_summary = creator_dashboard.json()
    assert creator_summary["conversions"] == 1
    assert creator_summary["gross_amount"] == "25.000"
    assert creator_summary["commission_amount"] == "2.500"

    provider_dashboard = client.get("/api/v1/dashboard/provider", headers=provider_headers)
    assert provider_dashboard.status_code == 200
    provider_summary = provider_dashboard.json()
    assert provider_summary["conversions"] == 1
    assert provider_summary["gross_amount"] == "25.000"
    assert provider_summary["commission_amount"] == "2.500"

    duplicate_response = client.post(
        "/api/v1/conversions",
        headers=provider_headers,
        json={
            "tracking_code": tracking_code,
            "gross_amount": "25.000",
            "currency": "OMR",
            "external_reference": "ORDER-1001",
        },
    )
    assert duplicate_response.status_code == 409


def test_creator_cannot_create_provider_offer(client: TestClient) -> None:
    client.post(
        "/api/v1/accounts/register",
        json={
            "email": "creator2@example.com",
            "display_name": "Creator Two",
            "password": "another-secure-password",
            "role": "creator",
            "slug": "creator-two",
        },
    )
    headers = auth_headers(client, "creator2@example.com", "another-secure-password")
    response = client.post(
        "/api/v1/offers",
        headers=headers,
        json={"title": "Nope", "offer_type": "product", "publish": True},
    )
    assert response.status_code == 403
