from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.core import InventoryBatchCreate


# ==================================================
# INVENTORY BATCH CREATE - VALID DATA
# ==================================================

def test_inventory_batch_create_valid():
    """
    InventoryBatchCreate should accept valid data.
    """

    batch = InventoryBatchCreate(
        product_id=1,
        supplier_id=1,
        batch_number="BATCH-001",
        initial_quantity=100,
        cost_price=Decimal("10.00"),
        selling_price=Decimal("15.00"),
        expiration_date=date(2027, 12, 31),
        notes="Valid batch",
    )

    assert batch.product_id == 1
    assert batch.supplier_id == 1
    assert batch.initial_quantity == 100
    assert batch.cost_price == Decimal("10.00")
    assert batch.selling_price == Decimal("15.00")


# ==================================================
# INITIAL QUANTITY MUST BE GREATER THAN ZERO
# ==================================================

def test_inventory_batch_create_zero_quantity():
    """
    Schema should reject an initial quantity of zero.
    """

    with pytest.raises(ValidationError) as exc:

        InventoryBatchCreate(
            product_id=1,
            supplier_id=1,
            batch_number="BATCH-001",
            initial_quantity=0,
            cost_price=Decimal("10.00"),
            selling_price=Decimal("15.00"),
            expiration_date=None,
            notes="Invalid quantity",
        )

    errors = exc.value.errors()

    assert errors[0]["loc"] == ("initial_quantity",)
    assert errors[0]["type"] == "greater_than"


# ==================================================
# COST PRICE MUST BE POSITIVE
# ==================================================

def test_inventory_batch_create_negative_cost_price():
    """
    Schema should reject a negative cost price.
    """

    with pytest.raises(ValidationError) as exc:

        InventoryBatchCreate(
            product_id=1,
            supplier_id=1,
            batch_number="BATCH-001",
            initial_quantity=50,
            cost_price=Decimal("-1.00"),
            selling_price=Decimal("15.00"),
            expiration_date=None,
            notes="Invalid cost",
        )

    errors = exc.value.errors()

    assert errors[0]["loc"] == ("cost_price",)
    assert errors[0]["type"] == "greater_than"


# ==================================================
# SELLING PRICE MUST BE POSITIVE
# ==================================================

def test_inventory_batch_create_negative_selling_price():
    """
    Schema should reject a negative selling price.
    """

    with pytest.raises(ValidationError) as exc:

        InventoryBatchCreate(
            product_id=1,
            supplier_id=1,
            batch_number="BATCH-001",
            initial_quantity=50,
            cost_price=Decimal("10.00"),
            selling_price=Decimal("-1.00"),
            expiration_date=None,
            notes="Invalid selling price",
        )

    errors = exc.value.errors()

    assert errors[0]["loc"] == ("selling_price",)
    assert errors[0]["type"] == "greater_than"