from __future__ import annotations

from typing import Any

ALLOWED_OVERRIDE_TOP_KEYS = {"a1_prefs_override", "a4_defaults_override", "a5_rewrite_defaults_override"}
FORBIDDEN_FIELDS = {"policy_stage", "allocation", "retention_floor", "max_retry"}


def _contains_forbidden_fields(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_FIELDS:
                return True
            if _contains_forbidden_fields(value):
                return True
    elif isinstance(payload, list):
        for item in payload:
            if _contains_forbidden_fields(item):
                return True
    return False


def validate_strategy_overrides_whitelist(overrides: dict[str, Any]) -> None:
    if not isinstance(overrides, dict):
        raise ValueError("STRATEGY_PATCH_WHITELIST_VIOLATION")

    for key, value in overrides.items():
        if key not in ALLOWED_OVERRIDE_TOP_KEYS:
            raise ValueError("STRATEGY_PATCH_WHITELIST_VIOLATION")
        if not isinstance(value, dict):
            raise ValueError("STRATEGY_PATCH_WHITELIST_VIOLATION")
        if _contains_forbidden_fields(value):
            raise ValueError("STRATEGY_PATCH_WHITELIST_VIOLATION")


def apply_strategy_overrides(*, registry: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    updated = dict(registry)
    strategy_overrides = dict(updated.get("strategy_overrides", {}))
    active = dict(strategy_overrides.get("active", {}))
    patch_overrides = patch.get("overrides", {})
    for key in ALLOWED_OVERRIDE_TOP_KEYS:
        value = patch_overrides.get(key, {})
        if isinstance(value, dict):
            active[key] = dict(value)

    history = list(strategy_overrides.get("history", []))
    history.append(
        {
            "patch_id": patch.get("patch_id"),
            "window_id": patch.get("window_id"),
            "policy_stage": patch.get("policy_stage"),
        }
    )
    strategy_overrides["active"] = active
    strategy_overrides["history"] = history
    strategy_overrides["last_action"] = "APPLY"
    updated["strategy_overrides"] = strategy_overrides
    return updated

