# PickByMe

PickByMe is a creator-commerce platform: brands publish offers, creators select what they want to promote, every creator gets trackable attribution, and completed orders split value into creator commission, platform fee, and brand net.

## Current product flow

1. Brand and creator create accounts.
2. New commercial accounts start in **pending verification**.
3. Admin approves or rejects brands and creators.
4. Approved brands publish offers with creator commission and platform fee.
5. Approved creators add offers to their public storefront.
6. Customers place attributed orders from creator storefronts.
7. If Thawani credentials are configured, PickByMe creates a hosted checkout session and redirects the buyer to the payment page.
8. On return, PickByMe retrieves the payment session server-side and only completes the order when the gateway reports it paid.
9. Completed orders create creator commission, platform revenue, and brand net.
10. Creators request payout from their available wallet balance.
11. Admin marks the payout paid or rejects it and returns the balance.
12. Refunds reverse unpaid commissions so revenue does not remain overstated.

## Included now

- Brand / Creator / Admin roles
- Account verification workflow
- Offer marketplace
- Public creator storefronts
- Creator tracking codes
- Orders with pending / completed / refunded lifecycle
- Creator commission ledger: available / reserved / paid / reversed
- Creator payout requests and admin payout queue
- Refund protection after creator payout
- Brand dashboard
- Creator wallet/dashboard
- Admin verification and payout dashboard
- Configurable Thawani hosted-checkout adapter
- Server-side payment status verification before commission creation
- Manual-confirmation fallback when a gateway is not configured
- Alembic database migrations
- SQLite local development
- PostgreSQL production configuration
- Docker Compose
- GitHub Actions CI
- End-to-end and payment-adapter tests

## Local setup

Create a virtual environment and install requirements, then copy the example environment variables.

Run the schema migration before starting the app:

    alembic upgrade head

Then:

    uvicorn app.main:app --reload

Open:
- App: http://127.0.0.1:8000
- Dashboard: http://127.0.0.1:8000/dashboard
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

Docker runs the migration automatically before Uvicorn starts.

## Admin bootstrap

Set ADMIN_EMAIL and ADMIN_PASSWORD before the first application start. If the email does not already exist, PickByMe creates the first administrator account automatically after migrations have run.

## Thawani checkout

Set these values to enable online checkout:

    THAWANI_SECRET_KEY=...
    THAWANI_PUBLISHABLE_KEY=...
    THAWANI_API_BASE=...
    THAWANI_CHECKOUT_BASE=...

The base URLs are configurable so sandbox/live environments can be switched without code changes. API secrets stay server-side. When credentials are absent, storefront orders still work but remain pending for manual brand/admin confirmation.

## Money model

All money is stored as integer minor units. For OMR, 1000 means 1.000 OMR. Percentage splits use basis points (1000 = 10%) to avoid floating-point accounting errors.

## Next production milestones

- Merchant sandbox/live credentials and a real end-to-end gateway transaction
- Signed webhook support/reconciliation for payments completed without browser return
- Gateway-initiated refunds
- KYC/business document upload and secure review
- Real payout provider/bank transfer integration
- Email/phone verification and password reset
- Rate limiting, audit logs, monitoring and backups
- Production deployment/domain/HTTPS
- Inventory and booking connectors
- Creator analytics and conversion tracking
- AI matching, campaign generation, and performance intelligence
