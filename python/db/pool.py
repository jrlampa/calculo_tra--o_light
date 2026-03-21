"""Database connection pool implementation."""
from __future__ import annotations

import os
import asyncio
import logging
from typing import Optional

import asyncpg
from asyncpg import create_pool

from db import get_supabase_client

logger = logging.getLogger(__name__)


class DatabasePool:
    """Async PostgreSQL connection pool manager."""
    
    _instance: Optional[DatabasePool] = None
    _pool: Optional[asyncpg.Pool] = None
    
    def __new__(cls) -> DatabasePool:
        """Singleton pattern for database pool."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self, database_url: str, min_size: int = 10, max_size: int = 20):
        """Initialize the connection pool."""
        try:
            self._pool = await create_pool(
                database_url,
                min_size=min_size,
                max_size=max_size,
                command_timeout=60,
                server_settings={
                    'application_name': 'calculo_tracao_api',
                    'jit': 'off'  # Disable JIT for better performance
                }
            )
            logger.info(f"Database pool initialized: min={min_size}, max={max_size}")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def execute(self, query: str, *args, timeout: Optional[float] = None):
        """Execute a query and return results."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")
        
        async with self._pool.acquire() as conn:
            try:
                if args:
                    result = await conn.fetch(query, *args, timeout=timeout)
                else:
                    result = await conn.fetch(query, timeout=timeout)
                return result
            except Exception as e:
                logger.error(f"Query execution failed: {query[:100]}... - {e}")
                raise
    
    async def execute_many(self, query: str, args_list: list, timeout: Optional[float] = None):
        """Execute multiple queries in a transaction."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")
        
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                try:
                    results = []
                    for args in args_list:
                        if args:
                            result = await conn.fetch(query, *args, timeout=timeout)
                        else:
                            result = await conn.fetch(query, timeout=timeout)
                        results.append(result)
                    return results
                except Exception as e:
                    logger.error(f"Batch execution failed: {query[:100]}... - {e}")
                    raise
    
    async def execute_val(self, query: str, *args, timeout: Optional[float] = None):
        """Execute a query and return a single value."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")
        
        async with self._pool.acquire() as conn:
            try:
                if args:
                    result = await conn.fetchval(query, *args, timeout=timeout)
                else:
                    result = await conn.fetchval(query, timeout=timeout)
                return result
            except Exception as e:
                logger.error(f"Value query execution failed: {query[:100]}... - {e}")
                raise
    
    async def get_pool_stats(self) -> dict:
        """Get connection pool statistics."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")
        
        pool = self._pool
        return {
            "size": pool.get_size(),
            "min_size": pool.get_min_size(),
            "max_size": pool.get_max_size(),
            "idle_connections": pool.get_idle_size(),
            "active_connections": pool.get_size() - pool.get_idle_size()
        }
    
    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            await self.execute_val("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")


# Global pool instance
db_pool = DatabasePool()


async def get_db_pool() -> DatabasePool:
    """Get the database pool instance."""
    return db_pool


async def initialize_db_pool() -> DatabasePool:
    """Initialize the database pool with settings from environment."""
    from . import get_supabase_client
    
    # Get database URL from environment or Supabase client
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        supabase = get_supabase_client()
        database_url = supabase.database_url
    
    if not database_url:
        raise ValueError("DATABASE_URL not configured")
    
    # Get pool settings
    min_size = int(os.getenv("DB_POOL_MIN_SIZE", "10"))
    max_size = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
    
    await db_pool.initialize(database_url, min_size, max_size)
    return db_pool


# Dependency injection for FastAPI
async def get_database() -> DatabasePool:
    """FastAPI dependency for database pool."""
    if db_pool._pool is None:
        await initialize_db_pool()
    return db_pool
