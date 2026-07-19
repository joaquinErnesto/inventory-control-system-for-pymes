"""
Database Seeder

Usage
-----
python scripts/seed_database.py

This script populates the development database with sample data.

It is safe to execute multiple times because each seeder is responsible for preventing duplicate records.
"""

from app.database import SessionLocal

from scripts.seeders.user_seeder import seed_users
from scripts.seeders.category_seeder import seed_categories
from scripts.seeders.supplier_seeder import seed_suppliers


def seed_database() -> None:
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Inventory Control System")
        print("Development Database Seeder")
        print("=" * 60)
        print()

        #
        # Future seeders
        #
        seed_users(db)
        seed_categories(db)
        seed_suppliers(db)
        # seed_customers(db)
        # seed_products(db)
        # seed_inventory_batches(db)
        # seed_sales(db)
        # seed_loss_logs(db)
        # seed_inventory_transactions(db)

        print()
        print("=" * 60)
        print("Database seeding completed successfully.")
        print("=" * 60)

    except Exception as exc:
        db.rollback()
        print()
        print("=" * 60)
        print("Database seeding failed.")
        print(exc)
        print("=" * 60)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()