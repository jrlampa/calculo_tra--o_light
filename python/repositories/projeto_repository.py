"""Repository for projeto data access operations."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import json
import logging

logger = logging.getLogger(__name__)

from repositories.base import BaseRepository
from models.projeto import Projeto, ProjetoCreate, ProjetoUpdate


class ProjetoRepository(BaseRepository[Projeto, ProjetoCreate, ProjetoUpdate]):
    """Repository for projeto operations."""

    def __init__(self, db_client):
        super().__init__(Projeto)
        self.db = db_client
        self._column_contract: Optional[Dict[str, Optional[str]]] = None

    async def _get_column_contract(self) -> Dict[str, Optional[str]]:
        """Detect supported timestamp/soft-delete columns for projetos."""
        if self._column_contract is not None:
            return self._column_contract

        expected_columns = {
            "created_at",
            "updated_at",
            "deleted_at",
            "criado_em",
            "atualizado_em",
            "deletado_em",
        }

        found_columns: set[str] = set()
        try:
            rows = await self.db.fetch_all(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'projetos'
                """
            )
            found_columns = {
                str(dict(row).get("column_name") if not isinstance(row, dict) else row.get("column_name"))
                for row in rows
            }
        except Exception:
            # Keep safe defaults when schema introspection is unavailable.
            # Including both English (Alembic default) and Portuguese (IM3 standard) mappings.
            found_columns = {
                "created_at", "updated_at", "deleted_at",
                "criado_em", "atualizado_em", "deletado_em"
            }

        available = expected_columns.intersection(found_columns)
        # Priority: Portuguese (IM3 standard) then English (Alembic default)
        created_col = "criado_em" if "criado_em" in available else ("created_at" if "created_at" in available else None)
        updated_col = "atualizado_em" if "atualizado_em" in available else ("updated_at" if "updated_at" in available else None)

        deleted_col: Optional[str] = None
        if "deletado_em" in available:
            deleted_col = "deletado_em"
        elif "deleted_at" in available:
            deleted_col = "deleted_at"

        self._column_contract = {
            "created": created_col,
            "updated": updated_col,
            "deleted": deleted_col,
            "order": updated_col or created_col or "id",
        }
        return self._column_contract

    @staticmethod
    def _active_filter(deleted_column: Optional[str], alias: str = "") -> str:
        if not deleted_column:
            return ""
        prefix = f"{alias}." if alias else ""
        return f" AND {prefix}{deleted_column} IS NULL"

    @staticmethod
    def _to_dict(record: Any) -> Dict[str, Any]:
        raw = record if isinstance(record, dict) else dict(record)
        normalized: Dict[str, Any] = {}
        for key, value in raw.items():
            normalized[key] = str(value) if isinstance(value, UUID) else value
        return normalized

    async def _log_activity(
        self,
        activity_type: str,
        user_id: Optional[UUID] = None,
        projeto_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Helper to log backend activities (Audit Trail)."""
        try:
            query = """
                INSERT INTO activity_logs (id, projeto_id, user_id, activity_type, details, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
            """
            await self.db.execute(
                query,
                str(uuid4()),
                str(projeto_id) if projeto_id else None,
                str(user_id) if user_id else None,
                activity_type,
                json.dumps(details) if details else None
            )
        except Exception as e:
            # Audit logging should not break the main transaction, but we log it.
            import logging
            logging.getLogger(__name__).error(f"Failed to log activity {activity_type}: {e}")

    async def get(self, id: UUID) -> Optional[Projeto]:
        """Get a projeto by ID."""
        try:
            contract = await self._get_column_contract()
            deleted_filter = self._active_filter(contract["deleted"])
            result = await self.db.fetch_one(
                f"SELECT * FROM projetos WHERE id = $1{deleted_filter}",  # nosec B608
                str(id)
            )
            return Projeto(**self._to_dict(result)) if result else None
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
            contract = await self._get_column_contract()
            deleted_filter = self._active_filter(contract["deleted"], alias="p")
            query = """
                SELECT p.*, COUNT(pt.id) as total_pontos
                FROM projetos p
                LEFT JOIN pontos pt ON p.id = pt.projeto_id
                WHERE 1=1
            """
            query += deleted_filter  # nosec B608
            params = []

            if owner_id:
                query += " AND p.owner_id = $%d"
                params.append(str(owner_id))

            query += f" GROUP BY p.id ORDER BY p.{contract['order']} DESC LIMIT $%d OFFSET $%d"
            params.extend([limit, skip])

            # Format query with proper parameter indices
            formatted_query = query % tuple(range(1, len(params) + 1))

            results = await self.db.fetch_all(formatted_query, *params)
            return [Projeto(**self._to_dict(result)) for result in results]
        except Exception as e:
            raise RuntimeError(f"Error fetching projetos: {e}")

    async def create(self, obj_in: ProjetoCreate) -> Projeto:
        """Create a new projeto."""
        try:
            contract = await self._get_column_contract()
            projeto_id = uuid4()

            # Ensure all required fields are present and valid
            if not obj_in.orgao or not obj_in.ns or not obj_in.nome or not obj_in.estudado_por or not obj_in.matricula:
                raise ValueError("Campos obrigatórios ausentes: orgao, ns, nome, estudado_por, matricula")

            if not obj_in.data_estudo:
                raise ValueError("Campo data_estudo é obrigatório")

            columns = [
                "id",
                "orgao",
                "ns",
                "nome",
                "endereco",
                "estudado_por",
                "matricula",
                "data_estudo",
                "owner_id",
            ]
            values_expr = ["$1", "$2", "$3", "$4", "$5", "$6", "$7", "$8", "$9"]

            if contract["created"]:
                columns.append(contract["created"])
                values_expr.append("NOW()")
            if contract["updated"]:
                columns.append(contract["updated"])
                values_expr.append("NOW()")

            query = f"""
                INSERT INTO projetos ({', '.join(columns)})
                VALUES ({', '.join(values_expr)})
                RETURNING *
            """

            result = await self.db.fetch_one(
                query,
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

            if not result:
                raise RuntimeError("Projeto não foi criado no banco de dados")

            projeto = Projeto(**self._to_dict(result))

            # Audit Trail
            await self._log_activity(
                activity_type="PROJECT_CREATE",
                user_id=obj_in.owner_id,
                projeto_id=projeto.id,
                details={"nome": projeto.nome, "ns": projeto.ns}
            )

            return projeto
        except Exception as e:
            raise RuntimeError(f"Error creating projeto: {e}")


    async def update(
        self,
        db_obj: Projeto,
        obj_in: ProjetoUpdate
    ) -> Projeto:
        """Update an existing projeto."""
        try:
            contract = await self._get_column_contract()
            update_data = obj_in.dict(exclude_unset=True)
            if not update_data:
                return db_obj

            # Build dynamic update query
            set_clauses = []
            params = [str(db_obj.id)]

            for i, (field, value) in enumerate(update_data.items(), 2):
                set_clauses.append(f"{field} = ${i}")
                params.append(value)

            if contract["updated"]:
                set_clauses.append(f"{contract['updated']} = NOW()")
            params.append(str(db_obj.id))

            deleted_filter = self._active_filter(contract["deleted"])

            query = f"""
                UPDATE projetos
                SET {', '.join(set_clauses)}
                WHERE id = $1{deleted_filter}
                RETURNING *
            """  # nosec B608

            result = await self.db.fetch_one(query, *params)
            projeto = Projeto(**self._to_dict(result)) if result else db_obj

            # Audit Trail
            if result:
                await self._log_activity(
                    activity_type="PROJECT_UPDATE",
                    user_id=db_obj.owner_id,
                    projeto_id=projeto.id,
                    details={"fields_updated": list(update_data.keys())}
                )

            return projeto
        except Exception as e:
            raise RuntimeError(f"Error updating projeto {db_obj.id}: {e}")

    async def delete(self, id: UUID) -> Optional[Projeto]:
        """Soft delete a projeto."""
        try:
            contract = await self._get_column_contract()
            if not contract["deleted"]:
                raise RuntimeError("Soft delete column not found on public.projetos")

            result = await self.db.fetch_one(
                f"UPDATE projetos SET {contract['deleted']} = NOW() "
                f"WHERE id = $1 AND {contract['deleted']} IS NULL RETURNING *",
                str(id)
            )
            return Projeto(**self._to_dict(result)) if result else None
        except Exception as e:
            raise RuntimeError(f"Error deleting projeto {id}: {e}")

    async def count(self, owner_id: Optional[UUID] = None) -> int:
        """Count projetos with optional owner filter."""
        try:
            contract = await self._get_column_contract()
            query = "SELECT COUNT(*) as count FROM projetos WHERE 1=1"
            query += self._active_filter(contract["deleted"])  # nosec B608
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
            contract = await self._get_column_contract()
            deleted_filter = self._active_filter(contract["deleted"])
            result = await self.db.fetch_one(
                f"SELECT id FROM projetos WHERE id = $1 AND owner_id = $2{deleted_filter}",  # nosec B608
                str(projeto_id),
                str(user_id)
            )
            return result is not None
        except Exception as e:
            raise RuntimeError(f"Error checking projeto access: {e}")

    async def get_with_pontos_count(self, projeto_id: UUID) -> Optional[Dict[str, Any]]:
        """Get projeto with pontos count."""
        try:
            contract = await self._get_column_contract()
            deleted_filter = self._active_filter(contract["deleted"], alias="p")
            result = await self.db.fetch_one(
                """
                SELECT p.*, COUNT(pt.id) as total_pontos
                FROM projetos p
                LEFT JOIN pontos pt ON p.id = pt.projeto_id
                WHERE p.id = $1
                GROUP BY p.id
                """ + deleted_filter,  # nosec B608
                str(projeto_id)
            )
            return self._to_dict(result) if result else None
        except Exception as e:
            raise RuntimeError(f"Error fetching projeto with pontos: {e}")

    # Métodos auxiliares para testes de hierarquia
    async def _get_ponto(self, ponto_id: str) -> Optional[Dict[str, Any]]:
        """Get ponto by ID (for testing)."""
        try:
            result = await self.db.fetch_one(
                "SELECT * FROM pontos WHERE id = $1",
                ponto_id
            )
            return self._to_dict(result) if result else None
        except Exception as e:
            raise RuntimeError(f"Error fetching ponto {ponto_id}: {e}")

    async def _get_niveis_calculo(self, ponto_id: str) -> List[Dict[str, Any]]:
        """Get all niveis for a ponto (for testing)."""
        try:
            result = await self.db.fetch_all(
                "SELECT * FROM niveis_calculo WHERE ponto_id = $1 ORDER BY nivel",
                ponto_id
            )
            return [self._to_dict(row) for row in result]
        except Exception as e:
            raise RuntimeError(f"Error fetching niveis for ponto {ponto_id}: {e}")

    async def _get_travessias(self, nivel_id: str) -> List[Dict[str, Any]]:
        """Get all travessias for a nivel (for testing)."""
        try:
            result = await self.db.fetch_all(
                "SELECT * FROM travessias WHERE nivel_id = $1 ORDER BY posicao",
                nivel_id
            )
            return [self._to_dict(row) for row in result]
        except Exception as e:
            raise RuntimeError(f"Error fetching travessias for nivel {nivel_id}: {e}")

    async def _get_resultado_calculo(self, ponto_id: str) -> Optional[Dict[str, Any]]:
        """Get resultado for a ponto (for testing)."""
        try:
            result = await self.db.fetch_one(
                "SELECT * FROM resultados_calculo WHERE ponto_id = $1",
                ponto_id
            )
            return self._to_dict(result) if result else None
        except Exception as e:
            raise RuntimeError(f"Error fetching resultado for ponto {ponto_id}: {e}")

    async def save_ponto(
        self,
        projeto_id: str,
        ponto: str,
        tipo_poste: str,
        modelo_poste: str,
    ) -> Optional[str]:
        """Persist a ponto delegating to the underlying DB client."""
        saver = getattr(self.db, "save_ponto", None)
        if saver is None:
            raise RuntimeError("DB client does not implement save_ponto")

        ponto_id = await saver(projeto_id, ponto, tipo_poste, modelo_poste)
        if ponto_id:
            return ponto_id

        # Keep tests and retries idempotent: when (projeto_id, ponto) already exists,
        # return the existing point id instead of propagating duplicate-insert behavior.
        existing = await self.db.fetch_one(
            "SELECT id::text AS id FROM pontos WHERE projeto_id = $1::uuid AND ponto = $2 LIMIT 1",
            projeto_id,
            ponto,
        )
        if existing:
            existing_dict = self._to_dict(existing)
            return existing_dict.get("id")
        return None

    async def save_calculo_snapshot(
        self,
        ponto_id: str,
        niveis: List[Dict[str, Any]] | Any,
        resultado: Dict[str, Any],
    ) -> bool:
        """Persist full snapshot (niveis/travessias/resultado) for a ponto."""
        saver = getattr(self.db, "save_calculo_snapshot", None)
        if saver is None:
            raise RuntimeError("DB client does not implement save_calculo_snapshot")
        normalized_niveis = self._normalize_niveis_payload(niveis)
        return await saver(ponto_id, normalized_niveis, resultado)

    @staticmethod
    def _normalize_niveis_payload(niveis: Any) -> List[Dict[str, Any]]:
        """Accept legacy CalculoInput payloads and normalize to niveis list."""
        if isinstance(niveis, list):
            return niveis

        if hasattr(niveis, "model_dump"):
            raw_payload = niveis.model_dump()
        elif hasattr(niveis, "dict"):
            raw_payload = niveis.dict()
        elif isinstance(niveis, dict):
            raw_payload = niveis
        else:
            return []

        if not isinstance(raw_payload, dict):
            return []

        level_map = [
            ("MT1", "mt1"),
            ("MT2", "mt2"),
            ("BT", "bt"),
            ("BTZ", "btz"),
            ("RAL", "ral"),
        ]

        normalized: List[Dict[str, Any]] = []
        for nivel_label, key in level_map:
            travessias_raw = raw_payload.get(key, [])
            travessias: List[Dict[str, Any]] = []
            for idx, item in enumerate(travessias_raw, start=1):
                if hasattr(item, "model_dump"):
                    trav = item.model_dump()
                elif hasattr(item, "dict"):
                    trav = item.dict()
                elif isinstance(item, dict):
                    trav = item
                else:
                    continue

                trav = dict(trav)
                trav.setdefault("posicao", idx)
                travessias.append(trav)

            altura_poste = travessias[0].get("altura_poste", 0.0) if travessias else 0.0
            altura_ancoragem = travessias[0].get("altura_ancoragem", 0.0) if travessias else 0.0
            normalized.append(
                {
                    "nivel": nivel_label,
                    "altura_poste": altura_poste,
                    "altura_ancoragem": altura_ancoragem,
                    "travessias": travessias,
                }
            )

        return normalized
