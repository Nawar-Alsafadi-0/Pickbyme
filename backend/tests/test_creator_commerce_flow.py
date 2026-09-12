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


def test_provider_to_creator_public_page_flow(client: TestClient) -> None:
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
    assert selection_response.json()["creator_rate"] == "10.00"

    page_response = client.get("/api/v1/creators/nawar-picks")
    assert page_response.status_code == 200
    page = page_response.json()
    assert page["display_name"] == "Nawar Picks"
    assert page["slug"] == "nawar-picks"
    assert len(page["offers"]) == 1
    assert page["offers"][0]["title"] == "Signature Experience"
    assert page["offers"][0]["is_featured"] is True


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
