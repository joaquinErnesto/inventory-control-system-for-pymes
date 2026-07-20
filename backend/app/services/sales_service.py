from decimal import Decimal

from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.models import core as models
from app.schemas import core as schemas

def create_sale(
    db: Session,
    sale_request: schemas.SaleCreate,
    current_user: models.User
) -> models.Sale:
    """
    Process a complex multi-table sale transaction using Automated FEFO/FIFO stock deduction.
    """
    try:
        # 2. Validate the Customer (If provided)
        if sale_request.customer_id:
            customer = db.query(models.Customer).filter(models.Customer.id == sale_request.customer_id).first()
            if not customer:
                raise HTTPException(status_code=400, detail="Invalid customer_id.")

        # 3. Create the parent Sale record
        new_sale = models.Sale(
            user_id=current_user.id,
            customer_id=sale_request.customer_id,
            payment_method=sale_request.payment_method,
            payment_status=sale_request.payment_status,
            total_amount=Decimal("0.00")
        )
        
        db.add(new_sale)
        db.flush() 

        calculated_total = Decimal("0.00")

        # 4. Loop through every product requested in the cart
        for item in sale_request.items:
            if item.quantity_sold <= 0:
                raise HTTPException(status_code=400, detail="Quantity sold must be greater than zero.")
                
            if item.unit_price < 0:
                raise HTTPException(status_code=400, detail="Unit price cannot be negative.")

            remaining_qty_to_fulfill = item.quantity_sold

            # 4a. Fetch active batches. Order by Expiration (FEFO) -> then Received Date (FIFO)
            available_batches = (
                db.query(models.InventoryBatch)
                .filter(
                    models.InventoryBatch.product_id == item.product_id,
                    models.InventoryBatch.current_quantity > 0
                )
                .order_by(
                    models.InventoryBatch.expiration_date.is_(None),
                    models.InventoryBatch.expiration_date.asc(),
                    models.InventoryBatch.received_date.asc()
                )
                .with_for_update()
                .all()
            )

            # 4b. Pre-calculate if we have enough total stock across all active batches
            total_available_stock = sum(batch.current_quantity for batch in available_batches)
            if total_available_stock < remaining_qty_to_fulfill:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient total stock for Product ID {item.product_id}. Requested: {remaining_qty_to_fulfill}, Available: {total_available_stock}."
                )

            # 4c. Cascade through the batches until the requested quantity is fulfilled
            for batch in available_batches:
                if remaining_qty_to_fulfill <= 0:
                    break 

                # Determine how much we can take from THIS specific batch
                qty_to_deduct = min(batch.current_quantity, remaining_qty_to_fulfill)

                # Deduct the inventory
                batch.current_quantity -= qty_to_deduct
                remaining_qty_to_fulfill -= qty_to_deduct

                # Create the Sale Item line linked to this specific batch
                new_sale_item = models.SaleItem(
                    sale_id=new_sale.id,
                    batch_id=batch.id,
                    product_id=item.product_id,
                    quantity_sold=qty_to_deduct,
                    unit_price=item.unit_price
                )
                db.add(new_sale_item)

                # Log the movement in the Centralized Transactions Ledger
                inventory_log = models.InventoryTransaction(
                    product_id=item.product_id,
                    batch_id=batch.id,
                    user_id=current_user.id,
                    quantity_changed=-(qty_to_deduct),
                    transaction_type=schemas.TransactionType.OUT.value, 
                    sale_id=new_sale.id,
                    notes=f"Auto-deducted {qty_to_deduct} units via Sale #{new_sale.id} (FEFO/FIFO)"
                )
                db.add(inventory_log)

                # Add to the running total math
                calculated_total += (Decimal(str(qty_to_deduct)) * item.unit_price)

        # 5. Finalize the total price on the parent receipt
        new_sale.total_amount = calculated_total

        # 6. COMMIT ALL CHANGES AT ONCE
        db.commit()
        db.refresh(new_sale)
    
    except Exception:
        db.rollback()
        raise

    return new_sale