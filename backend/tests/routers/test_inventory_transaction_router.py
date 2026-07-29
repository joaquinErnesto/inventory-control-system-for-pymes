from app.models.core import InventoryTransaction
from app.schemas.core import TransactionType

from datetime import datetime, timedelta


# ==================================================
# GET INVENTORY TRANSACTIONS (SUCCESS)
# ==================================================

def test_get_inventory_transactions_success(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    """
    Administrator should receive every transaction.
    """

    inventory_transaction_factory()
    inventory_transaction_factory()

    response = client.get(
        "/api/v1/inventory-transactions/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 2
    assert body["pagination"]["total_items"] == 2


# ==================================================
# EMPLOYEE ONLY SEES OWN TRANSACTIONS
# ==================================================

def test_get_inventory_transactions_employee_only_own(
    client,
    employee_headers,
    employee_user,
    inventory_transaction_factory,
    user_factory,
):
    """
    Employees must only see their own transactions.
    """

    inventory_transaction_factory(
        user=employee_user,
    )

    other_user = user_factory()

    inventory_transaction_factory(
        user=other_user,
    )

    response = client.get(
        "/api/v1/inventory-transactions/",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 1
    assert body["data"][0]["user_id"] == employee_user.id


# ==================================================
# AUTHENTICATION REQUIRED
# ==================================================

def test_get_inventory_transactions_requires_authentication(
    client,
):
    """
    Anonymous users cannot access transactions.
    """

    response = client.get(
        "/api/v1/inventory-transactions/",
    )

    assert response.status_code == 401


# ==================================================
# INVALID TOKEN
# ==================================================

def test_get_inventory_transactions_invalid_token(
    client,
):
    """
    Invalid JWT should return 401.
    """

    response = client.get(
        "/api/v1/inventory-transactions/",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401


# ==================================================
# PAGINATION
# ==================================================

def test_get_inventory_transactions_pagination(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    """
    Pagination should respect skip and limit.
    """

    for _ in range(5):
        inventory_transaction_factory()

    response = client.get(
        "/api/v1/inventory-transactions/?skip=0&limit=2",
        headers=admin_headers,
    )

    body = response.json()

    assert response.status_code == 200

    assert len(body["data"]) == 2

    assert body["pagination"]["total_items"] == 5
    assert body["pagination"]["page_size"] == 2


# ==================================================
# SORT ASCENDING
# ==================================================

def test_get_inventory_transactions_sort_ascending(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    """
    Ascending sorting should return oldest transaction first.
    """

    inventory_transaction_factory(
        quantity_changed=10,
    )

    inventory_transaction_factory(
        quantity_changed=20,
    )

    response = client.get(
        "/api/v1/inventory-transactions/?sort=quantity_changed&order=asc",
        headers=admin_headers,
    )

    body = response.json()

    quantities = [
        item["quantity_changed"]
        for item in body["data"]
    ]

    assert quantities == sorted(quantities)


# ==================================================
# SORT DESCENDING
# ==================================================

def test_get_inventory_transactions_sort_descending(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    """
    Descending sorting should return largest quantity first.
    """

    inventory_transaction_factory(
        quantity_changed=10,
    )

    inventory_transaction_factory(
        quantity_changed=20,
    )

    response = client.get(
        "/api/v1/inventory-transactions/?sort=quantity_changed&order=desc",
        headers=admin_headers,
    )

    body = response.json()

    quantities = [
        item["quantity_changed"]
        for item in body["data"]
    ]

    assert quantities == sorted(
        quantities,
        reverse=True,
    )


# ==================================================
# EMPTY DATABASE
# ==================================================

def test_get_inventory_transactions_empty_database(
    client,
    admin_headers,
):
    """
    Empty database should return an empty list.
    """

    response = client.get(
        "/api/v1/inventory-transactions/",
        headers=admin_headers,
    )

    body = response.json()

    assert response.status_code == 200

    assert body["data"] == []

    assert body["pagination"]["total_items"] == 0


# ==================================================
# FILTER BY PRODUCT
# ==================================================

def test_filter_transactions_by_product(
    client,
    admin_headers,
    inventory_transaction_factory,
    product_factory,
    inventory_batch_factory,
):
    """
    Should return only transactions belonging
    to the requested product.
    """

    product1 = product_factory(name="Product A")
    product2 = product_factory(name="Product B")

    batch1 = inventory_batch_factory(product=product1)
    batch2 = inventory_batch_factory(product=product2)

    inventory_transaction_factory(
        product=product1,
        batch=batch1,
    )

    inventory_transaction_factory(
        product=product2,
        batch=batch2,
    )

    response = client.get(
        f"/api/v1/inventory-transactions/?product_id={product1.id}",
        headers=admin_headers,
    )

    body = response.json()

    assert response.status_code == 200

    assert len(body["data"]) == 1
    assert body["data"][0]["product_id"] == product1.id


# ==================================================
# FILTER BY BATCH
# ==================================================

def test_filter_transactions_by_batch(
    client,
    admin_headers,
    inventory_transaction_factory,
    inventory_batch_factory,
):
    """
    Should return only transactions from one batch.
    """

    batch1 = inventory_batch_factory()
    batch2 = inventory_batch_factory()

    inventory_transaction_factory(batch=batch1)
    inventory_transaction_factory(batch=batch2)

    response = client.get(
        f"/api/v1/inventory-transactions/?batch_id={batch1.id}",
        headers=admin_headers,
    )

    body = response.json()

    assert len(body["data"]) == 1
    assert body["data"][0]["batch_id"] == batch1.id


# ==================================================
# FILTER BY TRANSACTION TYPE
# ==================================================

def test_filter_transactions_by_type(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    """
    Should filter by transaction type.
    """

    inventory_transaction_factory(
        transaction_type=TransactionType.IN.value,
    )

    inventory_transaction_factory(
        transaction_type=TransactionType.OUT.value,
    )

    response = client.get(
        "/api/v1/inventory-transactions/?transaction_type=OUT",
        headers=admin_headers,
    )

    body = response.json()

    assert len(body["data"]) == 1

    assert body["data"][0]["transaction_type"] == "OUT"


# ==================================================
# FILTER BY USER (ADMIN)
# ==================================================

def test_filter_transactions_by_user_admin(
    client,
    admin_headers,
    inventory_transaction_factory,
    user_factory,
):
    """
    Administrators may filter by user_id.
    """

    user1 = user_factory()
    user2 = user_factory()

    inventory_transaction_factory(user=user1)
    inventory_transaction_factory(user=user2)

    response = client.get(
        f"/api/v1/inventory-transactions/?user_id={user1.id}",
        headers=admin_headers,
    )

    body = response.json()

    assert len(body["data"]) == 1
    assert body["data"][0]["user_id"] == user1.id


# ==================================================
# EMPLOYEE CANNOT BYPASS USER FILTER
# ==================================================

def test_employee_user_filter_is_ignored(
    client,
    employee_headers,
    employee_user,
    inventory_transaction_factory,
    user_factory,
):
    """
    Employee must still only see
    their own transactions.
    """

    inventory_transaction_factory(
        user=employee_user,
    )

    other_user = user_factory()

    inventory_transaction_factory(
        user=other_user,
    )

    response = client.get(
        f"/api/v1/inventory-transactions/?user_id={other_user.id}",
        headers=employee_headers,
    )

    body = response.json()

    assert len(body["data"]) == 1

    assert body["data"][0]["user_id"] == employee_user.id


# ==================================================
# FILTER BY SALE
# ==================================================

def test_filter_transactions_by_sale(
    client,
    admin_headers,
    inventory_transaction_factory,
    sale_factory,
):
    """
    Should return only transactions
    belonging to one sale.
    """

    sale1 = sale_factory()
    sale2 = sale_factory()

    inventory_transaction_factory(
        sale=sale1,
    )

    inventory_transaction_factory(
        sale=sale2,
    )

    response = client.get(
        f"/api/v1/inventory-transactions/?sale_id={sale1.id}",
        headers=admin_headers,
    )

    body = response.json()

    assert len(body["data"]) == 1

    assert body["data"][0]["sale_id"] == sale1.id


# ==================================================
# FILTER BY LOSS
# ==================================================

def test_filter_transactions_by_loss(
    client,
    admin_headers,
    inventory_transaction_factory,
    loss_log_factory,
):
    """
    Should return only transactions
    linked to one loss log.
    """

    loss1 = loss_log_factory()
    loss2 = loss_log_factory()

    inventory_transaction_factory(
        loss=loss1,
    )

    inventory_transaction_factory(
        loss=loss2,
    )

    response = client.get(
        f"/api/v1/inventory-transactions/?loss_id={loss1.id}",
        headers=admin_headers,
    )

    body = response.json()

    assert len(body["data"]) == 1

    assert body["data"][0]["loss_id"] == loss1.id


# ==================================================
# MULTIPLE FILTERS
# ==================================================

def test_filter_transactions_multiple_filters(
    client,
    admin_headers,
    inventory_transaction_factory,
    product_factory,
    inventory_batch_factory,
):
    """
    Multiple filters should work together.
    """

    product = product_factory()

    batch = inventory_batch_factory(
        product=product,
    )

    inventory_transaction_factory(
        product=product,
        batch=batch,
        transaction_type=TransactionType.OUT.value,
    )

    inventory_transaction_factory(
        product=product,
        batch=batch,
        transaction_type=TransactionType.IN.value,
    )

    response = client.get(
        (
            f"/api/v1/inventory-transactions/"
            f"?product_id={product.id}"
            f"&batch_id={batch.id}"
            f"&transaction_type=OUT"
        ),
        headers=admin_headers,
    )

    body = response.json()

    assert len(body["data"]) == 1

    item = body["data"][0]

    assert item["product_id"] == product.id
    assert item["batch_id"] == batch.id
    assert item["transaction_type"] == "OUT"


# ==================================================
# FILTER BY START DATE
# ==================================================

def test_filter_transactions_by_start_date(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    """
    Transactions before the given start_date
    should not be returned.
    """

    old_transaction = inventory_transaction_factory()

    recent_transaction = inventory_transaction_factory()

    old_transaction.performed_at = datetime.utcnow() - timedelta(days=10)
    recent_transaction.performed_at = datetime.utcnow()

    client.app.dependency_overrides.clear()  # no-op, keeps linter happy if unused


    # Persist timestamps
    from app.database import SessionLocal
    db = SessionLocal()
    db.merge(old_transaction)
    db.merge(recent_transaction)
    db.commit()
    db.close()

    start = (datetime.utcnow() - timedelta(days=1)).isoformat()

    response = client.get(
        f"/api/v1/inventory-transactions/?start_date={start}",
        headers=admin_headers,
    )

    body = response.json()

    assert response.status_code == 200

    assert len(body["data"]) == 1


# ==================================================
# FILTER BY END DATE
# ==================================================

def test_filter_transactions_by_end_date(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    """
    Transactions after end_date
    should not be returned.
    """

    now = datetime.utcnow()

    inventory_transaction_factory(
        performed_at=now - timedelta(days=10),
    )

    inventory_transaction_factory(
        performed_at=now,
    )

    end = (now - timedelta(days=5)).isoformat()

    response = client.get(
        f"/api/v1/inventory-transactions/?end_date={end}",
        headers=admin_headers,
    )

    body = response.json()

    assert response.status_code == 200

    assert len(body["data"]) == 1


# ==================================================
# FILTER BY DATE RANGE
# ==================================================

def test_filter_transactions_by_date_range(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    """
    Only transactions inside the range
    should be returned.
    """

    now = datetime.utcnow()

    inventory_transaction_factory(
        performed_at=now - timedelta(days=10),
    )

    inventory_transaction_factory(
        performed_at=now - timedelta(days=5),
    )

    inventory_transaction_factory(
        performed_at=now,
    )

    start = (now - timedelta(days=6)).isoformat()
    end = (now - timedelta(days=2)).isoformat()

    response = client.get(
        (
            "/api/v1/inventory-transactions/"
            f"?start_date={start}"
            f"&end_date={end}"
        ),
        headers=admin_headers,
    )

    body = response.json()

    assert response.status_code == 200

    assert len(body["data"]) == 1

    assert body["data"][0]["quantity_changed"] == 100


# ==================================================
# INVALID DATE RANGE
# ==================================================

def test_filter_transactions_invalid_date_range(
    client,
    admin_headers,
):
    """
    start_date greater than end_date
    must return HTTP 400.
    """

    start = datetime.utcnow().isoformat()
    end = (datetime.utcnow() - timedelta(days=10)).isoformat()

    response = client.get(
        (
            "/api/v1/inventory-transactions/"
            f"?start_date={start}"
            f"&end_date={end}"
        ),
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["message"] == "start_date must be earlier than or equal to end_date."


# ==================================================
# DATE RANGE WITHOUT MATCHES
# ==================================================

def test_filter_transactions_date_range_no_matches(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    """
    Valid date range with no matching
    transactions should return an empty list.
    """

    now = datetime.utcnow()

    inventory_transaction_factory(
        performed_at=now - timedelta(days=100),
    )

    start = (now - timedelta(days=10)).isoformat()
    end = now.isoformat()

    response = client.get(
        (
            "/api/v1/inventory-transactions/"
            f"?start_date={start}"
            f"&end_date={end}"
        ),
        headers=admin_headers,
    )

    body = response.json()

    assert response.status_code == 200

    assert body["data"] == []


# ==================================================
# ADMIN CAN RETRIEVE ANY TRANSACTION
# ==================================================

def test_get_inventory_transaction_success(
    client,
    admin_headers,
    inventory_transaction,
):
    response = client.get(
        f"/api/v1/inventory-transactions/{inventory_transaction.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == inventory_transaction.id
    assert body["data"]["product_id"] == inventory_transaction.product_id
    assert body["data"]["batch_id"] == inventory_transaction.batch_id
    assert body["data"]["user_id"] == inventory_transaction.user_id
    

# ==================================================
# EMPLOYEE CAN RETRIEVE OWN TRANSACTION
# ==================================================

def test_employee_can_view_own_transaction(
    client,
    employee_headers,
    inventory_transaction_factory,
    employee_user,
):
    transaction = inventory_transaction_factory(
        user=employee_user,
    )

    response = client.get(
        f"/api/v1/inventory-transactions/{transaction.id}",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["data"]["id"] == transaction.id


# ==================================================
# EMPLOYEE CANNOT RETRIEVE ANOTHER EMPLOYEE'S TRANSACTION
# ==================================================

def test_employee_cannot_view_other_transaction(
    client,
    employee_headers,
    inventory_transaction,
):
    response = client.get(
        f"/api/v1/inventory-transactions/{inventory_transaction.id}",
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["message"] == "You are not authorized to view this transaction."
    
    
# ==================================================
# TRANSACTION NOT FOUND
# ==================================================

def test_get_inventory_transaction_not_found(
    client,
    admin_headers,
):
    response = client.get(
        "/api/v1/inventory-transactions/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["message"] == "Inventory transaction not found."
    
    
# ==================================================
# AUTHENTICATION REQUIRED
# ==================================================

def test_get_inventory_transaction_requires_authentication(
    client,
    inventory_transaction,
):
    response = client.get(
        f"/api/v1/inventory-transactions/{inventory_transaction.id}",
    )

    assert response.status_code == 401


# ==================================================
# INVALID TOKEN
# ==================================================

def test_get_inventory_transaction_invalid_token(
    client,
    inventory_transaction,
):
    response = client.get(
        f"/api/v1/inventory-transactions/{inventory_transaction.id}",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["message"] == "Could not validate credentials."


# ==================================================
# INVALID TRANSACTION ID (VALIDATION)
# ==================================================

def test_get_inventory_transaction_invalid_id_validation(
    client,
    admin_headers,
):
    response = client.get(
        "/api/v1/inventory-transactions/0",
        headers=admin_headers,
    )

    assert response.status_code == 422


# ==================================================
# ADMIN SUMMARY
# ==================================================

def test_transaction_summary_admin(
    client,
    admin_headers,
    inventory_transaction_factory,
):
    inventory_transaction_factory(
        transaction_type="IN",
    )

    inventory_transaction_factory(
        transaction_type="OUT",
        quantity_changed=-5,
    )

    inventory_transaction_factory(
        transaction_type="LOSS",
        quantity_changed=-2,
    )

    inventory_transaction_factory(
        transaction_type="ADJUSTMENT",
        quantity_changed=3,
    )

    response = client.get(
        "/api/v1/inventory-transactions/summary/overview",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    summary = body["data"]

    assert summary["total_transactions"] == 4
    assert summary["incoming_transactions"] == 1
    assert summary["outgoing_transactions"] == 1
    assert summary["loss_transactions"] == 1
    assert summary["adjustment_transactions"] == 1
    
    
# ==================================================
# EMPLOYEE ONLY COUNTS OWN TRANSACTIONS
# ==================================================

def test_transaction_summary_employee_only_own(
    client,
    employee_headers,
    employee_user,
    inventory_transaction_factory,
):
    inventory_transaction_factory(
        user=employee_user,
        transaction_type="IN",
    )

    inventory_transaction_factory(
        user=employee_user,
        transaction_type="OUT",
        quantity_changed=-3,
    )

    inventory_transaction_factory()

    inventory_transaction_factory()

    response = client.get(
        "/api/v1/inventory-transactions/summary/overview",
        headers=employee_headers,
    )

    assert response.status_code == 200

    summary = response.json()["data"]

    assert summary["total_transactions"] == 2
    assert summary["incoming_transactions"] == 1
    assert summary["outgoing_transactions"] == 1
    
    
# ==================================================
# EMPTY DATABASE
# ==================================================

def test_transaction_summary_empty_database(
    client,
    admin_headers,
):
    response = client.get(
        "/api/v1/inventory-transactions/summary/overview",
        headers=admin_headers,
    )

    assert response.status_code == 200

    summary = response.json()["data"]

    assert summary["total_transactions"] == 0
    assert summary["incoming_transactions"] == 0
    assert summary["outgoing_transactions"] == 0
    assert summary["loss_transactions"] == 0
    assert summary["adjustment_transactions"] == 0
    
    
# ==================================================
# AUTHENTICATION REQUIRED
# ==================================================

def test_transaction_summary_requires_authentication(
    client,
):
    response = client.get(
        "/api/v1/inventory-transactions/summary/overview",
    )

    assert response.status_code == 401
    
    
# ==================================================
# INVALID TOKEN
# ==================================================

def test_transaction_summary_invalid_token(
    client,
):
    response = client.get(
        "/api/v1/inventory-transactions/summary/overview",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["message"] == "Could not validate credentials."