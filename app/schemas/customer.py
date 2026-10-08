from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CustomerCreate(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=50,
    )

    email: EmailStr

    phone: str

    date_of_birth: date

    monthly_income: Decimal = Field(
        gt=0,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value or not all(
            character.isalpha() or character == " "
            for character in value
        ):
            raise ValueError(
                "must contain only letters and spaces"
            )

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not value.isascii() or not value.isdigit() or len(value) != 10:
            raise ValueError(
                "must be exactly 10 digits"
            )

        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date) -> date:
        if value >= date.today():
            raise ValueError(
                "must be in the past"
            )

        return value


class CustomerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    date_of_birth: date
    monthly_income: Decimal

    model_config = ConfigDict(
        from_attributes=True,
    )