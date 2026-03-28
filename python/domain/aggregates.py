"""Domain aggregates — root entities that enforce invariants over child entities.

An aggregate is a cluster of domain objects (entities and value objects) that can be 
treated as a single unit. The root entity enforces consistency boundaries.

Poste = Root Aggregate (owns Niveis, Travessias, CalculoSnapshots)
Projeto = Parent Aggregate (owns references to Postes)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import List, Optional
from uuid import UUID, uuid4

from domain.entities import Nivel, Travessia
from domain.value_objects import (
    CalculoResultado,
    Condutor,
    Geometria,
    Geometria_Poste,
    NivelEnum,
    PosteId,
    ProjetoId,
    TipoPoste,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class CalculoSnapshot:
    """Immutable snapshot of a calculation result (append-only event).
    
    Represents a saved calculation at a point in time. Once created, never modified.
    Status can be: 'draft' (unsaved working copy) or 'saved' (persistent).
    """

    resultado: CalculoResultado
    id: UUID = field(default_factory=uuid4)
    calculado_em: datetime = field(default_factory=_utc_now)
    calculado_por: Optional[str] = None  # user_id
    status: str = "draft"  # 'draft' | 'saved'

    def __hash__(self) -> int:
        return hash(self.id)

    def marcar_como_salvo(self) -> CalculoSnapshot:
        """Return new snapshot with status='saved' (immutable)."""
        return CalculoSnapshot(
            id=self.id,
            resultado=self.resultado,
            calculado_em=self.calculado_em,
            calculado_por=self.calculado_por,
            status="saved",
        )

    def resumo(self) -> str:
        """Summary for display."""
        return f"[{self.status}] {self.resultado.resumo()} @ {self.calculado_em.isoformat()}"


@dataclass
class Poste:
    """Root aggregate for pole/post in electrical distribution network.
    
    A Poste is the fundamental unit of calculation. It owns:
    - Niveis (voltage levels): always 5 (MT1, MT2, BT, BTZ, RAL)
    - Travessias (spans) within each Nivel: always 4 per level
    - CalculoSnapshots (calculation history): append-only

    Cross-project lineage
    ---------------------
    A physical pole can appear in multiple Projects across time.  When
    Project Y starts from a pole that was already part of Project X, the
    new Poste is created with ``origem_id`` pointing to the ancestor.
    The chain of ``origem_id`` links forms the full audit history of that
    physical pole across all projects.
    """

    projeto_id: ProjetoId
    numero: str
    niveis: List[Nivel]
    id: PosteId = field(default_factory=PosteId)
    tipo_poste: TipoPoste = TipoPoste.CONCRETO
    modelo_poste: str = ""  # e.g., "11/600", "13/800"
    calculos: List[CalculoSnapshot] = field(default_factory=list)  # Append-only history
    geometria: Geometria_Poste = field(default_factory=Geometria_Poste)
    # Lineage: UUID of the Poste in a previous project this one continues.
    # None means this is a "root" pole — first time this physical pole is studied.
    origem_id: Optional[PosteId] = None
    criado_em: datetime = field(default_factory=_utc_now)
    atualizado_em: datetime = field(default_factory=_utc_now)
    deletado_em: Optional[datetime] = None  # Soft-delete

    def validar(self) -> None:
        """Enforce aggregate invariants."""
        # Poste must have exactly 5 niveis
        if len(self.niveis) != 5:
            raise ValueError(
                f"Poste deve ter exatamente 5 Niveis, tem {len(self.niveis)}"
            )

        # Each nivel must have exactly 4 travessias
        for nivel in self.niveis:
            if len(nivel.travessias) != 4:
                raise ValueError(
                    f"Nivel {nivel.nivel_enum} deve ter 4 Travessias, tem {len(nivel.travessias)}"
                )

        # Niveis must be in correct order
        niveis_enum = [n.nivel_enum for n in self.niveis]
        ordem_esperada = [NivelEnum.MT1, NivelEnum.MT2, NivelEnum.BT, NivelEnum.BTZ, NivelEnum.RAL]
        if niveis_enum != ordem_esperada:
            raise ValueError(f"Niveis fora de ordem. Esperado {ordem_esperada}, got {niveis_enum}")

        # Numero must be unique within Projeto (checked at repository level)
        if not self.numero or len(self.numero.strip()) == 0:
            raise ValueError("Poste numero não pode estar vazio")

    def __post_init__(self) -> None:
        """Validate on construction."""
        self.validar()

    def obter_nivel(self, nivel_enum: NivelEnum) -> Nivel:
        """Get a specific nivel by enum."""
        for n in self.niveis:
            if n.nivel_enum == nivel_enum:
                return n
        raise ValueError(f"Nivel {nivel_enum} não encontrado neste Poste")

    def atualizar_travessia(
        self,
        nivel_enum: NivelEnum,
        posicao: int,
        condutor: Condutor,
        geometria: Geometria,
    ) -> None:
        """Update a travessia within a nivel."""
        nivel = self.obter_nivel(nivel_enum)
        nivel.atualizar_travessia(posicao, condutor, geometria)
        self.atualizado_em = _utc_now()

    def registrar_calculo(
        self,
        resultado: CalculoResultado,
        calculado_por: Optional[str] = None,
        status: str = "draft",
    ) -> CalculoSnapshot:
        """Record a new calculation snapshot (append-only)."""
        # Validate calculation result
        if resultado is None:
            raise ValueError("Resultado não pode ser None")

        snapshot = CalculoSnapshot(
            resultado=resultado,
            calculado_por=calculado_por,
            status=status,
        )
        self.calculos.append(snapshot)
        self.atualizado_em = _utc_now()
        return snapshot

    def marcar_ultimo_calculo_como_salvo(self) -> CalculoSnapshot:
        """Mark the most recent calculation draft as saved."""
        if not self.calculos:
            raise ValueError("Nenhum cálculo registrado ainda")

        # Find most recent draft
        draft = None
        for calc in reversed(self.calculos):
            if calc.status == "draft":
                draft = calc
                break

        if not draft:
            raise ValueError("Nenhum cálculo em draft encontrado")

        # Replace with saved version
        salvo = draft.marcar_como_salvo()
        idx = self.calculos.index(draft)
        self.calculos[idx] = salvo
        self.atualizado_em = _utc_now()
        return salvo

    def obter_ultimo_calculo_salvo(self) -> Optional[CalculoSnapshot]:
        """Get most recent saved calculation (or None)."""
        for calc in reversed(self.calculos):
            if calc.status == "saved":
                return calc
        return None

    def obter_historico_calculos(self) -> List[CalculoSnapshot]:
        """Get all calculation snapshots in chronological order."""
        return sorted(self.calculos, key=lambda c: c.calculado_em)

    def obter_condutores(self) -> List[dict]:
        """Return all conductors across every nivel and travessia.

        Each entry maps the nivel + position back to its conductor and geometry
        so callers can answer "what is hanging on this Poste?" without knowing
        the internal Nivel→Travessia hierarchy.
        """
        result = []
        for n in self.niveis:
            for t in n.travessias:
                result.append({
                    "nivel": n.nivel_enum.value,
                    "posicao": t.posicao,
                    "tipo_rede": t.condutor.tipo_rede.value,
                    "tipo_cabo": t.condutor.tipo_cabo.value,
                    "vao": t.geometria.vao,
                    "flecha": t.geometria.flecha,
                    "angulo": t.geometria.angulo,
                })
        return result

    def vincular_origem(self, origem_id: PosteId) -> None:
        """Link this Poste to its ancestor in a previous project.

        Call this when creating a Poste in Project Y that continues from a
        physical pole that was already studied in Project X.  The link is
        one-directional: the descendant holds a reference to the ancestor;
        navigating the full chain requires the repository.

        Raises:
            ValueError: If ``origem_id`` equals this Poste's own ID (self-loop).
        """
        if origem_id.value == self.id.value:
            raise ValueError("Poste não pode ser sua própria origem (self-loop)")
        self.origem_id = origem_id
        self.atualizado_em = _utc_now()

    def perfil(self) -> dict:
        """Human-readable summary of the physical items attached to this Poste.

        Returns identification, structural data, active spans (vao > 0),
        the last saved calculation, and lineage info.
        """
        ultimo = self.obter_ultimo_calculo_salvo()
        condutores_ativos = [
            c for c in self.obter_condutores() if c["vao"] > 0
        ]
        return {
            "id": str(self.id.value),
            "numero": self.numero,
            "tipo_poste": self.tipo_poste,
            "modelo_poste": self.modelo_poste,
            "projeto_id": str(self.projeto_id.value),
            "origem_id": str(self.origem_id.value) if self.origem_id else None,
            "condutores_ativos": condutores_ativos,
            "ultimo_calculo": ultimo.resumo() if ultimo else None,
        }

    def clonar_para_projeto(self, projeto_destino_id: ProjetoId) -> "Poste":
        """Create a deep copy of this Poste for a different project.

        The clone gets a new UUID, belongs to ``projeto_destino_id``, and has
        ``origem_id`` pre-set to this Poste's ID.  All Niveis and Travessias
        are deep-copied so modifications to the clone never touch the original.

        This is the canonical entry point for "Project Y starts from the
        physical pole already studied in Project X":

        1. Call this method on the Project-X Poste.
        2. Persist the returned clone via ``PosteRepository.salvar()``.
        3. The ``origem_id`` link is already in place — no extra call needed.

        The clone starts with a fresh timestamp (``criado_em``/``atualizado_em``)
        so it is immediately recognised as more recent than its ancestor.

        Raises:
            ValueError: If ``projeto_destino_id`` equals this Poste's own
                ``projeto_id`` (cloning within the same project is not allowed).
        """
        if projeto_destino_id.value == self.projeto_id.value:
            raise ValueError(
                "clonar_para_projeto: projeto destino deve ser diferente do projeto de origem"
            )

        # Deep-copy Niveis and their Travessias
        from copy import deepcopy

        niveis_clone = deepcopy(self.niveis)

        clone = Poste(
            projeto_id=projeto_destino_id,
            numero=self.numero,
            tipo_poste=self.tipo_poste,
            modelo_poste=self.modelo_poste,
            niveis=niveis_clone,
            geometria=deepcopy(self.geometria),
            # Lineage: this clone continues from the original
            origem_id=PosteId(value=self.id.value),
        )
        return clone

    def deletar(self, razao: str = "user requested") -> None:
        """Soft-delete this Poste (mark as deleted, not removed)."""
        self.deletado_em = _utc_now()
        # razao would be stored in events/audit log in Phase 3

    def esta_deletado(self) -> bool:
        """Check if this Poste is soft-deleted."""
        return self.deletado_em is not None


@dataclass
class Projeto:
    """Parent aggregate — groups multiple Postes and project metadata.
    
    A Projeto is the context/container for multiple Postes.
    It doesn't own Poste objects directly, only references (IDs).
    """

    owner_id: str
    nome: str
    id: ProjetoId = field(default_factory=ProjetoId)
    endereco: str = ""
    orgao: str = ""  # Organ/Department responsible
    ns: str = ""  # Code identifier
    estudado_por: str = ""
    matricula: str = ""  # Registration/Badge number
    data_estudo: Optional[datetime] = None
    poste_ids: List[PosteId] = field(default_factory=list)  # References only, not embedded
    criado_em: datetime = field(default_factory=_utc_now)
    atualizado_em: datetime = field(default_factory=_utc_now)
    deletado_em: Optional[datetime] = None  # Soft-delete

    def validar(self) -> None:
        """Enforce aggregate invariants."""
        if not self.owner_id or len(self.owner_id.strip()) == 0:
            raise ValueError("Projeto owner_id não pode estar vazio")
        if not self.nome or len(self.nome.strip()) == 0:
            raise ValueError("Projeto nome não pode estar vazio")

    def __post_init__(self) -> None:
        """Validate on construction."""
        self.validar()

    def adicionar_poste_id(self, poste_id: PosteId) -> None:
        """Register a new Poste ID in this Projeto."""
        if poste_id in self.poste_ids:
            raise ValueError(f"Poste {poste_id} já foi adicionado a este Projeto")
        self.poste_ids.append(poste_id)
        self.atualizado_em = _utc_now()

    def remover_poste_id(self, poste_id: PosteId) -> None:
        """Remove a Poste ID from this Projeto."""
        if poste_id not in self.poste_ids:
            raise ValueError(f"Poste {poste_id} não encontrado neste Projeto")
        self.poste_ids.remove(poste_id)
        self.atualizado_em = _utc_now()

    def obter_poste_ids(self) -> List[PosteId]:
        """Get all Poste IDs in this Projeto."""
        return self.poste_ids.copy()

    def deletar(self) -> None:
        """Soft-delete this Projeto."""
        self.deletado_em = _utc_now()

    def esta_deletado(self) -> bool:
        """Check if this Projeto is soft-deleted."""
        return self.deletado_em is not None
