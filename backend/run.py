#!/usr/bin/env python3
"""
SceneForge Backend - Development server runner.
Production-ready startup with proper error handling.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def get_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def setup_environment() -> dict:
    """
    Load and validate environment configuration.
    Does NOT mutate os.environ.
    """
    env = get_env("ENVIRONMENT", "development").lower()
    debug = get_env("DEBUG", "true").lower() == "true"

    config = {
        "ENVIRONMENT": env,
        "DEBUG": debug,
        "DATABASE_URL": get_env(
            "DATABASE_URL",
            "sqlite:///./sceneforge.db" if env == "development" else None,
        ),
        "SECRET_KEY": get_env("SECRET_KEY"),
        "BRIA_API_KEY": get_env("BRIA_API_KEY"),
        "GOOGLE_API_KEY": get_env("GOOGLE_API_KEY"),
    }

    # ---- VALIDATION ----
    if not config["DATABASE_URL"]:
        raise RuntimeError("DATABASE_URL is required")

    if env == "production":
        if not config["SECRET_KEY"] or len(config["SECRET_KEY"]) < 32:
            raise RuntimeError("SECRET_KEY must be set and at least 32 characters in production")

        if not config["BRIA_API_KEY"]:
            raise RuntimeError("BRIA_API_KEY is required in production")

        if not config["GOOGLE_API_KEY"]:
            raise RuntimeError("GOOGLE_API_KEY is required in production")
    else:
        if not config["BRIA_API_KEY"]:
            print("⚠️ BRIA_API_KEY not set. Using mock image generation")

        if not config["GOOGLE_API_KEY"]:
            print("⚠️ GOOGLE_API_KEY not set. Using mock AI agents")

    return config


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import langchain
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    print("🎬 SceneForge Backend - Agentic Pre-Vis Pipeline")
    print("=" * 50)
    
    
    # setup_environment()
    CONFIG = setup_environment()

    print(f"Config {CONFIG}")
    if not CONFIG["BRIA_API_KEY"]:
        print("⚠️  Warning: BRIA_API_KEY not set. Using mock responses for image generation.")

    if not CONFIG["GOOGLE_API_KEY"]:
        print("⚠️  Warning: GOOGLE_API_KEY not set. Using mock responses for AI agents.")


    
    if not check_dependencies():
        sys.exit(1)
    
    try:
        
        import uvicorn
        from app.core.config import settings
        
        print(f"🚀 Starting SceneForge Backend v{settings.APP_VERSION}")
        print(f"🌍 Environment: {settings.ENVIRONMENT}")
        print(f"🗄️  Database: {settings.DATABASE_URL}")
        print(f"📁 Upload Directory: {settings.UPLOAD_DIR}")
        print(f"📡 API Docs: http://localhost:8000/docs")
        print(f"🔍 Health Check: http://localhost:8000/health")
        print(f"🎯 Root Endpoint: http://localhost:8000/")
        print("=" * 50)
        
        
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.DEBUG,
            log_level="info",
            access_log=True,
        )
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)