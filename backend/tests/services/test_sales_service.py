import pytest

from fastapi import HTTPException

from decimal import Decimal

from app.models.core import (
    Sale,
    SaleItem,
    InventoryTransaction,
)

from app.schemas.core import (
    SaleCreate,
    SaleItemCreate,
    PaymentMethod,
    PaymentStatus,
    TransactionType,
    InventoryBatchCreate
)

from app.services.sales_service import create_sale
from app.services.inventory_batch_service import receive_inventory_batch


# ==================================================
# CREATE SALE SUCCESS
# ==================================================

def test_create_sale_success(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should successfully create a sale.
    """

    #
    # Arrange
    #

    employee = user_factory(role="employee")

    product = product_factory()

    supplier = supplier_factory()

    from app.services.inventory_batch_service import (
        receive_inventory_batch,
    )

    from app.schemas.core import InventoryBatchCreate

    receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SALE-001",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
        ),
    )

    sale_request = SaleCreate(
        customer_id=None,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        items=[
            SaleItemCreate(
                product_id=product.id,
                quantity_sold=5,
                unit_price=Decimal("10.00"),
            )
        ],
    )

    #
    # Act
    #

    sale = create_sale(
        db=db,
        sale_request=sale_request,
        current_user=employee,
    )

    #
    # Assert
    #

    assert sale.id is not None
    assert sale.user_id == employee.id
    assert sale.total_amount == Decimal("50.00")


# ==================================================
# CREATE SALE CREATES SALE ITEMS
# ==================================================

def test_create_sale_creates_sale_items(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should automatically create SaleItem records.
    """

    employee = user_factory(role="employee")

    product = product_factory()

    supplier = supplier_factory()

    from app.services.inventory_batch_service import (
        receive_inventory_batch,
    )

    from app.schemas.core import InventoryBatchCreate

    receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SALE-002",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
        ),
    )

    sale_request = SaleCreate(
        customer_id=None,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        items=[
            SaleItemCreate(
                product_id=product.id,
                quantity_sold=7,
                unit_price=Decimal("10.00"),
            )
        ],
    )

    sale = create_sale(
        db=db,
        sale_request=sale_request,
        current_user=employee,
    )

    items = (
        db.query(SaleItem)
        .filter(SaleItem.sale_id == sale.id)
        .all()
    )

    assert len(items) == 1

    assert items[0].quantity_sold == 7

    assert items[0].product_id == product.id


# ==================================================
# CREATE SALE CREATES OUT TRANSACTION
# ==================================================

def test_create_sale_creates_inventory_transaction(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should automatically register an OUT inventory transaction.
    """

    employee = user_factory(role="employee")

    product = product_factory()

    supplier = supplier_factory()

    from app.services.inventory_batch_service import (
        receive_inventory_batch,
    )

    from app.schemas.core import InventoryBatchCreate

    batch = receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SALE-003",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
        ),
    )

    sale_request = SaleCreate(
        customer_id=None,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        items=[
            SaleItemCreate(
                product_id=product.id,
                quantity_sold=8,
                unit_price=Decimal("10.00"),
            )
        ],
    )

    sale = create_sale(
        db=db,
        sale_request=sale_request,
        current_user=employee,
    )

    transaction = (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.sale_id == sale.id
        )
        .first()
    )

    assert transaction is not None

    assert transaction.transaction_type == TransactionType.OUT.value

    assert transaction.quantity_changed == -8

    assert transaction.batch_id == batch.id


# ==================================================
# CREATE SALE DECREASES STOCK
# ==================================================

def test_create_sale_decreases_inventory(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should deduct inventory from the selected batch.
    """

    employee = user_factory(role="employee")

    product = product_factory()

    supplier = supplier_factory()

    from app.services.inventory_batch_service import (
        receive_inventory_batch,
    )

    from app.schemas.core import InventoryBatchCreate

    batch = receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SALE-004",
            initial_quantity=100,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
        ),
    )

    sale_request = SaleCreate(
        customer_id=None,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        items=[
            SaleItemCreate(
                product_id=product.id,
                quantity_sold=15,
                unit_price=Decimal("10.00"),
            )
        ],
    )

    create_sale(
        db=db,
        sale_request=sale_request,
        current_user=employee,
    )

    db.refresh(batch)

    assert batch.current_quantity == 85


# ==================================================
# CREATE SALE INVALID CUSTOMER
# ==================================================

def test_create_sale_invalid_customer(
    db,
    user_factory,
):
    """
    Should reject a sale when the customer does not exist.
    """

    employee = user_factory(role="employee")

    sale_request = SaleCreate(
        customer_id=999999,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        items=[],
    )

    with pytest.raises(HTTPException) as exc:

        create_sale(
            db=db,
            sale_request=sale_request,
            current_user=employee,
        )

    assert exc.value.status_code == 400

    assert exc.value.detail == "Invalid customer_id."


# ==================================================
# CREATE SALE INSUFFICIENT STOCK
# ==================================================

def test_create_sale_insufficient_stock(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should reject a sale when there is not enough stock.
    """

    employee = user_factory(role="employee")

    product = product_factory()

    supplier = supplier_factory()

    from app.services.inventory_batch_service import (
        receive_inventory_batch,
    )

    from app.schemas.core import InventoryBatchCreate

    receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="LOW-STOCK",
            initial_quantity=10,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
        ),
    )

    sale_request = SaleCreate(
        customer_id=None,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        items=[
            SaleItemCreate(
                product_id=product.id,
                quantity_sold=25,
                unit_price=Decimal("10.00"),
            )
        ],
    )

    with pytest.raises(HTTPException) as exc:

        create_sale(
            db=db,
            sale_request=sale_request,
            current_user=employee,
        )

    assert exc.value.status_code == 400

    assert "Insufficient total stock" in exc.value.detail


# ==================================================
# CREATE SALE USES FEFO
# ==================================================

def test_create_sale_uses_fefo(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should deduct inventory from the batch with the
    earliest expiration date.
    """

    from datetime import date

    from app.services.inventory_batch_service import (
        receive_inventory_batch,
    )

    employee = user_factory(role="employee")

    product = product_factory()

    supplier = supplier_factory()

    batch1 = receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="LATE",
            initial_quantity=20,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
            expiration_date=date(2027, 12, 31),
        ),
    )

    batch2 = receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="EARLY",
            initial_quantity=20,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
            expiration_date=date(2026, 6, 1),
        ),
    )

    sale_request = SaleCreate(
        customer_id=None,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        items=[
            SaleItemCreate(
                product_id=product.id,
                quantity_sold=5,
                unit_price=Decimal("10.00"),
            )
        ],
    )

    create_sale(
        db=db,
        sale_request=sale_request,
        current_user=employee,
    )

    db.refresh(batch1)
    db.refresh(batch2)

    assert batch2.current_quantity == 15
    assert batch1.current_quantity == 20


# ==================================================
# CREATE SALE USES FIFO WHEN EXPIRATION IS EQUAL
# ==================================================

def test_create_sale_uses_fifo_when_expiration_is_equal(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should use FIFO when expiration dates are equal.
    """

    from datetime import date
    from time import sleep

    from app.services.inventory_batch_service import (
        receive_inventory_batch,
    )

    employee = user_factory(role="employee")

    product = product_factory()

    supplier = supplier_factory()

    expiration = date(2027, 12, 31)

    batch1 = receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="FIRST",
            initial_quantity=20,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
            expiration_date=expiration,
        ),
    )

    # Ensure received_date is later
    sleep(1)

    batch2 = receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="SECOND",
            initial_quantity=20,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
            expiration_date=expiration,
        ),
    )

    sale_request = SaleCreate(
        customer_id=None,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        items=[
            SaleItemCreate(
                product_id=product.id,
                quantity_sold=5,
                unit_price=Decimal("10.00"),
            )
        ],
    )

    create_sale(
        db=db,
        sale_request=sale_request,
        current_user=employee,
    )

    db.refresh(batch1)
    db.refresh(batch2)

    assert batch1.current_quantity == 15
    assert batch2.current_quantity == 20
    
    
# ==================================================
# CREATE SALE SPLITS BETWEEN MULTIPLE BATCHES
# ==================================================

def test_create_sale_splits_between_multiple_batches(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should continue deducting inventory from the
    next batch when the first one is exhausted.
    """

    from datetime import date

    from app.services.inventory_batch_service import (
        receive_inventory_batch,
    )

    employee = user_factory(role="employee")

    product = product_factory()

    supplier = supplier_factory()

    batch1 = receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="B1",
            initial_quantity=10,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
            expiration_date=date(2026, 1, 1),
        ),
    )

    batch2 = receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="B2",
            initial_quantity=20,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
            expiration_date=date(2026, 6, 1),
        ),
    )

    sale_request = SaleCreate(
        customer_id=None,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        items=[
            SaleItemCreate(
                product_id=product.id,
                quantity_sold=15,
                unit_price=Decimal("10.00"),
            )
        ],
    )

    sale = create_sale(
        db=db,
        sale_request=sale_request,
        current_user=employee,
    )

    db.refresh(batch1)
    db.refresh(batch2)

    assert batch1.current_quantity == 0
    assert batch2.current_quantity == 15

    sale_items = (
        db.query(SaleItem)
        .filter(SaleItem.sale_id == sale.id)
        .all()
    )

    assert len(sale_items) == 2

    quantities = sorted(
        item.quantity_sold
        for item in sale_items
    )

    assert quantities == [5, 10]
    

# ==================================================
# CREATE SALE SKIPS EMPTY BATCHES
# ==================================================

def test_create_sale_skips_empty_batches(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should ignore batches whose stock is already zero.
    """

    from datetime import date

    from app.services.inventory_batch_service import (
        receive_inventory_batch,
    )

    employee = user_factory(role="employee")

    product = product_factory()

    supplier = supplier_factory()

    empty_batch = receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="EMPTY",
            initial_quantity=10,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
            expiration_date=date(2026, 1, 1),
        ),
    )

    empty_batch.current_quantity = 0

    db.commit()

    usable_batch = receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="GOOD",
            initial_quantity=20,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
            expiration_date=date(2026, 6, 1),
        ),
    )

    sale_request = SaleCreate(
        customer_id=None,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        items=[
            SaleItemCreate(
                product_id=product.id,
                quantity_sold=5,
                unit_price=Decimal("10.00"),
            )
        ],
    )

    create_sale(
        db=db,
        sale_request=sale_request,
        current_user=employee,
    )

    db.refresh(empty_batch)
    db.refresh(usable_batch)

    assert empty_batch.current_quantity == 0
    assert usable_batch.current_quantity == 15
    

# ==================================================
# CREATE SALE ROLLS BACK ON FAILURE
# ==================================================

def test_create_sale_rolls_back_on_failure(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    If the sale fails, no Sale, SaleItem or
    InventoryTransaction should remain in the database.
    """

    from app.services.inventory_batch_service import (
        receive_inventory_batch,
    )

    employee = user_factory(role="employee")

    product = product_factory()

    supplier = supplier_factory()

    batch = receive_inventory_batch(
        db=db,
        current_user=employee,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="ROLLBACK",
            initial_quantity=10,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("10.00"),
        ),
    )

    sale_request = SaleCreate(
        customer_id=None,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        items=[
            SaleItemCreate(
                product_id=product.id,
                quantity_sold=999,
                unit_price=Decimal("10.00"),
            )
        ],
    )

    with pytest.raises(HTTPException):

        create_sale(
            db=db,
            sale_request=sale_request,
            current_user=employee,
        )

    # Nothing should have been created

    assert db.query(Sale).count() == 0

    assert db.query(SaleItem).count() == 0

    assert db.query(InventoryTransaction).count() == 1

    db.refresh(batch)

    assert batch.current_quantity == 10
    

# ==================================================
# CREATE SALE WITH MULTIPLE PRODUCTS
# ==================================================

def test_create_sale_multiple_products(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should process a sale containing multiple different
    products.
    """

    admin = user_factory(role="admin")

    supplier = supplier_factory()

    product_a = product_factory()

    product_b = product_factory()

    product_c = product_factory()

    receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product_a.id,
            supplier_id=supplier.id,
            batch_number="A-001",
            initial_quantity=20,
            cost_price=Decimal("4.00"),
            selling_price=Decimal("6.00"),
        ),
    )

    receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product_b.id,
            supplier_id=supplier.id,
            batch_number="B-001",
            initial_quantity=20,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
        ),
    )

    receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product_c.id,
            supplier_id=supplier.id,
            batch_number="C-001",
            initial_quantity=20,
            cost_price=Decimal("2.00"),
            selling_price=Decimal("3.00"),
        ),
    )

    sale = create_sale(
        db=db,
        current_user=admin,
        sale_request=SaleCreate(
            payment_method=PaymentMethod.CASH,
            payment_status=PaymentStatus.PAID,
            items=[
                SaleItemCreate(
                    product_id=product_a.id,
                    quantity_sold=2,
                    unit_price=Decimal("6.00"),
                ),
                SaleItemCreate(
                    product_id=product_b.id,
                    quantity_sold=5,
                    unit_price=Decimal("8.00"),
                ),
                SaleItemCreate(
                    product_id=product_c.id,
                    quantity_sold=1,
                    unit_price=Decimal("3.00"),
                ),
            ],
        ),
    )

    assert sale.total_amount == Decimal("55.00")

    assert (
        db.query(SaleItem)
        .filter(SaleItem.sale_id == sale.id)
        .count()
        == 3
    )

    assert (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.sale_id == sale.id,
            InventoryTransaction.transaction_type == TransactionType.OUT.value,
        )
        .count()
        == 3
    )


# ==================================================
# CREATE SALE USING MULTIPLE BATCHES (FEFO)
# ==================================================

def test_create_sale_uses_multiple_batches_fefo(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should automatically consume multiple inventory
    batches following the FEFO strategy.
    """

    from datetime import date

    admin = user_factory(role="admin")

    supplier = supplier_factory()

    product = product_factory()

    # First batch (expires first)
    first_batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="FEFO-001",
            initial_quantity=4,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
            expiration_date=date(2026, 1, 1),
        ),
    )

    # Second batch
    second_batch = receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product.id,
            supplier_id=supplier.id,
            batch_number="FEFO-002",
            initial_quantity=8,
            cost_price=Decimal("5.00"),
            selling_price=Decimal("8.00"),
            expiration_date=date(2026, 6, 1),
        ),
    )

    sale = create_sale(
        db=db,
        current_user=admin,
        sale_request=SaleCreate(
            payment_method=PaymentMethod.CASH,
            payment_status=PaymentStatus.PAID,
            items=[
                SaleItemCreate(
                    product_id=product.id,
                    quantity_sold=10,
                    unit_price=Decimal("8.00"),
                )
            ],
        ),
    )

    db.refresh(first_batch)
    db.refresh(second_batch)

    # First batch should be emptied first
    assert first_batch.current_quantity == 0

    # Remaining quantity comes from second batch
    assert second_batch.current_quantity == 2

    sale_items = (
        db.query(SaleItem)
        .filter(SaleItem.sale_id == sale.id)
        .order_by(SaleItem.id)
        .all()
    )

    assert len(sale_items) == 2

    assert sale_items[0].batch_id == first_batch.id
    assert sale_items[0].quantity_sold == 4

    assert sale_items[1].batch_id == second_batch.id
    assert sale_items[1].quantity_sold == 6

    transactions = (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.sale_id == sale.id,
            InventoryTransaction.transaction_type == TransactionType.OUT.value,
        )
        .order_by(InventoryTransaction.id)
        .all()
    )

    assert len(transactions) == 2

    assert transactions[0].batch_id == first_batch.id
    assert transactions[0].quantity_changed == -4

    assert transactions[1].batch_id == second_batch.id
    assert transactions[1].quantity_changed == -6

    assert sale.total_amount == Decimal("80.00")
    

# ==================================================
# CREATE SALE - DECIMAL TOTAL CALCULATION
# ==================================================

def test_create_sale_decimal_total(
    db,
    user_factory,
    product_factory,
    supplier_factory,
):
    """
    Should calculate the total amount correctly
    using Decimal arithmetic.
    """

    from decimal import Decimal

    admin = user_factory(role="admin")

    supplier = supplier_factory()

    product_a = product_factory()

    product_b = product_factory()

    receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product_a.id,
            supplier_id=supplier.id,
            batch_number="DEC-A",
            initial_quantity=20,
            cost_price=Decimal("2.00"),
            selling_price=Decimal("2.99"),
        ),
    )

    receive_inventory_batch(
        db=db,
        current_user=admin,
        batch=InventoryBatchCreate(
            product_id=product_b.id,
            supplier_id=supplier.id,
            batch_number="DEC-B",
            initial_quantity=20,
            cost_price=Decimal("1.00"),
            selling_price=Decimal("1.25"),
        ),
    )

    sale = create_sale(
        db=db,
        current_user=admin,
        sale_request=SaleCreate(
            customer_id=None,
            payment_method=PaymentMethod.CASH,
            payment_status=PaymentStatus.PAID,
            items=[
                SaleItemCreate(
                    product_id=product_a.id,
                    quantity_sold=3,
                    unit_price=Decimal("2.99"),
                ),
                SaleItemCreate(
                    product_id=product_b.id,
                    quantity_sold=4,
                    unit_price=Decimal("1.25"),
                ),
            ],
        ),
    )

    expected_total = (
        Decimal("2.99") * 3
        + Decimal("1.25") * 4
    )

    assert sale.total_amount == expected_total