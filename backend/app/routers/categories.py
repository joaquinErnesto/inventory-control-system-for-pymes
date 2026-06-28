from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas

# Initialize the router
router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

@router.post("/", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    """
    Create a new product category.
    """
    # 1. Check if a category with this name already exists
    db_category = db.query(models.Category).filter(models.Category.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="A category with this name already exists.")
    
    # 2. Convert Pydantic schema to SQLAlchemy model
    new_category = models.Category(**category.model_dump())
    
    # 3. Save to database
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    # 4. Return the newly created category (FastAPI automatically applies CategoryResponse)
    return new_category

@router.get("/", response_model=List[schemas.CategoryResponse])
def get_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of all categories.
    """
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories