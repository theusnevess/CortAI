from __future__ import annotations

from typing import Any

ALLOWED_POLICY_STAGES = {"GROWTH", "MONETIZATION", "RECOVERY"}

REQUIRED_BASE_FIELDS = (
    "attribution_id",
    "account_id",
    "publish_id",
    "video_id",
    "job_id",
    "window_id",
    "policy_stage",
    "hook_strategy",
    "human_patch_detected",
    "views",
    "retention_3s",
    "completion_rate",
    "captured_at",
    "generated_at",
)

OPTIONAL_ENRICHMENT_FIELDS = (
    "dominant_failure_reason",
    "effective_duration_s",
    "rare_fact_placement_s",
    "likes",
    "follows",
    "rpm",
)


class AttributionValidationError(ValueError):
    """Erro de contrato para violacoes do schema de content attribution."""


def _require_non_empty_str(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise AttributionValidationError(f"ContractViolation: invalid required field '{field}'")
    return value.strip()


def _coerce_int(record: dict[str, Any], field: str, *, required: bool = False) -> int | None:
    value = record.get(field)
    if value is None and not required:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise AttributionValidationError(f"ContractViolation: invalid integer field '{field}'") from exc
    return parsed


def _coerce_float(record: dict[str, Any], field: str, *, required: bool = False) -> float | None:
    value = record.get(field)
    if value is None and not required:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise AttributionValidationError(f"ContractViolation: invalid float field '{field}'") from exc
    return parsed


def validate_content_attribution(record: dict[str, Any]) -> dict[str, Any]:
    """Valida o payload canonico do content attribution v1.0."""
    if not isinstance(record, dict):
        raise AttributionValidationError("ContractViolation: record must be an object")

    for field in REQUIRED_BASE_FIELDS:
        if field not in record:
            raise AttributionValidationError(f"ContractViolation: missing required field '{field}'")

    normalized = dict(record)
    normalized["attribution_id"] = _require_non_empty_str(normalized, "attribution_id")
    normalized["account_id"] = _require_non_empty_str(normalized, "account_id")
    normalized["publish_id"] = _require_non_empty_str(normalized, "publish_id")
    normalized["video_id"] = _require_non_empty_str(normalized, "video_id")
    normalized["job_id"] = _require_non_empty_str(normalized, "job_id")
    normalized["window_id"] = _require_non_empty_str(normalized, "window_id")
    normalized["policy_stage"] = _require_non_empty_str(normalized, "policy_stage")
    normalized["hook_strategy"] = _require_non_empty_str(normalized, "hook_strategy")
    normalized["captured_at"] = _require_non_empty_str(normalized, "captured_at")
    normalized["generated_at"] = _require_non_empty_str(normalized, "generated_at")

    if normalized["policy_stage"] not in ALLOWED_POLICY_STAGES:
        raise AttributionValidationError("ContractViolation: invalid policy_stage")

    normalized["dominant_failure_reason"] = normalized.get("dominant_failure_reason")
    if normalized["dominant_failure_reason"] is not None and not isinstance(
        normalized["dominant_failure_reason"], str
    ):
        raise AttributionValidationError("ContractViolation: dominant_failure_reason must be string or null")

    normalized["human_patch_detected"] = bool(normalized.get("human_patch_detected"))

    normalized["effective_duration_s"] = _coerce_int(normalized, "effective_duration_s")
    if normalized["effective_duration_s"] is not None and normalized["effective_duration_s"] <= 0:
        raise AttributionValidationError("ContractViolation: effective_duration_s must be > 0")

    normalized["rare_fact_placement_s"] = _coerce_int(normalized, "rare_fact_placement_s")
    if normalized["rare_fact_placement_s"] is not None and normalized["rare_fact_placement_s"] < 0:
        raise AttributionValidationError("ContractViolation: rare_fact_placement_s must be >= 0")
    if (
        normalized["rare_fact_placement_s"] is not None
        and normalized["effective_duration_s"] is not None
        and normalized["rare_fact_placement_s"] > normalized["effective_duration_s"]
    ):
        raise AttributionValidationError(
            "ContractViolation: rare_fact_placement_s cannot be greater than effective_duration_s"
        )

    normalized["views"] = _coerce_int(normalized, "views", required=True)
    if normalized["views"] is None or normalized["views"] < 0:
        raise AttributionValidationError("ContractViolation: views must be >= 0")

    normalized["likes"] = _coerce_int(normalized, "likes")
    if normalized["likes"] is not None and normalized["likes"] < 0:
        raise AttributionValidationError("ContractViolation: likes must be >= 0")

    normalized["follows"] = _coerce_int(normalized, "follows")
    if normalized["follows"] is not None and normalized["follows"] < 0:
        raise AttributionValidationError("ContractViolation: follows must be >= 0")

    normalized["retention_3s"] = _coerce_float(normalized, "retention_3s", required=True)
    if normalized["retention_3s"] is None or not (0.0 <= normalized["retention_3s"] <= 1.0):
        raise AttributionValidationError("ContractViolation: retention_3s out of range [0,1]")

    normalized["completion_rate"] = _coerce_float(normalized, "completion_rate", required=True)
    if normalized["completion_rate"] is None or not (0.0 <= normalized["completion_rate"] <= 1.0):
        raise AttributionValidationError("ContractViolation: completion_rate out of range [0,1]")

    normalized["rpm"] = _coerce_float(normalized, "rpm")
    if normalized["rpm"] is not None and normalized["rpm"] < 0:
        raise AttributionValidationError("ContractViolation: rpm must be >= 0")

    return normalized
