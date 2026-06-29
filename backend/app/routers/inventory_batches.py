from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas

router = APIRouter(
    prefix="/batches",
    tags=["Inventory Batches"]
)

@router.post("/", response_model=schemas.InventoryBatchResponse, status_code=status.HTTP_201_CREATED)
def receive_stock_batch(batch: schemas.InventoryBatchCreate, db: Session = Depends(get_db)):
    """
    Receive new physical stock into the warehouse.
    """
    # 1. Validate that the Product actually exists
    product = db.query(models.Product).filter(models.Product.id == batch.product_id).first()
    if not product:
        raise HTTPException(status_code=400, detail=f"Product with ID {batch.product_id} does not exist.")

    # 2. Validate that the User receiving the stock exists
    user = db.query(models.User).filter(models.User.id == batch.created_by_user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail=f"User with ID {batch.created_by_user_id} does not exist.")

    # 3. Validate that the Supplier exists (if a supplier ID was provided)
    if batch.supplier_id:
        supplier = db.query(models.Supplier).filter(models.Supplier.id == batch.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=400, detail=f"Supplier with ID {batch.supplier_id} does not exist.")

    # 4. Enforce strict quantity and pricing rules
    if batch.initial_quantity <= 0:
        raise HTTPException(status_code=400, detail="Initial quantity must be greater than zero.")
    if batch.cost_price < 0 or batch.selling_price < 0:
        raise HTTPException(status_code=400, detail="Prices cannot be negative.")

    # 5. Convert to dictionary and inject the current_quantity
    batch_data = batch.model_dump()
    batch_data["current_quantity"] = batch.initial_quantity # Fresh stock means current = initial

    # 6. Save to database
    new_batch = models.InventoryBatch(**batch_data)
    db.add(new_batch)
    db.flush()
    
    initial_transaction = models.InventoryBatch(
        product_id = new_batch.product_id,
        batch_id = new_batch.id,
        user_id = new_batch.created_by_user_id,
        quantity_changed = new_batch.initial_quantity,
        transaction_type = schemas.TransactionType.IN.value,
        notes=f"Initial stock intake. Batch reference: {new_batch.batch_number or 'N/A'}"    
    )
    db.add(initial_transaction)
    
    db.commit()
    db.refresh(new_batch)
    
    return new_batch

@router.get("/", response_model=List[schemas.InventoryBatchResponse])
def get_all_batches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all received inventory batches.
    """
    batches = db.query(models.InventoryBatch).offset(skip).limit(limit).all()
    return batches