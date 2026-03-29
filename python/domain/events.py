"""Domain events — immutable records of what happened in the domain.

Domain events represent significant facts about the domain. They are immutable
and form an audit trail. In Phase 3, these will be persisted to an event log.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4



@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events (immutable)."""

    event_id: UUID
    aggregate_id: UUID  # poste_id or projeto_id
    aggregate_type: str  # "Poste" or "Projeto"
    timestamp: datetime
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for storage."""
        return {
            "event_id": str(self.event_id),
            "aggregate_id": str(self.aggregate_id),
            "aggregate_type": self.aggregate_type,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "event_type": self.__class__.__name__,
        }


@dataclass(frozen=True)
class ProjetoCriado(DomainEvent):
    """Event: A Projeto was created."""

    nome: str = ""
    owner_id: str = ""
    endereco: str = ""
    orgao: str = ""
    ns: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "nome": self.nome,
            "owner_id": self.owner_id,
            "endereco": self.endereco,
            "orgao": self.orgao,
            "ns": self.ns,
        })
        return d


@dataclass(frozen=True)
class PosteCriado(DomainEvent):
    """Event: A Poste was created within a Projeto."""

    projeto_id: UUID = field(default_factory=uuid4)
    numero: str = ""
    tipo_poste: str = ""
    modelo_poste: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "projeto_id": str(self.projeto_id),
            "numero": self.numero,
            "tipo_poste": self.tipo_poste,
            "modelo_poste": self.modelo_poste,
        })
        return d


@dataclass(frozen=True)
class NivelAtualizado(DomainEvent):
    """Event: A Nivel's geometry was updated."""

    projeto_id: UUID = field(default_factory=uuid4)
    poste_id: UUID = field(default_factory=uuid4)
    nivel: str = ""
    altura_poste: float = 0.0
    altura_ancoragem: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "projeto_id": str(self.projeto_id),
            "poste_id": str(self.poste_id),
            "nivel": self.nivel,
            "altura_poste": self.altura_poste,
            "altura_ancoragem": self.altura_ancoragem,
        })
        return d


@dataclass(frozen=True)
class TravessiaAtualizada(DomainEvent):
    """Event: A Travessia (span) was updated."""

    projeto_id: UUID = field(default_factory=uuid4)
    poste_id: UUID = field(default_factory=uuid4)
    nivel: str = ""
    posicao: int = 0
    tipo_rede: str = ""
    tipo_cabo: str = ""
    vao: float = 0.0
    flecha: float = 0.0
    angulo: float = 0.0
    qtd_ligacoes: int = 0
    qtd_cabos: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "projeto_id": str(self.projeto_id),
            "poste_id": str(self.poste_id),
            "nivel": self.nivel,
            "posicao": self.posicao,
            "tipo_rede": self.tipo_rede,
            "tipo_cabo": self.tipo_cabo,
            "vao": self.vao,
            "flecha": self.flecha,
            "angulo": self.angulo,
            "qtd_ligacoes": self.qtd_ligacoes,
            "qtd_cabos": self.qtd_cabos,
        })
        return d


@dataclass(frozen=True)
class CalculoSnapshot(DomainEvent):
    """Event: A calculation was performed and recorded on a Poste."""

    projeto_id: UUID = field(default_factory=uuid4)
    poste_id: UUID = field(default_factory=uuid4)
    calculo_id: UUID = field(default_factory=uuid4)
    resultado_json: Dict[str, Any] = field(default_factory=dict)
    status: str = "draft"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "projeto_id": str(self.projeto_id),
            "poste_id": str(self.poste_id),
            "calculo_id": str(self.calculo_id),
            "resultado_json": self.resultado_json,
            "status": self.status,
        })
        return d


@dataclass(frozen=True)
class CalculoDeletado(DomainEvent):
    """Event: A calculation snapshot was deleted (soft-delete)."""

    projeto_id: UUID = field(default_factory=uuid4)
    poste_id: UUID = field(default_factory=uuid4)
    calculo_id: UUID = field(default_factory=uuid4)
    razao: str = "user requested"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "projeto_id": str(self.projeto_id),
            "poste_id": str(self.poste_id),
            "calculo_id": str(self.calculo_id),
            "razao": self.razao,
        })
        return d


@dataclass(frozen=True)
class PosteVinculado(DomainEvent):
    """Event: A Poste was linked to its ancestor in a previous project.

    Recorded when a Poste in Project Y is declared a continuation of a Poste
    in Project X.  The chain of these events provides the full cross-project
    lineage (audit trail) for any physical pole.
    """

    projeto_id: UUID = field(default_factory=uuid4)
    poste_id: UUID = field(default_factory=uuid4)
    origem_id: UUID = field(default_factory=uuid4)
    numero: str = ""
    origem_numero: str = ""
    origem_projeto_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "projeto_id": str(self.projeto_id),
            "poste_id": str(self.poste_id),
            "origem_id": str(self.origem_id),
            "numero": self.numero,
            "origem_numero": self.origem_numero,
            "origem_projeto_id": str(self.origem_projeto_id) if self.origem_projeto_id else None,
        })
        return d

@dataclass(frozen=True)
class PosteDeletado(DomainEvent):
    """Event: A Poste was deleted (soft-delete)."""

    projeto_id: UUID = field(default_factory=uuid4)
    poste_id: UUID = field(default_factory=uuid4)
    numero: str = ""
    razao: str = "user requested"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "projeto_id": str(self.projeto_id),
            "poste_id": str(self.poste_id),
            "numero": self.numero,
            "razao": self.razao,
        })
        return d


@dataclass(frozen=True)
class ProjetoDeletado(DomainEvent):
    """Event: A Projeto was deleted (soft-delete)."""

    projeto_id: UUID = field(default_factory=uuid4)
    nome: str = ""
    razao: str = "user requested"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "projeto_id": str(self.projeto_id),
            "nome": self.nome,
            "razao": self.razao,
        })
        return d
