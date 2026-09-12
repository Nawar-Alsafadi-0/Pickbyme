# PickByMe

PickByMe is a creator-led commerce platform where providers publish offers, creators curate what they recommend, and the platform attributes resulting conversions and commissions back to the creator.

The core is intentionally **offer-centric**, not product-centric. An offer can later represent a physical product, service, reservation, stay, ticket, experience, or another commerce type without redesigning the platform.

## Current backend flow

`Provider -> Offer -> Creator selection -> Tracking code -> Conversion -> Commission`

Implemented today:

- Creator / provider account registration
- Bearer session authentication
- Provider-only offer creation
- Active-offer discovery
- Creator-only offer selection
- Unique creator-offer attribution codes
- Public creator storefront API
- Provider-recorded attributed conversions
- Automatic commission creation
- Duplicate conversion protection
- Creator and provider summary dashboards
- PostgreSQL + SQLAlchemy + Alembic
- Docker Compose development environment
- Ruff + pytest CI configuration

## Repository

- `backend/` — FastAPI API, persistence, migrations, tests
- `frontend/` — reserved for the browser experience
- `docs/` — architecture and MVP decisions

## Development

From the repository root:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`, with OpenAPI docs at `/docs`.

See `docs/mvp.md` for the current product slice and `docs/architecture.md` for the domain model.
