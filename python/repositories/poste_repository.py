"""Repository for Poste aggregate root — data persistence layer.

This repository is responsible for:
1. Hydrating Poste aggregates from DB rows (Poste + Niveis + Travessias)
2. Persisting complete Poste aggregates (insert/update atomically)
3. Managing calculation history (snapshots)
4. Enforcing domain invariants at persistence boundary
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.models import Poste, NivelCalculo, Travessia, CalculoSnapshot
from domain.aggregates import Poste as PosteAggregate, Nivel as NivelEntity, Travessia as TravessiaEntity
from domain.value_objects import (
    Condutor, Geometria, NivelEnum, PosteId, ProjetoId,
    CalculoResultado, parse_cabo_conductor, parse_tipo_rede
)

logger = logging.getLogger(__name__)


class PosteRepository:
    """Repository for Poste aggregate root persistence."""

    def __init__(self, db: Session):
        self.db = db

    # ─────────────────────── HYDRATION (DB → Agregado) ───────────────────

    def obter_por_id(self, poste_id: UUID) -> Optional[PosteAggregate]:
        """Hydrate complete Poste aggregate from DB by ID."""
        db_poste = self.db.query(Poste).filter(Poste.id == poste_id).first()
        if not db_poste:
            return None
        return self._hidrate_agregado(db_poste)

    def obter_por_numero(self, projeto_id: UUID, numero: str) -> Optional[PosteAggregate]:
        """Hydrate Poste aggregate by (projeto_id, numero) unique constraint."""
        db_poste = self.db.query(Poste).filter(
            and_(
                Poste.projeto_id == projeto_id,
                Poste.numero == numero
            )
        ).first()
        if not db_poste:
            return None
        return self._hidrate_agregado(db_poste)

    def obter_todos_por_projeto(self, projeto_id: UUID) -> List[PosteAggregate]:
        """List all Postes in a project (excludes soft-deleted)."""
        db_postes = self.db.query(Poste).filter(
            and_(
                Poste.projeto_id == projeto_id,
                Poste.deletado_em.is_(None)
            )
        ).order_by(Poste.numero).all()
        return [self._hidrate_agregado(p) for p in db_postes]

    def _hidrate_agregado(self, db_poste: Poste) -> PosteAggregate:
        """Convert DB Poste row to domain Poste aggregate with full hierarchy."""
        # Fetch all Niveis for this Poste
        db_niveis = self.db.query(NivelCalculo).filter(
            NivelCalculo.ponto_id == db_poste.id
        ).all()

        # Convert each Nivel + Travessias to domain entities
        niveis_domain = []
        for db_nivel in db_niveis:
            # Fetch all Travessias for this Nivel
            db_travessias = self.db.query(Travessia).filter(
                Travessia.nivel_id == db_nivel.id
            ).order_by(Travessia.posicao).all()

            # Convert Travessias to domain
            travessias_domain = [
                TravessiaEntity(
                    posicao=t.posicao,
                    condutor=Condutor(
                        tipo=parse_cabo_conductor(t.tipo_cabo),
                        tipo_rede=parse_tipo_rede(t.tipo_rede)
                    ),
                    geometria=Geometria(
                        vao=t.vao or 0.0,
                        flecha=t.flecha or 0.0,
                        angulo=t.angulo or 0.0
                    )
                )
                for t in db_travessias
            ]

            # Create Nivel entity
            nivel = NivelEntity(
                nivel_enum=NivelEnum(db_nivel.nivel),
                altura_poste=db_nivel.altura_poste or 0.0,
                altura_ancoragem=db_nivel.altura_ancoragem or 0.0,
                travessias=travessias_domain
            )
            niveis_domain.append(nivel)

        # Ensure niveis are in correct order for aggregation
        niveis_ordered = self._garantir_ordem_niveis(niveis_domain)

        # Create Poste aggregate
        poste = PosteAggregate(
            projeto_id=ProjetoId(value=db_poste.projeto_id),
            numero=db_poste.numero,
            niveis=niveis_ordered,
            id=PosteId(value=db_poste.id),
            tipo_poste=db_poste.tipo_poste or "",
            modelo_poste=db_poste.modelo_poste or "",
            origem_id=PosteId(value=db_poste.poste_origem_id) if db_poste.poste_origem_id else None,
            criado_em=db_poste.criado_em,
            atualizado_em=db_poste.atualizado_em,
            deletado_em=db_poste.deletado_em
        )

        # Attach calculation snapshots (if any)
        self.db.query(CalculoSnapshot).filter(
            CalculoSnapshot.poste_id == db_poste.id
        ).order_by(CalculoSnapshot.calculado_em.desc()).all()

        # Convert snapshots to domain (parse JSON resultado)
        # TODO: implement when CalculoResultado serialization is finalized

        return poste

    def _garantir_ordem_niveis(self, niveis: List[NivelEntity]) -> List[NivelEntity]:
        """Ensure niveis are ordered: MT1, MT2, BT, BTZ, RAL."""
        ordem_esperada = [NivelEnum.MT1, NivelEnum.MT2, NivelEnum.BT, NivelEnum.BTZ, NivelEnum.RAL]
        niveis_map = {n.nivel_enum: n for n in niveis}
        return [niveis_map[e] for e in ordem_esperada if e in niveis_map]

    # ─────────────────────── PERSISTENCE (Agregado → DB) ───────────────

    def salvar(self, poste: PosteAggregate) -> PosteAggregate:
        """Save complete Poste aggregate atomically.

        Creates or updates:
        - Poste record
        - All Niveis and Travessias (cascade)
        - Latest ResultadoCalculo (if calculation exists)
        """
        try:
            # Validate aggregate invariants before persistence
            poste.validar()

            # Check for existing Poste (insert vs update)
            db_poste = self.db.query(Poste).filter(Poste.id == poste.id.value).first()

            if db_poste:
                # UPDATE existing
                db_poste.numero = poste.numero
                db_poste.tipo_poste = poste.tipo_poste
                db_poste.modelo_poste = poste.modelo_poste
                db_poste.poste_origem_id = poste.origem_id.value if poste.origem_id else None
                db_poste.atualizado_em = datetime.now(UTC)
            else:
                # INSERT new
                db_poste = Poste(
                    id=poste.id.value,
                    projeto_id=poste.projeto_id.value,
                    numero=poste.numero,
                    tipo_poste=poste.tipo_poste,
                    modelo_poste=poste.modelo_poste,
                    poste_origem_id=poste.origem_id.value if poste.origem_id else None,
                    criado_em=poste.criado_em,
                    atualizado_em=poste.atualizado_em
                )
                self.db.add(db_poste)

            # Save or remove Niveis/Travessias cascade
            self._salvar_niveis(db_poste, poste.niveis)

            # Commit changes
            self.db.commit()
            self.db.refresh(db_poste)

            logger.info(f"Poste {poste.numero} salvo com sucesso")
            return self._hidrate_agregado(db_poste)

        except IntegrityError as e:
            self.db.rollback()
            if "unique constraint" in str(e).lower() and "numero" in str(e).lower():
                raise ValueError(
                    f"Poste número '{poste.numero}' já existe neste projeto"
                ) from e
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao salvar Poste: {e}")
            raise

    def _salvar_niveis(self, db_poste: Poste, niveis: List[NivelEntity]) -> None:
        """Save all Niveis and their Travessias for a Poste."""
        # Fetch existing Niveis from DB
        existing_niveis = {
            n.nivel: n for n in self.db.query(NivelCalculo).filter(
                NivelCalculo.ponto_id == db_poste.id
            ).all()
        }

        # Ensure all 5 niveis exist in expected order
        for nivel_entity in niveis:
            nivel_str = nivel_entity.nivel_enum.value

            if nivel_str in existing_niveis:
                db_nivel = existing_niveis[nivel_str]
                db_nivel.altura_poste = nivel_entity.altura_poste
                db_nivel.altura_ancoragem = nivel_entity.altura_ancoragem
            else:
                db_nivel = NivelCalculo(
                    ponto_id=db_poste.id,
                    nivel=nivel_str,
                    altura_poste=nivel_entity.altura_poste,
                    altura_ancoragem=nivel_entity.altura_ancoragem
                )
                self.db.add(db_nivel)
                self.db.flush()  # Need ID for FK

            # Save Travessias
            self._salvar_travessias(db_nivel, nivel_entity.travessias)

    def _salvar_travessias(self, db_nivel: NivelCalculo, travessias: List[TravessiaEntity]) -> None:
        """Save all Travessias for a Nivel."""
        # Fetch existing Travessias
        existing_travessias = {
            t.posicao: t for t in self.db.query(Travessia).filter(
                Travessia.nivel_id == db_nivel.id
            ).all()
        }

        # Ensure exactly 4 Travessias (positions 1-4)
        for trav_entity in travessias:
            posicao = trav_entity.posicao

            if posicao in existing_travessias:
                t = existing_travessias[posicao]
                t.tipo_rede = trav_entity.condutor.tipo_rede.value
                t.tipo_cabo = trav_entity.condutor.tipo_cabo.value
                t.vao = trav_entity.geometria.vao
                t.flecha = trav_entity.geometria.flecha
                t.angulo = trav_entity.geometria.angulo
            else:
                t = Travessia(
                    nivel_id=db_nivel.id,
                    posicao=posicao,
                    tipo_rede=trav_entity.condutor.tipo_rede.value,
                    tipo_cabo=trav_entity.condutor.tipo_cabo.value,
                    vao=trav_entity.geometria.vao,
                    flecha=trav_entity.geometria.flecha,
                    angulo=trav_entity.geometria.angulo
                )
                self.db.add(t)

    # ─────────────────────── CALCULATION HISTORY ──────────────────────────

    def registrar_calculo(
        self,
        poste: PosteAggregate,
        resultado: CalculoResultado,
        calculado_por: Optional[str] = None,
        status: str = "draft",
        projeto_id: Optional[UUID] = None,
    ) -> UUID:
        """Record a new calculation snapshot (append-only).

        Args:
            poste: Poste aggregate that was calculated.
            resultado: CalculoResultado value object.
            calculado_por: User ID or email that ran the calculation.
            status: 'draft' or 'saved'.
            projeto_id: Explicit project that triggered this calculation.
                Falls back to ``poste.projeto_id`` when not provided.

        Returns: snapshot_id (UUID)
        """
        # Serialize resultado to JSON
        resultado_json = resultado.json() if hasattr(resultado, 'json') else json.dumps(
            {
                'mt1_tracao': getattr(resultado, 'mt1_tracao', 0),
                'mt1_angulo': getattr(resultado, 'mt1_angulo', 0),
                'mt2_tracao': getattr(resultado, 'mt2_tracao', 0),
                'mt2_angulo': getattr(resultado, 'mt2_angulo', 0),
                'bt_tracao': getattr(resultado, 'bt_tracao', 0),
                'bt_angulo': getattr(resultado, 'bt_angulo', 0),
                'btz_tracao': getattr(resultado, 'btz_tracao', 0),
                'btz_angulo': getattr(resultado, 'btz_angulo', 0),
                'ral_tracao': getattr(resultado, 'ral_tracao', 0),
                'ral_angulo': getattr(resultado, 'ral_angulo', 0),
                'total_tracao': getattr(resultado, 'total_tracao', 0),
                'total_angulo': getattr(resultado, 'total_angulo', 0),
                'poste_ecc': getattr(resultado, 'poste_ecc', 0),
            }
        )

        effective_projeto_id = projeto_id if projeto_id is not None else poste.projeto_id.value
        calculado_em = datetime.now(UTC).replace(tzinfo=None)

        snapshot = CalculoSnapshot(
            id=uuid4(),
            poste_id=poste.id.value,
            projeto_id=effective_projeto_id,
            resultado_json=resultado_json,
            calculado_em=calculado_em,
            calculado_por=calculado_por,
            status=status,
        )
        self.db.add(snapshot)
        self.db.commit()
        logger.info(f"Cálculo snapshot registrado para Poste {poste.numero}")
        return snapshot.id

    def obter_historico(self, poste_id: UUID) -> List[Dict[str, Any]]:
        """Retrieve calculation history for a Poste (most recent first)."""
        snapshots = self.db.query(CalculoSnapshot).filter(
            CalculoSnapshot.poste_id == poste_id
        ).order_by(CalculoSnapshot.calculado_em.desc()).all()

        return [
            {
                'id': s.id,
                'calculado_em': s.calculado_em.isoformat(),
                'calculado_por': s.calculado_por,
                'status': s.status,
                'projeto_id': str(s.projeto_id) if s.projeto_id else None,
                'resultado': json.loads(s.resultado_json) if s.resultado_json else {},
            }
            for s in snapshots
        ]

    # ─────────────────────── LINEAGE ──────────────────────────────────────

    def vincular_origem(self, poste_id: UUID, origem_id: UUID) -> None:
        """Persist the lineage link between a Poste and its predecessor.

        Sets ``poste_origem_id`` on the descendant record.  This is separate
        from ``salvar()`` so callers can link an already-created Poste without
        going through the full aggregate save path.
        """
        db_poste = self.db.query(Poste).filter(Poste.id == poste_id).first()
        if not db_poste:
            raise ValueError(f"Poste {poste_id} não encontrado")
        origem = self.db.query(Poste).filter(Poste.id == origem_id).first()
        if not origem:
            raise ValueError(f"Poste origem {origem_id} não encontrado")
        db_poste.poste_origem_id = origem_id
        db_poste.atualizado_em = datetime.now(UTC)
        self.db.commit()
        logger.info(f"Poste {db_poste.numero} vinculado à origem {origem.numero}")

    def obter_linhagem(self, poste_id: UUID, max_profundidade: int = 50) -> List[Dict[str, Any]]:
        """Return the full ancestry chain for a Poste, oldest first.

        Follows the ``poste_origem_id`` chain up to ``max_profundidade`` hops
        to avoid infinite loops if data is inconsistent.  The list always
        starts with the root ancestor and ends with the requested Poste.

        Each entry includes:
        - id, numero, tipo_poste, modelo_poste
        - projeto_id (which project contains this Poste)
        - atualizado_em (timestamp — newer entries take precedence)
        - calculos_count (how many snapshots exist)
        """
        chain: List[Dict[str, Any]] = []
        visited: set = set()

        current_id: Optional[UUID] = poste_id
        while current_id and len(chain) < max_profundidade:
            if current_id in visited:
                logger.warning("Ciclo detectado na linhagem do Poste %s", poste_id)
                break
            visited.add(current_id)

            db_poste = self.db.query(Poste).filter(Poste.id == current_id).first()
            if not db_poste:
                break

            calculos_count = self.db.query(CalculoSnapshot).filter(
                CalculoSnapshot.poste_id == current_id
            ).count()

            chain.append({
                "id": str(db_poste.id),
                "numero": db_poste.numero,
                "tipo_poste": db_poste.tipo_poste or "",
                "modelo_poste": db_poste.modelo_poste or "",
                "projeto_id": str(db_poste.projeto_id),
                "origem_id": str(db_poste.poste_origem_id) if db_poste.poste_origem_id else None,
                "atualizado_em": db_poste.atualizado_em.isoformat() if db_poste.atualizado_em else None,
                "calculos_count": calculos_count,
            })

            current_id = db_poste.poste_origem_id

        # Reverse so the oldest ancestor is first
        chain.reverse()
        return chain

    def deletar_suave(self, poste_id: UUID) -> None:
        """Soft delete a Poste (mark deletado_em, don't remove from DB)."""
        poste = self.db.query(Poste).filter(Poste.id == poste_id).first()
        if poste:
            poste.deletado_em = datetime.now(UTC)
            self.db.commit()
            logger.info(f"Poste {poste.numero} marcado como deletado")

    def restaurar(self, poste_id: UUID) -> None:
        """Restore a soft-deleted Poste."""
        poste = self.db.query(Poste).filter(Poste.id == poste_id).first()
        if poste:
            poste.deletado_em = None
            self.db.commit()
            logger.info(f"Poste {poste.numero} restaurado")
