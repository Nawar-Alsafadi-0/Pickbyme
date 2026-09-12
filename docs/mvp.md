# PickByMe MVP

## Goal

Validate whether creator-led curation can drive real commerce across different offer types without locking PickByMe into one vertical too early.

## First working loop

1. A provider registers and logs in.
2. The provider publishes an offer.
3. A creator registers and logs in.
4. The creator discovers and selects the offer.
5. The selected offer appears on the creator's public page.
6. A future conversion is attributed to that creator.
7. Commission is calculated from the conversion.

## Current scope implemented

- Accounts and role-specific profiles
- Opaque Bearer authentication sessions
- Offer creation and active-offer discovery
- Creator offer selection
- Public creator page
- Conversion and commission domain models
- PostgreSQL migrations
- Docker development stack

## Next product slice

The next slice should add attribution and conversion capture before payment-provider integration. This lets PickByMe test the commercial loop even if the first transaction type is fulfilled externally.

Recommended next sequence:

`shareable creator link -> attribution token -> conversion event -> commission ledger -> provider/creator dashboards`

## Intentionally deferred

- Final market category
- Payment gateway
- Payout automation
- Shipping / fulfillment logic
- Reservation-specific availability logic
- Reviews and social features
- Native mobile apps

These should be driven by the first validated market rather than guessed during foundation work.
