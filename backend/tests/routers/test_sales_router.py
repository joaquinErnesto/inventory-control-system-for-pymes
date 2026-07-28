from decimal import Decimal

from app.models.core import (
    InventoryBatch,
    InventoryTransaction,
)
from app.schemas.core import (
    InventoryBatchCreate,
)

from app.services.inventory_batch_service import (
    receive_inventory_batch,
)


# ==================================================
# PROCESS SALE SUCCESS
# ==================================================

def test_process_sale_success(
    client,
    admin_token,
    user_factory,
    product_factory,
    supplier_factory,
    db,
):

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SALE-001",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
        ),
    )

    response = client.post(
        "/api/v1/sales/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "customer_id": None,
            "payment_method": "Cash",
            "payment_status": "Paid",
            "items": [
                {
                    "product_id": product.id,
                    "quantity_sold": 5,
                    "unit_price": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Sale processed successfully"

    assert body["data"]["total_amount"] == "50.00"


# ==================================================
# PROCESS SALE UPDATES INVENTORY
# ==================================================

def test_process_sale_updates_inventory(
    client,
    admin_token,
    user_factory,
    product_factory,
    supplier_factory,
    db,
):

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SALE-002",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
        ),
    )

    response = client.post(
        "/api/v1/sales/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "customer_id": None,
            "payment_method": "Cash",
            "payment_status": "Paid",
            "items": [
                {
                    "product_id": product.id,
                    "quantity_sold": 25,
                    "unit_price": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 201

    db.refresh(batch)

    assert batch.current_quantity == 75


# ==================================================
# PROCESS SALE CREATES TRANSACTIONS
# ==================================================

def test_process_sale_creates_transactions(
    client,
    admin_token,
    user_factory,
    product_factory,
    supplier_factory,
    db,
):

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SALE-003",
            initial_quantity=50,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
        ),
    )

    before = db.query(
        InventoryTransaction
    ).count()

    response = client.post(
        "/api/v1/sales/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "customer_id": None,
            "payment_method": "Cash",
            "payment_status": "Paid",
            "items": [
                {
                    "product_id": product.id,
                    "quantity_sold": 5,
                    "unit_price": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 201

    after = db.query(
        InventoryTransaction
    ).count()

    # Initial IN + OUT transaction
    assert after == before + 1


# ==================================================
# PROCESS SALE RETURNS CORRECT TOTAL
# ==================================================

def test_process_sale_returns_total_amount(
    client,
    admin_token,
    user_factory,
    product_factory,
    supplier_factory,
    db,
):

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SALE-004",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("20.00"),
        ),
    )

    response = client.post(
        "/api/v1/sales/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "customer_id": None,
            "payment_method": "Cash",
            "payment_status": "Paid",
            "items": [
                {
                    "product_id": product.id,
                    "quantity_sold": 4,
                    "unit_price": "20.00",
                }
            ],
        },
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["total_amount"]
        == "80.00"
    )


# ==================================================
# PROCESS SALE UNAUTHORIZED
# ==================================================

def test_process_sale_unauthorized(
    client,
    product_factory,
):

    product = product_factory()

    response = client.post(
        "/api/v1/sales/",
        json={
            "customer_id": None,
            "payment_method": "Cash",
            "payment_status": "Paid",
            "items": [
                {
                    "product_id": product.id,
                    "quantity_sold": 1,
                    "unit_price": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 401

    assert response.json()["success"] is False


# ==================================================
# PROCESS SALE INVALID CUSTOMER
# ==================================================

def test_process_sale_invalid_customer(
    client,
    admin_token,
    user_factory,
    product_factory,
    supplier_factory,
    db,
):

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SALE-005",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
        ),
    )

    response = client.post(
        "/api/v1/sales/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "customer_id": 999999,
            "payment_method": "Cash",
            "payment_status": "Paid",
            "items": [
                {
                    "product_id": product.id,
                    "quantity_sold": 1,
                    "unit_price": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400

    assert response.json()["success"] is False


# ==================================================
# PROCESS SALE INSUFFICIENT STOCK
# ==================================================

def test_process_sale_insufficient_stock(
    client,
    admin_token,
    user_factory,
    product_factory,
    supplier_factory,
    db,
):

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SALE-006",
            initial_quantity=5,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
        ),
    )

    response = client.post(
        "/api/v1/sales/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "customer_id": None,
            "payment_method": "Cash",
            "payment_status": "Paid",
            "items": [
                {
                    "product_id": product.id,
                    "quantity_sold": 20,
                    "unit_price": "10.00",
                }
            ],
        },
    )

    assert response.status_code == 400

    assert response.json()["success"] is False


# ==================================================
# PROCESS SALE VALIDATION ERROR
# ==================================================

def test_process_sale_validation_error(
    client,
    admin_token,
):

    response = client.post(
        "/api/v1/sales/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={},
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Validation error."


# ==================================================
# GET SALES SUCCESS
# ==================================================

def test_get_sales_success(
    client,
    admin_token,
    sale_factory,
):

    sale_factory()
    sale_factory()
    sale_factory()

    response = client.get(
        "/api/v1/sales/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert len(body["data"]) == 3


# ==================================================
# GET SALES REQUIRES AUTHENTICATION
# ==================================================

def test_get_sales_requires_authentication(
    client,
):

    response = client.get(
        "/api/v1/sales/",
    )

    assert response.status_code == 401

    assert response.json()["success"] is False


# ==================================================
# GET SALES EMPTY DATABASE
# ==================================================

def test_get_sales_empty_database(
    client,
    admin_token,
):

    response = client.get(
        "/api/v1/sales/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["data"] == []

    assert body["pagination"]["total_items"] == 0


# ==================================================
# GET SALES SORTED BY TOTAL
# ==================================================

def test_get_sales_sort_by_total_amount(
    client,
    admin_token,
    sale_factory,
):

    sale_factory(total_amount=Decimal("50.00"))

    sale_factory(total_amount=Decimal("150.00"))

    sale_factory(total_amount=Decimal("100.00"))

    response = client.get(
        "/api/v1/sales/?sort=total_amount&order=asc",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    totals = [
        Decimal(sale["total_amount"])
        for sale in response.json()["data"]
    ]

    assert totals == sorted(totals)


# ==================================================
# GET SALES SORTED BY DATE
# ==================================================

def test_get_sales_sort_by_date(
    client,
    admin_token,
    sale_factory,
):

    sale_factory()
    sale_factory()
    sale_factory()

    response = client.get(
        "/api/v1/sales/?sort=sold_at&order=desc",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 3


# ==================================================
# GET SALE SUCCESS
# ==================================================

def test_get_sale_success(
    client,
    admin_token,
    sale_item_factory,
):

    item = sale_item_factory()

    sale = item.sale

    response = client.get(
        f"/api/v1/sales/{sale.id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["data"]["id"] == sale.id

    assert body["data"]["total_amount"] == str(
        sale.total_amount
    )


# ==================================================
# GET SALE NOT FOUND
# ==================================================

def test_get_sale_not_found(
    client,
    admin_token,
):

    response = client.get(
        "/api/v1/sales/999999",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 404

    assert response.json()["success"] is False

    assert (
        response.json()["message"]
        == "Sale not found."
    )


# ==================================================
# GET SALE REQUIRES AUTHENTICATION
# ==================================================

def test_get_sale_requires_authentication(
    client,
):

    response = client.get(
        "/api/v1/sales/1",
    )

    assert response.status_code == 401

    assert response.json()["success"] is False


# ==================================================
# GET SALE CONTAINS ITEMS
# ==================================================

def test_get_sale_contains_items(
    client,
    admin_token,
    sale_item_factory,
):

    item = sale_item_factory()

    sale = item.sale

    response = client.get(
        f"/api/v1/sales/{sale.id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    items = response.json()["data"]["items"]

    assert len(items) == 1

    assert items[0]["product_id"] == item.product_id

    assert items[0]["batch_id"] == item.batch_id

    assert items[0]["quantity_sold"] == item.quantity_sold


# ==================================================
# GET SALE WITHOUT CUSTOMER
# ==================================================

def test_get_sale_without_customer(
    client,
    admin_token,
    db,
    user_factory,
    sale_item_factory,
):

    item = sale_item_factory()

    sale = item.sale

    sale.customer_id = None

    db.commit()

    db.refresh(sale)

    response = client.get(
        f"/api/v1/sales/{sale.id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    body = response.json()["data"]

    assert body["customer_id"] is None

    assert body["customer_name"] is None


# ==================================================
# GET SALES LIMIT
# ==================================================

def test_get_sales_limit(
    client,
    admin_token,
    sale_factory,
):

    for _ in range(5):
        sale_factory()

    response = client.get(
        "/api/v1/sales/?limit=2",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 2

    assert body["pagination"]["page_size"] == 2


# ==================================================
# GET SALES SKIP
# ==================================================

def test_get_sales_skip(
    client,
    admin_token,
    sale_factory,
):

    for _ in range(5):
        sale_factory()

    response = client.get(
        "/api/v1/sales/?skip=2&limit=2",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 2

    assert body["pagination"]["page"] == 2


# ==================================================
# GET SALES PAGINATION METADATA
# ==================================================

def test_get_sales_pagination_metadata(
    client,
    admin_token,
    sale_factory,
):

    for _ in range(3):
        sale_factory()

    response = client.get(
        "/api/v1/sales/?limit=2",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    pagination = response.json()["pagination"]

    assert pagination["total_items"] == 3

    assert pagination["page_size"] == 2

    assert pagination["total_pages"] == 2

    assert pagination["has_next"] is True

    assert pagination["has_previous"] is False