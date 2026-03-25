"""Authentication and authorization helpers for JWT and signed sessions.
The provided code contains authentication and authorization helpers for JWT and signed sessions in a
Python FastAPI application.

:param var_name: The `var_name` parameter in the `_read_positive_int_env` and `_read_bool_env`
functions is a string representing the name of the environment variable that you want to read the
value from. It is used to retrieve the value of the specified environment variable from the system
environment variables
:type var_name: str
:param default: The code you provided contains helper functions and classes for authentication and
authorization using JWT and signed sessions in a FastAPI application. Here is a brief overview of
the key components:
:type default: int
:return: The code snippet provided contains helper functions for authentication and authorization
using JWT and signed sessions. It includes functions for reading environment variables, resolving
secrets, creating and verifying session cookies, parsing JWT tokens, resolving current user
information, requiring JWT for mutations, and handling admin access.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from typing import Annotated, Any, Literal

from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

_logger = logging.getLogger(__name__)


def _read_positive_int_env(var_name: str, default: int) -> int:
    raw_value = os.getenv(var_name)
    if raw_value is None:
        return default

    try:
        parsed = int(raw_value)
    except ValueError:
        return default

    return parsed if parsed > 0 else default


def _read_bool_env(var_name: str, default: bool) -> bool:
    raw_value = os.getenv(var_name)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def _is_production_environment() -> bool:
    env_name = (
        (os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or os.getenv("PYTHON_ENV") or "")
        .strip()
        .lower()
    )
    return env_name in {"prod", "production"}


def _resolve_jwt_secret() -> str | None:
    for var_name in ("AUTH_JWT_SECRET", "SUPABASE_JWT_SECRET", "JWT_SECRET"):
        value = (os.getenv(var_name) or "").strip()
        if value:
            return value
    return None


def _should_require_jwt_for_mutations() -> bool:
    # Default: always require JWT. Opt-out explicitly with
    # AUTH_REQUIRE_JWT_FOR_MUTATIONS=false (development only).
    return _read_bool_env("AUTH_REQUIRE_JWT_FOR_MUTATIONS", default=True)


def _resolve_session_secret() -> str:
    configured = (os.getenv("AUTH_SESSION_SECRET") or "").strip()
    if configured:
        return configured
    if _is_production_environment():
        raise RuntimeError(
            "AUTH_SESSION_SECRET deve ser definido em produção. "
            "Defina a variável de ambiente AUTH_SESSION_SECRET."
        )
    # Desenvolvimento: gerar e avisar
    generated = uuid.uuid4().hex
    _logger.warning(
        "AUTH_SESSION_SECRET não configurado — usando valor volátil. "
        "Sessões serão invalidadas a cada restart. "
        "Defina AUTH_SESSION_SECRET para persistência de sessão."
    )
    return generated


SESSION_COOKIE_NAME = os.getenv("AUTH_SESSION_COOKIE_NAME", "calc_session")
SESSION_TTL_SECONDS = _read_positive_int_env("AUTH_SESSION_TTL_SECONDS", 86400)
SESSION_SECRET = _resolve_session_secret()

JWT_COOKIE_NAME = os.getenv("AUTH_JWT_COOKIE_NAME", "sb-access-token")
JWT_ALGORITHM = "HS256"
JWT_LEEWAY_SECONDS = _read_positive_int_env("AUTH_JWT_LEEWAY_SECONDS", 30)


class CurrentUser(BaseModel):
    """Authenticated user context resolved by the backend."""

    user_id: str = Field(..., description="Authenticated user UUID")
    role: str = Field(default="user", description="Caller role")
    auth_source: Literal["jwt", "session", "anonymous", "admin_token"] = Field(
        default="session",
        description="Source used for authentication",
    )
    claims: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw JWT claims when auth_source=jwt",
    )

    @property
    def is_admin(self) -> bool:
        return self.role.strip().lower() == "admin"


class CurrentUserResolution(BaseModel):
    """Result for resolving current user from JWT or signed session."""

    current_user: CurrentUser
    should_set_cookie: bool
    cookie_value: str | None = None


# Backward compatibility for modules importing the old type name.
CookieUserResolution = CurrentUserResolution


def _normalize_uuid(value: str) -> str | None:
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def _sign_session_payload(user_id: str, expires_ts: int) -> str:
    payload = f"{user_id}:{expires_ts}".encode("utf-8")
    return hmac.new(SESSION_SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def create_session_cookie(user_id: str, expires_ts: int | None = None) -> str:
    normalized_user_id = _normalize_uuid(user_id)
    if not normalized_user_id:
        raise ValueError("user_id must be a valid UUID")

    expiration = expires_ts or (int(time.time()) + SESSION_TTL_SECONDS)
    signature = _sign_session_payload(normalized_user_id, expiration)
    return f"{normalized_user_id}:{expiration}:{signature}"


def verify_session_cookie(cookie_value: str | None) -> CurrentUser | None:
    """Validate session signature, UUID format and expiration."""
    if not cookie_value:
        return None

    try:
        raw_user_id, raw_expires, raw_signature = cookie_value.split(":", 2)
    except ValueError:
        return None

    normalized_user_id = _normalize_uuid(raw_user_id)
    if not normalized_user_id:
        return None

    try:
        expires_ts = int(raw_expires)
    except ValueError:
        return None

    if expires_ts <= int(time.time()):
        return None

    expected_signature = _sign_session_payload(normalized_user_id, expires_ts)
    if not hmac.compare_digest(raw_signature, expected_signature):
        return None

    return CurrentUser(
        user_id=normalized_user_id,
        role="user",
        auth_source="session",
        claims={},
    )


def _extract_bearer_token(authorization_header: str | None) -> str | None:
    if not authorization_header:
        return None

    scheme, _, token = authorization_header.partition(" ")
    if scheme.strip().lower() != "bearer":
        return None

    stripped_token = token.strip()
    if not stripped_token:
        return None
    return stripped_token


def _extract_jwt_token(request: Request) -> str | None:
    header_token = _extract_bearer_token(request.headers.get("authorization"))
    if header_token:
        return header_token

    cookie_token = (request.cookies.get(JWT_COOKIE_NAME) or "").strip()
    if cookie_token:
        return cookie_token
    return None


def _base64url_decode(value: str) -> bytes:
    padded = value + ("=" * (-len(value) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _parse_timestamp(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return None
    return None


def _claims_time_window_is_valid(payload: dict[str, Any]) -> bool:
    now = int(time.time())

    exp_ts = _parse_timestamp(payload.get("exp"))
    if exp_ts is not None and now > exp_ts + JWT_LEEWAY_SECONDS:
        return False

    nbf_ts = _parse_timestamp(payload.get("nbf"))
    if nbf_ts is not None and now + JWT_LEEWAY_SECONDS < nbf_ts:
        return False

    iat_ts = _parse_timestamp(payload.get("iat"))
    if iat_ts is not None and now + JWT_LEEWAY_SECONDS < iat_ts:
        return False

    return True


def _resolve_role_from_claims(payload: dict[str, Any]) -> str:
    candidates: list[str] = []

    direct_role = payload.get("role")
    if isinstance(direct_role, str):
        candidates.append(direct_role)

    app_metadata = payload.get("app_metadata")
    if isinstance(app_metadata, dict):
        role_from_metadata = app_metadata.get("role")
        if isinstance(role_from_metadata, str):
            candidates.append(role_from_metadata)

    user_metadata = payload.get("user_metadata")
    if isinstance(user_metadata, dict):
        role_from_user_metadata = user_metadata.get("role")
        if isinstance(role_from_user_metadata, str):
            candidates.append(role_from_user_metadata)

    for role in candidates:
        normalized = role.strip().lower()
        if normalized:
            return normalized
    return "user"


def _resolve_user_id_from_claims(payload: dict[str, Any]) -> str | None:
    for key in ("sub", "user_id", "uid"):
        raw_value = payload.get(key)
        if isinstance(raw_value, str):
            normalized = _normalize_uuid(raw_value)
            if normalized:
                return normalized
    return None


def verify_jwt_token(jwt_token: str | None) -> CurrentUser | None:
    """Validate JWT HS256 signature and basic temporal claims."""
    if not jwt_token:
        return None

    secret = _resolve_jwt_secret()
    if not secret:
        _logger.warning(
            "JWT secret não configurado — token apresentado mas não pode ser verificado. "
            "Configure AUTH_JWT_SECRET, SUPABASE_JWT_SECRET ou JWT_SECRET."
        )
        return None

    parts = jwt_token.split(".")
    if len(parts) != 3:
        return None

    header_raw, payload_raw, signature_raw = parts
    signing_input = f"{header_raw}.{payload_raw}".encode("ascii")

    try:
        header = json.loads(_base64url_decode(header_raw).decode("utf-8"))
        payload = json.loads(_base64url_decode(payload_raw).decode("utf-8"))
        provided_signature = _base64url_decode(signature_raw)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return None

    if not isinstance(header, dict) or not isinstance(payload, dict):
        return None

    algorithm = str(header.get("alg") or "").upper()
    if algorithm != JWT_ALGORITHM:
        return None

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(provided_signature, expected_signature):
        return None

    if not _claims_time_window_is_valid(payload):
        return None

    user_id = _resolve_user_id_from_claims(payload)
    if not user_id:
        return None

    return CurrentUser(
        user_id=user_id,
        role=_resolve_role_from_claims(payload),
        auth_source="jwt",
        claims=payload,
    )


def resolve_current_user(request: Request) -> CurrentUserResolution:
    """Resolve user from JWT first, then signed session cookie fallback."""
    jwt_user = verify_jwt_token(_extract_jwt_token(request))
    if jwt_user:
        return CurrentUserResolution(
            current_user=jwt_user,
            should_set_cookie=False,
            cookie_value=None,
        )

    session_user = verify_session_cookie(request.cookies.get(SESSION_COOKIE_NAME))
    if session_user:
        return CurrentUserResolution(
            current_user=session_user,
            should_set_cookie=False,
            cookie_value=None,
        )

    new_user_id = str(uuid.uuid4())
    return CurrentUserResolution(
        current_user=CurrentUser(
            user_id=new_user_id,
            role="user",
            auth_source="session",
            claims={},
        ),
        should_set_cookie=True,
        cookie_value=create_session_cookie(new_user_id),
    )


def resolve_current_user_from_cookie(request: Request) -> CurrentUserResolution:
    """Backward-compatible alias for previous middleware integration."""
    return resolve_current_user(request)


def get_current_user(request: Request) -> CurrentUser:
    """Return authenticated user attached by middleware."""
    user = getattr(request.state, "current_user", None)
    if not isinstance(user, CurrentUser):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao autenticado",
        )
    return user


def require_mutation_identity(
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Require JWT identity for write operations when configured.
    Allow bypass if guest_mode is enabled (local dev/audit).
    """
    from core.config import get_settings

    # Allow bypass if guest_mode is on and header matches
    guest_header = request.headers.get("X-Guest-Access", "").lower() == "true"
    if get_settings().guest_mode and guest_header:
        return user

    if _should_require_jwt_for_mutations() and user.auth_source != "jwt":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT obrigatorio para operacoes de escrita",
        )
    return user


def _resolve_expected_admin_token() -> str | None:
    configured_token = (os.getenv("AUTH_ADMIN_TOKEN") or "").strip()
    if configured_token:
        return configured_token
    if not _is_production_environment():
        _logger.warning(
            "AUTH_ADMIN_TOKEN não configurado — autenticação admin via token desabilitada. "
            "Use JWT com role=admin ou configure AUTH_ADMIN_TOKEN."
        )
    return None


def require_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    x_admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
) -> CurrentUser:
    """Allow admin via JWT role or explicit admin token header."""
    if user.auth_source == "jwt" and user.is_admin:
        return user

    expected_token = _resolve_expected_admin_token()
    provided_token = (x_admin_token or "").strip()
    if expected_token and provided_token and hmac.compare_digest(provided_token, expected_token):
        if user.is_admin:
            return user
        return user.model_copy(update={"role": "admin"})

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acesso restrito a administradores",
    )
