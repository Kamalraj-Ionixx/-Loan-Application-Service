from tests.api.helpers import valid_customer_payload


def test_create_customer(client):
    response = client.post(
        "/api/customers",
        json=valid_customer_payload(),
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["id"] > 0
    assert data["name"] == "Arun Kumar"
    assert data["email"] == "arun@example.com"
    assert data["phone"] == "9876543210"


def test_get_customer(client):
    created_response = client.post(
        "/api/customers",
        json=valid_customer_payload(),
    )
    assert created_response.status_code == 201

    customer_id = created_response.json()["id"]
    response = client.get(f"/api/customers/{customer_id}")

    assert response.status_code == 200
    assert response.json()["id"] == customer_id


def test_get_missing_customer_returns_404(client):
    response = client.get("/api/customers/99999")

    assert response.status_code == 404
    assert response.json()["error"] == "NOT_FOUND"
    assert response.json()["request_id"]


def test_customer_cannot_create_a_second_profile(client):
    payload = valid_customer_payload()

    first = client.post("/api/customers", json=payload)
    second = client.post("/api/customers", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    body = second.json()
    assert body == {
        "error": "CONFLICT",
        "message": "The request conflicts with the current resource state.",
        "request_id": body["request_id"],
    }


def test_invalid_customer_returns_validation_errors(client):
    payload = valid_customer_payload(
        name="R1",
        email="not-an-email",
        phone="123",
        date_of_birth="2999-01-01",
        monthly_income="-100",
    )

    response = client.post("/api/customers", json=payload)

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "VALIDATION_FAILED"
    assert body["message"] == "The request could not be processed."

    fields = {item["field"] for item in body["details"]}
    assert {
        "name",
        "email",
        "phone",
        "date_of_birth",
        "monthly_income",
    } <= fields
    assert all(item["message"] == "Invalid value." for item in body["details"])
