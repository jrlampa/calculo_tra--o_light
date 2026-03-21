"""Security middleware for enhanced HTTP headers."""
from __future__ import annotations

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from core.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(self, app, settings=None):
        super().__init__(app)
        self.settings = settings or get_settings()
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request and add security headers."""
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response, request)
        
        return response
    
    def _add_security_headers(self, response: Response, request: Request) -> None:
        """Add security headers to response."""
        
        # Content Security Policy (CSP)
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        permissions_policy = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
            "ambient-light-sensor=()",
            "autoplay=()",
            "encrypted-media=()",
            "fullscreen=()",
            "picture-in-picture=()"
        ]
        
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)
        
        # Strict-Transport-Security (HTTPS only)
        if request.url.scheme == "https":
            hsts_directives = [
                "max-age=31536000",  # 1 year
                "includeSubDomains",
                "preload"
            ]
            response.headers["Strict-Transport-Security"] = "; ".join(hsts_directives)
        
        # Cross-Origin Embedder Policy
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        
        # Cross-Origin Opener Policy
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        
        # Cross-Origin Resource Policy
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Remove server information
        response.headers["Server"] = "Calculo de Tracao API"
        
        # Add cache control for API responses
        if request.url.path.startswith("/api/"):
            if request.method in ["GET", "HEAD"]:
                # Cache GET requests for 5 minutes
                response.headers["Cache-Control"] = "public, max-age=300"
            else:
                # Don't cache non-GET requests
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.request_counts = {}  # {client_ip: [timestamps]}
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with rate limiting."""
        client_ip = self._get_client_ip(request)
        
        # Check rate limits
        self._check_rate_limits(client_ip, request)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, client_ip)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to client IP
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limits(self, client_ip: str, request: Request) -> None:
        """Check if client has exceeded rate limits."""
        from datetime import datetime, timedelta
        import time
        
        now = time.time()
        
        # Initialize client tracking if needed
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Clean old requests (older than 1 hour)
        one_hour_ago = now - 3600
        self.request_counts[client_ip] = [
            timestamp for timestamp in self.request_counts[client_ip]
            if timestamp > one_hour_ago
        ]
        
        # Check minute limit
        one_minute_ago = now - 60
        requests_last_minute = len([
            timestamp for timestamp in self.request_counts[client_ip]
            if timestamp > one_minute_ago
        ])
        
        if requests_last_minute >= self.requests_per_minute:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again in a minute.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + 60))
                }
            )
        
        # Check hour limit
        requests_last_hour = len(self.request_counts[client_ip])
        
        if requests_last_hour >= self.requests_per_hour:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again in an hour.",
                headers={
                    "Retry-After": "3600",
                    "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
                    "X-RateLimit-Remaining-Hour": "0",
                    "X-RateLimit-Reset-Hour": str(int(now + 3600))
                }
            )
        
        # Record this request
        self.request_counts[client_ip].append(now)
    
    def _add_rate_limit_headers(self, response: Response, client_ip: str) -> None:
        """Add rate limit headers to response."""
        import time
        
        now = time.time()
        requests = self.request_counts.get(client_ip, [])
        
        # Calculate remaining requests
        one_minute_ago = now - 60
        requests_last_minute = len([
            timestamp for timestamp in requests
            if timestamp > one_minute_ago
        ])
        
        one_hour_ago = now - 3600
        requests_last_hour = len([
            timestamp for timestamp in requests
            if timestamp > one_hour_ago
        ])
        
        # Add headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.requests_per_minute - requests_last_minute)
        )
        response.headers["X-RateLimit-Reset"] = str(int(now + 60))
        
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, self.requests_per_hour - requests_last_hour)
        )
        response.headers["X-RateLimit-Reset-Hour"] = str(int(now + 3600))


def add_security_middleware(app, settings=None):
    """Add security middleware to FastAPI app."""
    settings = settings or get_settings()
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware, settings=settings)
    
    # Add rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.rate_limit_per_minute,
        requests_per_hour=settings.rate_limit_per_hour
    )
