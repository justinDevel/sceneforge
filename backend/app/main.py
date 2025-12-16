"""
SceneForge Backend - Main FastAPI application.
Production-ready backend for agentic pre-visualization pipeline.
"""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import generation
from app.core.config import settings
from app.core.exceptions import SceneForgeException
from app.core.logging import configure_logging, get_logger
from app.database import create_tables
from app.models.schemas import ErrorResponse, HealthCheck


configure_logging()
logger = get_logger(__name__)




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    
    logger.info("Starting SceneForge backend", version=settings.APP_VERSION)
    
    
    try:
        create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise
    
    yield
    
    
    logger.info("Shutting down SceneForge backend")



app = FastAPI(
    title="SceneForge Backend",
    description="Production-ready backend for agentic pre-visualization pipeline",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log requests and responses."""
    start_time = time.time()
    
   
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
    )
    
    response = await call_next(request)
    
    
    duration = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        duration=duration,
    )
    
    return response



@app.exception_handler(SceneForgeException)
async def sceneforge_exception_handler(request: Request, exc: SceneForgeException):
    """Handle SceneForge custom exceptions."""
    logger.error(
        "SceneForge exception",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        url=str(request.url),
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=exc.error_code or "SceneForgeError",
            message=exc.message,
            details=exc.details,
        ).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        url=str(request.url),
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An internal server error occurred",
        ).dict(),
    )



@app.get(
    "/health",
    response_model=HealthCheck,
    summary="Health check",
    description="Check service health and status",
)
async def health_check() -> HealthCheck:
    """Health check endpoint."""
    
    services = {}
    
    try:
        
        from app.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        services["database"] = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        services["database"] = "unhealthy"
    
    try:
        
        if settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "":
            services["gemini"] = "configured"
        else:
            services["gemini"] = "not_configured"
    except Exception:
        services["gemini"] = "error"
    
    try:
        
        if settings.BRIA_API_KEY and settings.BRIA_API_KEY != "":
            services["bria"] = "configured"
        else:
            services["bria"] = "not_configured"
    except Exception:
        services["bria"] = "error"
    
    
    try:
        import os
        if os.path.exists(settings.UPLOAD_DIR):
            services["storage"] = "healthy"
        else:
            services["storage"] = "directory_missing"
    except Exception:
        services["storage"] = "error"
    
    return HealthCheck(
        version=settings.APP_VERSION,
        services=services,
    )






app.include_router(
    generation.router,
    prefix=f"{settings.API_V1_STR}/generation",
    tags=["generation"],
)


import os
from pathlib import Path


upload_dir = Path(settings.UPLOAD_DIR).resolve()
upload_dir.mkdir(parents=True, exist_ok=True)

logger.info(f"Mounting uploads directory: {upload_dir}")
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")



@app.get(
    "/",
    summary="API Information",
    description="Get basic API information",
)
async def root() -> Dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs" if settings.DEBUG else None,
        "api_v1": settings.API_V1_STR,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )