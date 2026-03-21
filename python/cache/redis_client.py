"""Redis client for advanced caching."""
from __future__ import annotations

import json
import logging
import pickle
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

import redis.asyncio as redis
from redis.asyncio import Redis

from core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration."""
    default_ttl: int = 300  # 5 minutes
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    decode_responses: bool = True


class RedisCache:
    """Redis cache client with advanced features."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.redis_client: Optional[Redis] = None
        self.settings = get_settings()
        
        # Cache key prefixes
        self.prefixes = {
            'projeto': 'projeto:',
            'ponto': 'ponto:',
            'calculo': 'calculo:',
            'user': 'user:',
            'session': 'session:',
            'api': 'api:',
            'ai': 'ai:'
        }
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
    
    async def connect(self) -> bool:
        """Connect to Redis."""
        try:
            self.redis_client = Redis(
                host='localhost',
                port=6379,
                db=0,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                decode_responses=self.config.decode_responses
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            return False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Disconnected from Redis")
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create cache key with prefix."""
        return f"{self.prefixes.get(prefix, prefix)}{identifier}"
    
    async def get(self, key: str, prefix: str = 'default') -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            await self.connect()
        
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._make_key(prefix, key)
            value = await self.redis_client.get(cache_key)
            
            if value is not None:
                self.stats['hits'] += 1
                # Try to deserialize JSON first, then pickle
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        return pickle.loads(value.encode('latin1'))
                    except (pickle.PickleError, UnicodeEncodeError):
                        return value
            else:
                self.stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.stats['errors'] += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        prefix: str = 'default',
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        if not self.redis_client:
            await self.connect()
        
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(prefix, key)
            ttl = ttl or self.config.default_ttl
            
            # Try to serialize as JSON first, then pickle
            try:
                serialized_value = json.dumps(value, default=str)
            except (TypeError, ValueError):
                serialized_value = pickle.dumps(value).decode('latin1')
            
            result = await self.redis_client.setex(cache_key, ttl, serialized_value)
            
            if result:
                self.stats['sets'] += 1
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def delete(self, key: str, prefix: str = 'default') -> bool:
        """Delete value from cache."""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(prefix, key)
            result = await self.redis_client.delete(cache_key)
            
            if result:
                self.stats['deletes'] += 1
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def delete_pattern(self, pattern: str, prefix: str = 'default') -> int:
        """Delete keys matching pattern."""
        if not self.redis_client:
            return 0
        
        try:
            cache_pattern = self._make_key(prefix, pattern)
            keys = await self.redis_client.keys(cache_pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.stats['deletes'] += deleted
                return deleted
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Cache delete pattern error for pattern {pattern}: {e}")
            self.stats['errors'] += 1
            return 0
    
    async def exists(self, key: str, prefix: str = 'default') -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(prefix, key)
            return await self.redis_client.exists(cache_key) > 0
                
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def expire(self, key: str, ttl: int, prefix: str = 'default') -> bool:
        """Set expiration for existing key."""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(prefix, key)
            return await self.redis_client.expire(cache_key, ttl)
                
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def ttl(self, key: str, prefix: str = 'default') -> int:
        """Get time to live for key."""
        if not self.redis_client:
            return -1
        
        try:
            cache_key = self._make_key(prefix, key)
            return await self.redis_client.ttl(cache_key)
                
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            self.stats['errors'] += 1
            return -1
    
    async def increment(self, key: str, amount: int = 1, prefix: str = 'default') -> Optional[int]:
        """Increment numeric value."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._make_key(prefix, key)
            result = await self.redis_client.incrby(cache_key, amount)
            self.stats['sets'] += 1
            return result
                
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            self.stats['errors'] += 1
            return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        redis_info = {}
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                redis_info = {
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
            except Exception as e:
                logger.error(f"Failed to get Redis info: {e}")
        
        return {
            'local_stats': self.stats,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'redis_info': redis_info
        }
    
    async def clear_stats(self):
        """Clear cache statistics."""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
    
    async def flush_all(self) -> bool:
        """Flush all keys from Redis."""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushdb()
            logger.info("Flushed all cache keys")
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False


class CacheManager:
    """High-level cache manager with intelligent strategies."""
    
    def __init__(self):
        self.cache = RedisCache()
        self._connected = False
    
    async def initialize(self) -> bool:
        """Initialize cache manager."""
        self._connected = await self.cache.connect()
        return self._connected
    
    async def shutdown(self):
        """Shutdown cache manager."""
        await self.cache.disconnect()
        self._connected = False
    
    async def get_projeto(self, projeto_id: str) -> Optional[Dict[str, Any]]:
        """Get projeto from cache."""
        return await self.cache.get(projeto_id, 'projeto')
    
    async def set_projeto(self, projeto_id: str, projeto_data: Dict[str, Any], ttl: int = 600) -> bool:
        """Set projeto in cache."""
        return await self.cache.set(projeto_id, projeto_data, 'projeto', ttl)
    
    async def get_pontos(self, projeto_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get pontos from cache."""
        return await self.cache.get(f"{projeto_id}:pontos", 'ponto')
    
    async def set_pontos(self, projeto_id: str, pontos: List[Dict[str, Any]], ttl: int = 600) -> bool:
        """Set pontos in cache."""
        return await self.cache.set(f"{projeto_id}:pontos", pontos, 'ponto', ttl)
    
    async def get_calculo_result(self, calculation_hash: str) -> Optional[Dict[str, Any]]:
        """Get calculation result from cache."""
        return await self.cache.get(calculation_hash, 'calculo')
    
    async def set_calculo_result(self, calculation_hash: str, result: Dict[str, Any], ttl: int = 1800) -> bool:
        """Set calculation result in cache."""
        return await self.cache.set(calculation_hash, result, 'calculo', ttl)
    
    async def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session from cache."""
        return await self.cache.get(session_id, 'session')
    
    async def set_user_session(self, session_id: str, session_data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set user session in cache."""
        return await self.cache.set(session_id, session_data, 'session', ttl)
    
    async def invalidate_projeto_cache(self, projeto_id: str) -> bool:
        """Invalidate all cache entries for a projeto."""
        deleted = 0
        deleted += await self.cache.delete(projeto_id, 'projeto')
        deleted += await self.cache.delete(f"{projeto_id}:pontos", 'ponto')
        deleted += await self.cache.delete_pattern(f"{projeto_id}:*", 'calculo')
        return deleted > 0
    
    async def cache_api_response(self, endpoint: str, params: Dict[str, Any], response: Any, ttl: int = 300) -> bool:
        """Cache API response."""
        # Create cache key from endpoint and params
        param_hash = hash(str(sorted(params.items())))
        cache_key = f"{endpoint}:{param_hash}"
        return await self.cache.set(cache_key, response, 'api', ttl)
    
    async def get_cached_api_response(self, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached API response."""
        param_hash = hash(str(sorted(params.items())))
        cache_key = f"{endpoint}:{param_hash}"
        return await self.cache.get(cache_key, 'api')
    
    async def get_ai_response(self, prompt_hash: str) -> Optional[str]:
        """Get AI response from cache."""
        return await self.cache.get(prompt_hash, 'ai')
    
    async def set_ai_response(self, prompt_hash: str, response: str, ttl: int = 3600) -> bool:
        """Set AI response in cache."""
        return await self.cache.set(prompt_hash, response, 'ai', ttl)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return await self.cache.get_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check."""
        if not self._connected:
            return {
                'status': 'unhealthy',
                'error': 'Not connected to Redis'
            }
        
        try:
            # Test basic operations
            test_key = 'health_check'
            test_value = {'test': True, 'timestamp': datetime.utcnow().isoformat()}
            
            # Set
            set_success = await self.cache.set(test_key, test_value, 'test', 10)
            
            # Get
            retrieved = await self.cache.get(test_key, 'test')
            
            # Delete
            delete_success = await self.cache.delete(test_key, 'test')
            
            # Get stats
            stats = await self.cache.get_stats()
            
            if set_success and retrieved == test_value and delete_success:
                return {
                    'status': 'healthy',
                    'stats': stats,
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Cache operations failed',
                    'stats': stats
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get or create cache manager."""
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager()
        await _cache_manager.initialize()
    
    return _cache_manager


# Cache decorator for functions
def cache_result(ttl: int = 300, prefix: str = 'default'):
    """Decorator to cache function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_manager = await get_cache_manager()
            
            # Create cache key from function name and arguments
            func_name = func.__name__
            args_hash = hash(str(args) + str(sorted(kwargs.items())))
            cache_key = f"{func_name}:{args_hash}"
            
            # Try to get from cache
            cached_result = await cache_manager.cache.get(cache_key, prefix)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.cache.set(cache_key, result, prefix, ttl)
            
            return result
        return wrapper
    return decorator
