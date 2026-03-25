"""Domain exceptions — errors representing violations of domain invariants.

Domain exceptions are raised when business rules are violated.
They represent expected error conditions (not programming errors).
"""


class DomainException(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ProjetoException(DomainException):
    """Base exception for Projeto-related errors."""

    pass


class ProjetoNotFound(ProjetoException):
    """Projeto with given ID not found."""

    def __init__(self, projeto_id: str):
        super().__init__(f"Projeto não encontrado: {projeto_id}", "PROJETO_NOT_FOUND")


class DuplicateProjetoNumero(ProjetoException):
    """Projeto with this numero already exists (within same owner)."""

    def __init__(self, numero: str):
        super().__init__(
            f"Projeto com numero '{numero}' já existe",
            "DUPLICATE_PROJETO_NUMERO",
        )


class ProjetoAlreadyDeleted(ProjetoException):
    """Projeto is already soft-deleted."""

    def __init__(self, projeto_id: str):
        super().__init__(f"Projeto {projeto_id} já foi deletado", "PROJETO_ALREADY_DELETED")


class ProjetoAccessDenied(ProjetoException):
    """User does not have access to this Projeto."""

    def __init__(self, projeto_id: str, user_id: str):
        super().__init__(
            f"User {user_id} não tem acesso ao Projeto {projeto_id}",
            "PROJETO_ACCESS_DENIED",
        )


class PosteException(DomainException):
    """Base exception for Poste-related errors."""

    pass


class PosteNotFound(PosteException):
    """Poste with given ID not found."""

    def __init__(self, poste_id: str):
        super().__init__(f"Poste não encontrado: {poste_id}", "POSTE_NOT_FOUND")


class DuplicatePosteNumero(PosteException):
    """Poste with this numero already exists within the Projeto."""

    def __init__(self, projeto_id: str, numero: str):
        super().__init__(
            f"Poste com numero '{numero}' já existe no Projeto {projeto_id}",
            "DUPLICATE_POSTE_NUMERO",
        )


class PosteAlreadyDeleted(PosteException):
    """Poste is already soft-deleted."""

    def __init__(self, poste_id: str):
        super().__init__(f"Poste {poste_id} já foi deletado", "POSTE_ALREADY_DELETED")


class PosteAccessDenied(PosteException):
    """User does not have access to this Poste."""

    def __init__(self, poste_id: str, user_id: str):
        super().__init__(
            f"User {user_id} não tem acesso ao Poste {poste_id}",
            "POSTE_ACCESS_DENIED",
        )


class InvalidNivel(PosteException):
    """Invalid or unexpected NivelEnum."""

    def __init__(self, nivel: str):
        super().__init__(f"Nível 'inválido': {nivel}", "INVALID_NIVEL")


class InvalidTravessia(PosteException):
    """Invalid travessia (position, data, or state)."""

    def __init__(self, mensagem: str):
        super().__init__(f"Travessia inválida: {mensagem}", "INVALID_TRAVESSIA")


class CalculoSnapshotNotFound(PosteException):
    """Calculation snapshot not found."""

    def __init__(self, poste_id: str, calculo_id: str):
        super().__init__(
            f"Cálculo {calculo_id} não encontrado para Poste {poste_id}",
            "CALCULO_SNAPSHOT_NOT_FOUND",
        )


class NoCálculoDraft(PosteException):
    """No draft calculation found for Poste."""

    def __init__(self, poste_id: str):
        super().__init__(
            f"Nenhum cálculo em draft encontrado para Poste {poste_id}",
            "NO_CALCULO_DRAFT",
        )


class InvalidCalculoResult(PosteException):
    """Calculation result is invalid (e.g., negative tension)."""

    def __init__(self, mensagem: str):
        super().__init__(f"Resultado de cálculo inválido: {mensagem}", "INVALID_CALCULO_RESULT")


class NivelException(DomainException):
    """Base exception for Nivel-related errors."""

    pass


class InvalidNivelStructure(NivelException):
    """Nivel does not have required structure (e.g., not 4 travessias)."""

    def __init__(self, mensagem: str):
        super().__init__(f"Estrutura de Nivel inválida: {mensagem}", "INVALID_NIVEL_STRUCTURE")


class TravessiaException(DomainException):
    """Base exception for Travessia-related errors."""

    pass


class InvalidGeometria(DomainException):
    """Invalid geometric values (negative, out of bounds, etc)."""

    def __init__(self, mensagem: str):
        super().__init__(f"Geometria inválida: {mensagem}", "INVALID_GEOMETRIA")


class InvalidCondutor(DomainException):
    """Invalid conductor/cable data."""

    def __init__(self, mensagem: str):
        super().__init__(f"Condutor inválido: {mensagem}", "INVALID_CONDUTOR")


class AggregateInvariantViolation(DomainException):
    """Generic invariant violation at aggregate level."""

    def __init__(self, aggregate_type: str, mensagem: str):
        super().__init__(
            f"Invariante violada em {aggregate_type}: {mensagem}",
            "AGGREGATE_INVARIANT_VIOLATION",
        )
