from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from jose import JWTError

from sqlalchemy.exc import SQLAlchemyError

from app.logging.logger import logger
from app.schemas import responses

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
            content=responses.ErrorResponse(
                message=str(exc.detail)
            ).model_dump()
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

        errors = []

        for error in exc.errors():

            field = " -> ".join(
                str(item)
                for item in error["loc"]
            )

            errors.append(
                responses.ValidationErrorDetail(
                    field=field,
                    message=error["msg"]
                )
            )
            
        return JSONResponse(
            status_code=422,
            content=responses.ValidationErrorResponse(
                message="Validation error.",
                errors=errors
            ).model_dump()
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
            content=responses.ErrorResponse(
                message="Invalid authentication token."
            ).model_dump()
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
            content=responses.ErrorResponse(
                message="A database error occurred."
            ).model_dump()
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
            content=responses.ErrorResponse(
                message="Internal server error."
            ).model_dump()
        )