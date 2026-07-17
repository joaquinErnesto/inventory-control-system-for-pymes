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
    summary="Authenticate user",
    description=(
        "Authenticates a user using a username and password. "
        "If the credentials are valid, a JWT access token is returned. "
        "The token must be included in the Authorization header "
        "using the Bearer scheme when accessing protected endpoints."
    ),
    response_model=schemas.Token,
    responses={
        200: {
            "description": "Authentication successful. JWT access token generated."
        },
        401: {
            "description": "Invalid username or password."
        },
        422: {
            "description": "Validation error. Required form fields are missing or invalid."
        },
    },
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

    return schemas.Token(
        access_token=access_token,
        token_type="bearer"
    )