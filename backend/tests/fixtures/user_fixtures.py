import pytest

from app.models.core import User
from app.security import get_password_hash


# ==================================================
# ADMIN USER
# ==================================================

@pytest.fixture
def admin_user(db):
    """
    Creates an administrator user.
    """

    user = User(
        username="admin_test",
        password_hash=get_password_hash("admin123"),
        role="admin",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ==================================================
# EMPLOYEE USER
# ==================================================

@pytest.fixture
def employee_user(db):
    """
    Creates a regular employee.
    """

    user = User(
        username="employee_test",
        password_hash=get_password_hash("employee123"),
        role="employee",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user