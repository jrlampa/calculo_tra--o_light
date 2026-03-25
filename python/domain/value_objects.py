"""Domain value objects — immutable, no behavior, no dependencies.

Value objects represent concepts that are identified by their content, not identity.
Examples: Condutor (what a cable is), Geometria (the geometry of a span),
CalculoResultado (the output of a calculation).
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field


class PosteId(BaseModel):
    """Unique identifier for a Poste (aggregate root)."""
    value: UUID = Field(default_factory=lambda: __import__('uuid').uuid4())

    model_config = {"frozen": True}

    def __str__(self) -> str:
        return str(self.value)

    def __hash__(self) -> int:
        return hash(self.value)


class ProjetoId(BaseModel):
    """Unique identifier for a Projeto (aggregate parent)."""
    value: UUID = Field(default_factory=lambda: __import__('uuid').uuid4())

    model_config = {"frozen": True}

    def __str__(self) -> str:
        return str(self.value)

    def __hash__(self) -> int:
        return hash(self.value)


class NivelEnum(str, Enum):
    """Voltage level hierarchy in distribution network."""
    MT1 = "MT1"      # Média Tensão 1 (high voltage)
    MT2 = "MT2"      # Média Tensão 2
    BT = "BT"        # Baixa Tensão (low voltage)
    BTZ = "BTZ"      # Baixa Tensão com Zona de segurança
    RAL = "RAL"      # Aterramentos e Linhas adicionais

    def ordem(self) -> int:
        """Return vertical order (top to bottom on pole)."""
        return {"MT1": 1, "MT2": 2, "BT": 3, "BTZ": 4, "RAL": 5}[self.value]


class TipoPoste(str, Enum):
    """Type of pole/post."""
    CONCRETO = "concreto"      # Concrete
    ACO = "aço"                # Steel
    MADEIRA = "madeira"        # Wood
    DT = "DT"                  # Distribution Transformer pole
    COMPOSTO = "composto"      # Composite


class CaboConductor(str, Enum):
    """Cable/Conductor type."""
    CAA = "CAA"                # Aluminium Alloy (AAC)
    AACSR = "AACSR"            # Aluminium Conductor Steel Reinforced
    CU = "CU"                  # Copper
    AL = "AL"                  # Aluminium
    NEUTRO = "neutro"          # Neutral
    TERRA = "terra"            # Ground/Earth


class TipoRede(str, Enum):
    """Network/Circuit type."""
    CIRCUITO = "circuito"      # Circuit
    RAMIFICACAO = "ramificacao" # Branch/Tap
    INTERLIGACAO = "interligacao" # Interconnection


def parse_cabo_conductor(value: str | None) -> CaboConductor:
    """Parse workbook/UI cable labels into the supported conductor enum."""
    normalized = (value or "").strip().upper()
    if not normalized or normalized == "CAA" or "-CA" in normalized:
        return CaboConductor.CAA
    if "AACSR" in normalized:
        return CaboConductor.AACSR
    if "NEUTRO" in normalized:
        return CaboConductor.NEUTRO
    if "TERRA" in normalized:
        return CaboConductor.TERRA
    if normalized == "CU" or normalized.startswith("CU "):
        return CaboConductor.CU
    if normalized == "AL" or normalized.startswith("AL "):
        return CaboConductor.AL
    return CaboConductor.CAA


def parse_tipo_rede(value: str | None) -> TipoRede:
    """Parse workbook/UI network labels into the supported domain enum."""
    normalized = (value or "").strip().upper()
    if not normalized:
        return TipoRede.CIRCUITO
    if "RAMIF" in normalized:
        return TipoRede.RAMIFICACAO
    if "INTER" in normalized:
        return TipoRede.INTERLIGACAO
    return TipoRede.CIRCUITO


class Condutor(BaseModel):
    """Immutable representation of a conductor (cable) on a travessia (span)."""
    tipo_rede: TipoRede
    tipo_cabo: CaboConductor = Field(validation_alias=AliasChoices("tipo_cabo", "tipo"))
    qtd_ligacoes: int = Field(default=0, ge=0, description="Number of connections")
    qtd_cabos: int = Field(default=1, ge=1, description="Number of cable strands")

    model_config = {"frozen": True, "populate_by_name": True}

    @property
    def tipo(self) -> CaboConductor:
        return self.tipo_cabo

    def descricao(self) -> str:
        """Human-readable description."""
        return (
            f"{self.tipo_rede.value} | {self.tipo_cabo.value} "
            f"({self.qtd_cabos}x, {self.qtd_ligacoes} conexões)"
        )


class Geometria(BaseModel):
    """Immutable geometric properties of a span (travessia)."""
    vao: float = Field(ge=0, description="Span distance in meters")
    flecha: float = Field(ge=0, description="Sag/deflection in meters")
    angulo: float = Field(ge=0, le=360, description="Angle in degrees")

    model_config = {"frozen": True}

    def __str__(self) -> str:
        return f"Vão={self.vao}m, Flecha={self.flecha}m, Ângulo={self.angulo}°"


class CalculoResultado(BaseModel):
    """Immutable calculation result (output of tensioning/force calculation)."""
    # Traccion per level (force in daN — decanewtons)
    mt1_tracao: float = Field(default=0.0, ge=0)
    mt2_tracao: float = Field(default=0.0, ge=0)
    bt_tracao: float = Field(default=0.0, ge=0)
    btz_tracao: float = Field(default=0.0, ge=0)
    ral_tracao: float = Field(default=0.0, ge=0)

    # Angle per level (in degrees)
    mt1_angulo: float = Field(default=0.0, ge=0, le=360)
    mt2_angulo: float = Field(default=0.0, ge=0, le=360)
    bt_angulo: float = Field(default=0.0, ge=0, le=360)
    btz_angulo: float = Field(default=0.0, ge=0, le=360)
    ral_angulo: float = Field(default=0.0, ge=0, le=360)

    # Totals
    total_tracao: float = Field(default=0.0, ge=0, description="Total tension in daN")
    total_angulo: float = Field(default=0.0, ge=0, le=360, description="Total angle in degrees")

    # Pole eccentricity (descentramento do poste)
    poste_ecc: float = Field(default=0.0, ge=0, description="Pole eccentricity in percent")

    # Text outputs (for display)
    texto_mt1: str = ""
    texto_mt2: str = ""
    texto_bt: str = ""
    texto_btz: str = ""
    texto_ral: str = ""
    texto_total: str = ""

    model_config = {"frozen": True}

    def resumo(self) -> str:
        """Summary: total tension and angle."""
        return f"Total: {self.total_tracao} daN @ {self.total_angulo}°"


class Geometria_Poste(BaseModel):
    """Immutable geographic/physical coordinates of a Poste."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altura_solo: Optional[float] = Field(None, description="Height above ground in meters")

    model_config = {"frozen": True}

    def __bool__(self) -> bool:
        """Check if any coordinate is set."""
        return any(x is not None for x in [self.latitude, self.longitude, self.altura_solo])
