from time import perf_counter

from fastapi import FastAPI, Depends, HTTPException, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import engine, Base, get_db
from app.routers import (
    auth,
    categories,
    suppliers,
    products,
    users,
    inventory_batches,
    customers,
    sales,
    loss_logs,
    reports,
    inventory_transactions,
)
from app.exceptions.handlers import register_exception_handlers
from app.logging.logger import logger
from app.schemas import responses
from app.config import settings

# ==================================================
# CREATE DATABASE TABLES
# ==================================================

Base.metadata.create_all(bind=engine)

# ==================================================
# FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="Inventory Control MVP API",
    description="Backend API for the Baracoa Inventory Control System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):

    start = perf_counter()

    logger.info(
        f"Request started | "
        f"{request.method} "
        f"{request.url.path}"
    )

    response = await call_next(request)

    elapsed = perf_counter() - start

    logger.info(
        f"Request finished | "
        f"{request.method} "
        f"{request.url.path} | "
        f"Status {response.status_code} | "
        f"{elapsed:.3f}s"
    )

    return response

register_exception_handlers(app)


# ==================================================
# ROOT
# ==================================================

@app.get(
    "/",
    response_model=responses.MessageResponse
)
def read_root():
    return responses.MessageResponse(
        message="Welcome to the Inventory Control API"
    )


# ==================================================
# DATABASE HEALTH
# ==================================================

@app.get(
    "/health/db",
    response_model=responses.MessageResponse
)
def check_db_health(
    db: Session = Depends(get_db)
):
    """
    Test endpoint to verify the database connection is active.
    """

    try:

        db.execute(text("SELECT 1"))

        return responses.MessageResponse(
            message="Database connection is live and healthy!"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )

# ==================================================
# ROUTERS
# ==================================================

api_router = APIRouter(prefix=settings.API_PREFIX)

api_router.include_router(auth.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(suppliers.router)
api_router.include_router(users.router)
api_router.include_router(inventory_batches.router)
api_router.include_router(customers.router)
api_router.include_router(sales.router)
api_router.include_router(loss_logs.router)
api_router.include_router(reports.router)
api_router.include_router(inventory_transactions.router)

app.include_router(api_router)