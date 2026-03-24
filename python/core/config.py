from __future__ import annotations

import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database
    database_url: str = Field(
        default="postgresql://test:test@localhost:5432/test_calculo_tracao",
        description="PostgreSQL connection URL"
    )
    
    # Supabase
    supabase_url: str = Field(
        default="https://test.supabase.co",
        description="Supabase project URL"
    )
    supabase_key: str = Field(
        default="test_key_12345678901234567890",
        description="Supabase public key"
    )
    
    # Security
    secret_key: str = Field(
        default="test_secret_key_32_characters_long_minimum",
        min_length=32,
        description="Secret key for JWT tokens"
    )
    jwt_algorithm: str = Field(
        "HS256",
        description="JWT algorithm"
    )
    jwt_expiration: int = Field(
        3600,
        description="JWT token expiration in seconds"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(
        60,
        description="Rate limit per minute"
    )
    rate_limit_per_hour: int = Field(
        1000,
        description="Rate limit per hour"
    )
    
    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="CORS allowed origins"
    )
    
    # Logging
    log_level: str = Field(
        "INFO",
        description="Logging level"
    )
    
    # Cache
    cache_ttl: int = Field(
        300,
        description="Cache TTL in seconds"
    )
    
    # Monitoring
    enable_metrics: bool = Field(
        False,
        description="Enable metrics collection"
    )
    
    # App Info
    app_name: str = Field(
        "Cálculo de Tração",
        description="Application name"
    )
    app_version: str = Field(
        "2.0.0",
        description="Application version"
    )
    debug: bool = Field(
        False,
        description="Debug mode"
    )
    guest_mode: bool = Field(
        False,
        description="Enable guest mode for local development/audits"
    )
    
    # File Upload
    max_file_size: int = Field(
        10 * 1024 * 1024,
        description="Maximum file size in bytes (10MB)"
    )
    allowed_file_types: list[str] = Field(
        default=[".pdf", ".doc", ".docx", ".txt", ".csv"],
        description="Allowed file types"
    )
    
    # Email
    smtp_host: Optional[str] = Field(
        default=None,
        description="SMTP host"
    )
    smtp_port: int = Field(
        587,
        description="SMTP port"
    )
    smtp_username: Optional[str] = Field(
        default=None,
        description="SMTP username"
    )
    smtp_password: Optional[str] = Field(
        default=None,
        description="SMTP password"
    )
    smtp_use_tls: bool = Field(
        True,
        description="Use TLS for SMTP"
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def parse_allowed_file_types(cls, v):
        """Parse allowed file types from string or list."""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        """Validate secret key."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        return v
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL."""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("Database URL must start with postgresql://")
        return v


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings


def get_database_url() -> str:
    """Get database URL."""
    return get_settings().database_url


def get_jwt_secret() -> str:
    """Get JWT secret key."""
    return get_settings().secret_key


def get_cors_origins() -> list[str]:
    """Get CORS origins."""
    return get_settings().cors_origins


def get_log_level() -> str:
    """Get log level."""
    return get_settings().log_level
