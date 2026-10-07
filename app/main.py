from fastapi import FastAPI
from sqlalchemy import text
from app.database import engine

app = FastAPI()


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
