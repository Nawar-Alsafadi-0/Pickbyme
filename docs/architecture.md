# PickByMe Architecture

## Product model

PickByMe is a creator-led commerce platform. Providers publish **offers**; creators curate those offers; customers discover and convert through creator pages.

The core entity is `Offer`, not `Product`. An offer can represent a physical product, service, reservation, stay, ticket, experience, or a future commerce type.

## Core domains

### Accounts

A `User` has one role: customer, creator, provider, or admin. Creator and provider roles receive dedicated profiles.

Passwords are hashed with scrypt. Login creates an opaque random Bearer token; only the SHA-256 token hash is stored in `auth_sessions`. Sessions can expire or be revoked.

### Providers

Providers own and publish offers. Provider-only endpoints resolve the provider profile from the authenticated user instead of trusting a provider ID supplied by the client.

### Creators

Creators curate active offers. Creator-only endpoints resolve the creator profile from the authenticated user. Each creator has a public slug such as `/creators/nawar-picks`.

### Offers

Offers contain common commercial fields such as title, description, type, price, currency, status, and default creator commission rate. Type-specific detail models can be added later once a market category is validated.

### Creator selections

`CreatorOffer` links a creator to an offer and stores the commission rate and featured state used on the creator storefront.

### Attribution and conversions

`Conversion` is the neutral transaction record. It points to the offer and creator responsible for the conversion and can later represent checkout, reservation, booking, lead conversion, or external fulfillment.

### Commissions

`Commission` is a ledger record tied one-to-one to a conversion. The calculation logic is isolated from API and database code.

## Current request flow

```text
Provider register -> login -> publish Offer
                              |
Creator register -> login -> discover -> select
                              |
                     Public creator page
                              |
                      future attribution
                              |
                     Conversion -> Commission
```

## Runtime

- FastAPI application
- PostgreSQL persistence
- SQLAlchemy ORM
- Alembic migrations
- Docker Compose development environment
- pytest and Ruff quality checks

## Design rules

1. Do not encode first-market assumptions into the core Offer model.
2. Never trust role/profile identifiers supplied by a client for privileged actions.
3. Store commission outcomes as ledger records, not values recalculated historically on demand.
4. Keep payment provider details behind a future payments boundary.
5. Validate one creator-to-conversion loop before expanding into market-specific complexity.
