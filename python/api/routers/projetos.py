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
    ProjetoUpdate,
    BatchSalvarCalculoIn,
)
from services.projeto_service import ProjetoService
from repositories.projeto_repository import ProjetoRepository
from core.exceptions import NotFoundError, PermissionError, ValidationError
from db import get_supabase_client
from api.dependencies import get_supabase_dependency

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Projetos"])


async def get_projeto_service() -> ProjetoService:
    """Dependency injection for ProjetoService."""
    from db.pool import db_pool
    projeto_repository = ProjetoRepository(db_pool)
    return ProjetoService(projeto_repository)


@router.get("/projetos")
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


@router.post("/projetos", response_model=ProjetoOut, status_code=201)
async def create_projeto(
    inp: ProjetoIn,
    user: CurrentUser = Depends(require_mutation_identity),
    projeto_service: ProjetoService = Depends(get_projeto_service),
) -> ProjetoOut:
    """Cria um novo projeto. Retorna o projeto com id gerado."""
    from models.projeto import ProjetoCreate
    from uuid import UUID
    try:
        # Instanciar ProjetoCreate com defaults seguros para Guest Mode
        projeto_in = ProjetoCreate(
            orgao=inp.orgao or "CONVIDADO",
            ns=inp.ns or "S/N",
            nome=inp.nome or "Projeto Convidado",
            endereco=inp.endereco or "",
            estudado_por=inp.estudado_por or "Convidado",
            matricula=inp.matricula or "0000",
            data_estudo=inp.data_estudo,
            owner_id=UUID(str(user.user_id)),
        )

        projeto = await projeto_service.create_projeto(projeto_in, UUID(str(user.user_id)))
        return ProjetoOut(**projeto.model_dump(mode='json'))
    except (NotFoundError, PermissionError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error creating projeto: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar projeto")


@router.post("/projetos/{projeto_id}/pontos", response_model=PontoOut, status_code=201)
async def create_ponto(
    projeto_id: str,
    inp: PontoIn,
    user: CurrentUser = Depends(require_mutation_identity),
    supabase: object = Depends(get_supabase_dependency),
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
    supabase: object = Depends(get_supabase_dependency),
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


@router.post("/projetos/batch-save", status_code=200)
async def batch_save(
    inp: BatchSalvarCalculoIn,
    user: CurrentUser = Depends(require_mutation_identity),
    supabase: object = Depends(get_supabase_dependency),
) -> dict:
    """Persistência atômica de Projeto, Ponto e Cálculo em uma única chamada."""
    await _ensure_supabase_available(supabase)

    # Note: user_can_access check skipped if projeto_id is None (new project)
    # If projeto_id is provided, we check access
    if inp.projeto_id:
        can_access = await supabase.user_can_access_projeto(
            projeto_id=str(inp.projeto_id),
            user_id=user.user_id,
        )
        if not can_access:
            raise HTTPException(status_code=403, detail="Sem permissão para este projeto")

    res = await supabase.save_batch_calculo(
        owner_id=user.user_id,
        projeto_id=str(inp.projeto_id) if inp.projeto_id else None,
        projeto_dados=inp.projeto_dados.model_dump() if inp.projeto_dados else None,
        ponto_dados=inp.ponto_dados.model_dump(),
        niveis=[nivel.model_dump() for nivel in inp.niveis],
        resultado=inp.resultado.model_dump(),
    )

    if "error" in res:
        raise HTTPException(status_code=500, detail=res["error"])

    return res


# ── Novos Endpoints de Gerenciamento ─────────────────────────────────────

@router.put("/projetos/{projeto_id}", response_model=ProjetoOut)
async def update_projeto(
    projeto_id: str,
    inp: ProjetoUpdate,
    user: CurrentUser = Depends(require_mutation_identity),
    projeto_service: ProjetoService = Depends(get_projeto_service),
) -> ProjetoOut:
    """Atualiza dados do cabeçalho de um projeto."""
    try:
        projeto = await projeto_service.update_projeto(
            UUID(projeto_id), 
            inp, 
            UUID(str(user.user_id))
        )
        return ProjetoOut(**projeto.model_dump(mode='json'))
    except (NotFoundError, PermissionError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error updating projeto {projeto_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar projeto")


@router.delete("/projetos/{projeto_id}", status_code=204)
async def delete_projeto(
    projeto_id: str,
    user: CurrentUser = Depends(require_mutation_identity),
    projeto_service: ProjetoService = Depends(get_projeto_service),
):
    """Exclui um projeto. Falha se houver pontos vinculados (Soft Delete)."""
    try:
        await projeto_service.delete_projeto(
            UUID(projeto_id), 
            UUID(str(user.user_id))
        )
        return None
    except (NotFoundError, PermissionError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error deleting projeto {projeto_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao excluir projeto")


async def _ensure_supabase_available(supabase):
    """Verifica se o cliente de persistência está ativo."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
