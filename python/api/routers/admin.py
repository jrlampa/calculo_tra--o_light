"""Router para endpoints administrativos."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_supabase_dependency, ensure_supabase_available, run_supabase_lookup

from api.auth import (
    CurrentUser,
    require_admin,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/cabos")
async def list_admin_cabos(
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency)
) -> list:
    """Lista administrativa de cabos."""
    return await run_supabase_lookup(supabase, supabase.fetch_cabos)


@router.post("/cabos")
async def create_cabo(
    nome: str,
    diametro: float,
    peso: float,
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency),
):
    """Cria um novo cabo."""
    await ensure_supabase_available(supabase)
    try:
        result = await supabase.insert_cabo(nome, diametro, peso)
    except Exception:
        logger.exception("Erro ao inserir cabo no Supabase")
        raise HTTPException(
            status_code=503,
            detail="Supabase indisponivel no momento. Tente novamente em instantes.",
        )

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
    await ensure_supabase_available(supabase)
    try:
        deleted = await supabase.delete_cabo(cable_id)
    except Exception:
        logger.exception("Erro ao deletar cabo no Supabase")
        raise HTTPException(
            status_code=503,
            detail="Supabase indisponivel no momento. Tente novamente em instantes.",
        )

    if not deleted:
        raise HTTPException(status_code=404, detail="Cabo nao encontrado para remocao")

    return {"success": True}


@router.get("/postes")
async def list_admin_postes(
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency)
) -> list:
    """Lista administrativa de postes."""
    return await run_supabase_lookup(supabase, supabase.fetch_postes)


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
    await ensure_supabase_available(supabase)
    try:
        result = await supabase.insert_poste(tipo, modelo, altura_m, carga_admissivel_dan)
    except Exception:
        logger.exception("Erro ao inserir poste no Supabase")
        raise HTTPException(
            status_code=503,
            detail="Supabase indisponivel no momento. Tente novamente em instantes.",
        )

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
    await ensure_supabase_available(supabase)
    try:
        deleted = await supabase.delete_poste(poste_id)
    except Exception:
        logger.exception("Erro ao deletar poste no Supabase")
        raise HTTPException(
            status_code=503,
            detail="Supabase indisponivel no momento. Tente novamente em instantes.",
        )

    if not deleted:
        raise HTTPException(status_code=404, detail="Poste nao encontrado para remocao")

    return {"success": True}


@router.get("/redes")
async def list_admin_redes(
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency)
) -> list:
    """Lista administrativa de redes."""
    return await run_supabase_lookup(supabase, supabase.fetch_redes)


@router.get("/normas")
async def list_admin_normas(
    categoria: Optional[str] = None,
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency),
):
    """Lista administrativa de normas e regras."""
    if categoria:
        return await run_supabase_lookup(
            supabase,
            lambda: supabase.fetch_normas_by_categoria(categoria)
        )
    return await run_supabase_lookup(supabase, supabase.fetch_normas)


@router.get("/normas/categorias")
async def list_admin_normas_categorias(
    _: CurrentUser = Depends(require_admin),
    supabase: object = Depends(get_supabase_dependency)
):
    """Lista administrativa de categorias de normas."""
    return await run_supabase_lookup(supabase, supabase.fetch_normas_categorias)
