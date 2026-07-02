from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.security import (
    get_current_admin,
    get_current_user,
)

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)

# ==================================================
# CREATE SUPPLIER
# ==================================================

@router.post(
    "/",
    response_model=schemas.SupplierResponse,
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

    return new_supplier


# ==================================================
# GET ALL SUPPLIERS
# ==================================================

@router.get(
    "/",
    response_model=List[schemas.SupplierResponse],
)
def get_suppliers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve all suppliers.

    Admin and Employee.
    """

    return (
        db.query(models.Supplier)
        .offset(skip)
        .limit(limit)
        .all()
    )


# ==================================================
# GET SUPPLIER BY ID
# ==================================================

@router.get(
    "/{supplier_id}",
    response_model=schemas.SupplierResponse,
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

    return supplier


# ==================================================
# UPDATE SUPPLIER
# ==================================================

@router.put(
    "/{supplier_id}",
    response_model=schemas.SupplierResponse,
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

    return supplier


# ==================================================
# DELETE SUPPLIER
# ==================================================

@router.delete(
    "/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
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