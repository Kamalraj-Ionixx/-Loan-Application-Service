from decimal import Decimal

import pytest

from app.services.loan import calculate_emi


@pytest.mark.parametrize(
    ("principal", "annual_rate", "tenure", "expected"),
    [
        (
            Decimal(300000),
            Decimal("12.00"),
            36,
            Decimal("9964.29"),
        ),
        (
            Decimal(100000),
            Decimal("10.00"),
            12,
            Decimal("8791.59"),
        ),
        (
            Decimal(60000),
            Decimal("0.00"),
            12,
            Decimal("5000.00"),
        ),
    ],
)
def test_calculate_emi(
    principal: Decimal,
    annual_rate: Decimal,
    tenure: int,
    expected: Decimal,
) -> None:
    assert calculate_emi(principal, annual_rate, tenure) == expected
