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
from decimal import Decimal

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.schemas import responses
from app.security import get_current_user

from app.utils.query_sorting import apply_sorting
from app.utils.pagination import paginate

router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)


# ==================================================
# CREATE SALE
# ==================================================

@router.post(
    "/",
    response_model=responses.SuccessMessageResponse[schemas.SaleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Process a sale",
    description=(
        "Creates a new sale, deducts inventory using the FEFO/FIFO strategy, "
        "creates sale items, records inventory transactions, and calculates "
        "the total amount."
    ),
    responses={
        201: {"description": "Sale processed successfully."},
        400: {
            "description": (
                "Invalid customer, invalid product, insufficient stock, "
                "or invalid sale data."
            )
        },
        401: {"description": "Authentication required."},
    },
)
def process_sale(
    sale_request: schemas.SaleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process a complex multi-table sale transaction using Automated FEFO/FIFO stock deduction.
    """
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

    return responses.SuccessMessageResponse(
        message="Sale processed successfully",
        data=new_sale
    )


# ==================================================
# GET SALES
# ==================================================

@router.get(
    "/",
    response_model=responses.PaginatedResponse[List[schemas.SaleResponse]],
    summary="List sales",
    description=(
        "Returns a paginated list of sales. "
        "Supports sorting by sale date and total amount."
    ),
    responses={
        200: {"description": "Sales retrieved successfully."},
        401: {"description": "Authentication required."},
    },
)
def get_all_sales(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of sales to skip."
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
        description="Maximum number of sales to return."
    ), 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    sort: str = Query(
        default="sold_at",
        description="Field used for sorting."
    ),
    order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sorting direction."
    ),
):
    """
    Retrieve all sales receipts.
    """
    allowed_sort_fields = {
        "sold_at": models.Sale.sold_at,
        "total_amount": models.Sale.total_amount,
    }
    
    query = db.query(models.Sale)
    
    query = apply_sorting(
        query=query,
        sort=sort,
        order=order,
        allowed_fields=allowed_sort_fields,
    )
    
    sales, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )

    return responses.PaginatedResponse(
        data=sales,
        pagination=pagination
    )


# ==================================================
# GET SALE
# ==================================================

@router.get(
    "/{sale_id}",
    response_model=responses.SuccessResponse[schemas.SaleDetailResponse],
    summary="Get sale by ID",
    description=(
        "Returns the complete details of a sale, including customer, "
        "employee, payment information, and purchased items."
    ),
    responses={
        200: {"description": "Sale retrieved successfully."},
        401: {"description": "Authentication required."},
        404: {"description": "Sale not found."},
    },
)
def get_sale(
    sale_id: int = Path(
        ...,
        gt=0,
        description="Sale ID."
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Returns the complete receipt for a single sale.
    """

    sale = (
        db.query(models.Sale)
        .filter(models.Sale.id == sale_id)
        .first()
    )

    if sale is None:
        raise HTTPException(
            status_code=404,
            detail="Sale not found."
        )

    items = []

    for item in sale.items:

        items.append(
            schemas.SaleItemDetailResponse(
                product_id=item.product_id,
                product_name=item.product.name,
                batch_id=item.batch_id,
                quantity_sold=item.quantity_sold,
                unit_price=item.unit_price,
                subtotal=item.quantity_sold * item.unit_price
            )
        )

    sale_detail = schemas.SaleDetailResponse(

        id=sale.id,

        sold_at=sale.sold_at,

        total_amount=sale.total_amount,

        payment_method=sale.payment_method,

        payment_status=sale.payment_status,

        customer_id=sale.customer.id if sale.customer else None,
        customer_name=sale.customer.name if sale.customer else None,

        user_id=sale.user.id,
        employee_username=sale.user.username,

        items=items
    )
    
    return responses.SuccessResponse(
        data=sale_detail
    )