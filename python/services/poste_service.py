"""Service layer for Poste aggregate — business logic and orchestration.

This service:
1. Orchestrates Poste operations (create, read, update, delete)
2. Enforces business rules and domain invariants
3. Manages calculation workflow, snapshots, and history
4. Coordinates with repository layer
5. Provides clean API for routers and external services
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from domain.aggregates import Poste as PosteAggregate, Nivel as NivelEntity
from domain.entities import Travessia as TravessiaEntity
from domain.value_objects import (
    Condutor, Geometria, NivelEnum, PosteId, ProjetoId,
    CalculoResultado, parse_cabo_conductor, parse_tipo_rede
)
from repositories.poste_repository import PosteRepository

logger = logging.getLogger(__name__)


def _historico_sort_key(item: Dict[str, Any]) -> str:
    """Normalize snapshot timestamps so history is always returned newest first."""
    calculado_em = item.get("calculado_em")
    if isinstance(calculado_em, datetime):
        return calculado_em.isoformat()
    return str(calculado_em or "")


class PosteService:
    """Business logic service for Poste aggregate root."""

    def __init__(self, poste_repo: PosteRepository):
        self.repo = poste_repo

    # ─────────────────────── POSTE CRUD ────────────────────────────────

    def criar_poste(
        self,
        projeto_id: UUID,
        numero: str,
        tipo_poste: str = "",
        modelo_poste: str = "",
        altura_poste: float = 11.0,
        altura_ancoragem: float = 9.2
    ) -> PosteAggregate:
        """Create a new Poste aggregate with 5 empty levels and 4 traversals each.

        Args:
            projeto_id: Parent project UUID
            numero: Unique poste number (e.g. "1", "2", "POL-01")
            tipo_poste: Type (e.g. "Concreto", "Aço")
            modelo_poste: Model (e.g. "11/600", "13/800")
            altura_poste: Pole height in meters (default 11.0)
            altura_ancoragem: Anchor point height (default 9.2)

        Returns: Persisted PosteAggregate

        Raises:
            ValueError: If numero already exists in project
        """
        # Check for duplicate numero in same project
        existing = self.repo.obter_por_numero(projeto_id, numero)
        if existing:
            raise ValueError(
                f"Poste número '{numero}' já existe neste projeto"
            )

        # Create empty Poste with 5 niveis × 4 travessias each
        niveis = self._criar_niveis_vazios(altura_poste, altura_ancoragem)

        poste = PosteAggregate(
            projeto_id=ProjetoId(value=projeto_id),
            numero=numero,
            niveis=niveis,
            tipo_poste=tipo_poste,
            modelo_poste=modelo_poste
        )

        # Persist and return hydrated aggregate
        return self.repo.salvar(poste)

    def obter_poste(self, poste_id: UUID) -> Optional[PosteAggregate]:
        """Get Poste aggregate by ID."""
        return self.repo.obter_por_id(poste_id)

    def obter_poste_por_numero(self, projeto_id: UUID, numero: str) -> Optional[PosteAggregate]:
        """Get Poste aggregate by (projeto_id, numero)."""
        return self.repo.obter_por_numero(projeto_id, numero)

    def listar_postes_do_projeto(self, projeto_id: UUID) -> List[PosteAggregate]:
        """List all Postes in a project (excludes soft-deleted)."""
        return self.repo.obter_todos_por_projeto(projeto_id)

    def atualizar_poste(
        self,
        poste_id: UUID,
        tipo_poste: Optional[str] = None,
        modelo_poste: Optional[str] = None
    ) -> PosteAggregate:
        """Update Poste metadata (tipo/modelo)."""
        poste = self.repo.obter_por_id(poste_id)
        if not poste:
            raise ValueError(f"Poste {poste_id} não encontrado")

        if tipo_poste is not None:
            poste.tipo_poste = tipo_poste
        if modelo_poste is not None:
            poste.modelo_poste = modelo_poste

        return self.repo.salvar(poste)

    def deletar_poste(self, poste_id: UUID) -> None:
        """Soft delete a Poste (don't remove if has saved calculations)."""
        poste = self.repo.obter_por_id(poste_id)
        if not poste:
            raise ValueError(f"Poste {poste_id} não encontrado")

        # Check if has saved calculations
        historico = self.repo.obter_historico(poste_id)
        saved_calcs = [h for h in historico if h['status'] == 'saved']

        if saved_calcs:
            logger.warning(
                f"Poste {poste.numero} tem {len(saved_calcs)} cálculos salvos. "
                f"Marcando como deletado (soft delete)"
            )

        self.repo.deletar_suave(poste_id)

    def restaurar_poste(self, poste_id: UUID) -> PosteAggregate:
        """Restore a soft-deleted Poste."""
        self.repo.restaurar(poste_id)
        poste = self.repo.obter_por_id(poste_id)
        if not poste:
            raise ValueError(f"Poste {poste_id} não restaurado corretamente")
        return poste

    # ─────────────────────── TRAVESSIA MANAGEMENT ──────────────────────

    def atualizar_travessia(
        self,
        poste_id: UUID,
        nivel_enum: NivelEnum,
        posicao: int,
        tipo_rede: str,
        tipo_cabo: str,
        vao: float,
        flecha: float,
        angulo: float
    ) -> PosteAggregate:
        """Update a single Travessia within a Poste nivel.

        This is the main way to modify conductor/geometry data.
        """
        poste = self.repo.obter_por_id(poste_id)
        if not poste:
            raise ValueError(f"Poste {poste_id} não encontrado")

        # Create domain value objects
        condutor = Condutor(
            tipo=parse_cabo_conductor(tipo_cabo),
            tipo_rede=parse_tipo_rede(tipo_rede)
        )
        geometria = Geometria(vao=vao, flecha=flecha, angulo=angulo)

        # Update through aggregate root
        poste.atualizar_travessia(nivel_enum, posicao, condutor, geometria)

        # Persist updated aggregate
        return self.repo.salvar(poste)

    # ─────────────────────── CALCULATION WORKFLOW ──────────────────────

    def registrar_calculo(
        self,
        poste_id: UUID,
        resultado: CalculoResultado,
        calculado_por: Optional[str] = None,
        status: str = "draft"
    ) -> UUID:
        """Register a new calculation snapshot for a Poste.

        Args:
            poste_id: Poste aggregate root ID
            resultado: CalculoResultado (output from calculation engine)
            calculado_por: User ID or email (who performed calculation)
            status: 'draft' (unsaved) | 'saved' (persistent)

        Returns: snapshot_id (UUID)
        """
        poste = self.repo.obter_por_id(poste_id)
        if not poste:
            raise ValueError(f"Poste {poste_id} não encontrado")

        # Register through repository
        snapshot_id = self.repo.registrar_calculo(
            poste=poste,
            resultado=resultado,
            calculado_por=calculado_por,
            status=status
        )

        logger.info(
            f"Cálculo registrado para Poste {poste.numero} "
            f"(status={status}, snapshot_id={snapshot_id})"
        )

        return snapshot_id

    def obter_historico_calculos(self, poste_id: UUID) -> List[Dict[str, Any]]:
        """Get calculation history for a Poste (most recent first)."""
        poste = self.repo.obter_por_id(poste_id)
        if not poste:
            raise ValueError(f"Poste {poste_id} não encontrado")

        historico = self.repo.obter_historico(poste_id)
        return list(reversed(sorted(historico, key=_historico_sort_key)))

    def obter_ultimocalculo(self, poste_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the most recent calculation for a Poste."""
        historico = self.obter_historico_calculos(poste_id)
        return historico[0] if historico else None

    # ─────────────────────── INVARIANTS ────────────────────────────────

    def validar_poste(self, poste_id: UUID) -> tuple[bool, str]:
        """Validate all domain invariants for a Poste.

        Returns: (is_valid, message)
        """
        poste = self.repo.obter_por_id(poste_id)
        if not poste:
            return False, f"Poste {poste_id} não encontrado"

        try:
            poste.validar()
            return True, "Poste válido"
        except ValueError as e:
            return False, str(e)

    # ─────────────────────── LINEAGE ─────────────────────────────────────

    def vincular_origem(self, poste_id: UUID, origem_id: UUID) -> PosteAggregate:
        """Link a Poste to its ancestor in a previous project.

        Use this when Project Y inherits a physical pole that was already
        studied in Project X.  The ``poste_id`` (in Project Y) is the
        descendant; ``origem_id`` (in Project X) is the ancestor.

        Business rules enforced:
        - Both Postes must exist and not be soft-deleted.
        - They must belong to different projects (intra-project loops are not
          meaningful in this domain).
        - The origin must not already have a descendant in the same project as
          the descendant (one-to-one per project pair).

        Returns the updated descendant Poste aggregate.
        """
        poste = self.repo.obter_por_id(poste_id)
        if not poste:
            raise ValueError(f"Poste {poste_id} não encontrado")

        origem = self.repo.obter_por_id(origem_id)
        if not origem:
            raise ValueError(f"Poste origem {origem_id} não encontrado")

        if poste.projeto_id.value == origem.projeto_id.value:
            raise ValueError(
                "Vínculo de origem deve ser entre projetos diferentes — "
                "postes do mesmo projeto não podem ser vinculados"
            )

        # Apply domain method (validates self-loop)
        poste.vincular_origem(PosteId(value=origem_id))

        # Persist via repository
        self.repo.vincular_origem(poste_id, origem_id)

        logger.info(
            "Poste %s (projeto %s) vinculado à origem %s (projeto %s)",
            poste.numero, poste.projeto_id, origem.numero, origem.projeto_id,
        )
        return self.repo.obter_por_id(poste_id)

    def obter_linhagem(self, poste_id: UUID) -> List[Dict[str, Any]]:
        """Return the full cross-project ancestry chain for a physical pole.

        The chain is returned oldest-first so callers can determine which
        project's data is most recent (last entry).  Each entry exposes
        ``atualizado_em`` and ``calculos_count`` to support conflict resolution
        (latest-timestamp-wins policy).
        """
        poste = self.repo.obter_por_id(poste_id)
        if not poste:
            raise ValueError(f"Poste {poste_id} não encontrado")
        return self.repo.obter_linhagem(poste_id)

    def clonar_para_projeto(
        self,
        poste_origem_id: UUID,
        projeto_destino_id: UUID,
    ) -> PosteAggregate:
        """Clone a Poste from one project into another, establishing the lineage link.

        This is the canonical implementation of "Project Y starts from the
        physical pole already in Project X":

        1. Loads the origin Poste (must exist, not deleted).
        2. Deep-copies its entire configuration (Niveis, Travessias, geometry).
        3. Assigns the clone to ``projeto_destino_id``.
        4. Pre-sets ``clone.origem_id = poste_origem_id`` (lineage).
        5. Persists and returns the new Poste.

        The clone starts with a fresh timestamp so it is immediately
        recognised as the most-recent data for this physical pole
        (timestamp-wins policy).

        Both projects must be **different**.  The clone can then be freely
        modified in Project Y without affecting Project X's data.

        Returns the newly created Poste aggregate (clone in Project Y).
        """
        origem = self.repo.obter_por_id(poste_origem_id)
        if not origem:
            raise ValueError(f"Poste origem {poste_origem_id} não encontrado")

        if origem.projeto_id.value == projeto_destino_id:
            raise ValueError(
                "clonar_para_projeto: projeto destino deve ser diferente do projeto de origem"
            )

        # Use aggregate domain method to create the clone
        clone = origem.clonar_para_projeto(ProjetoId(value=projeto_destino_id))

        # Persist the clone (salvar also validates invariants)
        clone = self.repo.salvar(clone)

        logger.info(
            "Poste '%s' clonado de projeto %s para projeto %s (novo id=%s, origem_id=%s)",
            clone.numero,
            origem.projeto_id.value,
            projeto_destino_id,
            clone.id.value,
            clone.origem_id.value if clone.origem_id else None,
        )
        return clone

    # ─────────────────────── HELPERS ──────────────────────────────────

    def _criar_niveis_vazios(
        self,
        altura_poste: float,
        altura_ancoragem: float
    ) -> List[NivelEntity]:
        """Create 5 empty levels with 4 empty traversals each."""
        niveis_orden = [
            NivelEnum.MT1, NivelEnum.MT2, NivelEnum.BT,
            NivelEnum.BTZ, NivelEnum.RAL
        ]

        niveis = []
        for nivel_enum in niveis_orden:
            # 4 empty traversals per level
            travessias = [
                TravessiaEntity(
                    posicao=i,
                    condutor=Condutor(
                        tipo=parse_cabo_conductor(None),
                        tipo_rede=parse_tipo_rede(None)
                    ),
                    geometria=Geometria(vao=0.0, flecha=0.0, angulo=0.0)
                )
                for i in range(1, 5)
            ]

            nivel = NivelEntity(
                nivel_enum=nivel_enum,
                altura_poste=altura_poste,
                altura_ancoragem=altura_ancoragem,
                travessias=travessias
            )
            niveis.append(nivel)

        return niveis

    def contar_postes(self, projeto_id: UUID) -> int:
        """Count Postes in a project (excludes soft-deleted)."""
        return len(self.listar_postes_do_projeto(projeto_id))
