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

from app.utils.query_sorting import apply_sorting

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)

# ===================================================
# CREATE CATEGORY
# ===================================================

@router.post(
    "/",
    response_model=schemas.CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """
    Create a new category.

    Admin only.
    """

    existing_category = (
        db.query(models.Category)
        .filter(models.Category.name == category.name)
        .first()
    )

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this name already exists.",
        )

    new_category = models.Category(**category.model_dump())

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category


# ===================================================
# GET ALL CATEGORIES
# ===================================================

@router.get(
    "/",
    response_model=List[schemas.CategoryResponse],
)
def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    sort: str = "name",
    order: str = "asc"
):
    """
    Retrieve all categories.

    Admin and Employee.
    """
    
    allowed_sort_fields = {
        "name": models.Category.name,
    }

    query = db.query(models.Category)

    query = apply_sorting(
        query=query,
        sort=sort,
        order=order,
        allowed_fields=allowed_sort_fields,
    )

    categories = (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )

    return categories


# ===================================================
# GET CATEGORY BY ID
# ===================================================

@router.get(
    "/{category_id}",
    response_model=schemas.CategoryResponse,
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve one category by ID.

    Admin and Employee.
    """

    category = (
        db.query(models.Category)
        .filter(models.Category.id == category_id)
        .first()
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )

    return category


# ======================================================
# UPDATE CATEGORY
# ======================================================

@router.put(
    "/{category_id}",
    response_model=schemas.CategoryResponse,
)
def update_category(
    category_id: int,
    category_update: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """
    Update an existing category.

    Admin only.
    """

    category = (
        db.query(models.Category)
        .filter(models.Category.id == category_id)
        .first()
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )

    duplicate = (
        db.query(models.Category)
        .filter(
            models.Category.name == category_update.name,
            models.Category.id != category_id,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this name already exists.",
        )

    category.name = category_update.name
    category.description = category_update.description

    db.commit()
    db.refresh(category)

    return category


# ======================================================
# DELETE CATEGORY
# ======================================================

@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """
    Delete a category.

    Admin only.
    """

    category = (
        db.query(models.Category)
        .filter(models.Category.id == category_id)
        .first()
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )

    db.delete(category)
    db.commit()