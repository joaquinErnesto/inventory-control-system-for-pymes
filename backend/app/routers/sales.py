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
from app.security import get_current_user

from app.utils.query_sorting import apply_sorting
from app.utils.pagination import paginate

from app.services import sales_service

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
    sale = sales_service.create_sale(
        db=db,
        sale_request=sale_request,
        current_user=current_user
    )
    
    return responses.SuccessMessageResponse(
        message="Sale processed successfully",
        data= sale
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