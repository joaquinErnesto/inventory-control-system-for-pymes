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
    summary="Create customer",
    description=(
        "Registers a new customer in the system. "
        "If an identification number is provided, it must be unique. "
        "Only administrators can create customers."
    ),
    response_model=responses.SuccessMessageResponse[schemas.CustomerResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Customer created successfully."
        },
        400: {
            "description": "A customer with the provided identification number already exists."
        },
        401: {
            "description": "Authentication required."
        },
        403: {
            "description": "Administrator privileges required."
        },
    },
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
    summary="List customers",
    description=(
        "Returns a paginated list of registered customers. "
        "Results can be sorted by customer name or creation date."
    ),
    response_model=responses.PaginatedResponse[List[schemas.CustomerResponse]],
    responses={
        200: {
            "description": "Customers retrieved successfully."
        },
        401: {
            "description": "Authentication required."
        },
    },
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
    summary="Search customers",
    description=(
        "Searches customers by name, identification number, "
        "phone number, or email address. "
        "Results are returned using pagination."
    ),
    response_model=responses.PaginatedResponse[List[schemas.CustomerResponse]],
    responses={
        200: {
            "description": "Search completed successfully."
        },
        401: {
            "description": "Authentication required."
        },
    },
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
    summary="Get customer by ID",
    description=(
        "Returns the complete information of a specific customer."
    ),
    response_model=responses.SuccessResponse[schemas.CustomerResponse],
    responses={
        200: {
            "description": "Customer retrieved successfully."
        },
        401: {
            "description": "Authentication required."
        },
        404: {
            "description": "Customer not found."
        },
    },
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
    summary="Update customer",
    description=(
        "Updates an existing customer's information. "
        "If the identification number is modified, it must remain unique. "
        "Only administrators can update customer records."
    ),
    response_model=responses.SuccessMessageResponse[schemas.CustomerResponse],
    responses={
        200: {
            "description": "Customer updated successfully."
        },
        400: {
            "description": "The identification number already belongs to another customer."
        },
        401: {
            "description": "Authentication required."
        },
        403: {
            "description": "Administrator privileges required."
        },
        404: {
            "description": "Customer not found."
        },
    },
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
    summary="Delete customer",
    description=(
        "Deletes a customer from the system. "
        "Only administrators can perform this operation."
    ),
    response_model=responses.MessageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Customer deleted successfully."
        },
        401: {
            "description": "Authentication required."
        },
        403: {
            "description": "Administrator privileges required."
        },
        404: {
            "description": "Customer not found."
        },
    },
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