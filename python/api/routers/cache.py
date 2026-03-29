"""Router for cache management and monitoring."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from cache.redis_client import get_cache_manager

router = APIRouter(prefix="/cache", tags=["Cache Management"])
logger = logging.getLogger(__name__)


class CacheStatsResponse(BaseModel):
    """Cache statistics response model."""
    status: str = Field(..., description="Cache status")
    local_stats: Dict[str, int] = Field(..., description="Local cache statistics")
    hit_rate: float = Field(..., description="Cache hit rate percentage")
    total_requests: int = Field(..., description="Total cache requests")
    redis_info: Dict[str, Any] = Field(..., description="Redis server information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CacheHealthResponse(BaseModel):
    """Cache health check response model."""
    status: str = Field(..., description="Health status")
    error: Optional[str] = Field(default=None, description="Error message if unhealthy")
    stats: Optional[Dict[str, Any]] = Field(default=None, description="Cache statistics")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CacheOperationResponse(BaseModel):
    """Cache operation response model."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation result message")
    affected_keys: Optional[int] = Field(default=None, description="Number of affected keys")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_statistics() -> CacheStatsResponse:
    """Get cache statistics."""
    try:
        cache_manager = await get_cache_manager()
        stats = await cache_manager.get_cache_stats()

        return CacheStatsResponse(
            status="success",
            local_stats=stats["local_stats"],
            hit_rate=stats["hit_rate"],
            total_requests=stats["total_requests"],
            redis_info=stats["redis_info"]
        )

    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cache statistics"
        )


@router.get("/health", response_model=CacheHealthResponse)
async def cache_health_check() -> CacheHealthResponse:
    """Perform cache health check."""
    try:
        cache_manager = await get_cache_manager()
        health = await cache_manager.health_check()

        return CacheHealthResponse(
            status=health["status"],
            error=health.get("error"),
            stats=health.get("stats")
        )

    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return CacheHealthResponse(
            status="unhealthy",
            error=str(e)
        )


@router.post("/clear", response_model=CacheOperationResponse)
async def clear_cache(
    pattern: Optional[str] = Query(default=None, description="Pattern to clear (optional)"),
    prefix: str = Query(default="default", description="Cache prefix")
) -> CacheOperationResponse:
    """Clear cache entries."""
    try:
        cache_manager = await get_cache_manager()

        if pattern:
            # Clear specific pattern
            deleted = await cache_manager.cache.delete_pattern(pattern, prefix)
            message = f"Cleared {deleted} keys matching pattern '{pattern}' with prefix '{prefix}'"
        else:
            # Clear all cache
            success = await cache_manager.cache.flush_all()
            deleted = 1 if success else 0
            message = "Cleared all cache entries"

        return CacheOperationResponse(
            success=deleted > 0,
            message=message,
            affected_keys=deleted
        )

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to clear cache"
        )


@router.post("/invalidate/projeto/{projeto_id}", response_model=CacheOperationResponse)
async def invalidate_projeto_cache(projeto_id: str) -> CacheOperationResponse:
    """Invalidate all cache entries for a specific projeto."""
    try:
        cache_manager = await get_cache_manager()
        deleted = await cache_manager.invalidate_projeto_cache(projeto_id)

        return CacheOperationResponse(
            success=deleted > 0,
            message=f"Invalidated {deleted} cache entries for projeto {projeto_id}",
            affected_keys=deleted
        )

    except Exception as e:
        logger.error(f"Failed to invalidate projeto cache: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to invalidate projeto cache"
        )


@router.get("/keys", response_model=Dict[str, Any])
async def list_cache_keys(
    pattern: str = Query(default="*", description="Pattern to match keys"),
    prefix: str = Query(default="default", description="Cache prefix"),
    limit: int = Query(default=100, le=1000, description="Maximum number of keys to return")
) -> Dict[str, Any]:
    """List cache keys matching pattern."""
    try:
        cache_manager = await get_cache_manager()

        if not cache_manager.cache.redis_client:
            raise HTTPException(
                status_code=503,
                detail="Cache not available"
            )

        # Create full pattern with prefix
        full_pattern = cache_manager.cache._make_key(prefix, pattern)

        # Get keys
        keys = await cache_manager.cache.redis_client.keys(full_pattern)

        # Limit results
        keys = keys[:limit]

        # Get TTL for each key
        key_info = []
        for key in keys:
            ttl = await cache_manager.cache.redis_client.ttl(key)
            key_info.append({
                "key": key,
                "ttl": ttl,
                "type": await cache_manager.cache.redis_client.type(key)
            })

        return {
            "status": "success",
            "pattern": pattern,
            "prefix": prefix,
            "total_keys": len(key_info),
            "keys": key_info,
            "timestamp": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to list cache keys: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list cache keys"
        )


@router.get("/key/{key:path}", response_model=Dict[str, Any])
async def get_cache_key(
    key: str,
    prefix: str = Query(default="default", description="Cache prefix")
) -> Dict[str, Any]:
    """Get specific cache key value and metadata."""
    try:
        cache_manager = await get_cache_manager()

        # Get value
        value = await cache_manager.cache.get(key, prefix)

        # Get TTL
        ttl = await cache_manager.cache.ttl(key, prefix)

        # Check existence
        exists = await cache_manager.cache.exists(key, prefix)

        return {
            "status": "success",
            "key": key,
            "prefix": prefix,
            "exists": exists,
            "ttl": ttl,
            "value": value,
            "timestamp": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get cache key: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get cache key"
        )


@router.delete("/key/{key:path}", response_model=CacheOperationResponse)
async def delete_cache_key(
    key: str,
    prefix: str = Query(default="default", description="Cache prefix")
) -> CacheOperationResponse:
    """Delete specific cache key."""
    try:
        cache_manager = await get_cache_manager()
        success = await cache_manager.cache.delete(key, prefix)

        return CacheOperationResponse(
            success=success,
            message=f"{'Deleted' if success else 'Key not found'} cache key '{key}' with prefix '{prefix}'",
            affected_keys=1 if success else 0
        )

    except Exception as e:
        logger.error(f"Failed to delete cache key: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete cache key"
        )


@router.post("/key/{key:path}", response_model=CacheOperationResponse)
async def set_cache_key(
    key: str,
    value: Any,
    prefix: str = Query(default="default", description="Cache prefix"),
    ttl: int = Query(default=300, description="Time to live in seconds")
) -> CacheOperationResponse:
    """Set cache key value."""
    try:
        cache_manager = await get_cache_manager()
        success = await cache_manager.cache.set(key, value, prefix, ttl)

        return CacheOperationResponse(
            success=success,
            message=f"{'Set' if success else 'Failed to set'} cache key '{key}' with prefix '{prefix}' and TTL {ttl}s",
            affected_keys=1 if success else 0
        )

    except Exception as e:
        logger.error(f"Failed to set cache key: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to set cache key"
        )


@router.post("/reset-stats", response_model=CacheOperationResponse)
async def reset_cache_statistics() -> CacheOperationResponse:
    """Reset cache statistics."""
    try:
        cache_manager = await get_cache_manager()
        await cache_manager.cache.clear_stats()

        return CacheOperationResponse(
            success=True,
            message="Cache statistics reset successfully",
            affected_keys=0
        )

    except Exception as e:
        logger.error(f"Failed to reset cache statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to reset cache statistics"
        )


@router.get("/performance", response_model=Dict[str, Any])
async def get_cache_performance() -> Dict[str, Any]:
    """Get detailed cache performance metrics."""
    try:
        cache_manager = await get_cache_manager()
        stats = await cache_manager.get_cache_stats()

        # Calculate additional metrics
        local_stats = stats["local_stats"]
        total_requests = stats["total_requests"]

        # Calculate rates
        hit_rate = stats["hit_rate"]
        miss_rate = 100 - hit_rate
        set_rate = (local_stats["sets"] / total_requests * 100) if total_requests > 0 else 0
        delete_rate = (local_stats["deletes"] / total_requests * 100) if total_requests > 0 else 0
        error_rate = (local_stats["errors"] / total_requests * 100) if total_requests > 0 else 0

        # Performance classification
        if hit_rate >= 80:
            performance_grade = "A"
        elif hit_rate >= 60:
            performance_grade = "B"
        elif hit_rate >= 40:
            performance_grade = "C"
        else:
            performance_grade = "D"

        return {
            "status": "success",
            "performance": {
                "grade": performance_grade,
                "hit_rate": hit_rate,
                "miss_rate": miss_rate,
                "set_rate": set_rate,
                "delete_rate": delete_rate,
                "error_rate": error_rate
            },
            "operations": local_stats,
            "redis_info": stats["redis_info"],
            "recommendations": get_performance_recommendations(hit_rate, error_rate),
            "timestamp": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get cache performance: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get cache performance"
        )


def get_performance_recommendations(hit_rate: float, error_rate: float) -> list:
    """Get performance recommendations based on metrics."""
    recommendations = []

    if hit_rate < 50:
        recommendations.append("Consider increasing cache TTL for frequently accessed data")
        recommendations.append("Review cache key patterns and ensure proper caching strategies")

    if hit_rate < 30:
        recommendations.append("Cache hit rate is very low - review caching implementation")
        recommendations.append("Consider warming up cache with frequently accessed data")

    if error_rate > 5:
        recommendations.append("High error rate detected - check Redis connection stability")
        recommendations.append("Review error logs and fix underlying issues")

    if hit_rate > 90:
        recommendations.append("Excellent cache performance - consider optimizing memory usage")

    return recommendations
