"""Router for performance monitoring endpoints."""
from __future__ import annotations

from typing import Dict, Any
from datetime import UTC, datetime

from fastapi import APIRouter, Query

from monitoring.performance import get_performance_monitor
from monitoring.snapshot_metrics import get_snapshot_tracker
from core.config import get_settings
from core.snapshot_slos import SNAPSHOT_SLOS

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
        "timestamp": datetime.now(UTC).isoformat()
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
        "timestamp": datetime.now(UTC).isoformat()
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
        "timestamp": datetime.now(UTC).isoformat()
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
        "timestamp": datetime.now(UTC).isoformat()
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
        "timestamp": datetime.now(UTC).isoformat()
    }


@router.post("/metrics/reset", response_model=Dict[str, Any])
async def reset_metrics() -> Dict[str, Any]:
    """Reset all performance metrics."""
    monitor = get_performance_monitor()
    monitor.reset_metrics()

    return {
        "status": "success",
        "message": "All metrics have been reset",
        "timestamp": datetime.now(UTC).isoformat()
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
        "timestamp": datetime.now(UTC).isoformat()
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
        "timestamp": datetime.now(UTC).isoformat()
    }


# ── Snapshot SLO endpoints ────────────────────────────────────────────────

@router.get("/snapshot/baseline", response_model=Dict[str, Any])
async def snapshot_baseline() -> Dict[str, Any]:
    """Current latency and absence-rate baseline for snapshot operations.

    All values are computed from an in-memory rolling window (default 24 h).
    Returns zero-value metrics when the process has no observations yet.
    """
    tracker = get_snapshot_tracker()
    return {
        "status": "success",
        "data": tracker.baseline(),
        "timestamp": datetime.now(UTC).isoformat() + "Z",
    }


@router.get("/snapshot/slos", response_model=Dict[str, Any])
async def snapshot_slos() -> Dict[str, Any]:
    """Evaluate each snapshot SLO against the current baseline.

    Overall status is the worst-case status across all SLOs.
    Returns 'no_data' for SLOs whose metric has zero samples.
    """
    tracker = get_snapshot_tracker()
    bl = tracker.baseline()

    current_by_id = {
        "snapshot.latency.save.p95": bl["save"]["p95_ms"],
        "snapshot.latency.retrieve.p95": bl["retrieve"]["p95_ms"],
        "snapshot.undue_absence_rate": bl["undue_absence"]["absence_rate_percent"],
    }

    slo_results = []
    overall = "healthy"
    _rank = {"no_data": 0, "healthy": 1, "degraded": 2, "critical": 3}

    for slo in SNAPSHOT_SLOS:
        current = current_by_id.get(slo.slo_id)
        # Treat 0.0 as no_data for latency metrics (no samples yet)
        effective = None if (current is None or current == 0.0) else current
        status = slo.evaluate(effective)
        slo_results.append(slo.to_dict(effective))
        if _rank.get(status, 0) > _rank.get(overall, 1):
            overall = status

    return {
        "status": "success",
        "data": {
            "slos": slo_results,
            "overall_status": overall,
            "sample_counts": {
                "save": bl["save"]["sample_count"],
                "retrieve": bl["retrieve"]["sample_count"],
                "batch_save": bl["batch_save"]["sample_count"],
            },
        },
        "timestamp": datetime.now(UTC).isoformat() + "Z",
    }


@router.post("/snapshot/record-undue-absence", response_model=Dict[str, Any])
async def record_undue_absence() -> Dict[str, Any]:
    """Increment the undue-absence counter.

    Called by the E2E smoke suite after it detects a 404 on GET /snapshot
    immediately following a confirmed successful save for the same ponto_id.
    This endpoint is idempotent per call; each POST adds exactly one event.
    """
    get_snapshot_tracker().record_undue_absence()
    return {"recorded": True, "timestamp": datetime.now(UTC).isoformat() + "Z"}


@router.get("/snapshot/report", response_model=Dict[str, Any])
async def snapshot_report() -> Dict[str, Any]:
    """Structured baseline + SLO report suitable for CI output and auditing."""
    tracker = get_snapshot_tracker()
    bl = tracker.baseline()

    current_by_id = {
        "snapshot.latency.save.p95": bl["save"]["p95_ms"],
        "snapshot.latency.retrieve.p95": bl["retrieve"]["p95_ms"],
        "snapshot.undue_absence_rate": bl["undue_absence"]["absence_rate_percent"],
    }

    slo_summary = {}
    recommendations = []
    overall = "healthy"
    _rank = {"no_data": 0, "healthy": 1, "degraded": 2, "critical": 3}

    for slo in SNAPSHOT_SLOS:
        current = current_by_id.get(slo.slo_id)
        effective = None if (current is None or current == 0.0) else current
        status = slo.evaluate(effective)
        slo_summary[slo.slo_id] = {
            "target": slo.target,
            "current": effective,
            "status": status,
            "unit": slo.unit,
        }
        if _rank.get(status, 0) > _rank.get(overall, 1):
            overall = status
        if status == "critical":
            recommendations.append(
                f"CRITICAL: {slo.name} ({effective} {slo.unit}) exceeded "
                f"critical threshold ({slo.threshold_critical} {slo.unit})."
            )
        elif status == "degraded":
            recommendations.append(
                f"WARNING: {slo.name} ({effective} {slo.unit}) exceeded "
                f"degraded threshold ({slo.threshold_degraded} {slo.unit})."
            )

    return {
        "status": "success",
        "data": {
            "overall_status": overall,
            "baseline": {
                "save_latency_p95_ms": bl["save"]["p95_ms"],
                "save_latency_p99_ms": bl["save"]["p99_ms"],
                "retrieve_latency_p95_ms": bl["retrieve"]["p95_ms"],
                "retrieve_latency_p99_ms": bl["retrieve"]["p99_ms"],
                "undue_absence_rate_percent": bl["undue_absence"]["absence_rate_percent"],
                "save_attempts_total": bl["undue_absence"]["save_attempts_total"],
                "window_hours": bl["window_hours"],
            },
            "slos": slo_summary,
            "recommendations": recommendations,
        },
        "timestamp": datetime.now(UTC).isoformat() + "Z",
    }
