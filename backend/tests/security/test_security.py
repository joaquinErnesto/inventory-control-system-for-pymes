import pytest

from fastapi import HTTPException

from datetime import timedelta

from app.security import create_access_token
from app.security import decode_access_token

from app.security import get_current_user


def test_create_access_token_custom_expiration():
    token = create_access_token(
        {
            "sub": "admin",
            "user_id": 1,
            "role": "admin",
        },
        expires_delta=timedelta(minutes=5),
    )

    payload = decode_access_token(token)

    assert payload.username == "admin"
    assert payload.user_id == 1
    assert payload.role == "admin"


def test_get_current_admin_success(admin_user):
    from app.security import get_current_admin

    returned = get_current_admin(admin_user)

    assert returned.id == admin_user.id


def test_get_current_user_missing_database_user(
    db,
    admin_user,
    admin_token,
):
    """
    A valid JWT should become invalid if the corresponding
    user no longer exists in the database.
    """

    #
    # Delete the authenticated user.
    #
    db.delete(admin_user)
    db.commit()

    #
    # Authentication must now fail.
    #
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token=admin_token,
            db=db,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials."
    assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"