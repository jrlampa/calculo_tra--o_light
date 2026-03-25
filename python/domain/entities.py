"""Domain entities — mutable objects with identity, owned by aggregate root.

Entities live within an aggregate boundary and are manipulated through the aggregate root.
They have identity only within the aggregate context (not globally unique).
Examples: Nivel (voltage level within a Poste), Travessia (span within a Nivel).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from domain.value_objects import Condutor, Geometria, NivelEnum


@dataclass
class Travessia:
    """A single span between two poles at a given level."""

    posicao: int  # Position 1-4 (always 4 per Nivel)
    condutor: Condutor
    geometria: Geometria

    def validar(self) -> None:
        """Check invariants for this Travessia."""
        if not 1 <= self.posicao <= 4:
            raise ValueError(f"Posição deve estar entre 1-4, recebeu {self.posicao}")

    def __post_init__(self) -> None:
        """Validate on construction."""
        self.validar()


@dataclass
class Nivel:
    """A voltage level within a Poste (MT1, MT2, BT, BTZ, RAL)."""

    nivel_enum: NivelEnum
    altura_poste: float  # Height of pole at this level (meters)
    altura_ancoragem: float  # Anchor point height (meters)
    travessias: List[Travessia] = field(default_factory=list)

    def validar(self) -> None:
        """Check invariants for this Nivel."""
        if self.altura_poste <= 0:
            raise ValueError(f"Altura do poste deve ser > 0, recebeu {self.altura_poste}")
        if self.altura_ancoragem < 0:
            raise ValueError(f"Altura de ancoragem deve ser >= 0, recebeu {self.altura_ancoragem}")
        if self.altura_ancoragem > self.altura_poste:
            raise ValueError(
                f"Altura de ancoragem ({self.altura_ancoragem}m) não pode ser maior "
                f"que altura do poste ({self.altura_poste}m)"
            )
        if len(self.travessias) != 4:
            raise ValueError(
                f"Um Nivel deve ter exatamente 4 Travessias, recebeu {len(self.travessias)}"
            )

    def __post_init__(self) -> None:
        """Validate on construction."""
        self.validar()

    def obter_travessia(self, posicao: int) -> Travessia:
        """Get travessia at position (1-4)."""
        for t in self.travessias:
            if t.posicao == posicao:
                return t
        raise ValueError(f"Travessia na posição {posicao} não encontrada")

    def atualizar_travessia(self, posicao: int, condutor: Condutor, geometria: Geometria) -> None:
        """Update travessia at position."""
        for i, t in enumerate(self.travessias):
            if t.posicao == posicao:
                self.travessias[i] = Travessia(posicao=posicao, condutor=condutor, geometria=geometria)
                self.validar()
                return
        raise ValueError(f"Travessia na posição {posicao} não encontrada")
