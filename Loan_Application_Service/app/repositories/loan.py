from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.loan import Loan, LoanStatus


class LoanRepository:
    """Database operations for loans. Never commits; the service owns the transaction."""

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
        self.db.add(loan)
        self.db.flush()
        return loan

    def lock_customer(self, customer_id: int) -> None:
        """Lock the customer row so concurrent applications can't both pass the 2-loan limit."""
        self.db.execute(
            select(Customer.id).where(Customer.id == customer_id).with_for_update()
        )

    def get_by_id(self, loan_id: int) -> Loan | None:
        return self.db.get(Loan, loan_id)

    def count_approved_loans(self, customer_id: int) -> int:
        statement = (
            select(func.count())
            .select_from(Loan)
            .where(
                Loan.customer_id == customer_id,
                Loan.status == LoanStatus.APPROVED,
            )
        )
        return self.db.scalar(statement) or 0

    def get_customer_loans(
        self,
        customer_id: int,
        status: LoanStatus | None = None,
    ) -> list[Loan]:
        statement = select(Loan).where(Loan.customer_id == customer_id)

        if status is not None:
            statement = statement.where(Loan.status == status)

        statement = statement.order_by(Loan.id.desc())

        return list(self.db.scalars(statement).all())

    def list_loans(
        self,
        *,
        customer_id: int | None,
        status: LoanStatus | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Loan], int]:
        """Return one page of loans plus the total count matching the filters."""
        filters = []
        if customer_id is not None:
            filters.append(Loan.customer_id == customer_id)
        if status is not None:
            filters.append(Loan.status == status)

        total = self.db.scalar(select(func.count()).select_from(Loan).where(*filters))

        statement = (
            select(Loan)
            .where(*filters)
            .order_by(Loan.id.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(statement).all())

        return items, total or 0

    def get_summary_totals(self, customer_id: int) -> dict:
        """Aggregate counts and approved totals in one SQL query."""
        approved = Loan.status == LoanStatus.APPROVED
        rejected = Loan.status == LoanStatus.REJECTED

        row = self.db.execute(
            select(
                func.count(Loan.id),
                func.count(case((approved, 1))),
                func.count(case((rejected, 1))),
                func.coalesce(func.sum(case((approved, Loan.amount))), 0),
                func.coalesce(func.sum(case((approved, Loan.emi))), 0),
            ).where(Loan.customer_id == customer_id)
        ).one()

        return {
            "total_applications": row[0],
            "approved_count": row[1],
            "rejected_count": row[2],
            "total_approved_amount": Decimal(row[3]).quantize(Decimal("0.01")),
            "total_monthly_emi": Decimal(row[4]).quantize(Decimal("0.01")),
        }
