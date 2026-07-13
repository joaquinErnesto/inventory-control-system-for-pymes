from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from typing import Optional, List
from datetime import date, datetime, timedelta

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.schemas import responses
from app.security import get_current_user

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


# ==================================================
# GET LOW STOCK
# ==================================================

@router.get(
    "/low-stock",
    response_model=responses.SuccessResponse[List[schemas.LowStockItemResponse]]
)
def get_low_stock_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Returns a list of products whose total current quantity 
    is less than or equal to their defined minimum stock threshold.
    """
    
    if current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access reports."
        )
    
    results = (
        db.query(
            models.Product.id,
            models.Product.name,
            models.Product.min_stock_threshold,
            func.coalesce(
                func.sum(models.InventoryBatch.current_quantity),
                0
            ).label("current_stock")
        )
        .outerjoin(
            models.InventoryBatch,
            models.Product.id == models.InventoryBatch.product_id
        )
        .filter(models.Product.is_active.is_(True))
        .group_by(
            models.Product.id,
            models.Product.name,
            models.Product.min_stock_threshold
        )
        .all()
    )

    report = []

    for row in results:

        if row.current_stock <= row.min_stock_threshold:

            report.append(
                schemas.LowStockItemResponse(
                    product_id=row.id,
                    product_name=row.name,
                    current_stock=row.current_stock,
                    min_threshold=row.min_stock_threshold,
                    status=(
                        "REORDER_NOW"
                        if row.current_stock < row.min_stock_threshold
                        else "AT_THRESHOLD"
                    ),
                )
            )

    return responses.SuccessResponse(
        data=report
    )


# ==================================================
# GET BATCH AUDIT
# ==================================================

@router.get(
    "/batch-audit/{batch_id}",
    response_model=responses.SuccessResponse[schemas.BatchAuditResponse]
)
def get_batch_audit(
    batch_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Returns the complete movement history for a specific inventory batch.
    """
    
    if current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access reports."
        )
    
    # 1. Verify the batch exists
    batch = (
        db.query(models.InventoryBatch)
        .filter(models.InventoryBatch.id == batch_id)
        .first()
    )
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found.")

    # 2. Query all transactions linked to this batch
    transactions = db.query(models.InventoryTransaction).filter(
        models.InventoryTransaction.batch_id == batch_id
    ).order_by(models.InventoryTransaction.performed_at.asc()).all()

    # 3. Format the audit trail
    audit_trail = []
    for tx in transactions:
        audit_trail.append(
            schemas.BatchAuditTransactionResponse(
                performed_at=tx.performed_at,
                type=tx.transaction_type,
                quantity_change=tx.quantity_changed,
                user_id=tx.user_id,
                sale_id=tx.sale_id,
                loss_id=tx.loss_id,
                notes=tx.notes,
            )
        )
    
    report = schemas.BatchAuditResponse(
        batch_id=batch.id,
        product_name=batch.product.name,
        batch_number=batch.batch_number,
        initial_quantity=batch.initial_quantity,
        current_quantity=batch.current_quantity,
        audit_trail=audit_trail,
    )
      
    return responses.SuccessResponse(
        data=report
    )


# ==================================================
# GET SALES PERFORMANCE
# ==================================================

@router.get(
    "/sales-performance",
    response_model=responses.SuccessResponse[schemas.SalesPerformanceResponse]
)
def get_sales_performance(
    start_date: datetime, 
    end_date: datetime, 
    customer_id: Optional[int] = None, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Returns total sales volume and revenue within a date range, 
    optionally filtered by a specific customer.
    """
    
    if current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access reports."
        )
    
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be earlier than end_date."
        )
        
    # Base query for all sales within the date range
    query = db.query(models.Sale).filter(
        models.Sale.sold_at.between(start_date, end_date)
    )
    
    # Apply optional customer filter
    if customer_id:
        query = query.filter(models.Sale.customer_id == customer_id)
        
    sales = query.all()
    
    # Calculate metrics
    total_revenue = sum(sale.total_amount for sale in sales)
    total_sales_count = len(sales)
    average_sale = (
        total_revenue / total_sales_count
        if total_sales_count > 0
        else 0
    )
    
    report = schemas.SalesPerformanceResponse(
        start_date=start_date,
        end_date=end_date,
        customer_id=customer_id,
        total_sales_count=total_sales_count,
        total_revenue=total_revenue,
        average_sale=average_sale,
        sales_records=sales,
    )
    
    return responses.SuccessResponse(
        data=report
    )
 
 
# =================================================
# GET EXPIRING SOON
# =================================================
   
@router.get(
    "/expiring-soon", 
    response_model=responses.SuccessResponse[List[schemas.ExpiringBatchResponse]]
)
def get_expiring_soon(
    days: int = 30, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Returns a list of batches nearing expiration, sorted by urgency.
    Defaults to 30 days if no threshold is provided.
    """
    
    if current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access reports."
        )
        
    if days <= 0:
        raise HTTPException(
            status_code=400,
            detail="days must be greater than zero."
        )
    
    today = date.today()
    threshold_date = today + timedelta(days=days)

    # 1. Query batches that:
    # - Have an expiration date
    # - Are not yet expired (expiration_date >= today)
    # - Expire within the threshold (expiration_date <= threshold_date)
    expiring_batches = db.query(models.InventoryBatch).filter(
        models.InventoryBatch.expiration_date.isnot(None),
        models.InventoryBatch.expiration_date >= today,
        models.InventoryBatch.expiration_date <= threshold_date,
        models.InventoryBatch.current_quantity > 0
    ).order_by(
        models.InventoryBatch.expiration_date.asc()
    ).all()

    # 2. Transform the data into the response format
    report = []
    for batch in expiring_batches:
        remaining = (batch.expiration_date - today).days
        
        report.append(
            schemas.ExpiringBatchResponse(
                product_name=batch.product.name, # Accessed via SQLAlchemy relationship
                batch_number=batch.batch_number,
                current_quantity=batch.current_quantity,
                expiration_date=batch.expiration_date,
                days_remaining=remaining
            )
        )

    return responses.SuccessMessageResponse(
        data=report
    )