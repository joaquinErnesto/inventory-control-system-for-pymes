from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)

@router.post("/", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """
    Register a new customer in the system.
    """
    # 1. Enforce unique identification number if one is provided
    if customer.identification_number:
        existing_customer = db.query(models.Customer).filter(
            models.Customer.identification_number == customer.identification_number
        ).first()
        if existing_customer:
            raise HTTPException(
                status_code=400, 
                detail="A customer with this identification number already exists."
            )

    # 2. Save to database
    new_customer = models.Customer(**customer.model_dump())
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    return new_customer

@router.get("/", response_model=List[schemas.CustomerResponse])
def get_all_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all registered customers.
    """
    customers = db.query(models.Customer).offset(skip).limit(limit).all()
    return customers