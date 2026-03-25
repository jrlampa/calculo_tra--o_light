"""
Strategic Cache System for calculo_tração_light.
This module provides multi-layer caching with intelligent cache invalidation and warming.
"""

import logging
import time
import asyncio
import json
import hashlib
from typing import Any, Dict, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import pickle

logger = logging.getLogger(__name__)


class CacheLayer(Enum):
    """Cache layers with different characteristics."""
    L1_MEMORY = "l1_memory"      # Fastest, smallest, volatile
    L2_REDIS = "l2_redis"        # Fast, medium, persistent
    L3_DATABASE = "l3_database"  # Slowest, largest, persistent


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    layer: CacheLayer
    created_at: float
    expires_at: Optional[float]
    access_count: int
    last_accessed: float
    dependencies: List[str]  # Keys that this entry depends on


class CacheStrategy(ABC):
    """Abstract base class for cache strategies."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass


class MemoryCache(CacheStrategy):
    """L1 Memory Cache - Fastest access, volatile."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if entry.expires_at and time.time() > entry.expires_at:
                    del self.cache[key]
                    return None
                
                entry.access_count += 1
                entry.last_accessed = time.time()
                return entry.value
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self.lock:
            # Eviction policy: LRU (Least Recently Used)
            if len(self.cache) >= self.max_size:
                # Find least recently used entry
                lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_accessed)
                del self.cache[lru_key]
            
            expires_at = time.time() + ttl if ttl else None
            self.cache[key] = CacheEntry(
                key=key,
                value=value,
                layer=CacheLayer.L1_MEMORY,
                created_at=time.time(),
                expires_at=expires_at,
                access_count=1,
                last_accessed=time.time(),
                dependencies=[]
            )
            return True
    
    async def delete(self, key: str) -> bool:
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def clear(self) -> bool:
        async with self.lock:
            self.cache.clear()
            return True


class RedisCache(CacheStrategy):
    """L2 Redis Cache - Fast access, persistent."""
    
    def __init__(self, redis_client=None, max_size: int = 10000):
        self.redis_client = redis_client
        self.max_size = max_size
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        if not self.redis_client:
            return None
        
        try:
            data = await self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self.redis_client:
            return False
        
        try:
            data = pickle.dumps(value)
            if ttl:
                await self.redis_client.setex(key, ttl, data)
            else:
                await self.redis_client.set(key, data)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False


class StrategicCache:
    """Multi-layer strategic cache with intelligent invalidation."""
    
    def __init__(self, memory_cache: MemoryCache, redis_cache: RedisCache):
        self.memory_cache = memory_cache
        self.redis_cache = redis_cache
        self.dependency_map: Dict[str, List[str]] = {}  # key -> list of dependent keys
        self.cache_stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'total_requests': 0
        }
        self.lock = asyncio.Lock()
    
    async def get(self, key: str, fallback_func: Optional[Callable] = None) -> Optional[Any]:
        """Get value from cache with fallback function."""
        async with self.lock:
            self.cache_stats['total_requests'] += 1
            
            # Try L1 cache first
            value = await self.memory_cache.get(key)
            if value is not None:
                self.cache_stats['l1_hits'] += 1
                logger.debug(f"L1 cache hit for key: {key}")
                return value
            
            self.cache_stats['l1_misses'] += 1
            
            # Try L2 cache
            value = await self.redis_cache.get(key)
            if value is not None:
                self.cache_stats['l2_hits'] += 1
                logger.debug(f"L2 cache hit for key: {key}")
                # Promote to L1
                await self.memory_cache.set(key, value, ttl=300)  # 5 minutes in L1
                return value
            
            self.cache_stats['l2_misses'] += 1
            
            # Cache miss - try fallback function
            if fallback_func:
                logger.debug(f"Cache miss for key: {key}, executing fallback")
                value = await fallback_func()
                if value is not None:
                    await self.set(key, value)
                return value
            
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  dependencies: Optional[List[str]] = None) -> bool:
        """Set value in cache with dependencies."""
        async with self.lock:
            # Set in both layers
            l1_success = await self.memory_cache.set(key, value, ttl)
            l2_success = await self.redis_cache.set(key, value, ttl)
            
            # Register dependencies
            if dependencies:
                self.dependency_map[key] = dependencies
                for dep_key in dependencies:
                    if dep_key not in self.dependency_map:
                        self.dependency_map[dep_key] = []
                    if key not in self.dependency_map[dep_key]:
                        self.dependency_map[dep_key].append(key)
            
            return l1_success and l2_success
    
    async def invalidate(self, key: str) -> bool:
        """Invalidate cache entry and its dependents."""
        async with self.lock:
            # Delete from both layers
            l1_success = await self.memory_cache.delete(key)
            l2_success = await self.redis_cache.delete(key)
            
            # Invalidate dependents
            if key in self.dependency_map:
                dependents = self.dependency_map[key]
                for dep_key in dependents:
                    await self.invalidate(dep_key)
                del self.dependency_map[key]
            
            return l1_success and l2_success
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        async with self.lock:
            invalidated_count = 0
            
            # For memory cache, we need to check all keys
            keys_to_invalidate = [k for k in self.memory_cache.cache.keys() if pattern in k]
            for key in keys_to_invalidate:
                if await self.invalidate(key):
                    invalidated_count += 1
            
            # For Redis, we can use pattern matching
            try:
                if self.redis_cache.redis_client:
                    keys = await self.redis_cache.redis_client.keys(pattern)
                    for key in keys:
                        if await self.invalidate(key.decode()):
                            invalidated_count += 1
            except Exception as e:
                logger.error(f"Error invalidating Redis pattern {pattern}: {e}")
            
            return invalidated_count
    
    async def warm_cache(self, key_value_pairs: List[Tuple[str, Any]], 
                        ttl: Optional[int] = None) -> bool:
        """Warm cache with preloaded data."""
        async with self.lock:
            success_count = 0
            for key, value in key_value_pairs:
                if await self.set(key, value, ttl):
                    success_count += 1
            
            logger.info(f"Warmed cache with {success_count}/{len(key_value_pairs)} entries")
            return success_count == len(key_value_pairs)
    
    async def clear(self) -> bool:
        """Clear all cache layers."""
        async with self.lock:
            l1_success = await self.memory_cache.clear()
            l2_success = await self.redis_cache.clear()
            self.dependency_map.clear()
            return l1_success and l2_success
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        l1_hit_rate = self.cache_stats['l1_hits'] / max(1, self.cache_stats['l1_hits'] + self.cache_stats['l1_misses'])
        l2_hit_rate = self.cache_stats['l2_hits'] / max(1, self.cache_stats['l2_hits'] + self.cache_stats['l2_misses'])
        total_hit_rate = (self.cache_stats['l1_hits'] + self.cache_stats['l2_hits']) / max(1, self.cache_stats['total_requests'])
        
        return {
            **self.cache_stats,
            'l1_hit_rate': l1_hit_rate,
            'l2_hit_rate': l2_hit_rate,
            'total_hit_rate': total_hit_rate,
            'memory_cache_size': len(self.memory_cache.cache),
            'dependency_map_size': len(self.dependency_map)
        }
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments."""
        # Create a stable key from arguments
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': kwargs
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return f"{prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"


# Decorator for caching function results
def cache_result(ttl: int = 300, prefix: str = "func", 
                dependencies: Optional[List[str]] = None):
    """Decorator to cache function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = strategic_cache.generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            result = await strategic_cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await strategic_cache.set(cache_key, result, ttl, dependencies)
            
            return result
        
        return wrapper
    return decorator


# Global strategic cache instance
memory_cache = MemoryCache(max_size=1000)
redis_cache = RedisCache(max_size=10000)
strategic_cache = StrategicCache(memory_cache, redis_cache)


async def get_cache_health() -> Dict[str, Any]:
    """Get cache health status."""
    stats = strategic_cache.get_stats()
    
    health = {
        "status": "healthy",
        "l1_health": "good" if stats['l1_hit_rate'] > 0.7 else "warning" if stats['l1_hit_rate'] > 0.3 else "critical",
        "l2_health": "good" if stats['l2_hit_rate'] > 0.5 else "warning" if stats['l2_hit_rate'] > 0.2 else "critical",
        "overall_health": "good" if stats['total_hit_rate'] > 0.6 else "warning" if stats['total_hit_rate'] > 0.3 else "critical",
        "recommendations": []
    }
    
    # Generate recommendations
    if stats['l1_hit_rate'] < 0.5:
        health['recommendations'].append("Consider increasing L1 cache size or TTL")
    
    if stats['l2_hit_rate'] < 0.3:
        health['recommendations'].append("Consider warming L2 cache with frequently accessed data")
    
    if stats['total_hit_rate'] < 0.4:
        health['recommendations'].append("Review cache strategy - hit rate is low")
    
    return {**stats, **health}


async def warm_common_queries():
    """Warm cache with common queries."""
    # This would be populated with actual common queries from the application
    common_queries = [
        ("config:app_settings", {"theme": "dark", "language": "pt"}),
        ("lookup:materials", ["copper", "aluminum", "steel"]),
        ("lookup:voltages", [13800, 34500, 69000]),
    ]
    
    await strategic_cache.warm_cache(common_queries, ttl=3600)  # 1 hour