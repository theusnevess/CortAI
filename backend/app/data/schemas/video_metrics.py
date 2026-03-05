from __future__ import annotations

from typing import Any

ALLOWED_SOURCE_KINDS = {"PLATFORM_ANALYTICS", "SCRAPED_ANALYTICS", "MANUAL_ENTRY"}

REQUIRED_FIELDS = (
    "video_id",
    "account_id",
    "captured_at",
    "captured_window_id",
    "source_kind",
    "views",
    "ingested_at",
)


class VideoMetricsValidationError(ValueError):
    """Erro de contrato para violacoes do schema de video_metrics."""


def _require_non_empty_str(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise VideoMetricsValidationError(f"ContractViolation: invalid required field '{field}'")
    return value.strip()


def _coerce_int(record: dict[str, Any], field: str, *, required: bool = False) -> int | None:
    value = record.get(field)
    if value is None and not required:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise VideoMetricsValidationError(f"ContractViolation: invalid integer field '{field}'") from exc
    return parsed


def _coerce_float(record: dict[str, Any], field: str) -> float | None:
    value = record.get(field)
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise VideoMetricsValidationError(f"ContractViolation: invalid float field '{field}'") from exc
    return parsed


def validate_video_metrics(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise VideoMetricsValidationError("ContractViolation: record must be an object")

    for field in REQUIRED_FIELDS:
        if field not in record:
            raise VideoMetricsValidationError(f"ContractViolation: missing required field '{field}'")

    normalized = dict(record)
    normalized["video_id"] = _require_non_empty_str(normalized, "video_id")
    normalized["account_id"] = _require_non_empty_str(normalized, "account_id")
    normalized["captured_at"] = _require_non_empty_str(normalized, "captured_at")
    normalized["captured_window_id"] = _require_non_empty_str(normalized, "captured_window_id")
    normalized["source_kind"] = _require_non_empty_str(normalized, "source_kind")
    normalized["ingested_at"] = _require_non_empty_str(normalized, "ingested_at")

    if normalized["source_kind"] not in ALLOWED_SOURCE_KINDS:
        raise VideoMetricsValidationError("ContractViolation: invalid source_kind")

    normalized["views"] = _coerce_int(normalized, "views", required=True)
    if normalized["views"] is None or normalized["views"] < 0:
        raise VideoMetricsValidationError("ContractViolation: views must be >= 0")

    normalized["retention_3s"] = _coerce_float(normalized, "retention_3s")
    if normalized["retention_3s"] is not None and not (0.0 <= normalized["retention_3s"] <= 1.0):
        raise VideoMetricsValidationError("ContractViolation: retention_3s out of range [0,1]")

    normalized["completion_rate"] = _coerce_float(normalized, "completion_rate")
    if normalized["completion_rate"] is not None and not (0.0 <= normalized["completion_rate"] <= 1.0):
        raise VideoMetricsValidationError("ContractViolation: completion_rate out of range [0,1]")

    normalized["likes"] = _coerce_int(normalized, "likes", required=False)
    normalized["follows"] = _coerce_int(normalized, "follows", required=False)
    normalized["rpm"] = _coerce_float(normalized, "rpm")

    return normalized
