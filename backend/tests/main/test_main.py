from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db

client = TestClient(app)


# ==================================================
# ROOT
# ==================================================

def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Welcome to the Inventory Control API"


# ==================================================
# DATABASE HEALTH (SUCCESS)
# ==================================================

def test_database_health_success():

    mock_db = MagicMock()

    mock_db.execute.return_value = None

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/health/db")

    app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Database connection is live and healthy!"


# ==================================================
# DATABASE HEALTH (FAILURE)
# ==================================================

def test_database_health_failure():

    mock_db = MagicMock()

    mock_db.execute.side_effect = Exception("Connection lost")

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/health/db")

    app.dependency_overrides.clear()

    assert response.status_code == 500

    body = response.json()

    assert body["success"] is False
    assert "Database connection failed" in body["message"]


# ==================================================
# OPENAPI
# ==================================================

def test_openapi_schema_exists():

    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    assert schema["info"]["title"] == "Inventory Control MVP API"
    assert schema["info"]["version"] == "1.0.0"


# ==================================================
# DOCS
# ==================================================

def test_docs_endpoint():

    response = client.get("/docs")

    assert response.status_code == 200

    assert "text/html" in response.headers["content-type"]


# ==================================================
# REDOC
# ==================================================

def test_redoc_endpoint():

    response = client.get("/redoc")

    assert response.status_code == 200

    assert "text/html" in response.headers["content-type"]