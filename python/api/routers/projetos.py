"""Router para endpoints de gerenciamento de projetos e pontos."""

from __future__ import annotations

import time
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from uuid import UUID

from api.auth import (
    CurrentUser,
    require_mutation_identity,
)
from api.auth_standard import (
    WriteUser,
    AdminUser,
    validate_write_endpoint,
    validate_admin_endpoint,
    log_auth_attempt,
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
from core.operation_context import bind_operation_context, build_operation_context
from db import get_supabase_client
from api.dependencies import get_supabase_dependency
from monitoring.snapshot_metrics import get_snapshot_tracker

logger = structlog.get_logger(__name__)

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
        return [projeto.model_dump() for projeto in projetos]
    except (NotFoundError, PermissionError, ValidationError) as e:
        raise _map_domain_exception(e)
    except Exception as e:
        logger.error(f"Error listing projetos: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao listar projetos")


@router.post("/projetos", response_model=ProjetoOut, status_code=201)
async def create_projeto(
    request: Request,
    inp: ProjetoIn,
    user: CurrentUser = Depends(require_mutation_identity),
    projeto_service: ProjetoService = Depends(get_projeto_service),
) -> ProjetoOut:
    """Cria um novo projeto. Retorna o projeto com id gerado."""
    from models.projeto import ProjetoCreate
    from uuid import UUID
    bind_operation_context(request, user_id=str(user.user_id))
    logger.info(
        "projeto_create_started",
        **build_operation_context(request, user_id=str(user.user_id)),
    )
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
        projeto_id = str(projeto.id)
        bind_operation_context(
            request,
            projeto_id=projeto_id,
            user_id=str(user.user_id),
        )
        await _log_activity_event(
            request,
            activity_type="projeto_created",
            user_id=str(user.user_id),
            projeto_id=projeto_id,
            result="success",
        )
        logger.info(
            "projeto_create_succeeded",
            **build_operation_context(
                request,
                projeto_id=projeto_id,
                user_id=str(user.user_id),
                result="success",
            ),
        )
        return ProjetoOut(**projeto.model_dump(mode='json'))
    except (NotFoundError, PermissionError, ValidationError) as e:
        logger.warning(
            "projeto_create_failed",
            **build_operation_context(
                request,
                user_id=str(user.user_id),
                result="error",
                error=str(e),
            ),
        )
        raise _map_domain_exception(e)
    except Exception as e:
        logger.error(
            "projeto_create_failed",
            **build_operation_context(
                request,
                user_id=str(user.user_id),
                result="error",
                error=str(e),
            ),
        )
        raise HTTPException(status_code=500, detail="Erro ao criar projeto")


@router.post("/projetos/{projeto_id}/pontos", response_model=PontoOut, status_code=201)
async def create_ponto(
    request: Request,
    projeto_id: str,
    inp: PontoIn,
    user: CurrentUser = Depends(require_mutation_identity),
    supabase: object = Depends(get_supabase_dependency),
) -> PontoOut:
    """Adiciona um novo ponto (poste) a um projeto existente."""
    bind_operation_context(
        request,
        projeto_id=projeto_id,
        user_id=str(user.user_id),
    )
    logger.info(
        "ponto_create_started",
        **build_operation_context(
            request,
            projeto_id=projeto_id,
            user_id=str(user.user_id),
            ponto=inp.ponto,
        ),
    )
    await _ensure_supabase_available(supabase)

    projeto_exists = await supabase.projeto_exists(projeto_id)
    if not projeto_exists:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

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
        logger.warning(
            "ponto_create_failed",
            **build_operation_context(
                request,
                projeto_id=projeto_id,
                user_id=str(user.user_id),
                result="error",
                ponto=inp.ponto,
                error="duplicate_or_persistence_error",
            ),
        )
        raise HTTPException(
            status_code=409,
            detail=f"Ponto '{inp.ponto}' já existe neste projeto ou erro de persistência",
        )
    bind_operation_context(
        request,
        projeto_id=projeto_id,
        ponto_id=ponto_id,
        user_id=str(user.user_id),
    )
    await _log_activity_event(
        request,
        activity_type="ponto_created",
        user_id=str(user.user_id),
        projeto_id=projeto_id,
        ponto_id=ponto_id,
        result="success",
        ponto=inp.ponto,
    )
    logger.info(
        "ponto_create_succeeded",
        **build_operation_context(
            request,
            projeto_id=projeto_id,
            ponto_id=ponto_id,
            user_id=str(user.user_id),
            result="success",
            ponto=inp.ponto,
        ),
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
    request: Request,
    ponto_id: str,
    inp: SalvarCalculoIn,
    user: CurrentUser = Depends(require_mutation_identity),
    supabase: object = Depends(get_supabase_dependency),
) -> dict:
    """Persiste travessias + resultado do cálculo para um ponto.

    Deve ser chamado logo após /calcular retornar com sucesso.
    Idempotente: reescreve completamente o estado salvo para esse ponto.
    """
    _t0 = time.monotonic()
    tracker = get_snapshot_tracker()
    tracker.record_save_attempt()
    projeto_id = await _resolve_projeto_id_for_ponto(supabase, ponto_id)
    bind_operation_context(
        request,
        projeto_id=projeto_id,
        ponto_id=ponto_id,
        user_id=str(user.user_id),
    )
    logger.info(
        "snapshot_save_started",
        **build_operation_context(
            request,
            projeto_id=projeto_id,
            ponto_id=ponto_id,
            user_id=str(user.user_id),
        ),
    )

    await _ensure_supabase_available(supabase)

    ponto_exists = await supabase.ponto_exists(ponto_id)
    if not ponto_exists:
        raise HTTPException(status_code=404, detail="Ponto não encontrado")

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
        logger.warning(
            "snapshot_save_failed",
            **build_operation_context(
                request,
                projeto_id=projeto_id,
                ponto_id=ponto_id,
                user_id=str(user.user_id),
                result="error",
                error="persistence_failed",
            ),
        )
        raise HTTPException(status_code=500, detail="Erro ao persistir cálculo")

    duration_ms = round((time.monotonic() - _t0) * 1000, 2)
    tracker.record_save(duration_ms)
    await _log_activity_event(
        request,
        activity_type="snapshot_saved",
        user_id=str(user.user_id),
        projeto_id=projeto_id,
        ponto_id=ponto_id,
        result="success",
        duration_ms=duration_ms,
    )
    logger.info(
        "snapshot_save_succeeded",
        **build_operation_context(
            request,
            projeto_id=projeto_id,
            ponto_id=ponto_id,
            user_id=str(user.user_id),
            result="success",
            duration_ms=duration_ms,
        ),
    )
    return {"saved": True, "ponto_id": ponto_id}


@router.get("/pontos/{ponto_id}/snapshot", status_code=200)
async def obter_snapshot_ponto(
    request: Request,
    ponto_id: str,
    user: CurrentUser = Depends(require_mutation_identity),
    supabase: object = Depends(get_supabase_dependency),
) -> dict:
    """Retorna o snapshot persistido (niveis/travessias/resultado) de um ponto."""
    projeto_id = await _resolve_projeto_id_for_ponto(supabase, ponto_id)
    bind_operation_context(
        request,
        projeto_id=projeto_id,
        ponto_id=ponto_id,
        user_id=str(user.user_id),
    )
    logger.info(
        "snapshot_get_started",
        **build_operation_context(
            request,
            projeto_id=projeto_id,
            ponto_id=ponto_id,
            user_id=str(user.user_id),
        ),
    )
    await _ensure_supabase_available(supabase)

    ponto_exists = await supabase.ponto_exists(ponto_id)
    if not ponto_exists:
        raise HTTPException(status_code=404, detail="Ponto não encontrado")

    can_access = await supabase.user_can_access_ponto(
        ponto_id=ponto_id,
        user_id=user.user_id,
    )
    if not can_access:
        raise HTTPException(status_code=403, detail="Sem permissão para este ponto")

    _t0 = time.monotonic()
    snapshot = await supabase.get_calculo_snapshot(ponto_id)
    if not snapshot:
        logger.warning(
            "snapshot_get_failed",
            **build_operation_context(
                request,
                projeto_id=projeto_id,
                ponto_id=ponto_id,
                user_id=str(user.user_id),
                result="error",
                error="snapshot_not_available",
            ),
        )
        raise HTTPException(status_code=404, detail="Snapshot ainda não disponível para este ponto")

    duration_ms = round((time.monotonic() - _t0) * 1000, 2)
    get_snapshot_tracker().record_retrieve(duration_ms)
    await _log_activity_event(
        request,
        activity_type="snapshot_retrieved",
        user_id=str(user.user_id),
        projeto_id=projeto_id,
        ponto_id=ponto_id,
        result="success",
        duration_ms=duration_ms,
    )
    logger.info(
        "snapshot_get_succeeded",
        **build_operation_context(
            request,
            projeto_id=projeto_id,
            ponto_id=ponto_id,
            user_id=str(user.user_id),
            result="success",
            duration_ms=duration_ms,
        ),
    )
    return snapshot


@router.post("/projetos/batch-save", status_code=200)
async def batch_save(
    request: Request,
    inp: BatchSalvarCalculoIn,
    user: CurrentUser = Depends(require_mutation_identity),
    supabase: object = Depends(get_supabase_dependency),
) -> dict:
    """Persistência atômica de Projeto, Ponto e Cálculo em uma única chamada."""
    projeto_id = str(inp.projeto_id) if inp.projeto_id else None
    bind_operation_context(
        request,
        projeto_id=projeto_id,
        user_id=str(user.user_id),
    )
    logger.info(
        "batch_save_started",
        **build_operation_context(
            request,
            projeto_id=projeto_id,
            user_id=str(user.user_id),
        ),
    )
    await _ensure_supabase_available(supabase)

    # Note: user_can_access check skipped if projeto_id is None (new project)
    # If projeto_id is provided, we check access
    if inp.projeto_id:
        projeto_exists = await supabase.projeto_exists(str(inp.projeto_id))
        if not projeto_exists:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")

        can_access = await supabase.user_can_access_projeto(
            projeto_id=str(inp.projeto_id),
            user_id=user.user_id,
        )
        if not can_access:
            raise HTTPException(status_code=403, detail="Sem permissão para este projeto")

    _t0 = time.monotonic()
    res = await supabase.save_batch_calculo(
        owner_id=user.user_id,
        projeto_id=str(inp.projeto_id) if inp.projeto_id else None,
        projeto_dados=inp.projeto_dados.model_dump() if inp.projeto_dados else None,
        ponto_dados=inp.ponto_dados.model_dump(),
        niveis=[nivel.model_dump() for nivel in inp.niveis],
        resultado=inp.resultado.model_dump(),
    )

    if "error" in res:
        logger.warning(
            "batch_save_failed",
            **build_operation_context(
                request,
                projeto_id=projeto_id,
                user_id=str(user.user_id),
                result="error",
                error=res["error"],
            ),
        )
        raise HTTPException(status_code=500, detail=res["error"])

    final_projeto_id = res.get("projeto_id") or projeto_id
    final_ponto_id = res.get("ponto_id")
    duration_ms = round((time.monotonic() - _t0) * 1000, 2)
    get_snapshot_tracker().record_batch_save(duration_ms)
    bind_operation_context(
        request,
        projeto_id=final_projeto_id,
        ponto_id=final_ponto_id,
        user_id=str(user.user_id),
    )
    await _log_activity_event(
        request,
        activity_type="batch_save_completed",
        user_id=str(user.user_id),
        projeto_id=final_projeto_id,
        ponto_id=final_ponto_id,
        result="success",
        duration_ms=duration_ms,
    )
    logger.info(
        "batch_save_succeeded",
        **build_operation_context(
            request,
            projeto_id=final_projeto_id,
            ponto_id=final_ponto_id,
            user_id=str(user.user_id),
            result="success",
            duration_ms=duration_ms,
        ),
    )
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
        raise _map_domain_exception(e)
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
        raise _map_domain_exception(e)
    except Exception as e:
        logger.error(f"Error deleting projeto {projeto_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao excluir projeto")


async def _ensure_supabase_available(supabase):
    """Verifica se o cliente de persistência está ativo."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database connection unavailable")


def _map_domain_exception(error: Exception) -> HTTPException:
    """Map domain errors to semantic HTTP status codes."""
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=404, detail=error.message)
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail=error.message)
    if isinstance(error, ValidationError):
        return HTTPException(status_code=422, detail=error.message)
    return HTTPException(status_code=400, detail=str(error))


async def _resolve_projeto_id_for_ponto(
    supabase: object,
    ponto_id: str,
) -> Optional[str]:
    """Best-effort lookup to enrich correlation for snapshot operations."""
    resolver = getattr(supabase, "get_projeto_id_by_ponto", None)
    if resolver is None:
        return None
    return await resolver(ponto_id)


async def _log_activity_event(
    request: Request,
    *,
    activity_type: str,
    user_id: Optional[str],
    projeto_id: Optional[str] = None,
    ponto_id: Optional[str] = None,
    **details,
) -> None:
    """Persist best-effort operational audit trail without breaking flow."""
    from db.pool import db_pool

    repository = ProjetoRepository(db_pool)
    payload = build_operation_context(
        request,
        projeto_id=projeto_id,
        ponto_id=ponto_id,
        user_id=user_id,
        **details,
    )

    user_uuid = UUID(user_id) if user_id else None
    projeto_uuid = UUID(projeto_id) if projeto_id else None
    await repository._log_activity(
        activity_type=activity_type,
        user_id=user_uuid,
        projeto_id=projeto_uuid,
        details=payload,
    )
