"""Service layer for projeto business logic."""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import UTC, datetime

from models.projeto import Projeto, ProjetoCreate, ProjetoUpdate
from repositories.projeto_repository import ProjetoRepository
from core.exceptions import NotFoundError, PermissionError, ValidationError


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
        if limit > 1000:
            raise ValidationError("Limite máximo de 1000 projetos por requisição")
        
        return await self.projeto_repository.get_multi(
            skip=skip, 
            limit=limit, 
            owner_id=user_id
        )
    
    async def create_projeto(self, projeto_in: ProjetoCreate, user_id: UUID) -> Projeto:
        """Create a new projeto with business validation."""
        # Business validation
        await self._validate_projeto_data(projeto_in)
        
        # Ensure owner_id matches authenticated user without mutating input model.
        projeto_payload = projeto_in.model_copy(update={"owner_id": user_id})
        
        # Check for duplicate NS (if needed)
        existing = await self._check_duplicate_ns(projeto_payload.ns, user_id)
        if existing:
            raise ValidationError(f"Projeto com NS '{projeto_payload.ns}' já existe")
        
        return await self.projeto_repository.create(projeto_payload)
    
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
        # Validate NS format: allow letters, digits, '-', '/', and empty/default
        ns_clean = projeto_in.ns.replace("-", "").replace("/", "").strip()
        if ns_clean and not ns_clean.isalnum():
            raise ValidationError("NS deve conter apenas letras, números, '-' e '/'")

        # Validate matricula: minimum 1 character (relaxed for guest mode defaults)
        if len(projeto_in.matricula) < 1:
            raise ValidationError("Erro de validação: Matrícula não pode ser vazia")

        # Validate study date is not in future - this is now handled by Pydantic validator
        # but we keep this for additional safety and custom error messages
        if projeto_in.data_estudo:
            try:
                # Handle string format (consistent with Pydantic model change)
                dt = datetime.strptime(projeto_in.data_estudo, "%d/%m/%Y")
                if dt.date() > datetime.now(UTC).date():
                    raise ValidationError("Data de estudo não pode estar no futuro")
            except (ValueError, TypeError):
                raise ValidationError("Formato de data inválido. Use DD/MM/AAAA")

    
    async def _check_duplicate_ns(self, ns: str, user_id: UUID) -> bool:
        """Check if NS already exists for user."""
        projetos = await self.projeto_repository.get_multi(
            limit=1000, 
            owner_id=user_id
        )
        
        return any(p.ns == ns for p in projetos)
