from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.schemas import responses
from app.security import (
    get_current_user,
    get_current_admin,
)

from app.utils.query_sorting import apply_sorting
from app.utils.pagination import paginate

router = APIRouter(
    prefix="/batches",
    tags=["Inventory Batches"]
)


# ==================================================
# CREATE INVENTORY BATCH
# ==================================================

@router.post(
    "/",
    summary="Receive inventory batch",
    description=(
        "Registers a new inventory batch for an existing product. "
        "The batch's current quantity is initialized with the received quantity, "
        "and an inventory transaction of type 'IN' is automatically recorded. "
        "Only administrators can receive inventory."
    ),
    response_model=responses.SuccessMessageResponse[schemas.InventoryBatchResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Inventory batch created successfully."
        },
        400: {
            "description": (
                "Invalid product or supplier, duplicate business rule, "
                "or invalid quantity/pricing values."
            )
        },
        401: {
            "description": "Authentication required."
        },
        403: {
            "description": "Administrator privileges required."
        },
    },
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

    return responses.SuccessMessageResponse(
        message="Inventory batch created successfully",
        data=new_batch
    )


# ==================================================
# GET ALL INVENTORY BATCHES
# ==================================================

@router.get(
    "/",
    summary="List inventory batches",
    description=(
        "Returns a paginated list of inventory batches. "
        "Results can be sorted by received date, expiration date, "
        "quantity, cost price, or selling price."
    ),
    response_model=responses.PaginatedResponse[List[schemas.InventoryBatchResponse]],
    responses={
        200: {
            "description": "Inventory batches retrieved successfully."
        },
        401: {
            "description": "Authentication required."
        },
    },
)
def get_all_batches(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    sort: str = "received_date",
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
    
    batches, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )

    return responses.PaginatedResponse(
        data=batches,
        pagination=pagination
    )


# ==================================================
# GET INVENTORY BATCH BY ID
# ==================================================

@router.get(
    "/{batch_id}",
    summary="Get inventory batch by ID",
    description=(
        "Returns detailed information for a specific inventory batch."
    ),
    response_model=responses.SuccessResponse[schemas.InventoryBatchResponse],
    responses={
        200: {
            "description": "Inventory batch retrieved successfully."
        },
        401: {
            "description": "Authentication required."
        },
        404: {
            "description": "Inventory batch not found."
        },
    },
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

    return responses.SuccessResponse(
        data=batch
    )


# ==================================================
# DELETE INVENTORY BATCH
# ==================================================

@router.delete(
    "/{batch_id}",
    summary="Delete inventory batch",
    description=(
        "Deletes an inventory batch only if it has never been used in sales, "
        "loss records, or inventory transactions. "
        "Only administrators can perform this operation."
    ),
    response_model=responses.MessageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Inventory batch deleted successfully."
        },
        400: {
            "description": (
                "The batch has related sales, losses, or inventory transactions "
                "and cannot be deleted."
            )
        },
        401: {
            "description": "Authentication required."
        },
        403: {
            "description": "Administrator privileges required."
        },
        404: {
            "description": "Inventory batch not found."
        },
    },
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
    
    return responses.MessageResponse(
        message="Inventory batch deleted successfully"
    )