"""Pydantic v2 request/response schemas for the /calcular endpoint.

These models mirror the React frontend state shape so that the UI can
POST its current state directly and receive a typed result.
"""
from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Input models ──────────────────────────────────────────────────────────

class MTTraversalIn(BaseModel):
    tipo_rede: str = Field(default="", max_length=50)
    tipo_cabo: str = Field(default="", max_length=150)
    vao: float = Field(default=0.0, ge=0, le=5000)
    flecha: float = Field(default=0.0, ge=0, le=5000)
    angulo: float = Field(default=0.0, ge=0, le=360)
    altura_poste: float = Field(default=0.0, ge=0, le=100)
    altura_ancoragem: float = Field(default=0.0, ge=0, le=100)

    @model_validator(mode='after')
    def flecha_required_when_vao(self) -> 'MTTraversalIn':
        if self.vao > 0 and self.flecha <= 0:
            raise ValueError("flecha deve ser > 0 quando vao > 0")
        return self


class BTTraversalIn(BaseModel):
    """BT traversal input.

    For T1/T2 the vao/flecha/angulo/altura_poste are ignored by the
    calculator (overridden by MT1 T1/T2 geometry per C66=C14 etc.).
    They are still accepted here for round-trip fidelity with the UI.
    """
    tipo_rede: str = Field(default="", max_length=50)
    tipo_cabo: str = Field(default="", max_length=150)
    vao: float = Field(default=0.0, ge=0, le=5000)
    flecha: float = Field(default=0.0, ge=0, le=5000)
    angulo: float = Field(default=0.0, ge=0, le=360)
    altura_poste: float = Field(default=0.0, ge=0, le=100)
    altura_ancoragem: float = Field(default=0.0, ge=0, le=100)

    @model_validator(mode='after')
    def flecha_required_when_vao(self) -> 'BTTraversalIn':
        if self.vao > 0 and self.flecha <= 0:
            raise ValueError("flecha deve ser > 0 quando vao > 0")
        return self


class BTZeroTraversalIn(BaseModel):
    qtd_ligacoes: float = Field(default=0.0, ge=0, le=1000)
    vao: float = Field(default=0.0, ge=0, le=5000)
    flecha: float = Field(default=0.0, ge=0, le=5000)
    angulo: float = Field(default=0.0, ge=0, le=360)
    altura_poste: float = Field(default=0.0, ge=0, le=100)
    altura_ancoragem: float = Field(default=0.0, ge=0, le=100)

    @model_validator(mode='after')
    def flecha_required_when_vao(self) -> 'BTZeroTraversalIn':
        if self.vao > 0 and self.flecha <= 0:
            raise ValueError("flecha deve ser > 0 quando vao > 0")
        return self


class RamaisTraversalIn(BaseModel):
    tipo_cabo: str = Field(default="", max_length=150)
    qtd_cabos: float = Field(default=0.0, ge=0, le=1000)
    vao: float = Field(default=0.0, ge=0, le=5000)
    flecha: float = Field(default=0.0, ge=0, le=5000)
    angulo: float = Field(default=0.0, ge=0, le=360)
    altura_poste: float = Field(default=0.0, ge=0, le=100)
    altura_ancoragem: float = Field(default=0.0, ge=0, le=100)

    @model_validator(mode='after')
    def flecha_required_when_vao(self) -> 'RamaisTraversalIn':
        if self.vao > 0 and self.flecha <= 0:
            raise ValueError("flecha deve ser > 0 quando vao > 0")
        return self


class CabecalhoIn(BaseModel):
    orgao: str = Field(default="", max_length=100)
    ns: str = Field(default="", max_length=50)
    projeto: str = Field(default="", max_length=200)
    ponto: str = Field(default="", max_length=20)
    endereco: str = Field(default="", max_length=300)
    estudado_por: str = Field(default="", max_length=100)
    matricula: str = Field(default="", max_length=50)
    data: str = Field(default="", max_length=20)


class PosteIn(BaseModel):
    tipo_poste: str = Field(default="", max_length=100)
    modelo_poste: str = Field(default="", max_length=100)
    # carga_nominal removed per Phase 9 parity requirements


class CalculoInput(BaseModel):
    cabecalho: CabecalhoIn = Field(default_factory=CabecalhoIn)
    poste: PosteIn = Field(default_factory=PosteIn)
    mt1: list[MTTraversalIn] = Field(default_factory=lambda: [MTTraversalIn() for _ in range(4)], min_length=4, max_length=4)
    mt2: list[MTTraversalIn] = Field(default_factory=lambda: [MTTraversalIn() for _ in range(4)], min_length=4, max_length=4)
    bt:  list[BTTraversalIn] = Field(default_factory=lambda: [BTTraversalIn() for _ in range(4)], min_length=4, max_length=4)
    btz: list[BTZeroTraversalIn] = Field(default_factory=lambda: [BTZeroTraversalIn() for _ in range(4)], min_length=4, max_length=4)
    ral: list[RamaisTraversalIn] = Field(default_factory=lambda: [RamaisTraversalIn() for _ in range(4)], min_length=4, max_length=4)


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


# ── Projeto / Ponto transactional models ─────────────────────────────────

class ProjetoIn(BaseModel):
    orgao: str = ""
    ns: str = ""
    nome: str = Field(min_length=1, max_length=200)  # campo "Projeto" na UI (obrigatório)
    endereco: str = ""
    estudado_por: str = ""
    matricula: str = ""
    data_estudo: str = ""       # dd/mm/yyyy


class ProjetoOut(BaseModel):
    id: str
    orgao: str
    ns: str
    nome: str
    endereco: str
    estudado_por: str
    matricula: str
    data_estudo: str
    total_pontos: int = 0


class PontoIn(BaseModel):
    ponto: str = Field(min_length=1, max_length=10, pattern=r"^[A-Za-z0-9]+$")  # ex: "01", "1A"
    tipo_poste: str = Field(default="", max_length=100)
    modelo_poste: str = Field(default="", max_length=100)


class PontoOut(BaseModel):
    id: str
    projeto_id: str
    ponto: str
    tipo_poste: str
    modelo_poste: str


NivelTipo = Literal["MT1", "MT2", "BT", "BTZ", "RAL"]


class TravessiaSalvarIn(BaseModel):
    posicao: int = Field(ge=1, le=4)
    tipo_rede: str = Field(default="", max_length=50)
    tipo_cabo: str = Field(default="", max_length=150)
    vao: float = Field(default=0.0, ge=0, le=5000)
    flecha: float = Field(default=0.0, ge=0, le=5000)
    angulo: float = Field(default=0.0, ge=0, le=360)
    qtd_ligacoes: float = Field(default=0.0, ge=0, le=1000)
    qtd_cabos: float = Field(default=0.0, ge=0, le=1000)


class NivelSalvarIn(BaseModel):
    nivel: NivelTipo
    altura_poste: float = Field(default=0.0, ge=0, le=100)
    altura_ancoragem: float = Field(default=0.0, ge=0, le=100)
    travessias: list[TravessiaSalvarIn] = Field(default_factory=list, min_length=4, max_length=4)

    @field_validator("travessias")
    @classmethod
    def validate_travessias_positions(cls, travessias: list[TravessiaSalvarIn]) -> list[TravessiaSalvarIn]:
        expected_positions = {1, 2, 3, 4}
        informed_positions = {travessia.posicao for travessia in travessias}
        if informed_positions != expected_positions:
            raise ValueError("travessias must include positions 1..4 exactly once")
        return travessias


class ResultadoSalvarIn(BaseModel):
    mt1_tracao: float = Field(default=0.0, ge=0, le=50000)
    mt1_angulo: float = Field(default=0.0, ge=0, le=360)
    mt2_tracao: float = Field(default=0.0, ge=0, le=50000)
    mt2_angulo: float = Field(default=0.0, ge=0, le=360)
    bt_tracao: float = Field(default=0.0, ge=0, le=50000)
    bt_angulo: float = Field(default=0.0, ge=0, le=360)
    btz_tracao: float = Field(default=0.0, ge=0, le=50000)
    btz_angulo: float = Field(default=0.0, ge=0, le=360)
    ral_tracao: float = Field(default=0.0, ge=0, le=50000)
    ral_angulo: float = Field(default=0.0, ge=0, le=360)
    total_tracao: float = Field(default=0.0, ge=0, le=50000)
    total_angulo: float = Field(default=0.0, ge=0, le=360)
    poste_ecc: float = Field(default=0.0, ge=0, le=50000)
    texto_mt1: str = Field(default="", max_length=200)
    texto_mt2: str = Field(default="", max_length=200)
    texto_bt: str = Field(default="", max_length=200)
    texto_btz: str = Field(default="", max_length=200)
    texto_ral: str = Field(default="", max_length=200)
    texto_total: str = Field(default="", max_length=200)


class SalvarCalculoIn(BaseModel):
    """Payload para persistir travessias + resultado em uma só chamada."""
    ponto_id: UUID
    niveis: list[NivelSalvarIn] = Field(min_length=5, max_length=5)
    resultado: ResultadoSalvarIn

    @model_validator(mode="after")
    def validate_niveis_set(self) -> SalvarCalculoIn:
        expected_levels = {"MT1", "MT2", "BT", "BTZ", "RAL"}
        informed_levels = [nivel.nivel for nivel in self.niveis]
        if set(informed_levels) != expected_levels or len(informed_levels) != len(set(informed_levels)):
            raise ValueError("niveis must contain MT1, MT2, BT, BTZ and RAL without duplication")
        return self
