from sqlalchemy.orm import Session

from app.models.core import (
    InventoryBatch,
    LossLog,
    User,
)

from app.schemas.core import (
    LossLogCreate,
    LossReason,
)

from app.services.loss_logs_service import register_loss

from scripts.seeders.utils import (
    print_created,
    print_exists,
    print_section,
)


def seed_loss_logs(db: Session) -> None:
    """
    Seed inventory loss records.

    Safe to execute multiple times.
    """

    print_section("Loss Logs")

    users = {
        user.username.lower(): user
        for user in db.query(User).all()
    }

    batches = {
        batch.batch_number: batch
        for batch in db.query(InventoryBatch).all()
    }

    losses = [

        {
            "batch_number": "CC-2026-001",
            "username": "admin_user2",
            "quantity_lost": 3,
            "reason": LossReason.DAMAGED,
            "notes": "Three bottles damaged during transport.",
        },

        {
            "batch_number": "OJ-2026-001",
            "username": "admin_user2",
            "quantity_lost": 2,
            "reason": LossReason.EXPIRED,
            "notes": "Expired during inventory inspection.",
        },

        {
            "batch_number": "TP-2026-001",
            "username": "admin_user2",
            "quantity_lost": 1,
            "reason": LossReason.DAMAGED,
            "notes": "Package damaged.",
        },

        {
            "batch_number": "WM-2026-001",
            "username": "admin_user2",
            "quantity_lost": 5,
            "reason": LossReason.EXPIRED,
            "notes": "Milk expired before sale.",
        },

    ]

    for loss_data in losses:

        batch = batches[loss_data["batch_number"]]
        user = users[loss_data["username"].lower()]

        existing = (
            db.query(LossLog)
            .filter(
                LossLog.batch_id == batch.id,
                LossLog.user_id == user.id,
                LossLog.quantity_lost == loss_data["quantity_lost"],
                LossLog.reason == loss_data["reason"].value,
            )
            .first()
        )

        if existing:
            print_exists(
                f"Loss for batch '{batch.batch_number}' already exists."
            )
            continue

        register_loss(
            db=db,
            current_user=user,
            loss=LossLogCreate(
                batch_id=batch.id,
                quantity_lost=loss_data["quantity_lost"],
                reason=loss_data["reason"],
                notes=loss_data["notes"],
            ),
        )

        print_created(
            f"Loss registered for batch '{batch.batch_number}'."
        )