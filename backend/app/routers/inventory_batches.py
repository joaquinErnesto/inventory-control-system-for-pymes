from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.security import (
    get_current_user,
    get_current_admin,
)
from app.utils.query_sorting import apply_sorting

router = APIRouter(
    prefix="/batches",
    tags=["Inventory Batches"]
)


# ==================================================
# CREATE INVENTORY BATCH
# ==================================================

@router.post(
    "/",
    response_model=schemas.InventoryBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def receive_stock_batch(
    batch: schemas.InventoryBatchCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """
    Receive a new inventory batch.
    Only administrators may receive stock.
    """

    # Validate product
    product = (
        db.query(models.Product)
        .filter(models.Product.id == batch.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=400,
            detail=f"Product with ID {batch.product_id} does not exist.",
        )

    # Validate supplier
    if batch.supplier_id is not None:

        supplier = (
            db.query(models.Supplier)
            .filter(models.Supplier.id == batch.supplier_id)
            .first()
        )

        if not supplier:
            raise HTTPException(
                status_code=400,
                detail=f"Supplier with ID {batch.supplier_id} does not exist.",
            )

    # Business rules

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

    new_batch = models.InventoryBatch(**batch_data)

    db.add(new_batch)

    db.flush()

    transaction = models.InventoryTransaction(
        product_id=new_batch.product_id,
        batch_id=new_batch.id,
        user_id=current_user.id,
        quantity_changed=new_batch.initial_quantity,
        transaction_type=schemas.TransactionType.IN.value,
        notes=f"Initial stock intake. Batch: {new_batch.batch_number or 'N/A'}",
    )

    db.add(transaction)

    db.commit()

    db.refresh(new_batch)

    return new_batch


# ==================================================
# GET ALL INVENTORY BATCHES
# ==================================================

@router.get(
    "/",
    response_model=List[schemas.InventoryBatchResponse],
)
def get_all_batches(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    sort: str = "recieved_date",
    order: str = "desc"
):
    """
    Retrieve all inventory batches.
    """
    
    allowed_sort_fields = {
        "received_date": models.InventoryBatch.received_date,
        "expiration_date": models.InventoryBatch.expiration_date,
        "current_quantity": models.InventoryBatch.current_quantity,
        "cost_price": models.InventoryBatch.cost_price,
        "selling_price": models.InventoryBatch.selling_price,
    }

    query = db.query(models.InventoryBatch)
    
    query = apply_sorting(
        query=query,
        sort=sort,
        order=order,
        allowed_fields=allowed_sort_fields,
    )
    
    batches = (
        db.query(models.InventoryBatch)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return batches


# ==================================================
# GET INVENTORY BATCH BY ID
# ==================================================

@router.get(
    "/{batch_id}",
    response_model=schemas.InventoryBatchResponse,
)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve one inventory batch.
    """

    batch = (
        db.query(models.InventoryBatch)
        .filter(models.InventoryBatch.id == batch_id)
        .first()
    )

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Inventory batch not found.",
        )

    return batch


# ==================================================
# DELETE INVENTORY BATCH
# ==================================================

@router.delete(
    "/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """
    Delete an inventory batch only if it has never been used.
    """

    batch = (
        db.query(models.InventoryBatch)
        .filter(models.InventoryBatch.id == batch_id)
        .first()
    )

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Inventory batch not found.",
        )

    if batch.sale_items:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a batch used in sales.",
        )

    if batch.loss_logs:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a batch that has registered losses.",
        )

    if batch.transactions:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a batch because inventory transactions exist.",
        )

    db.delete(batch)

    db.commit()