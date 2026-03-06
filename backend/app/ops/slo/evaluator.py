from __future__ import annotations

from app.ops.slo.schema import SLOEvaluationResult, SLOMetricResult, SLOThreshold
from app.ops.slo.thresholds import default_slo_thresholds


def evaluate_slos(
    metrics: dict[str, float | int],
    *,
    thresholds: list[SLOThreshold] | None = None,
) -> SLOEvaluationResult:
    """Avalia metricas operacionais contra thresholds congelados."""
    active_thresholds = thresholds or default_slo_thresholds()
    metric_results: list[SLOMetricResult] = []
    missing_metrics: list[str] = []

    for threshold in active_thresholds:
        raw_value = metrics.get(threshold.metric_name)
        if raw_value is None:
            missing_metrics.append(threshold.metric_name)
            continue
        metric_results.append(_evaluate_metric(float(raw_value), threshold))

    overall_status = _overall_status(metric_results)
    return SLOEvaluationResult(
        overall_status=overall_status,
        metrics=metric_results,
        missing_metrics=missing_metrics,
    )


def metrics_from_load_results(load_report: dict) -> dict[str, float]:
    """Extrai metricas operacionais basicas a partir do relatorio do D18."""
    scenarios = list(load_report.get("scenarios", []))
    if not scenarios:
        return {}

    total_ops = sum(int(item.get("total_ops", 0)) for item in scenarios) or 1
    total_errors = sum(int(item.get("error_count", 0)) for item in scenarios)
    weighted_fallback = sum(float(item.get("fallback_hit_rate", 0.0)) * int(item.get("total_ops", 0)) for item in scenarios)
    weighted_lease = sum(float(item.get("lease_contention_rate", 0.0)) * int(item.get("total_ops", 0)) for item in scenarios)
    weighted_conflict = sum(float(item.get("idempotency_conflict_rate", 0.0)) * int(item.get("total_ops", 0)) for item in scenarios)

    event_query_p95 = 0.0
    window_pipeline_success_rate = 1.0
    window_post_pipeline_success_rate = 1.0

    for item in scenarios:
        latency = item.get("latency", {})
        event_query = latency.get("event_query_latency_ms")
        if isinstance(event_query, dict):
            event_query_p95 = max(event_query_p95, float(event_query.get("p95_ms", 0.0)))
        success_count = int(item.get("success_count", 0))
        ops = max(int(item.get("total_ops", 0)), 1)
        success_rate = success_count / ops
        window_pipeline_success_rate = min(window_pipeline_success_rate, success_rate)
        window_post_pipeline_success_rate = min(window_post_pipeline_success_rate, success_rate)

    return {
        "event_query_p95_ms": round(event_query_p95, 4),
        "event_query_error_rate": round(total_errors / total_ops, 4),
        "event_query_fallback_rate": round(weighted_fallback / total_ops, 4),
        "lease_denied_rate": round(weighted_lease / total_ops, 4),
        "strategy_patch_conflict_rate": round(weighted_conflict / total_ops, 4),
        "window_pipeline_success_rate": round(window_pipeline_success_rate, 4),
        "window_post_pipeline_success_rate": round(window_post_pipeline_success_rate, 4),
    }


def _evaluate_metric(value: float, threshold: SLOThreshold) -> SLOMetricResult:
    if threshold.direction == "zero_tolerance":
        if value > 0:
            return SLOMetricResult(
                metric_name=threshold.metric_name,
                value=value,
                status="CRITICAL",
                severity="CRITICAL",
                reason_code=f"{threshold.metric_name.upper()}_BREACH",
                threshold=threshold,
                budget_consumed_ratio=None,
            )
        return SLOMetricResult(
            metric_name=threshold.metric_name,
            value=value,
            status="PASS",
            severity="INFO",
            reason_code=f"{threshold.metric_name.upper()}_OK",
            threshold=threshold,
            budget_consumed_ratio=None,
        )

    if threshold.direction == "lower_is_better":
        if value >= threshold.critical_threshold:
            status = "CRITICAL"
            severity = "CRITICAL"
            reason_code = f"{threshold.metric_name.upper()}_CRITICAL"
        elif value >= threshold.warn_threshold:
            status = "WARN"
            severity = "WARN"
            reason_code = f"{threshold.metric_name.upper()}_WARN"
        else:
            status = "PASS"
            severity = "INFO"
            reason_code = f"{threshold.metric_name.upper()}_OK"
        budget_ratio = round(value / threshold.budget, 4) if threshold.budget else None
        return SLOMetricResult(
            metric_name=threshold.metric_name,
            value=value,
            status=status,
            severity=severity,
            reason_code=reason_code,
            threshold=threshold,
            budget_consumed_ratio=budget_ratio,
        )

    if value <= threshold.critical_threshold:
        status = "CRITICAL"
        severity = "CRITICAL"
        reason_code = f"{threshold.metric_name.upper()}_CRITICAL"
    elif value <= threshold.warn_threshold:
        status = "WARN"
        severity = "WARN"
        reason_code = f"{threshold.metric_name.upper()}_WARN"
    else:
        status = "PASS"
        severity = "INFO"
        reason_code = f"{threshold.metric_name.upper()}_OK"

    return SLOMetricResult(
        metric_name=threshold.metric_name,
        value=value,
        status=status,
        severity=severity,
        reason_code=reason_code,
        threshold=threshold,
        budget_consumed_ratio=None,
    )


def _overall_status(results: list[SLOMetricResult]) -> str:
    if any(result.status == "CRITICAL" for result in results):
        return "CRITICAL"
    if any(result.status == "WARN" for result in results):
        return "WARN"
    return "PASS"
