
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanStatus


class LoanRepository:
    """Database operations for loans."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        customer_id: int,
        amount: Decimal,
        tenure_months: int,
        interest_rate: Decimal,
        emi: Decimal | None,
        status: LoanStatus,
        rejection_reason: str | None,
        applied_on: date,
    ) -> Loan:
        """Create and persist a loan."""
        loan = Loan(
            customer_id=customer_id,
            amount=amount,
            tenure_months=tenure_months,
            interest_rate=interest_rate,
            emi=emi,
            status=status,
            rejection_reason=rejection_reason,
            applied_on=applied_on,
        )

        try:
            self.db.add(loan)
            self.db.commit()
            self.db.refresh(loan)
        except Exception:
            self.db.rollback()
            raise

        return loan

    def get_by_id(self, loan_id: int) -> Loan | None:
        """Find a loan by its primary key."""
        return self.db.get(Loan, loan_id)

    def count_approved_loans(self, customer_id: int) -> int:
        """Count approved loans belonging to a customer."""
        statement = (
            select(func.count())
            .select_from(Loan)
            .where(
                Loan.customer_id == customer_id,
                Loan.status == LoanStatus.APPROVED,
            )
        )

        count = self.db.scalar(statement)
        return count or 0

    def get_customer_loans(
        self,
        customer_id: int,
        status: LoanStatus | None = None,
    ) -> list[Loan]:
        """Return a customer's loans, optionally filtered by status."""
        statement = select(Loan).where(Loan.customer_id == customer_id)

        if status is not None:
            statement = statement.where(Loan.status == status)

        statement = statement.order_by(Loan.id.desc())

        return list(self.db.scalars(statement).all())

    def get_summary_totals(self, customer_id: int) -> dict:
        """Calculate application counts and approved loan totals."""
        loans = self.get_customer_loans(customer_id)

        approved_loans = [
            loan for loan in loans if loan.status == LoanStatus.APPROVED
        ]
        rejected_loans = [
            loan for loan in loans if loan.status == LoanStatus.REJECTED
        ]

        total_approved_amount = sum(
            (loan.amount for loan in approved_loans),
            start=Decimal("0.00"),
        )

        total_monthly_emi = sum(
            (
                loan.emi
                for loan in approved_loans
                if loan.emi is not None
            ),
            start=Decimal("0.00"),
        )

        return {
            "total_applications": len(loans),
            "approved_count": len(approved_loans),
            "rejected_count": len(rejected_loans),
            "total_approved_amount": total_approved_amount,
            "total_monthly_emi": total_monthly_emi,
        }
