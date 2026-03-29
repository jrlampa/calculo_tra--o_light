"""Pydantic v2 request/response schemas for the /calcular endpoint.

These models mirror the React frontend state shape so that the UI can
POST its current state directly and receive a typed result.
"""

from __future__ import annotations

from typing import Literal, Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field, field_validator, model_validator


# ── Input models ──────────────────────────────────────────────────────────


class MTTraversalIn(BaseModel):
    tipo_rede: str = Field(
        default="", max_length=50, description="Tipo de rede (ex: Convencional, Compacta)"
    )
    tipo_cabo: str = Field(
        default="", max_length=150, description="Nome do cabo conforme tabela técnica"
    )
    vao: float = Field(default=0.0, ge=0, le=5000, description="Comprimento do vão em metros")
    flecha: float = Field(default=0.0, ge=0, le=5000, description="Flecha do cabo em metros")
    angulo: float = Field(
        default=0.0, ge=0, le=360, description="Ângulo de deflexão em graus (0-360)"
    )
    altura_poste: float = Field(
        default=0.0, ge=0, le=100, description="Altura total do poste em metros"
    )
    altura_ancoragem: float = Field(
        default=0.0, ge=0, le=100, description="Altura do ponto de fixação em metros"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "tipo_rede": "Convencional",
                "tipo_cabo": "397MCM-CA, Nu",
                "vao": 33.0,
                "flecha": 0.5,
                "angulo": 0.0,
                "altura_poste": 11.0,
                "altura_ancoragem": 9.2,
            }
        }
    }

    @model_validator(mode="after")
    def validate_vao_flecha_consistency(self) -> MTTraversalIn:
        if self.vao > 0 and self.flecha <= 0:
            raise ValueError("flecha must be > 0 when vao > 0")
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

    @model_validator(mode="after")
    def validate_vao_flecha_consistency(self) -> BTTraversalIn:
        if self.vao > 0 and self.flecha <= 0:
            raise ValueError("flecha must be > 0 when vao > 0")
        return self


class BTZeroTraversalIn(BaseModel):
    qtd_ligacoes: float = Field(default=0.0, ge=0, le=1000)
    vao: float = Field(default=0.0, ge=0, le=5000)
    flecha: float = Field(default=0.0, ge=0, le=5000)
    angulo: float = Field(default=0.0, ge=0, le=360)
    altura_poste: float = Field(default=0.0, ge=0, le=100)
    altura_ancoragem: float = Field(default=0.0, ge=0, le=100)


class RamaisTraversalIn(BaseModel):
    tipo_cabo: str = Field(default="", max_length=150)
    qtd_cabos: float = Field(default=0.0, ge=0, le=1000)
    vao: float = Field(default=0.0, ge=0, le=5000)
    flecha: float = Field(default=0.0, ge=0, le=5000)
    angulo: float = Field(default=0.0, ge=0, le=360)
    altura_poste: float = Field(default=0.0, ge=0, le=100)
    altura_ancoragem: float = Field(default=0.0, ge=0, le=100)


class CabecalhoIn(BaseModel):
    orgao: str = Field(default="", max_length=100)
    ns: str = Field(default="", max_length=50)
    projeto: str = Field(default="", max_length=200)
    numero: str = Field(
        default="", max_length=20, description="Poste number/ID"
    )  # Renamed from 'ponto'
    endereco: str = Field(default="", max_length=300)
    estudado_por: str = Field(default="", max_length=100)
    matricula: str = Field(default="", max_length=50)
    data: str = Field(default="", max_length=20)


class PosteCalculoIn(BaseModel):
    tipo_poste: str = Field(default="", max_length=100)
    modelo_poste: str = Field(default="", max_length=100)
    # carga_nominal removed per Phase 9 parity requirements


class CalculoInput(BaseModel):
    cabecalho: CabecalhoIn = Field(default_factory=CabecalhoIn)
    poste: PosteCalculoIn = Field(default_factory=PosteCalculoIn)
    mt1: list[MTTraversalIn] = Field(
        default_factory=lambda: [MTTraversalIn() for _ in range(4)], min_length=4, max_length=4
    )
    mt2: list[MTTraversalIn] = Field(
        default_factory=lambda: [MTTraversalIn() for _ in range(4)], min_length=4, max_length=4
    )
    bt: list[BTTraversalIn] = Field(
        default_factory=lambda: [BTTraversalIn() for _ in range(4)], min_length=4, max_length=4
    )
    btz: list[BTZeroTraversalIn] = Field(
        default_factory=lambda: [BTZeroTraversalIn() for _ in range(4)], min_length=4, max_length=4
    )
    ral: list[RamaisTraversalIn] = Field(
        default_factory=lambda: [RamaisTraversalIn() for _ in range(4)], min_length=4, max_length=4
    )


# ── Output models ─────────────────────────────────────────────────────────


class LevelResultOut(BaseModel):
    tracao_dan: float = 0.0  # normalised tip force (daN)
    angulo_graus: float = 0.0  # direction (degrees)
    resultante_raw: float = 0.0  # before normalisation (for debug)
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
    bt: LevelResultOut = Field(default_factory=LevelResultOut)
    btz: LevelResultOut = Field(default_factory=LevelResultOut)
    ral: LevelResultOut = Field(default_factory=LevelResultOut)
    total_tracao_dan: float = 0.0
    total_angulo_graus: float = 0.0
    texto_total: str = ""
    vetores: list[VetorOut] = Field(default_factory=list)
    poste_ecc_dan: float = 0.0
    # Phase 11: 5% tolerance rule
    status_poste: str = "OK"  # OK, SOBRECARGA
    resistencia_nominal: float = 0.0

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_tracao_dan": 450.5,
                "total_angulo_graus": 12.3,
                "texto_total": "Resultado Final: 450 daN",
                "poste_ecc_dan": 120.0,
            }
        }
    }


# ── QDT models ────────────────────────────────────────────────────────────


class QDTInput(BaseModel):
    v_nominal_mt: float = Field(default=13200.0, description="Tensão nominal MT em Volts")
    v_nominal_bt: float = Field(default=220.0, description="Tensão nominal BT em Volts")
    coef_perda: float = Field(default=75.0, description="Coeficiente de perda")
    reg_mt: float = Field(default=1.02, description="Regulação da MT")
    drop_mt_pct: float = Field(default=0.0, ge=0, le=100, description="Queda MT (%)")
    drop_trafo_pct: float = Field(default=0.0, ge=0, le=100, description="Queda Trafo (%)")
    drop_bt1_pct: float = Field(default=0.0, ge=0, le=100, description="Queda Trecho 1 (%)")
    drop_bt2_pct: float = Field(default=0.0, ge=0, le=100, description="Queda Trecho 2 (%)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "v_nominal_mt": 13800.0,
                "v_nominal_bt": 220.0,
                "drop_mt_pct": 0.5,
                "drop_trafo_pct": 1.2,
            }
        }
    }


class QDTOutput(BaseModel):
    v_mt_initial: float
    v_mt_node: float
    v_bt_start: float
    v_bt_node1: float
    v_bt_node2: float
    drop_total_pct: float


# ── Admin create models ───────────────────────────────────────────────────


class CaboIn(BaseModel):
    """Request body for POST /admin/cabos."""

    nome: str = Field(..., min_length=1, max_length=200)
    diametro: float = Field(..., gt=0, description="Diâmetro do cabo em mm")
    peso: float = Field(..., gt=0, description="Peso do cabo em kg/m")


class AdminPosteIn(BaseModel):
    """Request body for POST /admin/postes."""

    tipo: str = Field(..., min_length=1, max_length=100)
    modelo: str = Field(..., min_length=1, max_length=200)
    altura_m: float = Field(..., gt=0, description="Altura do poste em metros")
    carga_admissivel_dan: float = Field(
        ..., gt=0, description="Carga admissível em daN"
    )


# ── Projeto / Ponto transactional models ─────────────────────────────────


class ProjetoIn(BaseModel):
    orgao: str = Field(default="", max_length=100)
    ns: str = Field(default="", max_length=50)
    nome: str = Field(min_length=1, max_length=200)  # campo "Projeto" na UI (obrigatório)
    endereco: str = ""
    estudado_por: str = ""
    matricula: str = ""
    data_estudo: str = ""  # dd/mm/yyyy

    model_config = {
        "extra": "forbid",  # Não permitir campos extras
        "json_schema_extra": {
            "example": {
                "orgao": "IM3 Brasil",
                "ns": "123456",
                "nome": "Expansão Rede Centro",
                "endereco": "Av. Brasil, 1000",
                "estudado_por": "Eng. Silva",
                "matricula": "M123",
                "data_estudo": "22/03/2026",
            }
        },
    }


class ProjetoUpdate(BaseModel):
    orgao: Optional[str] = None
    ns: Optional[str] = None
    nome: Optional[str] = None
    endereco: Optional[str] = None
    estudado_por: Optional[str] = None
    matricula: Optional[str] = None
    data_estudo: Optional[str] = None


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


class PosteIn(BaseModel):
    """Input schema for creating/updating a Poste (agregado raiz).

    Note: 'numero' replaces 'ponto' to align with domain aggregate naming.
    This is the Poste aggregate identifier within a project.
    """

    numero: str = Field(
        min_length=1,
        max_length=10,
        pattern=r"^[A-Za-z0-9]+$",
        description="Poste number (e.g. '01', '1A')",
        validation_alias=AliasChoices("numero", "ponto"),
    )
    tipo_poste: str = Field(default="", max_length=100, description="Type (e.g. 'Concreto', 'Aço')")
    modelo_poste: str = Field(
        default="", max_length=100, description="Model (e.g. '11/600', '13/800')"
    )

    model_config = {
        "json_schema_extra": {
            "example": {"numero": "12A", "tipo_poste": "Concreto", "modelo_poste": "11/600"}
        }
    }


class PosteOut(BaseModel):
    """Output schema for Poste responses."""

    id: str
    projeto_id: str
    numero: str
    tipo_poste: str
    modelo_poste: str
    origem_id: Optional[str] = None


class PosteVincularIn(BaseModel):
    """Request body for PUT /postes/{id}/vincular-origem.

    Links a Poste in the current project to its physical predecessor in a
    previous project (cross-project lineage).
    """

    origem_id: str = Field(
        min_length=36,
        max_length=36,
        description="UUID do Poste ancestral (de um projeto anterior) que este Poste continua.",
    )


class ClonarPosteIn(BaseModel):
    """Request body for POST /postes/{id}/clonar-para-projeto.

    Clones a Poste from one project into another.  The clone gets a new UUID,
    inherits all Niveis/Travessias configuration from the source, and has
    ``origem_id`` pre-set so the lineage is established automatically.

    Use this when Project Y starts from a physical pole already studied in
    Project X.  The clone can then be modified freely in Project Y without
    affecting Project X data.
    """

    projeto_id: str = Field(
        min_length=36,
        max_length=36,
        description="UUID do Projeto de destino onde o Poste clonado será criado.",
    )


class LinhagemEntry(BaseModel):
    """A single node in the cross-project lineage chain."""

    id: str
    numero: str
    tipo_poste: str
    modelo_poste: str
    projeto_id: str
    origem_id: Optional[str] = None
    atualizado_em: Optional[str] = None
    calculos_count: int = 0


class PosteLinhagem(BaseModel):
    """Response for GET /postes/{id}/linhagem.

    The chain is ordered oldest → newest (index 0 is the root ancestor,
    last entry is the requested Poste).  Use ``atualizado_em`` to determine
    which project's data is most recent (latest-timestamp-wins).
    """

    poste_id: str
    chain: list[LinhagemEntry]
    profundidade: int = Field(description="Length of the lineage chain")


class TravessiaUpdateIn(BaseModel):
    """Request body for PUT /postes/{id}/niveis/{nivel}/travessias/{posicao}."""

    tipo_rede: str = Field(default="circuito", max_length=50, description="Network type")
    tipo_cabo: str = Field(default="CAA", max_length=50, description="Cable type")
    vao: float = Field(default=0.0, ge=0.0, description="Span length in meters")
    flecha: float = Field(default=0.0, ge=0.0, description="Sag in meters")
    angulo: float = Field(default=0.0, ge=0.0, lt=360.0, description="Deflection angle in degrees")


class CondutorOut(BaseModel):
    """One conductor (cable) entry from a Poste traversal, returned by GET /condutores."""

    nivel: str = Field(description="Voltage level (MT1, MT2, BT, BTZ, RAL)")
    posicao: int = Field(ge=1, le=4, description="Position within the level (1–4)")
    tipo_rede: str = Field(description="Network type")
    tipo_cabo: str = Field(description="Cable/conductor type")
    vao: float = Field(description="Span length in meters")
    flecha: float = Field(description="Sag in meters")
    angulo: float = Field(description="Deflection angle in degrees")


class PontoIn(BaseModel):
    """Legacy schema kept for the existing /pontos contract."""

    ponto: str = Field(
        min_length=1,
        max_length=10,
        pattern=r"^[A-Za-z0-9]+$",
        validation_alias=AliasChoices("ponto", "numero"),
    )
    tipo_poste: str = Field(default="", max_length=100)
    modelo_poste: str = Field(default="", max_length=100)

    @property
    def numero(self) -> str:
        return self.ponto


class PontoOut(BaseModel):
    """Legacy output schema kept for the existing /pontos contract."""

    id: str
    projeto_id: str
    ponto: str
    tipo_poste: str
    modelo_poste: str

    @property
    def numero(self) -> str:
        return self.ponto


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
    def validate_travessias_positions(
        cls, travessias: list[TravessiaSalvarIn]
    ) -> list[TravessiaSalvarIn]:
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

    ponto_id: UUID = Field(description="ID único do ponto (UUID)")
    niveis: list[NivelSalvarIn] = Field(
        min_length=5, max_length=5, description="Lista de 5 níveis (MT1, MT2, BT, BTZ, RAL)"
    )
    resultado: ResultadoSalvarIn = Field(description="Resultado sumarizado do cálculo")

    model_config = {
        "json_schema_extra": {
            "example": {
                "ponto_id": "550e8400-e29b-41d4-a716-446655440000",
                "niveis": [],
                "resultado": {"total_tracao": 450.0, "total_angulo": 15.5},
            }
        }
    }

    @model_validator(mode="after")
    def validate_niveis_set(self) -> SalvarCalculoIn:
        expected_levels = {"MT1", "MT2", "BT", "BTZ", "RAL"}
        informed_levels = [nivel.nivel for nivel in self.niveis]
        if set(informed_levels) != expected_levels or len(informed_levels) != len(
            set(informed_levels)
        ):
            raise ValueError("niveis must contain MT1, MT2, BT, BTZ and RAL without duplication")
        return self


class BatchSalvarCalculoIn(BaseModel):
    """Payload atômico para persistir tudo (Projeto, Ponto e Cálculo)."""

    projeto_id: Optional[UUID] = None
    projeto_dados: Optional[ProjetoIn] = None
    ponto_dados: PontoIn
    niveis: list[NivelSalvarIn] = Field(min_length=5, max_length=5)
    resultado: ResultadoSalvarIn

    @model_validator(mode="after")
    def validate_project_info(self) -> BatchSalvarCalculoIn:
        if not self.projeto_id and not self.projeto_dados:
            raise ValueError("projeto_id or projeto_dados must be provided")
        return self
