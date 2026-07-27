from decimal import Decimal

from app.models.core import (
    InventoryBatch,
    InventoryTransaction,
)
from app.schemas.core import (
    TransactionType,
    SortOrder
)


# ==================================================
# CREATE INVENTORY BATCH SUCCESS
# ==================================================

def test_create_inventory_batch_success(
    client,
    admin_token,
    product,
    supplier,
):
    """
    An administrator should be able to receive
    a new inventory batch.
    """

    payload = {
        "product_id": product.id,
        "supplier_id": supplier.id,
        "batch_number": "POST-001",
        "initial_quantity": 100,
        "cost_price": "5.00",
        "selling_price": "8.00",
        "expiration_date": None,
        "notes": "Initial stock",
    }

    response = client.post(
        "/api/v1/batches/",
        json=payload,
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True

    assert (
        body["message"]
        == "Inventory batch created successfully"
    )

    data = body["data"]

    assert data["product_id"] == product.id
    assert data["supplier_id"] == supplier.id
    assert data["batch_number"] == "POST-001"
    assert data["initial_quantity"] == 100
    assert data["current_quantity"] == 100
    assert data["cost_price"] == "5.00"
    assert data["selling_price"] == "8.00"


# ==================================================
# CREATE INVENTORY BATCH CREATES TRANSACTION
# ==================================================

def test_create_inventory_batch_creates_transaction(
    client,
    admin_token,
    db,
    product,
    supplier,
):
    """
    Creating a batch should automatically
    register one IN transaction.
    """

    payload = {
        "product_id": product.id,
        "supplier_id": supplier.id,
        "batch_number": "POST-002",
        "initial_quantity": 50,
        "cost_price": "3.00",
        "selling_price": "5.00",
    }

    response = client.post(
        "/api/v1/batches/",
        json=payload,
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 201

    batch = (
        db.query(InventoryBatch)
        .filter(
            InventoryBatch.batch_number == "POST-002"
        )
        .first()
    )

    assert batch is not None

    transaction = (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.batch_id == batch.id
        )
        .first()
    )

    assert transaction is not None

    assert (
        transaction.transaction_type
        == TransactionType.IN.value
    )

    assert transaction.quantity_changed == 50


# ==================================================
# CREATE INVENTORY BATCH UNAUTHORIZED
# ==================================================

def test_create_inventory_batch_unauthorized(
    client,
    product,
    supplier,
):
    """
    Authentication is required.
    """

    payload = {
        "product_id": product.id,
        "supplier_id": supplier.id,
        "batch_number": "POST-003",
        "initial_quantity": 50,
        "cost_price": "3.00",
        "selling_price": "5.00",
    }

    response = client.post(
        "/api/v1/batches/",
        json=payload,
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


# ==================================================
# CREATE INVENTORY BATCH FORBIDDEN
# ==================================================

def test_create_inventory_batch_employee_forbidden(
    client,
    employee_token,
    product,
    supplier,
):
    """
    Employees cannot receive inventory.
    """

    payload = {
        "product_id": product.id,
        "supplier_id": supplier.id,
        "batch_number": "POST-004",
        "initial_quantity": 20,
        "cost_price": "2.00",
        "selling_price": "4.00",
    }

    response = client.post(
        "/api/v1/batches/",
        json=payload,
        headers={
            "Authorization": f"Bearer {employee_token}"
        },
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False

    assert (
        body["message"]
        == "Administrator privileges required."
    )


# ==================================================
# CREATE INVENTORY BATCH INVALID PRODUCT
# ==================================================

def test_create_inventory_batch_invalid_product(
    client,
    admin_token,
    supplier,
):
    """
    Product must exist.
    """

    payload = {
        "product_id": 999999,
        "supplier_id": supplier.id,
        "batch_number": "POST-005",
        "initial_quantity": 20,
        "cost_price": "2.00",
        "selling_price": "4.00",
    }

    response = client.post(
        "/api/v1/batches/",
        json=payload,
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert (
        body["message"]
        == "Product with ID 999999 does not exist."
    )


# ==================================================
# CREATE INVENTORY BATCH INVALID SUPPLIER
# ==================================================

def test_create_inventory_batch_invalid_supplier(
    client,
    admin_token,
    product,
):
    """
    Supplier must exist.
    """

    payload = {
        "product_id": product.id,
        "supplier_id": 999999,
        "batch_number": "POST-006",
        "initial_quantity": 20,
        "cost_price": "2.00",
        "selling_price": "4.00",
    }

    response = client.post(
        "/api/v1/batches/",
        json=payload,
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert (
        body["message"]
        == "Supplier with ID 999999 does not exist."
    )


# ==================================================
# CREATE INVENTORY BATCH VALIDATION ERROR
# ==================================================

def test_create_inventory_batch_validation_error(
    client,
    admin_token,
    product,
):
    """
    Pydantic validation should reject
    invalid request bodies.
    """

    payload = {
        "product_id": product.id,
        "supplier_id": None,
        "batch_number": "POST-007",
        "initial_quantity": -5,
        "cost_price": "-1.00",
        "selling_price": "5.00",
    }

    response = client.post(
        "/api/v1/batches/",
        json=payload,
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False

    assert body["message"] == "Validation error."

    assert len(body["errors"]) > 0
    

# ==================================================
# GET INVENTORY BATCHES SUCCESS
# ==================================================

def test_get_inventory_batches_success(
    client,
    admin_headers,
    inventory_batch_factory,
):
    """
    Should return all inventory batches.
    """

    inventory_batch_factory()
    inventory_batch_factory()
    inventory_batch_factory()

    response = client.get(
        "/api/v1/batches/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert len(body["data"]) == 3

    assert body["pagination"]["total_items"] == 3
    

# ==================================================
# GET INVENTORY BATCHES PAGINATION
# ==================================================

def test_get_inventory_batches_pagination(
    client,
    admin_headers,
    inventory_batch_factory,
):
    """
    Should paginate inventory batches.
    """

    for _ in range(5):
        inventory_batch_factory()

    response = client.get(
        "/api/v1/batches/?skip=2&limit=2",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 2

    assert body["pagination"]["page"] == 2

    assert body["pagination"]["page_size"] == 2

    assert body["pagination"]["total_items"] == 5

    assert body["pagination"]["total_pages"] == 3
    

# ==================================================
# GET INVENTORY BATCHES SORT ASC
# ==================================================

def test_get_inventory_batches_sort_cost_price_ascending(
    client,
    admin_headers,
    inventory_batch_factory,
):
    """
    Should return batches sorted by cost price ascending.
    """

    inventory_batch_factory(
        cost_price=Decimal("30.00"),
    )

    inventory_batch_factory(
        cost_price=Decimal("10.00"),
    )

    inventory_batch_factory(
        cost_price=Decimal("20.00"),
    )

    response = client.get(
        "/api/v1/batches/?sort=cost_price&order=asc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    prices = [
        Decimal(item["cost_price"])
        for item in response.json()["data"]
    ]

    assert prices == [
        Decimal("10.00"),
        Decimal("20.00"),
        Decimal("30.00"),
    ]


# ==================================================
# GET INVENTORY BATCHES INVALID SORT
# ==================================================

def test_get_inventory_batches_invalid_sort(
    client,
    admin_headers,
):
    """
    Should reject invalid sort fields.
    """

    response = client.get(
        "/api/v1/batches/?sort=invalid_field",
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert "Invalid sort field." in body["message"]


# ==================================================
# GET INVENTORY BATCHES UNAUTHORIZED
# ==================================================

def test_get_inventory_batches_unauthorized(
    client,
):
    """
    Authentication is required.
    """

    response = client.get(
        "/api/v1/batches/",
    )

    assert response.status_code == 401


# ==================================================
# GET INVENTORY BATCH BY ID SUCCESS
# ==================================================

def test_get_inventory_batch_by_id_success(
    client,
    admin_headers,
    inventory_batch_factory,
):
    """
    Should return one inventory batch.
    """

    batch = inventory_batch_factory()

    response = client.get(
        f"/api/v1/batches/{batch.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    data = body["data"]

    assert data["id"] == batch.id
    assert data["product_id"] == batch.product_id
    assert data["supplier_id"] == batch.supplier_id
    assert data["batch_number"] == batch.batch_number
    assert data["initial_quantity"] == batch.initial_quantity
    assert data["current_quantity"] == batch.current_quantity


# ==================================================
# GET INVENTORY BATCH BY ID NOT FOUND
# ==================================================

def test_get_inventory_batch_by_id_not_found(
    client,
    admin_headers,
):
    """
    Should return 404 when the batch does not exist.
    """

    response = client.get(
        "/api/v1/batches/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False

    assert (
        body["message"]
        == "Inventory batch not found."
    )


# ==================================================
# GET INVENTORY BATCH BY ID UNAUTHORIZED
# ==================================================

def test_get_inventory_batch_by_id_unauthorized(
    client,
    inventory_batch_factory,
):
    """
    Authentication is required.
    """

    batch = inventory_batch_factory()

    response = client.get(
        f"/api/v1/batches/{batch.id}"
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False
    
    
# ==================================================
# DELETE INVENTORY BATCH SUCCESS
# ==================================================

def test_delete_inventory_batch_success(
    client,
    admin_headers,
    product_factory,
    supplier_factory,
):
    product = product_factory()
    supplier = supplier_factory()

    response = client.post(
        "/api/v1/batches/",
        headers=admin_headers,
        json={
            "product_id": product.id,
            "supplier_id": supplier.id,
            "batch_number": "DELETE-001",
            "initial_quantity": 100,
            "cost_price": "5.00",
            "selling_price": "8.00",
            "expiration_date": None,
            "notes": None,
        },
    )

    batch_id = response.json()["data"]["id"]

    response = client.delete(
        f"/api/v1/batches/{batch_id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert (
        body["message"]
        == "Inventory batch deleted successfully"
    )


# ==================================================
# DELETE INVENTORY BATCH UNAUTHORIZED
# ==================================================

def test_delete_inventory_batch_unauthorized(
    client,
):
    response = client.delete(
        "/api/v1/batches/1"
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


# ==================================================
# DELETE INVENTORY BATCH EMPLOYEE FORBIDDEN
# ==================================================

def test_delete_inventory_batch_employee_forbidden(
    client,
    employee_headers,
):
    response = client.delete(
        "/api/v1/batches/1",
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False

    assert (
        body["message"]
        == "Administrator privileges required."
    )
    

# ==================================================
# DELETE INVENTORY BATCH NOT FOUND
# ==================================================

def test_delete_inventory_batch_not_found(
    client,
    admin_headers,
):
    response = client.delete(
        "/api/v1/batches/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False

    assert (
        body["message"]
        == "Inventory batch not found."
    )


# ==================================================
# DELETE INVENTORY BATCH VALIDATION ERROR
# ==================================================

def test_delete_inventory_batch_validation_error(
    client,
    admin_headers,
):
    response = client.delete(
        "/api/v1/batches/0",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False

    assert body["message"] == "Validation error."