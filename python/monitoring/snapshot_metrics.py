"""Snapshot-specific latency and availability tracking.

In-memory rolling window (24 h by default). No external storage required.
Thread-safe singleton – same pattern as PerformanceMonitor.
"""
from __future__ import annotations

import time
from collections import deque
from datetime import UTC, datetime
from threading import Lock
from typing import Deque, NamedTuple, Optional

_WINDOW_MAX = 10_000  # maximum samples kept per operation type


class _Sample(NamedTuple):
    duration_ms: float
    ts: float  # epoch seconds


class SnapshotMetricsTracker:
    """Tracks latency and undue-absence metrics for snapshot operations.

    All data lives in process memory within a configurable rolling window.
    Zero added infrastructure cost.
    """

    def __init__(
        self,
        window_hours: int = 24,
        max_samples: int = _WINDOW_MAX,
    ) -> None:
        self._window_seconds = window_hours * 3600
        self._lock = Lock()

        # Per-operation latency samples
        self._save: Deque[_Sample] = deque(maxlen=max_samples)
        self._retrieve: Deque[_Sample] = deque(maxlen=max_samples)
        self._batch_save: Deque[_Sample] = deque(maxlen=max_samples)

        # Absence tracking counters
        self._save_attempts: int = 0
        self._undue_absence_count: int = 0

    # ── Recording ────────────────────────────────────────────────────────

    def record_save(self, duration_ms: float) -> None:
        """Record a successful POST /pontos/{id}/calculo latency (ms)."""
        with self._lock:
            self._save.append(_Sample(duration_ms, time.time()))

    def record_retrieve(self, duration_ms: float) -> None:
        """Record a successful GET /pontos/{id}/snapshot latency (ms)."""
        with self._lock:
            self._retrieve.append(_Sample(duration_ms, time.time()))

    def record_batch_save(self, duration_ms: float) -> None:
        """Record a successful POST /projetos/batch-save latency (ms)."""
        with self._lock:
            self._batch_save.append(_Sample(duration_ms, time.time()))

    def record_save_attempt(self) -> None:
        """Increment total save attempts counter (call before persisting)."""
        with self._lock:
            self._save_attempts += 1

    def record_undue_absence(self) -> None:
        """Increment undue-absence counter.

        Called by the E2E suite when a GET /snapshot returns 404 immediately
        after a confirmed successful save for the same ponto_id.
        """
        with self._lock:
            self._undue_absence_count += 1

    # ── Internal helpers ─────────────────────────────────────────────────

    def _recent(self, samples: Deque[_Sample]) -> list[float]:
        """Return durations whose timestamp falls within the rolling window."""
        cutoff = time.time() - self._window_seconds
        return [s.duration_ms for s in samples if s.ts >= cutoff]

    @staticmethod
    def _percentile(values: list[float], pct: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        # Nearest-rank method
        idx = max(0, int(len(sorted_vals) * pct / 100) - 1)
        return round(sorted_vals[idx], 2)

    @staticmethod
    def _mean(values: list[float]) -> float:
        return round(sum(values) / len(values), 2) if values else 0.0

    # ── Public query ─────────────────────────────────────────────────────

    def baseline(self) -> dict:
        """Return the current baseline snapshot (thread-safe point-in-time read)."""
        with self._lock:
            save = self._recent(self._save)
            retrieve = self._recent(self._retrieve)
            batch = self._recent(self._batch_save)
            attempts = self._save_attempts
            absences = self._undue_absence_count

        absence_rate = round(absences / max(attempts, 1) * 100, 4) if attempts else 0.0

        return {
            "save": {
                "p95_ms": self._percentile(save, 95),
                "p99_ms": self._percentile(save, 99),
                "mean_ms": self._mean(save),
                "sample_count": len(save),
            },
            "retrieve": {
                "p95_ms": self._percentile(retrieve, 95),
                "p99_ms": self._percentile(retrieve, 99),
                "mean_ms": self._mean(retrieve),
                "sample_count": len(retrieve),
            },
            "batch_save": {
                "p95_ms": self._percentile(batch, 95),
                "p99_ms": self._percentile(batch, 99),
                "mean_ms": self._mean(batch),
                "sample_count": len(batch),
            },
            "undue_absence": {
                "count": absences,
                "save_attempts_total": attempts,
                "absence_rate_percent": absence_rate,
            },
            "window_hours": self._window_seconds // 3600,
            "timestamp": datetime.now(UTC).isoformat() + "Z",
        }


# ── Module-level singleton ────────────────────────────────────────────────

_tracker: Optional[SnapshotMetricsTracker] = None


def get_snapshot_tracker() -> SnapshotMetricsTracker:
    """Return the process-wide SnapshotMetricsTracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = SnapshotMetricsTracker()
    return _tracker
