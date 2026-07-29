from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models.core import InventoryTransaction
from app.schemas.core import TransactionType


# ==================================================
# LOW STOCK PRODUCT
# ==================================================

@pytest.fixture
def low_stock_product(
    db,
    product_factory,
    inventory_batch_factory,
):
    """
    Product whose stock is BELOW its minimum threshold.

    Used by the Low Stock report.
    """

    product = product_factory(
        name = "Low Stock Product",
        min_stock_threshold=10,
    )

    batch = inventory_batch_factory(
        product=product,
        initial_quantity=5,
        current_quantity=5,
    )

    db.refresh(product)
    db.refresh(batch)

    return product


# ==================================================
# NORMAL STOCK PRODUCT
# ==================================================

@pytest.fixture
def normal_stock_product(
    db,
    product_factory,
    inventory_batch_factory,
):
    """
    Product with healthy stock.

    Should NOT appear in the Low Stock report.
    """

    product = product_factory(
        name="Normal Stock Product",
        min_stock_threshold=10,
    )

    batch = inventory_batch_factory(
        product=product,
        initial_quantity=50,
        current_quantity=50,
    )

    db.refresh(product)
    db.refresh(batch)

    return product


# ==================================================
# EXPIRING BATCH
# ==================================================

@pytest.fixture
def expiring_batch(
    db,
    inventory_batch_factory,
):
    """
    Batch expiring in 10 days.
    """

    batch = inventory_batch_factory(
        expiration_date=date.today() + timedelta(days=10),
        current_quantity=20,
    )

    db.refresh(batch)

    return batch


# ==================================================
# NON-EXPIRING BATCH
# ==================================================

@pytest.fixture
def non_expiring_batch(
    db,
    inventory_batch_factory,
):
    """
    Batch expiring far in the future.

    Should not appear in a 30-day report.
    """

    batch = inventory_batch_factory(
        expiration_date=date.today() + timedelta(days=120),
        current_quantity=20,
    )

    db.refresh(batch)

    return batch


# ==================================================
# EXPIRED BATCH
# ==================================================

@pytest.fixture
def expired_batch(
    db,
    inventory_batch_factory,
):
    """
    Already expired batch.

    Should never appear in the report.
    """

    batch = inventory_batch_factory(
        expiration_date=date.today() - timedelta(days=5),
        current_quantity=20,
    )

    db.refresh(batch)

    return batch


# ==================================================
# BATCH WITHOUT EXPIRATION
# ==================================================

@pytest.fixture
def batch_without_expiration(
    db,
    inventory_batch_factory,
):
    """
    Batch without expiration date.
    """

    batch = inventory_batch_factory(
        expiration_date=None,
        current_quantity=20,
    )

    db.refresh(batch)

    return batch


# ==================================================
# BATCH AUDIT DATASET
# ==================================================

@pytest.fixture
def batch_audit_dataset(
    db,
    inventory_batch_factory,
    user_factory,
):
    """
    Creates one batch containing three inventory
    transactions:

    IN
    OUT
    LOSS

    Used by the Batch Audit report.
    """

    user = user_factory()

    batch = inventory_batch_factory()

    tx_in = InventoryTransaction(
        product_id=batch.product_id,
        batch_id=batch.id,
        user_id=user.id,
        quantity_changed=batch.initial_quantity,
        transaction_type=TransactionType.IN.value,
        notes="Initial inventory",
    )

    tx_out = InventoryTransaction(
        product_id=batch.product_id,
        batch_id=batch.id,
        user_id=user.id,
        quantity_changed=-3,
        transaction_type=TransactionType.OUT.value,
        notes="Sale",
    )

    tx_loss = InventoryTransaction(
        product_id=batch.product_id,
        batch_id=batch.id,
        user_id=user.id,
        quantity_changed=-2,
        transaction_type=TransactionType.LOSS.value,
        notes="Damaged",
    )

    db.add_all([
        tx_in,
        tx_out,
        tx_loss,
    ])

    db.commit()

    db.refresh(batch)

    return batch


# ==================================================
# SALES PERFORMANCE DATASET
# ==================================================

@pytest.fixture
def sales_report_dataset(
    sale_factory,
):
    """
    Creates several sales with different totals.

    Total revenue:
        100
        200
        300

    Expected total = 600
    """

    sale_factory(
        total_amount=Decimal("100.00"),
    )

    sale_factory(
        total_amount=Decimal("200.00"),
    )

    sale_factory(
        total_amount=Decimal("300.00"),
    )