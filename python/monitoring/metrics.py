"""
Sistema de monitoramento e métricas para o projeto calculo_tração_light.
Este módulo fornece coleta de métricas de performance, uso de recursos e saúde da aplicação.
"""

import time
import logging
import psutil
import asyncio
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """Métricas do sistema."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int


@dataclass
class ApplicationMetrics:
    """Métricas da aplicação."""
    timestamp: str
    request_count: int
    request_duration_avg: float
    request_duration_max: float
    error_count: int
    active_connections: int
    database_queries: int
    cache_hits: int
    cache_misses: int


@dataclass
class DatabaseMetrics:
    """Métricas do banco de dados."""
    timestamp: str
    connection_pool_size: int
    active_connections: int
    idle_connections: int
    query_count: int
    slow_queries: int
    avg_query_time: float
    max_query_time: float


class MetricsCollector:
    """Coletor de métricas do sistema."""
    
    def __init__(self, metrics_file: str = "metrics.jsonl"):
        self.metrics_file = metrics_file
        self.system_metrics_history: list[SystemMetrics] = []
        self.app_metrics_history: list[ApplicationMetrics] = []
        self.db_metrics_history: list[DatabaseMetrics] = []
        
        # Contadores de aplicação
        self.request_count = 0
        self.request_durations: list[float] = []
        self.error_count = 0
        self.active_connections = 0
        self.database_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Contadores de banco de dados
        self.db_connection_pool_size = 0
        self.db_active_connections = 0
        self.db_idle_connections = 0
        self.db_query_count = 0
        self.db_slow_queries = 0
        self.db_query_times: list[float] = []
        
        # Configuração de coleta
        self.collection_interval = 30  # segundos
        self.max_history_size = 1000
        
        logger.info("Metrics collector initialized")
    
    async def start_collection(self):
        """Inicia a coleta de métricas em background."""
        logger.info(f"Starting metrics collection every {self.collection_interval}s")
        while True:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(5)  # Esperar 5s antes de tentar novamente
    
    async def collect_all_metrics(self):
        """Coleta todas as métricas disponíveis."""
        # Coletar métricas do sistema
        system_metrics = await self.collect_system_metrics()
        self.system_metrics_history.append(system_metrics)
        
        # Coletar métricas da aplicação
        app_metrics = await self.collect_application_metrics()
        self.app_metrics_history.append(app_metrics)
        
        # Coletar métricas do banco de dados
        db_metrics = await self.collect_database_metrics()
        self.db_metrics_history.append(db_metrics)
        
        # Manter tamanho máximo do histórico
        self._trim_history()
        
        # Salvar métricas em arquivo
        await self._save_metrics_to_file(system_metrics, app_metrics, db_metrics)
        
        logger.debug("Metrics collected successfully")
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Coleta métricas do sistema operacional."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memória
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_total_mb = memory.total / (1024 * 1024)
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # Rede
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_total_mb=memory_total_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_total_mb=0.0,
                disk_usage_percent=0.0,
                disk_free_gb=0.0,
                network_bytes_sent=0,
                network_bytes_recv=0
            )
    
    async def collect_application_metrics(self) -> ApplicationMetrics:
        """Coleta métricas da aplicação."""
        # Calcular estatísticas de requests
        if self.request_durations:
            avg_duration = sum(self.request_durations) / len(self.request_durations)
            max_duration = max(self.request_durations)
        else:
            avg_duration = 0.0
            max_duration = 0.0
        
        metrics = ApplicationMetrics(
            timestamp=datetime.now().isoformat(),
            request_count=self.request_count,
            request_duration_avg=avg_duration,
            request_duration_max=max_duration,
            error_count=self.error_count,
            active_connections=self.active_connections,
            database_queries=self.database_queries,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses
        )
        
        # Resetar contadores de request para o próximo período
        self.request_durations.clear()
        
        return metrics
    
    async def collect_database_metrics(self) -> DatabaseMetrics:
        """Coleta métricas do banco de dados."""
        # Calcular estatísticas de queries
        if self.db_query_times:
            avg_query_time = sum(self.db_query_times) / len(self.db_query_times)
            max_query_time = max(self.db_query_times)
        else:
            avg_query_time = 0.0
            max_query_time = 0.0
        
        metrics = DatabaseMetrics(
            timestamp=datetime.now().isoformat(),
            connection_pool_size=self.db_connection_pool_size,
            active_connections=self.db_active_connections,
            idle_connections=self.db_idle_connections,
            query_count=self.db_query_count,
            slow_queries=self.db_slow_queries,
            avg_query_time=avg_query_time,
            max_query_time=max_query_time
        )
        
        # Resetar contadores de queries para o próximo período
        self.db_query_times.clear()
        
        return metrics
    
    def _trim_history(self):
        """Mantém o histórico dentro do limite de tamanho."""
        if len(self.system_metrics_history) > self.max_history_size:
            self.system_metrics_history = self.system_metrics_history[-self.max_history_size:]
        
        if len(self.app_metrics_history) > self.max_history_size:
            self.app_metrics_history = self.app_metrics_history[-self.max_history_size:]
        
        if len(self.db_metrics_history) > self.max_history_size:
            self.db_metrics_history = self.db_metrics_history[-self.max_history_size:]
    
    async def _save_metrics_to_file(self, system_metrics: SystemMetrics, 
                                   app_metrics: ApplicationMetrics, 
                                   db_metrics: DatabaseMetrics):
        """Salva métricas em arquivo JSONL."""
        try:
            metrics_data = {
                "timestamp": datetime.now().isoformat(),
                "system": asdict(system_metrics),
                "application": asdict(app_metrics),
                "database": asdict(db_metrics)
            }
            
            with open(self.metrics_file, 'a') as f:
                f.write(json.dumps(metrics_data) + '\n')
                
        except Exception as e:
            logger.error(f"Error saving metrics to file: {e}")
    
    # Métodos para atualizar contadores da aplicação
    def increment_request_count(self, duration: float):
        """Incrementa contador de requests."""
        self.request_count += 1
        self.request_durations.append(duration)
    
    def increment_error_count(self):
        """Incrementa contador de erros."""
        self.error_count += 1
    
    def set_active_connections(self, count: int):
        """Define número de conexões ativas."""
        self.active_connections = count
    
    def increment_database_queries(self, duration: float, is_slow: bool = False):
        """Incrementa contador de queries do banco de dados."""
        self.database_queries += 1
        self.db_query_times.append(duration)
        if is_slow:
            self.db_slow_queries += 1
    
    def increment_cache_hits(self):
        """Incrementa contador de cache hits."""
        self.cache_hits += 1
    
    def increment_cache_misses(self):
        """Incrementa contador de cache misses."""
        self.cache_misses += 1
    
    # Métodos para atualizar contadores do banco de dados
    def set_db_connection_pool_size(self, size: int):
        """Define tamanho do pool de conexões."""
        self.db_connection_pool_size = size
    
    def set_db_connections(self, active: int, idle: int):
        """Define número de conexões ativas e idle."""
        self.db_active_connections = active
        self.db_idle_connections = idle
    
    def get_latest_metrics(self) -> Dict[str, Any]:
        """Retorna as métricas mais recentes."""
        return {
            "system": asdict(self.system_metrics_history[-1]) if self.system_metrics_history else None,
            "application": asdict(self.app_metrics_history[-1]) if self.app_metrics_history else None,
            "database": asdict(self.db_metrics_history[-1]) if self.db_metrics_history else None
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna um resumo das métricas."""
        if not self.system_metrics_history:
            return {"error": "No metrics collected yet"}
        
        latest_system = self.system_metrics_history[-1]
        latest_app = self.app_metrics_history[-1] if self.app_metrics_history else None
        latest_db = self.db_metrics_history[-1] if self.db_metrics_history else None
        
        return {
            "last_update": latest_system.timestamp,
            "system": {
                "cpu_percent": latest_system.cpu_percent,
                "memory_percent": latest_system.memory_percent,
                "disk_usage_percent": latest_system.disk_usage_percent
            },
            "application": {
                "request_count": latest_app.request_count if latest_app else 0,
                "error_count": latest_app.error_count if latest_app else 0,
                "active_connections": latest_app.active_connections if latest_app else 0
            } if latest_app else None,
            "database": {
                "active_connections": latest_db.active_connections if latest_db else 0,
                "query_count": latest_db.query_count if latest_db else 0,
                "slow_queries": latest_db.slow_queries if latest_db else 0
            } if latest_db else None
        }


# Decorador para monitorar performance de funções
def monitor_performance(func: Callable) -> Callable:
    """Decorador para monitorar performance de funções."""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Registrar métricas (assumindo que o coletor está disponível globalmente)
            if hasattr(wrapper, '_metrics_collector'):
                wrapper._metrics_collector.increment_request_count(duration)
            
            logger.debug(f"{func.__name__} completed in {duration:.4f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            if hasattr(wrapper, '_metrics_collector'):
                wrapper._metrics_collector.increment_error_count()
            
            logger.error(f"{func.__name__} failed after {duration:.4f}s: {e}")
            raise
    
    return wrapper


# Instância global do coletor de métricas
metrics_collector = MetricsCollector()


def setup_monitoring():
    """Configura o sistema de monitoramento."""
    # Iniciar coleta de métricas em background
    asyncio.create_task(metrics_collector.start_collection())
    logger.info("Monitoring system setup completed")


# Função para obter métricas via API (para integração com endpoints)
async def get_metrics_for_api():
    """Retorna métricas formatadas para API."""
    return metrics_collector.get_metrics_summary()