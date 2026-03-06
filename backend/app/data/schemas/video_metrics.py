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
    """Erro de contrato para registros de video_metrics."""


def validate_video_metrics(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise VideoMetricsValidationError("ContractViolation: record must be an object")

    normalized = dict(record)
    for field in REQUIRED_FIELDS:
        if field not in normalized:
            raise VideoMetricsValidationError(f"ContractViolation: missing required field '{field}'")

    for field in ("video_id", "account_id", "captured_at", "captured_window_id", "source_kind", "ingested_at"):
        value = normalized.get(field)
        if not isinstance(value, str) or not value.strip():
            raise VideoMetricsValidationError(f"ContractViolation: invalid required field '{field}'")
        normalized[field] = value.strip()

    if normalized["source_kind"] not in ALLOWED_SOURCE_KINDS:
        raise VideoMetricsValidationError("ContractViolation: invalid source_kind")

    views = normalized.get("views")
    if not isinstance(views, int) or views < 0:
        raise VideoMetricsValidationError("ContractViolation: invalid views")

    for field in ("likes", "follows"):
        value = normalized.get(field)
        if value is not None and (not isinstance(value, int) or value < 0):
            raise VideoMetricsValidationError(f"ContractViolation: invalid {field}")

    for field in ("retention_3s", "completion_rate"):
        value = normalized.get(field)
        if value is not None and (not isinstance(value, (int, float)) or value < 0 or value > 1):
            raise VideoMetricsValidationError(f"ContractViolation: invalid {field}")

    rpm = normalized.get("rpm")
    if rpm is not None and (not isinstance(rpm, (int, float)) or rpm < 0):
        raise VideoMetricsValidationError("ContractViolation: invalid rpm")

    normalized.setdefault("provider", "")
    normalized.setdefault("external_video_id", normalized["video_id"])
    return normalized
