from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.loan import Loan, LoanStatus
from app.repositories.customer import CustomerRepository
from app.repositories.loan import LoanRepository
from app.schemas.loan import LoanCreate


INTEREST_RATES = {
    12: Decimal("10.00"),
    24: Decimal("11.00"),
    36: Decimal("12.00"),
    48: Decimal("13.00"),
    60: Decimal("13.00"),
}


def calculate_age(
    date_of_birth: date,
    today: date | None = None,
) -> int:
    today = today or date.today()

    age = today.year - date_of_birth.year

    if (
        today.month,
        today.day,
    ) < (
        date_of_birth.month,
        date_of_birth.day,
    ):
        age -= 1

    return age


def calculate_emi(
    principal: Decimal,
    annual_rate: Decimal,
    tenure_months: int,
) -> Decimal:
    monthly_rate = (
        annual_rate / Decimal("100") / Decimal("12")
    )

    if monthly_rate == 0:
        emi = principal / Decimal(tenure_months)
    else:
        factor = (
            Decimal("1") + monthly_rate
        ) ** tenure_months

        emi = (
            principal
            * monthly_rate
            * factor
            / (factor - Decimal("1"))
        )

    return emi.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


class LoanService:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        loan_repository: LoanRepository,
    ):
        self.customer_repository = customer_repository
        self.loan_repository = loan_repository

    def apply_loan(
        self,
        db: Session,
        loan_data: LoanCreate,
    ) -> Loan:
        customer = self.customer_repository.get_by_id(
            db,
            loan_data.customer_id,
        )

        if customer is None:
            raise NotFoundError(
                f"Customer with id {loan_data.customer_id} not found"
            )

        age = calculate_age(
            customer.date_of_birth,
        )

        interest_rate = INTEREST_RATES[
            loan_data.tenure_months
        ]

        rejection_reason = None
        status = LoanStatus.APPROVED
        emi = calculate_emi(
            loan_data.amount,
            interest_rate,
            loan_data.tenure_months,
        )

        if not 21 <= age <= 60:
            status = LoanStatus.REJECTED
            rejection_reason = (
                "Age must be between 21 and 60"
            )
            emi = None

        elif loan_data.amount > (
            customer.monthly_income * Decimal("20")
        ):
            status = LoanStatus.REJECTED
            rejection_reason = (
                "Requested amount exceeds 20x monthly income"
            )
            emi = None

        else:
            approved_count = (
                self.loan_repository.count_approved_loans(
                    db,
                    customer.id,
                )
            )

            if approved_count >= 2:
                status = LoanStatus.REJECTED
                rejection_reason = (
                    "Customer already has 2 active loans"
                )
                emi = None

        loan = Loan(
            customer_id=customer.id,
            amount=loan_data.amount,
            tenure_months=loan_data.tenure_months,
            interest_rate=interest_rate,
            emi=emi,
            status=status,
            rejection_reason=rejection_reason,
            applied_on=date.today(),
        )

        return self.loan_repository.create(
            db,
            loan,
        )

    def get_loan(
        self,
        db: Session,
        loan_id: int,
    ) -> Loan:
        loan = self.loan_repository.get_by_id(
            db,
            loan_id,
        )

        if loan is None:
            raise NotFoundError(
                f"Loan with id {loan_id} not found"
            )

        return loan

    def get_customer_loans(
        self,
        db: Session,
        customer_id: int,
        status: LoanStatus | None = None,
    ) -> list[Loan]:
        customer = self.customer_repository.get_by_id(
            db,
            customer_id,
        )

        if customer is None:
            raise NotFoundError(
                f"Customer with id {customer_id} not found"
            )

        return self.loan_repository.get_customer_loans(
            db,
            customer_id,
            status,
        )

    def get_summary(
        self,
        db: Session,
        customer_id: int,
    ) -> dict:
        customer = self.customer_repository.get_by_id(
            db,
            customer_id,
        )

        if customer is None:
            raise NotFoundError(
                f"Customer with id {customer_id} not found"
            )

        (
            total_applications,
            approved_count,
            rejected_count,
            total_approved_amount,
            total_monthly_emi,
        ) = self.loan_repository.get_customer_loan_summary(
            db,
            customer_id,
        )

        total_approved_amount = Decimal(
            str(total_approved_amount)
        ).quantize(
            Decimal("0.01"),
        )

        total_monthly_emi = Decimal(
            str(total_monthly_emi)
        ).quantize(
            Decimal("0.01"),
        )

        if customer.monthly_income > 0:
            emi_to_income_ratio = (
                total_monthly_emi
                / customer.monthly_income
                * Decimal("100")
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
        else:
            emi_to_income_ratio = Decimal("0.00")

        if emi_to_income_ratio < Decimal("30"):
            risk_band = "LOW"
        elif emi_to_income_ratio <= Decimal("50"):
            risk_band = "MEDIUM"
        else:
            risk_band = "HIGH"

        return {
            "customer_id": customer.id,
            "customer_name": customer.name,
            "total_applications": total_applications,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "total_approved_amount": total_approved_amount,
            "total_monthly_emi": total_monthly_emi,
            "emi_to_income_ratio": emi_to_income_ratio,
            "risk_band": risk_band,
        }