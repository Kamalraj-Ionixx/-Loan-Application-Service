from datetime import datetime

from tests.api.helpers import (
    create_customer,
    create_loan,
    valid_loan_payload,
)


def test_apply_loan_approved(client):
    customer = create_customer(client)

    response = client.post(
        "/api/loans",
        json=valid_loan_payload(customer["id"]),
    )

    assert response.status_code == 201, response.text
    loan = response.json()

    assert loan["customer_id"] == customer["id"]
    assert loan["status"] == "APPROVED"
    assert loan["interest_rate"] == "12.00"
    assert loan["emi"] == "9964.29"
    assert loan["rejection_reason"] is None
    assert loan["applied_on"] == str(datetime.now().astimezone().date())


def test_apply_loan_rejected_for_age(client):
    customer = create_customer(
        client,
        date_of_birth="2010-01-01",
    )

    loan = create_loan(client, customer["id"])

    assert loan["status"] == "REJECTED"
    assert loan["rejection_reason"] == "Age must be between 21 and 60"
    assert loan["emi"] is None


def test_apply_loan_rejected_for_income_limit(client):
    customer = create_customer(
        client,
        monthly_income="10000.00",
    )

    loan = create_loan(
        client,
        customer["id"],
        amount="300000.00",
    )

    assert loan["status"] == "REJECTED"
    assert loan["rejection_reason"] == "Requested amount exceeds 20x monthly income"
    assert loan["emi"] is None


def test_apply_loan_rejected_after_two_approved_loans(client):
    customer = create_customer(client)

    first = create_loan(client, customer["id"])
    second = create_loan(client, customer["id"])
    third = create_loan(client, customer["id"])

    assert first["status"] == "APPROVED"
    assert second["status"] == "APPROVED"
    assert third["status"] == "REJECTED"
    assert third["rejection_reason"] == "Customer already has 2 active loans"
    assert third["emi"] is None


def test_apply_loan_for_missing_customer_returns_404(client):
    create_customer(client)

    response = client.post(
        "/api/loans",
        json=valid_loan_payload(99999),
    )

    assert response.status_code == 404
    assert response.json()["error"] == "NOT_FOUND"


def test_get_loan(client):
    customer = create_customer(client)
    created = create_loan(client, customer["id"])

    response = client.get(f"/api/loans/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_missing_loan_returns_404(client):
    create_customer(client)

    response = client.get("/api/loans/99999")

    assert response.status_code == 404
    assert response.json()["error"] == "NOT_FOUND"


def test_loan_validation_errors(client):
    customer = create_customer(client)

    response = client.post(
        "/api/loans",
        json={
            "customer_id": customer["id"],
            "amount": 100,
            "tenure_months": 15,
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "VALIDATION_FAILED"

    fields = {item["field"] for item in body["details"]}
    assert {"amount", "tenure_months"} <= fields


def test_list_customer_loans(client):
    customer = create_customer(client)
    first = create_loan(client, customer["id"])
    second = create_loan(
        client,
        customer["id"],
        amount="2000000.00",
    )

    response = client.get(f"/api/customers/{customer['id']}/loans")

    assert response.status_code == 200
    loans = response.json()
    assert len(loans) == 2
    assert {loan["id"] for loan in loans} == {
        first["id"],
        second["id"],
    }


def test_list_customer_loans_filtered_by_status(client):
    customer = create_customer(client)
    create_loan(client, customer["id"])
    create_loan(
        client,
        customer["id"],
        amount="2000000.00",
    )

    response = client.get(
        f"/api/customers/{customer['id']}/loans",
        params={"status": "APPROVED"},
    )

    assert response.status_code == 200
    loans = response.json()
    assert len(loans) == 1
    assert loans[0]["status"] == "APPROVED"


def test_list_loans_for_missing_customer_returns_404(client):
    create_customer(client)

    response = client.get("/api/customers/99999/loans")

    assert response.status_code == 404
    assert response.json()["error"] == "NOT_FOUND"
