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

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# ==================================================
# CREATE USER
# ==================================================

@router.post(
    "/",
    response_model=responses.SuccessMessageResponse[schemas.UserResponse],
    status_code=status.HTTP_201_CREATED
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
    response_model=responses.SuccessResponse[List[schemas.UserResponse]]
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

    users = (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )

    return responses.SuccessResponse(
        data=users
    )


# ==================================================
# GET CURRENT AUTHENTICATED USER
# ==================================================

@router.get(
    "/me",
    response_model=responses.SuccessResponse[schemas.UserResponse]
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
    response_model=responses.SuccessResponse[schemas.UserResponse]
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
    response_model=responses.SuccessResponse[List[schemas.UserResponse]]
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

    users = (
        db.query(models.User)
        .filter(
            models.User.username.ilike(f"%{q}%")
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return responses.SuccessResponse(
        data=users
    )


# ==================================================
# UPDATE USER BY ID
# ==================================================

@router.put(
    "/{user_id}",
    response_model=responses.SuccessMessageResponse[schemas.UserResponse]
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
    response_model=responses.MessageResponse,
    status_code=status.HTTP_200_OK
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
    response_model=responses.MessageResponse,
    status_code=status.HTTP_200_OK
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