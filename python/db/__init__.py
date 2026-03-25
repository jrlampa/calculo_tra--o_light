"""
Database module initialization.
This module provides database connection and client management.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import get_database_url

from .supabase_client import get_supabase_client, SupabaseClient
from .pool import get_db_pool, db_pool, initialize_db_pool


def _build_sync_database_url() -> str:
    url = get_database_url()
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


_sync_engine = create_engine(_build_sync_database_url(), future=True, pool_pre_ping=True)
_SessionLocal = sessionmaker(bind=_sync_engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for sync SQLAlchemy sessions used by DDD routes."""
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()

__all__ = [
    'get_supabase_client',
    'SupabaseClient', 
    'get_db_pool',
    'db_pool',
    'initialize_db_pool',
    'get_db'
]