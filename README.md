# PickByMe

PickByMe is a creator-commerce MVP: brands publish offers, creators select what they want to promote, every creator gets trackable attribution, and each completed order automatically splits value into creator commission, platform fee, and brand net.

## MVP scope

- Brand and creator registration/login
- Role-based API access
- Brand offer creation
- Public marketplace of active offers
- Creator opt-in to offers with unique tracking codes
- Public creator storefronts (/c/{slug})
- Order attribution by creator tracking code
- Automatic commission accounting after order confirmation
- Brand and creator dashboards
- Admin KPI endpoint
- SQLite for zero-config local development; PostgreSQL-ready via DATABASE_URL
- Docker support
- End-to-end pytest covering the first commercial flow

## Run locally

Create a virtual environment, install requirements, then run:

    uvicorn app.main:app --reload

Open:
- App: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## Money model

All money is stored as integer minor units. For OMR, 1000 means 1.000 OMR. Percentage splits use basis points (1000 = 10%) to avoid floating-point accounting errors.

## First revenue loop

1. A brand creates an offer and sets the creator commission.
2. A creator joins the offer and receives a tracking code/store placement.
3. A customer places an attributed order.
4. The brand/payment flow confirms the order.
5. PickByMe calculates creator earnings, platform revenue, and brand net.

## Next milestones

Payment provider integration, checkout UI, brand/creator verification, payout ledger, refunds/cancellations, inventory/booking connectors, creator discovery/matching, and AI-assisted campaign/content generation.
