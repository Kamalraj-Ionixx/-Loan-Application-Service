from app.models.customer import Customer
from app.models.user import User
from app.repositories.customer import CustomerRepository


class CustomerService:
    def __init__(self, repository: CustomerRepository) -> None:
        self.repository = repository

    def create_customer_for_user(
        self,
        user: User,
        customer_data: dict,
    ) -> Customer:
        return self.repository.create_customer_for_user(
            user=user,
            customer_data=customer_data,
        )

    def get_customer(self, customer_id: int) -> Customer | None:
        return self.repository.get_by_id(customer_id)
