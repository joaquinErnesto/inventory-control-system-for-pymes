from datetime import date
from decimal import Decimal
import uuid

import pytest

from app.models.core import (
    InventoryBatch,
    InventoryTransaction
)

from app.schemas.core import TransactionType


# ==================================================
# INVENTORY BATCH FACTORY
# ==================================================

@pytest.fixture
def inventory_batch_factory(
    db,
    product_factory,
    supplier_factory,
    user_factory,
):
    """
    Factory fixture for creating inventory batches.

    Examples:

        batch = inventory_batch_factory()

        batch = inventory_batch_factory(
            initial_quantity=150,
            current_quantity=80,
        )

        product = product_factory()

        batch = inventory_batch_factory(
            product=product,
        )
    """

    def factory(
        *,
        product=None,
        supplier=None,
        created_by_user=None,
        batch_number: str | None = None,
        initial_quantity: int = 100,
        current_quantity: int | None = None,
        cost_price: Decimal = Decimal("10.00"),
        selling_price: Decimal = Decimal("15.00"),
        expiration_date: date | None = None,
        notes: str = "Test inventory batch.",
        create_initial_transaction: bool = False
    ) -> InventoryBatch:

        if product is None:
            product = product_factory()

        if supplier is None:
            supplier = supplier_factory()

        if created_by_user is None:
            created_by_user = user_factory()

        if current_quantity is None:
            current_quantity = initial_quantity

        generated_batch_number = (
            batch_number
            if batch_number is not None
            else f"BATCH-{uuid.uuid4().hex[:8].upper()}"
        )

        batch = InventoryBatch(
            product_id=product.id,
            supplier_id=supplier.id,
            created_by_user_id=created_by_user.id,
            batch_number=generated_batch_number,
            initial_quantity=initial_quantity,
            current_quantity=current_quantity,
            cost_price=cost_price,
            selling_price=selling_price,
            expiration_date=expiration_date,
            notes=notes,
        )

        db.add(batch)
        db.commit()
        db.refresh(batch)

        if create_initial_transaction:

            transaction = InventoryTransaction(
                product_id=batch.product_id,
                batch_id=batch.id,
                user_id=batch.created_by_user_id,
                quantity_changed=batch.initial_quantity,
                transaction_type=TransactionType.IN.value,
                notes=f"Initial stock intake. Batch: {batch.batch_number}",
            )

            db.add(transaction)
            db.commit()
            db.refresh(transaction)

        return batch

    return factory


# ==================================================
# DEFAULT INVENTORY BATCH
# ==================================================

@pytest.fixture
def inventory_batch(inventory_batch_factory):
    """
    Creates a default inventory batch.
    """

    return inventory_batch_factory()


# ==================================================
# DEFAULT INVENTORY BATCH REQUEST
# ==================================================

@pytest.fixture
def inventory_batch_request(
    product,
    supplier,
):
    """
    Creates a valid InventoryBatchCreate request
    for service-layer tests.
    """

    from app.schemas.core import InventoryBatchCreate

    return InventoryBatchCreate(
        product_id=product.id,
        supplier_id=supplier.id,
        batch_number="TEST-BATCH-001",
        initial_quantity=100,
        cost_price=Decimal("10.00"),
        selling_price=Decimal("15.00"),
        expiration_date=None,
        notes="Test inventory batch request.",
    )