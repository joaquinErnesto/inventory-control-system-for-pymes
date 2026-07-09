from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from jose import JWTError

from sqlalchemy.exc import SQLAlchemyError

from app.logging.logger import logger

def register_exception_handlers(app: FastAPI):
    """
    Register all global exception handlers.
    """

    # ==========================================
    # HTTP Exceptions
    # ==========================================

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException
    ):
        logger.warning(
            f"{request.method} {request.url.path} | "
            f"{exc.status_code} | "
            f"{exc.detail}"
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail
            }
        )

    # ==========================================
    # Validation Errors
    # ==========================================

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ):
        logger.warning(
            f"{request.method} {request.url.path} | Validation Error | {exc.errors()}"
        )

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation error.",
                "errors": exc.errors()
            }
        )

    # ==========================================
    # JWT Errors
    # ==========================================

    @app.exception_handler(JWTError)
    async def jwt_exception_handler(
        request: Request,
        exc: JWTError
    ):
        logger.warning(
            f"{request.method} {request.url.path} | Invalid JWT"
        )

        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": "Invalid authentication token."
            }
        )

    # ==========================================
    # Database Errors
    # ==========================================

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request,
        exc: SQLAlchemyError
    ):
        logger.exception(
            f"{request.method} {request.url.path} | Database Error"
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "A database error occurred."
            }
        )

    # ==========================================
    # Unknown Errors
    # ==========================================

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception
    ):
        logger.exception(
            f"{request.method} {request.url.path} | Unexpected Error"
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error."
            }
        )