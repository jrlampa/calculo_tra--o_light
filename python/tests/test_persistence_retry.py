"""Unit tests for resilient snapshot persistence retry behavior."""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.supabase_client import SupabaseClient


class FakePersistenceError(Exception):
    """Simple exception that mimics DB errors with SQLSTATE support."""

    def __init__(self, message: str, sqlstate: str | None = None):
        super().__init__(message)
        self.sqlstate = sqlstate


def _build_client() -> SupabaseClient:
    client = SupabaseClient()
    client.enabled = True
    client.snapshot_retry_max_retries = 3
    client.snapshot_retry_backoff_base_seconds = 0.1
    client.snapshot_retry_backoff_cap_seconds = 1.0
    return client


def test_snapshot_retry_succeeds_after_transient_failure(monkeypatch: pytest.MonkeyPatch):
    client = _build_client()
    attempts = {"count": 0}
    sleep_calls: list[float] = []

    async def fake_once(self, ponto_id, niveis, resultado):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise FakePersistenceError(
                "could not serialize access due to concurrent update",
                sqlstate="40001",
            )
        return True

    async def fake_sleep(self, delay_seconds: float):
        sleep_calls.append(delay_seconds)

    monkeypatch.setattr(
        client,
        "_save_calculo_snapshot_once",
        fake_once.__get__(client, SupabaseClient),
    )
    monkeypatch.setattr(
        client,
        "_sleep_before_snapshot_retry",
        fake_sleep.__get__(client, SupabaseClient),
    )

    result = asyncio.run(client.save_calculo_snapshot("ponto-1", [], {}))

    assert result is True
    assert attempts["count"] == 3
    assert sleep_calls == pytest.approx([0.1, 0.2])


@pytest.mark.parametrize(
    ("message", "sqlstate"),
    [
        ("new row violates row-level security policy", "42501"),
        ("permission denied for table resultados_calculo", None),
    ],
)
def test_snapshot_no_retry_on_rls_or_permission_denied(
    monkeypatch: pytest.MonkeyPatch,
    message: str,
    sqlstate: str | None,
):
    client = _build_client()
    attempts = {"count": 0}
    sleep_calls: list[float] = []

    async def fake_once(self, ponto_id, niveis, resultado):
        attempts["count"] += 1
        raise FakePersistenceError(message, sqlstate=sqlstate)

    async def fake_sleep(self, delay_seconds: float):
        sleep_calls.append(delay_seconds)

    monkeypatch.setattr(
        client,
        "_save_calculo_snapshot_once",
        fake_once.__get__(client, SupabaseClient),
    )
    monkeypatch.setattr(
        client,
        "_sleep_before_snapshot_retry",
        fake_sleep.__get__(client, SupabaseClient),
    )

    result = asyncio.run(client.save_calculo_snapshot("ponto-2", [], {}))

    assert result is False
    assert attempts["count"] == 1
    assert sleep_calls == []


def test_snapshot_retry_exhausted_returns_false(monkeypatch: pytest.MonkeyPatch):
    client = _build_client()
    client.snapshot_retry_max_retries = 2
    attempts = {"count": 0}
    sleep_calls: list[float] = []

    async def fake_once(self, ponto_id, niveis, resultado):
        attempts["count"] += 1
        raise FakePersistenceError(
            "could not serialize access due to read/write dependencies",
            sqlstate="40001",
        )

    async def fake_sleep(self, delay_seconds: float):
        sleep_calls.append(delay_seconds)

    monkeypatch.setattr(
        client,
        "_save_calculo_snapshot_once",
        fake_once.__get__(client, SupabaseClient),
    )
    monkeypatch.setattr(
        client,
        "_sleep_before_snapshot_retry",
        fake_sleep.__get__(client, SupabaseClient),
    )

    result = asyncio.run(client.save_calculo_snapshot("ponto-3", [], {}))

    assert result is False
    assert attempts["count"] == 3
    assert sleep_calls == pytest.approx([0.1, 0.2])
