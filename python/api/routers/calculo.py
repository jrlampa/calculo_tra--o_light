"""Router para endpoints de cálculo de tração."""
from __future__ import annotations

import logging
import math
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from services.excel_import import extract_excel_to_input

from api.schemas import (
    CalculoInput,
    CalculoOutput,
    LevelResultOut,
    VetorOut,
    QDTInput,
    QDTOutput,
)
from translated.ponto_blocks import (
    BTTraversalInput,
    BTZeroTraversalInput,
    MTTraversalInput,
    RamaisTraversalInput,
    calcular_polo,
)
from translated.qdt_blocks import calcular_qdt, QDTInput as QDTLogicInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calcular", tags=["Cálculo"])


@router.post("/qdt", response_model=QDTOutput)
def calculate_qdt(inp: QDTInput) -> QDTOutput:
    """Run the Voltage Drop (QDT) calculation."""
    # Map Pydantic to Logic Input
    logic_in = QDTLogicInput(
        v_nominal_mt=inp.v_nominal_mt,
        v_nominal_bt=inp.v_nominal_bt,
        coef_perda=inp.coef_perda,
        reg_mt=inp.reg_mt,
        drop_mt_pct=inp.drop_mt_pct,
        drop_trafo_pct=inp.drop_trafo_pct,
        drop_bt1_pct=inp.drop_bt1_pct,
        drop_bt2_pct=inp.drop_bt2_pct,
    )
    res = calcular_qdt(logic_in)
    return QDTOutput(
        v_mt_initial=res.v_mt_initial,
        v_mt_node=res.v_mt_node,
        v_bt_start=res.v_bt_start,
        v_bt_node1=res.v_bt_node1,
        v_bt_node2=res.v_bt_node2,
        drop_total_pct=res.drop_total_pct,
    )


@router.post("/importar-excel", response_model=CalculoInput, tags=["Importação"])
async def importar_excel(file: UploadFile = File(...)) -> CalculoInput:
    """Import legacy Excel data to pre-fill the frontend form."""
    if not file.filename.lower().endswith((".xlsm", ".xlsx")):
        raise HTTPException(status_code=400, detail="Apenas arquivos .xlsm ou .xlsx são permitidos")
    
    try:
        content = await file.read()
        extracted_data = extract_excel_to_input(content)
        return extracted_data
    except Exception as e:
        logger.exception("Erro ao importar planilha: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao processar planilha: {str(e)}")


@router.post("", response_model=CalculoOutput)
def calcular(inp: CalculoInput) -> CalculoOutput:
    """Run the Ponto (1) calculation and return structured results."""
    # Convert Pydantic input to dataclasses used by ponto_blocks
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

    try:
        result = calcular_polo(
            mt1_inputs=mt1,
            mt2_inputs=mt2,
            bt_inputs=bt,
            btz_inputs=btz,
            ral_inputs=ral,
            tipo_poste=inp.poste.tipo_poste,
            modelo_poste=inp.poste.modelo_poste,
        )

        # Build vector list for clock diagram
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
    except (ValueError, ZeroDivisionError, ArithmeticError) as domain_err:
        logger.warning("Entrada inválida em /calcular: %s", domain_err)
        raise HTTPException(
            status_code=422,
            detail=f"Entrada fora do domínio operacional: {domain_err}",
        )
    except Exception:
        logger.exception("Erro interno durante /calcular")
        raise HTTPException(status_code=500, detail="Erro interno ao processar cálculo")
