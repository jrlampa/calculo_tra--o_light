"""Application configuration using Pydantic Settings."""
from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = Field(
        ..., 
        env="DATABASE_URL",
        description="PostgreSQL connection URL"
    )
    
    # Supabase
    supabase_url: Optional[str] = Field(None, env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(None, env="SUPABASE_KEY")
    
    # Security
    secret_key: str = Field(
        ..., 
        env="SECRET_KEY",
        description="Secret key for JWT tokens"
    )
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiration: int = Field(3600, env="JWT_EXPIRATION")  # 1 hour
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # CORS
    cors_origins: list[str] = Field(
        ["http://localhost:3000", "http://localhost:5173"], 
        env="CORS_ORIGINS"
    )
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    
    # Cache
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    cache_ttl: int = Field(300, env="CACHE_TTL")  # 5 minutes
    
    # Monitoring
    monitoring_enabled: bool = Field(True, env="MONITORING_ENABLED")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    
    # Application
    app_name: str = Field("Cálculo de Tração", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    
    # File Upload
    max_file_size: int = Field(10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: list[str] = Field(
        ["image/jpeg", "image/png", "application/pdf"], 
        env="ALLOWED_FILE_TYPES"
    )
    
    # Email (for notifications)
    smtp_host: Optional[str] = Field(None, env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(True, env="SMTP_USE_TLS")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("allowed_file_types", pre=True)
    def parse_allowed_file_types(cls, v):
        """Parse allowed file types from string or list."""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        """Validate secret key is not too short."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("Database URL must be a valid PostgreSQL connection string")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def is_development() -> bool:
    """Check if running in development mode."""
    return settings.debug


def is_production() -> bool:
    """Check if running in production mode."""
    return not settings.debug


def get_database_url() -> str:
    """Get database URL."""
    return settings.database_url


def get_jwt_secret() -> str:
    """Get JWT secret key."""
    return settings.secret_key


def get_cors_origins() -> list[str]:
    """Get CORS origins."""
    return settings.cors_origins


def get_log_level() -> str:
    """Get log level."""
    return settings.log_level
