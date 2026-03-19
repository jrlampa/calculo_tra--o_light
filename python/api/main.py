"""FastAPI application – tração de poste calculator.

Run with:
    cd python
    uvicorn api.main:app --reload --port 8000

The React Vite dev server proxies /api/* to http://localhost:8000.
"""
from __future__ import annotations

import math
import sys
import os
from typing import Optional

# Allow imports from the python/ directory when run as `uvicorn api.main:app`
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db import get_supabase_client

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
from translated.plan1_tables import CABOS_TABLE, REDE_TABLE, POSTE_TABLE, CABOS_POR_REDE

app = FastAPI(title="Calculo Tração Poste", version="1.0.0")

# Initialize Supabase client
supabase = get_supabase_client()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/config")
def get_config() -> dict:
    """Return all dropdown options from the Excel-parity tables."""
    return {
        "redes": [row[0] for row in REDE_TABLE],
        "cabos": [row[0] for row in CABOS_TABLE],
        "postes": {
            tipo: [m[0] for m in modelos]
            for tipo, modelos in POSTE_TABLE.items()
        },
        "cabos_por_rede": CABOS_POR_REDE
    }


@app.post("/calcular/qdt", response_model=QDTOutput)
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


@app.post("/calcular", response_model=CalculoOutput)
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
    )


# ============================================================================
# Admin Endpoints - Database Management
# ============================================================================

@app.get("/admin/cabos", tags=["Admin"])
async def list_cabos():
    """List all cables (falls back to Excel if Supabase unavailable)."""
    if supabase.is_enabled:
        try:
            return await supabase.fetch_cabos()
        except Exception:
            pass
    from translated.plan1_tables import CABOS_TABLE
    return [{"nome": row[0], "diametro": row[1], "peso": row[2]} for row in CABOS_TABLE]


@app.post("/admin/cabos", tags=["Admin"])
async def create_cabo(nome: str, diametro: float, peso: float):
    """Create new cable. Requires Supabase connection."""
    if not supabase.is_enabled:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    return await supabase.insert_cabo(nome, diametro, peso)


@app.delete("/admin/cabos/{cable_id}", tags=["Admin"])
async def delete_cabo(cable_id: int):
    """Delete cable. Requires Supabase connection."""
    if not supabase.is_enabled:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    return {"success": await supabase.delete_cabo(cable_id)}


@app.get("/admin/postes", tags=["Admin"])
async def list_postes():
    """List all poles (falls back to Excel if Supabase unavailable)."""
    if supabase.is_enabled:
        try:
            return await supabase.fetch_postes()
        except Exception:
            pass
    from translated.plan1_tables import POSTE_TABLE
    result = []
    for tipo, models in POSTE_TABLE.items():
        for row in models:
            label = row[0] if isinstance(row, (list, tuple)) else str(row)
            result.append({"tipo": tipo, "modelo": label})
    return result


@app.post("/admin/postes", tags=["Admin"])
async def create_poste(tipo: str, modelo: str, altura_m: float, carga_admissivel_dan: float):
    """Create new pole. Requires Supabase connection."""
    if not supabase.is_enabled:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    return await supabase.insert_poste(tipo, modelo, altura_m, carga_admissivel_dan)


@app.delete("/admin/postes/{poste_id}", tags=["Admin"])
async def delete_poste(poste_id: int):
    """Delete pole. Requires Supabase connection."""
    if not supabase.is_enabled:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    return {"success": await supabase.delete_poste(poste_id)}


@app.get("/admin/redes", tags=["Admin"])
async def list_redes():
    """List all network types (falls back to Excel if Supabase unavailable)."""
    if supabase.is_enabled:
        try:
            return await supabase.fetch_redes()
        except Exception:
            pass
    from translated.plan1_tables import REDE_TABLE
    return [{"tipo": row[0], "descricao": row[1] if len(row) > 1 else None} for row in REDE_TABLE]


@app.get("/admin/normas", tags=["Admin"])
async def list_normas(categoria: Optional[str] = None):
    """List all rules and standards."""
    if not supabase.is_enabled:
        return {"message": "Supabase not configured"}
    try:
        if categoria:
            return await supabase.fetch_normas_by_categoria(categoria)
        return await supabase.fetch_normas()
    except Exception:
        return {"message": "Supabase connection error"}


@app.get("/admin/normas/categorias", tags=["Admin"])
async def list_normas_categorias():
    """List all available norm categories."""
    if not supabase.is_enabled:
        return {"categorias": []}
    try:
        return await supabase.fetch_normas_categorias()
    except Exception:
        return {"categorias": []}
