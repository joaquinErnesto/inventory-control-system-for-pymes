import os
from dotenv import load_dotenv

# Load the .env file from the root directory
load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")

settings = Settings()