"""FastAPI application – tração de poste calculator.

Run with:
    cd python
    uvicorn api.main:app --reload --port 8000

The React Vite dev server proxies /api/* to http://localhost:8000.
"""
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

# Allow imports from the python/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.routers import (
    admin,
    ai_assistant,
    cache,
    calculo,
    monitoring,
    projetos,
    public,
)
from core.config import get_settings
from core.logging import setup_logging
from core.ratelimit import RateLimitMiddleware
from db.pool import db_pool, initialize_db_pool
from cache.redis_client import get_cache_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    # Startup: Initialize connections
    await initialize_db_pool()
    await get_cache_manager()
    logger.info("application_started", version=get_settings().app_version)
    
    yield
    
    # Shutdown: Close connections
    await db_pool.close()
    logger.info("application_shutdown")

# Initialize structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title=get_settings().app_name,
    version=get_settings().app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    description="Sistema de Engenharia Elétrica para Cálculo de Tração em Redes Aéreas"
)

# Initialize Prometheus Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["Monitoring"])

# ----------------------------------------------------------------------------
# Middlewares
# ----------------------------------------------------------------------------

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# Authentication Middleware (Enterprise In-Process)
@app.middleware("http")
async def authentication_middleware(request: Request, call_next):
    """Resolve user from JWT/Session and attach to request state."""
    from api.auth import resolve_current_user, SESSION_COOKIE_NAME, SESSION_TTL_SECONDS
    
    # 1. Resolve user from headers or cookies
    resolution = resolve_current_user(request)
    request.state.current_user = resolution.current_user
    
    # 2. Process the request
    response = await call_next(request)
    
    # 3. If a new session was created (e.g. guest mode), set the cookie
    if resolution.should_set_cookie and resolution.cookie_value:
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=resolution.cookie_value,
            httponly=True,
            max_age=SESSION_TTL_SECONDS,
            samesite="lax",
            secure=False, # Set to True in HTTPS production
        )
    return response

# ----------------------------------------------------------------------------
# Global Error Handlers
# ----------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for standardized enterprise error responses."""
    import traceback
    print("CRITICAL_ERROR_TRACEBACK:")
    traceback.print_exc()
    
    logger.exception("unhandled_exception", 
                     path=request.url.path, 
                     method=request.method,
                     error=str(exc))
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "type": "INTERNAL_ERROR",
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ----------------------------------------------------------------------------
# Core / Monitoring Routes
# ----------------------------------------------------------------------------

@app.get("/health", tags=["Monitoring"])
async def health():
    """Simple Liveness probe."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/deep", tags=["Monitoring"])
async def deep_health():
    """Detailed Readiness probe for components."""
    results = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # 1. Database Health
    db_healthy = await db_pool.health_check()
    db_stats = await db_pool.get_pool_stats() if db_healthy else {}
    results["components"]["database"] = {
        "status": "healthy" if db_healthy else "unhealthy",
        "stats": db_stats
    }
    if not db_healthy:
        results["status"] = "unhealthy"

    # 2. Cache Health (Degraded instead of Unhealthy if down)
    try:
        cache_manager = await get_cache_manager()
        cache_status = await cache_manager.health_check()
        results["components"]["cache"] = cache_status
        if cache_status["status"] != "healthy":
            if results["status"] == "healthy":
                results["status"] = "degraded"
    except Exception as e:
        results["components"]["cache"] = {"status": "error", "error": str(e)}
        if results["status"] == "healthy":
            results["status"] = "degraded"

    return results

# ----------------------------------------------------------------------------
# Include Routers (Modular Architecture)
# ----------------------------------------------------------------------------

# All domain routes are prefixed with /api
app.include_router(calculo.router, prefix="/api")
app.include_router(projetos.router, prefix="/api")
app.include_router(ai_assistant.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")
app.include_router(cache.router, prefix="/api")
app.include_router(public.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
