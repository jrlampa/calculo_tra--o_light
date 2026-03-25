"""Supabase PostgreSQL client for calculo_tração_light."""
import asyncio
import os
import asyncpg
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


def _nullable_scalar(record: Dict[str, Any], key: str) -> Any:
    """Preserve numeric zero when persisting optional scalar fields."""
    value = record.get(key)
    if value == "":
        return None
    return value


class SupabaseClient:
    """Async PostgreSQL client for direct database access."""

    SNAPSHOT_RETRY_MAX_RETRIES_DEFAULT = 3
    SNAPSHOT_RETRY_BACKOFF_BASE_SECONDS_DEFAULT = 0.2
    SNAPSHOT_RETRY_BACKOFF_CAP_SECONDS_DEFAULT = 2.0

    _SNAPSHOT_NON_RETRYABLE_SQLSTATES = {"42501"}
    _SNAPSHOT_NON_RETRYABLE_MESSAGE_MARKERS = (
        "row-level security",
        "permission denied",
        "insufficient privilege",
    )
    _SNAPSHOT_RETRYABLE_SQLSTATES = {
        "40001",  # serialization_failure
        "40P01",  # deadlock_detected
        "55P03",  # lock_not_available
        "53300",  # too_many_connections
        "57P03",  # cannot_connect_now
    }
    _SNAPSHOT_RETRYABLE_MESSAGE_MARKERS = (
        "could not serialize access",
        "deadlock detected",
        "lock not available",
        "connection reset",
        "connection refused",
        "connection timed out",
        "connection pool unavailable",
        "timeout",
        "temporarily unavailable",
        "could not connect",
        "too many connections",
    )

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "")
        self.enabled = bool(self.database_url)
        self._pool: Optional[asyncpg.pool.Pool] = None
        self.snapshot_retry_max_retries = self._read_int_env(
            "SNAPSHOT_RETRY_MAX_RETRIES",
            self.SNAPSHOT_RETRY_MAX_RETRIES_DEFAULT,
            minimum=0,
        )
        self.snapshot_retry_backoff_base_seconds = self._read_float_env(
            "SNAPSHOT_RETRY_BACKOFF_BASE_SECONDS",
            self.SNAPSHOT_RETRY_BACKOFF_BASE_SECONDS_DEFAULT,
            minimum=0.0,
        )
        self.snapshot_retry_backoff_cap_seconds = self._read_float_env(
            "SNAPSHOT_RETRY_BACKOFF_CAP_SECONDS",
            self.SNAPSHOT_RETRY_BACKOFF_CAP_SECONDS_DEFAULT,
            minimum=0.0,
        )

    @staticmethod
    def _read_int_env(name: str, default: int, minimum: int = 0) -> int:
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            return max(minimum, int(raw))
        except ValueError:
            return default

    @staticmethod
    def _read_float_env(name: str, default: float, minimum: float = 0.0) -> float:
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            return max(minimum, float(raw))
        except ValueError:
            return default

    @staticmethod
    def _error_sqlstate(error: Exception) -> str:
        sqlstate = getattr(error, "sqlstate", None) or getattr(error, "pgcode", None)
        if sqlstate is None:
            return ""
        return str(sqlstate).upper()

    @classmethod
    def _is_snapshot_non_retryable_error(cls, error: Exception) -> bool:
        sqlstate = cls._error_sqlstate(error)
        if sqlstate in cls._SNAPSHOT_NON_RETRYABLE_SQLSTATES:
            return True
        message = str(error).lower()
        return any(marker in message for marker in cls._SNAPSHOT_NON_RETRYABLE_MESSAGE_MARKERS)

    @classmethod
    def _is_snapshot_retryable_error(cls, error: Exception) -> bool:
        if cls._is_snapshot_non_retryable_error(error):
            return False

        sqlstate = cls._error_sqlstate(error)
        if sqlstate.startswith("08"):
            return True
        if sqlstate in cls._SNAPSHOT_RETRYABLE_SQLSTATES:
            return True

        message = str(error).lower()
        return any(marker in message for marker in cls._SNAPSHOT_RETRYABLE_MESSAGE_MARKERS)

    def _snapshot_retry_backoff_seconds(self, retry_attempt: int) -> float:
        if retry_attempt <= 0:
            return 0.0

        delay = self.snapshot_retry_backoff_base_seconds * (2 ** (retry_attempt - 1))
        return min(delay, self.snapshot_retry_backoff_cap_seconds)

    async def _sleep_before_snapshot_retry(self, delay_seconds: float) -> None:
        if delay_seconds <= 0:
            return
        await asyncio.sleep(delay_seconds)

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
            print(f"[WARN] Error creating connection pool: {e}")
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
            print(f"[WARN] Error fetching cabos: {e}")
            raise

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
            print(f"[WARN] Error fetching postes: {e}")
            raise

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
            print(f"[WARN] Error fetching redes: {e}")
            raise

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
            print(f"[WARN] Error fetching normas: {e}")
            raise

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
            print(f"[WARN] Error fetching normas by categoria: {e}")
            raise

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
            print(f"[WARN] Error fetching categorias: {e}")
            raise

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
            print(f"[WARN] Error inserting cabo: {e}")
            raise

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
            print(f"[WARN] Error deleting cabo: {e}")
            raise

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
            print(f"[WARN] Error inserting poste: {e}")
            raise

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
            print(f"[WARN] Error deleting poste: {e}")
            raise

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
            print(f"[WARN] Error inserting norma: {e}")
            raise

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
            print(f"[WARN] Error deleting norma: {e}")
            raise


    # ── Transactional methods (projetos / pontos / calculo) ───────────────

    async def list_projetos(
        self,
        limit: int = 20,
        offset: int = 0,
        owner_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List projects ordered by most recently updated.

        owner_id: when informed, only return projects owned by that user.
        """
        if not self.enabled:
            return []
        try:
            pool = await self._get_pool()
            if not pool:
                return []

            bounded_limit = max(1, min(limit, 100))
            bounded_offset = max(0, min(offset, 10000))

            async with pool.acquire() as conn:
                if owner_id:
                    rows = await conn.fetch(
                        """
                        SELECT p.id::text AS id,
                               p.orgao,
                               p.ns,
                               p.nome,
                               p.endereco,
                               p.estudado_por,
                               p.matricula,
                               p.data_estudo,
                               p.atualizado_em,
                               COUNT(pt.id)::int AS total_pontos
                        FROM projetos p
                        LEFT JOIN pontos pt ON pt.projeto_id = p.id
                        WHERE p.owner_id = $1::uuid
                        GROUP BY p.id
                        ORDER BY p.atualizado_em DESC
                        LIMIT $2 OFFSET $3
                        """,
                        owner_id,
                        bounded_limit,
                        bounded_offset,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT p.id::text AS id,
                               p.orgao,
                               p.ns,
                               p.nome,
                               p.endereco,
                               p.estudado_por,
                               p.matricula,
                               p.data_estudo,
                               p.atualizado_em,
                               COUNT(pt.id)::int AS total_pontos
                        FROM projetos p
                        LEFT JOIN pontos pt ON pt.projeto_id = p.id
                        GROUP BY p.id
                        ORDER BY p.atualizado_em DESC
                        LIMIT $1 OFFSET $2
                        """,
                        bounded_limit,
                        bounded_offset,
                    )
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"[WARN] Error listing projetos: {e}")
            return []

    async def save_projeto(self, dados: Dict[str, Any], owner_id: str) -> Optional[str]:
        """INSERT a new project and return its UUID.

        dados keys: orgao, ns, nome, endereco, estudado_por, matricula, data_estudo
        """
        if not self.enabled:
            return None
        try:
            pool = await self._get_pool()
            if not pool:
                return None
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO projetos (orgao, ns, nome, endereco, estudado_por, matricula, data_estudo, owner_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::uuid)
                    RETURNING id::text
                    """,
                    dados.get("orgao"),
                    dados.get("ns"),
                    dados.get("nome"),
                    dados.get("endereco"),
                    dados.get("estudado_por"),
                    dados.get("matricula"),
                    dados.get("data_estudo"),
                    owner_id,
                )
                return row["id"] if row else None
        except Exception as e:
            print(f"[WARN] Error saving projeto: {e}")
            return None

    async def save_ponto(
        self,
        projeto_id: str,
        ponto: str,
        tipo_poste: str,
        modelo_poste: str,
    ) -> Optional[str]:
        """INSERT a new ponto under a project and return its UUID.

        Raises IntegrityError if (projeto_id, ponto) already exists.
        """
        if not self.enabled:
            return None
        try:
            pool = await self._get_pool()
            if not pool:
                return None
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO pontos (projeto_id, ponto, tipo_poste, modelo_poste)
                    VALUES ($1::uuid, $2, $3, $4)
                    RETURNING id::text
                    """,
                    projeto_id, ponto, tipo_poste, modelo_poste,
                )
                # Touch projeto.atualizado_em
                await conn.execute(
                    "UPDATE projetos SET atualizado_em = now() WHERE id = $1::uuid",
                    projeto_id,
                )
                return row["id"] if row else None
        except Exception as e:
            print(f"[WARN] Error saving ponto: {e}")
            return None

    async def user_can_access_projeto(
        self,
        projeto_id: str,
        user_id: str,
        is_admin: bool = False,
    ) -> bool:
        """Validate whether a user can access/mutate a project."""
        if not self.enabled:
            return False
        try:
            pool = await self._get_pool()
            if not pool:
                return False

            async with pool.acquire() as conn:
                if is_admin:
                    row = await conn.fetchrow(
                        "SELECT 1 FROM projetos WHERE id = $1::uuid",
                        projeto_id,
                    )
                else:
                    row = await conn.fetchrow(
                        """
                        SELECT 1
                        FROM projetos
                        WHERE id = $1::uuid
                          AND owner_id = $2::uuid
                        """,
                        projeto_id,
                        user_id,
                    )
                return row is not None
        except Exception as e:
            print(f"[WARN] Error checking projeto ownership: {e}")
            return False

    async def user_can_access_ponto(
        self,
        ponto_id: str,
        user_id: str,
        is_admin: bool = False,
    ) -> bool:
        """Validate whether a user can access/mutate a point."""
        if not self.enabled:
            return False
        try:
            pool = await self._get_pool()
            if not pool:
                return False

            async with pool.acquire() as conn:
                if is_admin:
                    row = await conn.fetchrow(
                        "SELECT 1 FROM pontos WHERE id = $1::uuid",
                        ponto_id,
                    )
                else:
                    row = await conn.fetchrow(
                        """
                        SELECT 1
                        FROM pontos pt
                        JOIN projetos p ON p.id = pt.projeto_id
                        WHERE pt.id = $1::uuid
                          AND p.owner_id = $2::uuid
                        """,
                        ponto_id,
                        user_id,
                    )
                return row is not None
        except Exception as e:
            print(f"[WARN] Error checking ponto ownership: {e}")
            return False

    async def _upsert_niveis_travessias_tx(
        self,
        conn: asyncpg.Connection,
        ponto_id: str,
        niveis: List[Dict[str, Any]],
    ) -> None:
        """Upsert niveis_calculo and travessias using an open transaction."""
        for nivel_data in niveis:
            nivel_label = nivel_data["nivel"]
            # Upsert nivel_calculo (UNIQUE ponto_id + nivel)
            nivel_row = await conn.fetchrow(
                """
                INSERT INTO niveis_calculo (ponto_id, nivel, altura_poste, altura_ancoragem)
                VALUES ($1::uuid, $2::nivel_tipo, $3, $4)
                ON CONFLICT (ponto_id, nivel)
                DO UPDATE SET altura_poste = EXCLUDED.altura_poste,
                              altura_ancoragem = EXCLUDED.altura_ancoragem
                RETURNING id
                """,
                ponto_id,
                nivel_label,
                nivel_data.get("altura_poste"),
                nivel_data.get("altura_ancoragem"),
            )
            nivel_id = str(nivel_row["id"])
            # Upsert each traversal (UNIQUE nivel_id + posicao)
            for t in nivel_data.get("travessias", []):
                await conn.execute(
                    """
                    INSERT INTO travessias
                      (nivel_id, posicao, tipo_rede, tipo_cabo,
                       vao, flecha, angulo, qtd_ligacoes, qtd_cabos)
                    VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (nivel_id, posicao)
                    DO UPDATE SET
                      tipo_rede    = EXCLUDED.tipo_rede,
                      tipo_cabo    = EXCLUDED.tipo_cabo,
                      vao          = EXCLUDED.vao,
                      flecha       = EXCLUDED.flecha,
                      angulo       = EXCLUDED.angulo,
                      qtd_ligacoes = EXCLUDED.qtd_ligacoes,
                      qtd_cabos    = EXCLUDED.qtd_cabos
                    """,
                    nivel_id,
                    t["posicao"],
                    _nullable_scalar(t, "tipo_rede"),
                    _nullable_scalar(t, "tipo_cabo"),
                    _nullable_scalar(t, "vao"),
                    _nullable_scalar(t, "flecha"),
                    _nullable_scalar(t, "angulo"),
                    _nullable_scalar(t, "qtd_ligacoes"),
                    _nullable_scalar(t, "qtd_cabos"),
                )

    async def _upsert_resultado_tx(
        self,
        conn: asyncpg.Connection,
        ponto_id: str,
        resultado: Dict[str, Any],
    ) -> None:
        """Upsert resultados_calculo using an open transaction."""
        await conn.execute(
            """
            INSERT INTO resultados_calculo (
              ponto_id,
              mt1_tracao,  mt1_angulo,
              mt2_tracao,  mt2_angulo,
              bt_tracao,   bt_angulo,
              btz_tracao,  btz_angulo,
              ral_tracao,  ral_angulo,
              total_tracao, total_angulo,
              poste_ecc,
              texto_mt1, texto_mt2, texto_bt,
              texto_btz, texto_ral, texto_total,
              calculado_em
            ) VALUES (
              $1::uuid, $2, $3, $4, $5, $6, $7, $8, $9,
              $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
              now()
            )
            ON CONFLICT (ponto_id) DO UPDATE SET
              mt1_tracao   = EXCLUDED.mt1_tracao,
              mt1_angulo   = EXCLUDED.mt1_angulo,
              mt2_tracao   = EXCLUDED.mt2_tracao,
              mt2_angulo   = EXCLUDED.mt2_angulo,
              bt_tracao    = EXCLUDED.bt_tracao,
              bt_angulo    = EXCLUDED.bt_angulo,
              btz_tracao   = EXCLUDED.btz_tracao,
              btz_angulo   = EXCLUDED.btz_angulo,
              ral_tracao   = EXCLUDED.ral_tracao,
              ral_angulo   = EXCLUDED.ral_angulo,
              total_tracao = EXCLUDED.total_tracao,
              total_angulo = EXCLUDED.total_angulo,
              poste_ecc    = EXCLUDED.poste_ecc,
              texto_mt1    = EXCLUDED.texto_mt1,
              texto_mt2    = EXCLUDED.texto_mt2,
              texto_bt     = EXCLUDED.texto_bt,
              texto_btz    = EXCLUDED.texto_btz,
              texto_ral    = EXCLUDED.texto_ral,
              texto_total  = EXCLUDED.texto_total,
              calculado_em = EXCLUDED.calculado_em
            """,
            ponto_id,
            resultado.get("mt1_tracao"),  resultado.get("mt1_angulo"),
            resultado.get("mt2_tracao"),  resultado.get("mt2_angulo"),
            resultado.get("bt_tracao"),   resultado.get("bt_angulo"),
            resultado.get("btz_tracao"),  resultado.get("btz_angulo"),
            resultado.get("ral_tracao"),  resultado.get("ral_angulo"),
            resultado.get("total_tracao"), resultado.get("total_angulo"),
            resultado.get("poste_ecc"),
            resultado.get("texto_mt1"),   resultado.get("texto_mt2"),
            resultado.get("texto_bt"),    resultado.get("texto_btz"),
            resultado.get("texto_ral"),   resultado.get("texto_total"),
        )

    async def save_calculo(
        self,
        ponto_id: str,
        niveis: List[Dict[str, Any]],
    ) -> bool:
        """Persist niveis_calculo + travessias inside a transaction.

        niveis: list of 5 dicts (one per level: MT1, MT2, BT, BTZ, RAL).
        Each dict:
        {
          "nivel":             str  (MT1|MT2|BT|BTZ|RAL),
          "altura_poste":      float | None,
          "altura_ancoragem":  float | None,
          "travessias": [
            {  # posicao 1..4
              "posicao":       int,
              "tipo_rede":     str,
              "tipo_cabo":     str,
              "vao":           float,
              "flecha":        float,
              "angulo":        float,
              "qtd_ligacoes":  float | None,  # BTZ only
              "qtd_cabos":     float | None,  # RAL only
            }, ...
          ]
        }
        """
        if not self.enabled:
            return False
        try:
            pool = await self._get_pool()
            if not pool:
                return False
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await self._upsert_niveis_travessias_tx(conn, ponto_id, niveis)
            return True
        except Exception as e:
            print(f"[WARN] Error saving calculo: {e}")
            return False

    async def upsert_resultado(
        self,
        ponto_id: str,
        resultado: Dict[str, Any],
    ) -> bool:
        """INSERT or UPDATE resultados_calculo for a given ponto.

        resultado keys mirror CalculoOutput fields:
        mt1_tracao, mt1_angulo, mt2_tracao, mt2_angulo,
        bt_tracao,  bt_angulo,  btz_tracao, btz_angulo,
        ral_tracao, ral_angulo, total_tracao, total_angulo,
        poste_ecc,  texto_mt1, texto_mt2, texto_bt,
        texto_btz,  texto_ral, texto_total
        """
        if not self.enabled:
            return False
        try:
            pool = await self._get_pool()
            if not pool:
                return False
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await self._upsert_resultado_tx(conn, ponto_id, resultado)
            return True
        except Exception as e:
            print(f"[WARN] Error upserting resultado: {e}")
            return False

    async def save_calculo_snapshot(
        self,
        ponto_id: str,
        niveis: List[Dict[str, Any]],
        resultado: Dict[str, Any],
    ) -> bool:
        """Persist calculo snapshot atomically (niveis/travessias + resultado)."""
        if not self.enabled:
            return False

        max_retries = max(0, self.snapshot_retry_max_retries)
        total_attempts = max_retries + 1

        for attempt in range(1, total_attempts + 1):
            try:
                return await self._save_calculo_snapshot_once(ponto_id, niveis, resultado)
            except Exception as e:
                if self._is_snapshot_non_retryable_error(e):
                    print(f"[WARN] Non-retryable error saving calculo snapshot: {e}")
                    return False

                if not self._is_snapshot_retryable_error(e):
                    print(f"[WARN] Error saving calculo snapshot: {e}")
                    return False

                if attempt >= total_attempts:
                    print(f"[WARN] Error saving calculo snapshot after {attempt} attempts: {e}")
                    return False

                delay_seconds = self._snapshot_retry_backoff_seconds(attempt)
                print(
                    "[WARN] Transient error saving calculo snapshot "
                    f"(attempt {attempt}/{total_attempts}); retry in {delay_seconds:.2f}s: {e}"
                )
                await self._sleep_before_snapshot_retry(delay_seconds)

        return False

    async def _save_calculo_snapshot_once(
        self,
        ponto_id: str,
        niveis: List[Dict[str, Any]],
        resultado: Dict[str, Any],
    ) -> bool:
        """Persist calculo snapshot once, letting exceptions bubble up."""
        if not self.enabled:
            return False

        pool = await self._get_pool()
        if not pool:
            raise ConnectionError("connection pool unavailable")

        async with pool.acquire() as conn:
            async with conn.transaction():
                await self._upsert_niveis_travessias_tx(conn, ponto_id, niveis)
                await self._upsert_resultado_tx(conn, ponto_id, resultado)
        return True

    async def save_batch_calculo(
        self,
        owner_id: str,
        projeto_id: Optional[str],
        projeto_dados: Optional[Dict[str, Any]],
        ponto_dados: Dict[str, Any],
        niveis: List[Dict[str, Any]],
        resultado: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Atomic batch save of everything in one transaction (Project, Point, Snapshot)."""
        if not self.enabled:
            return {"error": "Supabase disabled"}

        pool = await self._get_pool()
        if not pool:
            return {"error": "Connection pool unavailable"}

        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # 1. Projeto
                    final_proj_id = projeto_id
                    if not final_proj_id and projeto_dados:
                        row_p = await conn.fetchrow(
                            """
                            INSERT INTO projetos (orgao, ns, nome, endereco, estudado_por, matricula, data_estudo, owner_id)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::uuid)
                            RETURNING id::text
                            """,
                            projeto_dados.get("orgao"),
                            projeto_dados.get("ns"),
                            projeto_dados.get("nome"),
                            projeto_dados.get("endereco"),
                            projeto_dados.get("estudado_por"),
                            projeto_dados.get("matricula"),
                            projeto_dados.get("data_estudo"),
                            owner_id,
                        )
                        final_proj_id = row_p["id"]
                    
                    if not final_proj_id:
                        return {"error": "Falha ao resolver projeto_id"}

                    # 2. Ponto (Upsert-like logic to avoid 409)
                    # We check if (projeto_id, ponto) exists
                    ponto_label = ponto_dados.get("ponto")
                    row_pt = await conn.fetchrow(
                        "SELECT id::text FROM pontos WHERE projeto_id = $1::uuid AND ponto = $2",
                        final_proj_id, ponto_label
                    )
                    
                    final_ponto_id = None
                    if row_pt:
                        final_ponto_id = row_pt["id"]
                        # Update poste info if changed
                        await conn.execute(
                            "UPDATE pontos SET tipo_poste = $1, modelo_poste = $2 WHERE id = $3::uuid",
                            ponto_dados.get("tipo_poste"), ponto_dados.get("modelo_poste"), final_ponto_id
                        )
                    else:
                        row_pt_new = await conn.fetchrow(
                            """
                            INSERT INTO pontos (projeto_id, ponto, tipo_poste, modelo_poste)
                            VALUES ($1::uuid, $2, $3, $4)
                            RETURNING id::text
                            """,
                            final_proj_id, ponto_label, 
                            ponto_dados.get("tipo_poste"), ponto_dados.get("modelo_poste")
                        )
                        final_ponto_id = row_pt_new["id"]

                    if not final_ponto_id:
                        return {"error": "Falha ao resolver ponto_id"}

                    # 3. Snapshot (Níveis + Travessias)
                    await self._upsert_niveis_travessias_tx(conn, final_ponto_id, niveis)
                    
                    # 4. Resultado
                    await self._upsert_resultado_tx(conn, final_ponto_id, resultado)

                    # 5. Touch Project
                    await conn.execute(
                        "UPDATE projetos SET atualizado_em = now() WHERE id = $1::uuid",
                        final_proj_id
                    )

                    return {
                        "projeto_id": final_proj_id,
                        "ponto_id": final_ponto_id,
                        "success": True
                    }

        except Exception as e:
            print(f"[ERROR] save_batch_calculo failure: {e}")
            return {"error": str(e)}


_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get or create singleton Supabase client."""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client
