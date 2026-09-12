# PickByMe Backend

FastAPI backend for the creator-led commerce core.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- pytest
- Ruff

## Current flow

1. Provider registers and logs in.
2. Provider creates and publishes an offer.
3. Creator registers and logs in.
4. Creator selects an active offer.
5. PickByMe generates a unique `tracking_code` for that creator-offer pair.
6. The code is exposed with the creator's public storefront offer.
7. Provider records a conversion using that tracking code and an external reference.
8. PickByMe creates the confirmed conversion and earned commission in the same transaction.
9. Creator and provider summary dashboards expose conversion and commission totals.

## Run with Docker

From the repository root:

```bash
docker compose up --build
```

API: `http://localhost:8000`

OpenAPI: `http://localhost:8000/docs`

## Local development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

## Quality checks

```bash
ruff check .
pytest -q
```

The first launch category, payment gateway, payout automation, and category-specific fulfillment remain intentionally deferred until the market test is chosen.
