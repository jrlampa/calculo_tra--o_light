"""Router para endpoints administrativos."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_supabase_dependency

from api.auth import (
    CurrentUser,
    require_admin,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


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


def _supabase_indisponivel_exc() -> HTTPException:
    logger.exception("Supabase indisponivel")
    return HTTPException(
        status_code=503,
        detail="Supabase indisponivel no momento. Tente novamente em instantes.",
    )


@router.get("/cabos")
async def list_admin_cabos(
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency)
) -> list:
    """Lista administrativa de cabos."""
    return await _run_supabase_lookup(supabase, supabase.fetch_cabos)


@router.post("/cabos")
async def create_cabo(
    nome: str,
    diametro: float,
    peso: float,
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency),
):
    """Cria um novo cabo."""
    await _ensure_supabase_available(supabase)
    try:
        result = await supabase.insert_cabo(nome, diametro, peso)
    except Exception:
        raise _supabase_indisponivel_exc()

    if result == {}:
        raise HTTPException(status_code=500, detail="Falha ao criar cabo")

    return result


@router.delete("/cabos/{cable_id}")
async def delete_cabo(
    cable_id: int, 
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency)
):
    """Remove um cabo."""
    await _ensure_supabase_available(supabase)
    try:
        deleted = await supabase.delete_cabo(cable_id)
    except Exception:
        raise _supabase_indisponivel_exc()

    if not deleted:
        raise HTTPException(status_code=404, detail="Cabo nao encontrado para remocao")

    return {"success": True}


@router.get("/postes")
async def list_admin_postes(
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency)
) -> list:
    """Lista administrativa de postes."""
    return await _run_supabase_lookup(supabase, supabase.fetch_postes)


@router.post("/postes")
async def create_poste(
    tipo: str,
    modelo: str,
    altura_m: float,
    carga_admissivel_dan: float,
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency),
):
    """Cria um novo poste."""
    await _ensure_supabase_available(supabase)
    try:
        result = await supabase.insert_poste(tipo, modelo, altura_m, carga_admissivel_dan)
    except Exception:
        raise _supabase_indisponivel_exc()

    if result == {}:
        raise HTTPException(status_code=500, detail="Falha ao criar poste")

    return result


@router.delete("/postes/{poste_id}")
async def delete_poste(
    poste_id: int, 
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency)
):
    """Remove um poste."""
    await _ensure_supabase_available(supabase)
    try:
        deleted = await supabase.delete_poste(poste_id)
    except Exception:
        raise _supabase_indisponivel_exc()

    if not deleted:
        raise HTTPException(status_code=404, detail="Poste nao encontrado para remocao")

    return {"success": True}


@router.get("/redes")
async def list_admin_redes(
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency)
) -> list:
    """Lista administrativa de redes."""
    return await _run_supabase_lookup(supabase, supabase.fetch_redes)


@router.get("/normas")
async def list_admin_normas(
    categoria: Optional[str] = None,
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency),
):
    """Lista administrativa de normas e regras."""
    if categoria:
        return await _run_supabase_lookup(
            supabase, 
            lambda: supabase.fetch_normas_by_categoria(categoria)
        )
    return await _run_supabase_lookup(supabase, supabase.fetch_normas)


@router.get("/normas/categorias")
async def list_admin_normas_categorias(
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency)
):
    """Lista administrativa de categorias de normas."""
    return await _run_supabase_lookup(supabase, supabase.fetch_normas_categorias)
