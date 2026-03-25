from __future__ import annotations


from typing import Any, Optional
from uuid import UUID, uuid4

import structlog
from fastapi import Request

OPERATION_ID_HEADER = "X-Operation-ID"


def resolve_operation_id(candidate: Optional[str]) -> str:
    """Return a valid operation id, preserving trusted inbound UUIDs."""
    if candidate:
        try:
            return str(UUID(candidate))
        except (ValueError, TypeError, AttributeError):
            pass
    return str(uuid4())


def get_operation_id(request: Request) -> Optional[str]:
    """Read operation_id from request state when present."""
    return getattr(request.state, "operation_id", None)


def get_request_user_id(request: Request) -> Optional[str]:
    """Read current user id from request state when present."""
    current_user = getattr(request.state, "current_user", None)
    if current_user is None:
        return None
    user_id = getattr(current_user, "user_id", None)
    return str(user_id) if user_id is not None else None


def build_operation_context(
    request: Request,
    *,
    projeto_id: Optional[str] = None,
    ponto_id: Optional[str] = None,
    user_id: Optional[str] = None,
    include_request_fields: bool = True,
    **extra: Any,
) -> dict[str, Any]:
    """Build a normalized operational context payload for logs/audit."""
    context: dict[str, Any] = {
        "operation_id": get_operation_id(request),
        "user_id": user_id or get_request_user_id(request),
        "projeto_id": str(projeto_id) if projeto_id is not None else None,
        "ponto_id": str(ponto_id) if ponto_id is not None else None,
    }
    if include_request_fields:
        context["path"] = request.url.path
        context["method"] = request.method

    for key, value in extra.items():
        if value is not None:
            context[key] = value

    return {key: value for key, value in context.items() if value is not None}


def bind_operation_context(
    request: Request,
    *,
    projeto_id: Optional[str] = None,
    ponto_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **extra: Any,
) -> dict[str, Any]:
    """Bind operational context to structlog for the current request."""
    context = build_operation_context(
        request,
        projeto_id=projeto_id,
        ponto_id=ponto_id,
        user_id=user_id,
        **extra,
    )
    if context:
        structlog.contextvars.bind_contextvars(**context)
    return context
