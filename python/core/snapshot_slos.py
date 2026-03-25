"""SLO definitions for snapshot operations.
    The code defines Snapshot SLOs (Service Level Objectives) with evaluation logic and environment
    variable overrides for threshold values.

    :param var: The `var` parameter in the `_f` function is a string representing the name of the
    environment variable that the function will attempt to read
    :type var: str
    :param default: The code snippet you provided defines Service Level Objectives (SLOs) for snapshot
    operations. These SLOs are used to monitor and evaluate the performance of snapshot-related tasks.
    Here's a breakdown of the key components in the code:
    :type default: float
    :return: The code defines a data structure for Snapshot SLO (Service Level Objective) with
    evaluation logic. It includes definitions for different SLO metrics such as latency and absence
    rate, along with their target values, degraded thresholds, critical thresholds, units of
    measurement, and evaluation criteria.


Values are read from environment variables so each environment (staging,
production) can independently tune thresholds. Defaults are set to the
agreed baseline: P95 save < 200 ms, availability ≥ 99.9 %.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional

SloStatus = Literal["healthy", "degraded", "critical", "no_data"]


def _f(var: str, default: float) -> float:
    try:
        return float(os.getenv(var, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class SnapshotSLO:
    """Single SLO definition with evaluation logic."""

    slo_id: str
    name: str
    target: float  # the published SLO target value
    threshold_degraded: float  # cross this → "degraded" (advisory warning)
    threshold_critical: float  # cross this → "critical"  (hard gate triggers)
    unit: str  # "ms" | "percent"
    lower_is_better: bool = True

    def evaluate(self, current: Optional[float]) -> SloStatus:
        if current is None or current == 0.0:
            return "no_data"
        if self.lower_is_better:
            if current > self.threshold_critical:
                return "critical"
            if current > self.threshold_degraded:
                return "degraded"
        else:
            # Higher is better (e.g., availability percent)
            if current < self.threshold_critical:
                return "critical"
            if current < self.threshold_degraded:
                return "degraded"
        return "healthy"

    def to_dict(self, current: Optional[float] = None) -> dict:
        d: dict = {
            "id": self.slo_id,
            "name": self.name,
            "unit": self.unit,
            "target": self.target,
            f"target_{self.unit}": self.target,
            f"threshold_degraded_{self.unit}": self.threshold_degraded,
            f"threshold_critical_{self.unit}": self.threshold_critical,
        }
        if current is not None:
            d["current"] = current
            d["status"] = self.evaluate(current)
        return d


# ── Snapshot SLO catalogue ───────────────────────────────────────────────
#
# Env-var overrides follow the naming convention:
#   SLO_SNAPSHOT_<METRIC>_<LEVEL>_<UNIT>
#
# All latency thresholds are in **milliseconds**.
# All rate thresholds are in **percent** (0-100 scale).

SNAPSHOT_SLOS: list[SnapshotSLO] = [
    SnapshotSLO(
        slo_id="snapshot.latency.save.p95",
        name="Snapshot Save Latency (P95)",
        target=_f("SLO_SNAPSHOT_SAVE_P95_TARGET_MS", 200.0),
        threshold_degraded=_f("SLO_SNAPSHOT_SAVE_P95_DEGRADED_MS", 300.0),
        threshold_critical=_f("SLO_SNAPSHOT_SAVE_P95_CRITICAL_MS", 600.0),
        unit="ms",
        lower_is_better=True,
    ),
    SnapshotSLO(
        slo_id="snapshot.latency.retrieve.p95",
        name="Snapshot Retrieve Latency (P95)",
        target=_f("SLO_SNAPSHOT_RETRIEVE_P95_TARGET_MS", 100.0),
        threshold_degraded=_f("SLO_SNAPSHOT_RETRIEVE_P95_DEGRADED_MS", 150.0),
        threshold_critical=_f("SLO_SNAPSHOT_RETRIEVE_P95_CRITICAL_MS", 300.0),
        unit="ms",
        lower_is_better=True,
    ),
    SnapshotSLO(
        slo_id="snapshot.undue_absence_rate",
        name="Snapshot Undue Absence Rate",
        target=_f("SLO_SNAPSHOT_ABSENCE_TARGET_PERCENT", 0.5),
        threshold_degraded=_f("SLO_SNAPSHOT_ABSENCE_DEGRADED_PERCENT", 1.0),
        threshold_critical=_f("SLO_SNAPSHOT_ABSENCE_CRITICAL_PERCENT", 2.0),
        unit="percent",
        lower_is_better=True,
    ),
]

# Quick lookup by slo_id
SNAPSHOT_SLO_BY_ID: dict[str, SnapshotSLO] = {s.slo_id: s for s in SNAPSHOT_SLOS}
