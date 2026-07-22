import uuid

import pytest

from app.models.core import Customer


# ==================================================
# CUSTOMER FACTORY
# ==================================================

@pytest.fixture
def customer_factory(db):
    """
    Factory fixture for creating customers.

    Examples:

        customer = customer_factory()

        customer = customer_factory(
            name="John Doe",
            identification_number="12345678901",
        )
    """

    def factory(
        name: str = "Test Customer",
        identification_number: str | None = None,
        phone: str = "+53 5555 1234",
        email: str | None = None,
        address: str = "Baracoa, Guantánamo, Cuba",
    ) -> Customer:

        customer_identification = (
            identification_number
            if identification_number is not None
            else uuid.uuid4().hex[:12]
        )

        customer_email = (
            email
            if email is not None
            else f"{uuid.uuid4().hex[:8]}@customer.test"
        )

        customer = Customer(
            name=name,
            identification_number=customer_identification,
            phone=phone,
            email=customer_email,
            address=address,
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        return customer

    return factory


# ==================================================
# DEFAULT CUSTOMER
# ==================================================

@pytest.fixture
def customer(customer_factory):
    """
    Creates a default customer.
    """

    return customer_factory()