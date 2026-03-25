import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from .config import get_settings

# Import metrics collector for integration
from ..monitoring.metrics import metrics_collector


class StructuredFormatter(logging.Formatter):
    """Formatador de logs estruturado em JSON."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Adicionar informações extras se existirem
        if hasattr(record, 'extra_info'):
            log_entry['extra'] = record.extra_info
        
        # Adicionar exceção se existir
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Adicionar stack trace se existir
        if record.stack_info:
            log_entry['stack_trace'] = record.stack_info
        
        return json.dumps(log_entry, ensure_ascii=False)


class PerformanceFormatter(logging.Formatter):
    """Formatador de logs de performance."""
    
    def format(self, record):
        if hasattr(record, 'performance_data'):
            perf_data = record.performance_data
            return f"[PERF] {perf_data['operation']} - {perf_data['duration']:.4f}s - {perf_data['details']}"
        return super().format(record)


class SecurityFormatter(logging.Formatter):
    """Formatador de logs de segurança."""
    
    def format(self, record):
        if hasattr(record, 'security_event'):
            sec_data = record.security_event
            return f"[SECURITY] {sec_data['event_type']} - {sec_data['details']} - IP: {sec_data.get('ip', 'unknown')}"
        return super().format(record)


class MetricsHandler(logging.Handler):
    """Handler para coletar métricas de logs."""
    
    def __init__(self):
        super().__init__()
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0
    
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            self.error_count += 1
            metrics_collector.increment_error_count()
        elif record.levelno >= logging.WARNING:
            self.warning_count += 1
        else:
            self.info_count += 1


def setup_logging():
    """Setup structured logging for the application."""
    settings = get_settings()
    
    # Converter nível de log para enum
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Remover handlers existentes
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Criar handlers
    handlers = []
    
    # Handler para console (sempre habilitado)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    handlers.append(console_handler)
    
    # Handler para arquivo
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler("logs/app.log", encoding='utf-8')
    file_handler.setFormatter(StructuredFormatter())
    handlers.append(file_handler)
    
    # Handler para logs de performance
    perf_handler = logging.FileHandler("logs/performance.log", encoding='utf-8')
    perf_handler.setFormatter(PerformanceFormatter())
    perf_handler.addFilter(lambda record: hasattr(record, 'performance_data'))
    handlers.append(perf_handler)
    
    # Handler para logs de segurança
    security_handler = logging.FileHandler("logs/security.log", encoding='utf-8')
    security_handler.setFormatter(SecurityFormatter())
    security_handler.addFilter(lambda record: hasattr(record, 'security_event'))
    handlers.append(security_handler)
    
    # Handler para métricas
    metrics_handler = MetricsHandler()
    handlers.append(metrics_handler)
    
    # Configurar root logger
    root_logger.setLevel(log_level)
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Configurar loggers específicos
    configure_specific_loggers(log_level)
    
    # Configurar captura de exceções não tratadas
    setup_exception_capture()
    
    # Configurar structlog
    setup_structlog(settings.debug)
    
    logging.info(f"Logging system configured - Level: {settings.log_level}")


def setup_structlog(debug: bool):
    """Setup structlog configuration."""
    processors: list[Any] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if debug:
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


def configure_specific_loggers(log_level: int):
    """Configura loggers específicos para diferentes componentes."""
    
    # Logger para banco de dados
    db_logger = logging.getLogger('sqlalchemy.engine')
    db_logger.setLevel(log_level)
    
    # Logger para requests HTTP
    requests_logger = logging.getLogger('urllib3')
    requests_logger.setLevel(logging.WARNING)
    
    # Logger para asyncio
    asyncio_logger = logging.getLogger('asyncio')
    asyncio_logger.setLevel(logging.WARNING)
    
    # Logger para aplicações externas
    external_loggers = [
        'urllib3.connectionpool',
        'requests',
        'boto3',
        'botocore'
    ]
    
    for logger_name in external_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)


def setup_exception_capture():
    """Configura captura de exceções não tratadas."""
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handler para exceções não tratadas."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = logging.getLogger(__name__)
        logger.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
            extra={'extra_info': {'type': 'unhandled_exception'}}
        )
    
    sys.excepthook = handle_exception


# Funções auxiliares para logging estruturado
def log_performance(operation: str, duration: float, details: str = "", **kwargs):
    """Registra log de performance."""
    logger = logging.getLogger('performance')
    logger.info(
        f"Performance: {operation}",
        extra={
            'performance_data': {
                'operation': operation,
                'duration': duration,
                'details': details,
                **kwargs
            }
        }
    )


def log_security_event(event_type: str, details: str, ip: Optional[str] = None, **kwargs):
    """Registra log de evento de segurança."""
    logger = logging.getLogger('security')
    logger.warning(
        f"Security event: {event_type}",
        extra={
            'security_event': {
                'event_type': event_type,
                'details': details,
                'ip': ip,
                **kwargs
            }
        }
    )


def log_business_event(event_type: str, details: Dict[str, Any], **kwargs):
    """Registra log de evento de negócio."""
    logger = logging.getLogger('business')
    logger.info(
        f"Business event: {event_type}",
        extra={
            'business_event': {
                'event_type': event_type,
                'details': details,
                **kwargs
            }
        }
    )


def log_api_request(method: str, endpoint: str, status_code: int, 
                   duration: float, user_id: Optional[str] = None, **kwargs):
    """Registra log de requisição API."""
    logger = logging.getLogger('api')
    logger.info(
        f"API Request: {method} {endpoint}",
        extra={
            'api_request': {
                'method': method,
                'endpoint': endpoint,
                'status_code': status_code,
                'duration': duration,
                'user_id': user_id,
                **kwargs
            }
        }
    )


def log_database_query(query: str, duration: float, table: Optional[str] = None, **kwargs):
    """Registra log de consulta ao banco de dados."""
    logger = logging.getLogger('database')
    logger.debug(
        f"Database query: {query[:100]}...",
        extra={
            'database_query': {
                'query': query,
                'duration': duration,
                'table': table,
                **kwargs
            }
        }
    )


def log_cache_operation(operation: str, key: str, hit: bool, **kwargs):
    """Registra log de operação de cache."""
    logger = logging.getLogger('cache')
    logger.debug(
        f"Cache {operation}: {key}",
        extra={
            'cache_operation': {
                'operation': operation,
                'key': key,
                'hit': hit,
                **kwargs
            }
        }
    )


# Decorador para logging de funções
def log_function_calls(logger_name: str = 'function'):
    """Decorador para registrar chamadas de funções."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.debug(
                    f"Function {func.__name__} completed",
                    extra={
                        'function_call': {
                            'function': func.__name__,
                            'duration': duration,
                            'args_count': len(args),
                            'kwargs_count': len(kwargs),
                            'result_type': type(result).__name__
                        }
                    }
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.error(
                    f"Function {func.__name__} failed",
                    exc_info=True,
                    extra={
                        'function_call': {
                            'function': func.__name__,
                            'duration': duration,
                            'error': str(e),
                            'error_type': type(e).__name__
                        }
                    }
                )
                
                raise
        
        return wrapper
    return decorator


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
