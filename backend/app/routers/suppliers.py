from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas

# Initialize the router
router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"]
)

@router.post("/", response_model=schemas.SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(supplier: schemas.SupplierCreate, db: Session = Depends(get_db)):
    """
    Register a new supplier in the system.
    """
    # 1. Check if a supplier with this name already exists
    db_supplier = db.query(models.Supplier).filter(models.Supplier.name == supplier.name).first()
    if db_supplier:
        raise HTTPException(status_code=400, detail="A supplier with this name already exists.")
    
    # 2. Convert Pydantic schema to SQLAlchemy model
    new_supplier = models.Supplier(**supplier.model_dump())
    
    # 3. Save to database
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    
    # 4. Return the newly created supplier
    return new_supplier

@router.get("/", response_model=List[schemas.SupplierResponse])
def get_suppliers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of all suppliers.
    """
    suppliers = db.query(models.Supplier).offset(skip).limit(limit).all()
    return suppliers

@router.get("/{supplier_id}", response_model=schemas.SupplierResponse)
def get_single_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific supplier by their ID.
    """
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return supplier