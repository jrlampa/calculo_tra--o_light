"""Performance benchmarks for backend API and database operations.

This module contains pytest-benchmark tests to track performance metrics
and ensure no regressions in critical paths.

Usage:
    pytest python/benchmarks/test_perf_api.py --benchmark-only
    pytest python/benchmarks/test_perf_api.py --benchmark-histogram
    pytest python/benchmarks/test_perf_api.py --benchmark-compare=0001
"""

import asyncio
import json
from uuid import uuid4

import pytest
from httpx import AsyncClient

from api.main import app
from db.pool import db_pool


@pytest.fixture
async def client():
    """Async HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def sample_projeto_id():
    """Create a sample projeto for benchmarking."""
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO projetos 
            (id, nome, orgao, ns, endereco, estudado_por, matricula, owner_id, criado_em, atualizado_em)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
            RETURNING id
            """,
            str(uuid4()),
            f"BENCH_PROJ_{uuid4().hex[:8]}",
            "TEST_ORG",
            "TEST-01",
            "Test Address",
            "Benchmark Bot",
            "9999",
            str(uuid4()),
        )
        yield result["id"]


class TestAPIPerformance:
    """API endpoint performance benchmarks."""

    @pytest.mark.benchmark(
        group="list_projetos",
        min_rounds=10,
    )
    def test_list_projetos_performance(self, benchmark, client):
        """Benchmark GET /projetos endpoint."""

        async def benchmark_list():
            response = await client.get(
                "/projetos",
                headers={"X-Admin-Token": "test-token"},
            )
            return response

        result = benchmark(lambda: asyncio.run(benchmark_list()))
        assert result.status_code == 200

    @pytest.mark.benchmark(
        group="create_projeto",
        min_rounds=5,
    )
    def test_create_projeto_performance(self, benchmark, client):
        """Benchmark POST /projetos endpoint."""

        async def benchmark_create():
            payload = {
                "orgao": "BENCH_ORG",
                "ns": f"BENCH-{uuid4().hex[:4]}",
                "nome": f"BenchProj_{uuid4().hex[:6]}",
                "endereco": "Benchmark Street",
                "estudado_por": "Perf Bot",
                "matricula": "9999",
            }
            response = await client.post(
                "/projetos",
                json=payload,
                headers={"X-Admin-Token": "test-token"},
            )
            return response

        result = benchmark(lambda: asyncio.run(benchmark_create()))
        assert result.status_code == 201

    @pytest.mark.benchmark(
        group="create_ponto",
        min_rounds=5,
    )
    def test_create_ponto_performance(self, benchmark, client, sample_projeto_id):
        """Benchmark POST /projetos/{projeto_id}/pontos endpoint."""

        async def benchmark_create_ponto():
            payload = {
                "ponto": f"BENCH_{uuid4().hex[:3]}",
                "tipo_poste": "DT",
                "modelo_poste": "11/600",
            }
            response = await client.post(
                f"/projetos/{sample_projeto_id}/pontos",
                json=payload,
                headers={"X-Admin-Token": "test-token"},
            )
            return response

        result = benchmark(lambda: asyncio.run(benchmark_create_ponto()))
        assert result.status_code == 201


class TestDatabasePerformance:
    """Database operation performance benchmarks."""

    @pytest.mark.benchmark(
        group="db_projet_select",
        min_rounds=20,
    )
    def test_db_projeto_select(self, benchmark):
        """Benchmark projeto SELECT queries."""

        async def benchmark_select():
            async with db_pool.acquire() as conn:
                result = await conn.fetch(
                    "SELECT id, nome, orgao, criado_em FROM projetos LIMIT 100"
                )
            return result

        result = benchmark(lambda: asyncio.run(benchmark_select()))
        assert isinstance(result, list)

    @pytest.mark.benchmark(
        group="db_projeto_insert",
        min_rounds=10,
    )
    def test_db_projeto_insert(self, benchmark):
        """Benchmark projeto INSERT operations."""

        async def benchmark_insert():
            async with db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    INSERT INTO projetos 
                    (id, nome, orgao, ns, endereco, estudado_por, matricula, owner_id, criado_em, atualizado_em)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
                    RETURNING id
                    """,
                    str(uuid4()),
                    f"BENCH_{uuid4().hex[:8]}",
                    "BENCH_ORG",
                    "BENCH-NS",
                    "Benchmark Address",
                    "Perf Bot",
                    "9999",
                    str(uuid4()),
                )
            return result

        result = benchmark(lambda: asyncio.run(benchmark_insert()))
        assert result is not None

    @pytest.mark.benchmark(
        group="db_join_query",
        min_rounds=20,
    )
    def test_db_join_performance(self, benchmark):
        """Benchmark JOIN queries across related tables."""

        async def benchmark_join():
            async with db_pool.acquire() as conn:
                result = await conn.fetch(
                    """
                    SELECT 
                        p.id, p.nome,
                        COUNT(pt.id) as ponto_count,
                        COUNT(nc.id) as nivel_count
                    FROM projetos p
                    LEFT JOIN pontos pt ON pt.projeto_id = p.id
                    LEFT JOIN niveis_calculo nc ON nc.ponto_id = pt.id
                    GROUP BY p.id
                    LIMIT 50
                    """
                )
            return result

        result = benchmark(lambda: asyncio.run(benchmark_join()))
        assert isinstance(result, list)

    @pytest.mark.benchmark(
        group="db_transaction",
        min_rounds=5,
    )
    def test_db_transaction_performance(self, benchmark):
        """Benchmark transactional operations."""

        async def benchmark_transaction():
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    # Insert projeto
                    proj_id = await conn.fetchval(
                        """
                        INSERT INTO projetos 
                        (id, nome, orgao, ns, endereco, estudado_por, matricula, owner_id, criado_em, atualizado_em)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
                        RETURNING id
                        """,
                        str(uuid4()),
                        f"TXN_{uuid4().hex[:8]}",
                        "TXN_ORG",
                        "TXN-01",
                        "Transaction Address",
                        "TXN Bot",
                        "9999",
                        str(uuid4()),
                    )

                    # Insert ponto
                    ponto_id = await conn.fetchval(
                        """
                        INSERT INTO pontos
                        (id, projeto_id, ponto, tipo_poste, modelo_poste)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id
                        """,
                        str(uuid4()),
                        proj_id,
                        "01",
                        "DT",
                        "11/600",
                    )

                return {"project": proj_id, "ponto": ponto_id}

        result = benchmark(lambda: asyncio.run(benchmark_transaction()))
        assert result is not None

    @pytest.mark.benchmark(
        group="db_index_query",
        min_rounds=20,
    )
    def test_db_index_performance(self, benchmark):
        """Benchmark queries using indexes."""

        async def benchmark_index():
            async with db_pool.acquire() as conn:
                # Query using FK index
                result = await conn.fetch(
                    """
                    SELECT pt.id, pt.ponto 
                    FROM pontos pt
                    WHERE pt.projeto_id IS NOT NULL
                    LIMIT 50
                    """
                )
            return result

        result = benchmark(lambda: asyncio.run(benchmark_index()))
        assert isinstance(result, list)


class TestConnectionPoolPerformance:
    """Connection pool performance under concurrent load."""

    @pytest.mark.benchmark(group="pool_concurrent_acquire")
    def test_pool_concurrent_operations(self, benchmark):
        """Benchmark connection pool under concurrent load."""

        async def benchmark_pool():
            async def worker():
                async with db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")

            # Create 10 concurrent operations
            await asyncio.gather(*[worker() for _ in range(10)])

        benchmark(lambda: asyncio.run(benchmark_pool()))


class TestCachingPerformance:
    """Caching layer performance benchmarks."""

    @pytest.mark.benchmark(group="cache_redis")
    @pytest.mark.asyncio
    async def test_redis_cache_performance(self, benchmark):
        """Benchmark Redis cache operations."""
        from cache.manager import get_cache_manager

        cache = await get_cache_manager()

        async def benchmark_cache():
            key = f"perf_test_{uuid4()}"
            value = {"test": "data", "timestamp": "2026-03-24"}

            # Cache set
            await cache.set(key, json.dumps(value), ttl=60)

            # Cache get
            result = await cache.get(key)
            return result

        result = benchmark(lambda: asyncio.run(benchmark_cache()))
        assert result is not None


# Configuration for pytest-benchmark
pytest_plugins = ("pytest_benchmark",)


# Generate benchmark report
def pytest_configure(config):
    """Configure pytest with benchmark plugin."""
    if not hasattr(config, "workerinput"):
        config.addinivalue_line(
            "markers",
            "benchmark(group, min_rounds): mark test as benchmark with group and rounds",
        )
