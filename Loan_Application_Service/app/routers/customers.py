from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentUser
from app.exceptions import NotFoundError
from app.repositories.customer import (
    CustomerRepository,
    DuplicateCustomerEmailError,
)
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.services.customer import CustomerService

router = APIRouter(
    prefix="/api/customers",
    tags=["Customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    customer_data: CustomerCreate,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CustomerResponse:
    if user.role != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customer accounts can create customer profiles.",
        )

    if user.customer_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer profile already exists for this account.",
        )

    service = CustomerService(CustomerRepository(db))

    try:
        customer = service.create_customer_for_user(
            user=user,
            customer_data=customer_data.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DuplicateCustomerEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DUPLICATE_EMAIL",
                "message": "A customer with this email already exists.",
            },
        ) from None

    return CustomerResponse.model_validate(customer)


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CustomerResponse:
    customer = CustomerService(CustomerRepository(db)).get_customer(customer_id)

    if customer is None:
        raise NotFoundError("Customer not found.")

    if user.role == "OFFICER":
        pass
    elif user.role == "CUSTOMER" and user.customer_id == customer.id:
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another customer's profile.",
        )

    return CustomerResponse.model_validate(customer)
