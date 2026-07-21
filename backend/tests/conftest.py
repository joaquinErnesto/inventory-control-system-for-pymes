import os

os.environ["ENV_FILE"] = ".env.test"

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base


# ==================================================
# TEST DATABASE ENGINE
# ==================================================

engine = create_engine(
    settings.DATABASE_URL
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ==================================================
# DATABASE SESSION FIXTURE
# ==================================================

@pytest.fixture
def db():
    """
    Creates a clean database for every test and
    provides an isolated SQLAlchemy session.
    """

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()

    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def session(db):
    return db