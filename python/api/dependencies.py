"""Dependency injection utilities for FastAPI.

The provided code defines dependency injection functions for FastAPI services related to projects
and posts.
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.orm import Session

from db import get_supabase_client, get_db
from repositories.projeto_repository import ProjetoRepository
from repositories.poste_repository import PosteRepository
from services.projeto_service import ProjetoService
from services.poste_service import PosteService


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
