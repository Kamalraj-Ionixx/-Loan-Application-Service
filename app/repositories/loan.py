from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanStatus


class LoanRepository:
    @staticmethod
    def create(
        db: Session,
        loan: Loan,
    ) -> Loan:
        db.add(loan)
        db.commit()
        db.refresh(loan)

        return loan

    @staticmethod
    def get_by_id(
        db: Session,
        loan_id: int,
    ) -> Loan | None:
        statement = select(Loan).where(
            Loan.id == loan_id
        )

        return db.scalar(statement)

    @staticmethod
    def count_approved_loans(
        db: Session,
        customer_id: int,
    ) -> int:
        statement = select(
            func.count(Loan.id)
        ).where(
            Loan.customer_id == customer_id,
            Loan.status == LoanStatus.APPROVED,
        )

        return db.scalar(statement) or 0

    @staticmethod
    def get_customer_loans(
        db: Session,
        customer_id: int,
        status: LoanStatus | None = None,
    ) -> list[Loan]:
        statement = select(Loan).where(
            Loan.customer_id == customer_id,
        )

        if status is not None:
            statement = statement.where(
                Loan.status == status,
            )

        statement = statement.order_by(
            Loan.applied_on.desc(),
            Loan.id.desc(),
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def get_customer_loan_summary(
        db: Session,
        customer_id: int,
    ) -> tuple[int, int, int, object, object]:
        total_applications = db.scalar(
            select(func.count(Loan.id)).where(
                Loan.customer_id == customer_id,
            )
        ) or 0

        approved_count = db.scalar(
            select(func.count(Loan.id)).where(
                Loan.customer_id == customer_id,
                Loan.status == LoanStatus.APPROVED,
            )
        ) or 0

        rejected_count = db.scalar(
            select(func.count(Loan.id)).where(
                Loan.customer_id == customer_id,
                Loan.status == LoanStatus.REJECTED,
            )
        ) or 0

        total_approved_amount = db.scalar(
            select(func.coalesce(func.sum(Loan.amount), 0)).where(
                Loan.customer_id == customer_id,
                Loan.status == LoanStatus.APPROVED,
            )
        ) or 0

        total_monthly_emi = db.scalar(
            select(func.coalesce(func.sum(Loan.emi), 0)).where(
                Loan.customer_id == customer_id,
                Loan.status == LoanStatus.APPROVED,
            )
        ) or 0

        return (
            total_applications,
            approved_count,
            rejected_count,
            total_approved_amount,
            total_monthly_emi,
        )