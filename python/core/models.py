# The above code defines SQLAlchemy models for managing electrical distribution network data including
# projects, poles, calculation results, and reference data.
from datetime import datetime
from uuid import uuid4
from typing import Optional, List

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class Projeto(Base):
    __tablename__ = "projetos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    orgao = Column(String(100))
    ns = Column(String(50))
    nome = Column(String(200))
    endereco = Column(Text)
    estudado_por = Column(String(100))
    matricula = Column(String(50))
    data_estudo = Column(String(20))
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    postes = relationship("Poste", back_populates="projeto", cascade="all, delete-orphan")


class Poste(Base):
    """Agregado raiz Poste — pole/post in electrical distribution network.

    Each Poste aggregates:
    - Niveis (voltage levels): MT1, MT2, BT, BTZ, RAL (5 sempre)
    - Travessias per nivel: 4 (positions 1-4)
    - Calculation history: snapshots (append-only)
    """

    __tablename__ = "pontos"  # Keep table name for backward compat, but class = Poste

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    projeto_id = Column(UUID(as_uuid=True), ForeignKey("projetos.id"), nullable=False)
    numero = Column("ponto", String(50), nullable=False)
    tipo_poste = Column(String(50))
    modelo_poste = Column(String(50))
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deletado_em = Column(DateTime, nullable=True)  # Soft-delete support

    # Cross-project lineage: the Poste in a previous project that this one continues.
    # Nullable — only set when this Poste was derived from an ancestor.
    poste_origem_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pontos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    __table_args__ = (UniqueConstraint("projeto_id", "ponto", name="_projeto_ponto_uc"),)

    projeto = relationship("Projeto", back_populates="postes")
    # Self-referential: the ancestor Poste (in another project)
    poste_origem = relationship(
        "Poste",
        foreign_keys=[poste_origem_id],
        back_populates="continuacoes",
        uselist=False,
        remote_side=[id],
    )
    # All Postes that inherit from this one (in later projects)
    continuacoes = relationship(
        "Poste",
        foreign_keys=[poste_origem_id],
        back_populates="poste_origem",
        uselist=True,
    )
    niveis = relationship("NivelCalculo", back_populates="poste", cascade="all, delete-orphan")
    resultado = relationship(
        "ResultadoCalculo", back_populates="poste", uselist=False, cascade="all, delete-orphan"
    )
    calculos_snapshots = relationship(
        "CalculoSnapshot", back_populates="poste", cascade="all, delete-orphan"
    )

    @property
    def ponto(self) -> str:
        return self.numero

    @ponto.setter
    def ponto(self, value: str) -> None:
        self.numero = value


class NivelCalculo(Base):
    __tablename__ = "niveis_calculo"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ponto_id = Column(UUID(as_uuid=True), ForeignKey("pontos.id"), nullable=False)
    nivel = Column(String(20), nullable=False)  # MT1, MT2, BT, BTZ, RAL
    altura_poste = Column(Float)
    altura_ancoragem = Column(Float)

    __table_args__ = (UniqueConstraint("ponto_id", "nivel", name="_ponto_nivel_uc"),)

    poste = relationship("Poste", back_populates="niveis")
    travessias = relationship("Travessia", back_populates="nivel_ref", cascade="all, delete-orphan")


class Travessia(Base):
    __tablename__ = "travessias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    nivel_id = Column(UUID(as_uuid=True), ForeignKey("niveis_calculo.id"), nullable=False)
    posicao = Column(Integer, nullable=False)  # 1, 2, 3, 4
    tipo_rede = Column(String(50))
    tipo_cabo = Column(String(50))
    vao = Column(Float)
    flecha = Column(Float)
    angulo = Column(Float)
    qtd_ligacoes = Column(Float)
    qtd_cabos = Column(Float)

    __table_args__ = (UniqueConstraint("nivel_id", "posicao", name="_nivel_posicao_uc"),)

    nivel_ref = relationship("NivelCalculo", back_populates="travessias")


class ResultadoCalculo(Base):
    __tablename__ = "resultados_calculo"

    ponto_id = Column(UUID(as_uuid=True), ForeignKey("pontos.id"), primary_key=True)
    mt1_tracao = Column(Float)
    mt1_angulo = Column(Float)
    mt2_tracao = Column(Float)
    mt2_angulo = Column(Float)
    bt_tracao = Column(Float)
    bt_angulo = Column(Float)
    btz_tracao = Column(Float)
    btz_angulo = Column(Float)
    ral_tracao = Column(Float)
    ral_angulo = Column(Float)
    total_tracao = Column(Float)
    total_angulo = Column(Float)
    poste_ecc = Column(Float)
    texto_mt1 = Column(Text)
    texto_mt2 = Column(Text)
    texto_bt = Column(Text)
    texto_btz = Column(Text)
    texto_ral = Column(Text)
    texto_total = Column(Text)
    calculado_em = Column(DateTime, default=datetime.utcnow)

    poste = relationship("Poste", back_populates="resultado")


class CalculoSnapshot(Base):
    """Immutable snapshot of a calculation result (append-only event).

    Records calculation history with: resultado JSONB, timestamp, user, status.
    Enables audit trail and recovery of past calculations.
    """

    __tablename__ = "calculos_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    poste_id = Column(UUID(as_uuid=True), ForeignKey("pontos.id"), nullable=False)

    # Project that triggered this calculation — enables cross-project audit.
    # Nullable so old rows without this column are still valid.
    projeto_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projetos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Calculation result as JSONB (all fields from ResultadoCalculo flattened)
    resultado_json = Column(Text)  # JSON string of CalculoResultado

    calculado_em = Column(DateTime, default=datetime.utcnow)
    calculado_por = Column(String(100), nullable=True)  # user_id or email
    status = Column(String(20), default="draft")  # 'draft' | 'saved'

    poste = relationship("Poste", back_populates="calculos_snapshots")


class Cabo(Base):
    __tablename__ = "cabos"
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), unique=True, nullable=False)
    diametro = Column(Float)
    peso = Column(Float)


class PosteLookup(Base):
    """Reference lookup table for Poste types/models and capacity."""

    __tablename__ = "postes"
    id = Column(Integer, primary_key=True)
    tipo = Column(String(50))
    modelo = Column(String(50))
    altura_m = Column(Float)
    carga_admissivel_dan = Column(Float)


class Rede(Base):
    __tablename__ = "redes"
    id = Column(Integer, primary_key=True)
    tipo = Column(String(50), unique=True)
    descricao = Column(Text)


class NormaRegra(Base):
    __tablename__ = "normas_regras"
    id = Column(Integer, primary_key=True)
    categoria = Column(String(100))
    arquivo_origem = Column(String(200))
    titulo = Column(String(200))
    descricao = Column(Text)
    regra_tecnica = Column(Text)
    aplicavel_a = Column(Text)
    fonte_referencia = Column(Text)


Ponto = Poste
