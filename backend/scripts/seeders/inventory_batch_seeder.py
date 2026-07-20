from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.core import (
    InventoryBatch,
    InventoryTransaction,
    Product,
    Supplier,
    User,
)

from scripts.seeders.utils import (
    print_created,
    print_exists,
    print_section,
    save,
)


def seed_inventory_batches(db: Session) -> None:
    """
    Seed initial inventory batches.

    For every created batch an InventoryTransaction
    of type IN is also created automatically.

    Safe to execute multiple times.
    """

    print_section("Inventory Batches")

    #
    # Lookup tables
    #

    users = {
        user.username.lower(): user
        for user in db.query(User).all()
    }

    suppliers = {
        supplier.name.lower(): supplier
        for supplier in db.query(Supplier).all()
    }

    products = {
        product.sku_or_barcode: product
        for product in db.query(Product).all()
    }

    batches = [

        #
        # Coca-Cola
        #

        {
            "sku": "P000001",
            "supplier": "Coca-Cola Cuba",
            "created_by": "admin_user2",
            "batch_number": "CC-2026-001",
            "initial_quantity": 120,
            "cost_price": Decimal("1.80"),
            "selling_price": Decimal("2.50"),
            "expiration_date": date(2027, 1, 15),
            "notes": "Initial Coca-Cola shipment.",
        },

        #
        # Orange Juice
        #

        {
            "sku": "P000002",
            "supplier": "Nestlé Distribution",
            "created_by": "admin_user2",
            "batch_number": "OJ-2026-001",
            "initial_quantity": 80,
            "cost_price": Decimal("2.30"),
            "selling_price": Decimal("3.10"),
            "expiration_date": date(2026, 11, 30),
            "notes": "Initial orange juice shipment.",
        },

        #
        # Rice
        #

        {
            "sku": "P000003",
            "supplier": "Local Food Distributor",
            "created_by": "admin_user2",
            "batch_number": "RI-2026-001",
            "initial_quantity": 200,
            "cost_price": Decimal("1.15"),
            "selling_price": Decimal("1.85"),
            "expiration_date": date(2028, 6, 1),
            "notes": "Premium white rice.",
        },

        #
        # Black Beans
        #

        {
            "sku": "P000004",
            "supplier": "Local Food Distributor",
            "created_by": "admin_user2",
            "batch_number": "BB-2026-001",
            "initial_quantity": 160,
            "cost_price": Decimal("0.95"),
            "selling_price": Decimal("1.40"),
            "expiration_date": date(2028, 5, 1),
            "notes": "Dry black beans.",
        },

        #
        # Potato Chips
        #

        {
            "sku": "P000005",
            "supplier": "Baracoa Local Logistics",
            "created_by": "admin_user2",
            "batch_number": "PC-2026-001",
            "initial_quantity": 90,
            "cost_price": Decimal("1.10"),
            "selling_price": Decimal("1.75"),
            "expiration_date": date(2027, 4, 15),
            "notes": "Salted potato chips.",
        },

        #
        # Cookies
        #

        {
            "sku": "P000006",
            "supplier": "Baracoa Local Logistics",
            "created_by": "admin_user2",
            "batch_number": "CK-2026-001",
            "initial_quantity": 75,
            "cost_price": Decimal("1.45"),
            "selling_price": Decimal("2.15"),
            "expiration_date": date(2027, 3, 10),
            "notes": "Chocolate cookies.",
        },

        #
        # Dish Soap
        #

        {
            "sku": "P000007",
            "supplier": "Unilever Caribbean",
            "created_by": "admin_user2",
            "batch_number": "DS-2026-001",
            "initial_quantity": 60,
            "cost_price": Decimal("2.00"),
            "selling_price": Decimal("2.95"),
            "expiration_date": None,
            "notes": "Dish soap.",
        },

        #
        # Laundry Detergent
        #

        {
            "sku": "P000008",
            "supplier": "Unilever Caribbean",
            "created_by": "admin_user2",
            "batch_number": "LD-2026-001",
            "initial_quantity": 50,
            "cost_price": Decimal("5.10"),
            "selling_price": Decimal("6.80"),
            "expiration_date": None,
            "notes": "Laundry detergent.",
        },

        #
        # Toothpaste
        #

        {
            "sku": "P000009",
            "supplier": "Unilever Caribbean",
            "created_by": "admin_user2",
            "batch_number": "TP-2026-001",
            "initial_quantity": 85,
            "cost_price": Decimal("1.70"),
            "selling_price": Decimal("2.25"),
            "expiration_date": date(2029, 1, 1),
            "notes": "Mint toothpaste.",
        },

        #
        # Shampoo
        #

        {
            "sku": "P000010",
            "supplier": "Unilever Caribbean",
            "created_by": "admin_user2",
            "batch_number": "SH-2026-001",
            "initial_quantity": 55,
            "cost_price": Decimal("4.20"),
            "selling_price": Decimal("5.40"),
            "expiration_date": date(2029, 6, 1),
            "notes": "Daily shampoo.",
        },

        #
        # Whole Milk
        #

        {
            "sku": "P000011",
            "supplier": "Fresh Dairy Suppliers",
            "created_by": "admin_user2",
            "batch_number": "WM-2026-001",
            "initial_quantity": 100,
            "cost_price": Decimal("2.00"),
            "selling_price": Decimal("2.80"),
            "expiration_date": date(2026, 8, 10),
            "notes": "Fresh whole milk.",
        },

        #
        # Cheese
        #

        {
            "sku": "P000012",
            "supplier": "Fresh Dairy Suppliers",
            "created_by": "admin_user2",
            "batch_number": "CH-2026-001",
            "initial_quantity": 40,
            "cost_price": Decimal("3.80"),
            "selling_price": Decimal("4.95"),
            "expiration_date": date(2026, 9, 1),
            "notes": "Cheddar cheese.",
        },
    ]

    for batch_data in batches:

        existing = (
            db.query(InventoryBatch)
            .filter(
                InventoryBatch.batch_number ==
                batch_data["batch_number"]
            )
            .first()
        )

        if existing:
            print_exists(
                f"Batch '{batch_data['batch_number']}' already exists."
            )
            continue

        product = products[batch_data["sku"]]
        supplier = suppliers[batch_data["supplier"].lower()]
        user = users[batch_data["created_by"].lower()]

        batch = InventoryBatch(
            product_id=product.id,
            supplier_id=supplier.id,
            created_by_user_id=user.id,
            batch_number=batch_data["batch_number"],
            initial_quantity=batch_data["initial_quantity"],
            current_quantity=batch_data["initial_quantity"],
            cost_price=batch_data["cost_price"],
            selling_price=batch_data["selling_price"],
            expiration_date=batch_data["expiration_date"],
            notes=batch_data["notes"],
        )

        save(db, batch)

        transaction = InventoryTransaction(
            product_id=product.id,
            batch_id=batch.id,
            user_id=user.id,
            quantity_changed=batch.initial_quantity,
            transaction_type="IN",
            notes=f"Initial stock intake. Batch: {batch.batch_number}",
        )

        save(db, transaction)

        print_created(
            f"Batch '{batch.batch_number}' created."
        )