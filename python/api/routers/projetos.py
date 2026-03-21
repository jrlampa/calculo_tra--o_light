"""Router para endpoints de gerenciamento de projetos e pontos."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID

from api.auth import (
    CurrentUser,
    require_mutation_identity,
)
from api.schemas import (
    ProjetoIn,
    ProjetoOut,
    PontoIn,
    PontoOut,
    SalvarCalculoIn,
)
from services.projeto_service import ProjetoService
from repositories.projeto_repository import ProjetoRepository
from core.exceptions import NotFoundError, PermissionError, ValidationError
from db import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projetos", tags=["Projetos"])


async def get_projeto_service() -> ProjetoService:
    """Dependency injection for ProjetoService."""
    supabase = get_supabase_client()
    projeto_repository = ProjetoRepository(supabase)
    return ProjetoService(projeto_repository)


@router.get("")
async def list_projetos(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    user: CurrentUser = Depends(require_mutation_identity),
    projeto_service: ProjetoService = Depends(get_projeto_service),
) -> list:
    """Lista todos os projetos com contagem de pontos."""
    try:
        projetos = await projeto_service.get_projetos(
            user_id=user.user_id,
            skip=offset,
            limit=limit
        )
        return [projeto.dict() for projeto in projetos]
    except (NotFoundError, PermissionError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error listing projetos: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao listar projetos")


@router.post("", response_model=ProjetoOut, status_code=201)
async def create_projeto(
    inp: ProjetoIn,
    user: CurrentUser = Depends(require_mutation_identity),
    projeto_service: ProjetoService = Depends(get_projeto_service),
) -> ProjetoOut:
    """Cria um novo projeto. Retorna o projeto com id gerado."""
    try:
        # Convert input to service model
        projeto_create = {
            "orgao": inp.orgao,
            "ns": inp.ns,
            "nome": inp.nome,
            "endereco": inp.endereco,
            "estudado_por": inp.estudado_por,
            "matricula": inp.matricula,
            "data_estudo": inp.data_estudo,
            "owner_id": user.user_id
        }
        
        projeto = await projeto_service.create_projeto(projeto_create, user.user_id)
        return ProjetoOut(**projeto.dict())
    except (NotFoundError, PermissionError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error creating projeto: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar projeto")


@router.post("/{projeto_id}/pontos", response_model=PontoOut, status_code=201)
async def create_ponto(
    projeto_id: str,
    inp: PontoIn,
    user: CurrentUser = Depends(require_mutation_identity),
    supabase: object = Depends(),
) -> PontoOut:
    """Adiciona um novo ponto (poste) a um projeto existente."""
    await _ensure_supabase_available(supabase)

    can_access = await supabase.user_can_access_projeto(
        projeto_id=projeto_id,
        user_id=user.user_id,
    )
    if not can_access:
        raise HTTPException(status_code=403, detail="Sem permissão para este projeto")

    ponto_id = await supabase.save_ponto(
        projeto_id=projeto_id,
        ponto=inp.ponto,
        tipo_poste=inp.tipo_poste,
        modelo_poste=inp.modelo_poste,
    )
    if not ponto_id:
        raise HTTPException(
            status_code=409,
            detail=f"Ponto '{inp.ponto}' já existe neste projeto ou erro de persistência",
        )
    return PontoOut(
        id=ponto_id,
        projeto_id=projeto_id,
        ponto=inp.ponto,
        tipo_poste=inp.tipo_poste,
        modelo_poste=inp.modelo_poste,
    )


@router.post("/pontos/{ponto_id}/calculo", status_code=200)
async def salvar_calculo(
    ponto_id: str,
    inp: SalvarCalculoIn,
    user: CurrentUser = Depends(require_mutation_identity),
    supabase: object = Depends(),
) -> dict:
    """Persiste travessias + resultado do cálculo para um ponto.

    Deve ser chamado logo após /calcular retornar com sucesso.
    Idempotente: reescreve completamente o estado salvo para esse ponto.
    """
    await _ensure_supabase_available(supabase)

    if str(inp.ponto_id) != ponto_id:
        raise HTTPException(status_code=422, detail="ponto_id do payload difere da rota")

    can_access = await supabase.user_can_access_ponto(
        ponto_id=ponto_id,
        user_id=user.user_id,
    )
    if not can_access:
        raise HTTPException(status_code=403, detail="Sem permissão para este ponto")

    ok_snapshot = await supabase.save_calculo_snapshot(
        ponto_id,
        [nivel.model_dump() for nivel in inp.niveis],
        inp.resultado.model_dump(),
    )
    if not ok_snapshot:
        raise HTTPException(status_code=500, detail="Erro ao persistir cálculo")
    return {"saved": True, "ponto_id": ponto_id}
