from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.schemas import responses
from app.security import (
    get_password_hash,
    get_current_admin,
    get_current_user
)

from app.utils.query_sorting import apply_sorting
from app.utils.pagination import paginate

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# ==================================================
# CREATE USER
# ==================================================

@router.post(
    "/",
    summary="Create user",
    description="Creates a new system user with a securely hashed password. Only administrators can create user accounts.",
    response_model=responses.SuccessMessageResponse[schemas.UserResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Username already exists"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
    },
)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """
    Register a new user.
    Only administrators are allowed to create users.
    """

    existing_user = (
        db.query(models.User)
        .filter(models.User.username == user.username)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username is already taken."
        )

    hashed_password = get_password_hash(user.password)

    new_user = models.User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return responses.SuccessMessageResponse(
        message="User created successfully",
        data=new_user
    )


# ==================================================
# GET USERS
# ==================================================

@router.get(
    "/",
    summary="List users",
    description="Returns a paginated list of all registered users with optional sorting. Only administrators can access this endpoint.",
    response_model=responses.PaginatedResponse[List[schemas.UserResponse]],
    responses={
        200: {"description": "Users retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
    },
)
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin),
    sort: str = "created_at",
    order: str = "desc"
):
    """
    Retrieve all registered users.
    Only administrators are allowed to access this endpoint.
    """

    allowed_sort_fields = {
        "username": models.User.username,
        "created_at": models.User.created_at,
    }

    query = db.query(models.User)

    query = apply_sorting(
        query=query,
        sort=sort,
        order=order,
        allowed_fields=allowed_sort_fields,
    )

    users, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )

    return responses.PaginatedResponse(
        data=users,
        pagination=pagination
    )


# ==================================================
# GET CURRENT AUTHENTICATED USER
# ==================================================

@router.get(
    "/me",
    summary="Get current user",
    description="Returns the currently authenticated user's profile. This endpoint is typically used by the frontend immediately after login to restore the user session.",
    response_model=responses.SuccessResponse[schemas.UserResponse],
    responses={
        200: {"description": "Current user retrieved successfully"},
        401: {"description": "Authentication required"},
    },
)
def get_current_authenticated_user(
    current_user: models.User = Depends(get_current_user),
):
    """
    Returns the currently authenticated user.

    This endpoint is used by the frontend after login
    to identify the logged-in user.
    """

    return responses.SuccessResponse(
        data=current_user
    )


# ==================================================
# GET USER BY ID
# ==================================================

@router.get(
    "/{user_id}",
    summary="Get user by ID",
    description="Returns the information of a specific user. Only administrators can access this endpoint.",
    response_model=responses.SuccessResponse[schemas.UserResponse],
    responses={
        200: {"description": "User retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
        404: {"description": "User not found"},
    },
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """
    Retrieve one user by ID.
    """

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    return responses.SuccessResponse(
        data=user
    )


# ==================================================
# SEARCH USER
# ==================================================

@router.get(
    "/search",
    summary="Search users",
    description="Searches users by username. Results are returned using pagination. Only administrators can access this endpoint.",
    response_model=responses.PaginatedResponse[List[schemas.UserResponse]],
    responses={
        200: {"description": "Search completed successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
    },
)
def search_users(
    q: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin),
):
    """
    Search users by username.
    """

    query = (
        db.query(models.User)
        .filter(
            models.User.username.ilike(f"%{q}%")
        )
    )
    
    users, pagination = paginate(
        query=query,
        skip=skip,
        limit=limit
    )

    return responses.PaginatedResponse(
        data=users,
        pagination=pagination
    )


# ==================================================
# UPDATE USER BY ID
# ==================================================

@router.put(
    "/{user_id}",
    summary="Update user",
    description="Updates a user's username and role. Usernames must remain unique. Only administrators can perform this operation.",
    response_model=responses.SuccessMessageResponse[schemas.UserResponse],
    responses={
        200: {"description": "User updated successfully"},
        400: {"description": "Username already exists"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
        404: {"description": "User not found"},
    },
)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """
    Update username and role.
    """

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    duplicate = (
        db.query(models.User)
        .filter(
            models.User.username == user_update.username,
            models.User.id != user_id
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=400,
            detail="Username already exists."
        )

    user.username = user_update.username
    user.role = user_update.role

    db.commit()
    db.refresh(user)

    return responses.SuccessMessageResponse(
        message="User updated successfully",
        data=user
    )


# ==================================================
# CHANGE USER PASSWORD
# ==================================================

@router.put(
    "/{user_id}/password",
    summary="Change user password",
    description="Updates a user's password using secure password hashing. Only administrators can change another user's password.",
    response_model=responses.MessageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Password updated successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
        404: {"description": "User not found"},
    },
)
def change_password(
    user_id: int,
    password_update: schemas.UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """
    Change a user's password.
    """

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    user.password_hash = get_password_hash(
        password_update.password
    )

    db.commit()

    return responses.MessageResponse(
        message="Password updated successfully"
    )
    

# ==================================================
# DELETE USER
# ==================================================

@router.delete(
    "/{user_id}",
    summary="Delete user",
    description="Deletes a user account. Users that have related sales, inventory batches, loss logs, or inventory transactions cannot be deleted. Only administrators can perform this operation.",
    response_model=responses.MessageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "User deleted successfully"},
        400: {"description": "User has related records and cannot be deleted"},
        401: {"description": "Authentication required"},
        403: {"description": "Administrator privileges required"},
        404: {"description": "User not found"},
    },
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """
    Delete a user.
    """

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    if user.sales:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a user with registered sales."
        )

    if user.batches_created:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a user that created inventory batches."
        )

    if user.losses_logged:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a user with registered losses."
        )

    if user.transactions:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a user with inventory transactions."
        )

    db.delete(user)

    db.commit()
    
    return responses.MessageResponse(
        message="User deleted successfully"
    )