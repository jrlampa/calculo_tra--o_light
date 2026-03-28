"""Router para endpoints CRUD de Poste (DDD Aggregate Root)."""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from api.auth import CurrentUser, require_mutation_identity
from api.dependencies import get_poste_service
from api.schemas import (
    CalculoInput,
    CalculoOutput,
    CondutorOut,
    PosteIn,
    PosteOut,
    TravessiaUpdateIn,
)
from domain.factories import PosteFactory
from domain.value_objects import NivelEnum
from services.calculo_service import calculo_service
from services.poste_service import PosteService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/postes", tags=["Postes (DDD)"])


# ─────────────────────── CRUD POSTES ──────────────────────────────

@router.post("", response_model=PosteOut, status_code=201)
async def criar_poste(
    projeto_id: UUID,
    inp: PosteIn,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> PosteOut:
    """Cria novo Poste (agregado raiz) em um projeto.
    
    O Poste é criado com 5 Niveis (MT1, MT2, BT, BTZ, RAL) × 4 Travessias cada.
    """
    try:
        poste = service.criar_poste(
            projeto_id=projeto_id,
            numero=inp.numero,
            tipo_poste=inp.tipo_poste,
            modelo_poste=inp.modelo_poste
        )
        logger.info("Poste %s criado em projeto %s", inp.numero, projeto_id)
        return PosteFactory.to_response_dict(poste)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Erro ao criar Poste: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao criar Poste") from e


@router.get("/{poste_id}", response_model=PosteOut)
async def obter_poste(
    poste_id: UUID,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> PosteOut:
    """Obtém detalhes completos de um Poste (agregado inteiro)."""
    poste = service.obter_poste(poste_id)
    if not poste:
        raise HTTPException(status_code=404, detail="Poste não encontrado")
    return PosteFactory.to_response_dict(poste)


@router.get("/projeto/{projeto_id}", response_model=list[PosteOut])
async def listar_postes_projeto(
    projeto_id: UUID,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> list[PosteOut]:
    """Lista todos os Postes de um projeto."""
    postes = service.listar_postes_do_projeto(projeto_id)
    return [PosteFactory.to_response_dict(p) for p in postes]


@router.put("/{poste_id}", response_model=PosteOut)
async def atualizar_poste(
    poste_id: UUID,
    inp: PosteIn,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> PosteOut:
    """Atualiza tipo_poste e modelo_poste."""
    try:
        poste = service.atualizar_poste(
            poste_id=poste_id,
            tipo_poste=inp.tipo_poste,
            modelo_poste=inp.modelo_poste
        )
        return PosteFactory.to_response_dict(poste)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Erro ao atualizar Poste: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao atualizar Poste") from e


@router.delete("/{poste_id}", status_code=204)
async def deletar_poste(
    poste_id: UUID,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
):
    """Soft delete um Poste (preserva histórico de cálculos)."""
    try:
        service.deletar_poste(poste_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# ─────────────────────── TRAVESSIAS ───────────────────────────────

@router.put(
    "/{poste_id}/niveis/{nivel}/travessias/{posicao}", response_model=PosteOut
)
async def atualizar_travessia(
    poste_id: UUID,
    nivel: str,
    posicao: int,
    inp: TravessiaUpdateIn,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> PosteOut:
    """Atualiza uma Travessia dentro de um Nivel de um Poste.
    
    Valida que 1 ≤ posicao ≤ 4 e que nivel ∈ {MT1, MT2, BT, BTZ, RAL}.
    """
    try:
        # Parse nivel enum
        nivel_enum = NivelEnum(nivel.upper())
        
        # Validate posicao
        if not 1 <= posicao <= 4:
            raise ValueError(f"Posição deve estar entre 1-4, recebeu {posicao}")
        
        # Update through service (goes through aggregate)
        poste = service.atualizar_travessia(
            poste_id=poste_id,
            nivel_enum=nivel_enum,
            posicao=posicao,
            tipo_rede=inp.tipo_rede,
            tipo_cabo=inp.tipo_cabo,
            vao=inp.vao,
            flecha=inp.flecha,
            angulo=inp.angulo,
        )
        return PosteFactory.to_response_dict(poste)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Erro ao atualizar Travessia: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao atualizar Travessia") from e


# ─────────────────────── NAVEGAÇÃO (O QUE ESTÁ NO POSTE) ─────────────────

@router.get("/projeto/{projeto_id}/numero/{numero}", response_model=PosteOut)
async def obter_poste_por_numero(
    projeto_id: UUID,
    numero: str,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> PosteOut:
    """Localiza um Poste pelo número dentro do projeto (chave natural).

    Use este endpoint para resolver "Poste 1 do Projeto X" sem precisar
    do UUID do poste.  O par (projeto_id, numero) é único.
    """
    poste = service.obter_poste_por_numero(projeto_id, numero)
    if not poste:
        raise HTTPException(
            status_code=404,
            detail=f"Poste '{numero}' não encontrado no projeto {projeto_id}",
        )
    return PosteFactory.to_response_dict(poste)


@router.get("/{poste_id}/condutores", response_model=list[CondutorOut])
async def listar_condutores_poste(
    poste_id: UUID,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> list[CondutorOut]:
    """Lista todos os condutores (cabos) instalados neste Poste.

    Percorre todos os Niveis × Travessias e devolve cada condutor com sua
    geometria.  Este é o endpoint canônico para responder "o que está
    pendurado no Poste?".
    """
    poste = service.obter_poste(poste_id)
    if not poste:
        raise HTTPException(status_code=404, detail="Poste não encontrado")
    return poste.obter_condutores()


# ─────────────────────── CÁLCULOS ────────────────────────────────

@router.post("/{poste_id}/calcular", response_model=CalculoOutput)
async def calcular_poste(
    poste_id: UUID,
    inp: CalculoInput,
    user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> CalculoOutput:
    """Calcula forças num Poste e salva snapshot de cálculo.

    Fluxo:
    1. Verifica existência do Poste
    2. Delega mapeamento e cálculo ao CalculoService
    3. Persiste resultado como snapshot append-only
    4. Retorna CalculoOutput
    """
    try:
        poste = service.obter_poste(poste_id)
        if not poste:
            raise HTTPException(status_code=404, detail="Poste não encontrado")

        output, resultado = calculo_service.calcular_com_resultado(inp)

        snapshot_id = service.registrar_calculo(
            poste_id=poste_id,
            resultado=resultado,
            calculado_por=str(user.user_id),
            status="saved",
        )
        logger.info(
            "Cálculo registrado para Poste %s, snapshot %s", poste_id, snapshot_id
        )
        return output

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Entrada inválida em cálculo: %s", e)
        raise HTTPException(status_code=422, detail=f"Erro: {str(e)}") from e
    except Exception as e:
        logger.error("Erro ao calcular Poste: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar cálculo",
        ) from e


@router.get("/{poste_id}/calculos")
async def obter_historico_calculos(
    poste_id: UUID,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> list[dict]:
    """Obtém histórico de cálculos de um Poste (append-only snapshots).
    
    Retorna lista de snapshots mais recentes primeiro.
    """
    try:
        return service.obter_historico_calculos(poste_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{poste_id}/ultimo-calculo")
async def obter_ultimo_calculo(
    poste_id: UUID,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> dict:
    """Obtém o cálculo mais recente de um Poste."""
    try:
        ultimo = service.obter_ultimocalculo(poste_id)
        if not ultimo:
            raise HTTPException(status_code=404, detail="Nenhum cálculo encontrado para este Poste")
        return ultimo
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
