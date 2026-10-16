from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security import decode_access_token


DbSession = Annotated[Session, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")

        if not isinstance(subject, str) or not subject.isdigit():
            raise unauthorized

        user_id = int(subject)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise unauthorized from None

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise unauthorized

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_customer_profile(user: CurrentUser) -> User:
    if user.role != "CUSTOMER" or user.customer_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Create your customer profile before accessing this resource.",
        )

    return user


def require_officer(user: CurrentUser) -> User:
    if user.role != "OFFICER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Officer permission is required.",
        )

    return user
