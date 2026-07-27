from fastapi.testclient import TestClient

import pytest

from app.main import app
from app.database import get_db


# ==================================================
# DATABASE OVERRIDE
# ==================================================

def override_get_db(db):
    """
    Makes the API use the pytest database session
    instead of the application's real database session.
    """

    def _override():
        yield db

    return _override


# ==================================================
# TEST CLIENT
# ==================================================

@pytest.fixture
def client(db):
    """
    FastAPI TestClient using the test database.
    """

    app.dependency_overrides[get_db] = override_get_db(db)

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ==================================================
# ADMIN TOKEN
# ==================================================

@pytest.fixture
def admin_token(
    client,
    admin_user,
):
    """
    Returns a JWT token for an administrator.
    """

    response = client.post(
        "/api/v1/token",
        data={
            "username": "admin_test",
            "password": "admin123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


# ==================================================
# EMPLOYEE TOKEN
# ==================================================

@pytest.fixture
def employee_token(
    client,
    employee_user,
):
    """
    Returns a JWT token for an employee.
    """

    response = client.post(
        "/api/v1/token",
        data={
            "username": "employee_test",
            "password": "employee123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


# ==================================================
# ADMIN HEADERS
# ==================================================

@pytest.fixture
def admin_headers(admin_token):
    """
    Authorization headers for an administrator.
    """

    return {
        "Authorization": f"Bearer {admin_token}"
    }


# ==================================================
# EMPLOYEE HEADERS
# ==================================================

@pytest.fixture
def employee_headers(employee_token):
    """
    Authorization headers for an employee.
    """

    return {
        "Authorization": f"Bearer {employee_token}"
    }