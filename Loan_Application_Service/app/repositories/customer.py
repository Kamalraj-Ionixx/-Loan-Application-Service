from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.user import User


class DuplicateCustomerEmailError(Exception):
    """Raised when a customer email is already registered."""


class CustomerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_customer_for_user(
        self,
        user: User,
        customer_data: dict,
    ) -> Customer:
        try:
            if user.customer_id is not None:
                raise ValueError("Customer profile already exists.")

            email = str(customer_data["email"]).strip().lower()

            if email != user.email.strip().lower():
                raise ValueError(
                    "Customer profile email must match the registered email."
                )

            existing_customer = self.db.scalar(
                select(Customer).where(Customer.email == email)
            )

            if existing_customer is not None:
                raise DuplicateCustomerEmailError

            customer = Customer(
                name=customer_data["name"],
                email=email,
                phone=customer_data["phone"],
                date_of_birth=customer_data["date_of_birth"],
                monthly_income=customer_data["monthly_income"],
            )

            self.db.add(customer)
            self.db.flush()

            user.customer_id = customer.id

            self.db.commit()
            self.db.refresh(customer)

            return customer

        except (ValueError, DuplicateCustomerEmailError):
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateCustomerEmailError from exc
        except Exception:
            self.db.rollback()
            raise

    def get_by_id(self, customer_id: int) -> Customer | None:
        return self.db.get(Customer, customer_id)
