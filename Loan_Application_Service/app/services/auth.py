from sqlalchemy.exc import IntegrityError

from app.repositories.auth import DuplicateRegistrationError, RegistrationRepository
from app.schemas.auth import UserRegistration
from app.security import get_password_hash


class AuthService:
    def __init__(self, repository: RegistrationRepository) -> None:
        self.repository = repository

    def register_customer(self, registration: UserRegistration):
        db = self.repository.db
        normalized_email = str(registration.email).strip().lower()
        hashed_password = get_password_hash(registration.password)

        try:
            user = self.repository.register_customer(
                email=normalized_email,
                password_hash=hashed_password,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise DuplicateRegistrationError from exc
        except Exception:
            db.rollback()
            raise

        db.refresh(user)
        return user
