from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from typing import Optional, List
from datetime import date, datetime, timedelta

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router.get("/low-stock")
def get_low_stock_report(db: Session = Depends(get_db)):
    """
    Returns a list of products whose total current quantity 
    is less than or equal to their defined minimum stock threshold.
    """
    
    # We query all active products
    all_products = db.query(models.Product).filter(models.Product.is_active == True).all()
    
    low_stock_report = []

    for product in all_products:
        # Calculate total current quantity for this product across all batches
        total_quantity = db.query(func.sum(models.InventoryBatch.current_quantity)).filter(
            models.InventoryBatch.product_id == product.id
        ).scalar() or 0
        
        # If total is at or below the threshold, add to report
        if total_quantity <= product.min_stock_threshold:
            low_stock_report.append({
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": total_quantity,
                "min_threshold": product.min_stock_threshold,
                "status": "REORDER_NOW" if total_quantity < product.min_stock_threshold else "AT_THRESHOLD"
            })
            
    return {"low_stock_items": low_stock_report}


@router.get("/batch-audit/{batch_id}")
def get_batch_audit(batch_id: int, db: Session = Depends(get_db)):
    """
    Returns the complete movement history for a specific inventory batch.
    """
    
    # 1. Verify the batch exists
    batch = db.query(models.InventoryBatch).filter(models.InventoryBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found.")

    # 2. Query all transactions linked to this batch
    transactions = db.query(models.InventoryTransaction).filter(
        models.InventoryTransaction.batch_id == batch_id
    ).order_by(models.InventoryTransaction.performed_at.asc()).all()

    # 3. Format the audit trail
    audit_trail = []
    for tx in transactions:
        audit_trail.append({
            "performed_at": tx.performed_at,
            "type": tx.transaction_type,
            "quantity_change": tx.quantity_changed,
            "user_id": tx.user_id,
            "sale_id": tx.sale_id,
            "loss_id": tx.loss_id,
            "notes": tx.notes
        })
            
    return {
        "batch_id": batch.id,
        "product_name": batch.product.name,
        "batch_number": batch.batch_number,
        "initial_quantity": batch.initial_quantity,
        "current_quantity": batch.current_quantity,
        "audit_trail": audit_trail
    }


@router.get("/sales-performance")
def get_sales_performance(
    start_date: datetime, 
    end_date: datetime, 
    customer_id: Optional[int] = None, 
    db: Session = Depends(get_db)
):
    """
    Returns total sales volume and revenue within a date range, 
    optionally filtered by a specific customer.
    """
    
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
    
    return {
        "period": {"start": start_date, "end": end_date},
        "customer_id": customer_id,
        "total_sales_count": total_sales_count,
        "total_revenue": total_revenue,
        "sales_records": sales
    }
    
@router.get("/expiring-soon", response_model=List[schemas.ExpiringBatchResponse])
def get_expiring_soon(days: int = 30, db: Session = Depends(get_db)):
    """
    Returns a list of batches nearing expiration, sorted by urgency.
    Defaults to 30 days if no threshold is provided.
    """
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

    return report