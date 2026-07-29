from decimal import Decimal

from app.models.core import (
    InventoryBatch,
    InventoryTransaction,
)

from app.schemas.core import (
    InventoryBatchCreate,
    LossLogCreate,
    LossReason,
    TransactionType,
)

from app.services.inventory_batch_service import (
    receive_inventory_batch,
)


# ==================================================
# CREATE LOSS SUCCESS
# ==================================================

def test_register_loss_success(
    client,
    db,
    admin_headers,
    admin_user,
    product_factory,
    supplier_factory,
):
    """
    Administrator should successfully register
    an inventory loss.
    """

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin_user,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="LOSS-001",
            initial_quantity=20,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    response = client.post(
        "/api/v1/losses/",
        headers=admin_headers,
        json=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=5,
            reason=LossReason.DAMAGED,
            notes="Broken products",
        ).model_dump(mode="json"),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["message"] == "Loss registered successfully"

    assert body["data"]["batch_id"] == batch.id

    assert body["data"]["quantity_lost"] == 5

    assert body["data"]["reason"] == LossReason.DAMAGED.value


# ==================================================
# CREATE LOSS DECREASES INVENTORY
# ==================================================

def test_register_loss_updates_inventory(
    client,
    db,
    admin_headers,
    admin_user,
    product_factory,
    supplier_factory,
):
    """
    API should decrease the remaining quantity
    inside the inventory batch.
    """

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin_user,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="LOSS-002",
            initial_quantity=15,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    client.post(
        "/api/v1/losses/",
        headers=admin_headers,
        json=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=4,
            reason=LossReason.DAMAGED,
        ).model_dump(mode="json"),
    )

    db.refresh(batch)

    assert batch.current_quantity == 11


# ==================================================
# CREATE LOSS CREATES TRANSACTION
# ==================================================

def test_register_loss_creates_transaction(
    client,
    db,
    admin_headers,
    admin_user,
    product_factory,
    supplier_factory,
):
    """
    API should create one LOSS inventory
    transaction.
    """

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin_user,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="LOSS-003",
            initial_quantity=10,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    client.post(
        "/api/v1/losses/",
        headers=admin_headers,
        json=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=2,
            reason=LossReason.DAMAGED,
        ).model_dump(mode="json"),
    )

    transaction = (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.batch_id == batch.id,
            InventoryTransaction.transaction_type == TransactionType.LOSS.value,
        )
        .first()
    )

    assert transaction is not None

    assert transaction.quantity_changed == -2


# ==================================================
# CREATE LOSS UNAUTHORIZED
# ==================================================

def test_register_loss_requires_authentication(
    client,
):
    """
    Anonymous users cannot register losses.
    """

    response = client.post(
        "/api/v1/losses/",
        json={
            "batch_id": 1,
            "quantity_lost": 2,
            "reason": "Damaged",
        },
    )

    assert response.status_code == 401


# ==================================================
# CREATE LOSS INVALID TOKEN
# ==================================================

def test_register_loss_invalid_token(
    client,
):
    """
    Invalid JWT should return 401.
    """

    response = client.post(
        "/api/v1/losses/",
        headers={
            "Authorization": "Bearer invalid-token"
        },
        json={
            "batch_id": 1,
            "quantity_lost": 2,
            "reason": "Damaged",
        },
    )

    assert response.status_code == 401


# ==================================================
# CREATE LOSS BATCH NOT FOUND
# ==================================================

def test_register_loss_batch_not_found(
    client,
    admin_headers,
):
    """
    Should return 404 if the batch
    does not exist.
    """

    response = client.post(
        "/api/v1/losses/",
        headers=admin_headers,
        json={
            "batch_id": 999999,
            "quantity_lost": 5,
            "reason": "Damaged",
        },
    )

    assert response.status_code == 404

    assert response.json()["message"] == "Batch not found."


# ==================================================
# CREATE LOSS INSUFFICIENT STOCK
# ==================================================

def test_register_loss_insufficient_stock(
    client,
    db,
    admin_headers,
    admin_user,
    product_factory,
    supplier_factory,
):
    """
    Cannot remove more stock than available.
    """

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin_user,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="LOSS-004",
            initial_quantity=3,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    response = client.post(
        "/api/v1/losses/",
        headers=admin_headers,
        json={
            "batch_id": batch.id,
            "quantity_lost": 10,
            "reason": "Damaged",
        },
    )

    assert response.status_code == 400

    assert response.json()["message"] == "Insufficient stock to log this loss."


# ==================================================
# CREATE LOSS INACTIVE PRODUCT
# ==================================================

def test_register_loss_inactive_product(
    client,
    db,
    admin_headers,
    admin_user,
    product_factory,
    supplier_factory,
):
    """
    Losses cannot be registered for
    inactive products.
    """

    product = product_factory(
        is_active=False,
    )

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin_user,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="LOSS-005",
            initial_quantity=10,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    response = client.post(
        "/api/v1/losses/",
        headers=admin_headers,
        json={
            "batch_id": batch.id,
            "quantity_lost": 2,
            "reason": "Damaged",
        },
    )

    assert response.status_code == 400

    assert response.json()["message"] == (
        "Cannot register losses for an inactive product."
    )


# ==================================================
# GET ALL LOSSES SUCCESS (ADMIN)
# ==================================================

def test_get_all_losses_admin(
    client,
    admin_headers,
    loss_log_factory,
):
    """
    Administrator should retrieve every loss record.
    """

    loss_log_factory()

    loss_log_factory()

    response = client.get(
        "/api/v1/losses/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()
    # print(body)

    assert len(body["data"]) == 2

    assert body["pagination"]["total_items"] == 2

    assert body["pagination"]["page"] == 1

    assert body["pagination"]["total_pages"] == 1


# ==================================================
# GET ALL LOSSES EMPLOYEE ONLY SEES OWN RECORDS
# ==================================================

def test_get_all_losses_employee_only_own(
    client,
    employee_headers,
    employee_user,
    admin_user,
    loss_log_factory,
):
    """
    Employees should only retrieve the losses
    they personally registered.
    """

    loss_log_factory(user=employee_user)

    loss_log_factory(user=employee_user)

    loss_log_factory(user=admin_user)

    response = client.get(
        "/api/v1/losses/",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 2

    for loss in body["data"]:
        assert loss["user_id"] == employee_user.id


# ==================================================
# GET ALL LOSSES PAGINATION
# ==================================================

def test_get_all_losses_pagination(
    client,
    admin_headers,
    loss_log_factory,
):
    """
    Pagination should return only the requested
    number of records.
    """

    for _ in range(5):
        loss_log_factory()

    response = client.get(
        "/api/v1/losses/?skip=0&limit=2",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 2

    assert body["pagination"]["total_items"] == 5

    assert body["pagination"]["page_size"] == 2

    assert body["pagination"]["page"] == 1

    assert body["pagination"]["total_pages"] == 3

    assert body["pagination"]["has_next"] is True

    assert body["pagination"]["has_previous"] is False


# ==================================================
# GET ALL LOSSES SORT ASCENDING
# ==================================================

def test_get_all_losses_sort_ascending(
    client,
    admin_headers,
    loss_log_factory,
):
    """
    Should sort losses in ascending order.
    """

    loss_log_factory(quantity_lost=10)

    loss_log_factory(quantity_lost=2)

    response = client.get(
        "/api/v1/losses/?sort=quantity_lost&order=asc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    quantities = [
        item["quantity_lost"]
        for item in response.json()["data"]
    ]

    assert quantities == sorted(quantities)


# ==================================================
# GET ALL LOSSES SORT DESCENDING
# ==================================================

def test_get_all_losses_sort_descending(
    client,
    admin_headers,
    loss_log_factory,
):
    """
    Should sort losses in descending order.
    """

    loss_log_factory(quantity_lost=3)

    loss_log_factory(quantity_lost=20)

    response = client.get(
        "/api/v1/losses/?sort=quantity_lost&order=desc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    quantities = [
        item["quantity_lost"]
        for item in response.json()["data"]
    ]

    assert quantities == sorted(
        quantities,
        reverse=True,
    )


# ==================================================
# GET LOSS BY ID
# ==================================================

def test_get_loss_by_id_success(
    client,
    admin_headers,
    loss_log,
):
    """
    Administrator should be able to retrieve a loss record.
    """

    response = client.get(
        f"/api/v1/losses/{loss_log.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == loss_log.id
    assert body["data"]["batch_id"] == loss_log.batch_id
    assert body["data"]["quantity_lost"] == loss_log.quantity_lost


def test_get_loss_by_id_not_found(
    client,
    admin_headers,
):
    """
    Requesting a non-existing loss should return 404.
    """

    response = client.get(
        "/api/v1/losses/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["message"] == "Loss log not found."


def test_employee_can_view_own_loss(
    client,
    employee_headers,
    employee_user,
    inventory_batch_factory,
    loss_log_factory,
):
    """
    Employees should be able to view their own losses.
    """

    batch = inventory_batch_factory()

    loss = loss_log_factory(
        batch=batch,
        user=employee_user,
    )

    response = client.get(
        f"/api/v1/losses/{loss.id}",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["data"]["id"] == loss.id
    assert body["data"]["user_id"] == employee_user.id


def test_employee_cannot_view_other_employee_loss(
    client,
    employee_headers,
    user_factory,
    inventory_batch_factory,
    loss_log_factory,
):
    """
    Employees cannot access another employee's loss record.
    """

    other_employee = user_factory(
        username="employee_two",
        role="employee",
    )

    batch = inventory_batch_factory()

    loss = loss_log_factory(
        batch=batch,
        user=other_employee,
    )

    response = client.get(
        f"/api/v1/losses/{loss.id}",
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["message"] == "You are not authorized to view this loss log."


def test_admin_can_view_any_employee_loss(
    client,
    admin_headers,
    user_factory,
    inventory_batch_factory,
    loss_log_factory,
):
    """
    Administrators can access every loss record.
    """

    employee = user_factory(
        username="employee_three",
        role="employee",
    )

    batch = inventory_batch_factory()

    loss = loss_log_factory(
        batch=batch,
        user=employee,
    )

    response = client.get(
        f"/api/v1/losses/{loss.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["data"]["id"] == loss.id
    assert body["data"]["user_id"] == employee.id


# ==================================================
# GET LOSS BY ID SUCCESS
# ==================================================

def test_get_loss_by_id_success(
    client,
    admin_headers,
    loss_log,
):
    """
    Administrator should be able to retrieve a loss record.
    """

    response = client.get(
        f"/api/v1/losses/{loss_log.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == loss_log.id
    assert body["data"]["batch_id"] == loss_log.batch_id
    assert body["data"]["quantity_lost"] == loss_log.quantity_lost


# ==================================================
# GET LOSS BY ID NOT FOUND
# ==================================================

def test_get_loss_by_id_not_found(
    client,
    admin_headers,
):
    """
    Requesting a non-existing loss should return 404.
    """

    response = client.get(
        "/api/v1/losses/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["message"] == "Loss log not found."


# ==================================================
# EMPLOYEE CAN VIEW OWN LOSS
# ==================================================

def test_employee_can_view_own_loss(
    client,
    employee_headers,
    employee_user,
    inventory_batch_factory,
    loss_log_factory,
):
    """
    Employees should be able to view their own losses.
    """

    batch = inventory_batch_factory()

    loss = loss_log_factory(
        batch=batch,
        user=employee_user,
    )

    response = client.get(
        f"/api/v1/losses/{loss.id}",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["data"]["id"] == loss.id
    assert body["data"]["user_id"] == employee_user.id


# ==================================================
# EMPLOYEE CANNOT VIEW OTHER EMPLOYEE LOSS
# ==================================================

def test_employee_cannot_view_other_employee_loss(
    client,
    employee_headers,
    user_factory,
    inventory_batch_factory,
    loss_log_factory,
):
    """
    Employees cannot access another employee's loss record.
    """

    other_employee = user_factory(
        username="employee_two",
        role="employee",
    )

    batch = inventory_batch_factory()

    loss = loss_log_factory(
        batch=batch,
        user=other_employee,
    )

    response = client.get(
        f"/api/v1/losses/{loss.id}",
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["message"] == "You are not authorized to view this loss log."


# ==================================================
# TEST ADMIN CAN VIEW ANY EMPLOYEE LOSS
# ==================================================

def test_admin_can_view_any_employee_loss(
    client,
    admin_headers,
    user_factory,
    inventory_batch_factory,
    loss_log_factory,
):
    """
    Administrators can access every loss record.
    """

    employee = user_factory(
        username="employee_three",
        role="employee",
    )

    batch = inventory_batch_factory()

    loss = loss_log_factory(
        batch=batch,
        user=employee,
    )

    response = client.get(
        f"/api/v1/losses/{loss.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["data"]["id"] == loss.id
    assert body["data"]["user_id"] == employee.id


# ==================================================
# AUTHORIZATION & VALIDATION EDGE CASES
# ==================================================

# ==================================================
# GET LOSS REQUIRES AUTHENTICATION
# ==================================================

def test_get_loss_requires_authentication(
    client,
    loss_log,
):
    """
    Anonymous users cannot retrieve a loss.
    """

    response = client.get(
        f"/api/v1/losses/{loss_log.id}",
    )

    assert response.status_code == 401

    body = response.json()

    assert body["message"] == "Not authenticated"


# ==================================================
# GET LOSS INVALID TOKEN
# ==================================================

def test_get_loss_invalid_token(
    client,
    loss_log,
):
    """
    Invalid JWT should be rejected.
    """

    response = client.get(
        f"/api/v1/losses/{loss_log.id}",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["message"] == "Could not validate credentials."


# ==================================================
# GET LOSS INVALID ID VALIDATION
# ==================================================

def test_get_loss_invalid_id_validation(
    client,
    admin_headers,
):
    """
    Path parameter validation should reject invalid IDs.
    """

    response = client.get(
        "/api/v1/losses/0",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["message"] == "Validation error."

    assert len(body["errors"]) >= 1

    assert body["errors"][0]["field"] == "path -> loss_id"