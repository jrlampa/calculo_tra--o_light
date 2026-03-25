# The `RateLimitMiddleware` class enforces rate limits based on IP address using Redis cache in a
# FastAPI application.
"""Rate limiting middleware using Redis cache."""

from __future__ import annotations

import time
from typing import Callable, Optional
import structlog
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.config import get_settings
from cache.redis_client import get_cache_manager

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limits based on IP address.
    Uses the project's Redis cache for tracking requests.
    """

    def __init__(
        self,
        app: ASGIApp,
        rate_limit_per_minute: Optional[int] = None,
        rate_limit_per_hour: Optional[int] = None,
    ):
        super().__init__(app)
        settings = get_settings()
        self.rate_limit_per_minute = rate_limit_per_minute or settings.rate_limit_per_minute
        self.rate_limit_per_hour = rate_limit_per_hour or settings.rate_limit_per_hour
        self._cache_manager = None

    async def _get_cache(self):
        if self._cache_manager is None:
            self._cache_manager = await get_cache_manager()
        return self._cache_manager

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for static files and health checks
        if request.url.path.startswith(("/static", "/health", "/docs", "/openapi.json")):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        try:
            cache_manager = await self._get_cache()

            # Simple window-based rate limiting
            # Key format: ratelimit:IP:YYYYMMDDHHMM (per minute)
            # Key format: ratelimit:IP:YYYYMMDDHH (per hour)

            now = time.time()
            minute_key = time.strftime("%Y%m%d%H%M", time.gmtime(now))
            hour_key = time.strftime("%Y%m%d%H", time.gmtime(now))

            ip_minute_key = f"{client_ip}:{minute_key}"
            ip_hour_key = f"{client_ip}:{hour_key}"

            # Use increment from our Redis cache client
            # The client's increment method handles connection if needed
            minute_count = await cache_manager.cache.increment(
                ip_minute_key, prefix="ratelimit:min:"
            )
            hour_count = await cache_manager.cache.increment(ip_hour_key, prefix="ratelimit:hour:")

            # Set TTL for these keys if they are new (count == 1)
            if minute_count == 1:
                await cache_manager.cache.expire(ip_minute_key, 60, prefix="ratelimit:min:")
            if hour_count == 1:
                await cache_manager.cache.expire(ip_hour_key, 3600, prefix="ratelimit:hour:")

            # Check limits
            if minute_count and minute_count > self.rate_limit_per_minute:
                logger.warning(
                    "rate_limit_exceeded", ip=client_ip, limit="minute", count=minute_count
                )
                raise HTTPException(status_code=429, detail="Too many requests (per minute)")

            if hour_count and hour_count > self.rate_limit_per_hour:
                logger.warning("rate_limit_exceeded", ip=client_ip, limit="hour", count=hour_count)
                raise HTTPException(status_code=429, detail="Too many requests (per hour)")

        except HTTPException:
            # Re-raise HTTP exceptions (like 429)
            raise
        except Exception as e:
            # Don't block requests if Redis is down, but log the error
            logger.error("rate_limiting_error", error=str(e), ip=client_ip)
            return await call_next(request)

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.rate_limit_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.rate_limit_per_hour)
        if minute_count:
            response.headers["X-RateLimit-Remaining-Minute"] = str(
                max(0, self.rate_limit_per_minute - minute_count)
            )

        return response
