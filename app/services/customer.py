from sqlalchemy.orm import Session

from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate


class CustomerService:
    def __init__(
        self,
        repository: CustomerRepository,
    ):
        self.repository = repository

    def create_customer(
        self,
        db: Session,
        customer_data: CustomerCreate,
    ):
        return self.repository.create(
            db,
            customer_data,
        )

    def get_customer(
        self,
        db: Session,
        customer_id: int,
    ):
        return self.repository.get_by_id(
            db,
            customer_id,
        )