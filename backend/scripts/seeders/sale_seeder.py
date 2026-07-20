from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.core import Customer, Product, User
from app.schemas.core import (
    PaymentMethod,
    PaymentStatus,
    SaleCreate,
    SaleItemCreate,
)

from app.services.sales_service import create_sale

from scripts.seeders.utils import (
    get_one,
    print_created,
    print_exists,
    print_section,
)

def seed_sales(db: Session) -> None:
    """
    Seed sample sales.

    This seeder intentionally uses the sales service
    instead of inserting directly into the database.

    That guarantees that:

    - FEFO/FIFO is executed
    - Stock is deducted
    - SaleItems are created
    - Inventory Transactions are created
    - Totals are calculated

    Seed sample sales using the application's business logic.

    This seeder is intended for development and testing.

    Unlike master-data seeders (users, categories, suppliers, etc.),
    this seeder creates transactional data and should normally be run
    only on a fresh development database.
    """

    print_section("Sales")
    
    # Get Admin and Employee whom will execute the sale
    admin = get_one(
        db,
        User,
        username="admin_user2",
    )

    employee = get_one(
        db,
        User,
        username="employee2",
    )
    
    # Get the Customers
    alice = get_one(
        db,
        Customer,
        name="Alice Johnson",
    )

    george = get_one(
        db,
        Customer,
        name="George Thompson",
    )

    julia = get_one(
        db,
        Customer,
        name="Julia Roberts",
    )
    
    # Get the Products the Customers gotta buy
    coke = get_one(
        db,
        Product,
        sku_or_barcode="P000001",
    )

    juice = get_one(
        db,
        Product,
        sku_or_barcode="P000002",
    )

    rice = get_one(
        db,
        Product,
        sku_or_barcode="P000003",
    )

    cookies = get_one(
        db,
        Product,
        sku_or_barcode="P000006",
    )
    
    # Sale dictionary with all the data to record in the database
    sales = [

        {
            "user": admin,
            "sale": SaleCreate(
                customer_id=alice.id,
                payment_method=PaymentMethod.CASH,
                payment_status=PaymentStatus.PAID,
                items=[
                    SaleItemCreate(
                        product_id=coke.id,
                        quantity_sold=3,
                        unit_price=Decimal("2.50"),
                    ),
                    SaleItemCreate(
                        product_id=juice.id,
                        quantity_sold=2,
                        unit_price=Decimal("3.10"),
                    ),
                ],
            ),
        },

        {
            "user": employee,
            "sale": SaleCreate(
                customer_id=george.id,
                payment_method=PaymentMethod.CARD,
                payment_status=PaymentStatus.PAID,
                items=[
                    SaleItemCreate(
                        product_id=rice.id,
                        quantity_sold=5,
                        unit_price=Decimal("1.85"),
                    ),
                    SaleItemCreate(
                        product_id=cookies.id,
                        quantity_sold=2,
                        unit_price=Decimal("2.15"),
                    ),
                ],
            ),
        },

        {
            "user": admin,
            "sale": SaleCreate(
                customer_id=julia.id,
                payment_method=PaymentMethod.TRANSFER,
                payment_status=PaymentStatus.PAID,
                items=[
                    SaleItemCreate(
                        product_id=coke.id,
                        quantity_sold=4,
                        unit_price=Decimal("2.50"),
                    ),
                ],
            ),
        },
    ]
    
    # Looping the Sale dictionary to make the records
    for record in sales:

        sale = create_sale(
            db=db,
            sale_request=record["sale"],
            current_user=record["user"],
        )

        print_created(
            f"Sale #{sale.id} created successfully."
        )