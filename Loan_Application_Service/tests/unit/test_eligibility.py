from datetime import date, datetime
from decimal import Decimal

import pytest

from app.models.customer import Customer
from app.services.loan import check_eligibility


@pytest.mark.parametrize(
    ("age", "amount", "income", "approved_count", "expected"),
    [
        (
            20,
            Decimal(100000),
            Decimal(50000),
            0,
            (False, "Age must be between 21 and 60"),
        ),
        (
            61,
            Decimal(100000),
            Decimal(50000),
            0,
            (False, "Age must be between 21 and 60"),
        ),
        (
            30,
            Decimal(1100000),
            Decimal(50000),
            0,
            (False, "Requested amount exceeds 20x monthly income"),
        ),
        (
            30,
            Decimal(100000),
            Decimal(50000),
            2,
            (
                False,
                "Customer already has 2 active loans",
            ),
        ),
        (
            30,
            Decimal(100000),
            Decimal(50000),
            1,
            (True, None),
        ),
    ],
)
def test_check_eligibility(
    age: int,
    amount: Decimal,
    income: Decimal,
    approved_count: int,
    expected: tuple[bool, str | None],
) -> None:
    today = datetime.now().astimezone().date()
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
        phone="9876543210",
        date_of_birth=date(today.year - age, today.month, min(today.day, 28)),
        monthly_income=income,
    )

    result = check_eligibility(
        customer=customer,
        amount=amount,
        approved_loan_count=approved_count,
    )

    assert result == expected
