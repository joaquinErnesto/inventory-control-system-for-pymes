from typing import List, Annotated

from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    Path,
    Query,
    status
)

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
    summary="Create supplier",
    description="Registers a new supplier. Only administrators can perform this operation.",
    response_model=responses.SuccessMessageResponse[schemas.SupplierResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Supplier created successfully"},
        400: {"description": "Supplier already exists"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
    },
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
    summary="List suppliers",
    description="Returns a paginated list of all suppliers with optional sorting.",
    response_model=responses.PaginatedResponse[List[schemas.SupplierResponse]],
    responses={
        200: {"description": "Suppliers retrieved successfully"},
        401: {"description": "Authentication required"},
    },
)
def get_all_suppliers(
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
    current_user=Depends(get_current_user),
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
    ] = "asc"
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
    summary="Search suppliers",
    description="Search suppliers by company name, contact person, phone number, or email address.",
    response_model=responses.PaginatedResponse[List[schemas.SupplierResponse]],
    responses={
        200: {"description": "Search completed successfully"},
        401: {"description": "Authentication required"},
    },
)
def search_suppliers(
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
            le=100,
            description="Maximum number of records to return."
        )
    ] = 100,
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
    summary="Get supplier by ID",
    description="Returns the details of a specific supplier.",
    response_model=responses.SuccessResponse[schemas.SupplierResponse],
    responses={
        200: {"description": "Supplier retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Supplier not found"},
    },
)
def get_supplier(
    supplier_id: Annotated[
        int,
        Path(
            gt=0,
            description="Supplier ID"
        )
    ],
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
    summary="Update supplier",
    description="Updates an existing supplier. Only administrators can perform this operation.",
    response_model=responses.SuccessMessageResponse[schemas.SupplierResponse],
    responses={
        200: {"description": "Supplier updated successfully"},
        400: {"description": "Supplier already exists"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
        404: {"description": "Supplier not found"},
    },
)
def update_supplier(
    supplier_id: Annotated[
        int,
        Path(
            gt=0,
            description="Supplier ID"
        )
    ],
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
    summary="Delete supplier",
    description="Deletes a supplier. Only administrators can perform this operation.",
    response_model=responses.MessageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Supplier deleted successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
        404: {"description": "Supplier not found"},
    },
)
def delete_supplier(
    supplier_id: Annotated[
        int,
        Path(
            gt=0,
            description="Supplier ID"
        )
    ],
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