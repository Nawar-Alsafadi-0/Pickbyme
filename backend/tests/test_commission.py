from decimal import Decimal

import pytest

from app.services.commission import calculate_commission


def test_calculate_commission() -> None:
    assert calculate_commission(Decimal("100.000"), Decimal("10")) == Decimal("10.000")


def test_commission_rounding() -> None:
    assert calculate_commission(Decimal("12.345"), Decimal("7.5")) == Decimal("0.926")


def test_invalid_commission_rate() -> None:
    with pytest.raises(ValueError):
        calculate_commission(Decimal("10"), Decimal("101"))
