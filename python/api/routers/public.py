"""Router para endpoints públicos de lookup."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from translated.plan1_tables import CABOS_POR_REDE, CABOS_TABLE, POSTE_TABLE, REDE_TABLE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Publico"])


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


@router.get("/public/normas/categorias")
async def list_public_normas_categorias(supabase: object = Depends()) -> dict:
    """Lista pública de categorias de normas."""
    return await _run_supabase_lookup(supabase, supabase.fetch_normas_categorias)


@router.get("/config")
async def get_config() -> dict:
    """Retorna opções de lookup a partir das tabelas traduzidas do workbook."""
    cabos_nomes = [str(row[0]) for row in CABOS_TABLE if row and row[0]]
    redes_nomes = [str(row[0]) for row in REDE_TABLE if row and row[0]]
    postes_por_tipo: dict[str, list[str]] = {
        str(tipo): [str(modelo[0]) for modelo in modelos if modelo and modelo[0]]
        for tipo, modelos in POSTE_TABLE.items()
    }

    return {
        "redes": redes_nomes,
        "cabos": cabos_nomes,
        "postes": postes_por_tipo,
        "cabos_por_rede": CABOS_POR_REDE,
    }
