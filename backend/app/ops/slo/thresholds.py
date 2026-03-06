from __future__ import annotations

from app.ops.slo.schema import SLOThreshold


def default_slo_thresholds() -> list[SLOThreshold]:
    """Retorna thresholds operacionais congelados para o D19."""
    return [
        SLOThreshold(
            metric_name="event_query_p95_ms",
            description="Latencia p95 da Event Query",
            direction="lower_is_better",
            target=250.0,
            warn_threshold=250.0,
            critical_threshold=500.0,
        ),
        SLOThreshold(
            metric_name="event_query_error_rate",
            description="Taxa de erro da Event Query",
            direction="lower_is_better",
            target=0.005,
            warn_threshold=0.01,
            critical_threshold=0.05,
            budget=0.005,
        ),
        SLOThreshold(
            metric_name="event_query_fallback_rate",
            description="Taxa de fallback da Event Query",
            direction="lower_is_better",
            target=0.05,
            warn_threshold=0.10,
            critical_threshold=0.25,
        ),
        SLOThreshold(
            metric_name="window_pipeline_success_rate",
            description="Taxa de sucesso do window pipeline",
            direction="higher_is_better",
            target=0.99,
            warn_threshold=0.98,
            critical_threshold=0.95,
        ),
        SLOThreshold(
            metric_name="window_post_pipeline_success_rate",
            description="Taxa de sucesso do post pipeline",
            direction="higher_is_better",
            target=0.99,
            warn_threshold=0.98,
            critical_threshold=0.95,
        ),
        SLOThreshold(
            metric_name="lease_denied_rate",
            description="Taxa de contencao por lease",
            direction="lower_is_better",
            target=0.01,
            warn_threshold=0.05,
            critical_threshold=0.15,
        ),
        SLOThreshold(
            metric_name="strategy_patch_conflict_rate",
            description="Taxa de conflito de strategy patch",
            direction="lower_is_better",
            target=0.01,
            warn_threshold=0.02,
            critical_threshold=0.10,
        ),
        SLOThreshold(
            metric_name="double_apply_count",
            description="Double-apply deve ser zero",
            direction="zero_tolerance",
            target=0.0,
            warn_threshold=0.0,
            critical_threshold=0.0,
        ),
        SLOThreshold(
            metric_name="snapshot_partial_count",
            description="Snapshot parcial aceito deve ser zero",
            direction="zero_tolerance",
            target=0.0,
            warn_threshold=0.0,
            critical_threshold=0.0,
        ),
    ]
