from tests.api.helpers import (
    authenticate_customer,
    create_customer,
    create_loan,
)


def _setup_two_users(client):
    """Create first user's customer profile and loan, then switch to second user."""
    customer = create_customer(client)
    loan = create_loan(client, customer["id"])

    authenticate_customer(client, email="other@example.com")

    other_customer = create_customer(
        client,
        name="Other User",
        email="other@example.com",
        phone="9876543211",
    )

    return customer, loan, other_customer


def test_customer_cannot_view_another_customers_profile(client):
    customer, _, _ = _setup_two_users(client)

    response = client.get(f"/api/customers/{customer['id']}")

    assert response.status_code == 403


def test_customer_cannot_view_another_customers_loans(client):
    customer, _, _ = _setup_two_users(client)

    response = client.get(f"/api/customers/{customer['id']}/loans")

    assert response.status_code == 403


def test_customer_cannot_view_another_customers_loan_by_id(client):
    customer, loan, _ = _setup_two_users(client)

    response = client.get(f"/api/loans/{loan['id']}")

    assert response.status_code == 403


def test_customer_cannot_view_another_customers_summary(client):
    customer, _, _ = _setup_two_users(client)

    response = client.get(f"/api/customers/{customer['id']}/summary")

    assert response.status_code == 403


def test_customer_cannot_apply_loan_for_another_customer(client):
    customer, _, _ = _setup_two_users(client)

    response = client.post(
        "/api/loans",
        json={
            "customer_id": customer["id"],
            "amount": "300000.00",
            "tenure_months": 36,
        },
    )

    assert response.status_code == 403
