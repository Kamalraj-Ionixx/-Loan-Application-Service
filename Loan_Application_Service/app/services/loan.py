import math
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.models.customer import Customer
from app.models.loan import Loan, LoanStatus
from app.repositories.loan import LoanRepository


INTEREST_RATES = {
    12: Decimal("10.00"),
    24: Decimal("11.00"),
    36: Decimal("12.00"),
    48: Decimal("13.00"),
    60: Decimal("13.00"),
}


def calculate_age(date_of_birth: date) -> int:
    today = date.today()
    return (
        today.year
        - date_of_birth.year
        - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    )


def calculate_emi(
    principal: Decimal,
    annual_interest_rate: Decimal,
    tenure_months: int,
) -> Decimal:
    monthly_rate = annual_interest_rate / Decimal("1200")

    if monthly_rate == 0:
        emi = principal / tenure_months
    else:
        factor = (Decimal("1") + monthly_rate) ** tenure_months
        emi = principal * monthly_rate * factor / (factor - Decimal("1"))

    return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def check_eligibility(
    customer: Customer,
    amount: Decimal,
    approved_loan_count: int,
) -> tuple[bool, str | None]:
    """Check whether a customer meets the loan eligibility rules."""
    age = calculate_age(customer.date_of_birth)

    if age < 21 or age > 60:
        return False, "Age must be between 21 and 60"

    if amount > customer.monthly_income * Decimal("20"):
        return False, "Requested amount exceeds 20x monthly income"

    if approved_loan_count >= 2:
        return False, "Customer already has 2 active loans"

    return True, None


class LoanService:
    def __init__(self, repository: LoanRepository) -> None:
        self.repository = repository

    def list_loans(
        self,
        *,
        customer_id: int | None,
        status: LoanStatus | None,
        page: int,
        size: int,
    ) -> dict:
        items, total = self.repository.list_loans(
            customer_id=customer_id,
            status=status,
            offset=(page - 1) * size,
            limit=size,
        )
        return {
            "items": items,
            "page": page,
            "size": size,
            "total": total,
            "pages": math.ceil(total / size) if total else 0,
        }

    def apply_loan(
        self,
        customer: Customer,
        amount: Decimal,
        tenure_months: int,
    ) -> Loan:
        db = self.repository.db
        interest_rate = INTEREST_RATES[tenure_months]

        try:
            self.repository.lock_customer(customer.id)
            approved_loan_count = self.repository.count_approved_loans(customer.id)

            eligible, rejection_reason = check_eligibility(
                customer=customer,
                amount=amount,
                approved_loan_count=approved_loan_count,
            )

            loan_status = LoanStatus.APPROVED if eligible else LoanStatus.REJECTED
            emi = (
                calculate_emi(amount, interest_rate, tenure_months)
                if eligible
                else None
            )

            loan = self.repository.create(
                customer_id=customer.id,
                amount=amount,
                tenure_months=tenure_months,
                interest_rate=interest_rate,
                emi=emi,
                status=loan_status,
                rejection_reason=rejection_reason,
                applied_on=date.today(),
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(loan)
        return loan
