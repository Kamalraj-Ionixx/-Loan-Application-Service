from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.customer import CustomerRepository
from app.repositories.loan import LoanRepository
from app.schemas.loan import LoanCreate, LoanResponse
from app.services.loan import LoanService


router = APIRouter(
    prefix="/api/loans",
    tags=["loans"],
)


def get_loan_service() -> LoanService:
    return LoanService(
        CustomerRepository(),
        LoanRepository(),
    )


@router.post(
    "",
    response_model=LoanResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_loan(
    loan_data: LoanCreate,
    db: Session = Depends(get_db),
    service: LoanService = Depends(get_loan_service),
):
    return service.apply_loan(
        db,
        loan_data,
    )


@router.get(
    "/{loan_id}",
    response_model=LoanResponse,
)
def get_loan(
    loan_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    service: LoanService = Depends(get_loan_service),
):
    return service.get_loan(
        db,
        loan_id,
    )