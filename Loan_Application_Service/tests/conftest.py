import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from tests.api.helpers import authenticate_customer

# Set this before importing the application, because database.py creates
# its SQLAlchemy engine when it is imported.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/loan_test_db",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-only-secret-key-long-enough-for-hs256",
)

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def migrate_test_database() -> Generator[None, None, None]:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option(
        "sqlalchemy.url",
        TEST_DATABASE_URL.replace("%", "%%"),
    )

    command.upgrade(config, "head")
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

    testing_session = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        autocommit=False,
    )

    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE TABLE loans, customers, users RESTART IDENTITY CASCADE")
        )

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            authenticate_customer(test_client)
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.fixture
def unauthenticated_client() -> Generator[TestClient, None, None]:
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

    testing_session = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        autocommit=False,
    )

    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE TABLE loans, customers, users RESTART IDENTITY CASCADE")
        )

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
