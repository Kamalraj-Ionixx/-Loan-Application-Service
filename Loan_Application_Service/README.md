# Loan Application Service

A REST API built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL** to manage customer records and loan applications with JWT authentication and role-based access control.

## Tech Stack

- Python 3.12+
- FastAPI
- SQLAlchemy 2 (ORM)
- PostgreSQL 16
- Psycopg 3
- Pydantic v2
- Alembic (migrations)
- JWT (PyJWT) + OAuth2 password flow
- pwdlib with Argon2 (password hashing)
- Pytest and HTTPX
- Ruff and Black (linting/formatting)
- pre-commit hooks
- uv (package manager)

## Features

- JWT-based authentication with OAuth2 password flow
- Role-based access control (CUSTOMER / OFFICER)
- Loan eligibility evaluation with automated approval/rejection
- EMI and interest rate calculation
- Customer loan summary with risk band classification
- Structured JSON request logging with request tracing
- Centralized error handling with consistent response format

## API Endpoints

### Authentication

| Method | Endpoint         | Description                  | Auth Required |
|--------|------------------|------------------------------|---------------|
| POST   | `/auth/register` | Register a new user account  | No            |
| POST   | `/auth/login`    | Log in and receive JWT token | No            |

### Customers

| Method | Endpoint                   | Description              | Roles            |
|--------|----------------------------|--------------------------|------------------|
| POST   | `/api/customers`           | Create a customer profile| CUSTOMER         |
| GET    | `/api/customers/{id}`      | Retrieve a customer      | CUSTOMER, OFFICER|

### Loans

| Method | Endpoint                          | Description                  | Roles            |
|--------|-----------------------------------|------------------------------|------------------|
| POST   | `/api/loans`                      | Submit a loan application    | CUSTOMER         |
| GET    | `/api/loans/{id}`                 | Retrieve a loan              | CUSTOMER, OFFICER|
| GET    | `/api/customers/{id}/loans`       | List a customer's loans      | CUSTOMER, OFFICER|
| GET    | `/api/customers/{id}/summary`     | Customer loan summary        | CUSTOMER, OFFICER|

### Health

| Method | Endpoint  | Description                        | Auth Required |
|--------|-----------|------------------------------------|---------------|
| GET    | `/health` | Check API and database availability| No            |

**Role access rules:**
- **CUSTOMER** — can only access their own data
- **OFFICER** — can view any customer's profile, loans, and summary (read-only)

## Prerequisites

- Python 3.12 or later
- PostgreSQL
- uv package manager — [installation guide](https://docs.astral.sh/uv/getting-started/installation/)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url> loan-application-service
cd loan-application-service
```

### 2. Install dependencies

```bash
uv sync --project ./Loan_Application_Service
```

### 3. Configure environment

Copy the example env file and update values:

```bash
cp Loan_Application_Service/.env.example Loan_Application_Service/.env
```

Set the following in `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/loan_db
JWT_SECRET_KEY=<generate-a-random-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Do not commit `.env` files to version control.

### 4. Start PostgreSQL

Using the included Docker Compose file:

```bash
docker compose -f ./Loan_Application_Service/docker-compose.yml up -d db
```

Create the test database:

```bash
docker compose -f ./Loan_Application_Service/docker-compose.yml exec db psql -U postgres -c "CREATE DATABASE loan_test_db;"
```

### 5. Apply database migrations

```bash
uv run --project ./Loan_Application_Service alembic -c ./Loan_Application_Service/alembic.ini upgrade head
```

## Running the Application

```bash
cd Loan_Application_Service
uv run uvicorn app.main:app --reload
```

The application will be available at:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **Health check:** http://127.0.0.1:8000/health

## API Usage

### 1. Register a user

```bash
POST /auth/register
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "mypassword123"
}
```

### 2. Log in

```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=john@example.com&password=mypassword123
```

Returns a JWT token:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### 3. Create a customer profile

```bash
POST /api/customers
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "9876543210",
  "date_of_birth": "1995-05-15",
  "monthly_income": 75000
}
```

### 4. Apply for a loan

```bash
POST /api/loans
Authorization: Bearer <token>
Content-Type: application/json

{
  "customer_id": 1,
  "amount": 500000,
  "tenure_months": 36
}
```

The service evaluates eligibility, calculates interest rate and EMI, and returns the loan with APPROVED or REJECTED status.

### 5. Filter loans by status

```
GET /api/customers/1/loans?status=APPROVED
```

### 6. View loan summary

```
GET /api/customers/1/summary
```

Returns loan counts, approved totals, EMI totals, EMI-to-income ratio, and risk band (LOW / MEDIUM / HIGH).

## Authentication Flow

1. **Register** → `POST /auth/register` — password is hashed with Argon2 and stored
2. **Login** → `POST /auth/login` — credentials verified, JWT token returned (expires in 30 minutes)
3. **Use API** → pass `Authorization: Bearer <token>` header on every protected request
4. **Token decoded** → user identity and role extracted, access enforced per endpoint

## Error Handling

| HTTP Status | Error Code          | Description                              |
|-------------|---------------------|------------------------------------------|
| 400         | `VALIDATION_FAILED` | Request fields fail validation           |
| 400         | `INVALID_REQUEST`   | Malformed or invalid JSON                |
| 401         | `UNAUTHORIZED`      | Missing or invalid authentication        |
| 403         | `FORBIDDEN`         | Insufficient role or accessing other data|
| 404         | `NOT_FOUND`         | Customer or loan does not exist          |
| 409         | `DUPLICATE_EMAIL`   | Email already registered                 |
| 500         | `INTERNAL_ERROR`    | Unexpected application error             |

## Application Architecture

```
Routers → Services → Repositories → Database
   ↑          ↑            ↑
Schemas    Security    SQLAlchemy Models
```

- **Routers** — handle HTTP requests, parameters, and response models
- **Services** — implement business rules (eligibility, EMI calculation)
- **Repositories** — encapsulate database queries and persistence
- **Schemas** — validate request data and define response structures
- **Security** — password hashing, JWT token creation/verification
- **Dependencies** — `get_current_user()` guard injected via FastAPI's `Depends()`

## Project Structure

```
Loan_Application_Service/
├── app/
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── routers/         # API route handlers
│   ├── services/        # Business logic
│   ├── repositories/    # Database operations
│   ├── config.py        # Settings from .env
│   ├── database.py      # Engine and session setup
│   ├── dependencies.py  # Auth guards (CurrentUser)
│   ├── exceptions.py    # Custom exceptions
│   ├── logging_config.py# Structured JSON logging
│   ├── main.py          # FastAPI app, middleware, error handlers
│   └── security.py      # JWT + password hashing
├── alembic/             # Database migrations
├── tests/
│   ├── api/             # Integration tests
│   └── unit/            # Unit tests
├── .env.example
├── .pre-commit-config.yaml
├── docker-compose.yml
└── pyproject.toml
```

## Testing

Run all tests:

```bash
uv run pytest
```

With verbose output:

```bash
uv run pytest -v
```

Tests require a separate `loan_test_db` database. The test fixtures automatically apply migrations and clean data between tests.

## Code Quality

Run pre-commit hooks:

```bash
uv run pre-commit run --all-files
```

Lint with Ruff:

```bash
uv run ruff check .
```

Format with Black:

```bash
uv run black .
```

## License

Add the applicable license information here.
