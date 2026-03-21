"""Router para endpoints públicos de lookup."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["Publico"])


async def _ensure_supabase_available(supabase) -> None:
    """Garante que o Supabase está disponível."""
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


async def _run_supabase_lookup(supabase, fetcher):
    """Executa uma operação de lookup no Supabase com tratamento de erro."""
    await _ensure_supabase_available(supabase)
    try:
        return await fetcher()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Supabase indisponivel no momento. Tente novamente em instantes.",
        )


@router.get("/cabos")
async def list_public_cabos(supabase: object = Depends()) -> list:
    """Lista pública de cabos."""
    return await _run_supabase_lookup(supabase, supabase.fetch_cabos)


@router.get("/postes")
async def list_public_postes(supabase: object = Depends()) -> list:
    """Lista pública de postes."""
    return await _run_supabase_lookup(supabase, supabase.fetch_postes)


@router.get("/redes")
async def list_public_redes(supabase: object = Depends()) -> list:
    """Lista pública de redes."""
    return await _run_supabase_lookup(supabase, supabase.fetch_redes)


@router.get("/normas")
async def list_public_normas(
    categoria: Optional[str] = None,
    supabase: object = Depends()
) -> list:
    """Lista pública de normas e regras."""
    if categoria:
        return await _run_supabase_lookup(
            supabase, 
            lambda: supabase.fetch_normas_by_categoria(categoria)
        )
    return await _run_supabase_lookup(supabase, supabase.fetch_normas)


@router.get("/normas/categorias")
async def list_public_normas_categorias(supabase: object = Depends()) -> dict:
    """Lista pública de categorias de normas."""
    return await _run_supabase_lookup(supabase, supabase.fetch_normas_categorias)
