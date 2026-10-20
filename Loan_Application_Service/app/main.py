import json
import time
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import engine
from app.exceptions import DuplicateEmailError, NotFoundError
from app.logging_config import configure_logging, logger
from app.security import decode_access_token

configure_logging()

app = FastAPI(
    title="Loan Application Service",
)


HTTP_ERROR_RESPONSES = {
    status.HTTP_400_BAD_REQUEST: (
        "BAD_REQUEST",
        "The request could not be processed.",
    ),
    status.HTTP_401_UNAUTHORIZED: (
        "UNAUTHORIZED",
        "Authentication is required or invalid.",
    ),
    status.HTTP_403_FORBIDDEN: (
        "FORBIDDEN",
        "You are not authorized to perform this action.",
    ),
    status.HTTP_404_NOT_FOUND: (
        "NOT_FOUND",
        "The requested resource was not found.",
    ),
    status.HTTP_409_CONFLICT: (
        "CONFLICT",
        "The request conflicts with the current resource state.",
    ),
}


@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next,
):
    request_id = request.headers.get(
        "X-Request-ID",
        str(uuid.uuid4()),
    )

    request.state.request_id = request_id

    user_id = "anonymous"
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            payload = decode_access_token(auth_header[7:])
            user_id = payload.get("sub", "anonymous")
        except Exception:
            pass
    request.state.user_id = user_id

    client_ip = request.client.host if request.client else "-"
    log_extra = {
        "request_id": request_id,
        "user_id": user_id,
        "client_ip": client_ip,
    }

    start = time.perf_counter()

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s → %s",
            request.method,
            request.url.path,
            response.status_code,
            extra={
                **log_extra,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            "Unhandled application error",
            extra={**log_extra, "status_code": 500, "duration_ms": duration_ms},
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )


def get_request_id(request: Request) -> str:
    return getattr(
        request.state,
        "request_id",
        str(uuid.uuid4()),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    request_id = get_request_id(request)
    errors = exc.errors()

    if any(error["type"] == "json_invalid" for error in errors):
        return JSONResponse(
            status_code=400,
            content={
                "error": "INVALID_REQUEST",
                "message": "The request could not be processed.",
                "request_id": request_id,
            },
        )

    details = []

    for error in errors:
        field_parts = [str(part) for part in error["loc"] if part != "body"]

        details.append(
            {
                "field": ".".join(field_parts) or "body",
                "message": "Invalid value.",
            }
        )

    return JSONResponse(
        status_code=400,
        content={
            "error": "VALIDATION_FAILED",
            "message": "The request could not be processed.",
            "details": details,
            "request_id": request_id,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    error, message = HTTP_ERROR_RESPONSES.get(
        exc.status_code,
        (
            "HTTP_ERROR",
            "The request could not be completed.",
        ),
    )

    # Routes may raise a deliberate public code, e.g. detail={"error": "DUPLICATE_EMAIL", ...}
    if isinstance(exc.detail, dict) and {"error", "message"} <= exc.detail.keys():
        error, message = exc.detail["error"], exc.detail["message"]

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error,
            "message": message,
            "request_id": get_request_id(request),
        },
        headers=exc.headers,
    )


@app.exception_handler(DuplicateEmailError)
async def duplicate_email_handler(
    request: Request,
    exc: DuplicateEmailError,
) -> JSONResponse:
    request_id = get_request_id(request)

    return JSONResponse(
        status_code=409,
        content={
            "error": "DUPLICATE_EMAIL",
            "message": "The request conflicts with the current resource state.",
            "request_id": request_id,
        },
    )


@app.exception_handler(NotFoundError)
async def not_found_handler(
    request: Request,
    exc: NotFoundError,
) -> JSONResponse:
    request_id = get_request_id(request)

    return JSONResponse(
        status_code=404,
        content={
            "error": "NOT_FOUND",
            "message": "The requested resource was not found.",
            "request_id": request_id,
        },
    )


@app.exception_handler(json.JSONDecodeError)
async def invalid_json_handler(
    request: Request,
    exc: json.JSONDecodeError,
) -> JSONResponse:
    request_id = get_request_id(request)

    return JSONResponse(
        status_code=400,
        content={
            "error": "INVALID_REQUEST",
            "message": "The request could not be processed.",
            "request_id": request_id,
        },
    )


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "ok",
        }

    except Exception:
        return {
            "status": "error",
            "database": "unavailable",
        }


from app.routers.auth import router as auth_router  # noqa: E402
from app.routers.customers import router as customer_router  # noqa: E402
from app.routers.loans import router as loan_router  # noqa: E402

app.include_router(customer_router)
app.include_router(loan_router)
app.include_router(auth_router)
