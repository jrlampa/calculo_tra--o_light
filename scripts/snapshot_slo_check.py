#!/usr/bin/env python3
"""Snapshot SLO baseline checker for CI.

Connects to a running API instance, performs N save+retrieve cycles,
collects latency observations, then evaluates the agreed SLOs.

Exit code is always 0 (advisory gate – blocking requires human approval).
Results are printed to stdout in a format suitable for GitHub Actions
step-summary output.

Usage:
    python scripts/snapshot_slo_check.py \
        --api-url http://127.0.0.1:8000/api \
        --jwt-secret <secret> \
        --iterations 20

Environment variable overrides (same as application):
    SLO_SNAPSHOT_SAVE_P95_TARGET_MS         (default 200)
    SLO_SNAPSHOT_SAVE_P95_DEGRADED_MS       (default 300)
    SLO_SNAPSHOT_SAVE_P95_CRITICAL_MS       (default 600)
    SLO_SNAPSHOT_RETRIEVE_P95_TARGET_MS     (default 100)
    SLO_SNAPSHOT_RETRIEVE_P95_DEGRADED_MS   (default 150)
    SLO_SNAPSHOT_RETRIEVE_P95_CRITICAL_MS   (default 300)
    SLO_SNAPSHOT_ABSENCE_TARGET_PERCENT     (default 0.5)
    SLO_SNAPSHOT_ABSENCE_DEGRADED_PERCENT   (default 1.0)
    SLO_SNAPSHOT_ABSENCE_CRITICAL_PERCENT   (default 2.0)
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
import base64


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _make_jwt(secret: str, user_id: str | None = None) -> str:
    uid = user_id or "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    now = int(time.time())
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(
        json.dumps({"sub": uid, "role": "user", "iat": now, "exp": now + 3600}).encode()
    )
    sig = _b64url(
        hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{sig}"


def _f(var: str, default: float) -> float:
    try:
        return float(os.getenv(var, str(default)))
    except ValueError:
        return default


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sv = sorted(values)
    idx = max(0, int(len(sv) * pct / 100) - 1)
    return round(sv[idx], 2)


def _evaluate(value: float, degraded: float, critical: float,
              lower_is_better: bool) -> str:
    if lower_is_better:
        if value > critical:
            return "critical"
        if value > degraded:
            return "degraded"
    else:
        if value < critical:
            return "critical"
        if value < degraded:
            return "degraded"
    return "healthy"


_STATUS_ICON = {"healthy": "✅", "degraded": "⚠️", "critical": "🔴", "no_data": "⬜"}


def run(api_url: str, jwt_secret: str, iterations: int, timeout: float) -> bool:
    """Execute the SLO check. Returns True if any SLO is critical."""
    try:
        import httpx
    except ImportError:
        print("httpx not available; install python/requirements.txt first.")
        return False

    jwt = _make_jwt(jwt_secret)
    headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}
    client = httpx.Client(base_url=api_url, headers=headers, timeout=timeout)

    run_id = uuid.uuid4().hex[:8]
    print(f"\n── Snapshot SLO Check (run={run_id}, iterations={iterations}) ──────────────\n")

    # 1. Create a temporary project + point
    proj_resp = client.post("/projetos", json={
        "orgao": "SLO_CHECK", "ns": f"SLO-{run_id}", "nome": f"SloCheck-{run_id}",
        "endereco": "CI", "estudado_por": "CI Bot", "matricula": "9999",
        "data_estudo": "25/03/2026",
    })
    if proj_resp.status_code != 201:
        print(f"SKIP: Could not create test project (HTTP {proj_resp.status_code}). "
              "Is the API running and authenticated?")
        return False
    projeto_id = proj_resp.json()["id"]

    ponto_resp = client.post(f"/projetos/{projeto_id}/pontos", json={
        "numero": f"SLO{run_id}", "tipo_poste": "DT", "modelo_poste": "11/600",
    })
    if ponto_resp.status_code != 201:
        print(f"SKIP: Could not create test ponto (HTTP {ponto_resp.status_code}).")
        return False
    ponto_id = ponto_resp.json()["id"]

    save_times: list[float] = []
    retrieve_times: list[float] = []
    absence_count = 0
    def _travessias() -> list[dict]:
        return [{"posicao": p, "tipo_rede": "", "tipo_cabo": "", "vao": 0.0,
                 "flecha": 0.0, "angulo": 0.0, "qtd_ligacoes": 0, "qtd_cabos": 0}
                for p in range(1, 5)]

    payload_template = {
        "ponto_id": ponto_id,
        "niveis": [
            {"nivel": lvl, "travessias": _travessias()}
            for lvl in ("MT1", "MT2", "BT", "BTZ", "RAL")
        ],
        "resultado": {
            "mt1_tracao": 100.0, "mt1_angulo": 5.0,
            "total_tracao": 100.0, "total_angulo": 5.0, "poste_ecc": 50.0,
            "texto_mt1": "MT1: 100.0 daN @ 5.0°",
            "texto_total": "Total final: 100.0 daN @ 5.0°",
        },
    }

    # 2. Measure save + retrieve
    for i in range(iterations):
        t0 = time.monotonic()
        save_resp = client.post(f"/pontos/{ponto_id}/calculo", json=payload_template)
        save_ms = (time.monotonic() - t0) * 1000

        if save_resp.status_code == 200:
            save_times.append(save_ms)
            t1 = time.monotonic()
            get_resp = client.get(f"/pontos/{ponto_id}/snapshot")
            retrieve_ms = (time.monotonic() - t1) * 1000
            if get_resp.status_code == 200:
                retrieve_times.append(retrieve_ms)
            else:
                absence_count += 1
                # Also report to in-process counter so /monitoring/snapshot/slos reflects it
                client.post("/monitoring/snapshot/record-undue-absence")
        else:
            print(f"  [iter {i+1}] save failed with HTTP {save_resp.status_code}")

    # 3. Compute metrics
    save_p95 = _percentile(save_times, 95)
    retrieve_p95 = _percentile(retrieve_times, 95)
    absence_rate = round(absence_count / max(iterations, 1) * 100, 4)

    # 4. Evaluate SLOs
    slo_save = _evaluate(
        save_p95,
        _f("SLO_SNAPSHOT_SAVE_P95_DEGRADED_MS", 300),
        _f("SLO_SNAPSHOT_SAVE_P95_CRITICAL_MS", 600),
        lower_is_better=True,
    )
    slo_retrieve = _evaluate(
        retrieve_p95,
        _f("SLO_SNAPSHOT_RETRIEVE_P95_DEGRADED_MS", 150),
        _f("SLO_SNAPSHOT_RETRIEVE_P95_CRITICAL_MS", 300),
        lower_is_better=True,
    )
    slo_absence = _evaluate(
        absence_rate,
        _f("SLO_SNAPSHOT_ABSENCE_DEGRADED_PERCENT", 1.0),
        _f("SLO_SNAPSHOT_ABSENCE_CRITICAL_PERCENT", 2.0),
        lower_is_better=True,
    )

    any_critical = any(s == "critical" for s in (slo_save, slo_retrieve, slo_absence))
    any_degraded = any(s == "degraded" for s in (slo_save, slo_retrieve, slo_absence))

    # 5. Print report
    print(f"Samples: save={len(save_times)}, retrieve={len(retrieve_times)}\n")
    print(f"{'SLO':<42} {'Current':>10} {'Target':>10} {'Status':>12}")
    print("-" * 80)
    print(f"{'Save Latency P95 (ms)':<42} {save_p95:>10.1f} {_f('SLO_SNAPSHOT_SAVE_P95_TARGET_MS', 200):>10.0f} "
          f"{_STATUS_ICON.get(slo_save, '?')} {slo_save:>8}")
    print(f"{'Retrieve Latency P95 (ms)':<42} {retrieve_p95:>10.1f} {_f('SLO_SNAPSHOT_RETRIEVE_P95_TARGET_MS', 100):>10.0f} "
          f"{_STATUS_ICON.get(slo_retrieve, '?')} {slo_retrieve:>8}")
    print(f"{'Undue Absence Rate (%)':<42} {absence_rate:>10.4f} {_f('SLO_SNAPSHOT_ABSENCE_TARGET_PERCENT', 0.5):>10.1f} "
          f"{_STATUS_ICON.get(slo_absence, '?')} {slo_absence:>8}")
    print("-" * 80)

    if any_critical:
        print("\n🔴 ONE OR MORE SNAPSHOT SLOs CRITICAL — manual review required before merge.\n")
    elif any_degraded:
        print("\n⚠️  ONE OR MORE SNAPSHOT SLOs DEGRADED — review recommended.\n")
    else:
        print("\n✅ All snapshot SLOs within target.\n")

    # Write GitHub Actions step summary if available
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("## Snapshot SLO Check\n\n")
            f.write("| SLO | Current | Target | Status |\n|---|---|---|---|\n")
            f.write(f"| Save Latency P95 | {save_p95:.1f} ms | ≤200 ms | {_STATUS_ICON.get(slo_save, '?')} {slo_save} |\n")
            f.write(f"| Retrieve Latency P95 | {retrieve_p95:.1f} ms | ≤100 ms | {_STATUS_ICON.get(slo_retrieve, '?')} {slo_retrieve} |\n")
            f.write(f"| Undue Absence Rate | {absence_rate:.4f}% | ≤0.5% | {_STATUS_ICON.get(slo_absence, '?')} {slo_absence} |\n\n")
            if any_critical:
                f.write("> **🔴 Manual review required before merge** — at least one SLO is critical.\n")
            elif any_degraded:
                f.write("> **⚠️ Review recommended** — at least one SLO is degraded.\n")
            else:
                f.write("> ✅ All snapshot SLOs within acceptable range.\n")

    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            status = (
                "critical" if any_critical
                else "degraded" if any_degraded
                else "healthy"
            )
            f.write(f"snapshot_slo_status={status}\n")
            f.write(f"save_latency_p95={save_p95}\n")
            f.write(f"retrieve_latency_p95={retrieve_p95}\n")
            f.write(f"absence_rate={absence_rate}\n")

    return any_critical


def main() -> None:
    parser = argparse.ArgumentParser(description="Snapshot SLO baseline checker")
    parser.add_argument("--api-url", default=os.getenv("API_URL", "http://127.0.0.1:8000/api"))
    parser.add_argument("--jwt-secret", default=os.getenv("AUTH_JWT_SECRET", ""))
    parser.add_argument("--iterations", type=int, default=int(os.getenv("SLO_CHECK_ITERATIONS", "20")))
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()

    if not args.jwt_secret:
        print("ERROR: --jwt-secret or AUTH_JWT_SECRET is required.")
        sys.exit(0)  # advisory: don't block

    run(args.api_url, args.jwt_secret, args.iterations, args.timeout)
    # Always exit 0 – advisory gate (human review required, not auto-block)
    sys.exit(0)


if __name__ == "__main__":
    main()
