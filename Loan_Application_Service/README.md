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
| GET    | `/api/loans?status=&page=&size=`  | Paginated loan list (officers: all, customers: own) | CUSTOMER, OFFICER|
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

## Quick Start (Docker)

The only requirements are **Git** and **Docker Desktop**. You don't need Python or PostgreSQL installed.

### 1. Clone the repository

```bash
git clone https://github.com/Kamalraj-Ionixx/-Loan-Application-Service.git loan-app
cd loan-app/Loan_Application_Service
```

The trailing `loan-app` gives the folder a simple name. A folder name starting with `-` can be mistaken for a command option.

### 2. Create your `.env`

```bash
cp .env.example .env
```

Then edit `.env` and set:

- `POSTGRES_PASSWORD`: any password for the local database
- `JWT_SECRET_KEY`: a long random secret, for example generated with
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`

Secrets are read only from the environment. `.env` is gitignored, so never commit it.

### 3. Start the API and the database

```bash
docker compose up -d --build
```

This builds the API image, starts PostgreSQL, waits until it is healthy, runs the
Alembic migrations, and starts FastAPI.

### 4. Open the app

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **Health check:** http://127.0.0.1:8000/health returns `{"status":"ok","database":"ok"}`

Useful commands:

```bash
docker compose ps            # container status
docker compose logs -f api   # structured JSON request logs
docker compose down          # stop (data is kept in the postgres_data volume)
```

### Creating an officer account

Registration always creates `CUSTOMER` accounts. To create an `OFFICER`, register
normally and then promote the user in the database:

```bash
docker compose exec db psql -U postgres -d loan_db -c "UPDATE users SET role='OFFICER' WHERE email='officer@example.com';"
```

## Local Development

To edit code with auto-reload, you also need **Python 3.12+** and
[uv](https://docs.astral.sh/uv/getting-started/installation/). Run the database in
Docker and the API locally:

```bash
docker compose up -d db
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

`DATABASE_URL` in `.env` must point at `localhost:5432`. The example file already
does. Stop the `api` container first (`docker compose stop api`), because only one
process can use port 8000.

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
├── docs/adr/            # Architecture Decision Records
├── tests/
│   ├── api/             # API tests (success and failure paths)
│   └── unit/            # Unit tests (EMI, eligibility)
├── .env.example
├── .pre-commit-config.yaml
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml

.github/workflows/ci.yml # CI pipeline (at the repository root)
```

## Testing

Tests use a separate `loan_test_db` database. Create it once:

```bash
docker compose up -d db
docker compose exec db psql -U postgres -c "CREATE DATABASE loan_test_db;"
```

Run the tests, with coverage:

```bash
uv run pytest --cov=app
```

The fixtures apply migrations automatically and clear data between tests.

## Continuous Integration

GitHub Actions runs on every pull request and every push to `main`:
`ruff check`, then `ruff format --check`, then `pytest` with at least 80% coverage
against a temporary PostgreSQL service. Results appear on the PR and in the
**Actions** tab.

## Architecture Decisions

- [ADR 0001: JWT vs session auth](docs/adr/0001-jwt-vs-session-auth.md)

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
