from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database import engine
from app.exceptions import DuplicateEmailError
from app.routers.customers import router as customer_router

app = FastAPI(
    title="Loan API",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=400,
        content={
            "errors": [
                {
                    "field": ".".join(
                        str(location)
                        for location in error["loc"]
                        if location != "body"
                    ),
                    "message": error["msg"],
                }
                for error in exc.errors()
            ]
        },
    )


@app.exception_handler(DuplicateEmailError)
async def duplicate_email_handler(
    request: Request,
    exc: DuplicateEmailError,
):
    return JSONResponse(
        status_code=409,
        content={
            "error": "DUPLICATE_EMAIL",
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


app.include_router(customer_router)
