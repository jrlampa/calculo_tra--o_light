"""
Database Integration Manager for calculo_tração_light.
This module provides unified database access with connection pooling, 
transaction management, and multi-database support.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
import asyncpg
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    SUPABASE = "supabase"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    type: DatabaseType
    url: str
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


class DatabaseConnectionManager:
    """Unified database connection manager."""
    
    def __init__(self):
        self.configs: Dict[str, DatabaseConfig] = {}
        self.engines: Dict[str, Any] = {}
        self.redis_clients: Dict[str, aioredis.Redis] = {}
        self.lock = asyncio.Lock()
    
    def add_database(self, name: str, config: DatabaseConfig):
        """Add database configuration."""
        self.configs[name] = config
        
        if config.type == DatabaseType.POSTGRESQL:
            self._setup_postgresql_engine(name, config)
        elif config.type == DatabaseType.REDIS:
            self._setup_redis_client(name, config)
    
    def _setup_postgresql_engine(self, name: str, config: DatabaseConfig):
        """Setup PostgreSQL engine."""
        engine = create_async_engine(
            config.url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            echo=config.echo,
            future=True
        )
        
        self.engines[name] = engine
        logger.info(f"PostgreSQL engine configured for {name}")
    
    def _setup_redis_client(self, name: str, config: DatabaseConfig):
        """Setup Redis client."""
        # Redis URL format: redis://username:password@host:port/db
        redis_client = aioredis.from_url(
            config.url,
            encoding="utf-8",
            decode_responses=True
        )
        
        self.redis_clients[name] = redis_client
        logger.info(f"Redis client configured for {name}")
    
    @asynccontextmanager
    async def get_session(self, db_name: str = "default") -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        if db_name not in self.engines:
            raise ValueError(f"Database {db_name} not configured")
        
        engine = self.engines[db_name]
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        session = async_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
    
    async def execute_query(self, db_name: str, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute raw SQL query."""
        if db_name not in self.engines:
            raise ValueError(f"Database {db_name} not configured")
        
        engine = self.engines[db_name]
        
        try:
            async with engine.connect() as conn:
                result = await conn.execute(text(query), params or {})
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_transaction(self, db_name: str, queries: List[tuple]) -> bool:
        """Execute multiple queries in transaction."""
        if db_name not in self.engines:
            raise ValueError(f"Database {db_name} not configured")
        
        engine = self.engines[db_name]
        
        try:
            async with engine.begin() as conn:
                for query, params in queries:
                    await conn.execute(text(query), params or {})
                return True
        except Exception as e:
            logger.error(f"Transaction execution failed: {e}")
            return False
    
    async def get_redis_client(self, db_name: str = "default") -> aioredis.Redis:
        """Get Redis client."""
        if db_name not in self.redis_clients:
            raise ValueError(f"Redis {db_name} not configured")
        
        return self.redis_clients[db_name]
    
    async def health_check(self, db_name: str) -> Dict[str, Any]:
        """Check database health."""
        config = self.configs.get(db_name)
        if not config:
            return {"status": "error", "message": f"Database {db_name} not configured"}
        
        try:
            if config.type == DatabaseType.POSTGRESQL:
                start_time = time.time()
                result = await self.execute_query(db_name, "SELECT 1 as test")
                duration = time.time() - start_time
                
                return {
                    "status": "healthy",
                    "type": config.type.value,
                    "duration": duration,
                    "test_result": result[0] if result else None
                }
            
            elif config.type == DatabaseType.REDIS:
                start_time = time.time()
                redis_client = await self.get_redis_client(db_name)
                await redis_client.ping()
                duration = time.time() - start_time
                
                return {
                    "status": "healthy",
                    "type": config.type.value,
                    "duration": duration
                }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "type": config.type.value,
                "error": str(e)
            }
    
    async def get_connection_stats(self, db_name: str) -> Dict[str, Any]:
        """Get connection pool statistics."""
        if db_name not in self.engines:
            return {"error": f"Database {db_name} not configured"}
        
        engine = self.engines[db_name]
        
        try:
            pool = engine.pool
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "detached": pool.detached()
            }
        except Exception as e:
            return {"error": str(e)}


class DatabaseRepository:
    """Base repository class with database integration."""
    
    def __init__(self, db_manager: DatabaseConnectionManager, db_name: str = "default"):
        self.db_manager = db_manager
        self.db_name = db_name
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        async with self.db_manager.get_session(self.db_name) as session:
            yield session
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute raw query."""
        return await self.db_manager.execute_query(self.db_name, query, params)
    
    async def execute_transaction(self, queries: List[tuple]) -> bool:
        """Execute transaction."""
        return await self.db_manager.execute_transaction(self.db_name, queries)


class CacheManager:
    """Redis cache manager with advanced features."""
    
    def __init__(self, db_manager: DatabaseConnectionManager, db_name: str = "redis"):
        self.db_manager = db_manager
        self.db_name = db_name
    
    async def get_redis_client(self) -> aioredis.Redis:
        """Get Redis client."""
        return await self.db_manager.get_redis_client(self.db_name)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value."""
        try:
            redis_client = await self.get_redis_client()
            
            # Serialize value
            import json
            serialized_value = json.dumps(value)
            
            if ttl:
                await redis_client.setex(key, ttl, serialized_value)
            else:
                await redis_client.set(key, serialized_value)
            
            return True
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cache value."""
        try:
            redis_client = await self.get_redis_client()
            value = await redis_client.get(key)
            
            if value:
                import json
                return json.loads(value)
            
            return None
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete cache value."""
        try:
            redis_client = await self.get_redis_client()
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete failed: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            redis_client = await self.get_redis_client()
            return await redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists check failed: {e}")
            return False
    
    async def flush(self) -> bool:
        """Flush all cache."""
        try:
            redis_client = await self.get_redis_client()
            await redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache flush failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseConnectionManager()
cache_manager = CacheManager(db_manager)


def setup_database_connections():
    """Setup database connections from environment variables."""
    
    # PostgreSQL setup
    postgres_url = os.getenv('DATABASE_URL')
    if postgres_url:
        postgres_config = DatabaseConfig(
            type=DatabaseType.POSTGRESQL,
            url=postgres_url,
            pool_size=int(os.getenv('DB_POOL_SIZE', '20')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '30')),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '3600')),
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
        )
        db_manager.add_database('default', postgres_config)
        logger.info("PostgreSQL database configured")
    
    # Redis setup
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        redis_config = DatabaseConfig(
            type=DatabaseType.REDIS,
            url=redis_url
        )
        db_manager.add_database('redis', redis_config)
        logger.info("Redis database configured")
    
    # Test connections
    asyncio.create_task(test_connections())


async def test_connections():
    """Test database connections."""
    await asyncio.sleep(2)  # Wait for services to be ready
    
    for db_name, config in db_manager.configs.items():
        health = await db_manager.health_check(db_name)
        if health['status'] == 'healthy':
            logger.info(f"✅ {config.type.value} connection healthy for {db_name}")
        else:
            logger.error(f"❌ {config.type.value} connection failed for {db_name}: {health.get('error', 'Unknown error')}")


async def get_database_health() -> Dict[str, Any]:
    """Get health status of all databases."""
    health_status = {}
    
    for db_name in db_manager.configs.keys():
        health = await db_manager.health_check(db_name)
        stats = await db_manager.get_connection_stats(db_name)
        
        health_status[db_name] = {
            "health": health,
            "stats": stats
        }
    
    return health_status


async def get_cache_health() -> Dict[str, Any]:
    """Get Redis cache health status."""
    try:
        redis_client = await cache_manager.get_redis_client()
        info = await redis_client.info()
        
        return {
            "status": "healthy",
            "memory_usage": info.get('used_memory_human', 'unknown'),
            "connected_clients": info.get('connected_clients', 0),
            "keyspace_hits": info.get('keyspace_hits', 0),
            "keyspace_misses": info.get('keyspace_misses', 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }