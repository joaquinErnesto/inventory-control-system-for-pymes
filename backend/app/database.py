from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Create the SQLAlchemy engine pointing to your custom Docker port (4800)
engine = create_engine(settings.DATABASE_URL)

# 2. Create a SessionLocal class. Each instance will be a distinct database session.
# autocommit=False ensures transactions are only saved when you explicitly type db.commit()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Create a Base class. Our database models will inherit from this to map to Postgres tables.
Base = declarative_base()

# Dependency utility function to yield database sessions to our endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()