import uuid

import pytest

from app.models.core import User
from app.security import get_password_hash


# ==================================================
# USER FACTORY
# ==================================================

@pytest.fixture
def user_factory(db):
    """
    Factory fixture for creating users.

    Examples:

        admin = user_factory(
            username="admin",
            role="admin"
        )

        employee = user_factory(
            username="employee",
            role="employee"
        )
    """

    def factory(
        username: str | None = None,
        password: str = "password123",
        role: str = "employee",
    ) -> User:

        if username is None :
            username = f"test_user_{uuid.uuid4().hex}"
            
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role=role,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    return factory


# ==================================================
# DEFAULT ADMIN USER
# ==================================================

@pytest.fixture
def admin_user(user_factory):
    """
    Creates a default administrator.
    """

    return user_factory(
        username="admin_test",
        password="admin123",
        role="admin",
    )


# ==================================================
# DEFAULT EMPLOYEE USER
# ==================================================

@pytest.fixture
def employee_user(user_factory):
    """
    Creates a default employee.
    """

    return user_factory(
        username="employee_test",
        password="employee123",
        role="employee",
    )