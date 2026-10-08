import json
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database import engine
from app.exceptions import DuplicateEmailError, NotFoundError


logging.basicConfig(
    level=logging.INFO,
    format=(
        '{"level":"%(levelname)s",'
        '"request_id":"%(request_id)s",'
        '"message":"%(message)s"}'
    ),
)

logger = logging.getLogger("loan-api")


app = FastAPI(
    title="Loan Application Service",
)


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

    try:
        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response

    except Exception:
        logger.exception(
            "Unhandled application error",
            extra={
                "request_id": request_id,
            },
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "request_id": request_id,
            },
            headers={
                "X-Request-ID": request_id,
            },
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
):
    details = []

    for error in exc.errors():
        location = error.get("loc", [])

        field_parts = [
            str(part)
            for part in location
            if part not in {"body", "query", "path"}
        ]

        field = ".".join(field_parts)

        if not field:
            field = "request"

        message = error.get(
            "msg",
            "Invalid value",
        )

        if message.startswith("Value error, "):
            message = message.removeprefix(
                "Value error, "
            )

        details.append(
            {
                "field": field,
                "message": message,
            }
        )

    request_id = get_request_id(request)

    return JSONResponse(
        status_code=400,
        content={
            "error": "VALIDATION_FAILED",
            "details": details,
            "request_id": request_id,
        },
    )


@app.exception_handler(DuplicateEmailError)
async def duplicate_email_handler(
    request: Request,
    exc: DuplicateEmailError,
):
    request_id = get_request_id(request)

    return JSONResponse(
        status_code=409,
        content={
            "error": "DUPLICATE_EMAIL",
            "request_id": request_id,
        },
    )


@app.exception_handler(NotFoundError)
async def not_found_handler(
    request: Request,
    exc: NotFoundError,
):
    request_id = get_request_id(request)

    return JSONResponse(
        status_code=404,
        content={
            "error": "NOT_FOUND",
            "message": str(exc),
            "request_id": request_id,
        },
    )


@app.exception_handler(json.JSONDecodeError)
async def invalid_json_handler(
    request: Request,
    exc: json.JSONDecodeError,
):
    request_id = get_request_id(request)

    return JSONResponse(
        status_code=400,
        content={
            "error": "INVALID_REQUEST",
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


from app.routers.customers import router as customer_router
from app.routers.loans import router as loan_router


app.include_router(customer_router)
app.include_router(loan_router)