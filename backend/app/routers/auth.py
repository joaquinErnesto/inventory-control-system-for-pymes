from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import core as models
from app.schemas import core as schemas
from app.schemas import responses
from app.security import verify_password, create_access_token

router = APIRouter(tags=["Authentication"])


# ==================================================
# LOGIN AND TOKEN GENERATION
# ==================================================

@router.post(
    "/token",
    response_model=responses.SuccessResponse[schemas.Token]
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return a JWT access token.
    """

    # Search user
    user = (
        db.query(models.User)
        .filter(models.User.username == form_data.username)
        .first()
    )

    # Validate credentials
    if not user or not verify_password(
        form_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        }
    )

    return responses.SuccessResponse(
        message="Authentication successful",
        data=schemas.Token(
            access_token=access_token, 
            token_type="bearer"
        )
    )