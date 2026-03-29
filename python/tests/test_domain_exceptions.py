"""Unit tests for domain exceptions.

Verifies that:
1. Each exception carries the correct ``message`` and ``code``.
2. Exception hierarchy is as declared (inheritance chain).
3. ``str(exc)`` equals the message (via ``Exception.__init__``).
"""
import sys
import os

os.environ.setdefault("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "false")
os.environ.setdefault("APP_ENV", "development")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from domain.exceptions import (
    DomainException,
    ProjetoException,
    ProjetoNotFound,
    DuplicateProjetoNumero,
    ProjetoAlreadyDeleted,
    ProjetoAccessDenied,
    PosteException,
    PosteNotFound,
    DuplicatePosteNumero,
    PosteAlreadyDeleted,
    PosteAccessDenied,
    InvalidNivel,
    InvalidTravessia,
    CalculoSnapshotNotFound,
    NoCálculoDraft,
    InvalidCalculoResult,
    NivelException,
    InvalidNivelStructure,
    TravessiaException,
    InvalidGeometria,
    InvalidCondutor,
    AggregateInvariantViolation,
)


# ──────────────────────── DomainException base ────────────────────────────────

class TestDomainException:
    def test_message_and_code_stored(self):
        exc = DomainException("Test error", "TEST_CODE")
        assert exc.message == "Test error"
        assert exc.code == "TEST_CODE"

    def test_default_code(self):
        exc = DomainException("Something went wrong")
        assert exc.code == "DOMAIN_ERROR"

    def test_str_equals_message(self):
        exc = DomainException("My error")
        assert str(exc) == "My error"

    def test_is_exception(self):
        exc = DomainException("x")
        assert isinstance(exc, Exception)


# ──────────────────────── Projeto exceptions ──────────────────────────────────

class TestProjetoExceptions:
    def test_projeto_not_found_message_and_code(self):
        exc = ProjetoNotFound("abc-123")
        assert "abc-123" in exc.message
        assert exc.code == "PROJETO_NOT_FOUND"
        assert isinstance(exc, ProjetoException)
        assert isinstance(exc, DomainException)

    def test_duplicate_projeto_numero(self):
        exc = DuplicateProjetoNumero("NS-001")
        assert "NS-001" in exc.message
        assert exc.code == "DUPLICATE_PROJETO_NUMERO"
        assert isinstance(exc, ProjetoException)

    def test_projeto_already_deleted(self):
        exc = ProjetoAlreadyDeleted("proj-456")
        assert "proj-456" in exc.message
        assert exc.code == "PROJETO_ALREADY_DELETED"
        assert isinstance(exc, ProjetoException)

    def test_projeto_access_denied(self):
        exc = ProjetoAccessDenied("proj-789", "user-001")
        assert "proj-789" in exc.message
        assert "user-001" in exc.message
        assert exc.code == "PROJETO_ACCESS_DENIED"
        assert isinstance(exc, ProjetoException)


# ──────────────────────── Poste exceptions ────────────────────────────────────

class TestPosteExceptions:
    def test_poste_not_found(self):
        exc = PosteNotFound("poste-001")
        assert "poste-001" in exc.message
        assert exc.code == "POSTE_NOT_FOUND"
        assert isinstance(exc, PosteException)
        assert isinstance(exc, DomainException)

    def test_duplicate_poste_numero(self):
        exc = DuplicatePosteNumero("proj-abc", "P-01")
        assert "proj-abc" in exc.message
        assert "P-01" in exc.message
        assert exc.code == "DUPLICATE_POSTE_NUMERO"
        assert isinstance(exc, PosteException)

    def test_poste_already_deleted(self):
        exc = PosteAlreadyDeleted("poste-999")
        assert "poste-999" in exc.message
        assert exc.code == "POSTE_ALREADY_DELETED"
        assert isinstance(exc, PosteException)

    def test_poste_access_denied(self):
        exc = PosteAccessDenied("poste-1", "user-2")
        assert "poste-1" in exc.message
        assert "user-2" in exc.message
        assert exc.code == "POSTE_ACCESS_DENIED"
        assert isinstance(exc, PosteException)

    def test_invalid_nivel(self):
        exc = InvalidNivel("MT999")
        assert "MT999" in exc.message
        assert exc.code == "INVALID_NIVEL"
        assert isinstance(exc, PosteException)

    def test_invalid_travessia(self):
        exc = InvalidTravessia("posição negativa")
        assert "posição negativa" in exc.message
        assert exc.code == "INVALID_TRAVESSIA"
        assert isinstance(exc, PosteException)

    def test_calculo_snapshot_not_found(self):
        exc = CalculoSnapshotNotFound("poste-1", "calc-2")
        assert "poste-1" in exc.message
        assert "calc-2" in exc.message
        assert exc.code == "CALCULO_SNAPSHOT_NOT_FOUND"
        assert isinstance(exc, PosteException)

    def test_no_calculo_draft(self):
        exc = NoCálculoDraft("poste-5")
        assert "poste-5" in exc.message
        assert exc.code == "NO_CALCULO_DRAFT"
        assert isinstance(exc, PosteException)

    def test_invalid_calculo_result(self):
        exc = InvalidCalculoResult("tensão negativa")
        assert "tensão negativa" in exc.message
        assert exc.code == "INVALID_CALCULO_RESULT"
        assert isinstance(exc, PosteException)


# ──────────────────────── Nivel / Travessia exceptions ────────────────────────

class TestNivelAndTravessiaExceptions:
    def test_invalid_nivel_structure(self):
        exc = InvalidNivelStructure("menos de 4 travessias")
        assert "menos de 4 travessias" in exc.message
        assert exc.code == "INVALID_NIVEL_STRUCTURE"
        assert isinstance(exc, NivelException)
        assert isinstance(exc, DomainException)

    def test_invalid_geometria(self):
        exc = InvalidGeometria("vão negativo")
        assert "vão negativo" in exc.message
        assert exc.code == "INVALID_GEOMETRIA"
        assert isinstance(exc, DomainException)

    def test_invalid_condutor(self):
        exc = InvalidCondutor("cabo desconhecido")
        assert "cabo desconhecido" in exc.message
        assert exc.code == "INVALID_CONDUTOR"
        assert isinstance(exc, DomainException)


# ──────────────────────── AggregateInvariantViolation ─────────────────────────

class TestAggregateInvariantViolation:
    def test_aggregate_type_in_message(self):
        exc = AggregateInvariantViolation("Poste", "número duplicado")
        assert "Poste" in exc.message
        assert "número duplicado" in exc.message
        assert exc.code == "AGGREGATE_INVARIANT_VIOLATION"
        assert isinstance(exc, DomainException)

    def test_can_be_caught_as_domain_exception(self):
        with pytest.raises(DomainException):
            raise AggregateInvariantViolation("Projeto", "invariante violada")


# ──────────────────────── Raising and catching ────────────────────────────────

class TestRaisingAndCatching:
    def test_poste_not_found_can_be_caught_as_poste_exception(self):
        with pytest.raises(PosteException):
            raise PosteNotFound("p-001")

    def test_projeto_not_found_can_be_caught_as_domain_exception(self):
        with pytest.raises(DomainException):
            raise ProjetoNotFound("pr-001")

    def test_travessia_exception_hierarchy(self):
        # TravessiaException extends DomainException (not PosteException)
        assert issubclass(TravessiaException, DomainException)
        assert not issubclass(TravessiaException, PosteException)
