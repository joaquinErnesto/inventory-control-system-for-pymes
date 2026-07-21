import os
from dotenv import load_dotenv
from typing import Final

ENV_FILE = os.getenv("ENV_FILE", ".env")
load_dotenv(ENV_FILE)

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError(
        "DATABASE_URL environment variable is not configured."
    )

SECRET_KEY = os.getenv("SECRET_KEY")

if SECRET_KEY is None:
    raise RuntimeError(
        "SECRET_KEY environment variable is not configured."
    )
        
class Settings:
    
    API_PREFIX: Final[str] = "/api/v1"
    
    DATABASE_URL: Final[str] = DATABASE_URL
    
    SECRET_KEY: Final[str] = SECRET_KEY
    
    CORS_ORIGINS: list[str] = [
        origin.strip()
        
        for origin in os.getenv(
            "CORS_ORIGINS",
            ""
        ).split(",")
        
        if origin.strip()
    ]
    
    ALGORITHM: Final[str] = "HS256"
    
    ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 30

settings = Settings()