import pytest

from datetime import datetime

from app.models.core import InventoryTransaction
from app.schemas.core import TransactionType


# ==================================================
# INVENTORY TRANSACTION FACTORY
# ==================================================

@pytest.fixture
def inventory_transaction_factory(
    db,
    product_factory,
    inventory_batch_factory,
    user_factory,
):
    """
    Factory fixture for creating inventory transactions.

    Examples:

        transaction = inventory_transaction_factory()

        transaction = inventory_transaction_factory(
            quantity_changed=-5,
            transaction_type=TransactionType.OUT.value,
        )

        batch = inventory_batch_factory()

        transaction = inventory_transaction_factory(
            batch=batch,
        )
    """

    def factory(
        *,
        product=None,
        batch=None,
        user=None,
        quantity_changed: int = 100,
        transaction_type: str = TransactionType.IN.value,
        sale=None,
        loss=None,
        notes: str = "Test inventory transaction.",
        performed_at: datetime | None = None
    ) -> InventoryTransaction:

        #
        # Create related entities if not provided
        #

        if batch is None:
            batch = inventory_batch_factory()

        if product is None:
            product = batch.product

        if user is None:
            user = user_factory()

        if performed_at is None :
            performed_at = datetime.now()
            
        transaction = InventoryTransaction(
            product_id=product.id,
            batch_id=batch.id,
            user_id=user.id,
            quantity_changed=quantity_changed,
            transaction_type=transaction_type,
            sale_id=sale.id if sale else None,
            loss_id=loss.id if loss else None,
            notes=notes,
            performed_at = performed_at
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return transaction

    return factory


# ==================================================
# DEFAULT INVENTORY TRANSACTION
# ==================================================

@pytest.fixture
def inventory_transaction(
    inventory_transaction_factory,
):
    """
    Creates a default inventory transaction.
    """

    return inventory_transaction_factory()