from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import engine, Base, get_db
from app.models import core
from app.routers import categories, suppliers, products, users, inventory_batches, customers, sales, loss_logs, reports

# This command tells SQLAlchemy to create the tables if they don't exist.
# (Since you already created them in Navicat, this just safely verifies them).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Inventory Control MVP API",
    description="Backend API for the Baracoa Inventory Control System",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Inventory Control API"}

@app.get("/health/db")
def check_db_health(db: Session = Depends(get_db)):
    """
    Test endpoint to verify the database connection is active.
    """
    try:
        # Run a simple query to ensure the database responds
        db.execute(text("SELECT 1"))
        return {"status": "success", "message": "Database connection is live and healthy!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Connect the routers to the main application    
app.include_router(categories.router)
app.include_router(suppliers.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(inventory_batches.router)
app.include_router(customers.router)
app.include_router(sales.router)
app.include_router(loss_logs.router)
app.include_router(reports.router)