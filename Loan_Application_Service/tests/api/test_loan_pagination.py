from tests.api.helpers import (
    authenticate_customer,
    authenticate_officer,
    create_customer,
    create_loan,
)


def _create_loans(client, count: int) -> dict:
    customer = create_customer(client)
    for _ in range(count):
        create_loan(client, customer["id"], amount="10000.00")
    return customer


def test_first_page_has_metadata_and_newest_first(client):
    _create_loans(client, 3)

    response = client.get("/api/loans", params={"page": 1, "size": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["size"] == 2
    assert body["total"] == 3
    assert body["pages"] == 2
    assert [loan["id"] for loan in body["items"]] == [3, 2]


def test_last_page_has_remaining_items(client):
    _create_loans(client, 3)

    body = client.get("/api/loans", params={"page": 2, "size": 2}).json()

    assert [loan["id"] for loan in body["items"]] == [1]


def test_page_past_the_end_is_empty(client):
    _create_loans(client, 1)

    body = client.get("/api/loans", params={"page": 5, "size": 10}).json()

    assert body["items"] == []
    assert body["total"] == 1


def test_filter_by_status(client):
    _create_loans(client, 3)

    body = client.get("/api/loans", params={"status": "REJECTED"}).json()

    assert body["total"] == 1
    assert body["items"][0]["status"] == "REJECTED"


def test_invalid_page_and_size_return_400(client):
    assert client.get("/api/loans", params={"page": 0}).status_code == 400
    assert client.get("/api/loans", params={"size": 101}).status_code == 400


def test_customer_without_profile_returns_403(client):
    response = client.get("/api/loans")

    assert response.status_code == 403


def test_customer_only_sees_own_loans(client):
    _create_loans(client, 2)

    authenticate_customer(client, email="other@example.com")
    create_customer(
        client, name="Other User", email="other@example.com", phone="9876543211"
    )

    body = client.get("/api/loans").json()

    assert body["total"] == 0


def test_officer_sees_all_loans(client):
    _create_loans(client, 2)

    authenticate_officer(client)
    body = client.get("/api/loans").json()

    assert body["total"] == 2


def test_requires_authentication(client):
    client.headers.pop("Authorization")

    assert client.get("/api/loans").status_code == 401
