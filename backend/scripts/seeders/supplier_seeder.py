from sqlalchemy.orm import Session

from app.models.core import Supplier

from scripts.seeders.utils import (
    already_exists,
    print_created,
    print_exists,
    print_section,
    save,
)


def seed_suppliers(db: Session) -> None:
    """
    Seed the default suppliers.

    Safe to execute multiple times.
    """

    print_section("Suppliers")

    suppliers = [
        {
            "name": "Coca-Cola Cuba",
            "contact_person": "Luis Hernández",
            "phone": "+53 555-1001",
            "email": "sales@cocacola.cu",
            "address": "Havana, Cuba",
        },
        {
            "name": "Nestlé Distribution",
            "contact_person": "Ana Rodríguez",
            "phone": "+53 555-1002",
            "email": "contact@nestle.cu",
            "address": "Santiago de Cuba",
        },
        {
            "name": "Unilever Caribbean",
            "contact_person": "Carlos Pérez",
            "phone": "+53 555-1003",
            "email": "ventas@unilever.cu",
            "address": "Holguín",
        },
        {
            "name": "Local Food Distributor",
            "contact_person": "María Gómez",
            "phone": "+53 555-1004",
            "email": "info@localfood.cu",
            "address": "Baracoa",
        },
        {
            "name": "Fresh Dairy Suppliers",
            "contact_person": "Daniel Morales",
            "phone": "+53 555-1005",
            "email": "sales@freshdairy.cu",
            "address": "Guantánamo",
        },
    ]

    for supplier_data in suppliers:

        if already_exists(
            db,
            Supplier,
            name=supplier_data["name"],
        ):
            print_exists(
                f"Supplier '{supplier_data['name']}' already exists."
            )
            continue

        supplier = Supplier(
            name=supplier_data["name"],
            contact_person=supplier_data["contact_person"],
            phone=supplier_data["phone"],
            email=supplier_data["email"],
            address=supplier_data["address"],
            is_active=True,
        )

        save(db, supplier)

        print_created(
            f"Supplier '{supplier.name}' created successfully."
        )