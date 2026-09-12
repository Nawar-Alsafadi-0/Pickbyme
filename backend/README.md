# PickByMe Backend

PickByMe is a creator-led commerce platform. The backend is intentionally **offer-centric** rather than product-centric so the same core can support products, services, reservations, stays, tickets, experiences, and future commerce types.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2
- PostgreSQL 17
- Alembic
- pytest
- Ruff

## Current flow

1. Provider registers an account.
2. Provider logs in and receives a Bearer session token.
3. Provider creates and publishes an offer.
4. Creator registers and logs in.
5. Creator selects an active offer.
6. The offer appears on the creator's public PickByMe page.
7. Conversion and commission models are ready for the next checkout/attribution phase.

## Run with Docker

From the repository root:

```bash
docker compose up --build
```

The API will be available at:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

The API container runs `alembic upgrade head` before starting FastAPI.

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Quality checks

```bash
ruff check .
pytest -q
```

## Main endpoints

- `POST /api/v1/accounts/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/offers`
- `POST /api/v1/offers` — provider only
- `POST /api/v1/creator/offers/{offer_id}` — creator only
- `GET /api/v1/creators/{slug}` — public creator page

## Security baseline

Passwords are hashed with Python's `scrypt`. Login issues a random opaque token; only its SHA-256 hash is stored in the database. Provider and creator actions are authorization-checked against the authenticated user's role and profile.
