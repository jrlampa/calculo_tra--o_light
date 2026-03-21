"""Router for performance monitoring endpoints."""
from __future__ import annotations

import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from monitoring.performance import get_performance_monitor, PerformanceMetrics
from core.config import get_settings

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])
settings = get_settings()


@router.get("/metrics", response_model=Dict[str, Any])
async def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics."""
    monitor = get_performance_monitor()
    metrics = monitor.get_current_metrics()
    
    return {
        "status": "success",
        "data": metrics.to_dict(),
        "alerts": monitor.get_alerts(),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics/summary", response_model=Dict[str, Any])
async def get_metrics_summary() -> Dict[str, Any]:
    """Get performance metrics summary."""
    monitor = get_performance_monitor()
    metrics = monitor.get_current_metrics()
    
    # Determine health status
    health_status = "healthy"
    issues = []
    
    if metrics.avg_response_time > 1.0:
        health_status = "degraded"
        issues.append("High average response time")
    
    if metrics.error_rate > 0.05:
        health_status = "critical"
        issues.append("High error rate")
    
    if metrics.cpu_usage > 0.80:
        health_status = "critical"
        issues.append("High CPU usage")
    
    if metrics.memory_usage > 0.85:
        health_status = "critical"
        issues.append("High memory usage")
    
    return {
        "status": "success",
        "data": {
            "health_status": health_status,
            "issues": issues,
            "summary": {
                "total_requests": metrics.total_requests,
                "avg_response_time": round(metrics.avg_response_time, 3),
                "error_rate": f"{metrics.error_rate:.2%}",
                "cpu_usage": f"{metrics.cpu_usage:.1%}",
                "memory_usage": f"{metrics.memory_usage:.1%}",
                "uptime": "N/A"  # Would need to track app start time
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics/endpoints/{endpoint:path}", response_model=Dict[str, Any])
async def get_endpoint_metrics(
    endpoint: str,
    limit: int = Query(default=100, le=1000)
) -> Dict[str, Any]:
    """Get metrics for a specific endpoint."""
    monitor = get_performance_monitor()
    metrics = monitor.get_endpoint_metrics(endpoint)
    
    return {
        "status": "success",
        "data": {
            "endpoint": endpoint,
            "metrics": metrics
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics/endpoints", response_model=Dict[str, Any])
async def list_endpoint_metrics() -> Dict[str, Any]:
    """List all endpoints with metrics."""
    monitor = get_performance_monitor()
    
    # Get all endpoints
    endpoints = list(monitor.endpoint_metrics.keys())
    
    # Get summary metrics for each endpoint
    endpoint_summaries = {}
    for endpoint in endpoints[:50]:  # Limit to 50 endpoints
        metrics = monitor.get_endpoint_metrics(endpoint)
        endpoint_summaries[endpoint] = {
            "count": metrics["count"],
            "avg_time": round(metrics["avg_time"], 3),
            "min_time": round(metrics["min_time"], 3),
            "max_time": round(metrics["max_time"], 3)
        }
    
    return {
        "status": "success",
        "data": {
            "total_endpoints": len(endpoints),
            "endpoints": endpoint_summaries
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/alerts", response_model=Dict[str, Any])
async def get_active_alerts() -> Dict[str, Any]:
    """Get current active alerts."""
    monitor = get_performance_monitor()
    alerts = monitor.get_alerts()
    
    return {
        "status": "success",
        "data": {
            "active_alerts": alerts,
            "alert_count": len(alerts)
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/metrics/reset", response_model=Dict[str, Any])
async def reset_metrics() -> Dict[str, Any]:
    """Reset all performance metrics."""
    monitor = get_performance_monitor()
    monitor.reset_metrics()
    
    return {
        "status": "success",
        "message": "All metrics have been reset",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/performance", response_model=Dict[str, Any])
async def performance_health_check() -> Dict[str, Any]:
    """Performance-specific health check."""
    monitor = get_performance_monitor()
    metrics = monitor.get_current_metrics()
    
    # Determine health status
    status = "healthy"
    checks = {}
    
    # Response time check
    if metrics.avg_response_time > 1.0:
        checks["response_time"] = "critical" if metrics.avg_response_time > 2.0 else "warning"
    else:
        checks["response_time"] = "healthy"
    
    # Error rate check
    if metrics.error_rate > 0.05:
        checks["error_rate"] = "critical" if metrics.error_rate > 0.10 else "warning"
    else:
        checks["error_rate"] = "healthy"
    
    # CPU check
    if metrics.cpu_usage > 0.80:
        checks["cpu"] = "critical" if metrics.cpu_usage > 0.90 else "warning"
    else:
        checks["cpu"] = "healthy"
    
    # Memory check
    if metrics.memory_usage > 0.85:
        checks["memory"] = "critical" if metrics.memory_usage > 0.95 else "warning"
    else:
        checks["memory"] = "healthy"
    
    # Overall status
    if any(check == "critical" for check in checks.values()):
        status = "critical"
    elif any(check == "warning" for check in checks.values()):
        status = "warning"
    
    return {
        "status": status,
        "data": {
            "checks": checks,
            "metrics": {
                "avg_response_time": round(metrics.avg_response_time, 3),
                "error_rate": f"{metrics.error_rate:.2%}",
                "cpu_usage": f"{metrics.cpu_usage:.1%}",
                "memory_usage": f"{metrics.memory_usage:.1%}"
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_data() -> Dict[str, Any]:
    """Get comprehensive dashboard data."""
    monitor = get_performance_monitor()
    metrics = monitor.get_current_metrics()
    
    # Get top endpoints by request count
    endpoint_data = {}
    for endpoint in list(monitor.endpoint_metrics.keys())[:10]:
        endpoint_metrics = monitor.get_endpoint_metrics(endpoint)
        endpoint_data[endpoint] = endpoint_metrics
    
    return {
        "status": "success",
        "data": {
            "overview": {
                "total_requests": metrics.total_requests,
                "requests_per_minute": round(metrics.requests_per_minute, 2),
                "avg_response_time": round(metrics.avg_response_time, 3),
                "error_rate": f"{metrics.error_rate:.2%}",
                "uptime": "N/A"
            },
            "system": {
                "cpu_usage": f"{metrics.cpu_usage:.1%}",
                "memory_usage": f"{metrics.memory_usage:.1%}",
                "disk_usage": f"{metrics.disk_usage:.1%}",
                "db_connections": metrics.db_connections
            },
            "performance": {
                "min_response_time": round(metrics.min_response_time, 3),
                "max_response_time": round(metrics.max_response_time, 3),
                "p95_response_time": round(metrics.p95_response_time, 3),
                "p99_response_time": round(metrics.p99_response_time, 3)
            },
            "alerts": monitor.get_alerts(),
            "top_endpoints": endpoint_data
        },
        "timestamp": datetime.utcnow().isoformat()
    }
