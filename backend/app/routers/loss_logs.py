from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas

router = APIRouter(
    prefix="/losses",
    tags=["Loss Logs"]
)

@router.post("/", response_model=schemas.LossLogResponse, status_code=status.HTTP_201_CREATED)
def log_loss(loss: schemas.LossLogCreate, db: Session = Depends(get_db)):
    # 1. Fetch the batch
    batch = db.query(models.InventoryBatch).filter(models.InventoryBatch.id == loss.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found.")

    # 2. Check stock
    if batch.current_quantity < loss.quantity_lost:
        raise HTTPException(status_code=400, detail="Insufficient stock to log this loss.")

    # 3. Deduct stock
    batch.current_quantity -= loss.quantity_lost

    # 4. Create Loss Record
    new_loss = models.LossLog(**loss.model_dump())
    db.add(new_loss)
    db.flush() # Flush to get new_loss.id

    # 5. Add Transaction Ledger Entry
    transaction = models.InventoryTransaction(
        product_id=batch.product_id,
        batch_id=batch.id,
        user_id=loss.user_id,
        quantity_changed=-(loss.quantity_lost),
        transaction_type=schemas.TransactionType.LOSS.value,
        loss_id=new_loss.id,
        notes=f"Loss Logged: {loss.reason}"
    )
    db.add(transaction)
    
    # 6. Check for Low Stock Alert (The logic we discussed!)
    if batch.current_quantity <= batch.product.min_stock_threshold:
        # In a real app, you might trigger an email here.
        # For now, we will print a message to the logs as a placeholder.
        print(f"ALERT: Product {batch.product.name} (ID: {batch.product_id}) is below minimum threshold!")

    db.commit()
    db.refresh(new_loss)
    return new_loss