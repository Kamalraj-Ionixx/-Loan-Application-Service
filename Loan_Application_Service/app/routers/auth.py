from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select

from app.dependencies import DbSession
from app.models.user import User
from app.repositories.auth import (
    DuplicateRegistrationError,
    RegistrationRepository,
)
from app.schemas.auth import TokenResponse, UserRegistration
from app.security import create_access_token, verify_password
from app.services.auth import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register_customer(
    registration: UserRegistration,
    db: DbSession,
) -> dict[str, str | int]:
    service = AuthService(RegistrationRepository(db))

    try:
        user = service.register_customer(registration)
    except DuplicateRegistrationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DUPLICATE_EMAIL",
                "message": "An account with this email already exists.",
            },
        ) from None

    return {
        "message": "Registration successful. Log in to continue.",
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and receive an access token",
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> TokenResponse:
    email = form_data.username.strip().lower()

    user = db.scalar(select(User).where(func.lower(User.email) == email))

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        raise invalid_credentials

    if not verify_password(form_data.password, user.password_hash):
        raise invalid_credentials

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return TokenResponse(access_token=token)
