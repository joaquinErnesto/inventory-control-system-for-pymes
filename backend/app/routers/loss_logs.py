from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status,
    Query,
    Path
)

from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.schemas import responses
from app.security import (
    get_current_user
)

from app.logging.logger import logger

from app.utils.query_sorting import apply_sorting
from app.utils.pagination import paginate

router = APIRouter(
    prefix="/losses",
    tags=["Loss Logs"]
)


# ==================================================
# LOG LOSS (CREATE)
# ==================================================

@router.post(
    "/",
    response_model=responses.SuccessMessageResponse[schemas.LossLogResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register inventory loss",
    description=(
        "Registers an inventory loss, deducts stock from the selected batch, "
        "creates an inventory transaction record, and triggers a low-stock "
        "warning when the remaining stock reaches the configured threshold."
    ),
    responses={
        201: {"description": "Loss registered successfully"},
        400: {
            "description": (
                "Invalid batch, inactive product, insufficient stock, "
                "or invalid quantity."
            )
        },
        401: {"description": "Authentication required"},
        404: {"description": "Batch not found"},
    },
)
def log_loss(
    loss: schemas.LossLogCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
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
    
    return responses.SuccessMessageResponse(
        message="Loss registered successfully",
        data=new_loss
    )


# ==================================================
# GET ALL LOSS LOGS
# ==================================================

@router.get(
    "/",
    response_model=responses.PaginatedResponse[List[schemas.LossLogResponse]],
    summary="List inventory loss records",
    description=(
        "Returns a paginated list of inventory loss records. "
        "Administrators can view all losses, while employees "
        "can only view the losses they registered."
    ),
    responses={
        200: {"description": "Loss records retrieved successfully"},
        401: {"description": "Authentication required"},
    },
)
def get_all_loss_logs(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of loss records to skip."
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
        description="Maximum number of loss records to return."
    ),
    sort: str = Query(
        default="logged_at",
        description="Field used for sorting."
    ),
    order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sorting direction: asc or desc."
    ),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve all loss logs.

    Administrators can view every record.

    Employees can only view their own records.
    """

    query = db.query(models.LossLog)

    allowed_sort_fields = {
        "logged_at": models.LossLog.logged_at,
        "quantity_lost": models.LossLog.quantity_lost,
        "reason": models.LossLog.reason,
    }
    
    query = apply_sorting(
        query=query,
        sort=sort,
        order=order,
        allowed_fields=allowed_sort_fields,
    )
    
    if current_user.role != schemas.UserRole.ADMIN:
        query = query.filter(
            models.LossLog.user_id == current_user.id
        )
    
    loss_logs, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )
    
    return responses.PaginatedResponse(
        data=loss_logs,
        pagination=pagination
    )


# ==================================================
# GET LOSS LOG BY ID
# ==================================================

@router.get(
    "/{loss_id}",
    response_model=responses.SuccessResponse[schemas.LossLogResponse],
    summary="Retrieve a loss record",
    description=(
        "Returns the details of a specific inventory loss record "
        "by its identifier."
    ),
    responses={
        200: {"description": "Loss record retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized to access this loss record"},
        404: {"description": "Loss record not found"},
    },
)
def get_loss_log(
    loss_id: int = Path(
        ...,
        gt=0,
        description="Loss record ID."
    ),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve one loss log.
    """

    loss = (
        db.query(models.LossLog)
        .filter(models.LossLog.id == loss_id)
        .first()
    )

    if loss is None:
        raise HTTPException(
            status_code=404,
            detail="Loss log not found."
        )

    if (
        current_user.role != schemas.UserRole.ADMIN
        and loss.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view this loss log."
        )

    return responses.SuccessResponse(
        data=loss
    )