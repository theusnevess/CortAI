from __future__ import annotations

from typing import Any

REQUIRED_FIELDS = (
    "window_id",
    "account_id",
    "videos_considered",
    "avg_views",
    "total_views",
    "computed_at",
)


class WindowMetricsValidationError(ValueError):
    """Erro de contrato para violacoes do schema de window_metrics."""


def _require_non_empty_str(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise WindowMetricsValidationError(f"ContractViolation: invalid required field '{field}'")
    return value.strip()


def _coerce_int(record: dict[str, Any], field: str, *, required: bool = False) -> int | None:
    value = record.get(field)
    if value is None and not required:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise WindowMetricsValidationError(f"ContractViolation: invalid integer field '{field}'") from exc
    return parsed


def _coerce_float(record: dict[str, Any], field: str, *, required: bool = False) -> float | None:
    value = record.get(field)
    if value is None and not required:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise WindowMetricsValidationError(f"ContractViolation: invalid float field '{field}'") from exc
    return parsed


def validate_window_metrics(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise WindowMetricsValidationError("ContractViolation: record must be an object")

    for field in REQUIRED_FIELDS:
        if field not in record:
            raise WindowMetricsValidationError(f"ContractViolation: missing required field '{field}'")

    normalized = dict(record)
    normalized["window_id"] = _require_non_empty_str(normalized, "window_id")
    normalized["account_id"] = _require_non_empty_str(normalized, "account_id")
    normalized["computed_at"] = _require_non_empty_str(normalized, "computed_at")

    normalized["videos_considered"] = _coerce_int(normalized, "videos_considered", required=True)
    if normalized["videos_considered"] is None or normalized["videos_considered"] < 0:
        raise WindowMetricsValidationError("ContractViolation: videos_considered must be >= 0")

    normalized["avg_views"] = _coerce_float(normalized, "avg_views", required=True)
    if normalized["avg_views"] is None or normalized["avg_views"] < 0:
        raise WindowMetricsValidationError("ContractViolation: avg_views must be >= 0")

    normalized["avg_retention_3s"] = _coerce_float(normalized, "avg_retention_3s")
    if normalized["avg_retention_3s"] is not None and not (0.0 <= normalized["avg_retention_3s"] <= 1.0):
        raise WindowMetricsValidationError("ContractViolation: avg_retention_3s out of range [0,1]")

    normalized["avg_completion_rate"] = _coerce_float(normalized, "avg_completion_rate")
    if normalized["avg_completion_rate"] is not None and not (0.0 <= normalized["avg_completion_rate"] <= 1.0):
        raise WindowMetricsValidationError("ContractViolation: avg_completion_rate out of range [0,1]")

    normalized["avg_rpm"] = _coerce_float(normalized, "avg_rpm")
    if normalized["avg_rpm"] is not None and normalized["avg_rpm"] < 0:
        raise WindowMetricsValidationError("ContractViolation: avg_rpm must be >= 0 when provided")

    normalized["total_views"] = _coerce_int(normalized, "total_views", required=True)
    if normalized["total_views"] is None or normalized["total_views"] < 0:
        raise WindowMetricsValidationError("ContractViolation: total_views must be >= 0")

    normalized["total_follows"] = _coerce_int(normalized, "total_follows")
    if normalized["total_follows"] is not None and normalized["total_follows"] < 0:
        raise WindowMetricsValidationError("ContractViolation: total_follows must be >= 0 when provided")

    return normalized
