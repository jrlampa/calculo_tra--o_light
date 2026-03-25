# The above code defines custom exception classes for different error scenarios in an application.
"""Custom exceptions for the application."""
from __future__ import annotations


class BaseAppException(Exception):
    """Base exception for the application."""

    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(BaseAppException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "NOT_FOUND")


class PermissionError(BaseAppException):
    """Exception raised when user lacks permission."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, "PERMISSION_DENIED")


class ValidationError(BaseAppException):
    """Exception raised when validation fails."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR")


class DatabaseError(BaseAppException):
    """Exception raised when database operation fails."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DATABASE_ERROR")


class AuthenticationError(BaseAppException):
    """Exception raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class RateLimitError(BaseAppException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")


class ConfigurationError(BaseAppException):
    """Exception raised when configuration is invalid."""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, "CONFIGURATION_ERROR")


class ExternalServiceError(BaseAppException):
    """Exception raised when external service call fails."""

    def __init__(self, message: str = "External service error"):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
