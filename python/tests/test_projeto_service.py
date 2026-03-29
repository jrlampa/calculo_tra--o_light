"""Unit tests for ProjetoService."""
import pytest
from datetime import UTC, datetime
from uuid import uuid4

from models.projeto import Projeto, ProjetoCreate, ProjetoUpdate
from services.projeto_service import ProjetoService
from core.exceptions import NotFoundError, PermissionError, ValidationError


class MockProjetoRepository:
    """Mock repository for testing."""

    def __init__(self):
        self.projetos = {}
        self.pontos_count = {}

    async def get(self, id):
        return self.projetos.get(id)

    async def get_multi(self, skip=0, limit=100, owner_id=None):
        projetos = list(self.projetos.values())
        if owner_id:
            projetos = [p for p in projetos if p.owner_id == owner_id]
        return projetos[skip:skip + limit]

    async def create(self, obj_in):
        projeto = Projeto(
            id=uuid4(),
            **obj_in.model_dump(),
            total_pontos=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        self.projetos[projeto.id] = projeto
        self.pontos_count[projeto.id] = 0
        return projeto

    async def update(self, db_obj, obj_in):
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db_obj.updated_at = datetime.now(UTC)
        self.projetos[db_obj.id] = db_obj
        return db_obj

    async def delete(self, id):
        projeto = self.projetos.get(id)
        if projeto:
            del self.projetos[id]
            del self.pontos_count[id]
        return projeto

    async def count(self, owner_id=None):
        if owner_id:
            return len([p for p in self.projetos.values() if p.owner_id == owner_id])
        return len(self.projetos)

    async def user_can_access_projeto(self, projeto_id, user_id):
        projeto = self.projetos.get(projeto_id)
        return projeto and projeto.owner_id == user_id

    async def get_with_pontos_count(self, projeto_id):
        projeto = self.projetos.get(projeto_id)
        if projeto:
            return {
                **projeto.model_dump(),
                "total_pontos": self.pontos_count.get(projeto_id, 0)
            }
        return None


@pytest.fixture
def mock_repo():
    """Fixture for mock repository."""
    return MockProjetoRepository()


@pytest.fixture
def projeto_service(mock_repo):
    """Fixture for projeto service with mock repository."""
    return ProjetoService(mock_repo)


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return uuid4()


@pytest.fixture
def sample_projeto_data():
    """Sample projeto data for testing."""
    return {
        "orgao": "Test Orgao",
        "ns": "NS-001",
        "nome": "Test Projeto",
        "endereco": "Test Address",
        "estudado_por": "Test User",
        "matricula": "12345",
        "data_estudo": datetime.now(UTC),
        "owner_id": uuid4()
    }


class TestProjetoService:
    """Test cases for ProjetoService."""

    @pytest.mark.asyncio
    async def test_create_projeto_success(self, projeto_service, sample_user_id):
        """Test successful projeto creation."""
        projeto_data = ProjetoCreate(
            orgao="Test Orgao",
            ns="NS-001",
            nome="Test Projeto",
            endereco="Test Address",
            estudado_por="Test User",
            matricula="12345",
            data_estudo=datetime.now(UTC),
            owner_id=sample_user_id
        )

        result = await projeto_service.create_projeto(projeto_data, sample_user_id)

        assert result.orgao == "Test Orgao"
        assert result.ns == "NS-001"
        assert result.nome == "Test Projeto"
        assert result.owner_id == sample_user_id

    @pytest.mark.asyncio
    async def test_create_projeto_duplicate_ns(self, projeto_service, sample_user_id):
        """Test projeto creation with duplicate NS."""
        projeto_data = ProjetoCreate(
            orgao="Test Orgao",
            ns="NS-001",
            nome="Test Projeto 1",
            estudado_por="Test User",
            matricula="12345",
            owner_id=sample_user_id
        )

        # Create first projeto
        await projeto_service.create_projeto(projeto_data, sample_user_id)

        # Try to create second with same NS
        projeto_data2 = ProjetoCreate(
            orgao="Test Orgao",
            ns="NS-001",
            nome="Test Projeto 2",
            estudado_por="Test User",
            matricula="12345",
            owner_id=sample_user_id
        )

        with pytest.raises(ValidationError, match="já existe"):
            await projeto_service.create_projeto(projeto_data2, sample_user_id)

    @pytest.mark.asyncio
    async def test_get_projeto_success(self, projeto_service, sample_user_id):
        """Test successful projeto retrieval."""
        projeto_data = ProjetoCreate(
            orgao="Test Orgao",
            ns="NS-001",
            nome="Test Projeto",
            estudado_por="Test User",
            matricula="12345",
            owner_id=sample_user_id
        )

        created = await projeto_service.create_projeto(projeto_data, sample_user_id)
        retrieved = await projeto_service.get_projeto(created.id, sample_user_id)

        assert retrieved.id == created.id
        assert retrieved.nome == "Test Projeto"

    @pytest.mark.asyncio
    async def test_get_projeto_not_found(self, projeto_service, sample_user_id):
        """Test projeto retrieval when not found."""
        with pytest.raises(NotFoundError, match="não encontrado"):
            await projeto_service.get_projeto(uuid4(), sample_user_id)

    @pytest.mark.asyncio
    async def test_get_projeto_permission_denied(self, projeto_service, sample_user_id):
        """Test projeto retrieval without permission."""
        other_user_id = uuid4()
        projeto_data = ProjetoCreate(
            orgao="Test Orgao",
            ns="NS-001",
            nome="Test Projeto",
            estudado_por="Test User",
            matricula="12345",
            owner_id=other_user_id
        )

        created = await projeto_service.create_projeto(projeto_data, other_user_id)

        with pytest.raises(PermissionError, match="Sem permissão"):
            await projeto_service.get_projeto(created.id, sample_user_id)

    @pytest.mark.asyncio
    async def test_update_projeto_success(self, projeto_service, sample_user_id):
        """Test successful projeto update."""
        projeto_data = ProjetoCreate(
            orgao="Test Orgao",
            ns="NS-001",
            nome="Test Projeto",
            estudado_por="Test User",
            matricula="12345",
            owner_id=sample_user_id
        )

        created = await projeto_service.create_projeto(projeto_data, sample_user_id)

        update_data = ProjetoUpdate(
            nome="Updated Projeto",
            endereco="Updated Address"
        )

        updated = await projeto_service.update_projeto(created.id, update_data, sample_user_id)

        assert updated.nome == "Updated Projeto"
        assert updated.endereco == "Updated Address"
        assert updated.orgao == "Test Orgao"  # Unchanged

    @pytest.mark.asyncio
    async def test_delete_projeto_success(self, projeto_service, sample_user_id):
        """Test successful projeto deletion."""
        projeto_data = ProjetoCreate(
            orgao="Test Orgao",
            ns="NS-001",
            nome="Test Projeto",
            estudado_por="Test User",
            matricula="12345",
            owner_id=sample_user_id
        )

        created = await projeto_service.create_projeto(projeto_data, sample_user_id)
        deleted = await projeto_service.delete_projeto(created.id, sample_user_id)

        assert deleted.id == created.id

        with pytest.raises(NotFoundError):
            await projeto_service.get_projeto(created.id, sample_user_id)

    @pytest.mark.asyncio
    async def test_delete_projeto_with_pontos(self, projeto_service, sample_user_id):
        """Test projeto deletion with associated pontos."""
        projeto_data = ProjetoCreate(
            orgao="Test Orgao",
            ns="NS-001",
            nome="Test Projeto",
            estudado_por="Test User",
            matricula="12345",
            owner_id=sample_user_id
        )

        created = await projeto_service.create_projeto(projeto_data, sample_user_id)

        # Simulate pontos associated with projeto
        projeto_service.projeto_repository.pontos_count[created.id] = 5

        with pytest.raises(ValidationError, match="pontos associados"):
            await projeto_service.delete_projeto(created.id, sample_user_id)

    @pytest.mark.asyncio
    async def test_get_projetos_pagination(self, projeto_service, sample_user_id):
        """Test projetos listing with pagination."""
        # Create multiple projetos
        for i in range(25):
            projeto_data = ProjetoCreate(
                orgao="Test Orgao",
                ns=f"NS-{i:03d}",
                nome=f"Test Projeto {i}",
                estudado_por="Test User",
                matricula="12345",
                owner_id=sample_user_id
            )
            await projeto_service.create_projeto(projeto_data, sample_user_id)

        # Test first page
        page1 = await projeto_service.get_projetos(sample_user_id, skip=0, limit=10)
        assert len(page1) == 10

        # Test second page
        page2 = await projeto_service.get_projetos(sample_user_id, skip=10, limit=10)
        assert len(page2) == 10

        # Test last page
        page3 = await projeto_service.get_projetos(sample_user_id, skip=20, limit=10)
        assert len(page3) == 5

    @pytest.mark.asyncio
    async def test_get_projeto_stats(self, projeto_service, sample_user_id):
        """Test projeto statistics."""
        # Create projetos
        for i in range(3):  # Reduced to avoid hitting limit
            projeto_data = ProjetoCreate(
                orgao="Test Orgao",
                ns=f"NS-{i:03d}",
                nome=f"Test Projeto {i}",
                estudado_por="Test User",
                matricula="12345",
                owner_id=sample_user_id
            )
            await projeto_service.create_projeto(projeto_data, sample_user_id)

        stats = await projeto_service.get_projeto_stats(sample_user_id)

        assert stats["total_projetos"] == 3
        assert stats["total_pontos"] == 0
        assert "projetos_by_month" in stats
        assert stats["average_pontos_per_projeto"] == 0
