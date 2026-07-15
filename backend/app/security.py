from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import core as models
from app.schemas.core import TokenData

# ===================================================
# Password Hashing
# ===================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ===================================================
# OAuth2
# ===================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token"
)

# ===================================================
# Password Utilities
# ===================================================

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password
    )

# ===================================================
# JWT Creation
# ===================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = (
            datetime.now(timezone.utc)
            + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )

    to_encode.update(
        {
            "exp": expire
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt

# ===================================================
# JWT Decoder
# ===================================================

def decode_access_token(
    token: str
) -> TokenData:

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        username = payload.get("sub")
        user_id = payload.get("user_id")
        role = payload.get("role")

        if (
            username is None 
            or user_id is None 
            or role is None
        ):
            raise JWTError()

        return TokenData(
            username=username,
            user_id=user_id,
            role=role
        )

    except JWTError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )
    
# ===================================================
# Current Authenticated User
# ===================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    
    token_data = decode_access_token(token)
    
    user = (
        db.query(models.User)
        .filter(models.User.id == token_data.user_id)
        .first()
    )

    if user is None:
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

# ===================================================
# Admin Authorization
# ===================================================

def get_current_admin(
    current_user: models.User = Depends(get_current_user)
):

    if current_user.role != "admin":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required.",
        )

    return current_user