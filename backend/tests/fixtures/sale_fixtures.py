from decimal import Decimal

import pytest

from app.models.core import Sale
from app.schemas.core import (
    PaymentMethod,
    PaymentStatus,
)


# ==================================================
# SALE FACTORY
# ==================================================

@pytest.fixture
def sale_factory(
    db,
    user_factory,
    customer_factory,
):
    """
    Factory fixture for creating sales.

    Examples:

        sale = sale_factory()

        sale = sale_factory(
            payment_method=PaymentMethod.CARD,
        )

        customer = customer_factory()

        sale = sale_factory(
            customer=customer,
        )
    """

    def factory(
        *,
        user=None,
        customer=None,
        total_amount: Decimal = Decimal("100.00"),
        payment_method: PaymentMethod = PaymentMethod.CASH,
        payment_status: PaymentStatus = PaymentStatus.PAID,
    ) -> Sale:

        if user is None:
            user = user_factory()

        if customer is None:
            customer = customer_factory()

        sale = Sale(
            user_id=user.id,
            customer_id=customer.id,
            total_amount=total_amount,
            payment_method=payment_method.value,
            payment_status=payment_status.value,
        )

        db.add(sale)
        db.commit()
        db.refresh(sale)

        return sale

    return factory


# ==================================================
# DEFAULT SALE
# ==================================================

@pytest.fixture
def sale(
    sale_factory,
):
    """
    Creates a default sale.
    """

    return sale_factory()