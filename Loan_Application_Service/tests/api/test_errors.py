from tests.api.helpers import valid_customer_payload


def test_malformed_json_returns_400(client):
    response = client.post(
        "/api/customers",
        content='{"name": ',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "INVALID_REQUEST"
    assert response.json()["message"] == "The request could not be processed."
    assert response.json()["request_id"]


def test_empty_json_body_returns_400(client):
    response = client.post(
        "/api/customers",
        content="",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "The request could not be processed."
    assert response.json()["request_id"]


def test_validation_error_has_matching_request_id(client):
    response = client.post(
        "/api/customers",
        json=valid_customer_payload(phone="123"),
    )

    assert response.status_code == 400
    body = response.json()

    assert body["error"] == "VALIDATION_FAILED"
    assert body["message"] == "The request could not be processed."
    assert body["request_id"]
    assert response.headers.get("X-Request-ID") == body["request_id"]
    assert all(item["message"] == "Invalid value." for item in body["details"])


def test_not_found_has_matching_request_id(client):
    response = client.get("/api/customers/99999")

    assert response.status_code == 404
    body = response.json()

    assert body["error"] == "NOT_FOUND"
    assert body["message"] == "The requested resource was not found."
    assert body["request_id"]
    assert response.headers.get("X-Request-ID") == body["request_id"]


def test_unauthorized_error_uses_standard_message_and_keeps_auth_header(client):
    client.headers.pop("Authorization")

    response = client.get("/api/customers/1")

    assert response.status_code == 401
    assert response.json()["error"] == "UNAUTHORIZED"
    assert response.json()["message"] == "Authentication is required or invalid."
    assert response.json()["request_id"]
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert "detail" not in response.json()
