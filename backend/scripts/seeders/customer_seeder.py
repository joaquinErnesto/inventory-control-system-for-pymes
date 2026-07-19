from sqlalchemy.orm import Session

from app.models.core import Customer

from scripts.seeders.utils import (
    already_exists,
    print_created,
    print_exists,
    print_section,
    save,
)


def seed_customers(db: Session) -> None:
    """
    Seed the default customers.

    Safe to execute multiple times.
    """

    print_section("Customers")

    customers = [
        {
            "name": "Juan Pérez",
            "identification_number": "90010100123",
            "phone": "+53 555-2001",
            "email": "juan.perez@example.com",
            "address": "Baracoa, Guantánamo",
        },
        {
            "name": "María Rodríguez",
            "identification_number": "91030500456",
            "phone": "+53 555-2002",
            "email": "maria.rodriguez@example.com",
            "address": "Baracoa, Guantánamo",
        },
        {
            "name": "Carlos Gómez",
            "identification_number": "92041000789",
            "phone": "+53 555-2003",
            "email": "carlos.gomez@example.com",
            "address": "Maisí, Guantánamo",
        },
        {
            "name": "Ana Fernández",
            "identification_number": "93051200321",
            "phone": "+53 555-2004",
            "email": "ana.fernandez@example.com",
            "address": "Imías, Guantánamo",
        },
        {
            "name": "Pedro Martínez",
            "identification_number": "94080100987",
            "phone": "+53 555-2005",
            "email": "pedro.martinez@example.com",
            "address": "San Antonio del Sur, Guantánamo",
        },
        {
            "name": "Laura Díaz",
            "identification_number": "95091500555",
            "phone": "+53 555-2006",
            "email": "laura.diaz@example.com",
            "address": "Baracoa, Guantánamo",
        },
        {
            "name": "Roberto Sánchez",
            "identification_number": "96022000888",
            "phone": "+53 555-2007",
            "email": "roberto.sanchez@example.com",
            "address": "Guantánamo",
        },
        {
            "name": "Elena Morales",
            "identification_number": "97073000111",
            "phone": "+53 555-2008",
            "email": "elena.morales@example.com",
            "address": "Santiago de Cuba",
        },
        {
            "name": "Miguel Castro",
            "identification_number": "98042500666",
            "phone": "+53 555-2009",
            "email": "miguel.castro@example.com",
            "address": "Baracoa, Guantánamo",
        },
        {
            "name": "Sofía Herrera",
            "identification_number": "99011000222",
            "phone": "+53 555-2010",
            "email": "sofia.herrera@example.com",
            "address": "Moa, Holguín",
        },
    ]

    for customer_data in customers:

        if already_exists(
            db,
            Customer,
            identification_number=customer_data["identification_number"],
        ):
            print_exists(
                f"Customer '{customer_data['name']}' already exists."
            )
            continue

        customer = Customer(
            name=customer_data["name"],
            identification_number=customer_data["identification_number"],
            phone=customer_data["phone"],
            email=customer_data["email"],
            address=customer_data["address"],
        )

        save(db, customer)

        print_created(
            f"Customer '{customer.name}' created successfully."
        )