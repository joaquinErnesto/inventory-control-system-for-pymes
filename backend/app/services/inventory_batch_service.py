from sqlalchemy.orm import Session, Query

from fastapi import HTTPException

from app.models import core as models
from app.schemas import core as schemas

from app.utils.query_sorting import apply_sorting
from app.utils.pagination import paginate


# ===================================================
# RECIEVE INVENTORY BATCH
# ===================================================

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


# ===================================================
# GET INVENTORY BATCHES
# ===================================================

def list_inventory_batches(
    db: Session,
    skip: int,
    limit: int,
    sort: str,
    order: schemas.SortOrder,
):
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
    
    batches, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )
    
    return batches, pagination


# ===================================================
# PRIVATE HELPERS
# ===================================================

def _get_batch_or_404(
    db: Session,
    batch_id: int,
) -> models.InventoryBatch:
    """
    Returns an inventory batch or raises 404 if it does not exist.
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


# ===================================================
# GET INVENTORY BATCH BY ID
# ===================================================

def get_inventory_batch_by_id(
    db: Session,
    batch_id: int,
) -> models.InventoryBatch:
    return _get_batch_or_404(
        db=db,
        batch_id=batch_id
    )


# ===================================================
# DELETE INVENTORY BATCH
# ===================================================

def delete_inventory_batch(
    db: Session,
    batch_id: int,
) -> None:
    
    batch = _get_batch_or_404(
        db=db,
        batch_id=batch_id
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
    
    non_initial_transactions = [
        transaction
        for transaction in batch.transactions
        if not (
            transaction.transaction_type == schemas.TransactionType.IN.value
            and transaction.quantity_changed == batch.initial_quantity
        )
    ]

    if non_initial_transactions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete a batch because inventory "
                "transactions exist."
            ),
        )
    
    db.delete(batch)

    db.commit()