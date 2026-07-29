from decimal import Decimal

from app.models.core import (
    InventoryTransaction,
    LossLog
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

from app.services.loss_logs_service import (
    register_loss,
)


# ==================================================
# REGISTER LOSS SUCCESS
# ==================================================

def test_register_loss_success(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should register a new inventory loss successfully.
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

    loss = register_loss(
        db=db,
        current_user=admin,
        loss=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=5,
            reason=LossReason.DAMAGED,
            notes="Broken bottles",
        ),
    )

    assert loss.id is not None
    assert loss.batch_id == batch.id
    assert loss.user_id == admin.id
    assert loss.quantity_lost == 5
    assert loss.reason == LossReason.DAMAGED.value
    

# ==================================================
# REGISTER LOSS DECREASES INVENTORY
# ==================================================

def test_register_loss_decreases_inventory(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should deduct the lost quantity from the batch.
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
            batch_number="LOSS-002",
            initial_quantity=50,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    register_loss(
        db=db,
        current_user=admin,
        loss=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=12,
            reason=LossReason.DAMAGED,
        ),
    )

    db.refresh(batch)

    assert batch.current_quantity == 38
    

# ==================================================
# REGISTER LOSS CREATES TRANSACTION
# ==================================================

def test_register_loss_creates_inventory_transaction(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should create a LOSS transaction in the ledger.
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
            batch_number="LOSS-003",
            initial_quantity=40,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    loss = register_loss(
        db=db,
        current_user=admin,
        loss=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=7,
            reason=LossReason.EXPIRED,
        ),
    )

    transaction = (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.loss_id == loss.id
        )
        .first()
    )

    assert transaction is not None
    assert transaction.batch_id == batch.id
    assert transaction.product_id == product.id
    assert transaction.user_id == admin.id
    assert transaction.quantity_changed == -7
    assert transaction.transaction_type == TransactionType.LOSS.value


# ==================================================
# REGISTER LOSS STORES NOTES
# ==================================================

def test_register_loss_stores_notes(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should persist optional notes.
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
            batch_number="LOSS-004",
            initial_quantity=25,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    notes = "Package damaged during transportation."

    loss = register_loss(
        db=db,
        current_user=admin,
        loss=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=3,
            reason=LossReason.DAMAGED,
            notes=notes,
        ),
    )

    assert loss.notes == notes


# ==================================================
# REGISTER LOSS - BATCH NOT FOUND
# ==================================================

def test_register_loss_batch_not_found(
    db,
    user_factory,
):
    """
    Should raise 404 when the batch does not exist.
    """

    from fastapi import HTTPException
    import pytest

    admin = user_factory(role="admin")

    with pytest.raises(HTTPException) as exc:

        register_loss(
            db=db,
            current_user=admin,
            loss=LossLogCreate(
                batch_id=999999,
                quantity_lost=5,
                reason=LossReason.DAMAGED,
            ),
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Batch not found."


# ==================================================
# REGISTER LOSS - INACTIVE PRODUCT
# ==================================================

def test_register_loss_inactive_product(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should not allow losses on inactive products.
    """

    from fastapi import HTTPException
    import pytest

    admin = user_factory(role="admin")

    product = product_factory(
        is_active=False,
    )

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="INACTIVE-001",
            initial_quantity=30,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    with pytest.raises(HTTPException) as exc:

        register_loss(
            db=db,
            current_user=admin,
            loss=LossLogCreate(
                batch_id=batch.id,
                quantity_lost=5,
                reason=LossReason.DAMAGED,
            ),
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "Cannot register losses for an inactive product."
    )


# ==================================================
# REGISTER LOSS - INSUFFICIENT STOCK
# ==================================================

def test_register_loss_insufficient_stock(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should not allow losing more units than exist.
    """

    from fastapi import HTTPException
    import pytest

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="LOW-001",
            initial_quantity=10,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    with pytest.raises(HTTPException) as exc:

        register_loss(
            db=db,
            current_user=admin,
            loss=LossLogCreate(
                batch_id=batch.id,
                quantity_lost=50,
                reason=LossReason.DAMAGED,
            ),
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "Insufficient stock to log this loss."
    )


# ==================================================
# REGISTER LOSS ROLLBACK
# ==================================================

def test_register_loss_rollback_on_failure(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Inventory should remain unchanged after a failed loss.
    """

    from fastapi import HTTPException
    import pytest

    admin = user_factory(role="admin")

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="ROLLBACK-001",
            initial_quantity=20,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    with pytest.raises(HTTPException):

        register_loss(
            db=db,
            current_user=admin,
            loss=LossLogCreate(
                batch_id=batch.id,
                quantity_lost=100,
                reason=LossReason.DAMAGED,
            ),
        )

    db.refresh(batch)

    assert batch.current_quantity == 20


# ==================================================
# REGISTER LOSS LINKS TRANSACTION TO LOSS
# ==================================================

def test_register_loss_links_transaction_to_loss(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    The inventory transaction should reference
    the created loss record.
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
            batch_number="LINK-001",
            initial_quantity=40,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    loss = register_loss(
        db=db,
        current_user=admin,
        loss=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=8,
            reason=LossReason.DAMAGED,
        ),
    )

    transaction = (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.loss_id == loss.id
        )
        .first()
    )

    assert transaction is not None
    assert transaction.loss_id == loss.id


# ==================================================
# REGISTER LOSS TRANSACTION NOTES
# ==================================================

def test_register_loss_transaction_note(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    The generated inventory transaction should
    contain a meaningful note.
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
            batch_number="NOTE-001",
            initial_quantity=30,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    loss = register_loss(
        db=db,
        current_user=admin,
        loss=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=4,
            reason=LossReason.EXPIRED,
        ),
    )

    transaction = (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.loss_id == loss.id
        )
        .first()
    )

    assert transaction.notes == "Loss Logged: Expired"


# ==================================================
# REGISTER LOSS LOW STOCK
# ==================================================

def test_register_loss_reaches_low_stock_threshold(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Registering a loss that reaches the minimum stock
    threshold should still succeed.
    """

    admin = user_factory(role="admin")

    product = product_factory(
        min_stock_threshold=5,
    )

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="LOWSTOCK-001",
            initial_quantity=10,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    loss = register_loss(
        db=db,
        current_user=admin,
        loss=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=5,
            reason=LossReason.DAMAGED,
        ),
    )

    db.refresh(batch)

    assert loss.id is not None
    assert batch.current_quantity == 5


# ==================================================
# REGISTER LOSS WITH NOTES
# ==================================================

def test_register_loss_with_notes(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should store optional notes.
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
            batch_number="NOTES-001",
            initial_quantity=30,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    loss = register_loss(
        db=db,
        current_user=admin,
        loss=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=5,
            reason=LossReason.DAMAGED,
            notes="Broken during transport",
        ),
    )

    assert loss.notes == "Broken during transport"


# ==================================================
# MULTIPLE LOSSES
# ==================================================

def test_register_multiple_losses(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Multiple losses should deduct stock correctly.
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
            batch_number="MULTI-001",
            initial_quantity=50,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    register_loss(
        db=db,
        current_user=admin,
        loss=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=8,
            reason=LossReason.DAMAGED,
        ),
    )

    register_loss(
        db=db,
        current_user=admin,
        loss=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=7,
            reason=LossReason.EXPIRED,
        ),
    )

    db.refresh(batch)

    assert batch.current_quantity == 35

    assert (
        db.query(LossLog).count()
        == 2
    )

    assert (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.transaction_type
            == TransactionType.LOSS.value
        )
        .count()
        == 2
    )


# ==================================================
# DIFFERENT LOSS REASONS
# ==================================================

def test_register_loss_reason_saved(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    The selected loss reason should be persisted.
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
            batch_number="REASON-001",
            initial_quantity=20,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    loss = register_loss(
        db=db,
        current_user=admin,
        loss=LossLogCreate(
            batch_id=batch.id,
            quantity_lost=2,
            reason=LossReason.THEFT,
        ),
    )

    assert loss.reason == LossReason.THEFT.value