"""Unit tests for PosteService — business logic layer for Poste aggregate."""
import pytest
from datetime import datetime, UTC
from uuid import UUID, uuid4

from domain.aggregates import Poste as PosteAggregate, Nivel as NivelEntity
from domain.entities import Travessia as TravessiaEntity
from domain.value_objects import (
    Condutor, Geometria, NivelEnum, PosteId, ProjetoId,
    CaboConductor, TipoRede, CalculoResultado
)
from services.poste_service import PosteService
from repositories.poste_repository import PosteRepository


# ─────────────────────── MOCKS & FIXTURES ───────────────────────────

class MockPosteRepository:
    """Mock repository for testing PosteService in isolation."""
    
    def __init__(self):
        self.postes = {}  # id → PosteAggregate
        self.snapshots = {}  # poste_id → [snapshots]
    
    def obter_por_id(self, poste_id: UUID) -> PosteAggregate | None:
        return self.postes.get(poste_id)
    
    def obter_por_numero(self, projeto_id: UUID, numero: str) -> PosteAggregate | None:
        for p in self.postes.values():
            if p.projeto_id.value == projeto_id and p.numero == numero:
                return p
        return None
    
    def obter_todos_por_projeto(self, projeto_id: UUID) -> list[PosteAggregate]:
        return [
            p for p in self.postes.values()
            if p.projeto_id.value == projeto_id and p.deletado_em is None
        ]
    
    def salvar(self, poste: PosteAggregate) -> PosteAggregate:
        # Check for duplicate number
        for p in self.postes.values():
            if (p.projeto_id.value == poste.projeto_id.value and
                p.numero == poste.numero and
                p.id.value != poste.id.value):
                raise ValueError(f"Poste número '{poste.numero}' já existe")
        
        # Validate
        poste.validar()
        
        # Store (in real repo, would persist to DB)
        self.postes[poste.id.value] = poste
        return poste
    
    def registrar_calculo(self, poste: PosteAggregate, resultado: CalculoResultado,
                         calculado_por: str | None = None, status: str = "draft") -> UUID:
        snapshot_id = uuid4()
        if poste.id.value not in self.snapshots:
            self.snapshots[poste.id.value] = []
        self.snapshots[poste.id.value].append({
            'id': snapshot_id,
            'calculado_em': datetime.now(UTC),
            'calculado_por': calculado_por,
            'status': status,
            'resultado': resultado.__dict__ if hasattr(resultado, '__dict__') else {}
        })
        return snapshot_id
    
    def obter_historico(self, poste_id: UUID) -> list[dict]:
        return self.snapshots.get(poste_id, [])
    
    def deletar_suave(self, poste_id: UUID) -> None:
        if poste_id in self.postes:
            self.postes[poste_id].deletado_em = datetime.now(UTC)
    
    def restaurar(self, poste_id: UUID) -> None:
        if poste_id in self.postes:
            self.postes[poste_id].deletado_em = None


@pytest.fixture
def mock_repo():
    """Mock repository fixture."""
    return MockPosteRepository()


@pytest.fixture
def poste_service(mock_repo):
    """PosteService fixture with mock repository."""
    return PosteService(mock_repo)


@pytest.fixture
def projeto_id():
    """Sample project ID."""
    return uuid4()


# ─────────────────────── TESTS ────────────────────────────────────

class TestPosteCRUD:
    """Test basic CRUD operations."""
    
    def test_criar_poste_success(self, poste_service, projeto_id):
        """Test creating a new Poste aggregate."""
        poste = poste_service.criar_poste(
            projeto_id=projeto_id,
            numero="1",
            tipo_poste="Concreto",
            modelo_poste="11/600"
        )
        
        assert poste.numero == "1"
        assert poste.tipo_poste == "Concreto"
        assert poste.modelo_poste == "11/600"
        assert len(poste.niveis) == 5  # Must have 5 niveis
        
        # Check that each nivel has 4 travessias
        for nivel in poste.niveis:
            assert len(nivel.travessias) == 4
    
    def test_criar_poste_duplicate_numero(self, poste_service, projeto_id):
        """Test that duplicate numero in same project raises error."""
        poste_service.criar_poste(projeto_id, "1")
        
        with pytest.raises(ValueError, match="já existe"):
            poste_service.criar_poste(projeto_id, "1")
    
    def test_obter_poste(self, poste_service, projeto_id):
        """Test retrieving a Poste by ID."""
        created = poste_service.criar_poste(projeto_id, "1")
        retrieved = poste_service.obter_poste(created.id.value)
        
        assert retrieved is not None
        assert retrieved.numero == "1"
        assert retrieved.id == created.id
    
    def test_obter_poste_nao_existente(self, poste_service):
        """Test retrieving non-existent Poste returns None."""
        result = poste_service.obter_poste(uuid4())
        assert result is None
    
    def test_obter_poste_por_numero(self, poste_service, projeto_id):
        """Test retrieving Poste by (project_id, numero)."""
        created = poste_service.criar_poste(projeto_id, "POL-01")
        retrieved = poste_service.obter_poste_por_numero(projeto_id, "POL-01")
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    def test_listar_postes_do_projeto(self, poste_service, projeto_id):
        """Test listing all Postes in a project."""
        p1 = poste_service.criar_poste(projeto_id, "1")
        p2 = poste_service.criar_poste(projeto_id, "2")
        
        postes = poste_service.listar_postes_do_projeto(projeto_id)
        
        assert len(postes) == 2
        ids = {p.id.value for p in postes}
        assert p1.id.value in ids
        assert p2.id.value in ids
    
    def test_atualizar_poste(self, poste_service, projeto_id):
        """Test updating Poste metadata."""
        created = poste_service.criar_poste(projeto_id, "1", tipo_poste="Aço")
        updated = poste_service.atualizar_poste(
            created.id.value,
            tipo_poste="Concreto",
            modelo_poste="13/800"
        )
        
        assert updated.tipo_poste == "Concreto"
        assert updated.modelo_poste == "13/800"
    
    def test_deletar_poste_soft_delete(self, poste_service, projeto_id):
        """Test soft delete marks deletado_em."""
        created = poste_service.criar_poste(projeto_id, "1")
        
        poste_service.deletar_poste(created.id.value)
        
        # Should not appear in listings
        postes = poste_service.listar_postes_do_projeto(projeto_id)
        assert len(postes) == 0
        
        # But should be retrievable directly
        retrieved = poste_service.obter_poste(created.id.value)
        assert retrieved.deletado_em is not None
    
    def test_restaurar_poste(self, poste_service, projeto_id):
        """Test restoring a soft-deleted Poste."""
        created = poste_service.criar_poste(projeto_id, "1")
        poste_service.deletar_poste(created.id.value)
        
        restored = poste_service.restaurar_poste(created.id.value)
        
        assert restored.deletado_em is None
        postes = poste_service.listar_postes_do_projeto(projeto_id)
        assert len(postes) == 1


class TestTravessiaManagement:
    """Test updating individual Travessias."""
    
    def test_atualizar_travessia(self, poste_service, projeto_id):
        """Test updating a single Travessia within a Poste."""
        poste = poste_service.criar_poste(projeto_id, "1")
        
        updated = poste_service.atualizar_travessia(
            poste_id=poste.id.value,
            nivel_enum=NivelEnum.MT1,
            posicao=1,
            tipo_rede="Convencional",
            tipo_cabo="CAA",
            vao=30.0,
            flecha=0.5,
            angulo=10.0
        )
        
        mt1 = updated.obter_nivel(NivelEnum.MT1)
        trav = mt1.obter_travessia(1)
        
        assert trav.geometria.vao == 30.0
        assert trav.geometria.flecha == 0.5
        assert trav.geometria.angulo == 10.0


class TestCalculoHistory:
    """Test calculation snapshot storage and retrieval."""
    
    def test_registrar_calculo(self, poste_service, projeto_id):
        """Test recording a calculation snapshot."""
        poste = poste_service.criar_poste(projeto_id, "1")
        
        resultado = CalculoResultado(
            mt1_tracao=217.0, mt1_angulo=177.0,
            mt2_tracao=171.0, mt2_angulo=90.0,
            bt_tracao=165.0, bt_angulo=60.0,
            btz_tracao=0.0, btz_angulo=0.0,
            ral_tracao=0.0, ral_angulo=0.0,
            total_tracao=374.0, total_angulo=112.0,
            poste_ecc=120.0
        )
        
        snapshot_id = poste_service.registrar_calculo(
            poste_id=poste.id.value,
            resultado=resultado,
            calculado_por="eng.silva@im3.com",
            status="saved"
        )
        
        assert snapshot_id is not None
    
    def test_obter_historico_calculos(self, poste_service, projeto_id):
        """Test retrieving calculation history."""
        poste = poste_service.criar_poste(projeto_id, "1")
        resultado = CalculoResultado(total_tracao=374.0, total_angulo=112.0, poste_ecc=120.0)
        
        snap1 = poste_service.registrar_calculo(poste.id.value, resultado, status="draft")
        snap2 = poste_service.registrar_calculo(poste.id.value, resultado, status="saved")
        
        historico = poste_service.obter_historico_calculos(poste.id.value)
        
        assert len(historico) == 2
        assert historico[0]['status'] == 'saved'  # Most recent first
    
    def test_obter_ultimocalculo(self, poste_service, projeto_id):
        """Test getting the most recent calculation."""
        poste = poste_service.criar_poste(projeto_id, "1")
        resultado = CalculoResultado(total_tracao=374.0, total_angulo=112.0, poste_ecc=120.0)
        
        poste_service.registrar_calculo(poste.id.value, resultado, status="draft")
        poste_service.registrar_calculo(poste.id.value, resultado, status="saved")
        
        ultimo = poste_service.obter_ultimocalculo(poste.id.value)
        
        assert ultimo is not None
        assert ultimo['status'] == 'saved'


class TestInvariants:
    """Test domain invariant validation."""
    
    def test_validar_poste_valid(self, poste_service, projeto_id):
        """Test validation of a valid Poste."""
        poste = poste_service.criar_poste(projeto_id, "1")
        
        is_valid, msg = poste_service.validar_poste(poste.id.value)
        
        assert is_valid is True
        assert "válido" in msg.lower()
    
    def test_validar_poste_nao_existente(self, poste_service):
        """Test validation fails for non-existent Poste."""
        is_valid, msg = poste_service.validar_poste(uuid4())
        
        assert is_valid is False
        assert "não encontrado" in msg.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
