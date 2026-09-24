# PickByMe

PickByMe is a creator-commerce MVP: brands publish offers, creators select what they want to promote, every creator gets trackable attribution, and each completed order automatically splits value into creator commission, platform fee, and brand net.

## Current product flow

1. Brand and creator create accounts.
2. New commercial accounts start in **pending verification**.
3. Admin approves or rejects brands and creators.
4. Approved brands publish offers with creator commission and platform fee.
5. Approved creators add offers to their public storefront.
6. Customers place attributed orders from creator storefronts.
7. Completed orders create creator commission, platform revenue, and brand net.
8. Creators request payout from their available wallet balance.
9. Admin marks the payout paid or rejects it and returns the balance.
10. Refunds reverse unpaid commissions so revenue does not remain overstated.

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
- SQLite local development
- PostgreSQL-ready DATABASE_URL
- Docker Compose
- GitHub Actions CI
- End-to-end tests

## Run locally

Create a virtual environment, install requirements, copy the example environment file, then run:

    uvicorn app.main:app --reload

Open:
- App: http://127.0.0.1:8000
- Dashboard: http://127.0.0.1:8000/dashboard
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## Admin bootstrap

Set ADMIN_EMAIL and ADMIN_PASSWORD before the first application start. If the email does not already exist, PickByMe creates the first administrator account automatically.

## Money model

All money is stored as integer minor units. For OMR, 1000 means 1.000 OMR. Percentage splits use basis points (1000 = 10%) to avoid floating-point accounting errors.

## Still required before public launch

- Real payment gateway and signed payment webhooks
- Database migrations for production upgrades
- KYC/business document upload and secure review
- Real payout provider/bank transfer integration
- Inventory and booking connectors
- Email/phone verification and password reset
- Rate limiting, audit logs, monitoring and backups
- Production deployment/domain/HTTPS
- Creator analytics and conversion tracking
- AI matching, campaign generation, and performance intelligence
