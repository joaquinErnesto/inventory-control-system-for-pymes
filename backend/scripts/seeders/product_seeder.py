from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.core import Category, Product
from app.schemas.core import UnitOfMeasure

from scripts.seeders.utils import (
    already_exists,
    print_created,
    print_exists,
    print_section,
    save,
)


def seed_products(db: Session) -> None:
    """
    Seed the default product catalog.

    Safe to execute multiple times.
    """

    print_section("Products")

    categories = {
        category.name.strip().lower(): category
        for category in db.query(Category).all()
    }

    products = [

        # ==================================================
        # BEVERAGES
        # ==================================================

        {
            "category": "Beverages",
            "name": "Coca-Cola 1.5L",
            "description": "Carbonated soft drink.",
            "sku_or_barcode": "P000001",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("2.50"),
            "min_stock_threshold": 10,
        },

        {
            "category": "Beverages",
            "name": "Orange Juice 1L",
            "description": "Natural orange juice.",
            "sku_or_barcode": "P000002",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("3.10"),
            "min_stock_threshold": 8,
        },

        # ==================================================
        # FOOD
        # ==================================================

        {
            "category": "Food",
            "name": "White Rice 1kg",
            "description": "Premium white rice.",
            "sku_or_barcode": "P000003",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("1.85"),
            "min_stock_threshold": 15,
        },

        {
            "category": "Food",
            "name": "Black Beans 500g",
            "description": "Dry black beans.",
            "sku_or_barcode": "P000004",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("1.40"),
            "min_stock_threshold": 15,
        },

        # ==================================================
        # SNACKS
        # ==================================================

        {
            "category": "Snacks",
            "name": "Potato Chips",
            "description": "Salted potato chips.",
            "sku_or_barcode": "P000005",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("1.75"),
            "min_stock_threshold": 10,
        },

        {
            "category": "Snacks",
            "name": "Chocolate Cookies",
            "description": "Chocolate flavored cookies.",
            "sku_or_barcode": "P000006",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("2.15"),
            "min_stock_threshold": 10,
        },

        # ==================================================
        # CLEANING
        # ==================================================

        {
            "category": "Cleaning",
            "name": "Dish Soap",
            "description": "Liquid dishwashing soap.",
            "sku_or_barcode": "P000007",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("2.95"),
            "min_stock_threshold": 8,
        },

        {
            "category": "Cleaning",
            "name": "Laundry Detergent",
            "description": "Laundry detergent powder.",
            "sku_or_barcode": "P000008",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("6.80"),
            "min_stock_threshold": 5,
        },

        # ==================================================
        # PERSONAL CARE
        # ==================================================

        {
            "category": "Personal Care",
            "name": "Toothpaste",
            "description": "Mint toothpaste.",
            "sku_or_barcode": "P000009",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("2.25"),
            "min_stock_threshold": 8,
        },

        {
            "category": "Personal Care",
            "name": "Shampoo",
            "description": "Daily use shampoo.",
            "sku_or_barcode": "P000010",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("5.40"),
            "min_stock_threshold": 6,
        },

        # ==================================================
        # DAIRY
        # ==================================================

        {
            "category": "Dairy",
            "name": "Whole Milk 1L",
            "description": "Whole milk.",
            "sku_or_barcode": "P000011",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("2.80"),
            "min_stock_threshold": 10,
        },

        {
            "category": "Dairy",
            "name": "Cheddar Cheese",
            "description": "Cheddar cheese block.",
            "sku_or_barcode": "P000012",
            "unit_of_measure": UnitOfMeasure.UNITS.value,
            "base_price": Decimal("4.95"),
            "min_stock_threshold": 5,
        },

    ]

    for product_data in products:

        if already_exists(
            db,
            Product,
            sku_or_barcode=product_data["sku_or_barcode"],
        ):
            print_exists(
                f"Product '{product_data['name']}' already exists."
            )
            continue

        category = categories.get(
            product_data["category"].strip().lower()
        )

        if category is None:
            raise ValueError(
                f"Category '{product_data['category']}' does not exist."
            )

        product = Product(
            category_id=category.id,
            name=product_data["name"],
            description=product_data["description"],
            sku_or_barcode=product_data["sku_or_barcode"],
            unit_of_measure=product_data["unit_of_measure"],
            base_price=product_data["base_price"],
            min_stock_threshold=product_data["min_stock_threshold"],
            is_active=True,
        )

        save(db, product)

        print_created(
            f"Product '{product.name}' created successfully."
        )