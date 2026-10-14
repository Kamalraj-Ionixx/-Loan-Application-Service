from datetime import datetime, timedelta


def authenticate_customer(client, email: str = "arun@example.com") -> None:
    password = "test-password-123"

    registration = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert registration.status_code == 201, registration.text

    login = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200, login.text

    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"


def valid_customer_payload(**overrides: object) -> dict:
    payload = {
        "name": "Arun Kumar",
        "email": "arun@example.com",
        "phone": "9876543210",
        "date_of_birth": str(
            datetime.now().astimezone().date() - timedelta(days=30 * 365)
        ),
        "monthly_income": "50000.00",
    }
    payload.update(overrides)
    return payload


def valid_loan_payload(customer_id: int, **overrides: object) -> dict:
    payload = {
        "customer_id": customer_id,
        "amount": "300000.00",
        "tenure_months": 36,
    }
    payload.update(overrides)
    return payload


def create_customer(client, **overrides: object) -> dict:
    response = client.post(
        "/api/customers",
        json=valid_customer_payload(**overrides),
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_loan(client, customer_id: int, **overrides: object) -> dict:
    response = client.post(
        "/api/loans",
        json=valid_loan_payload(customer_id, **overrides),
    )
    assert response.status_code == 201, response.text
    return response.json()
