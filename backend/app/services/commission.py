from decimal import ROUND_HALF_UP, Decimal

MONEY_QUANTUM = Decimal("0.001")


def calculate_commission(gross_amount: Decimal, rate_percent: Decimal) -> Decimal:
    if gross_amount < 0:
        raise ValueError("gross_amount cannot be negative")
    if rate_percent < 0 or rate_percent > 100:
        raise ValueError("rate_percent must be between 0 and 100")

    amount = gross_amount * (rate_percent / Decimal(100))
    return amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
