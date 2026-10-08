from datetime import date
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LoanStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Loan(Base):
    __tablename__ = "loans"

    __table_args__ = (
        CheckConstraint(
            "amount >= 10000 AND amount <= 5000000",
            name="ck_loans_amount_range",
        ),
        CheckConstraint(
            "tenure_months IN (12, 24, 36, 48, 60)",
            name="ck_loans_tenure",
        ),
        CheckConstraint(
            "interest_rate >= 0",
            name="ck_loans_interest_rate",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    tenure_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    emi: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    status: Mapped[LoanStatus] = mapped_column(
        String(20),
        nullable=False,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    applied_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="loans",
    )