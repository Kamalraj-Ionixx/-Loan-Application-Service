from pydantic import BaseModel


class ValidationErrorDetail(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    error: str
    details: list[ValidationErrorDetail]
    request_id: str


class ErrorResponse(BaseModel):
    error: str
    message: str | None = None
    request_id: str