import uuid
from decimal import Decimal

import pytest

from app.models.core import Product


# ==================================================
# PRODUCT FACTORY
# ==================================================

@pytest.fixture
def product_factory(db, category_factory):
    """
    Factory fixture for creating products.

    Examples:

        product = product_factory()

        product = product_factory(
            name="Coca-Cola",
            sku_or_barcode="P000001",
        )

        category = category_factory(name="Beverages")

        product = product_factory(
            category=category,
            name="Orange Juice",
        )
    """

    def factory(
        *,
        category=None,
        name: str = "Test Product",
        description: str = "Test product description.",
        sku_or_barcode: str | None = None,
        unit_of_measure: str = "Units",
        base_price: Decimal = Decimal("10.00"),
        min_stock_threshold: int = 5,
        is_active: bool = True,
    ) -> Product:

        if category is None:
            category = category_factory()

        product_sku = (
            sku_or_barcode
            if sku_or_barcode is not None
            else f"SKU-{uuid.uuid4().hex[:8].upper()}"
        )

        product = Product(
            category_id=category.id,
            name=name,
            description=description,
            sku_or_barcode=product_sku,
            unit_of_measure=unit_of_measure,
            base_price=base_price,
            min_stock_threshold=min_stock_threshold,
            is_active=is_active,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return product

    return factory


# ==================================================
# DEFAULT PRODUCT
# ==================================================

@pytest.fixture
def product(product_factory):
    """
    Creates a default product.
    """

    return product_factory()