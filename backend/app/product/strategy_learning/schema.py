from __future__ import annotations

from typing import Any

ALLOWED_POLICY_STAGES = {"GROWTH", "MONETIZATION", "RECOVERY"}
ALLOWED_LAYERS = {"A1", "A4", "A5"}
PATCH_KIND = "STRATEGY_V1"

REQUIRED_FIELDS = (
    "patch_id",
    "account_id",
    "window_id",
    "policy_stage",
    "inputs",
    "overrides",
    "active",
    "layers_applied",
    "reason_codes",
    "patch_kind",
    "generated_at",
)


class StrategyPatchValidationError(ValueError):
    """Erro de contrato para violações do schema de strategy patch."""


def _require_non_empty_str(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise StrategyPatchValidationError(f"ContractViolation: invalid required field '{field}'")
    return value.strip()


def validate_strategy_patch(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise StrategyPatchValidationError("ContractViolation: record must be an object")

    for field in REQUIRED_FIELDS:
        if field not in record:
            raise StrategyPatchValidationError(f"ContractViolation: missing required field '{field}'")

    normalized = dict(record)
    normalized["patch_id"] = _require_non_empty_str(normalized, "patch_id")
    normalized["account_id"] = _require_non_empty_str(normalized, "account_id")
    normalized["window_id"] = _require_non_empty_str(normalized, "window_id")
    normalized["policy_stage"] = _require_non_empty_str(normalized, "policy_stage")
    normalized["patch_kind"] = _require_non_empty_str(normalized, "patch_kind")
    normalized["generated_at"] = _require_non_empty_str(normalized, "generated_at")

    if normalized["policy_stage"] not in ALLOWED_POLICY_STAGES:
        raise StrategyPatchValidationError("SL_POLICY_STAGE_INVALID")
    if normalized["patch_kind"] != PATCH_KIND:
        raise StrategyPatchValidationError("ContractViolation: invalid patch_kind")

    if not isinstance(normalized.get("inputs"), dict):
        raise StrategyPatchValidationError("ContractViolation: inputs must be an object")
    if not isinstance(normalized.get("overrides"), dict):
        raise StrategyPatchValidationError("ContractViolation: overrides must be an object")

    if not isinstance(normalized.get("active"), bool):
        raise StrategyPatchValidationError("ContractViolation: active must be bool")

    layers = normalized.get("layers_applied")
    if not isinstance(layers, list):
        raise StrategyPatchValidationError("ContractViolation: layers_applied must be a list")
    for layer in layers:
        if layer not in ALLOWED_LAYERS:
            raise StrategyPatchValidationError("ContractViolation: invalid layer in layers_applied")

    reasons = normalized.get("reason_codes")
    if not isinstance(reasons, list) or any(not isinstance(item, str) or not item.strip() for item in reasons):
        raise StrategyPatchValidationError("ContractViolation: reason_codes must be a non-empty string list")

    allowed_override_keys = {"a1_prefs_override", "a4_defaults_override", "a5_rewrite_defaults_override"}
    for key, value in normalized["overrides"].items():
        if key not in allowed_override_keys:
            raise StrategyPatchValidationError("SL_OVERRIDE_NOT_ALLOWED")
        if not isinstance(value, dict):
            raise StrategyPatchValidationError("ContractViolation: override payload must be an object")

    return normalized

