from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoanStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LoanCreate(BaseModel):
    customer_id: int = Field(
        gt=0,
    )

    amount: Decimal = Field(
        ge=10000,
        le=5000000,
    )

    tenure_months: int

    @field_validator("tenure_months")
    @classmethod
    def validate_tenure(cls, value: int) -> int:
        if value not in {12, 24, 36, 48, 60}:
            raise ValueError(
                "must be one of 12, 24, 36, 48, 60"
            )

        return value


class LoanResponse(BaseModel):
    id: int
    customer_id: int
    amount: Decimal
    tenure_months: int
    interest_rate: Decimal
    emi: Decimal | None
    status: LoanStatus
    rejection_reason: str | None
    applied_on: date

    model_config = ConfigDict(
        from_attributes=True,
    )


class LoanSummaryResponse(BaseModel):
    customer_id: int
    customer_name: str
    total_applications: int
    approved_count: int
    rejected_count: int
    total_approved_amount: Decimal
    total_monthly_emi: Decimal
    emi_to_income_ratio: Decimal
    risk_band: str