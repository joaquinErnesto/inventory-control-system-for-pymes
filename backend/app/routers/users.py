from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.security import (
    get_password_hash,
    get_current_admin
)

from app.utils.query_sorting import apply_sorting

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# ==================================================
# CREATE USERS
# ==================================================

@router.post(
    "/",
    response_model=schemas.UserResponse,
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

    return new_user


# ==================================================
# GET USERS
# ==================================================

@router.get(
    "/",
    response_model=List[schemas.UserResponse]
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

    return users