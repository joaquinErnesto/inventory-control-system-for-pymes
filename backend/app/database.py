from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings  # This line fixes your error!

# 1. Create the SQLAlchemy engine pointing to your MySQL Docker container
engine = create_engine(settings.DATABASE_URL)

# 2. Create a SessionLocal class. Each instance will be a distinct database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Create a Base class. Our database models will inherit from this.
Base = declarative_base()

# Dependency utility function to yield database sessions to our endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()