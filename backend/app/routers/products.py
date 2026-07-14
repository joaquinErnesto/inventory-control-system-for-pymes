from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status,
    Path,
    Query
)

from sqlalchemy import or_
from sqlalchemy.orm import Session

from typing import List, Annotated

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.schemas import responses
from app.security import (
    get_current_user,
    get_current_admin
)

from app.utils.query_sorting import apply_sorting
from app.utils.pagination import paginate

# Initialize the router
router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# ==================================================
# CREATE PRODUCT
# ==================================================

@router.post(
    "/",
    summary="Create product",
    description="Creates a new product in the catalog. This operation only registers the product metadata and does not add physical inventory. Only administrators can perform this operation.",
    response_model=responses.SuccessMessageResponse[schemas.ProductResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Product created successfully"},
        400: {"description": "Invalid category or duplicate SKU/barcode"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
    },
)
def create_product(
    product: schemas.ProductCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Add a new product to the catalog. (Does not add physical stock).
    """
    # 1. Verify the category actually exists
    category = (
        db.query(models.Category)
        .filter(
            models.Category.id == product.category_id
        )
        .first()
    )
    
    if not category:
        raise HTTPException(status_code=400, detail=f"Category with ID {product.category_id} does not exist.")
        
    # 2. Check for duplicate SKU/Barcode if one was provided
    
    if product.sku_or_barcode:
        existing_product = (
            db.query(models.Product)
            .filter(
                models.Product.sku_or_barcode == product.sku_or_barcode
            )
            .first()
        )
        
        if existing_product:
            raise HTTPException(status_code=400, detail="A product with this SKU or barcode already exists.")

    # 3. Convert Pydantic schema to SQLAlchemy model and save
    new_product = models.Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return responses.SuccessMessageResponse(
        message="Product created successfully",
        data=new_product
    )


# ==================================================
# GET PRODUCTS 
# ==================================================

@router.get(
    "/",
    summary="List products",
    description="Returns a paginated list of products with optional sorting.",
    response_model=responses.PaginatedResponse[List[schemas.ProductResponse]],
    responses={
        200: {"description": "Products retrieved successfully"},
        401: {"description": "Authentication required"},
    },
)
def get_products(
    skip: Annotated[
        int,
        Query(
            ge=0,
            description="Number of records to skip."
        )
    ] = 0, 
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Maximum number of records to return."
        )
    ] = 100, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    sort: Annotated[
        str,
        Query(
            description="Field used for sorting."
        )
    ] = "name",
    order: Annotated[
        str,
        Query(
            pattern="^(asc|desc)$",
            description="Sort order: asc or desc."
        )
    ] = "asc",
):
    """
    Retrieve a list of all products in the catalog.
    """
    
    allowed_sort_fields = {
        "name": models.Product.name,
        "base_price": models.Product.base_price,
        "created_at": models.Product.created_at,
        "min_stock_threshold": models.Product.min_stock_threshold,
    }
    
    query = db.query(models.Product)

    query = apply_sorting(
        query=query,
        sort=sort,
        order=order,
        allowed_fields=allowed_sort_fields,
    )
    
    products, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )
    
    return responses.PaginatedResponse(
        data=products,
        pagination=pagination
    )


# ==================================================
# SEARCH PRODUCTS
# ==================================================

@router.get(
    "/search/",
    summary="Search products",
    description="Searches active products by name, SKU/barcode, or description.",
    response_model=responses.PaginatedResponse[List[schemas.ProductResponse]],
    responses={
        200: {"description": "Search completed successfully"},
        401: {"description": "Authentication required"},
    },
)
def search_products(
    q: Annotated[
        str,
        Query(
            min_length=1,
            max_length=100,
            description="Search term."
        )
    ],
    skip: Annotated[
        int,
        Query(
            ge=0,
            description="Number of records to skip."
        )
    ] = 0,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=50,
            description="Maximum number of records to return."
        )
    ] = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search products by name, SKU/barcode or description.
    """

    search = f"%{q}%"

    query = (
        db.query(models.Product)
        .filter(
            models.Product.is_active.is_(True),
            or_(
                models.Product.name.like(search),
                models.Product.sku_or_barcode.like(search),
                models.Product.description.like(search),
            ),
        )
    )
    
    products, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )

    return responses.PaginatedResponse(
        data=products,
        pagination=pagination
    )


# ==================================================
# GET PRODUCT BY ID
# ==================================================

@router.get(
    "/{product_id}",
    summary="Get product by ID",
    description="Returns the details of a specific product.",
    response_model=responses.SuccessResponse[schemas.ProductResponse],
    responses={
        200: {"description": "Product retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Product not found"},
    },
)
def get_single_product(
    product_id: Annotated[
        int,
        Path(
            gt=0,
            description="Product ID"
        )
    ], 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retrieve a specific product by its ID.
    """
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id
        )
        .first()
    )
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    
    return responses.SuccessResponse(
        data=product
    )


# ==================================================
# UPDATE PRODUCT
# ==================================================

@router.put(
    "/{product_id}",
    summary="Update product",
    description="Updates an existing product, including its category, pricing, stock threshold, and metadata. Only administrators can perform this operation.",
    response_model=responses.SuccessMessageResponse[schemas.ProductResponse],
    responses={
        200: {"description": "Product updated successfully"},
        400: {"description": "Invalid category or duplicate SKU/barcode"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
        404: {"description": "Product not found"},
    },
)
def update_product(
    product_id: Annotated[
        int,
        Path(
            gt=0,
            description="Product ID"
        )
    ], 
    product_update: schemas.ProductCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Update a product's metadata (name, base price, category, etc.).
    """
    # 1. Find the existing product
    db_product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id
        )
        .first()    
    )
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found.")
        
    # 2. If the category is being changed, verify the new one exists
    if db_product.category_id != product_update.category_id:
        category = (
            db.query(models.Category)
            .filter(
                models.Category.id == product_update.category_id
            )
            .first()    
        )
        
        if not category:
            raise HTTPException(status_code=400, detail=f"Category with ID {product_update.category_id} does not exist.")

    # 3. If the SKU is being changed, verify it doesn't collide with another product
    if product_update.sku_or_barcode and product_update.sku_or_barcode != db_product.sku_or_barcode:
        existing_product = (
            db.query(models.Product)
            .filter(
                models.Product.sku_or_barcode == product_update.sku_or_barcode
            )
            .first()
        )
        
        if existing_product:
            raise HTTPException(status_code=400, detail="A product with this SKU or barcode already exists.")

    # 4. Apply the updates
    update_data = product_update.model_dump()
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    
    return responses.SuccessMessageResponse(
        message="Product updated successfully",
        data=db_product
    )


# ==================================================
# DELETE PRODUCT
# ==================================================

@router.delete(
    "/{product_id}",
    summary="Delete product",
    description="Deletes a product from the catalog. Products that are referenced by inventory batches, sales, or inventory transactions cannot be deleted. Only administrators can perform this operation.",
    status_code=status.HTTP_200_OK,
    response_model=responses.MessageResponse,
    responses={
        200: {"description": "Product deleted successfully"},
        400: {"description": "Product is referenced by inventory, sales, or transactions"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
        404: {"description": "Product not found"},
    },
)
def delete_product(
    product_id: Annotated[
        int,
        Path(
            gt=0,
            description="Product ID"
        )
    ],
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """
    Delete a product from the catalog.

    A product cannot be deleted if it has related inventory,
    sales or transactions.
    """

    db_product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )

    if not db_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found."
        )

    if (
        db_product.batches
        or db_product.sale_items
        or db_product.transactions
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "This product cannot be deleted because it is "
                "referenced by inventory, sales or transactions."
            ),
        )

    db.delete(db_product)
    db.commit()
    
    return responses.MessageResponse(
        message="Product deleted succesfully"
    )