# PickByMe

PickByMe is a creator-led commerce platform where providers publish offers and creators curate the offers they genuinely want to recommend to their audience.

The platform is **offer-centric**, not product-centric. The same core is designed to support physical products, services, reservations, stays, tickets, experiences, and future commerce categories without rebuilding the business model.

## Current foundation

The first working vertical slice is in place:

- Provider and creator account registration
- Secure password hashing with scrypt
- Login/logout with opaque Bearer sessions
- Provider-only offer creation
- Public active-offer discovery
- Creator-only offer selection
- Public creator storefront endpoint
- Conversion and commission domain models
- PostgreSQL + SQLAlchemy
- Alembic migrations
- Docker Compose development stack
- pytest + Ruff CI

## Core flow

`Provider -> Offer -> Creator selection -> Creator storefront -> Customer conversion -> Commission`

The first market category and checkout/payment provider are intentionally not locked in yet.

## Run

```bash
docker compose up --build
```

Then open `http://localhost:8000/docs`.

See `backend/README.md` for backend setup and API details.
