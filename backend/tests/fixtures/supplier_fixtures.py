import uuid

import pytest

from app.models.core import Supplier


# ==================================================
# SUPPLIER FACTORY
# ==================================================

@pytest.fixture
def supplier_factory(db):
    """
    Factory fixture for creating suppliers.

    Examples:

        supplier = supplier_factory()

        supplier = supplier_factory(
            name="Coca-Cola Cuba",
            email="sales@cocacola.cu",
        )
    """

    def factory(
        name: str | None = None,
        contact_person: str = "John Supplier",
        phone: str = "+53 5555 1234",
        email: str | None = None,
        address: str = "Baracoa, Guantánamo, Cuba",
        is_active: bool = True,
    ) -> Supplier:

        supplier_name = (
            name
            if name is not None
            else f"Supplier_{uuid.uuid4().hex[:8]}"
        )

        supplier_email = (
            email
            if email is not None
            else f"{uuid.uuid4().hex[:8]}@supplier.test"
        )

        supplier = Supplier(
            name=supplier_name,
            contact_person=contact_person,
            phone=phone,
            email=supplier_email,
            address=address,
            is_active=is_active,
        )

        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        return supplier

    return factory


# ==================================================
# DEFAULT SUPPLIER
# ==================================================

@pytest.fixture
def supplier(supplier_factory):
    """
    Creates a default supplier.
    """

    return supplier_factory()