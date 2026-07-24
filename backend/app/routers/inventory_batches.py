from fastapi import (
    APIRouter, 
    Depends,  
    status,
    Query,
    Path
)

from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import core as schemas
from app.schemas import responses
from app.security import (
    get_current_user,
    get_current_admin,
)

from app.services.inventory_batch_service import (
    receive_inventory_batch,
    delete_inventory_batch,
    get_inventory_batch_by_id,
    list_inventory_batches
)

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
def create_stock_batch(
    batch: schemas.InventoryBatchCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """
    Receive a new inventory batch.
    Only administrators may receive stock.
    """
    new_batch = receive_inventory_batch(
        db=db,
        current_user=current_user,
        batch=batch,
    )

    return responses.SuccessMessageResponse(
        message="Inventory batch created successfully",
        data=new_batch,
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
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip."
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
        description="Maximum number of records to return."
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    sort: str = Query(
        default="received_date",
        description=(
            "Field used for sorting. "
            "Allowed values: received_date, expiration_date, "
            "current_quantity, cost_price, selling_price."
        ),
    ),
    order: schemas.SortOrder = Query(
        default=schemas.SortOrder.DESC,
        description="Sort direction."
    )
):
    """
    Retrieve all inventory batches.
    """
    
    batches, pagination = list_inventory_batches(
        db=db,
        skip=skip,
        limit=limit,
        sort=sort,
        order=order,
    )

    return responses.PaginatedResponse(
        data=batches,
        pagination=pagination,
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
    batch_id: int = Path(
        ...,
        gt=0,
        description="Unique identifier of the inventory batch."
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve one inventory batch.
    """
    
    batch = get_inventory_batch_by_id(
        db=db,
        batch_id=batch_id,
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
    batch_id: int = Path(
        ...,
        gt=0,
        description="Unique identifier of the inventory batch."
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """
    Delete an inventory batch only if it has never been used.
    """

    delete_inventory_batch(
        db=db,
        batch_id=batch_id,
    )

    return responses.MessageResponse(
        message="Inventory batch deleted successfully"
    )    