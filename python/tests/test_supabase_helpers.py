"""Unit tests for api.dependencies shared Supabase helpers.

Verifies that:
1. ensure_supabase_available raises HTTP 503 when Supabase is disabled.
2. ensure_supabase_available raises HTTP 503 when the pool health-check fails.
3. ensure_supabase_available passes silently when Supabase is healthy.
4. run_supabase_lookup raises HTTP 503 when Supabase is disabled.
5. run_supabase_lookup raises HTTP 503 when the fetcher raises an exception.
6. run_supabase_lookup returns the fetcher result when healthy.
"""
import sys
import os

os.environ.setdefault("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "false")
os.environ.setdefault("APP_ENV", "development")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from api.dependencies import ensure_supabase_available, run_supabase_lookup


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_supabase(*, is_enabled=True, pool_healthy=True):
    """Build a fake Supabase client for testing."""
    supabase = MagicMock()
    supabase.is_enabled = is_enabled

    if pool_healthy:
        # Simulate a healthy pool with a working connection
        conn = AsyncMock()
        conn.fetchval = AsyncMock(return_value=1)
        conn.__aenter__ = AsyncMock(return_value=conn)
        conn.__aexit__ = AsyncMock(return_value=None)

        pool = AsyncMock()
        pool.acquire = MagicMock(return_value=conn)

        supabase._get_pool = AsyncMock(return_value=pool)
    else:
        # Simulate a failed pool
        supabase._get_pool = AsyncMock(side_effect=RuntimeError("pool down"))

    return supabase


# ── ensure_supabase_available ─────────────────────────────────────────────────

class TestEnsureSupabaseAvailable:

    @pytest.mark.asyncio
    async def test_raises_503_when_disabled(self):
        """HTTP 503 when supabase.is_enabled is False."""
        supabase = _mock_supabase(is_enabled=False)
        with pytest.raises(HTTPException) as exc_info:
            await ensure_supabase_available(supabase)
        assert exc_info.value.status_code == 503
        assert "DATABASE_URL" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_503_when_pool_fails(self):
        """HTTP 503 when the pool health-check raises."""
        supabase = _mock_supabase(is_enabled=True, pool_healthy=False)
        with pytest.raises(HTTPException) as exc_info:
            await ensure_supabase_available(supabase)
        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_passes_when_healthy(self):
        """No exception when Supabase is healthy."""
        supabase = _mock_supabase(is_enabled=True, pool_healthy=True)
        await ensure_supabase_available(supabase)  # should not raise


# ── run_supabase_lookup ───────────────────────────────────────────────────────

class TestRunSupabaseLookup:

    @pytest.mark.asyncio
    async def test_raises_503_when_supabase_disabled(self):
        """HTTP 503 when Supabase is disabled."""
        supabase = _mock_supabase(is_enabled=False)
        with pytest.raises(HTTPException) as exc_info:
            await run_supabase_lookup(supabase, AsyncMock())
        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_raises_503_when_fetcher_fails(self):
        """HTTP 503 when the fetcher raises any exception."""
        supabase = _mock_supabase(is_enabled=True, pool_healthy=True)
        failing_fetcher = AsyncMock(side_effect=RuntimeError("db error"))
        with pytest.raises(HTTPException) as exc_info:
            await run_supabase_lookup(supabase, failing_fetcher)
        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_returns_fetcher_result_when_healthy(self):
        """Returns fetcher's result when Supabase is healthy."""
        supabase = _mock_supabase(is_enabled=True, pool_healthy=True)
        fetcher = AsyncMock(return_value=[{"id": 1, "nome": "Cabo XLPE"}])
        result = await run_supabase_lookup(supabase, fetcher)
        assert result == [{"id": 1, "nome": "Cabo XLPE"}]
        fetcher.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_propagates_http_exception_from_fetcher(self):
        """If fetcher raises HTTPException it is re-raised as-is."""
        supabase = _mock_supabase(is_enabled=True, pool_healthy=True)
        http_exc = HTTPException(status_code=404, detail="Not found")
        fetcher = AsyncMock(side_effect=http_exc)
        with pytest.raises(HTTPException) as exc_info:
            await run_supabase_lookup(supabase, fetcher)
        assert exc_info.value.status_code == 404
