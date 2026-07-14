from datetime import datetime, date, time
from typing import Optional, List

from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status,
    Path,
    Query
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.schemas import responses
from app.security import get_current_user

from app.utils.query_sorting import apply_sorting
from app.utils.pagination import paginate

router = APIRouter(
    prefix="/inventory-transactions",
    tags=["Inventory Transactions"]
)


# ==================================================
# GET INVENTORY TRANSACTIONS
# ==================================================

@router.get(
    "/",
    response_model=responses.PaginatedResponse[List[schemas.InventoryTransactionResponse]],
    summary="List inventory transactions",
    description=(
        "Returns inventory transaction records with optional filtering by "
        "product, batch, user, transaction type, sale, loss, and date range. "
        "Administrators can view all transactions, while employees can only "
        "view transactions they created."
    ),
    responses={
        200: {"description": "Inventory transactions retrieved successfully"},
        401: {"description": "Authentication required"},
    },
)
def get_inventory_transactions(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of transactions to skip."
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
        description="Maximum number of transactions to return."
    ),
    product_id: Optional[int] = Query(
        default=None,
        gt=0,
        description="Filter by product ID."
    ),
    batch_id: Optional[int] = Query(
        default=None,
        gt=0,
        description="Filter by inventory batch ID."
    ),
    user_id: Optional[int] = Query(
        default=None,
        gt=0,
        description="Filter by user ID (administrators only)."
    ),
    transaction_type: Optional[schemas.TransactionType] = Query(
        default=None,
        description="Filter by transaction type."
    ),
    sale_id: Optional[int] = Query(
        default=None,
        gt=0,
        description="Filter by sale ID."
    ),
    loss_id: Optional[int] = Query(
        default=None,
        gt=0,
        description="Filter by loss record ID."
    ),
    start_date: Optional[datetime] = Query(
        default=None,
        description="Return transactions performed on or after this date."
    ),
    end_date: Optional[datetime] = Query(
        default=None,
        description="Return transactions performed on or before this date."
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    sort: str = Query(
        default="performed_at",
        description="Field used for sorting."
    ),
    order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sorting direction: asc or desc."
    )
):
    """
    Retrieve inventory transactions with optional filters.

    Admin:
        Can view every transaction.

    Employee:
        Can only view transactions created by themselves.
    """

    allowed_sort_fields = {
        "performed_at": models.InventoryTransaction.performed_at,
        "transaction_type": models.InventoryTransaction.transaction_type,
        "quantity_changed": models.InventoryTransaction.quantity_changed,
    }

    query = db.query(models.InventoryTransaction)
    
    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be earlier than or equal to end_date."
        )
    
    query = apply_sorting(
        query=query,
        sort=sort,
        order=order,
        allowed_fields=allowed_sort_fields,
    )

    # Employee restriction
    if current_user.role != schemas.UserRole.ADMIN:
        query = query.filter(
            models.InventoryTransaction.user_id == current_user.id
        )
    else:
        if user_id is not None:
            query = query.filter(
                models.InventoryTransaction.user_id == user_id
            )

    if product_id is not None:
        query = query.filter(
            models.InventoryTransaction.product_id == product_id
        )

    if batch_id is not None:
        query = query.filter(
            models.InventoryTransaction.batch_id == batch_id
        )

    if transaction_type is not None:
        query = query.filter(
            models.InventoryTransaction.transaction_type == transaction_type
        )

    if sale_id is not None:
        query = query.filter(
            models.InventoryTransaction.sale_id == sale_id
        )

    if loss_id is not None:
        query = query.filter(
            models.InventoryTransaction.loss_id == loss_id
        )

    if start_date is not None:
        query = query.filter(
            models.InventoryTransaction.performed_at >= start_date
        )

    if end_date is not None:
        query = query.filter(
            models.InventoryTransaction.performed_at <= end_date
        )

    transactions, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )

    return responses.PaginatedResponse(
        data=transactions,
        pagination=pagination
    )


# ==================================================
# GET INVENTORY TRANSACTION
# ==================================================

@router.get(
    "/{transaction_id}",
    response_model=responses.SuccessResponse[schemas.InventoryTransactionResponse],
    summary="Retrieve inventory transaction",
    description=(
        "Returns the details of a specific inventory transaction. "
        "Employees may only access their own transactions, while "
        "administrators can access any transaction."
    ),
    responses={
        200: {"description": "Inventory transaction retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized to access this transaction"},
        404: {"description": "Inventory transaction not found"},
    },
)
def get_inventory_transaction(
    transaction_id: int = Path(
        ...,
        gt=0,
        description="Inventory transaction ID."
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Retrieve a single inventory transaction.
    """

    transaction = (
        db.query(models.InventoryTransaction)
        .filter(models.InventoryTransaction.id == transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory transaction not found."
        )

    if (
        current_user.role != schemas.UserRole.ADMIN
        and transaction.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this transaction."
        )

    return responses.SuccessResponse(
        data=transaction
    )


# ==================================================
# GET TRANSACTION SUMMARY
# ==================================================

@router.get(
    "/summary/overview",
    response_model=responses.SuccessResponse[schemas.InventoryTransactionSummaryResponse],
    summary="Retrieve transaction summary",
    description=(
        "Returns an overview of inventory transaction activity, including "
        "the total number of transactions and the number of incoming, "
        "outgoing, loss, and adjustment operations. Administrators receive "
        "system-wide statistics, while employees receive statistics only "
        "for their own transactions."
    ),
    responses={
        200: {"description": "Transaction summary generated successfully"},
        401: {"description": "Authentication required"},
    },
)
def get_transaction_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Returns transaction summary.
    """

    query = db.query(models.InventoryTransaction)

    if current_user.role != schemas.UserRole.ADMIN:
        query = query.filter(
            models.InventoryTransaction.user_id == current_user.id
        )

    total_transactions = query.count()

    incoming = query.filter(
        models.InventoryTransaction.transaction_type == schemas.TransactionType.IN.value
    ).count()

    outgoing = query.filter(
        models.InventoryTransaction.transaction_type == schemas.TransactionType.OUT.value
    ).count()

    losses = query.filter(
        models.InventoryTransaction.transaction_type == schemas.TransactionType.LOSS.value
    ).count()

    adjustments = query.filter(
        models.InventoryTransaction.transaction_type == schemas.TransactionType.ADJUSTMENT.value
    ).count()

    summary = schemas.InventoryTransactionSummaryResponse(
        total_transactions=total_transactions,
        incoming_transactions=incoming,
        outgoing_transactions=outgoing,
        loss_transactions=losses,
        adjustment_transactions=adjustments
    )
    
    return responses.SuccessResponse(
        data=summary
    )


# ==================================================
# GET TODAY ACTIVITY
# ==================================================

@router.get(
    "/today/activity",
    response_model=responses.PaginatedResponse[List[schemas.InventoryTransactionResponse]],
    summary="Retrieve today's inventory activity",
    description=(
        "Returns inventory transactions performed during the current day. "
        "Administrators can view all activity, while employees only see "
        "their own transactions."
    ),
    responses={
        200: {"description": "Today's inventory activity retrieved successfully"},
        401: {"description": "Authentication required"},
    },
)
def get_today_activity(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of transactions to skip."
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
        description="Maximum number of transactions to return."
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    sort: str = Query(
        default="performed_at",
        description="Field used for sorting."
    ),
    order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sorting direction: asc or desc."
    ),
):
    """
    Returns today's inventory activity.
    """

    today = date.today()

    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)

    query = db.query(models.InventoryTransaction).filter(
        models.InventoryTransaction.performed_at >= start_of_day,
        models.InventoryTransaction.performed_at <= end_of_day
    )

    if current_user.role != schemas.UserRole.ADMIN:
        query = query.filter(
            models.InventoryTransaction.user_id == current_user.id
        )

    allowed_sort_fields = {
        "performed_at": models.InventoryTransaction.performed_at,
        "transaction_type": models.InventoryTransaction.transaction_type,
        "quantity_changed": models.InventoryTransaction.quantity_changed,
    }

    query = apply_sorting(
        query=query,
        sort=sort,
        order=order,
        allowed_fields=allowed_sort_fields,
    )

    transactions, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )

    return responses.PaginatedResponse(
        data=transactions,
        pagination=pagination
    )