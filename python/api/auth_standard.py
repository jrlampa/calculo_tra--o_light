"""Padrão de autenticação padronizado para endpoints críticos.
    
    This Python module defines a standardized authentication pattern for critical endpoints, ensuring
    consistent authentication across environments.
    
    :param request: The `request` parameter in the context of FastAPI represents the incoming HTTP
    request made to your API endpoint. It contains information such as headers, cookies, query
    parameters, and more that are sent by the client making the request. In your code, you are using the
    `Request` class from Fast
    :type request: Request
    :param name: The code you provided is a standardized authentication pattern for critical endpoints
    in a FastAPI application. It defines a set of functions and classes to handle authentication logic,
    including JWT verification, session handling, and role-based access control
    :type name: str
    :return: The code provided defines a standardized authentication pattern for critical endpoints in a
    FastAPI application. It includes functions for different types of authentication (public, write,
    admin), validation functions for endpoint access, logging authentication attempts, and compatibility
    functions with existing dependencies.
    

Este módulo define o padrão único de autenticação que deve ser usado
por todos os endpoints, eliminando variantes por ambiente e reduzindo
ambiguidade operacional.
"""


import os
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel

from api.auth import (
    CurrentUser,
    get_current_user,
    require_admin,
    require_mutation_identity,
    verify_jwt_token,
    verify_session_cookie,
)

import structlog

logger = structlog.get_logger(__name__)


def _get_header(request: Request, name: str) -> str | None:
    """Read header from regular request headers or non-standard test scopes."""
    value = request.headers.get(name)
    if value:
        return value

    for pair in request.scope.get("headers", []):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            continue
        key, raw_value = pair
        if isinstance(key, bytes):
            key = key.decode("latin-1")
        if isinstance(raw_value, bytes):
            raw_value = raw_value.decode("latin-1")
        if isinstance(key, str) and key.lower() == name.lower():
            return raw_value if isinstance(raw_value, str) else None
    return None


def _get_cookie(request: Request, cookie_name: str) -> str | None:
    """Read cookie from parsed cookie header or non-standard test scopes."""
    value = request.cookies.get(cookie_name)
    if value:
        return value

    raw_cookies = request.scope.get("cookies")
    if isinstance(raw_cookies, dict):
        cookie_value = raw_cookies.get(cookie_name)
        if isinstance(cookie_value, str) and cookie_value:
            return cookie_value
    return None


class AuthConfig(BaseModel):
    """Configuração padronizada de autenticação."""
    
    # JWT Configuration
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_leeway_seconds: int = 30
    
    # Session Configuration  
    session_secret: str
    session_ttl_seconds: int = 86400
    session_cookie_name: str = "calc_session"
    
    # Authentication Rules
    require_jwt_for_writes: bool = True
    allow_session_for_reads: bool = True
    require_admin_role: bool = True
    
    # Environment
    environment: str = "development"
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em ambiente de produção."""
        return self.environment.lower() in ["prod", "production"]


def get_auth_config() -> AuthConfig:
    """Obtém a configuração padronizada de autenticação."""
    # JWT Secret - única variável padronizada
    jwt_secret = os.getenv("AUTH_JWT_SECRET")
    if not jwt_secret:
        raise ValueError("AUTH_JWT_SECRET deve ser definido")
    
    # Session Secret - única variável padronizada
    session_secret = os.getenv("AUTH_SESSION_SECRET")
    if not session_secret:
        if os.getenv("APP_ENV", "").lower() in ["prod", "production"]:
            raise ValueError("AUTH_SESSION_SECRET deve ser definido em produção")
        session_secret = "development_session_secret_change_in_production"
    
    return AuthConfig(
        jwt_secret=jwt_secret,
        session_secret=session_secret,
        require_jwt_for_writes=os.getenv("AUTH_REQUIRE_JWT_FOR_WRITES", "true").lower() == "true",
        allow_session_for_reads=os.getenv("AUTH_ALLOW_SESSION_FOR_READS", "true").lower() == "true",
        require_admin_role=os.getenv("AUTH_REQUIRE_ADMIN_ROLE", "true").lower() == "true",
        environment=os.getenv("APP_ENV", "development"),
    )


class AuthenticationError(Exception):
    """Exceção para erros de autenticação padronizados."""
    
    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


def validate_auth_config():
    """Valida a configuração de autenticação no startup."""
    try:
        config = get_auth_config()
        
        # Logs de auditoria da configuração
        logger.info(f"auth_config_validated - Env: {config.environment}, JWT: {config.require_jwt_for_writes}, Session: {config.allow_session_for_reads}, Prod: {config.is_production}")
        
        return config
    except Exception as e:
        logger.error(f"auth_config_validation_failed: {e}")
        raise AuthenticationError(f"Configuração de autenticação inválida: {str(e)}")


# Padrões de autenticação por tipo de endpoint

def public_auth(request: Request) -> CurrentUser:
    """Autenticação para endpoints públicos (leitura).
    
    Permite acesso anônimo, mas tenta autenticar se houver credenciais.
    """
    config = get_auth_config()
    
    # Verificar JWT primeiro
    jwt_token = None
    auth_header = _get_header(request, "authorization")
    if auth_header and auth_header.startswith("Bearer "):
        jwt_token = auth_header[7:]
    
    jwt_user = verify_jwt_token(jwt_token) if jwt_token else None
    if jwt_user:
        logger.info("public_auth_jwt_success", user_id=jwt_user.user_id)
        return jwt_user
    
    # Verificar sessão se permitido
    if config.allow_session_for_reads:
        session_cookie = _get_cookie(request, config.session_cookie_name)
        session_user = verify_session_cookie(session_cookie) if session_cookie else None
        if session_user:
            logger.info("public_auth_session_success", user_id=session_user.user_id)
            return session_user
    
    # Acesso anônimo
    logger.info("public_auth_anonymous")
    return CurrentUser(
        user_id="anonymous",
        role="anonymous",
        auth_source="anonymous",
        claims={}
    )


def write_auth(request: Request) -> CurrentUser:
    """Autenticação para endpoints de escrita.
    
    Exige JWT em produção, permite fallback para sessão em desenvolvimento.
    """
    config = get_auth_config()
    
    # Verificar JWT
    jwt_token = None
    auth_header = _get_header(request, "authorization")
    if auth_header and auth_header.startswith("Bearer "):
        jwt_token = auth_header[7:]
    
    jwt_user = verify_jwt_token(jwt_token) if jwt_token else None
    if jwt_user:
        logger.info("write_auth_jwt_success", user_id=jwt_user.user_id)
        return jwt_user
    
    # Fallback para sessão apenas em desenvolvimento
    if not config.is_production and config.allow_session_for_reads:
        session_cookie = _get_cookie(request, config.session_cookie_name)
        session_user = verify_session_cookie(session_cookie) if session_cookie else None
        if session_user:
            logger.warning("write_auth_session_fallback", user_id=session_user.user_id)
            return session_user
    
    # Falha de autenticação
    logger.warning("write_auth_failed", 
                  environment=config.environment,
                  require_jwt=config.require_jwt_for_writes)
    
    if config.is_production:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "JWT obrigatório para operações de escrita",
                "code": "JWT_REQUIRED",
                "environment": "production"
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Autenticação necessária para operações de escrita",
                "code": "AUTH_REQUIRED",
                "environment": config.environment
            }
        )


def admin_auth(request: Request) -> CurrentUser:
    """Autenticação para endpoints administrativos.
    
    Exige JWT com role=admin ou token admin.
    """
    config = get_auth_config()
    
    # Primeiro tenta autenticação normal
    try:
        user = get_current_user(request)
        if user.is_admin:
            logger.info("admin_auth_jwt_success", user_id=user.user_id)
            return user
    except HTTPException:
        pass
    
    # Verifica token admin
    admin_token = _get_header(request, "X-Admin-Token")
    expected_admin_token = os.getenv("AUTH_ADMIN_TOKEN")
    
    if expected_admin_token and admin_token:
        import hmac
        if hmac.compare_digest(admin_token, expected_admin_token):
            logger.warning("admin_auth_token_fallback", 
                          user_id="admin_token_user")
            return CurrentUser(
                user_id="admin_token_user",
                role="admin",
                auth_source="admin_token",
                claims={}
            )
    
    # Falha de autenticação admin
    logger.warning("admin_auth_failed", 
                  environment=config.environment)
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": "Acesso restrito a administradores",
            "code": "ADMIN_REQUIRED",
            "environment": config.environment
        }
    )


# Dependências padronizadas para uso nos routers

PublicUser = Annotated[CurrentUser, Depends(public_auth)]
WriteUser = Annotated[CurrentUser, Depends(write_auth)]
AdminUser = Annotated[CurrentUser, Depends(admin_auth)]


# Funções de validação de endpoint

def validate_public_endpoint(user: CurrentUser) -> bool:
    """Valida se o usuário pode acessar endpoints públicos."""
    return user.user_id != "anonymous" or get_auth_config().allow_session_for_reads


def validate_write_endpoint(user: CurrentUser) -> bool:
    """Valida se o usuário pode acessar endpoints de escrita."""
    config = get_auth_config()
    if config.is_production:
        return user.auth_source == "jwt"
    return user.user_id != "anonymous"


def validate_admin_endpoint(user: CurrentUser) -> bool:
    """Valida se o usuário pode acessar endpoints administrativos."""
    return user.is_admin


# Auditoria de autenticação

def log_auth_attempt(
    endpoint: str,
    user: CurrentUser,
    success: bool,
    auth_type: Literal["public", "write", "admin"]
):
    """Registra tentativas de autenticação para auditoria."""
    logger.info("auth_attempt", 
               endpoint=endpoint,
               user_id=user.user_id,
               auth_source=user.auth_source,
               role=user.role,
               success=success,
               auth_type=auth_type,
               timestamp=datetime.now(UTC).isoformat())


# Compatibilidade com dependências existentes

def require_mutation_identity_standard(
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)]
) -> CurrentUser:
    """Versão padronizada do require_mutation_identity."""
    config = get_auth_config()
    
    if config.require_jwt_for_writes and user.auth_source != "jwt":
        if config.is_production:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": "JWT obrigatório para operações de escrita",
                    "code": "JWT_REQUIRED",
                    "environment": "production"
                }
            )
        else:
            logger.warning("mutation_identity_session_fallback", 
                          user_id=user.user_id,
                          environment=config.environment)
    
    return user


def require_admin_standard(
    user: Annotated[CurrentUser, Depends(get_current_user)]
) -> CurrentUser:
    """Versão padronizada do require_admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Acesso restrito a administradores",
                "code": "ADMIN_REQUIRED",
                "environment": get_auth_config().environment
            }
        )
    return user