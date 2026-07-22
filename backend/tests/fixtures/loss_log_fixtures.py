from decimal import Decimal

import pytest

from app.models.core import LossLog
from app.schemas.core import LossReason


# ==================================================
# LOSS LOG FACTORY
# ==================================================

@pytest.fixture
def loss_log_factory(
    db,
    inventory_batch_factory,
    user_factory,
):
    """
    Factory fixture for creating inventory loss records.

    Examples:

        loss = loss_log_factory()

        loss = loss_log_factory(
            quantity_lost=15,
        )

        batch = inventory_batch_factory()

        loss = loss_log_factory(
            batch=batch,
            reason=LossReason.EXPIRED,
        )
    """

    def factory(
        *,
        batch=None,
        user=None,
        quantity_lost: int = 5,
        reason: LossReason = LossReason.DAMAGED,
        notes: str = "Test loss log.",
    ) -> LossLog:

        if batch is None:
            batch = inventory_batch_factory()

        if user is None:
            user = user_factory()

        loss = LossLog(
            batch_id=batch.id,
            user_id=user.id,
            quantity_lost=quantity_lost,
            reason=reason.value,
            notes=notes,
        )

        db.add(loss)
        db.commit()
        db.refresh(loss)

        return loss

    return factory


# ==================================================
# DEFAULT LOSS LOG
# ==================================================

@pytest.fixture
def loss_log(loss_log_factory):
    """
    Creates a default inventory loss record.
    """

    return loss_log_factory()