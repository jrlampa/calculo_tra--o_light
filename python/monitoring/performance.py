"""Performance monitoring and metrics collection."""
from __future__ import annotations

import time
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

import psutil
from fastapi import Request, Response
from fastapi.routing import APIRoute


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    
    # Request metrics
    total_requests: int = 0
    requests_per_minute: float = 0.0
    requests_per_hour: float = 0.0
    
    # Response time metrics
    avg_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    
    # Error metrics
    error_rate: float = 0.0
    total_errors: int = 0
    
    # System metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    
    # Database metrics
    db_connections: int = 0
    db_query_time: float = 0.0
    
    # Timestamps
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to dictionary."""
        return {
            "total_requests": float(self.total_requests),
            "requests_per_minute": self.requests_per_minute,
            "requests_per_hour": self.requests_per_hour,
            "avg_response_time": self.avg_response_time,
            "min_response_time": self.min_response_time,
            "max_response_time": self.max_response_time,
            "p95_response_time": self.p95_response_time,
            "p99_response_time": self.p99_response_time,
            "error_rate": self.error_rate,
            "total_errors": float(self.total_errors),
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "disk_usage": self.disk_usage,
            "db_connections": float(self.db_connections),
            "db_query_time": self.db_query_time,
            "last_updated": self.last_updated.timestamp()
        }


class PerformanceMonitor:
    """Performance monitoring system."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        
        # Request tracking
        self.request_times: deque = deque(maxlen=max_history)
        self.request_timestamps: deque = deque(maxlen=max_history)
        self.error_count: int = 0
        
        # Endpoint-specific metrics
        self.endpoint_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        
        # System metrics history
        self.system_metrics_history: deque = deque(maxlen=max_history)
        
        # Database metrics
        self.db_metrics: Dict[str, float] = {}
        
        # Alert thresholds
        self.alert_thresholds = {
            "response_time": 1.0,  # seconds
            "error_rate": 0.05,   # 5%
            "cpu_usage": 0.80,    # 80%
            "memory_usage": 0.85   # 85%
        }
        
        # Alerts
        self.active_alerts: List[Dict[str, str]] = []
    
    async def start_monitoring(self):
        """Start background monitoring tasks."""
        # Start system metrics collection
        asyncio.create_task(self._collect_system_metrics())
    
    async def _collect_system_metrics(self):
        """Collect system metrics periodically."""
        while True:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                metrics = {
                    "timestamp": datetime.now(UTC),
                    "cpu_usage": cpu_percent / 100.0,
                    "memory_usage": memory.percent / 100.0,
                    "disk_usage": disk.percent / 100.0
                }
                
                self.system_metrics_history.append(metrics)
                
                # Check for alerts
                await self._check_alerts(metrics)
                
            except Exception as e:
                print(f"Error collecting system metrics: {e}")
            
            await asyncio.sleep(30)  # Collect every 30 seconds
    
    async def _check_alerts(self, metrics: Dict[str, float]):
        """Check for performance alerts."""
        alerts = []
        
        if metrics["cpu_usage"] > self.alert_thresholds["cpu_usage"]:
            alerts.append({
                "type": "cpu_high",
                "message": f"CPU usage is {metrics['cpu_usage']:.1%}",
                "severity": "warning"
            })
        
        if metrics["memory_usage"] > self.alert_thresholds["memory_usage"]:
            alerts.append({
                "type": "memory_high",
                "message": f"Memory usage is {metrics['memory_usage']:.1%}",
                "severity": "critical"
            })
        
        # Update active alerts
        self.active_alerts = alerts
    
    def record_request(self, request: Request, response_time: float, status_code: int):
        """Record a request for metrics."""
        now = datetime.now(UTC)
        
        # Record request time
        self.request_times.append(response_time)
        self.request_timestamps.append(now)
        
        # Record endpoint-specific metrics
        endpoint = f"{request.method} {request.url.path}"
        self.endpoint_metrics[endpoint].append(response_time)
        
        # Record errors
        if status_code >= 400:
            self.error_count += 1
    
    def record_database_query(self, query_time: float, connection_count: int):
        """Record database query metrics."""
        self.db_metrics["query_time"] = query_time
        self.db_metrics["connections"] = connection_count
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        now = datetime.now(UTC)
        
        # Calculate request metrics
        total_requests = len(self.request_times)
        
        # Requests per time period
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)
        
        requests_last_minute = sum(
            1 for timestamp in self.request_timestamps 
            if timestamp > one_minute_ago
        )
        requests_last_hour = sum(
            1 for timestamp in self.request_timestamps 
            if timestamp > one_hour_ago
        )
        
        # Response time metrics
        if self.request_times:
            sorted_times = sorted(self.request_times)
            avg_response_time = sum(self.request_times) / len(self.request_times)
            min_response_time = min(self.request_times)
            max_response_time = max(self.request_times)
            
            # Percentiles
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else 0
            p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else 0
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        # Error rate
        error_rate = self.error_count / max(total_requests, 1)
        
        # System metrics (latest)
        if self.system_metrics_history:
            latest_system = self.system_metrics_history[-1]
            cpu_usage = latest_system["cpu_usage"]
            memory_usage = latest_system["memory_usage"]
            disk_usage = latest_system["disk_usage"]
        else:
            cpu_usage = memory_usage = disk_usage = 0
        
        # Database metrics
        db_connections = self.db_metrics.get("connections", 0)
        db_query_time = self.db_metrics.get("query_time", 0)
        
        return PerformanceMetrics(
            total_requests=total_requests,
            requests_per_minute=float(requests_last_minute),
            requests_per_hour=float(requests_last_hour),
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            error_rate=error_rate,
            total_errors=self.error_count,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            db_connections=db_connections,
            db_query_time=db_query_time,
            last_updated=now
        )
    
    def get_endpoint_metrics(self, endpoint: str) -> Dict[str, float]:
        """Get metrics for a specific endpoint."""
        times = list(self.endpoint_metrics[endpoint])
        
        if not times:
            return {
                "count": 0,
                "avg_time": 0,
                "min_time": 0,
                "max_time": 0,
                "p95_time": 0,
                "p99_time": 0
            }
        
        sorted_times = sorted(times)
        
        return {
            "count": len(times),
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "p95_time": sorted_times[int(len(times) * 0.95)] if len(times) > 0 else 0,
            "p99_time": sorted_times[int(len(times) * 0.99)] if len(times) > 0 else 0
        }
    
    def get_alerts(self) -> List[Dict[str, str]]:
        """Get current active alerts."""
        return self.active_alerts.copy()
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.request_times.clear()
        self.request_timestamps.clear()
        self.error_count = 0
        self.endpoint_metrics.clear()
        self.active_alerts.clear()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return performance_monitor


class PerformanceMiddleware:
    """Middleware to track performance metrics."""
    
    def __init__(self, app):
        self.app = app
        self.monitor = get_performance_monitor()
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Create request object for metrics
        request = Request(scope, receive)
        
        # Process request
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Calculate response time
                response_time = time.time() - start_time
                status_code = message.get("status", 200)
                
                # Record metrics
                self.monitor.record_request(request, response_time, status_code)
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


def add_performance_monitoring(app):
    """Add performance monitoring to FastAPI app."""
    # Add middleware using app.add_middleware
    app.add_middleware(PerformanceMiddleware)
