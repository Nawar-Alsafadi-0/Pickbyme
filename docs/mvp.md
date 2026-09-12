# PickByMe MVP

## Goal

Validate whether creator-led curation can drive real commerce across different offer types without locking PickByMe into one vertical too early.

## Working loop

1. A provider registers and logs in.
2. The provider publishes an offer.
3. A creator registers and logs in.
4. The creator discovers and selects the offer.
5. PickByMe issues a unique tracking code for that creator-offer pair.
6. The selected offer appears on the creator's public page with that attribution code.
7. The provider records a completed conversion using the tracking code and its own external reference.
8. PickByMe resolves the creator attribution, creates the conversion, and creates the earned commission atomically.
9. Creator and provider dashboards expose conversion, gross-sales, and commission totals.

## Current scope implemented

- Accounts and role-specific creator/provider profiles
- Opaque Bearer authentication sessions
- Provider-only offer creation
- Public active-offer discovery
- Creator offer selection
- Unique creator-offer tracking codes
- Public creator page
- Attributed conversion capture
- Duplicate conversion protection through external references
- Automatic commission calculation and ledger records
- Creator and provider summary dashboards
- PostgreSQL migrations
- Docker development stack

## Next product slice

The backend now covers the commercial attribution loop before payment-provider integration. The next slice should make the flow usable from a real browser UI:

`landing / discovery -> creator storefront -> creator dashboard -> provider dashboard -> conversion management`

After the UI is usable, payment and fulfillment should be integrated based on the first launch category rather than guessed in advance.

## Intentionally deferred

- Final launch category
- Payment gateway
- Automated payouts
- Shipping / fulfillment rules
- Reservation-specific availability
- Reviews and social features
- Native mobile apps
- Multi-currency accounting summaries

These should be driven by the first validated market rather than guessed during foundation work.
