from sqlalchemy.exc import IntegrityError

from app.models.customer import Customer
from app.models.user import User
from app.repositories.customer import CustomerRepository, DuplicateCustomerEmailError


class CustomerService:
    def __init__(self, repository: CustomerRepository) -> None:
        self.repository = repository

    def create_customer_for_user(
        self,
        user: User,
        customer_data: dict,
    ) -> Customer:
        """Create the profile and link it to the user in one transaction."""
        db = self.repository.db

        try:
            customer = self.repository.create_customer_for_user(
                user=user,
                customer_data=customer_data,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise DuplicateCustomerEmailError from exc
        except Exception:
            db.rollback()
            raise

        db.refresh(customer)
        return customer

    def get_customer(self, customer_id: int) -> Customer | None:
        return self.repository.get_by_id(customer_id)
