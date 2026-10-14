from tests.api.helpers import create_customer, create_loan


def test_summary_for_customer_without_loans(client):
    customer = create_customer(client)

    response = client.get(f"/api/customers/{customer['id']}/summary")

    assert response.status_code == 200
    summary = response.json()

    assert summary["customer_id"] == customer["id"]
    assert summary["total_applications"] == 0
    assert summary["approved_count"] == 0
    assert summary["rejected_count"] == 0
    assert summary["total_approved_amount"] == "0.00"
    assert summary["total_monthly_emi"] == "0.00"
    assert summary["emi_to_income_ratio"] == "0.00"
    assert summary["risk_band"] == "LOW"


def test_summary_counts_approved_and_rejected_loans(client):
    customer = create_customer(client)

    approved = create_loan(client, customer["id"])
    rejected = create_loan(
        client,
        customer["id"],
        amount="2000000.00",
    )

    assert approved["status"] == "APPROVED"
    assert rejected["status"] == "REJECTED"

    response = client.get(f"/api/customers/{customer['id']}/summary")

    assert response.status_code == 200
    summary = response.json()

    assert summary["total_applications"] == 2
    assert summary["approved_count"] == 1
    assert summary["rejected_count"] == 1
    assert summary["total_approved_amount"] == "300000.00"
    assert summary["total_monthly_emi"] == "9964.29"
    assert summary["emi_to_income_ratio"] == "19.93"
    assert summary["risk_band"] == "LOW"


def test_summary_returns_404_for_missing_customer(client):
    create_customer(client)

    response = client.get("/api/customers/99999/summary")

    assert response.status_code == 404
    assert response.json()["error"] == "NOT_FOUND"
