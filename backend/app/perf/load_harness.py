from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from app.perf.metrics import LatencySummary, summarize_latencies
from app.perf.report import write_load_report
from app.perf.scenarios import LoadScenario


WindowRunner = Callable[..., Any]
QueryRunner = Callable[..., Any]
RebuildRunner = Callable[..., Any]


@dataclass(frozen=True)
class LoadHarnessDeps:
    """Dependencias injetaveis do harness de carga."""

    window_pipeline_runner: WindowRunner
    window_post_pipeline_runner: WindowRunner
    query_runner: QueryRunner
    rebuild_runner: RebuildRunner | None = None


@dataclass(frozen=True)
class LoadHarnessResult:
    """Resultado consolidado por cenario de carga."""

    scenario_name: str
    total_ops: int
    success_count: int
    error_count: int
    throughput_ops_s: float
    lease_contention_rate: float
    idempotency_conflict_rate: float
    fallback_hit_rate: float
    error_rate: float
    latency: dict[str, LatencySummary] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["latency"] = {name: summary.to_dict() for name, summary in self.latency.items()}
        return payload


def run_load_suite(
    scenarios: list[LoadScenario],
    *,
    deps: LoadHarnessDeps,
    max_workers: int = 8,
    output_dir: Path | None = None,
) -> list[LoadHarnessResult]:
    """Executa a suite de carga e opcionalmente persiste relatorio."""
    results = [run_load_scenario(scenario, deps=deps, max_workers=max_workers) for scenario in scenarios]
    if output_dir is not None:
        write_load_report(results, output_dir=output_dir)
    return results


def run_load_scenario(
    scenario: LoadScenario,
    *,
    deps: LoadHarnessDeps,
    max_workers: int = 8,
) -> LoadHarnessResult:
    """Executa um cenario de carga deterministico para pipeline e query."""
    latency_samples: dict[str, list[float]] = {
        "window_pipeline_latency_ms": [],
        "window_post_pipeline_latency_ms": [],
        "event_query_latency_ms": [],
        "rebuild_latency_ms": [],
    }
    success_count = 0
    error_count = 0
    lease_denied_count = 0
    idempotency_conflict_count = 0
    fallback_hits = 0
    notes: list[str] = []

    def _run_window(account_index: int, window_index: int) -> None:
        nonlocal success_count, error_count, lease_denied_count, idempotency_conflict_count, fallback_hits
        account_id = f"acc_{account_index:03d}"
        window_id = f"w_{account_index:03d}_{window_index:03d}"
        start = perf_counter()
        first = _safe_call(
            deps.window_pipeline_runner,
            account_id=account_id,
            window_id=window_id,
            videos_per_account=scenario.videos_per_account,
            scenario_name=scenario.name,
        )
        latency_samples["window_pipeline_latency_ms"].append(_elapsed_ms(start))
        _accumulate_counters(first, counters={
            "success_count": lambda: _inc("success"),
            "error_count": lambda: _inc("error"),
            "lease_denied_count": lambda: _inc("lease"),
            "idempotency_conflict_count": lambda: _inc("conflict"),
            "fallback_hits": lambda: _inc("fallback"),
        })

        start = perf_counter()
        second = _safe_call(
            deps.window_post_pipeline_runner,
            account_id=account_id,
            window_id=window_id,
            videos_per_account=scenario.videos_per_account,
            scenario_name=scenario.name,
        )
        latency_samples["window_post_pipeline_latency_ms"].append(_elapsed_ms(start))
        _accumulate_counters(second, counters={
            "success_count": lambda: _inc("success"),
            "error_count": lambda: _inc("error"),
            "lease_denied_count": lambda: _inc("lease"),
            "idempotency_conflict_count": lambda: _inc("conflict"),
            "fallback_hits": lambda: _inc("fallback"),
        })

    def _run_query(query_index: int) -> None:
        nonlocal success_count, error_count, fallback_hits
        start = perf_counter()
        result = _safe_call(
            deps.query_runner,
            account_id=f"acc_{(query_index % max(1, scenario.account_count)) + 1:03d}",
            query_index=query_index,
            scenario_name=scenario.name,
            force_hot_store_failure=scenario.force_hot_store_failure,
        )
        latency_samples["event_query_latency_ms"].append(_elapsed_ms(start))
        _accumulate_counters(result, counters={
            "success_count": lambda: _inc("success"),
            "error_count": lambda: _inc("error"),
            "fallback_hits": lambda: _inc("fallback"),
        })

    counts = {"success": 0, "error": 0, "lease": 0, "conflict": 0, "fallback": 0}

    def _inc(name: str) -> None:
        counts[name] += 1

    started = perf_counter()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for account_index in range(1, scenario.account_count + 1):
            for window_index in range(1, scenario.windows_per_account + 1):
                futures.append(executor.submit(_run_window, account_index, window_index))
        for query_index in range(scenario.query_burst):
            futures.append(executor.submit(_run_query, query_index))
        for future in futures:
            future.result()

    if scenario.run_rebuild and deps.rebuild_runner is not None:
        start = perf_counter()
        rebuild_result = _safe_call(deps.rebuild_runner, scenario_name=scenario.name)
        latency_samples["rebuild_latency_ms"].append(_elapsed_ms(start))
        _accumulate_counters(rebuild_result, counters={
            "success_count": lambda: _inc("success"),
            "error_count": lambda: _inc("error"),
            "fallback_hits": lambda: _inc("fallback"),
        })
    elif scenario.run_rebuild:
        notes.append("rebuild_runner_not_configured")

    total_duration = max(perf_counter() - started, 0.001)
    total_ops = (scenario.total_windows * 2) + scenario.query_burst + (1 if scenario.run_rebuild else 0)
    success_count = counts["success"]
    error_count = counts["error"]
    lease_denied_count = counts["lease"]
    idempotency_conflict_count = counts["conflict"]
    fallback_hits = counts["fallback"]

    return LoadHarnessResult(
        scenario_name=scenario.name,
        total_ops=total_ops,
        success_count=success_count,
        error_count=error_count,
        throughput_ops_s=round(total_ops / total_duration, 3),
        lease_contention_rate=_rate(lease_denied_count, total_ops),
        idempotency_conflict_rate=_rate(idempotency_conflict_count, total_ops),
        fallback_hit_rate=_rate(fallback_hits, total_ops),
        error_rate=_rate(error_count, total_ops),
        latency={name: summarize_latencies(samples) for name, samples in latency_samples.items() if samples},
        notes=notes,
    )


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 3)


def _rate(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(count / total, 4)


def _safe_call(func: Callable[..., Any], **kwargs: Any) -> dict[str, Any]:
    try:
        result = func(**kwargs)
        if isinstance(result, dict):
            return result
        if hasattr(result, "to_dict"):
            return result.to_dict()
        return {"status": "OK", "result": result}
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "ERROR",
            "reason_code": str(exc) or exc.__class__.__name__,
            "error": exc.__class__.__name__,
        }


def _accumulate_counters(result: dict[str, Any], *, counters: dict[str, Callable[[], None]]) -> None:
    status = str(result.get("status", "")).upper()
    reason_code = str(result.get("reason_code", "")).upper()
    fallback_level = str(result.get("fallback_level", "")).upper()

    if status in {"ERROR", "FAILED", "FAILED_SCORECARD", "FAILED_ATTRIBUTION", "FAILED_LEARNING"}:
        counters.get("error_count", lambda: None)()
    else:
        counters.get("success_count", lambda: None)()

    if "LEASE" in reason_code and ("DENIED" in reason_code or "EXPIRED" in reason_code):
        counters.get("lease_denied_count", lambda: None)()

    if "CONFLICT" in status or "CONFLICT" in reason_code:
        counters.get("idempotency_conflict_count", lambda: None)()

    if fallback_level or result.get("fallback_used") or result.get("path_used") in {"INDEX", "SCANNER"}:
        counters.get("fallback_hits", lambda: None)()
