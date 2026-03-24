import logging
import sys
from typing import Any

import structlog
from .config import get_settings

def setup_logging():
    """Setup structured logging for the application."""
    settings = get_settings()
    
    # Standard Python logging configuration
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log")
        ],
        level=getattr(logging, settings.log_level.upper()),
    )

    # Structlog configuration
    processors: list[Any] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.debug:
        # Development: Human-readable PrettyPrint
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # Production: Structured JSON
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
