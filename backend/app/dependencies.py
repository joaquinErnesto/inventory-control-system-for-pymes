from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import core as models
from app.config import settings

# Points to the token URL we created in auth.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Decodes the JWT. If valid, fetches the user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
        
    return user


def require_admin(current_user: models.User = Depends(get_current_user)):
    """
    Middleware dependency that enforces the 'admin' role.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required."
        )
    return current_user