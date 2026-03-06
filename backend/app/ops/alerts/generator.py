from __future__ import annotations

from app.ops.alerts.models import AlertRecord
from app.ops.slo.schema import SLOEvaluationResult


def generate_alerts(evaluation: SLOEvaluationResult) -> list[AlertRecord]:
    """Gera alertas acionaveis a partir da avaliacao consolidada."""
    alerts: list[AlertRecord] = []
    for metric in evaluation.metrics:
        if metric.status == "PASS":
            continue
        alerts.append(
            AlertRecord(
                alert_code=f"ALERT_{metric.metric_name.upper()}",
                severity=metric.severity,
                metric_name=metric.metric_name,
                reason_code=metric.reason_code,
                action=_action_for_severity(metric.severity),
                value=metric.value,
                details={
                    "target": metric.threshold.target,
                    "warn_threshold": metric.threshold.warn_threshold,
                    "critical_threshold": metric.threshold.critical_threshold,
                },
            )
        )
        if metric.budget_consumed_ratio is not None and metric.budget_consumed_ratio >= 1.0:
            alerts.append(
                AlertRecord(
                    alert_code=f"BUDGET_{metric.metric_name.upper()}",
                    severity="CRITICAL",
                    metric_name=metric.metric_name,
                    reason_code=f"{metric.metric_name.upper()}_BUDGET_EXHAUSTED",
                    action="INVESTIGATE",
                    value=metric.budget_consumed_ratio,
                    details={"budget_consumed_ratio": metric.budget_consumed_ratio},
                )
            )
    return alerts


def _action_for_severity(severity: str) -> str:
    if severity == "CRITICAL":
        return "BLOCK"
    if severity == "WARN":
        return "DEGRADE"
    return "OBSERVE"
