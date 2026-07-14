from typing import List, Annotated

from fastapi import (
    APIRouter, 
    Depends, 
    status,
    Path,
    Query,
    HTTPException
)

from sqlalchemy.orm import Session

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
    prefix="/categories",
    tags=["Categories"],
)

# ===================================================
# CREATE CATEGORY
# ===================================================

@router.post(
    "/",
    summary="Create category",
    description="Creates a new product category. Only administrators can perform this operation.",
    response_model=responses.SuccessMessageResponse[schemas.CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Category created successfully"},
        400: {"description": "Category already exists"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
    },
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

    return responses.SuccessMessageResponse(
        message="Category created successfully",
        data=new_category
    )


# ===================================================
# GET ALL CATEGORIES
# ===================================================

@router.get(
    "/",
    summary="List categories",
    description="Returns a paginated list of all product categories with optional sorting.",
    response_model=responses.PaginatedResponse[List[schemas.CategoryResponse]],
    responses={
        200: {"description": "Categories retrieved successfully"},
        401: {"description": "Authentication required"},
    },
)
def get_categories(
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
    ] = "asc",
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
    
    categories, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )
    
    return responses.PaginatedResponse(
        data=categories,
        pagination=pagination
    )


# ===================================================
# GET CATEGORY BY ID
# ===================================================

@router.get(
    "/{category_id}",
    summary="Get category by ID",
    description="Returns the details of a specific category.",
    response_model=responses.SuccessResponse[schemas.CategoryResponse],
    responses={
        200: {"description": "Category retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Category not found"},
    },
)
def get_category(
    category_id: Annotated[
        int,
        Path(
            gt=0,
            description="Unique identifier of the category"
        )
    ],
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

    return responses.SuccessResponse(
        data=category
    )


# ====================================================
# UPDATE CATEGORY
# ====================================================

@router.put(
    "/{category_id}",
    summary="Update category",
    description="Updates an existing category. Only administrators can perform this operation.",
    response_model=responses.SuccessMessageResponse[schemas.CategoryResponse],
    responses={
        200: {"description": "Category updated successfully"},
        400: {"description": "Duplicate category name"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
        404: {"description": "Category not found"},
    },
)
def update_category(
    category_id: Annotated[
        int,
        Path(
            gt=0,
            description="Unique identifier of the category to update."
        )
    ],
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

    return responses.SuccessMessageResponse(
        message="Category updated successfully",
        data=category
    )


# ====================================================
# DELETE CATEGORY
# ====================================================

@router.delete(
    "/{category_id}",
    summary="Delete category",
    description="Deletes a category. Only administrators can perform this operation.",
    response_model=responses.MessageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Category deleted successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
        404: {"description": "Category not found"},
    },
)
def delete_category(
    category_id: Annotated[
        int,
        Path(
            gt=0,
            description="Unique identifier of the category to delete."
        )
    ],
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
    
    return responses.MessageResponse(
        message="Category deleted successfully"
    )