from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy import or_

from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.schemas import responses
from app.security import (
    get_current_user,
    get_current_admin,
)

from app.utils.query_sorting import apply_sorting
from app.utils.pagination import paginate

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


# ==================================================
# CREATE CUSTOMER
# ==================================================

@router.post(
    "/",
    response_model=responses.SuccessMessageResponse[schemas.CustomerResponse],
    status_code=status.HTTP_201_CREATED
)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Register a new customer.
    Admin only.
    """

    if customer.identification_number:

        existing_customer = (
            db.query(models.Customer)
            .filter(
                models.Customer.identification_number
                == customer.identification_number
            )
            .first()
        )

        if existing_customer:
            raise HTTPException(
                status_code=400,
                detail="A customer with this identification number already exists.",
            )

    new_customer = models.Customer(
        **customer.model_dump()
    )

    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    return responses.SuccessMessageResponse(
        message="Customer created successfully",
        data=new_customer
    )


# ==================================================
# GET CUSTOMERS
# ==================================================

@router.get(
    "/",
    response_model=responses.PaginatedResponse[List[schemas.CustomerResponse]]
)
def get_all_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    sort: str = "name",
    order: str = "asc"
):
    """
    Retrieve all customers.
    Any authenticated user.
    """

    allowed_sort_fields = {
        "name": models.Customer.name,
        "created_at": models.Customer.created_at,
    }
    
    query = db.query(models.Customer)
    
    query = apply_sorting(
        query=query,
        sort=sort,
        order=order,
        allowed_fields=allowed_sort_fields,
    )
    
    customers, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )

    return responses.PaginatedResponse(
        data=customers,
        pagination=pagination
    )


# ==================================================
# SEARCH CUSTOMERS
# ==================================================

@router.get(
    "/search/", 
    response_model=responses.PaginatedResponse[List[schemas.CustomerResponse]]
)
def search_customers(
    q: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search customers by name, identification,
    phone or email.
    """

    search = f"%{q}%"

    query = (
        db.query(models.Customer)
        .filter(
            or_(
                models.Customer.name.like(search),
                models.Customer.identification_number.like(search),
                models.Customer.phone.like(search),
                models.Customer.email.like(search),
            )
        )
    )
    
    customers, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )

    return responses.PaginatedResponse(
        data=customers,
        pagination=pagination
    )


# ==================================================
# GET CUSTOMER BY ID
# ==================================================

@router.get(
    "/{customer_id}",
    response_model=responses.SuccessResponse[schemas.CustomerResponse]
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve a customer by ID.
    Any authenticated user.
    """

    customer = (
        db.query(models.Customer)
        .filter(models.Customer.id == customer_id)
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    return responses.SuccessResponse(
        data=customer
    )


# ==================================================
# UPDATE CUSTOMER
# ==================================================

@router.put(
    "/{customer_id}",
    response_model=responses.SuccessMessageResponse[schemas.CustomerResponse]
)
def update_customer(
    customer_id: int,
    customer_update: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Update a customer.
    Admin only.
    """

    customer = (
        db.query(models.Customer)
        .filter(models.Customer.id == customer_id)
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    if (
        customer_update.identification_number
        and customer_update.identification_number
        != customer.identification_number
    ):

        existing_customer = (
            db.query(models.Customer)
            .filter(
                models.Customer.identification_number
                == customer_update.identification_number
            )
            .first()
        )

        if existing_customer:
            raise HTTPException(
                status_code=400,
                detail="A customer with this identification number already exists.",
            )

    update_data = customer_update.model_dump()

    for key, value in update_data.items():
        setattr(customer, key, value)

    db.commit()
    db.refresh(customer)

    return responses.SuccessMessageResponse(
        message="Customer updated successfully",
        data=customer
    )


# ==================================================
# DELETE CUSTOMER
# ==================================================

@router.delete(
    "/{customer_id}",
    response_model=responses.MessageResponse,
    status_code=status.HTTP_200_OK
)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Delete a customer.
    Admin only.
    """

    customer = (
        db.query(models.Customer)
        .filter(models.Customer.id == customer_id)
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    db.delete(customer)
    db.commit()

    return responses.MessageResponse(
        message="Customer deleted successfully"
    )