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
    ClonarPosteIn,
    CondutorOut,
    LinhagemEntry,
    PosteIn,
    PosteLinhagem,
    PosteOut,
    PosteVincularIn,
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


# ─────────────────────── LINHAGEM (cross-project audit trail) ────────────────

@router.put("/{poste_id}/vincular-origem", response_model=PosteOut)
async def vincular_origem(
    poste_id: UUID,
    inp: PosteVincularIn,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> PosteOut:
    """Vincula este Poste ao seu ancestral em um projeto anterior.

    Use quando o Projeto Y herda um poste físico que já foi estudado no
    Projeto X.  O par (poste_id, origem_id) estabelece o elo de linhagem:
    dados do Projeto Y (mais recente) têm prioridade; o histórico completo
    de ambos os projetos fica disponível via GET /linhagem.

    Regras:
    - Ambos os Postes devem existir e não estar deletados.
    - Devem pertencer a projetos **diferentes**.
    - Um Poste não pode ser sua própria origem.
    """
    try:
        origem_uuid = UUID(inp.origem_id)
        poste = service.vincular_origem(poste_id, origem_uuid)
        return PosteFactory.to_response_dict(poste)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Erro ao vincular origem do Poste: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao vincular origem") from e


@router.get("/{poste_id}/linhagem", response_model=PosteLinhagem)
async def obter_linhagem(
    poste_id: UUID,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> PosteLinhagem:
    """Retorna a cadeia completa de linhagem cross-projeto de um Poste.

    A cadeia é ordenada do ancestral mais antigo (índice 0) ao Poste
    atual (último elemento).  Use ``atualizado_em`` para determinar qual
    projeto tem os dados mais recentes (política timestamp-mais-novo-vence).

    Use este endpoint para:
    - Auditar quais projetos modificaram um poste físico e em que ordem.
    - Recuperar configurações anteriores de um poste físico.
    - Rastrear a evolução de um poste ao longo de múltiplos estudos.
    """
    try:
        chain_data = service.obter_linhagem(poste_id)
        entries = [LinhagemEntry(**entry) for entry in chain_data]
        return PosteLinhagem(
            poste_id=str(poste_id),
            chain=entries,
            profundidade=len(entries),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{poste_id}/clonar-para-projeto", response_model=PosteOut, status_code=201)
async def clonar_para_projeto(
    poste_id: UUID,
    inp: ClonarPosteIn,
    _user: CurrentUser = Depends(require_mutation_identity),
    service: PosteService = Depends(get_poste_service),
) -> PosteOut:
    """Clona um Poste para outro Projeto, estabelecendo o elo de linhagem.

    Use este endpoint quando o Projeto Y herda um poste físico que já foi
    estudado no Projeto X:

    1. O Poste de origem (``poste_id``, no Projeto X) é carregado.
    2. Toda a configuração (Niveis, Travessias, tipo/modelo) é copiada.
    3. O clone é criado no ``projeto_id`` informado (Projeto Y).
    4. ``clone.origem_id`` é automaticamente definido como ``poste_id``.
    5. O clone tem timestamp recente — é imediatamente reconhecido como o
       dado mais atual para aquele poste físico (política timestamp-wins).

    O clone pode ser modificado livremente no Projeto Y sem afetar os
    dados do Projeto X.
    """
    try:
        projeto_destino_uuid = UUID(inp.projeto_id)
        clone = service.clonar_para_projeto(poste_id, projeto_destino_uuid)
        return PosteFactory.to_response_dict(clone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Erro ao clonar Poste: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao clonar Poste") from e
