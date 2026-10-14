
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentUser
from app.exceptions import NotFoundError
from app.models.customer import Customer
from app.models.loan import LoanStatus
from app.models.user import User
from app.repositories.loan import LoanRepository
from app.schemas.loan import LoanCreate, LoanResponse, LoanSummaryResponse
from app.services.loan import LoanService

router = APIRouter(tags=["Loans"])


def get_loan_service(
    db: Annotated[Session, Depends(get_db)],
) -> LoanService:
    """Create the loan service using the request's database session."""
    return LoanService(LoanRepository(db))


LoanServiceDependency = Annotated[LoanService, Depends(get_loan_service)]


def get_linked_customer(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Customer:
    """Return the authenticated customer's linked profile."""
    if user.role != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can access these loan endpoints.",
        )

    if user.customer_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Create your customer profile before accessing loans.",
        )

    customer = db.get(Customer, user.customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid customer profile is required.",
        )

    return customer


LinkedCustomer = Annotated[Customer, Depends(get_linked_customer)]


def resolve_customer(
    user: User,
    customer_id: int,
    db: Session,
) -> Customer:
    """Return the requested customer, enforcing ownership for CUSTOMER role."""
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise NotFoundError("Customer not found.")

    if user.role == "OFFICER":
        return customer

    if user.role == "CUSTOMER" and user.customer_id == customer.id:
        return customer

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You cannot access another customer's data.",
    )


@router.post(
    "/api/loans",
    response_model=LoanResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_for_loan(
    loan_data: LoanCreate,
    customer: LinkedCustomer,
    service: LoanServiceDependency,
    db: Annotated[Session, Depends(get_db)],
) -> LoanResponse:
    """Apply for a loan for the authenticated customer."""
    if loan_data.customer_id != customer.id:
        other = db.get(Customer, loan_data.customer_id)
        if other is None:
            raise NotFoundError("Customer not found.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot apply for a loan on another customer's behalf.",
        )

    loan = service.apply_loan(
        customer=customer,
        amount=loan_data.amount,
        tenure_months=loan_data.tenure_months,
    )

    return LoanResponse.model_validate(loan)


@router.get(
    "/api/loans/{loan_id}",
    response_model=LoanResponse,
)
def get_loan(
    loan_id: Annotated[int, Path(gt=0)],
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> LoanResponse:
    """Retrieve a loan. Officers can view any; customers only their own."""
    repository = LoanRepository(db)
    loan = repository.get_by_id(loan_id)

    if loan is None:
        raise NotFoundError("Loan not found.")

    if user.role != "OFFICER":
        if user.customer_id is None or loan.customer_id != user.customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access another customer's loan.",
            )

    return LoanResponse.model_validate(loan)


@router.get(
    "/api/customers/{customer_id}/loans",
    response_model=list[LoanResponse],
)
def get_customer_loans(
    customer_id: Annotated[int, Path(gt=0)],
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    loan_status: Annotated[
        LoanStatus | None,
        Query(alias="status"),
    ] = None,
) -> list[LoanResponse]:
    """List a customer's loans. Officers can view any; customers only their own."""
    customer = resolve_customer(user, customer_id, db)

    loans = LoanRepository(db).get_customer_loans(
        customer_id=customer.id,
        status=loan_status,
    )

    return [LoanResponse.model_validate(loan) for loan in loans]


@router.get(
    "/api/customers/{customer_id}/summary",
    response_model=LoanSummaryResponse,
)
def get_customer_loan_summary(
    customer_id: Annotated[int, Path(gt=0)],
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> LoanSummaryResponse:
    """Calculate a customer's loan summary. Officers can view any."""
    customer = resolve_customer(user, customer_id, db)

    repository = LoanRepository(db)
    totals = repository.get_summary_totals(customer.id)

    total_applications = totals["total_applications"]
    approved_count = totals["approved_count"]
    rejected_count = totals["rejected_count"]
    total_approved_amount = totals["total_approved_amount"]
    total_monthly_emi = totals["total_monthly_emi"]

    if customer.monthly_income > 0:
        emi_to_income_ratio = (
            total_monthly_emi / customer.monthly_income * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        emi_to_income_ratio = Decimal("0.00")

    if emi_to_income_ratio < Decimal("30.00"):
        risk_band = "LOW"
    elif emi_to_income_ratio <= Decimal("50.00"):
        risk_band = "MEDIUM"
    else:
        risk_band = "HIGH"

    return LoanSummaryResponse(
        customer_id=customer.id,
        customer_name=customer.name,
        total_applications=total_applications,
        approved_count=approved_count,
        rejected_count=rejected_count,
        total_approved_amount=total_approved_amount,
        total_monthly_emi=total_monthly_emi,
        emi_to_income_ratio=emi_to_income_ratio,
        risk_band=risk_band,
    )
