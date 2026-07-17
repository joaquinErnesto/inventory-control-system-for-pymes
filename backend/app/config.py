import os
from dotenv import load_dotenv
from typing import Final

# Load the .env file from the root directory
load_dotenv()

class Settings:
    
    API_PREFIX: Final[str] = "/api/v1"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-fallback-super-secret-key-for-dev")
    
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