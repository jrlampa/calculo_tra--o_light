"""Supabase PostgreSQL client for calculo_tração_light."""
import os
import asyncpg
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class SupabaseClient:
    """Async PostgreSQL client for direct database access."""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "")
        self.enabled = bool(self.database_url)
        self._pool: Optional[asyncpg.pool.Pool] = None

    @property
    def is_enabled(self) -> bool:
        """Check if Supabase is configured."""
        return self.enabled

    async def _get_pool(self) -> Optional[asyncpg.pool.Pool]:
        """Get or create connection pool."""
        if not self.enabled:
            return None
        
        try:
            if self._pool is None:
                self._pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=5,
                    max_size=20,
                    max_queries=50000,
                    max_inactive_connection_lifetime=300.0,
                    command_timeout=60,
                )
            return self._pool
        except Exception as e:
            print(f"⚠️ Error creating connection pool: {e}")
            return None

    async def close(self):
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def fetch_cabos(self) -> List[Dict[str, Any]]:
        """Fetch all cables from database."""
        if not self.enabled:
            return []
        
        try:
            pool = await self._get_pool()
            if not pool:
                return []
            
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT id, nome, diametro, peso FROM cabos ORDER BY nome")
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"⚠️ Error fetching cabos: {e}")
            return []

    async def fetch_postes(self) -> List[Dict[str, Any]]:
        """Fetch all poles from database."""
        if not self.enabled:
            return []
        
        try:
            pool = await self._get_pool()
            if not pool:
                return []
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT id, tipo, modelo, altura_m, carga_admissivel_dan FROM postes ORDER BY tipo, modelo"
                )
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"⚠️ Error fetching postes: {e}")
            return []

    async def fetch_redes(self) -> List[Dict[str, Any]]:
        """Fetch all network types from database."""
        if not self.enabled:
            return []
        
        try:
            pool = await self._get_pool()
            if not pool:
                return []
            
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT id, tipo, descricao FROM redes ORDER BY tipo")
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"⚠️ Error fetching redes: {e}")
            return []

    async def fetch_normas(self) -> List[Dict[str, Any]]:
        """Fetch all rules and standards from database."""
        if not self.enabled:
            return []
        
        try:
            pool = await self._get_pool()
            if not pool:
                return []
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT id, categoria, arquivo_origem, titulo, descricao, regra_tecnica, aplicavel_a, fonte_referencia FROM normas_regras ORDER BY categoria, titulo"
                )
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"⚠️ Error fetching normas: {e}")
            return []

    async def fetch_normas_by_categoria(self, categoria: str) -> List[Dict[str, Any]]:
        """Fetch rules by category."""
        if not self.enabled:
            return []
        
        try:
            pool = await self._get_pool()
            if not pool:
                return []
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT id, categoria, arquivo_origem, titulo, descricao, regra_tecnica, aplicavel_a, fonte_referencia FROM normas_regras WHERE categoria = $1 ORDER BY titulo",
                    categoria
                )
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"⚠️ Error fetching normas by categoria: {e}")
            return []

    async def fetch_normas_categorias(self) -> Dict[str, Any]:
        """Fetch available categories and counts."""
        if not self.enabled:
            return {}
        
        try:
            pool = await self._get_pool()
            if not pool:
                return {}
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT categoria, COUNT(*) as count FROM normas_regras GROUP BY categoria ORDER BY categoria"
                )
                categorias = {row['categoria']: row['count'] for row in rows}
                return {"categorias": categorias}
        except Exception as e:
            print(f"⚠️ Error fetching categorias: {e}")
            return {}

    async def insert_cabo(self, nome: str, diametro: float, peso: float) -> Dict[str, Any]:
        """Insert new cable into database."""
        if not self.enabled:
            return {}
        
        try:
            pool = await self._get_pool()
            if not pool:
                return {}
            
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "INSERT INTO cabos (nome, diametro, peso) VALUES ($1, $2, $3) RETURNING id, nome, diametro, peso",
                    nome, diametro, peso
                )
                return dict(row) if row else {}
        except Exception as e:
            print(f"⚠️ Error inserting cabo: {e}")
            return {}

    async def delete_cabo(self, id: int) -> bool:
        """Delete cable from database."""
        if not self.enabled:
            return False
        
        try:
            pool = await self._get_pool()
            if not pool:
                return False
            
            async with pool.acquire() as conn:
                result = await conn.execute("DELETE FROM cabos WHERE id = $1", id)
                return result == "DELETE 1"
        except Exception as e:
            print(f"⚠️ Error deleting cabo: {e}")
            return False

    async def insert_poste(
        self, tipo: str, modelo: str, altura_m: float, carga_admissivel_dan: float
    ) -> Dict[str, Any]:
        """Insert new pole into database."""
        if not self.enabled:
            return {}
        
        try:
            pool = await self._get_pool()
            if not pool:
                return {}
            
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "INSERT INTO postes (tipo, modelo, altura_m, carga_admissivel_dan) VALUES ($1, $2, $3, $4) RETURNING id, tipo, modelo, altura_m, carga_admissivel_dan",
                    tipo, modelo, altura_m, carga_admissivel_dan
                )
                return dict(row) if row else {}
        except Exception as e:
            print(f"⚠️ Error inserting poste: {e}")
            return {}

    async def delete_poste(self, id: int) -> bool:
        """Delete pole from database."""
        if not self.enabled:
            return False
        
        try:
            pool = await self._get_pool()
            if not pool:
                return False
            
            async with pool.acquire() as conn:
                result = await conn.execute("DELETE FROM postes WHERE id = $1", id)
                return result == "DELETE 1"
        except Exception as e:
            print(f"⚠️ Error deleting poste: {e}")
            return False

    async def insert_norma(
        self,
        categoria: str,
        arquivo_origem: str,
        titulo: str,
        descricao: Optional[str] = None,
        regra_tecnica: Optional[str] = None,
        aplicavel_a: Optional[str] = None,
        fonte_referencia: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Insert new norm/rule into database."""
        if not self.enabled:
            return {}
        
        try:
            pool = await self._get_pool()
            if not pool:
                return {}
            
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """INSERT INTO normas_regras 
                    (categoria, arquivo_origem, titulo, descricao, regra_tecnica, aplicavel_a, fonte_referencia) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7) 
                    RETURNING id, categoria, arquivo_origem, titulo, descricao, regra_tecnica, aplicavel_a, fonte_referencia""",
                    categoria, arquivo_origem, titulo, descricao, regra_tecnica, aplicavel_a, fonte_referencia
                )
                return dict(row) if row else {}
        except Exception as e:
            print(f"⚠️ Error inserting norma: {e}")
            return {}

    async def delete_norma(self, id: int) -> bool:
        """Delete norm/rule from database."""
        if not self.enabled:
            return False
        
        try:
            pool = await self._get_pool()
            if not pool:
                return False
            
            async with pool.acquire() as conn:
                result = await conn.execute("DELETE FROM normas_regras WHERE id = $1", id)
                return result == "DELETE 1"
        except Exception as e:
            print(f"⚠️ Error deleting norma: {e}")
            return False


_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get or create singleton Supabase client."""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client
