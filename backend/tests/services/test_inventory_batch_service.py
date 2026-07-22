from decimal import Decimal

import pytest

from datetime import date

from fastapi import HTTPException

from app.models.core import (
    InventoryTransaction,
    InventoryBatch,
    Product
)
from app.schemas.core import InventoryBatchCreate, TransactionType
from app.services.inventory_batch_service import (
    receive_inventory_batch,
)


# ==================================================
# RECEIVE INVENTORY BATCH SUCCESS
# ==================================================

def test_receive_inventory_batch_success(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should create an inventory batch and
    automatically register an IN transaction.
    """

    #
    # Arrange
    #

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    batch_data = InventoryBatchCreate(
        product_id=product.id,
        supplier_id=supplier.id,
        batch_number="TEST-001",
        initial_quantity=100,
        cost_price=Decimal("5.00"),
        selling_price=Decimal("8.00"),
        expiration_date=None,
        notes="Initial stock",
    )

    #
    # Act
    #

    batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=batch_data,
    )

    #
    # Assert
    #

    assert batch.id is not None

    assert batch.product_id == product.id

    assert batch.supplier_id == supplier.id

    assert batch.created_by_user_id == admin.id

    assert batch.initial_quantity == 100

    assert batch.current_quantity == 100

    assert batch.cost_price == Decimal("5.00")

    assert batch.selling_price == Decimal("8.00")

    transaction = (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.batch_id == batch.id
        )
        .first()
    )

    assert transaction is not None

    assert transaction.product_id == product.id

    assert transaction.user_id == admin.id

    assert transaction.quantity_changed == 100

    assert (
        transaction.transaction_type
        == TransactionType.IN.value
    )

    assert transaction.notes.startswith(
        "Initial stock intake."
    )


# ==================================================
# RECEIVE INVENTORY BATCH INVALID PRODUCT
# ==================================================

def test_receive_inventory_batch_invalid_product(
    db,
    user_factory,
    supplier_factory,
):
    """
    Should raise an HTTPException when
    the product does not exist.
    """

    #
    # Arrange
    #

    NON_EXISTENT_PRODUCT_ID = 999999
    
    admin = user_factory(role="admin")

    supplier = supplier_factory()

    batch_data = InventoryBatchCreate(
        product_id=NON_EXISTENT_PRODUCT_ID,
        supplier_id=supplier.id,
        batch_number="TEST-001",
        initial_quantity=100,
        cost_price=Decimal("5.00"),
        selling_price=Decimal("8.00"),
        expiration_date=None,
        notes="Initial stock",
    )

    #
    # Act / Assert
    #

    with pytest.raises(HTTPException) as exc:

        receive_inventory_batch(
            db=db,
            current_user=admin,
            batch=batch_data,
        )

    #
    # Assert
    #

    assert exc.value.status_code == 400

    assert (
        exc.value.detail
        == f"Product with ID {NON_EXISTENT_PRODUCT_ID} does not exist."
    )
    

# ==================================================
# RECEIVE INVENTORY BATCH INVALID SUPPLIER
# ==================================================

def test_receive_inventory_batch_invalid_supplier(
    db,
    admin_user,
    product,
):
    """
    A batch cannot be received using
    a supplier that does not exist.
    """

    batch_data = InventoryBatchCreate(
        product_id=product.id,
        supplier_id=999999,
        batch_number="BATCH-001",
        initial_quantity=50,
        cost_price=Decimal("10.00"),
        selling_price=Decimal("15.00"),
        expiration_date=date(2027, 12, 31),
        notes="Test batch",
    )

    with pytest.raises(HTTPException) as exc_info:
        receive_inventory_batch(
            db=db,
            current_user=admin_user,
            batch=batch_data,
        )

    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "Supplier with ID 999999 does not exist."
    )

    #
    # Ensure nothing was created
    #

    assert (
        db.query(InventoryBatch).count()
        == 0
    )

    assert (
        db.query(InventoryTransaction).count()
        == 0
    )
    

# ==================================================
# RECEIVE INVENTORY BATCH ZERO QUANTITY
# ==================================================

def test_receive_inventory_batch_zero_quantity(
    db,
    admin_user,
    product,
    supplier,
):
    """
    A batch cannot be created when the initial quantity is zero.
    """

    batch_data = InventoryBatchCreate(
        product_id=product.id,
        supplier_id=supplier.id,
        batch_number="BATCH-001",
        initial_quantity=0,
        cost_price=Decimal("10.00"),
        selling_price=Decimal("15.00"),
        expiration_date=date(2027, 12, 31),
        notes="Test batch",
    )

    with pytest.raises(HTTPException) as exc_info:
        receive_inventory_batch(
            db=db,
            current_user=admin_user,
            batch=batch_data,
        )

    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "Initial quantity must be greater than zero."
    )


# ==================================================
# RECEIVE INVENTORY BATCH NEGATIVE COST PRICE
# ==================================================

def test_receive_inventory_batch_negative_cost_price(
    db,
    admin_user,
    supplier,
    product,
):
    """
    Should raise HTTPException when the cost price is negative.
    """

    batch_data = InventoryBatchCreate(
        product_id=product.id,
        supplier_id=supplier.id,
        batch_number="BATCH-001",
        initial_quantity=50,
        cost_price=Decimal("-1.00"),
        selling_price=Decimal("2.50"),
        expiration_date=date(2027, 12, 31),
        notes="Invalid cost price test",
    )

    with pytest.raises(HTTPException) as exc:

        receive_inventory_batch(
            db=db,
            current_user=admin_user,
            batch=batch_data,
        )

    assert exc.value.status_code == 400

    assert (
        exc.value.detail
        == "Cost price cannot be negative."
    )
    

# ==================================================
# RECEIVE INVENTORY BATCH NEGATIVE SELLING PRICE
# ==================================================

def test_receive_inventory_batch_negative_selling_price(
    db,
    admin_user,
    category,
    supplier,
):
    """
    Should raise HTTPException(400) when the selling price is negative.
    """

    batch_data = InventoryBatchCreate(
        product_id=999,  # Placeholder (updated below)
        supplier_id=supplier.id,
        batch_number="TEST-006",
        initial_quantity=50,
        cost_price=Decimal("10.00"),
        selling_price=Decimal("-1.00"),
        expiration_date=None,
        notes="Testing negative selling price.",
    )

    product = Product(
        category_id=category.id,
        name="Test Product",
        sku_or_barcode="TEST-006",
        unit_of_measure="Units",
        base_price=Decimal("15.00"),
        min_stock_threshold=5,
        is_active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    batch_data.product_id = product.id

    with pytest.raises(HTTPException) as exc:

        receive_inventory_batch(
            db=db,
            current_user=admin_user,
            batch=batch_data,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Selling price cannot be negative."