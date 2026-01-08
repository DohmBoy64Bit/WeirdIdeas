"""
Application configuration settings.
Loads from environment variables and .env file.
"""
from pydantic_settings import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    PROJECT_NAME: str = "DBZ MUD Framework"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./mud.db"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate random key if not set
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://localhost:3000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Database
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # Debug/Development
    DEBUG_MODE: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
