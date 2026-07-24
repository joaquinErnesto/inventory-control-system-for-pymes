from decimal import Decimal

import pytest

from app.models.core import SaleItem


# ==================================================
# SALE ITEM FACTORY
# ==================================================

@pytest.fixture
def sale_item_factory(
    db,
    sale_factory,
    inventory_batch_factory,
):
    """
    Factory fixture for creating sale items.

    Examples:

        item = sale_item_factory()

        item = sale_item_factory(
            quantity_sold=5,
        )

        sale = sale_factory()

        item = sale_item_factory(
            sale=sale,
        )
    """

    def factory(
        *,
        sale=None,
        batch=None,
        quantity_sold: int = 2,
        unit_price: Decimal = Decimal("15.00"),
    ) -> SaleItem:

        if sale is None:
            sale = sale_factory()

        if batch is None:
            batch = inventory_batch_factory()

        item = SaleItem(
            sale_id=sale.id,
            batch_id=batch.id,
            product_id=batch.product_id,
            quantity_sold=quantity_sold,
            unit_price=unit_price,
        )

        db.add(item)
        db.commit()
        db.refresh(item)

        return item

    return factory


# ==================================================
# DEFAULT SALE ITEM
# ==================================================

@pytest.fixture
def sale_item(
    sale_item_factory,
):
    """
    Creates a default sale item.
    """

    return sale_item_factory()