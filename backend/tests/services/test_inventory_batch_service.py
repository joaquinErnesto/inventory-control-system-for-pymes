from decimal import Decimal

import pytest

from datetime import date

from fastapi import HTTPException

from app.models.core import (
    InventoryTransaction,
    InventoryBatch
)
from app.schemas.core import InventoryBatchCreate, TransactionType, SortOrder
from app.services.inventory_batch_service import (
    receive_inventory_batch,
    get_inventory_batch_by_id,
    list_inventory_batches
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
# GET INVENTORY BATCH BY ID SUCCESS
# ==================================================

def test_get_inventory_batch_by_id_success(
    db,
    inventory_batch_factory,
):
    """
    Should return the requested inventory batch.
    """

    #
    # Arrange
    #

    batch = inventory_batch_factory()

    #
    # Act
    #

    result = get_inventory_batch_by_id(
        db=db,
        batch_id=batch.id,
    )

    #
    # Assert
    #

    assert result.id == batch.id

    assert result.product_id == batch.product_id

    assert result.supplier_id == batch.supplier_id

    assert result.batch_number == batch.batch_number

    assert result.initial_quantity == batch.initial_quantity

    assert result.current_quantity == batch.current_quantity

    assert result.cost_price == batch.cost_price

    assert result.selling_price == batch.selling_price


# ==================================================
# GET INVENTORY BATCH BY ID NOT FOUND
# ==================================================

def test_get_inventory_batch_by_id_not_found(
    db,
):
    """
    Should raise an HTTPException when
    the inventory batch does not exist.
    """

    #
    # Arrange
    #

    NON_EXISTENT_BATCH_ID = 999999

    #
    # Act / Assert
    #

    with pytest.raises(HTTPException) as exc:

        get_inventory_batch_by_id(
            db=db,
            batch_id=NON_EXISTENT_BATCH_ID,
        )

    #
    # Assert
    #

    assert exc.value.status_code == 404

    assert (
        exc.value.detail
        == "Inventory batch not found."
    )
    

# ==================================================
# LIST INVENTORY BATCHES SORT BY COST PRICE
# ==================================================

def test_list_inventory_batches_sort_by_cost_price(
    db,
    inventory_batch_factory,
):
    """
    Should return batches ordered by cost price ascending.
    """

    #
    # Arrange
    #

    inventory_batch_factory(
        cost_price=Decimal("30.00"),
    )

    inventory_batch_factory(
        cost_price=Decimal("10.00"),
    )

    inventory_batch_factory(
        cost_price=Decimal("20.00"),
    )

    #
    # Act
    #

    batches, pagination = list_inventory_batches(
        db=db,
        skip=0,
        limit=10,
        sort="cost_price",
        order=SortOrder.ASC,
    )

    #
    # Assert
    #

    assert len(batches) == 3

    assert batches[0].cost_price == Decimal("10.00")
    assert batches[1].cost_price == Decimal("20.00")
    assert batches[2].cost_price == Decimal("30.00")


# ==================================================
# LIST INVENTORY BATCHES SORT DESCENDING
# ==================================================

def test_list_inventory_batches_sort_desc(
    db,
    inventory_batch_factory,
):
    """
    Should return batches ordered by cost price descending.
    """

    #
    # Arrange
    #

    inventory_batch_factory(
        cost_price=Decimal("30.00"),
    )

    inventory_batch_factory(
        cost_price=Decimal("10.00"),
    )

    inventory_batch_factory(
        cost_price=Decimal("20.00"),
    )

    #
    # Act
    #

    batches, pagination = list_inventory_batches(
        db=db,
        skip=0,
        limit=10,
        sort="cost_price",
        order=SortOrder.DESC,
    )

    #
    # Assert
    #

    assert len(batches) == 3

    assert batches[0].cost_price == Decimal("30.00")
    assert batches[1].cost_price == Decimal("20.00")
    assert batches[2].cost_price == Decimal("10.00")


# ==================================================
# LIST INVENTORY BATCHES PAGINATION
# ==================================================

def test_list_inventory_batches_pagination(
    db,
    inventory_batch_factory,
):
    """
    Should paginate inventory batches correctly.
    """

    #
    # Arrange
    #

    for _ in range(5):
        inventory_batch_factory()

    #
    # Act
    #

    batches, pagination = list_inventory_batches(
        db=db,
        skip=2,
        limit=2,
        sort="received_date",
        order=SortOrder.DESC,
    )

    #
    # Assert
    #

    assert len(batches) == 2

    assert pagination.total_items == 5
    assert pagination.page == 2
    assert pagination.page_size == 2
    assert pagination.total_pages == 3
    assert pagination.has_previous is True
    assert pagination.has_next is True
        

# ==================================================
# LIST INVENTORY BATCHES INVALID SORT FIELD
# ==================================================

def test_list_inventory_batches_invalid_sort_field(
    db,
):
    """
    Should raise an HTTPException when
    an invalid sort field is requested.
    """

    #
    # Act / Assert
    #

    with pytest.raises(HTTPException) as exc:

        list_inventory_batches(
            db=db,
            skip=0,
            limit=10,
            sort="invalid_field",
            order=SortOrder.ASC,
        )

    #
    # Assert
    #

    assert exc.value.status_code == 400

    assert "Invalid sort field." in exc.value.detail
    
    
# ==================================================
# LIST INVENTORY BATCHES DEFAULT ORDER
# ==================================================

def test_list_inventory_batches_default_order(
    db,
    inventory_batch_factory,
):
    """
    Should return batches ordered by received_date descending.
    """

    #
    # Arrange
    #

    inventory_batch_factory()
    inventory_batch_factory()
    inventory_batch_factory()

    #
    # Act
    #

    batches, pagination = list_inventory_batches(
        db=db,
        skip=0,
        limit=10,
        sort="received_date",
        order=SortOrder.DESC,
    )

    #
    # Assert
    #

    assert len(batches) == 3

    assert pagination.total_items == 3
    assert pagination.page == 1
    assert pagination.page_size == 10
    assert pagination.total_pages == 1
    assert pagination.has_previous is False
    assert pagination.has_next is False