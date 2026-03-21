"""FastAPI application – tração de poste calculator (Updated Version).

Run with:
    cd python
    uvicorn api.main_updated:app --reload --port 8000

The React Vite dev server proxies /api/* to http://localhost:8000.
"""
from __future__ import annotations

import logging
import sys
import os
from typing import Optional

# Allow imports from the python/ directory when run as `uvicorn api.main:app`
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Import routers
from api.routers import projetos, calculo, public, admin, monitoring
from api.dependencies import get_projeto_service
from api.documentation import setup_api_documentation
from monitoring.performance import add_performance_monitoring
from middleware.security import add_security_middleware
from core.config import get_settings
from core.exceptions import BaseAppException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Cálculo de Tração API...")
    
    # Initialize services if needed
    try:
        # Test database connection
        projeto_service = await get_projeto_service()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    # Start performance monitoring
    try:
        from monitoring.performance import get_performance_monitor
        monitor = get_performance_monitor()
        await monitor.start_monitoring()
        logger.info("Performance monitoring started")
    except Exception as e:
        logger.error(f"Failed to start performance monitoring: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Cálculo de Tração API...")


# Create FastAPI app
app = FastAPI(
    title="Cálculo de Tração API",
    description="API para cálculo de tração de redes elétricas",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup enhanced documentation
setup_api_documentation(app)

# Add performance monitoring
add_performance_monitoring(app)

# Add security middleware
add_security_middleware(app, settings)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(BaseAppException)
async def base_app_exception_handler(request: Request, exc: BaseAppException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.code or "APPLICATION_ERROR",
            "message": exc.message,
            "type": "application_error"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "type": "http_error"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "type": "internal_error"
        }
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "Cálculo de Tração API"
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check with dependencies."""
    try:
        # Test database connection
        projeto_service = await get_projeto_service()
        await projeto_service.count_projetos()
        
        return {
            "status": "ready",
            "database": "connected",
            "version": "2.0.0",
            "service": "Cálculo de Tração API"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "error": str(e),
                "version": "2.0.0",
                "service": "Cálculo de Tração API"
            }
        )


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness check."""
    return {
        "status": "alive",
        "version": "2.0.0",
        "service": "Cálculo de Tração API"
    }


# Include routers
app.include_router(
    projetos.router,
    prefix="/api/projetos",
    tags=["Projetos"]
)

app.include_router(
    calculo.router,
    prefix="/api/calculo",
    tags=["Cálculo"]
)

app.include_router(
    public.router,
    prefix="/api/public",
    tags=["Public"]
)

app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["Admin"]
)

app.include_router(
    monitoring.router,
    prefix="/api",
    tags=["Monitoring"]
)


# Legacy endpoints for backward compatibility
@app.get("/", tags=["Legacy"])
async def root():
    """Root endpoint for backward compatibility."""
    return {
        "message": "Cálculo de Tração API v2.0.0",
        "docs": "/docs",
        "health": "/health",
        "version": "2.0.0"
    }


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    
    return response


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to responses."""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_updated:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
