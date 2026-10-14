
# Loan Application Service

A REST API built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL** to manage customer records and loan applications.

## Tech Stack

- Python 3.12+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Psycopg 3
- Pydantic
- Alembic
- Pytest and HTTPX
- Ruff and Black

## Features

### Customer APIs

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/customer` | Create a customer |
| GET | `/api/customer/{customer_id}` | Retrieve a customer |
| GET | `/api/customer/{customer_id}/loans` | List a customer's loans |
| GET | `/api/customer/{customer_id}/summary` | Retrieve a customer's loan summary |

### Loan APIs

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/loans` | Submit a loan application |
| GET | `/api/loans/{loan_id}` | Retrieve a loan application |

### Health Check

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API and database availability |

## Prerequisites

Install the following:

- Python 3.12 or later
- PostgreSQL
- uv package manager

Install uv by following the official guide:

https://docs.astral.sh/uv/getting-started/installation/

## Installation

### 1. Clone the repository

```bash
git clone <repository-url> loan-application-service
cd loan-application-service
```

Replace `<repository-url>` with your repository URL. Keep the shell in the
repository root and use the nested project path for `uv` commands.

### 2. Install dependencies

```bash
uv sync --project ./Loan_Application_Service
```

### 3. Configure the database

Create a PostgreSQL database named `loan_db` for the application. To use the
PostgreSQL service in the supplied Compose file, start it with:

```bash
docker compose -f ./Loan_Application_Service/docker-compose.yml up -d db
```

Create the separate test database if it does not already exist:

```bash
docker compose -f ./Loan_Application_Service/docker-compose.yml exec db psql -U postgres -c "CREATE DATABASE loan_test_db;"
```

Copy `.env.example` to `.env` and set `DATABASE_URL` to your database
connection and `JWT_SECRET_KEY` to a private random secret of at least 32
characters. Do not use the example placeholder as a production secret.

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/loan_db
```

The tests use a separate database named `loan_test_db` by default (or the
database specified by `TEST_DATABASE_URL`). Create that database on the same
PostgreSQL server before running tests. Keep it separate from `loan_db`; the
test fixtures clear test data.

Do not commit database credentials or `.env` files to version control.

### 4. Apply database migrations

Apply the database migrations:

```bash
uv run --project ./Loan_Application_Service alembic -c ./Loan_Application_Service/alembic.ini upgrade head
```

## Running the Application

From the repository root, with the project environment active, start the
development server with:

```powershell
. .\Loan_Application_Service\.venv\Scripts\Activate.ps1
uv run uvicorn app.main:app --reload
```

The application will be available at:

- **API base URL:** http://127.0.0.1:8000
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **Health check:** http://127.0.0.1:8000/health

## API Usage

### Create a customer

**Endpoint:** `POST /api/customer`

Content-Type: `application/json`

Example request:

```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "9876543210",
  "date_of_birth": "1995-05-15",
  "monthly_income": 75000
}
```

The response should contain the saved customer details and generated customer ID.

### Retrieve a customer

**Endpoint:** `GET /api/customer/1`

### Apply for a loan

**Endpoint:** `POST /api/loans`

Content-Type: `application/json`

Example request:

```json
{
  "customer_id": 1,
  "amount": 500000,
  "tenure_months": 36
}
```

The service should evaluate eligibility, calculate the applicable interest rate and EMI, and return the saved loan application.

### Retrieve a loan

**Endpoint:** `GET /api/loans/1`

### List customer loans

**Endpoint:** `GET /api/customer/1/loans`

Filter loans by status:

```http
GET /api/customer/1/loans?status=APPROVED
```

Supported statuses are `APPROVED` and `REJECTED`, subject to the implemented validation rules.

### Retrieve customer loan summary

**Endpoint:** `GET /api/customer/1/summary`

The summary endpoint is intended to provide loan counts, approved loan totals, EMI totals, and a risk classification.

## Error Handling

The application defines centralized exception handlers for common errors.

| HTTP status | Error code | Description |
|---|---|---|
| 400 | `VALIDATION_FAILED` | Request fields fail validation |
| 400 | `INVALID_REQUEST` | Malformed or invalid JSON request |
| 404 | `NOT_FOUND` | Requested customer or loan does not exist |
| 409 | `DUPLICATE_EMAIL` | Customer email already exists |
| 500 | `INTERNAL_ERROR` | Unexpected application error |

Ensure that response fields and validation messages match the assessment requirements.

## Application Architecture

The application separates HTTP request handling from business logic and database operations.

- **Routers:** Handle HTTP requests, parameters, and response models.
- **Services:** Implement business rules and calculations.
- **Repositories:** Encapsulate database queries and persistence.
- **Schemas:** Validate request data and define response structures.
- **Database module:** Provides SQLAlchemy database sessions.

FastAPI's `Depends()` mechanism is used to inject service instances and database sessions into endpoints.

## Testing

Run the test suite:

```bash
uv run pytest
```

Run tests with detailed output:

```bash
uv run pytest -v
```

Recommended test cases include:

- Customer field validation
- Duplicate email handling
- Missing customer and loan records
- Loan eligibility rules
- Interest rate and EMI calculations
- Approved and rejected loan applications
- Loan filtering and sorting
- Customer loan summary calculations
- Error response formats

## Code Quality

Run Ruff checks:

```bash
uv run ruff check .
```

Format code with Ruff:

```bash
uv run ruff format .
```

Alternatively, format the code with Black:

```bash
uv run black .
```

## Security and Configuration

- Keep database credentials in environment variables.
- Do not commit secrets or production credentials.
- Avoid exposing internal tracebacks in API responses.
- Use database transactions appropriately when creating records.
- Validate incoming request data before processing business rules.

## License

Add the applicable license information here.
