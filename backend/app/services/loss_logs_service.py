from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.models import core as models
from app.schemas import core as schemas

from app.logging.logger import logger


def register_loss(
    db: Session,
    current_user: models.User,
    loss: schemas.LossLogCreate,
) -> models.LossLog:
    # 1. Fetch the batch
    batch = (
        db.query(models.InventoryBatch)
        .filter(models.InventoryBatch.id == loss.batch_id)
        .with_for_update()
        .first()
    )
    
    if not batch:
        raise HTTPException(
            status_code=404, 
            detail="Batch not found."
        )
    
    if not batch.product.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot register losses for an inactive product."
        )
        
    # 2. Check stock
    if loss.quantity_lost <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity lost must be greater than zero."
        )
        
    if batch.current_quantity < loss.quantity_lost:
        raise HTTPException(status_code=400, detail="Insufficient stock to log this loss.")

    # 3. Deduct stock
    batch.current_quantity -= loss.quantity_lost

    # 4. Create Loss Record
    new_loss = models.LossLog(
        **loss.model_dump(),
        user_id = current_user.id
    )
    db.add(new_loss)
    db.flush() # Flush to get new_loss.id

    # 5. Add Transaction Ledger Entry
    transaction = models.InventoryTransaction(
        product_id=batch.product_id,
        batch_id=batch.id,
        user_id=current_user.id,
        quantity_changed=-(loss.quantity_lost),
        transaction_type=schemas.TransactionType.LOSS.value,
        loss_id=new_loss.id,
        notes=f"Loss Logged: {loss.reason.value}"
    )
    db.add(transaction)
    
    # 6. Check for Low Stock Alert (The logic we discussed!)
    if batch.current_quantity <= batch.product.min_stock_threshold:
        # In a real app, you might trigger an email here.
        # For now, we will print a message to the logs as a placeholder.
        logger.warning(
            f"LOW STOCK ALERT | "
            f"Product='{batch.product.name}' | "
            f"Product ID={batch.product_id} | "
            f"Current Stock={batch.current_quantity} | "
            f"Minimum={batch.product.min_stock_threshold}"
        )

    db.commit()
    db.refresh(new_loss)
    
    logger.info(
        f"Loss registered | "
        f"Loss ID={new_loss.id} | "
        f"Product ID={batch.product_id} | "
        f"Batch ID={batch.id} | "
        f"Quantity={loss.quantity_lost} | "
        f"User ID={current_user.id}"
    )
    
    return new_loss