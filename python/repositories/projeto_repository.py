"""Repository for projeto data access operations."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from repositories.base import BaseRepository
from models.projeto import Projeto, ProjetoCreate, ProjetoUpdate


class ProjetoRepository(BaseRepository[Projeto, ProjetoCreate, ProjetoUpdate]):
    """Repository for projeto operations."""
    
    def __init__(self, db_client):
        super().__init__(Projeto)
        self.db = db_client
    
    async def get(self, id: UUID) -> Optional[Projeto]:
        """Get a projeto by ID."""
        try:
            result = await self.db.fetch_one(
                "SELECT * FROM projetos WHERE id = $1 AND deleted_at IS NULL",
                str(id)
            )
            return Projeto(**result) if result else None
        except Exception as e:
            raise RuntimeError(f"Error fetching projeto {id}: {e}")
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        owner_id: Optional[UUID] = None
    ) -> List[Projeto]:
        """Get multiple projetos with pagination."""
        try:
            query = """
                SELECT p.*, COUNT(pt.id) as total_pontos
                FROM projetos p
                LEFT JOIN pontos pt ON p.id = pt.projeto_id
                WHERE p.deleted_at IS NULL
            """
            params = []
            
            if owner_id:
                query += " AND p.owner_id = $%d"
                params.append(str(owner_id))
            
            query += " GROUP BY p.id ORDER BY p.created_at DESC LIMIT $%d OFFSET $%d"
            params.extend([limit, skip])
            
            # Format query with proper parameter indices
            formatted_query = query % tuple(range(1, len(params) + 1))
            
            results = await self.db.fetch_all(formatted_query, *params)
            return [Projeto(**result) for result in results]
        except Exception as e:
            raise RuntimeError(f"Error fetching projetos: {e}")
    
    async def create(self, obj_in: ProjetoCreate) -> Projeto:
        """Create a new projeto."""
        try:
            projeto_id = uuid4()
            
            result = await self.db.fetch_one(
                """
                INSERT INTO projetos (id, orgao, ns, nome, endereco, estudado_por, 
                                   matricula, data_estudo, owner_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
                RETURNING *
                """,
                str(projeto_id),
                obj_in.orgao,
                obj_in.ns,
                obj_in.nome,
                obj_in.endereco,
                obj_in.estudado_por,
                obj_in.matricula,
                obj_in.data_estudo,
                str(obj_in.owner_id)
            )
            
            return Projeto(**result)
        except Exception as e:
            raise RuntimeError(f"Error creating projeto: {e}")
    
    async def update(
        self, 
        db_obj: Projeto, 
        obj_in: ProjetoUpdate
    ) -> Projeto:
        """Update an existing projeto."""
        try:
            update_data = obj_in.dict(exclude_unset=True)
            if not update_data:
                return db_obj
            
            # Build dynamic update query
            set_clauses = []
            params = [str(db_obj.id)]
            
            for i, (field, value) in enumerate(update_data.items(), 2):
                set_clauses.append(f"{field} = ${i}")
                params.append(value)
            
            set_clauses.append("updated_at = NOW()")
            params.append(str(db_obj.id))
            
            query = f"""
                UPDATE projetos 
                SET {', '.join(set_clauses)}
                WHERE id = $1 AND deleted_at IS NULL
                RETURNING *
            """
            
            result = await self.db.fetch_one(query, *params)
            return Projeto(**result) if result else db_obj
        except Exception as e:
            raise RuntimeError(f"Error updating projeto {db_obj.id}: {e}")
    
    async def delete(self, id: UUID) -> Optional[Projeto]:
        """Soft delete a projeto."""
        try:
            result = await self.db.fetch_one(
                "UPDATE projetos SET deleted_at = NOW() WHERE id = $1 AND deleted_at IS NULL RETURNING *",
                str(id)
            )
            return Projeto(**result) if result else None
        except Exception as e:
            raise RuntimeError(f"Error deleting projeto {id}: {e}")
    
    async def count(self, owner_id: Optional[UUID] = None) -> int:
        """Count projetos with optional owner filter."""
        try:
            query = "SELECT COUNT(*) as count FROM projetos WHERE deleted_at IS NULL"
            params = []
            
            if owner_id:
                query += " AND owner_id = $1"
                params.append(str(owner_id))
            
            result = await self.db.fetch_one(query, *params)
            return result["count"]
        except Exception as e:
            raise RuntimeError(f"Error counting projetos: {e}")
    
    async def get_by_owner(self, owner_id: UUID) -> List[Projeto]:
        """Get all projetos for a specific owner."""
        return await self.get_multi(owner_id=owner_id)
    
    async def user_can_access_projeto(self, projeto_id: UUID, user_id: UUID) -> bool:
        """Check if user can access a projeto."""
        try:
            result = await self.db.fetch_one(
                "SELECT id FROM projetos WHERE id = $1 AND owner_id = $2 AND deleted_at IS NULL",
                str(projeto_id),
                str(user_id)
            )
            return result is not None
        except Exception as e:
            raise RuntimeError(f"Error checking projeto access: {e}")
    
    async def get_with_pontos_count(self, projeto_id: UUID) -> Optional[Dict[str, Any]]:
        """Get projeto with pontos count."""
        try:
            result = await self.db.fetch_one(
                """
                SELECT p.*, COUNT(pt.id) as total_pontos
                FROM projetos p
                LEFT JOIN pontos pt ON p.id = pt.projeto_id
                WHERE p.id = $1 AND p.deleted_at IS NULL
                GROUP BY p.id
                """,
                str(projeto_id)
            )
            return result
        except Exception as e:
            raise RuntimeError(f"Error fetching projeto with pontos: {e}")
