from datetime import datetime, timedelta

from app.schemas.core import TransactionType


# ==================================================
# GET TODAY ACTIVITY
# ==================================================

def test_get_today_activity_no_activity(
    client,
    admin_headers,
):
    response = client.get(
        "/api/v1/inventory-transactions/today/activity",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"] == []

    assert body["pagination"]["total_items"] == 0
    assert body["pagination"]["page"] == 1


def test_get_today_activity_returns_only_today_transactions(
    client,
    db,
    admin_headers,
    inventory_transaction_factory,
):
    yesterday = datetime.now() - timedelta(days=1)
    today = datetime.now()
    tomorrow = datetime.now() + timedelta(days=1)

    inventory_transaction_factory(
        performed_at=yesterday
    )

    today_transaction = inventory_transaction_factory(
        performed_at=today
    )

    inventory_transaction_factory(
        performed_at=tomorrow
    )

    response = client.get(
        "/api/v1/inventory-transactions/today/activity",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == today_transaction.id


def test_get_today_activity_multiple_transactions(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    for _ in range(5):
        inventory_transaction_factory(
            performed_at=datetime.now()
        )

    response = client.get(
        "/api/v1/inventory-transactions/today/activity",
        headers=admin_headers,
    )

    body = response.json()

    assert response.status_code == 200
    assert len(body["data"]) == 5
    assert body["pagination"]["total_items"] == 5


def test_get_today_activity_includes_all_transaction_types(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    inventory_transaction_factory(
        transaction_type=TransactionType.IN.value,
        performed_at=datetime.now(),
    )

    inventory_transaction_factory(
        transaction_type=TransactionType.OUT.value,
        performed_at=datetime.now(),
    )

    inventory_transaction_factory(
        transaction_type=TransactionType.LOSS.value,
        performed_at=datetime.now(),
    )

    inventory_transaction_factory(
        transaction_type=TransactionType.ADJUSTMENT.value,
        performed_at=datetime.now(),
    )

    response = client.get(
        "/api/v1/inventory-transactions/today/activity",
        headers=admin_headers,
    )

    body = response.json()

    returned_types = {
        item["transaction_type"]
        for item in body["data"]
    }

    assert returned_types == {
        TransactionType.IN.value,
        TransactionType.OUT.value,
        TransactionType.LOSS.value,
        TransactionType.ADJUSTMENT.value,
    }


def test_get_today_activity_requires_authentication(
    client,
):
    response = client.get(
        "/api/v1/inventory-transactions/today/activity",
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_get_today_activity_invalid_token(
    client,
):
    response = client.get(
        "/api/v1/inventory-transactions/today/activity",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_get_today_activity_admin_sees_everything(
    client,
    admin_headers,
    inventory_transaction_factory,
    user_factory,
):
    employee_one = user_factory()
    employee_two = user_factory()

    inventory_transaction_factory(
        user=employee_one,
        performed_at=datetime.now(),
    )

    inventory_transaction_factory(
        user=employee_two,
        performed_at=datetime.now(),
    )

    response = client.get(
        "/api/v1/inventory-transactions/today/activity",
        headers=admin_headers,
    )

    body = response.json()

    assert response.status_code == 200
    assert len(body["data"]) == 2


def test_get_today_activity_employee_sees_only_own_transactions(
    client,
    employee_headers,
    employee_user,
    user_factory,
    inventory_transaction_factory,
):
    inventory_transaction_factory(
        user=employee_user,
        performed_at=datetime.now(),
    )

    inventory_transaction_factory(
        user=employee_user,
        performed_at=datetime.now(),
    )

    other_employee = user_factory()

    inventory_transaction_factory(
        user=other_employee,
        performed_at=datetime.now(),
    )

    response = client.get(
        "/api/v1/inventory-transactions/today/activity",
        headers=employee_headers,
    )

    body = response.json()

    assert response.status_code == 200
    assert len(body["data"]) == 2

    for transaction in body["data"]:
        assert transaction["user_id"] == employee_user.id


def test_get_today_activity_pagination(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    for _ in range(10):
        inventory_transaction_factory(
            performed_at=datetime.now()
        )

    response = client.get(
        "/api/v1/inventory-transactions/today/activity"
        "?skip=5&limit=3",
        headers=admin_headers,
    )

    body = response.json()

    assert response.status_code == 200

    assert len(body["data"]) == 3

    assert body["pagination"]["total_items"] == 10
    assert body["pagination"]["page"] == 2


def test_get_today_activity_sorting(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    oldest = datetime.now() - timedelta(hours=2)
    newest = datetime.now()

    inventory_transaction_factory(
        quantity_changed=10,
        performed_at=oldest,
    )

    inventory_transaction_factory(
        quantity_changed=20,
        performed_at=newest,
    )

    response = client.get(
        "/api/v1/inventory-transactions/today/activity"
        "?sort=performed_at&order=asc",
        headers=admin_headers,
    )

    body = response.json()

    assert response.status_code == 200

    dates = [
        item["performed_at"]
        for item in body["data"]
    ]

    assert dates == sorted(dates)