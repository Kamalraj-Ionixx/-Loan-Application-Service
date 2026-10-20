def test_register_success(unauthenticated_client):
    response = unauthenticated_client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["role"] == "CUSTOMER"
    assert body["user_id"]


def test_register_duplicate_email_returns_409(unauthenticated_client):
    unauthenticated_client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "password123"},
    )

    response = unauthenticated_client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "password456"},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["error"] == "DUPLICATE_EMAIL"
    assert body["message"] == "An account with this email already exists."
    assert body["request_id"]


def test_register_short_password_returns_400(unauthenticated_client):
    response = unauthenticated_client.post(
        "/auth/register",
        json={"email": "bad@example.com", "password": "short"},
    )

    assert response.status_code == 400


def test_login_success(unauthenticated_client):
    unauthenticated_client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "password123"},
    )

    response = unauthenticated_client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(unauthenticated_client):
    unauthenticated_client.post(
        "/auth/register",
        json={"email": "wrong@example.com", "password": "password123"},
    )

    response = unauthenticated_client.post(
        "/auth/login",
        data={"username": "wrong@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401


def test_login_nonexistent_user_returns_401(unauthenticated_client):
    response = unauthenticated_client.post(
        "/auth/login",
        data={"username": "ghost@example.com", "password": "password123"},
    )

    assert response.status_code == 401


def test_expired_token_returns_401(unauthenticated_client):
    response = unauthenticated_client.get(
        "/api/customers/1",
        headers={"Authorization": "Bearer invalid.token.here"},
    )

    assert response.status_code == 401
