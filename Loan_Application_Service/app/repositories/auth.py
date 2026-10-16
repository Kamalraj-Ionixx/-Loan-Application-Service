from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


class DuplicateRegistrationError(Exception):
    """Raised when an email is already registered."""


class RegistrationRepository:
    """Database operations for users. Never commits; the service owns the transaction."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def register_customer(
        self,
        email: str,
        password_hash: str,
    ) -> User:
        normalized_email = email.strip().lower()

        existing_user = self.db.scalar(
            select(User).where(func.lower(User.email) == normalized_email)
        )
        if existing_user is not None:
            raise DuplicateRegistrationError

        user = User(
            email=normalized_email,
            password_hash=password_hash,
            role="CUSTOMER",
            is_active=True,
            customer_id=None,
        )
        self.db.add(user)
        self.db.flush()
        return user
