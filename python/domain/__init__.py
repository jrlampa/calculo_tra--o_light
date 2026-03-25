"""Domain layer — DDD domain model (pure business logic, no dependencies).

This package contains the ubiquitous language of the application:
- Value Objects: immutable concepts (Condutor, Geometria, CalculoResultado)
- Entities: Travessia, Nivel (children of aggregates)
- Aggregates: Poste (root), Projeto (parent root)
- Events: Domain events for event sourcing & audit
- Exceptions: Domain-specific errors
"""

# Value objects
from domain.value_objects import (
    CaboConductor,
    Condutor,
    Geometria,
    Geometria_Poste,
    NivelEnum,
    PosteId,
    ProjetoId,
    TipoPoste,
    TipoRede,
    CalculoResultado,
)

# Entities
from domain.entities import Nivel, Travessia

# Aggregates
from domain.aggregates import CalculoSnapshot, Poste, Projeto

# Events
from domain.events import (
    CalculoDeletado,
    CalculoSnapshot as CalculoSnapshotEvent,
    DomainEvent,
    NivelAtualizado,
    PosteCriado,
    PosteDeletado,
    ProjetoCriado,
    ProjetoDeletado,
    TravessiaAtualizada,
)

# Exceptions
from domain.exceptions import (
    AggregateInvariantViolation,
    CalculoSnapshotNotFound,
    DomainException,
    DuplicatePosteNumero,
    DuplicateProjetoNumero,
    InvalidCalculoResult,
    InvalidCondutor,
    InvalidGeometria,
    InvalidNivel,
    InvalidNivelStructure,
    InvalidTravessia,
    NivelException,
    NoCálculoDraft,
    PosteAccessDenied,
    PosteAlreadyDeleted,
    PosteException,
    PosteNotFound,
    ProjetoAccessDenied,
    ProjetoAlreadyDeleted,
    ProjetoException,
    ProjetoNotFound,
    TravessiaException,
)

__all__ = [
    # Value objects
    "PosteId",
    "ProjetoId",
    "NivelEnum",
    "TipoPoste",
    "TipoRede",
    "CaboConductor",
    "Condutor",
    "Geometria",
    "Geometria_Poste",
    "CalculoResultado",
    # Entities
    "Travessia",
    "Nivel",
    # Aggregates
    "Poste",
    "Projeto",
    "CalculoSnapshot",
    # Events
    "DomainEvent",
    "ProjetoCriado",
    "PosteCriado",
    "NivelAtualizado",
    "TravessiaAtualizada",
    "CalculoSnapshotEvent",
    "CalculoDeletado",
    "PosteDeletado",
    "ProjetoDeletado",
    # Exceptions
    "DomainException",
    "ProjetoException",
    "ProjetoNotFound",
    "DuplicateProjetoNumero",
    "ProjetoAlreadyDeleted",
    "ProjetoAccessDenied",
    "PosteException",
    "PosteNotFound",
    "DuplicatePosteNumero",
    "PosteAlreadyDeleted",
    "PosteAccessDenied",
    "InvalidNivel",
    "InvalidTravessia",
    "CalculoSnapshotNotFound",
    "NoCálculoDraft",
    "InvalidCalculoResult",
    "NivelException",
    "InvalidNivelStructure",
    "TravessiaException",
    "InvalidGeometria",
    "InvalidCondutor",
    "AggregateInvariantViolation",
]
