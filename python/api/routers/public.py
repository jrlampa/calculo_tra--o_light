"""Router para endpoints públicos de lookup."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from translated.plan1_tables import CABOS_POR_REDE, CABOS_TABLE, POSTE_TABLE, REDE_TABLE
from api.dependencies import get_supabase_dependency, run_supabase_lookup

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Publico"])
@router.get("/cabos")
async def list_public_cabos(supabase: object = Depends(get_supabase_dependency)) -> list:
    """Lista pública de cabos."""
    return await run_supabase_lookup(supabase, supabase.fetch_cabos)


@router.get("/postes")
async def list_public_postes(supabase: object = Depends(get_supabase_dependency)) -> list:
    """Lista pública de postes."""
    return await run_supabase_lookup(supabase, supabase.fetch_postes)


@router.get("/redes")
async def list_public_redes(supabase: object = Depends(get_supabase_dependency)) -> list:
    """Lista pública de redes."""
    return await run_supabase_lookup(supabase, supabase.fetch_redes)


@router.get("/normas")
async def list_public_normas(
    categoria: Optional[str] = None,
    supabase: object = Depends(get_supabase_dependency)
) -> list:
    """Lista pública de normas e regras."""
    if categoria:
        return await run_supabase_lookup(
            supabase,
            lambda: supabase.fetch_normas_by_categoria(categoria)
        )
    return await run_supabase_lookup(supabase, supabase.fetch_normas)


@router.get("/public/normas/categorias")
async def list_public_normas_categorias(supabase: object = Depends(get_supabase_dependency)) -> dict:
    """Lista pública de categorias de normas."""
    return await run_supabase_lookup(supabase, supabase.fetch_normas_categorias)


@router.get("/config")
async def get_config() -> dict:
    """Retorna opções de lookup a partir das tabelas traduzidas do workbook."""
    try:
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
    except Exception:
        logger.exception("Erro em /api/config")
        raise HTTPException(status_code=500, detail="Erro interno ao carregar configuracoes")
