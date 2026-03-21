"""Cache middleware for API responses."""
from __future__ import annotations

import json
import hashlib
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import parse_qs

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from cache.redis_client import get_cache_manager

logger = logging.getLogger(__name__)


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware to cache API responses."""
    
    def __init__(self, app, cache_config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.cache_config = cache_config or {}
        self.cache_manager = None
        
        # Default cache settings
        self.default_ttl = self.cache_config.get("default_ttl", 300)  # 5 minutes
        self.max_ttl = self.cache_config.get("max_ttl", 3600)  # 1 hour
        
        # Routes to cache
        self.cacheable_routes = self.cache_config.get("routes", [
            {"path": "/api/projetos", "ttl": 600},
            {"path": "/api/public", "ttl": 1800},  # 30 minutes for public data
            {"path": "/api/monitoring/metrics", "ttl": 60},  # 1 minute for metrics
            {"path": "/api/cache/stats", "ttl": 30},  # 30 seconds for cache stats
        ])
        
        # Routes to never cache
        self.exclude_routes = self.cache_config.get("exclude", [
            "/api/auth",
            "/api/calculo",  # Don't cache calculation results by default
            "/api/ai/chat",  # Don't cache AI responses
            "/api/admin"
        ])
        
        # HTTP methods to cache
        self.cacheable_methods = {"GET", "HEAD"}
        
        # Status codes to cache
        self.cacheable_status_codes = {200, 201, 304}
        
        # Headers that should not be cached
        self.exclude_headers = {
            "authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
            "cache-control",
            "expires"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with caching."""
        # Check if request should be cached
        if not self._should_cache_request(request):
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get from cache
        try:
            self.cache_manager = await get_cache_manager()
            cached_response = await self.cache_manager.get_cached_api_response(
                request.url.path,
                self._get_request_params(request)
            )
            
            if cached_response:
                logger.debug(f"Cache hit for key: {cache_key}")
                return self._create_response_from_cache(cached_response)
                
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            # Continue with normal request if cache fails
        
        # Process request normally
        response = await call_next(request)
        
        # Cache response if appropriate
        if self._should_cache_response(response):
            try:
                await self._cache_response(request, response, cache_key)
                logger.debug(f"Cached response for key: {cache_key}")
            except Exception as e:
                logger.error(f"Cache storage error: {e}")
        
        return response
    
    def _should_cache_request(self, request: Request) -> bool:
        """Check if request should be cached."""
        # Check method
        if request.method not in self.cacheable_methods:
            return False
        
        # Check exclude routes
        for exclude_route in self.exclude_routes:
            if request.url.path.startswith(exclude_route):
                return False
        
        # Check cacheable routes
        for route_config in self.cacheable_routes:
            if request.url.path.startswith(route_config["path"]):
                return True
        
        return False
    
    def _should_cache_response(self, response: Response) -> bool:
        """Check if response should be cached."""
        # Check status code
        if response.status_code not in self.cacheable_status_codes:
            return False
        
        # Check for no-cache headers
        cache_control = response.headers.get("cache-control", "")
        if "no-cache" in cache_control or "private" in cache_control:
            return False
        
        # Check content type (only cache JSON responses)
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return False
        
        return True
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        # Include method, path, and relevant query parameters
        key_parts = [
            request.method,
            request.url.path,
            self._get_query_string(request)
        ]
        
        # Create hash
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_query_string(self, request: Request) -> str:
        """Get normalized query string."""
        query_params = parse_qs(request.url.query)
        
        # Remove cache-irrelevant parameters
        exclude_params = {"_", "nocache", "refresh"}
        filtered_params = {
            k: sorted(v) for k, v in query_params.items() 
            if k not in exclude_params
        }
        
        # Sort parameters for consistent key generation
        sorted_params = sorted(filtered_params.items())
        
        return json.dumps(sorted_params, separators=(",", ":"))
    
    def _get_request_params(self, request: Request) -> Dict[str, Any]:
        """Get request parameters for caching."""
        params = {}
        
        # Add query parameters
        query_params = parse_qs(request.url.query)
        for key, values in query_params.items():
            if key not in {"_", "nocache", "refresh"}:
                params[key] = values[0] if len(values) == 1 else values
        
        # Add relevant headers
        for header in ["accept-language", "x-user-id"]:
            if header in request.headers:
                params[header] = request.headers[header]
        
        return params
    
    def _get_ttl_for_route(self, path: str) -> int:
        """Get TTL for specific route."""
        for route_config in self.cacheable_routes:
            if path.startswith(route_config["path"]):
                return min(route_config["ttl"], self.max_ttl)
        
        return self.default_ttl
    
    async def _cache_response(self, request: Request, response: Response, cache_key: str):
        """Cache response data."""
        if not self.cache_manager:
            return
        
        try:
            # Get TTL for this route
            ttl = self._get_ttl_for_route(request.url.path)
            
            # Prepare cache data
            cache_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.body if hasattr(response, 'body') else None,
                "timestamp": response.headers.get("date")
            }
            
            # For JSONResponse, try to parse and store the actual data
            if isinstance(response, JSONResponse) and hasattr(response, 'body'):
                try:
                    if response.body:
                        cache_data["data"] = json.loads(response.body.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            
            # Cache the response
            await self.cache_manager.cache_api_response(
                request.url.path,
                self._get_request_params(request),
                cache_data,
                ttl
            )
            
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
    
    def _create_response_from_cache(self, cached_data: Dict[str, Any]) -> Response:
        """Create response from cached data."""
        # Create response
        if cached_data.get("data"):
            # Use cached JSON data
            response = JSONResponse(
                content=cached_data["data"],
                status_code=cached_data["status_code"]
            )
        else:
            # Use cached body
            body = cached_data.get("body", b"")
            if isinstance(body, str):
                body = body.encode()
            
            response = Response(
                content=body,
                status_code=cached_data["status_code"]
            )
        
        # Set headers (excluding cache-irrelevant headers)
        cached_headers = cached_data.get("headers", {})
        for header, value in cached_headers.items():
            if header.lower() not in self.exclude_headers:
                response.headers[header] = value
        
        # Add cache headers
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Cache-Key"] = hashlib.md5(
            f"{cached_data['timestamp']}".encode()
        ).hexdigest()[:8]
        
        return response


class CacheInvalidationMiddleware(BaseHTTPMiddleware):
    """Middleware to invalidate cache on data changes."""
    
    def __init__(self, app):
        super().__init__(app)
        self.cache_manager = None
        
        # Routes that should trigger cache invalidation
        self.invalidation_routes = {
            "POST": [
                "/api/projetos",
                "/api/calculo",
                "/api/pontos"
            ],
            "PUT": [
                "/api/projetos",
                "/api/calculo",
                "/api/pontos"
            ],
            "DELETE": [
                "/api/projetos",
                "/api/calculo",
                "/api/pontos"
            ]
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with cache invalidation."""
        # Process request
        response = await call_next(request)
        
        # Check if cache should be invalidated
        if self._should_invalidate_cache(request, response):
            await self._invalidate_cache(request)
        
        return response
    
    def _should_invalidate_cache(self, request: Request, response: Response) -> bool:
        """Check if cache should be invalidated."""
        # Check if method and path match invalidation rules
        method = request.method
        path = request.url.path
        
        if method in self.invalidation_routes:
            for invalidation_path in self.invalidation_routes[method]:
                if path.startswith(invalidation_path):
                    # Only invalidate if the request was successful
                    return response.status_code in {200, 201, 204}
        
        return False
    
    async def _invalidate_cache(self, request: Request):
        """Invalidate relevant cache entries."""
        try:
            self.cache_manager = await get_cache_manager()
            
            path = request.url.path
            
            # Invalidate based on path
            if path.startswith("/api/projetos"):
                # Invalidate projeto-related cache
                await self.cache_manager.cache.delete_pattern("projeto:*")
                await self.cache_manager.cache.delete_pattern("api:/api/projetos*")
            
            elif path.startswith("/api/calculo"):
                # Invalidate calculation-related cache
                await self.cache_manager.cache.delete_pattern("calculo:*")
                await self.cache_manager.cache.delete_pattern("api:/api/calculo*")
            
            elif path.startswith("/api/pontos"):
                # Invalidate pontos-related cache
                await self.cache_manager.cache.delete_pattern("ponto:*")
                await self.cache_manager.cache.delete_pattern("api:/api/pontos*")
            
            # Also invalidate API cache for the specific endpoint
            await self.cache_manager.cache.delete_pattern(f"api:{path}*")
            
            logger.info(f"Invalidated cache for {path}")
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")


def setup_cache_middleware(app, cache_config: Optional[Dict[str, Any]] = None):
    """Setup cache middleware for FastAPI app."""
    # Add cache middleware
    app.add_middleware(CacheMiddleware, cache_config=cache_config)
    
    # Add cache invalidation middleware
    app.add_middleware(CacheInvalidationMiddleware)
    
    logger.info("Cache middleware configured")
