"""Pydantic v2 request/response schemas for the /calcular endpoint.

These models mirror the React frontend state shape so that the UI can
POST its current state directly and receive a typed result.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ── Input models ──────────────────────────────────────────────────────────

class MTTraversalIn(BaseModel):
    tipo_rede: str = ""
    tipo_cabo: str = ""
    vao: float = 0.0
    flecha: float = 0.0
    angulo: float = 0.0
    altura_poste: float = 0.0
    altura_ancoragem: float = 0.0


class BTTraversalIn(BaseModel):
    """BT traversal input.

    For T1/T2 the vao/flecha/angulo/altura_poste are ignored by the
    calculator (overridden by MT1 T1/T2 geometry per C66=C14 etc.).
    They are still accepted here for round-trip fidelity with the UI.
    """
    tipo_rede: str = ""
    tipo_cabo: str = ""
    vao: float = 0.0
    flecha: float = 0.0
    angulo: float = 0.0
    altura_poste: float = 0.0
    altura_ancoragem: float = 0.0


class BTZeroTraversalIn(BaseModel):
    qtd_ligacoes: float = 0.0
    vao: float = 0.0
    flecha: float = 0.0
    angulo: float = 0.0
    altura_poste: float = 0.0
    altura_ancoragem: float = 0.0


class RamaisTraversalIn(BaseModel):
    tipo_cabo: str = ""
    qtd_cabos: float = 0.0
    vao: float = 0.0
    flecha: float = 0.0
    angulo: float = 0.0
    altura_poste: float = 0.0
    altura_ancoragem: float = 0.0


class CabecalhoIn(BaseModel):
    orgao: str = ""
    ns: str = ""
    projeto: str = ""
    ponto: str = ""
    endereco: str = ""
    estudado_por: str = ""
    matricula: str = ""
    data: str = ""


class PosteIn(BaseModel):
    tipo_poste: str = ""
    modelo_poste: str = ""
    # carga_nominal is informational; eccentricity comes from tipo+modelo lookup
    carga_nominal: float = 0.0


class CalculoInput(BaseModel):
    cabecalho: CabecalhoIn = Field(default_factory=CabecalhoIn)
    poste: PosteIn = Field(default_factory=PosteIn)
    mt1: list[MTTraversalIn] = Field(default_factory=lambda: [MTTraversalIn() for _ in range(4)])
    mt2: list[MTTraversalIn] = Field(default_factory=lambda: [MTTraversalIn() for _ in range(4)])
    bt:  list[BTTraversalIn] = Field(default_factory=lambda: [BTTraversalIn()  for _ in range(4)])
    btz: list[BTZeroTraversalIn] = Field(default_factory=lambda: [BTZeroTraversalIn() for _ in range(4)])
    ral: list[RamaisTraversalIn] = Field(default_factory=lambda: [RamaisTraversalIn() for _ in range(4)])


# ── Output models ─────────────────────────────────────────────────────────

class LevelResultOut(BaseModel):
    tracao_dan: float = 0.0       # normalised tip force (daN)
    angulo_graus: float = 0.0     # direction (degrees)
    resultante_raw: float = 0.0   # before normalisation (for debug)
    texto: str = ""


class VetorOut(BaseModel):
    label: str
    tracao_dan: float
    angulo_graus: float
    comp_x: float
    comp_y: float


class CalculoOutput(BaseModel):
    mt1: LevelResultOut = Field(default_factory=LevelResultOut)
    mt2: LevelResultOut = Field(default_factory=LevelResultOut)
    bt:  LevelResultOut = Field(default_factory=LevelResultOut)
    btz: LevelResultOut = Field(default_factory=LevelResultOut)
    ral: LevelResultOut = Field(default_factory=LevelResultOut)
    total_tracao_dan: float = 0.0
    total_angulo_graus: float = 0.0
    texto_total: str = ""
    vetores: list[VetorOut] = Field(default_factory=list)
    poste_ecc_dan: float = 0.0


# ── QDT models ────────────────────────────────────────────────────────────

class QDTInput(BaseModel):
    v_nominal_mt: float = 13200.0
    v_nominal_bt: float = 220.0
    coef_perda: float = 75.0
    reg_mt: float = 1.02
    drop_mt_pct: float = 0.0
    drop_trafo_pct: float = 0.0
    drop_bt1_pct: float = 0.0
    drop_bt2_pct: float = 0.0


class QDTOutput(BaseModel):
    v_mt_initial: float
    v_mt_node: float
    v_bt_start: float
    v_bt_node1: float
    v_bt_node2: float
    drop_total_pct: float
