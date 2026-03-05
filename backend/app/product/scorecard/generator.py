from __future__ import annotations

from typing import Any

from app.product.scorecard.schema import validate_scorecard


def _resolve_status_and_recommendation(window_metrics: dict[str, Any]) -> tuple[str, str]:
    retention = window_metrics.get("avg_retention_3s")
    completion = window_metrics.get("avg_completion_rate")
    views = float(window_metrics.get("avg_views") or 0.0)

    if retention is not None and float(retention) < 0.35:
        return "RECOVERY", "MODO_RECUPERACAO"
    if completion is not None and float(completion) < 0.30:
        return "OPTIMIZE", "OTIMIZAR_HOOKS"
    if views < 200:
        return "OPTIMIZE", "AUMENTAR_DISTRIBUICAO"
    return "STABLE", "MANTER_ESTRATEGIA"


def generate_real_batch_scorecard(
    *,
    window_metrics: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    """Gera scorecard a partir de window_metrics de forma determinística."""
    status, recommendation = _resolve_status_and_recommendation(window_metrics)
    candidate = {
        "account_id": window_metrics.get("account_id"),
        "window_id": window_metrics.get("window_id"),
        "videos_considered": window_metrics.get("videos_considered"),
        "avg_views": window_metrics.get("avg_views"),
        "avg_retention_3s": window_metrics.get("avg_retention_3s"),
        "avg_completion_rate": window_metrics.get("avg_completion_rate"),
        "avg_rpm": window_metrics.get("avg_rpm"),
        "status": status,
        "recommendation": recommendation,
        "generated_at": generated_at,
    }
    return validate_scorecard(candidate)

