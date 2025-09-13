# src/core/config.py
import os
from typing import Optional

class Settings:
    PROJECT_NAME: str = "Gemini Backend Clone - Kuvaka Tech"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_super_secret_key_here_123!")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

settings = Settings()