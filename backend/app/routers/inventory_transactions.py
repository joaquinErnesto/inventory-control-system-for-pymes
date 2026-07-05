from datetime import datetime, date, time
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.security import get_current_user

router = APIRouter(
    prefix="/inventory-transactions",
    tags=["Inventory Transactions"]
)


@router.get("/", response_model=List[schemas.InventoryTransactionResponse])
def get_inventory_transactions(
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    user_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    sale_id: Optional[int] = None,
    loss_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Retrieve inventory transactions with optional filters.

    Admin:
        Can view every transaction.

    Employee:
        Can only view transactions created by themselves.
    """

    query = db.query(models.InventoryTransaction)

    # Employee restriction
    if current_user.role != "admin":
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

    transactions = (
        query.order_by(models.InventoryTransaction.performed_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return transactions


@router.get("/{transaction_id}", response_model=schemas.InventoryTransactionResponse)
def get_inventory_transaction(
    transaction_id: int,
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
        current_user.role != "admin"
        and transaction.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this transaction."
        )

    return transaction


@router.get("/summary/overview")
def get_transaction_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Returns transaction summary.
    """

    query = db.query(models.InventoryTransaction)

    if current_user.role != "admin":
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

    return {
        "total_transactions": total_transactions,
        "incoming_transactions": incoming,
        "outgoing_transactions": outgoing,
        "loss_transactions": losses,
        "adjustment_transactions": adjustments
    }


@router.get("/today/activity", response_model=List[schemas.InventoryTransactionResponse])
def get_today_activity(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
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

    if current_user.role != "admin":
        query = query.filter(
            models.InventoryTransaction.user_id == current_user.id
        )

    return (
        query.order_by(
            models.InventoryTransaction.performed_at.desc()
        ).all()
    )