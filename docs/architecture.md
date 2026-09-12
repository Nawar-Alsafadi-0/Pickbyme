# PickByMe Architecture Foundation

## Product principle

PickByMe is a creator-led commerce platform. The core should not assume that every sellable thing is a physical product.

The central domain object is an **Offer**.

An Offer can later represent:
- physical product
- digital product
- service
- restaurant booking
- salon booking
- hotel stay
- ticket
- experience
- another future commerce type

## Core actors

### Customer
Discovers offers through creators and completes a purchase or reservation.

### Creator
Curates offers, shares a public PickByMe page, drives attributed transactions, and earns commissions.

### Provider
Owns or fulfills an offer. A provider can be a brand, merchant, restaurant, salon, hotel, service business, or another supplier.

### Admin
Operates the platform, approves participants, handles disputes, manages commissions, and monitors transactions.

## Core domains

### Users
Authentication, identity, account state, permissions, and roles.

### Creators
Creator profile, public slug, status, selected offers, attribution, and earnings.

### Providers
Provider profile, verification, payout information, fulfillment settings, and offers.

### Offers
A flexible sellable/bookable entity with common fields and type-specific metadata.

### Creator selections
The relationship between a creator and the offers they choose to feature.

### Attribution
Tracks which creator caused or influenced a transaction.

### Transactions
A common commercial record that can later specialize into orders or reservations where needed.

### Commissions
Stores platform and creator commission rules and the resulting ledger entries.

### Payments
Payment intent/state, refunds, provider settlement, and creator payout state. Payment implementation is intentionally deferred until the first validated commerce flow is selected.

## Architectural rule

Do not build the platform around a `Product` object and later force bookings and services into it. Build around a generic `Offer`, then attach type-specific behavior only where necessary.

## First validation loop

Provider creates offer -> Creator selects offer -> Offer appears on creator page -> Customer converts -> Attribution is stored -> Commission is calculated.

Everything beyond this loop should be treated as optional until the first market direction is validated.
