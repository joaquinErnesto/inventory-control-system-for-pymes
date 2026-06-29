from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.security import get_password_hash

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (Admin or Employee).
    """
    # 1. Check if username is already taken
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username is already taken.")
    
    # 2. Hash the password securely using bcrypt
    hashed_password = get_password_hash(user.password)
    
    # 3. Create the SQLAlchemy model instance
    new_user = models.User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role
    )
    
    # 4. Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.get("/", response_model=List[schemas.UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all registered users.
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users