from __future__ import annotations

import os
import re
import sys
import uuid
from typing import Any

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.main import app
import api.main as api_main
from core.operation_context import OPERATION_ID_HEADER


def _make_client(monkeypatch) -> TestClient:
    async def _noop_async(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "false")
    monkeypatch.setattr(api_main, "validate_auth_config", lambda: None)
    monkeypatch.setattr(api_main, "initialize_db_pool", _noop_async)
    monkeypatch.setattr(api_main, "get_cache_manager", _noop_async)
    monkeypatch.setattr(api_main.db_pool, "close", _noop_async)

    return TestClient(app)


def test_health_response_includes_operation_id(monkeypatch) -> None:
    with _make_client(monkeypatch) as client:
        response = client.get("/health")

    operation_id = response.headers.get(OPERATION_ID_HEADER)
    assert response.status_code == 200
    assert operation_id is not None
    assert str(uuid.UUID(operation_id)) == operation_id


def test_valid_inbound_operation_id_is_preserved(monkeypatch) -> None:
    custom_operation_id = str(uuid.uuid4())

    with _make_client(monkeypatch) as client:
        response = client.get(
            "/health",
            headers={OPERATION_ID_HEADER: custom_operation_id},
        )

    assert response.status_code == 200
    assert response.headers[OPERATION_ID_HEADER] == custom_operation_id


def test_invalid_inbound_operation_id_is_replaced(monkeypatch) -> None:
    with _make_client(monkeypatch) as client:
        response = client.get(
            "/health",
            headers={OPERATION_ID_HEADER: "not-a-uuid"},
        )

    operation_id = response.headers.get(OPERATION_ID_HEADER)
    assert response.status_code == 200
    assert operation_id != "not-a-uuid"
    assert operation_id is not None
    assert re.match(r"^[0-9a-f-]{36}$", operation_id)