from sqlalchemy.orm import Session

from app.models.core import Category

from scripts.seeders.utils import (
    already_exists,
    print_created,
    print_exists,
    print_section,
    save,
)


def seed_categories(db: Session) -> None:
    """
    Seed the default product categories.

    Safe to execute multiple times.
    """

    print_section("Categories")

    categories = [
        {
            "name": "Beverages",
            "description": "Soft drinks, juices, bottled water and other beverages.",
        },
        {
            "name": "Food",
            "description": "Packaged and canned food products.",
        },
        {
            "name": "Snacks",
            "description": "Cookies, chips, candies and similar products.",
        },
        {
            "name": "Cleaning",
            "description": "Cleaning and sanitation products.",
        },
        {
            "name": "Personal Care",
            "description": "Personal hygiene and cosmetic products.",
        },
        {
            "name": "Dairy",
            "description": "Milk, cheese, yogurt and dairy products.",
        },
    ]

    for category_data in categories:

        if already_exists(
            db,
            Category,
            name=category_data["name"],
        ):
            print_exists(
                f"Category '{category_data['name']}' already exists."
            )
            continue

        category = Category(
            name=category_data["name"],
            description=category_data["description"],
        )

        save(db, category)

        print_created(
            f"Category '{category.name}' created successfully."
        )