import os
from dotenv import load_dotenv

# Load the .env file from the root directory
load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # --- JWT Security Settings ---
    # In production, ensure SECRET_KEY is loaded from your .env file
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-fallback-super-secret-key-for-dev")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()