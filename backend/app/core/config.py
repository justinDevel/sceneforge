"""
Core configuration settings for SceneForge backend.
Production-ready configuration with environment-based settings.
"""

import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "SceneForge Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(default="", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:8081", "http://127.0.0.1:8081"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If not valid JSON, treat as single origin
                return [v]
        return v
    
    # Database (SQLite for simplicity)
    DATABASE_URL: str = Field(default="sqlite:///./sceneforge.db", env="DATABASE_URL")
    
    # Bria AI V2 Configuration
    BRIA_API_KEY: str = Field(default="", env="BRIA_API_KEY")
    BRIA_BASE_URL: str = Field(
        default="https://engine.prod.bria-api.com", 
        env="BRIA_BASE_URL"
    )
    BRIA_API_VERSION: str = Field(default="v2", env="BRIA_API_VERSION")
    
    # Google Gemini Configuration (for agents)
    GOOGLE_API_KEY: str = Field(default="", env="GOOGLE_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash-latest", env="GEMINI_MODEL")
    
    # File Storage
    UPLOAD_DIR: str = Field(default="./uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    
    # Monitoring
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Generation Settings
    MAX_FRAMES_PER_SCENE: int = Field(default=20, env="MAX_FRAMES_PER_SCENE")
    DEFAULT_FRAME_COUNT: int = Field(default=6, env="DEFAULT_FRAME_COUNT")
    GENERATION_TIMEOUT: int = Field(default=300, env="GENERATION_TIMEOUT")  # 5 minutes
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is provided and secure."""
        if not v:
            # Generate a default secret key for development
            import secrets
            return secrets.token_urlsafe(32)
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()