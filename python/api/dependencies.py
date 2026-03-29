"""Dependency injection utilities for FastAPI.

The provided code defines dependency injection functions for FastAPI services related to projects
and posts.  It also exports the shared Supabase availability helpers used by both the admin and
public routers — keeping the helpers in one place (DRY).
"""

from __future__ import annotations

from typing import AsyncGenerator, Callable

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_supabase_client, get_db
from repositories.projeto_repository import ProjetoRepository
from repositories.poste_repository import PosteRepository
from services.projeto_service import ProjetoService
from services.poste_service import PosteService


# ── Shared Supabase helpers ───────────────────────────────────────────────────

async def ensure_supabase_available(supabase) -> None:
    """Raise HTTP 503 when the Supabase dependency is not reachable.

    Used by both the admin and public routers.  Raises:
        HTTPException(503): when Supabase is disabled or the pool is down.
    """
    if not supabase.is_enabled:
        raise HTTPException(
            status_code=503,
            detail="Supabase nao configurado. Defina DATABASE_URL no backend.",
        )

    try:
        pool = await supabase._get_pool()
        if pool is None:
            raise RuntimeError("Pool do Supabase indisponivel")
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Supabase indisponivel no momento. Tente novamente em instantes.",
        )


async def run_supabase_lookup(supabase, fetcher: Callable):
    """Check availability, execute *fetcher*, and surface DB errors as HTTP 503.

    Parameters:
        supabase: the injected Supabase client dependency.
        fetcher: a zero-argument async callable that performs the actual query.

    Raises:
        HTTPException(503): when Supabase is unavailable or the query fails.
    """
    await ensure_supabase_available(supabase)
    try:
        return await fetcher()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Supabase indisponivel no momento. Tente novamente em instantes.",
        )


# ── Service / Repository factories ───────────────────────────────────────────

async def get_supabase_dependency() -> AsyncGenerator:
    """Dependency injection for Supabase client."""
    supabase = get_supabase_client()
    try:
        yield supabase
    finally:
        # Cleanup if needed
        pass


async def get_projeto_repository() -> AsyncGenerator[ProjetoRepository, None]:
    """Dependency injection for ProjetoRepository."""
    supabase = get_supabase_client()
    yield ProjetoRepository(supabase)


async def get_projeto_service(
    projeto_repository: ProjetoRepository = Depends(get_projeto_repository),
) -> AsyncGenerator[ProjetoService, None]:
    """Dependency injection for ProjetoService."""
    yield ProjetoService(projeto_repository)


async def get_poste_repository(db: Session = Depends(get_db)) -> PosteRepository:
    """Dependency injection for PosteRepository (DDD aggregate root)."""
    return PosteRepository(db)


async def get_poste_service(
    poste_repository: PosteRepository = Depends(get_poste_repository),
) -> PosteService:
    """Dependency injection for PosteService (DDD business logic)."""
    return PosteService(poste_repository)
