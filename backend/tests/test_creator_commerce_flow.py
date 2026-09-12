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
    provider_id = provider_response.json()["profile_id"]

    offer_response = client.post(
        "/api/v1/offers",
        json={
            "provider_id": provider_id,
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
    creator_id = creator_response.json()["profile_id"]

    selection_response = client.post(
        f"/api/v1/creators/{creator_id}/offers/{offer_id}",
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
