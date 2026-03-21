"""Dependency injection utilities for FastAPI."""
from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends

from db import get_supabase_client
from repositories.projeto_repository import ProjetoRepository
from services.projeto_service import ProjetoService


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
    projeto_repository: ProjetoRepository = Depends(get_projeto_repository)
) -> AsyncGenerator[ProjetoService, None]:
    """Dependency injection for ProjetoService."""
    yield ProjetoService(projeto_repository)
