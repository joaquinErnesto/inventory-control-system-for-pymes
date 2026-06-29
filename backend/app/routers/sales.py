from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas

router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)

@router.post("/", response_model=schemas.SaleResponse, status_code=status.HTTP_201_CREATED)
def process_sale(sale_request: schemas.SaleCreate, db: Session = Depends(get_db)):
    """
    Process a complex multi-table sale transaction.
    """
    # 1. Validate the User (Cashier)
    user = db.query(models.User).filter(models.User.id == sale_request.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid user_id.")

    # 2. Validate the Customer (If provided)
    if sale_request.customer_id:
        customer = db.query(models.Customer).filter(models.Customer.id == sale_request.customer_id).first()
        if not customer:
            raise HTTPException(status_code=400, detail="Invalid customer_id.")

    # 3. Create the parent Sale record (initially with 0 total)
    new_sale = models.Sale(
        user_id=sale_request.user_id,
        customer_id=sale_request.customer_id,
        payment_method=sale_request.payment_method,
        payment_status=sale_request.payment_status,
        total_amount=Decimal('0.00')
    )
    
    db.add(new_sale)
    # Flush pushes the Sale to the database to generate the ID, but DOES NOT commit yet.
    # If something fails later, this still gets rolled back.
    db.flush() 

    calculated_total = Decimal('0.00')

    # 4. Loop through every item being sold
    for item in sale_request.items:
        if item.quantity_sold <= 0:
            raise HTTPException(status_code=400, detail="Quantity sold must be greater than zero.")
            
        if item.unit_price < 0:
            raise HTTPException(status_code=400, detail="Unit price cannot be negative.")

        # 4a. Fetch the specific inventory batch
        batch = db.query(models.InventoryBatch).filter(
            models.InventoryBatch.id == item.batch_id,
            models.InventoryBatch.product_id == item.product_id
        ).first()

        if not batch:
            raise HTTPException(
                status_code=400, 
                detail=f"Batch {item.batch_id} containing Product {item.product_id} not found."
            )

        # 4b. Enforce strict stock limits
        if batch.current_quantity < item.quantity_sold:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Batch {item.batch_id} only has {batch.current_quantity} left."
            )

        # 4c. Deduct the inventory from the warehouse shelf
        batch.current_quantity -= item.quantity_sold

        # 4d. Create the Sale Item line
        new_sale_item = models.SaleItem(
            sale_id=new_sale.id,
            batch_id=item.batch_id,
            product_id=item.product_id,
            quantity_sold=item.quantity_sold,
            unit_price=item.unit_price
        )
        db.add(new_sale_item)

        # 4e. Log the movement in the Centralized Transactions Ledger
        inventory_log = models.InventoryTransaction(
            product_id=item.product_id,
            batch_id=item.batch_id,
            user_id=sale_request.user_id,
            quantity_changed=-(item.quantity_sold), # Negative number because stock is leaving
            transaction_type=schemas.TransactionType.OUT.value,
            sale_id=new_sale.id,
            notes=f"Sold {item.quantity_sold} units via Sale #{new_sale.id}"
        )
        db.add(inventory_log)

        # 4f. Add to the running total math
        calculated_total += (Decimal(item.quantity_sold) * item.unit_price)

    # 5. Finalize the total price on the parent receipt
    new_sale.total_amount = calculated_total

    # 6. COMMIT ALL CHANGES AT ONCE
    db.commit()
    db.refresh(new_sale)

    return new_sale

@router.get("/", response_model=List[schemas.SaleResponse])
def get_all_sales(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all sales receipts.
    """
    sales = db.query(models.Sale).offset(skip).limit(limit).all()
    return sales