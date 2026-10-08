from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import DuplicateEmailError
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate


class CustomerRepository:
    @staticmethod
    def create(
        db: Session,
        customer_data: CustomerCreate,
    ) -> Customer:
        customer = Customer(
            name=customer_data.name,
            email=str(customer_data.email),
            phone=customer_data.phone,
            date_of_birth=customer_data.date_of_birth,
            monthly_income=customer_data.monthly_income,
        )

        db.add(customer)

        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()

            if "uq_customers_email" in str(exc.orig):
                raise DuplicateEmailError from exc

            raise

        db.refresh(customer)

        return customer

    @staticmethod
    def get_by_id(
        db: Session,
        customer_id: int,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.id == customer_id
        )

        return db.scalar(statement)