from app.repositories.auth import RegistrationRepository
from app.schemas.auth import UserRegistration
from app.security import get_password_hash


class AuthService:
    def __init__(self, repository: RegistrationRepository) -> None:
        self.repository = repository

    def register_customer(self, registration: UserRegistration):
        normalized_email = str(registration.email).strip().lower()
        hashed_password = get_password_hash(registration.password)

        return self.repository.register_customer(
            email=normalized_email,
            password_hash=hashed_password,
        )
