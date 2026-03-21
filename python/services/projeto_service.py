"""Service layer for projeto business logic."""
from __future__ import annotations

from typing import List, Optional, UUID
from uuid import uuid4

from ..models.projeto import Projeto, ProjetoCreate, ProjetoUpdate
from ..repositories.projeto_repository import ProjetoRepository
from ..core.exceptions import NotFoundError, PermissionError, ValidationError


class ProjetoService:
    """Service for projeto business operations."""
    
    def __init__(self, projeto_repository: ProjetoRepository):
        self.projeto_repository = projeto_repository
    
    async def get_projeto(self, projeto_id: UUID, user_id: UUID) -> Projeto:
        """Get a projeto by ID with permission check."""
        projeto = await self.projeto_repository.get(projeto_id)
        
        if not projeto:
            raise NotFoundError(f"Projeto {projeto_id} não encontrado")
        
        if projeto.owner_id != user_id:
            raise PermissionError("Sem permissão para acessar este projeto")
        
        return projeto
    
    async def get_projetos(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Projeto]:
        """Get projetos for a user with pagination."""
        if limit > 100:
            raise ValidationError("Limite máximo de 100 projetos por requisição")
        
        return await self.projeto_repository.get_multi(
            skip=skip, 
            limit=limit, 
            owner_id=user_id
        )
    
    async def create_projeto(self, projeto_in: ProjetoCreate, user_id: UUID) -> Projeto:
        """Create a new projeto with business validation."""
        # Business validation
        await self._validate_projeto_data(projeto_in)
        
        # Ensure owner_id matches authenticated user
        projeto_in.owner_id = user_id
        
        # Check for duplicate NS (if needed)
        existing = await self._check_duplicate_ns(projeto_in.ns, user_id)
        if existing:
            raise ValidationError(f"Projeto com NS '{projeto_in.ns}' já existe")
        
        return await self.projeto_repository.create(projeto_in)
    
    async def update_projeto(
        self, 
        projeto_id: UUID, 
        projeto_update: ProjetoUpdate, 
        user_id: UUID
    ) -> Projeto:
        """Update a projeto with permission and business validation."""
        # Get existing projeto
        projeto = await self.get_projeto(projeto_id, user_id)
        
        # Business validation for updates
        if projeto_update.ns and projeto_update.ns != projeto.ns:
            existing = await self._check_duplicate_ns(projeto_update.ns, user_id)
            if existing:
                raise ValidationError(f"Projeto com NS '{projeto_update.ns}' já existe")
        
        return await self.projeto_repository.update(projeto, projeto_update)
    
    async def delete_projeto(self, projeto_id: UUID, user_id: UUID) -> Projeto:
        """Soft delete a projeto with permission check."""
        # Get projeto to ensure it exists and user has permission
        projeto = await self.get_projeto(projeto_id, user_id)
        
        # Check if projeto has associated pontos
        projeto_with_pontos = await self.projeto_repository.get_with_pontos_count(projeto_id)
        if projeto_with_pontos and projeto_with_pontos["total_pontos"] > 0:
            raise ValidationError("Não é possível excluir projeto com pontos associados")
        
        return await self.projeto_repository.delete(projeto_id)
    
    async def count_projetos(self, user_id: UUID) -> int:
        """Count projetos for a user."""
        return await self.projeto_repository.count(owner_id=user_id)
    
    async def user_can_access_projeto(self, projeto_id: UUID, user_id: UUID) -> bool:
        """Check if user can access a projeto."""
        return await self.projeto_repository.user_can_access_projeto(projeto_id, user_id)
    
    async def get_projeto_stats(self, user_id: UUID) -> dict:
        """Get statistics for user's projetos."""
        total_projetos = await self.count_projetos(user_id)
        
        # Get projetos with pontos count
        projetos = await self.get_projetos(user_id, limit=1000)
        
        total_pontos = sum(p.total_pontos for p in projetos)
        
        # Calculate projetos by month (last 6 months)
        projetos_by_month = {}
        for projeto in projetos:
            month_key = projeto.created_at.strftime("%Y-%m")
            projetos_by_month[month_key] = projetos_by_month.get(month_key, 0) + 1
        
        return {
            "total_projetos": total_projetos,
            "total_pontos": total_pontos,
            "projetos_by_month": projetos_by_month,
            "average_pontos_per_projeto": total_pontos / total_projetos if total_projetos > 0 else 0
        }
    
    async def _validate_projeto_data(self, projeto_in: ProjetoCreate) -> None:
        """Validate projeto business rules."""
        # Validate NS format (if specific format required)
        if not projeto_in.ns.replace("-", "").replace("/", "").isalnum():
            raise ValidationError("NS deve conter apenas letras, números, '-' e '/'")
        
        # Validate matricula format (if specific format required)
        if len(projeto_in.matricula) < 4:
            raise ValidationError("Matrícula deve ter pelo menos 4 caracteres")
        
        # Validate study date is not in future
        if projeto_in.data_estudo and projeto_in.data_estudo > datetime.utcnow():
            raise ValidationError("Data de estudo não pode estar no futuro")
    
    async def _check_duplicate_ns(self, ns: str, user_id: UUID) -> bool:
        """Check if NS already exists for user."""
        projetos = await self.projeto_repository.get_multi(
            limit=1000, 
            owner_id=user_id
        )
        
        return any(p.ns == ns for p in projetos)
