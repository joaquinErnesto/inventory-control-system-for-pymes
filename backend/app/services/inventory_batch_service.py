from sqlalchemy.orm import Session

from fastapi import HTTPException

from app.models import core as models
from app.schemas import core as schemas


def receive_inventory_batch(
    db: Session,
    current_user: models.User,
    batch: schemas.InventoryBatchCreate,
) -> models.InventoryBatch:
    """
    Receives inventory for a product and automatically
    creates the corresponding IN inventory transaction.
    """

    #
    # Validate product
    #

    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == batch.product_id
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=400,
            detail=f"Product with ID {batch.product_id} does not exist.",
        )

    #
    # Validate supplier
    #

    if batch.supplier_id is not None:

        supplier = (
            db.query(models.Supplier)
            .filter(
                models.Supplier.id == batch.supplier_id
            )
            .first()
        )

        if not supplier:
            raise HTTPException(
                status_code=400,
                detail=f"Supplier with ID {batch.supplier_id} does not exist.",
            )

    #
    # Business rules
    #

    if batch.initial_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Initial quantity must be greater than zero.",
        )

    if batch.cost_price < 0:
        raise HTTPException(
            status_code=400,
            detail="Cost price cannot be negative.",
        )

    if batch.selling_price < 0:
        raise HTTPException(
            status_code=400,
            detail="Selling price cannot be negative.",
        )

    batch_data = batch.model_dump()

    batch_data["current_quantity"] = batch.initial_quantity
    batch_data["created_by_user_id"] = current_user.id

    new_batch = models.InventoryBatch(
        **batch_data
    )

    db.add(new_batch)

    db.flush()

    transaction = models.InventoryTransaction(
        product_id=new_batch.product_id,
        batch_id=new_batch.id,
        user_id=current_user.id,
        quantity_changed=new_batch.initial_quantity,
        transaction_type=schemas.TransactionType.IN.value,
        notes=(
            f"Initial stock intake. "
            f"Batch: {new_batch.batch_number or 'N/A'}"
        ),
    )

    db.add(transaction)

    db.commit()

    db.refresh(new_batch)

    return new_batch