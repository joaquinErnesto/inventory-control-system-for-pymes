from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas

# Initialize the router
router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.post("/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """
    Add a new product to the catalog. (Does not add physical stock).
    """
    # 1. Verify the category actually exists
    category = db.query(models.Category).filter(models.Category.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail=f"Category with ID {product.category_id} does not exist.")
        
    # 2. Check for duplicate SKU/Barcode if one was provided
    if product.sku_or_barcode:
        existing_product = db.query(models.Product).filter(models.Product.sku_or_barcode == product.sku_or_barcode).first()
        if existing_product:
            raise HTTPException(status_code=400, detail="A product with this SKU or barcode already exists.")

    # 3. Convert Pydantic schema to SQLAlchemy model and save
    new_product = models.Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return new_product


@router.get("/", response_model=List[schemas.ProductResponse])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of all products in the catalog.
    """
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_single_product(product_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific product by its ID.
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(product_id: int, product_update: schemas.ProductCreate, db: Session = Depends(get_db)):
    """
    Update a product's metadata (name, base price, category, etc.).
    """
    # 1. Find the existing product
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found.")
        
    # 2. If the category is being changed, verify the new one exists
    if db_product.category_id != product_update.category_id:
        category = db.query(models.Category).filter(models.Category.id == product_update.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail=f"Category with ID {product_update.category_id} does not exist.")

    # 3. If the SKU is being changed, verify it doesn't collide with another product
    if product_update.sku_or_barcode and product_update.sku_or_barcode != db_product.sku_or_barcode:
        existing_product = db.query(models.Product).filter(models.Product.sku_or_barcode == product_update.sku_or_barcode).first()
        if existing_product:
            raise HTTPException(status_code=400, detail="A product with this SKU or barcode already exists.")

    # 4. Apply the updates
    update_data = product_update.model_dump()
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    
    return db_product