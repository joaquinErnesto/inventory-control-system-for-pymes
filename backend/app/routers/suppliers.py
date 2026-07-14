from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.schemas import responses
from app.security import (
    get_current_admin,
    get_current_user,
)

from app.utils.query_sorting import apply_sorting
from app.utils.pagination import paginate

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)

# ==================================================
# CREATE SUPPLIER
# ==================================================

@router.post(
    "/",
    response_model=responses.SuccessMessageResponse[schemas.SupplierResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_supplier(
    supplier: schemas.SupplierCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """
    Register a new supplier.

    Admin only.
    """

    existing_supplier = (
        db.query(models.Supplier)
        .filter(models.Supplier.name == supplier.name)
        .first()
    )

    if existing_supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A supplier with this name already exists.",
        )

    new_supplier = models.Supplier(
        **supplier.model_dump()
    )

    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)

    return responses.SuccessMessageResponse(
        message="Supplier created successfully",
        data=new_supplier
    )


# ==================================================
# GET ALL SUPPLIERS
# ==================================================

@router.get(
    "/",
    response_model=responses.PaginatedResponse[List[schemas.SupplierResponse]]
)
def get_suppliers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    sort: str = "name",
    order: str = "asc"
):
    """
    Retrieve all suppliers.

    Admin and Employee.
    """

    allowed_sort_fields = {
        "name": models.Supplier.name,
        "created_at": models.Supplier.created_at
    }

    query = db.query(models.Supplier)

    query = apply_sorting(
        query=query,
        sort=sort,
        order=order,
        allowed_fields=allowed_sort_fields,
    )
    
    suppliers, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )
    
    return responses.PaginatedResponse(
        data=suppliers,
        pagination=pagination
    )


# ==================================================
# SEARCH SUPPLIERS
# ==================================================

@router.get(
    "/search/", 
    response_model=responses.PaginatedResponse[List[schemas.SupplierResponse]]
)
def search_suppliers(
    q: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search suppliers by company name,
    contact person, phone or email.
    """

    search = f"%{q}%"

    query = (
        db.query(models.Supplier)
        .filter(
            or_(
                models.Supplier.name.like(search),
                models.Supplier.contact_person.like(search),
                models.Supplier.phone.like(search),
                models.Supplier.email.like(search),
            )
        )
    )

    suppliers, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )
    
    return responses.PaginatedResponse(
        data=suppliers,
        pagination=pagination
    )


# ==================================================
# GET SUPPLIER BY ID
# ==================================================

@router.get(
    "/{supplier_id}",
    response_model=responses.SuccessResponse[schemas.SupplierResponse]
)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve one supplier by ID.

    Admin and Employee.
    """

    supplier = (
        db.query(models.Supplier)
        .filter(models.Supplier.id == supplier_id)
        .first()
    )

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    return responses.SuccessResponse(
        data=supplier
    )


# ==================================================
# UPDATE SUPPLIER
# ==================================================

@router.put(
    "/{supplier_id}",
    response_model=responses.SuccessMessageResponse[schemas.SupplierResponse]
)
def update_supplier(
    supplier_id: int,
    supplier_update: schemas.SupplierUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """
    Update an existing supplier.

    Admin only.
    """

    supplier = (
        db.query(models.Supplier)
        .filter(models.Supplier.id == supplier_id)
        .first()
    )

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    duplicate = (
        db.query(models.Supplier)
        .filter(
            models.Supplier.name == supplier_update.name,
            models.Supplier.id != supplier_id,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A supplier with this name already exists.",
        )

    supplier.name = supplier_update.name
    supplier.contact_person = supplier_update.contact_person
    supplier.phone = supplier_update.phone
    supplier.email = supplier_update.email
    supplier.address = supplier_update.address
    supplier.is_active = supplier_update.is_active

    db.commit()
    db.refresh(supplier)

    return responses.SuccessMessageResponse(
        message="Supplier updated successfully",
        data=supplier
    )


# ==================================================
# DELETE SUPPLIER
# ==================================================

@router.delete(
    "/{supplier_id}",
    response_model=responses.MessageResponse,
    status_code=status.HTTP_200_OK
)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """
    Delete a supplier.

    Admin only.
    """

    supplier = (
        db.query(models.Supplier)
        .filter(models.Supplier.id == supplier_id)
        .first()
    )

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    db.delete(supplier)
    db.commit()
    
    return responses.MessageResponse(
        message="Supplier deleted successfully"
    )