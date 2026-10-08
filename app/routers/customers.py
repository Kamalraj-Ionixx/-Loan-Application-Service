from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.customer import CustomerRepository
from app.repositories.loan import LoanRepository
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.schemas.loan import LoanResponse, LoanStatus, LoanSummaryResponse
from app.services.customer import CustomerService
from app.services.loan import LoanService


router = APIRouter(
    prefix="/api/customers",
    tags=["customers"],
)


def get_customer_service() -> CustomerService:
    return CustomerService(
        CustomerRepository(),
    )


def get_loan_service() -> LoanService:
    return LoanService(
        CustomerRepository(),
        LoanRepository(),
    )


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
):
    return service.create_customer(
        db,
        customer_data,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
):
    customer = service.get_customer(
        db,
        customer_id,
    )

    if customer is None:
        from app.exceptions import NotFoundError

        raise NotFoundError(
            f"Customer with id {customer_id} not found"
        )

    return customer


@router.get(
    "/{customer_id}/loans",
    response_model=list[LoanResponse],
)
def get_customer_loans(
    customer_id: int = Path(gt=0),
    status_filter: LoanStatus | None = Query(
        default=None,
        alias="status",
    ),
    db: Session = Depends(get_db),
    service: LoanService = Depends(get_loan_service),
):
    return service.get_customer_loans(
        db,
        customer_id,
        status_filter,
    )


@router.get(
    "/{customer_id}/summary",
    response_model=LoanSummaryResponse,
)
def get_customer_summary(
    customer_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    service: LoanService = Depends(get_loan_service),
):
    return service.get_summary(
        db,
        customer_id,
    )