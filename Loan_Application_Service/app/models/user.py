from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint(
            "email",
            name="uq_users_email",
        ),
        CheckConstraint(
            "role IN ('CUSTOMER', 'OFFICER')",
            name="ck_users_role",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        unique=True,
    )

    customer: Mapped["Customer | None"] = relationship(
        "Customer",
    )
