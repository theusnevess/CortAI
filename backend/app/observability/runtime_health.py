from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime
from time import perf_counter_ns
from typing import Any

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_C1_HEALTH_STATUS_WINDOW_MINUTES = 15
_C1_HEALTH_ENDPOINTS = {
    "overview": "/api/v1/metrics/overview",
    "runs": "/api/v1/metrics/runs",
    "report": "/api/v1/observability/report",
}
_C1_HEALTH_THRESHOLDS = {
    "overview": {"warn_p99_ms": 1500, "fail_p99_ms": 2500},
    "runs": {"warn_p99_ms": 1500, "fail_p99_ms": 2500},
    "report": {"warn_p99_ms": 1500, "fail_p99_ms": 2500},
}
_C1_HEALTH_PCT5XX_FAIL = 1.0
_C1_HEALTH_RUNTIME_VERSION = "v1.1"
_C1_HEALTH_RUNTIME_CACHE: dict[str, Any] = {
    "payload": None,
    "computed_at": None,
    "compute_ms": None,
    "window_minutes": _C1_HEALTH_STATUS_WINDOW_MINUTES,
}


def _execute_with_db_stats(
    db: AsyncSession,
    statement,
    db_stats: dict[str, int],
    params: dict | None = None,
):
    """
    Versao local do wrapper de DB para evitar acoplamento com endpoint /status.
    """
    raise RuntimeError("This sync stub should not be called")


async def _execute_with_db_stats_async(
    db: AsyncSession,
    statement,
    db_stats: dict[str, int],
    params: dict | None = None,
):
    started_ns = perf_counter_ns()
    if params is None:
        result = await db.execute(statement)
    else:
        result = await db.execute(statement, params)
    elapsed_us = max(0, (perf_counter_ns() - started_ns) // 1000)
    db_stats["db_us"] = int(db_stats.get("db_us", 0)) + int(elapsed_us)
    db_stats["db_queries"] = int(db_stats.get("db_queries", 0)) + 1
    return result


def _env_flag_enabled(name: str, default: str = "0") -> bool:
    raw = str(os.getenv(name, default)).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _get_c1_health_cache_ttl_seconds() -> int:
    try:
        return max(0, int(os.getenv("C1_HEALTH_CACHE_TTL_SECONDS", "10")))
    except Exception:
        return 10


def clear_runtime_c1_health_cache() -> None:
    _C1_HEALTH_RUNTIME_CACHE["payload"] = None
    _C1_HEALTH_RUNTIME_CACHE["computed_at"] = None
    _C1_HEALTH_RUNTIME_CACHE["compute_ms"] = None
    _C1_HEALTH_RUNTIME_CACHE["window_minutes"] = _C1_HEALTH_STATUS_WINDOW_MINUTES


def should_include_internal_status(request: Request) -> bool:
    if not _env_flag_enabled("EXPOSE_C1_HEALTH_STATUS", "0"):
        return False
    return str(request.headers.get("X-Internal-Status", "")).strip() == "1"


def classify_c1_health_row(
    *,
    endpoint: str,
    p99_ms: float | None,
    rps: float,
    timeouts: int,
    pct_429: float,
    pct_503: float,
    pct_5xx: float,
) -> dict[str, Any]:
    thresholds = _C1_HEALTH_THRESHOLDS.get(endpoint, {"warn_p99_ms": 1500, "fail_p99_ms": 2500})
    reasons: list[str] = []
    decision = "PASS"

    if timeouts > 0:
        decision = "FAIL"
        reasons.append("timeouts>0")
    elif rps < 1:
        decision = "FAIL"
        reasons.append("rps<1")
    elif pct_5xx >= _C1_HEALTH_PCT5XX_FAIL:
        decision = "FAIL"
        reasons.append("pct_5xx>=limit")
    elif p99_ms is not None and p99_ms > float(thresholds["fail_p99_ms"]):
        decision = "FAIL"
        reasons.append("p99>fail_limit")
    elif p99_ms is None:
        decision = "WARN"
        reasons.append("p99_missing")
    elif p99_ms > float(thresholds["warn_p99_ms"]):
        decision = "WARN"
        reasons.append("p99>warn_limit")
    elif pct_429 > 0:
        decision = "WARN"
        reasons.append("pct_429>0")
    elif pct_503 > 0:
        decision = "WARN"
        reasons.append("pct_503>0")

    return {"decision": decision, "reasons": reasons, "thresholds": thresholds}


def build_c1_health_payload(rows: list[dict[str, Any]], *, as_of: datetime, window_minutes: int) -> dict[str, Any]:
    score = "PASS"
    if any(row["decision"] == "FAIL" for row in rows):
        score = "FAIL"
    elif any(row["decision"] == "WARN" for row in rows):
        score = "WARN"
    consolidated_reasons: list[str] = []
    for row in rows:
        endpoint = str(row.get("endpoint", "unknown"))
        for reason in row.get("reasons", []) or []:
            consolidated_reasons.append(f"{endpoint}:{reason}")
    return {
        "enabled": True,
        "version": _C1_HEALTH_RUNTIME_VERSION,
        "score": score,
        "as_of": as_of.replace(microsecond=0).isoformat() + "Z",
        "inputs": {"window_minutes": int(window_minutes), "source": "metrics_endpoint_timing"},
        "reasons": consolidated_reasons,
        "rows": rows,
    }


def with_c1_health_meta(payload: dict[str, Any], *, cached: bool, cache_age_seconds: int, compute_ms: int) -> dict[str, Any]:
    result = deepcopy(payload)
    result["meta"] = {
        "cached": bool(cached),
        "cache_age_seconds": max(0, int(cache_age_seconds)),
        "compute_ms": max(0, int(compute_ms)),
        "stale": False,
    }
    return result


async def _compute_runtime_c1_health(
    *,
    db: AsyncSession,
    db_stats: dict[str, int],
    window_minutes: int = _C1_HEALTH_STATUS_WINDOW_MINUTES,
) -> dict[str, Any]:
    endpoint_paths = list(_C1_HEALTH_ENDPOINTS.values())
    timing_rows = (
        await _execute_with_db_stats_async(
            db,
            text(
                """
                WITH timing AS (
                  SELECT
                    facts->>'endpoint' AS endpoint,
                    NULLIF(facts->>'duration_ms', '')::float AS duration_ms,
                    COALESCE(NULLIF(facts->>'status_code', '')::int, 0) AS status_code
                  FROM observations
                  WHERE facts->>'event_type' = 'metrics_endpoint_timing'
                    AND timestamp >= NOW() - make_interval(mins => :window_minutes)
                    AND facts->>'endpoint' IN (:endpoint_overview, :endpoint_runs, :endpoint_report)
                )
                SELECT
                  endpoint,
                  COUNT(*)::int AS events,
                  percentile_cont(0.99) WITHIN GROUP (ORDER BY duration_ms) AS p99_ms,
                  SUM(CASE WHEN status_code = 429 THEN 1 ELSE 0 END)::int AS c429,
                  SUM(CASE WHEN status_code = 503 THEN 1 ELSE 0 END)::int AS c503,
                  SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END)::int AS c5xx
                FROM timing
                GROUP BY endpoint
                """
            ),
            db_stats,
            {
                "window_minutes": int(window_minutes),
                "endpoint_overview": endpoint_paths[0],
                "endpoint_runs": endpoint_paths[1],
                "endpoint_report": endpoint_paths[2],
            },
        )
    ).mappings().all()

    rows_by_path = {str(r["endpoint"]): r for r in timing_rows}
    runtime_rows: list[dict[str, Any]] = []
    window_seconds = max(1, int(window_minutes) * 60)
    as_of = datetime.utcnow()

    for short_name in ("overview", "runs", "report"):
        path = _C1_HEALTH_ENDPOINTS[short_name]
        row = rows_by_path.get(path)
        events = int((row or {}).get("events") or 0)
        p99_val = None if row is None or row.get("p99_ms") is None else float(row["p99_ms"])
        rps = round(events / float(window_seconds), 3)
        timeouts = 0
        pct_429 = round((int(row["c429"] or 0) / events) * 100.0, 2) if events > 0 else 0.0
        pct_503 = round((int(row["c503"] or 0) / events) * 100.0, 2) if events > 0 else 0.0
        pct_5xx = round((int(row["c5xx"] or 0) / events) * 100.0, 2) if events > 0 else 0.0
        classified = classify_c1_health_row(
            endpoint=short_name,
            p99_ms=p99_val,
            rps=rps,
            timeouts=timeouts,
            pct_429=pct_429,
            pct_503=pct_503,
            pct_5xx=pct_5xx,
        )
        runtime_rows.append(
            {
                "endpoint": short_name,
                "path": "direct",
                "p99_ms": None if p99_val is None else round(p99_val, 2),
                "rps": rps,
                "timeouts": timeouts,
                "pct_429": pct_429,
                "pct_503": pct_503,
                "pct_5xx": pct_5xx,
                "decision": classified["decision"],
                "reasons": classified["reasons"],
            }
        )

    return build_c1_health_payload(runtime_rows, as_of=as_of, window_minutes=window_minutes)


async def get_runtime_c1_health_cached(
    *,
    db: AsyncSession,
    db_stats: dict[str, int],
    window_minutes: int = _C1_HEALTH_STATUS_WINDOW_MINUTES,
) -> dict[str, Any]:
    ttl_seconds = _get_c1_health_cache_ttl_seconds()
    now = datetime.utcnow()
    cached_payload = _C1_HEALTH_RUNTIME_CACHE.get("payload")
    cached_at = _C1_HEALTH_RUNTIME_CACHE.get("computed_at")
    cached_compute_ms = int(_C1_HEALTH_RUNTIME_CACHE.get("compute_ms") or 0)
    cached_window_minutes = int(_C1_HEALTH_RUNTIME_CACHE.get("window_minutes") or window_minutes)
    if (
        ttl_seconds > 0
        and cached_payload is not None
        and isinstance(cached_at, datetime)
        and cached_window_minutes == int(window_minutes)
    ):
        age_seconds_float = max(0.0, (now - cached_at).total_seconds())
        age_seconds = int(age_seconds_float)
        if age_seconds_float <= float(ttl_seconds):
            return with_c1_health_meta(
                cached_payload,
                cached=True,
                cache_age_seconds=age_seconds,
                compute_ms=cached_compute_ms,
            )

    compute_started = perf_counter_ns()
    payload = await _compute_runtime_c1_health(db=db, db_stats=db_stats, window_minutes=window_minutes)
    compute_ms = int(max(0, (perf_counter_ns() - compute_started) // 1_000_000))
    computed_at = datetime.utcnow()
    _C1_HEALTH_RUNTIME_CACHE["payload"] = deepcopy(payload)
    _C1_HEALTH_RUNTIME_CACHE["computed_at"] = computed_at
    _C1_HEALTH_RUNTIME_CACHE["compute_ms"] = compute_ms
    _C1_HEALTH_RUNTIME_CACHE["window_minutes"] = int(window_minutes)
    return with_c1_health_meta(payload, cached=False, cache_age_seconds=0, compute_ms=compute_ms)
