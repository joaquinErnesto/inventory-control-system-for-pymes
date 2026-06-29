from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import core as models
from app.security import verify_password, create_access_token

router = APIRouter(tags=["Authentication"])

@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Find the user by username
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    # Verify user exists and password matches the bcrypt hash
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Generate the JWT, injecting both username and role into the payload
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    
    # FastAPI requires this exact JSON structure for OAuth2 compatibility
    return {"access_token": access_token, "token_type": "bearer"}