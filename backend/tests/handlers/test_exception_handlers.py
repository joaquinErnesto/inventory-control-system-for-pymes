from fastapi import FastAPI, HTTPException

from fastapi.exceptions import RequestValidationError

from fastapi.testclient import TestClient

from jose import JWTError

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.handlers import register_exception_handlers


def create_test_app():
    app = FastAPI()

    register_exception_handlers(app)

    return app


# ==================================================
# TESTS
# ==================================================

def test_http_400_handler():

    app = create_test_app()

    @app.get("/400")
    def endpoint():
        raise HTTPException(
            status_code=400,
            detail="Bad request."
        )

    client = TestClient(app)

    response = client.get("/400")

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Bad request."


def test_http_401_handler():

    app = create_test_app()

    @app.get("/401")
    def endpoint():
        raise HTTPException(
            status_code=401,
            detail="Unauthorized."
        )

    client = TestClient(app)

    response = client.get("/401")

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Unauthorized."


def test_http_403_handler():

    app = create_test_app()

    @app.get("/403")
    def endpoint():
        raise HTTPException(
            status_code=403,
            detail="Forbidden."
        )

    client = TestClient(app)

    response = client.get("/403")

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Forbidden."


def test_http_404_handler():

    app = create_test_app()

    @app.get("/404")
    def endpoint():
        raise HTTPException(
            status_code=404,
            detail="Resource not found."
        )

    client = TestClient(app)

    response = client.get("/404")

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Resource not found."


def test_validation_error_handler():

    app = create_test_app()

    @app.get("/items/{item_id}")
    def endpoint(item_id: int):
        return item_id

    client = TestClient(app)

    response = client.get("/items/not-an-int")

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False

    assert body["message"] == "Validation error."

    assert len(body["errors"]) > 0

    assert body["errors"][0]["field"] == "path -> item_id"


def test_jwt_error_handler():

    app = create_test_app()

    @app.get("/jwt")
    def endpoint():
        raise JWTError()

    client = TestClient(app)

    response = client.get("/jwt")

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Invalid authentication token."


def test_sqlalchemy_error_handler():

    app = create_test_app()

    @app.get("/database")
    def endpoint():
        raise SQLAlchemyError()

    client = TestClient(app)

    response = client.get("/database")

    assert response.status_code == 500

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "A database error occurred."


def test_unexpected_error_handler():

    app = FastAPI()

    register_exception_handlers(app)
    
    @app.get("/error")
    def endpoint():
        raise RuntimeError("Boom")

    client = TestClient(
        app,
        raise_server_exceptions=False
    )

    response = client.get("/error")

    assert response.status_code == 500

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Internal server error."