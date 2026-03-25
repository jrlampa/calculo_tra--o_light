"""Router para endpoints CRUD de Poste (DDD Aggregate Root)."""
from __future__ import annotations

import logging
import math
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from api.auth import CurrentUser, require_mutation_identity
from api.dependencies import get_poste_service
from api.schemas import (
    CalculoInput,
    CalculoOutput,
    LevelResultOut,
    VetorOut,
    PosteIn,
    PosteOut,
)
from domain.factories import PosteFactory
from domain.value_objects import NivelEnum, CalculoResultado
from services.poste_service import PosteService
from translated.ponto_blocks import (
    BTTraversalInput,
    BTZeroTraversalInput,
    MTTraversalInput,
    RamaisTraversalInput,
    calcular_polo,
)

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
    tipo_rede: str,
    tipo_cabo: str,
    vao: float,
    flecha: float,
    angulo: float,
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
            tipo_rede=tipo_rede,
            tipo_cabo=tipo_cabo,
            vao=vao,
            flecha=flecha,
            angulo=angulo
        )
        return PosteFactory.to_response_dict(poste)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Erro ao atualizar Travessia: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao atualizar Travessia") from e


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
    1. Carrega agregado Poste pelo ID
    2. Converte CalculoInput para PosteAggregate (in-memory)
    3. Executa engine de cálculo
    4. Salva resultado como snapshot append-only
    5. Retorna CalculoOutput
    """
    try:
        # 1. Get Poste aggregate
        poste = service.obter_poste(poste_id)
        if not poste:
            raise HTTPException(status_code=404, detail="Poste não encontrado")
        
        # 2. Convert CalculoInput to PosteAggregate (override geometry)
        _ = PosteFactory.from_calculo_input(
            projeto_id=poste.projeto_id.value,
            calculo_input=inp
        )
        
        # 3. Convert to ponto_blocks input format
        mt1 = [
            MTTraversalInput(
                tipo_rede=t.tipo_rede, tipo_cabo=t.tipo_cabo,
                vao=t.vao, flecha=t.flecha, angulo=t.angulo,
                altura_poste=t.altura_poste, altura_ancoragem=t.altura_ancoragem,
            )
            for t in inp.mt1
        ]
        mt2 = [
            MTTraversalInput(
                tipo_rede=t.tipo_rede, tipo_cabo=t.tipo_cabo,
                vao=t.vao, flecha=t.flecha, angulo=t.angulo,
                altura_poste=t.altura_poste, altura_ancoragem=t.altura_ancoragem,
            )
            for t in inp.mt2
        ]
        bt = [
            BTTraversalInput(
                tipo_rede=t.tipo_rede, tipo_cabo=t.tipo_cabo,
                vao=t.vao, flecha=t.flecha, angulo=t.angulo,
                altura_poste=t.altura_poste, altura_ancoragem=t.altura_ancoragem,
            )
            for t in inp.bt
        ]
        btz = [
            BTZeroTraversalInput(
                qtd_ligacoes=t.qtd_ligacoes,
                vao=t.vao, flecha=t.flecha, angulo=t.angulo,
                altura_poste=t.altura_poste, altura_ancoragem=t.altura_ancoragem,
            )
            for t in inp.btz
        ]
        ral = [
            RamaisTraversalInput(
                tipo_cabo=t.tipo_cabo, qtd_cabos=t.qtd_cabos,
                vao=t.vao, flecha=t.flecha, angulo=t.angulo,
                altura_poste=t.altura_poste, altura_ancoragem=t.altura_ancoragem,
            )
            for t in inp.ral
        ]
        
        # 4. Run calculation engine
        result = calcular_polo(
            mt1_inputs=mt1,
            mt2_inputs=mt2,
            bt_inputs=bt,
            btz_inputs=btz,
            ral_inputs=ral,
            tipo_poste=inp.poste.tipo_poste,
            modelo_poste=inp.poste.modelo_poste,
        )
        
        # 5. Create CalculoResultado
        resultado = CalculoResultado(
            mt1_tracao=result.mt1.f_tip,
            mt1_angulo=result.mt1.angulo,
            mt2_tracao=result.mt2.f_tip,
            mt2_angulo=result.mt2.angulo,
            bt_tracao=result.bt.f_tip,
            bt_angulo=result.bt.angulo,
            btz_tracao=result.btz.f_tip,
            btz_angulo=result.btz.angulo,
            ral_tracao=result.ral.f_tip,
            ral_angulo=result.ral.angulo,
            total_tracao=result.total_tracao,
            total_angulo=result.total_angulo,
            poste_ecc=result.poste_ecc,
        )
        
        # 6. Register snapshot
        snapshot_id = service.registrar_calculo(
            poste_id=poste_id,
            resultado=resultado,
            calculado_por=str(user.user_id),
            status="saved"
        )
        logger.info(
            "Cálculo registrado para Poste %s, snapshot %s", poste_id, snapshot_id
        )
        
        # 7. Build vectors
        level_defs = [
            ("MT1", result.mt1.f_tip, result.mt1.angulo),
            ("MT2", result.mt2.f_tip, result.mt2.angulo),
            ("BT",  result.bt.f_tip,  result.bt.angulo),
            ("BTZ", result.btz.f_tip, result.btz.angulo),
            ("RAL", result.ral.f_tip, result.ral.angulo),
        ]
        vetores = [
            VetorOut(
                label=label,
                tracao_dan=f,
                angulo_graus=a,
                comp_x=f * math.cos(a * math.pi / 180),
                comp_y=f * math.sin(a * math.pi / 180),
            )
            for label, f, a in level_defs
            if f != 0
        ]
        
        # 8. Return response
        return CalculoOutput(
            mt1=LevelResultOut(
                tracao_dan=result.mt1.f_tip,
                angulo_graus=result.mt1.angulo,
                resultante_raw=result.mt1.resultante,
                texto=result.texto_mt1,
            ),
            mt2=LevelResultOut(
                tracao_dan=result.mt2.f_tip,
                angulo_graus=result.mt2.angulo,
                resultante_raw=result.mt2.resultante,
                texto=result.texto_mt2,
            ),
            bt=LevelResultOut(
                tracao_dan=result.bt.f_tip,
                angulo_graus=result.bt.angulo,
                resultante_raw=result.bt.resultante,
                texto=result.texto_bt,
            ),
            btz=LevelResultOut(
                tracao_dan=result.btz.f_tip,
                angulo_graus=result.btz.angulo,
                resultante_raw=result.btz.resultante,
                texto=result.texto_btz,
            ),
            ral=LevelResultOut(
                tracao_dan=result.ral.f_tip,
                angulo_graus=result.ral.angulo,
                resultante_raw=result.ral.resultante,
                texto=result.texto_ral,
            ),
            total_tracao_dan=result.total_tracao,
            total_angulo_graus=result.total_angulo,
            texto_total=result.texto_total,
            vetores=vetores,
            poste_ecc_dan=result.poste_ecc,
            status_poste=result.status_poste,
            resistencia_nominal=result.resistencia_nominal,
        )
        
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
