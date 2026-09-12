# PickByMe

PickByMe is a creator-led commerce platform where creators curate offers from brands and service providers, share them with their audience, and earn commission from attributed transactions.

The platform is intentionally **offer-centric**, not product-centric. An offer may later represent a physical product, digital product, service, reservation, hotel stay, ticket, experience, or another commerce type.

## Repository structure

- `backend/` — backend foundation and future application code
- `frontend/` — customer, creator, provider, and admin web surfaces
- `docs/architecture.md` — domain and architecture foundation
- `docs/mvp.md` — first validation scope

## Core transaction loop

Provider creates an offer -> Creator selects it -> Customer discovers it through the creator -> Transaction is attributed -> Commission is calculated.

## Current status

Foundation only. No framework, payment provider, or first commerce category is locked in yet.
