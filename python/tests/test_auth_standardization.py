"""Testes de validação do padrão de autenticação padronizado."""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Configurar variáveis ANTES de importar o app (módulo lido uma única vez)
os.environ.setdefault("AUTH_JWT_SECRET", "test_jwt_secret_key_32_characters_long")
os.environ.setdefault("AUTH_SESSION_SECRET", "test_session_secret")
os.environ.setdefault("AUTH_REQUIRE_JWT_FOR_WRITES", "true")
os.environ.setdefault("AUTH_ALLOW_SESSION_FOR_READS", "true")
os.environ.setdefault("AUTH_REQUIRE_ADMIN_ROLE", "true")
os.environ.setdefault("APP_ENV", "test")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.auth_standard import (
    get_auth_config,
    validate_auth_config,
    public_auth,
    write_auth,
    admin_auth,
    AuthenticationError,
    PublicUser,
    WriteUser,
    AdminUser,
    validate_public_endpoint,
    validate_write_endpoint,
    validate_admin_endpoint,
    log_auth_attempt,
)
from api.auth import CurrentUser


class TestAuthConfig:
    """Testes de configuração de autenticação."""
    
    def test_get_auth_config_success(self):
        """Testa a obtenção da configuração de autenticação."""
        with patch.dict(os.environ, {
            "AUTH_JWT_SECRET": "test_jwt_secret_key_32_characters_long",
            "AUTH_SESSION_SECRET": "test_session_secret",
            "AUTH_REQUIRE_JWT_FOR_WRITES": "true",
            "AUTH_ALLOW_SESSION_FOR_READS": "true",
            "AUTH_REQUIRE_ADMIN_ROLE": "true",
            "APP_ENV": "test",
        }, clear=False):
            config = get_auth_config()
        
        assert config.jwt_secret == "test_jwt_secret_key_32_characters_long"
        assert config.session_secret == "test_session_secret"
        assert config.require_jwt_for_writes is True
        assert config.allow_session_for_reads is True
        assert config.require_admin_role is True
        assert config.environment == "test"
        assert config.is_production is False
    
    def test_get_auth_config_missing_jwt_secret(self):
        """Testa erro quando JWT secret não está configurado."""
        with patch.dict(os.environ, {"AUTH_JWT_SECRET": ""}, clear=False):
            with pytest.raises(ValueError, match="AUTH_JWT_SECRET deve ser definido"):
                get_auth_config()
    
    def test_get_auth_config_production_missing_session_secret(self):
        """Testa erro quando session secret não está configurado em produção."""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "AUTH_SESSION_SECRET": ""
        }, clear=False):
            with pytest.raises(ValueError, match="AUTH_SESSION_SECRET deve ser definido em produção"):
                get_auth_config()
    
    def test_validate_auth_config_success(self):
        """Testa a validação da configuração de autenticação."""
        with patch.dict(os.environ, {
            "AUTH_JWT_SECRET": "test_jwt_secret_key_32_characters_long",
            "AUTH_SESSION_SECRET": "test_session_secret",
            "AUTH_REQUIRE_JWT_FOR_WRITES": "true",
            "AUTH_ALLOW_SESSION_FOR_READS": "true",
            "AUTH_REQUIRE_ADMIN_ROLE": "true",
            "APP_ENV": "test",
        }, clear=False):
            config = validate_auth_config()
        
        assert config.jwt_secret == "test_jwt_secret_key_32_characters_long"
        assert config.environment == "test"
        assert config.require_jwt_for_writes is True


class TestPublicAuth:
    """Testes de autenticação pública."""
    
    def test_public_auth_jwt_success(self):
        """Testa autenticação pública com JWT válido."""
        from fastapi import Request
        from starlette.datastructures import Headers
        
        # Mock JWT verification
        with patch('api.auth_standard.verify_jwt_token') as mock_verify:
            mock_verify.return_value = CurrentUser(
                user_id="test_user",
                role="user",
                auth_source="jwt",
                claims={}
            )
            
            request = Request(scope={
                "type": "http",
                "method": "GET",
                "headers": Headers({"authorization": "Bearer test_token"}).items()
            })
            
            user = public_auth(request)
            
            assert user.user_id == "test_user"
            assert user.auth_source == "jwt"
            mock_verify.assert_called_once_with("test_token")
    
    def test_public_auth_session_success(self):
        """Testa autenticação pública com sessão válida."""
        from fastapi import Request
        from starlette.datastructures import Headers
        
        # Mock session verification
        with patch('api.auth_standard.verify_session_cookie') as mock_verify:
            mock_verify.return_value = CurrentUser(
                user_id="test_user",
                role="user",
                auth_source="session",
                claims={}
            )
            
            request = Request(scope={
                "type": "http",
                "method": "GET",
                "headers": Headers({}).items(),
                "cookies": {"calc_session": "test_session_cookie"}
            })
            
            user = public_auth(request)
            
            assert user.user_id == "test_user"
            assert user.auth_source == "session"
            mock_verify.assert_called_once_with("test_session_cookie")
    
    def test_public_auth_anonymous(self):
        """Testa autenticação pública anônima."""
        from fastapi import Request
        from starlette.datastructures import Headers
        
        request = Request(scope={
            "type": "http",
            "method": "GET",
            "headers": Headers({}).items(),
            "cookies": {}
        })
        
        user = public_auth(request)
        
        assert user.user_id == "anonymous"
        assert user.auth_source == "anonymous"
        assert user.role == "anonymous"


class TestWriteAuth:
    """Testes de autenticação para escrita."""
    
    def test_write_auth_jwt_success_production(self):
        """Testa autenticação de escrita com JWT em produção."""
        from fastapi import Request
        from starlette.datastructures import Headers
        
        with patch.dict(os.environ, {"APP_ENV": "production"}):
            with patch('api.auth_standard.verify_jwt_token') as mock_verify:
                mock_verify.return_value = CurrentUser(
                    user_id="test_user",
                    role="user",
                    auth_source="jwt",
                    claims={}
                )
                
                request = Request(scope={
                    "type": "http",
                    "method": "POST",
                    "headers": Headers({"authorization": "Bearer test_token"}).items()
                })
                
                user = write_auth(request)
                
                assert user.user_id == "test_user"
                assert user.auth_source == "jwt"
    
    def test_write_auth_jwt_success_development(self):
        """Testa autenticação de escrita com JWT em desenvolvimento."""
        from fastapi import Request
        from starlette.datastructures import Headers
        
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            with patch('api.auth_standard.verify_jwt_token') as mock_verify:
                mock_verify.return_value = CurrentUser(
                    user_id="test_user",
                    role="user",
                    auth_source="jwt",
                    claims={}
                )
                
                request = Request(scope={
                    "type": "http",
                    "method": "POST",
                    "headers": Headers({"authorization": "Bearer test_token"}).items()
                })
                
                user = write_auth(request)
                
                assert user.user_id == "test_user"
                assert user.auth_source == "jwt"
    
    def test_write_auth_session_fallback_development(self):
        """Testa fallback para sessão em desenvolvimento."""
        from fastapi import Request
        from starlette.datastructures import Headers
        
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            with patch('api.auth_standard.verify_jwt_token') as mock_jwt:
                with patch('api.auth_standard.verify_session_cookie') as mock_session:
                    mock_jwt.return_value = None
                    mock_session.return_value = CurrentUser(
                        user_id="test_user",
                        role="user",
                        auth_source="session",
                        claims={}
                    )
                    
                    request = Request(scope={
                        "type": "http",
                        "method": "POST",
                        "headers": Headers({}).items(),
                        "cookies": {"calc_session": "test_session"}
                    })
                    
                    user = write_auth(request)
                    
                    assert user.user_id == "test_user"
                    assert user.auth_source == "session"
    
    def test_write_auth_failed_production(self):
        """Testa falha de autenticação de escrita em produção."""
        from fastapi import Request
        from starlette.datastructures import Headers
        
        with patch.dict(os.environ, {"APP_ENV": "production"}):
            with patch('api.auth_standard.verify_jwt_token') as mock_jwt:
                mock_jwt.return_value = None
                
                request = Request(scope={
                    "type": "http",
                    "method": "POST",
                    "headers": Headers({}).items()
                })
                
                with pytest.raises(HTTPException) as exc_info:
                    write_auth(request)
                
                assert exc_info.value.status_code == 401
                assert "JWT obrigatório para operações de escrita" in str(exc_info.value.detail)
    
    def test_write_auth_failed_development(self):
        """Testa falha de autenticação de escrita em desenvolvimento."""
        from fastapi import Request
        from starlette.datastructures import Headers
        
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            with patch('api.auth_standard.verify_jwt_token') as mock_jwt:
                with patch('api.auth_standard.verify_session_cookie') as mock_session:
                    mock_jwt.return_value = None
                    mock_session.return_value = None
                    
                    request = Request(scope={
                        "type": "http",
                        "method": "POST",
                        "headers": Headers({}).items()
                    })
                    
                    with pytest.raises(HTTPException) as exc_info:
                        write_auth(request)
                    
                    assert exc_info.value.status_code == 401
                    assert "Autenticação necessária para operações de escrita" in str(exc_info.value.detail)


class TestAdminAuth:
    """Testes de autenticação administrativa."""
    
    def test_admin_auth_jwt_success(self):
        """Testa autenticação admin com JWT válido."""
        from fastapi import Request
        from starlette.datastructures import Headers
        
        with patch('api.auth_standard.get_current_user') as mock_get_user:
            mock_get_user.return_value = CurrentUser(
                user_id="admin_user",
                role="admin",
                auth_source="jwt",
                claims={}
            )
            
            request = Request(scope={
                "type": "http",
                "method": "GET",
                "headers": Headers({}).items()
            })
            
            user = admin_auth(request)
            
            assert user.user_id == "admin_user"
            assert user.role == "admin"
            assert user.auth_source == "jwt"
    
    def test_admin_auth_token_fallback(self):
        """Testa fallback para token admin."""
        from fastapi import Request
        from starlette.datastructures import Headers
        
        with patch('api.auth_standard.get_current_user') as mock_get_user:
            with patch.dict(os.environ, {"AUTH_ADMIN_TOKEN": "test_admin_token"}):
                mock_get_user.side_effect = HTTPException(status_code=401)
                
                request = Request(scope={
                    "type": "http",
                    "method": "GET",
                    "headers": Headers({"X-Admin-Token": "test_admin_token"}).items()
                })
                
                user = admin_auth(request)
                
                assert user.user_id == "admin_token_user"
                assert user.role == "admin"
                assert user.auth_source == "admin_token"
    
    def test_admin_auth_failed(self):
        """Testa falha de autenticação admin."""
        from fastapi import Request
        from starlette.datastructures import Headers
        
        with patch('api.auth_standard.get_current_user') as mock_get_user:
            with patch.dict(os.environ, {"AUTH_ADMIN_TOKEN": "test_admin_token"}):
                mock_get_user.side_effect = HTTPException(status_code=401)
                
                request = Request(scope={
                    "type": "http",
                    "method": "GET",
                    "headers": Headers({"X-Admin-Token": "wrong_token"}).items()
                })
                
                with pytest.raises(HTTPException) as exc_info:
                    admin_auth(request)
                
                assert exc_info.value.status_code == 403
                assert "Acesso restrito a administradores" in str(exc_info.value.detail)


class TestValidationFunctions:
    """Testes de funções de validação."""
    
    def test_validate_public_endpoint(self):
        """Testa validação de endpoint público."""
        config_mock = MagicMock()
        config_mock.allow_session_for_reads = True
        
        with patch('api.auth_standard.get_auth_config', return_value=config_mock):
            # Usuário autenticado
            user_authenticated = CurrentUser(
                user_id="test_user",
                role="user",
                auth_source="jwt",
                claims={}
            )
            assert validate_public_endpoint(user_authenticated) is True
            
            # Usuário anônimo com sessões permitidas
            user_anonymous = CurrentUser(
                user_id="anonymous",
                role="anonymous",
                auth_source="anonymous",
                claims={}
            )
            assert validate_public_endpoint(user_anonymous) is True
    
    def test_validate_write_endpoint_production(self):
        """Testa validação de endpoint de escrita em produção."""
        config_mock = MagicMock()
        config_mock.is_production = True
        
        with patch('api.auth_standard.get_auth_config', return_value=config_mock):
            # JWT em produção
            user_jwt = CurrentUser(
                user_id="test_user",
                role="user",
                auth_source="jwt",
                claims={}
            )
            assert validate_write_endpoint(user_jwt) is True
            
            # Sessão em produção (deve falhar)
            user_session = CurrentUser(
                user_id="test_user",
                role="user",
                auth_source="session",
                claims={}
            )
            assert validate_write_endpoint(user_session) is False
    
    def test_validate_write_endpoint_development(self):
        """Testa validação de endpoint de escrita em desenvolvimento."""
        config_mock = MagicMock()
        config_mock.is_production = False
        
        with patch('api.auth_standard.get_auth_config', return_value=config_mock):
            # Usuário autenticado
            user_authenticated = CurrentUser(
                user_id="test_user",
                role="user",
                auth_source="jwt",
                claims={}
            )
            assert validate_write_endpoint(user_authenticated) is True
            
            # Usuário anônimo (deve falhar)
            user_anonymous = CurrentUser(
                user_id="anonymous",
                role="anonymous",
                auth_source="anonymous",
                claims={}
            )
            assert validate_write_endpoint(user_anonymous) is False
    
    def test_validate_admin_endpoint(self):
        """Testa validação de endpoint administrativo."""
        # Usuário admin
        user_admin = CurrentUser(
            user_id="admin_user",
            role="admin",
            auth_source="jwt",
            claims={}
        )
        assert validate_admin_endpoint(user_admin) is True
        
        # Usuário não admin
        user_regular = CurrentUser(
            user_id="regular_user",
            role="user",
            auth_source="jwt",
            claims={}
        )
        assert validate_admin_endpoint(user_regular) is False


class TestLogAuthAttempt:
    """Testes de auditoria de autenticação."""
    
    def test_log_auth_attempt(self):
        """Testa o registro de tentativas de autenticação."""
        with patch('api.auth_standard.logger') as mock_logger:
            user = CurrentUser(
                user_id="test_user",
                role="user",
                auth_source="jwt",
                claims={}
            )
            
            log_auth_attempt(
                endpoint="/api/test",
                user=user,
                success=True,
                auth_type="write"
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "auth_attempt"
            assert call_args[1]["endpoint"] == "/api/test"
            assert call_args[1]["user_id"] == "test_user"
            assert call_args[1]["success"] is True
            assert call_args[1]["auth_type"] == "write"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])