from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


class DuplicateRegistrationError(Exception):
    """Raised when an email is already registered."""


class RegistrationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register_customer(
        self,
        email: str,
        password_hash: str,
    ) -> User:
        normalized_email = email.strip().lower()

        try:
            existing_user = self.db.scalar(
                select(User).where(
                    func.lower(User.email) == normalized_email
                )
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
            self.db.commit()
            self.db.refresh(user)

            return user

        except DuplicateRegistrationError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateRegistrationError from exc
        except Exception:
            self.db.rollback()
            raise
