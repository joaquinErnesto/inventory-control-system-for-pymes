from decimal import Decimal

import pytest

from fastapi import HTTPException

from app.models.core import (
    InventoryBatch,
    InventoryTransaction,
    LossLog,
    Sale,
    SaleItem,
)
from app.schemas.core import (
    InventoryBatchCreate,
    TransactionType,
    PaymentMethod,
    PaymentStatus,
    LossReason,
)

from app.services.inventory_batch_service import (
    receive_inventory_batch,
    delete_inventory_batch,
)


# ==================================================
# DELETE INVENTORY BATCH SUCCESS
# ==================================================

def test_delete_inventory_batch_success(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should delete a batch that has never been used.
    """

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="DELETE-001",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    delete_inventory_batch(
        db=db,
        batch_id=batch.id
    )

    assert (
        db.query(InventoryBatch)
        .filter(InventoryBatch.id == batch.id)
        .first()
        is None
    )
    

# ==================================================
# DELETE INVENTORY BATCH NOT FOUND
# ==================================================

def test_delete_inventory_batch_not_found(
    db,
    user_factory,
):
    """
    Should raise HTTPException when the batch
    does not exist.
    """

    admin = user_factory(role="admin")

    with pytest.raises(HTTPException) as exc:

        delete_inventory_batch(
            db=db,
            batch_id=999999
        )

    assert exc.value.status_code == 404

    assert exc.value.detail == "Inventory batch not found."


# ==================================================
# DELETE INVENTORY BATCH USED IN SALES
# ==================================================

def test_delete_inventory_batch_used_in_sales(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should not delete a batch used in sales.
    """

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SALE-001",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    sale = Sale(
        user_id=admin.id,
        customer_id=None,
        total_amount=Decimal("8.00"),
        payment_method=PaymentMethod.CASH.value,
        payment_status=PaymentStatus.PAID.value,
    )

    db.add(sale)

    db.flush()

    sale_item = SaleItem(
        sale_id=sale.id,
        batch_id=batch.id,
        product_id=product.id,
        quantity_sold=1,
        unit_price=Decimal("8.00"),
    )

    db.add(sale_item)

    db.commit()

    with pytest.raises(HTTPException) as exc:

        delete_inventory_batch(
            db=db,
            batch_id=batch.id
        )

    assert exc.value.status_code == 400

    assert (
        exc.value.detail
        == "Cannot delete a batch used in sales."
    )


# ==================================================
# DELETE INVENTORY BATCH WITH LOSSES
# ==================================================

def test_delete_inventory_batch_with_losses(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should not delete a batch with registered losses.
    """

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="LOSS-001",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    loss = LossLog(
        batch_id=batch.id,
        user_id=admin.id,
        quantity_lost=5,
        reason=LossReason.DAMAGED.value,
        notes="Testing",
    )

    db.add(loss)

    db.commit()

    with pytest.raises(HTTPException) as exc:

        delete_inventory_batch(
            db=db,
            batch_id=batch.id
        )

    assert exc.value.status_code == 400

    assert (
        exc.value.detail
        == "Cannot delete a batch that has registered losses."
    )
    

# ==================================================
# DELETE INVENTORY BATCH WITH EXTRA TRANSACTIONS
# ==================================================

def test_delete_inventory_batch_with_extra_transaction(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should not delete a batch that has inventory
    transactions other than the initial IN transaction.
    """

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="TX-001",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    transaction = InventoryTransaction(
        product_id=product.id,
        batch_id=batch.id,
        user_id=admin.id,
        quantity_changed=-10,
        transaction_type=TransactionType.ADJUSTMENT.value,
        notes="Adjustment",
    )

    db.add(transaction)

    db.commit()

    with pytest.raises(HTTPException) as exc:

        delete_inventory_batch(
            db=db,
            batch_id=batch.id
        )

    assert exc.value.status_code == 400

    assert (
        exc.value.detail
        == "Cannot delete a batch because inventory transactions exist."
    )
    

# ====================================================
# DELETE INVENTORY BATCH WITH ONLY INITIAL TRANSACTION
# ====================================================

def test_delete_inventory_batch_only_initial_transaction(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should allow deleting a batch when the only
    inventory transaction is the automatically
    created initial IN transaction.
    """

    #
    # Arrange
    #

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="INITIAL-001",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    #
    # Verify exactly one transaction exists
    #

    assert len(batch.transactions) == 1

    transaction = batch.transactions[0]

    assert transaction.transaction_type == TransactionType.IN.value
    assert transaction.quantity_changed == 100

    #
    # Act
    #

    delete_inventory_batch(
        db=db,
        batch_id=batch.id,
    )

    #
    # Assert
    #

    assert (
        db.query(InventoryBatch)
        .filter(InventoryBatch.id == batch.id)
        .first()
        is None
    )

    #
    # Cascade should delete the initial transaction
    #

    assert (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.batch_id == batch.id
        )
        .count()
        == 0
    )