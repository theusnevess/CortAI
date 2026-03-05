from __future__ import annotations

from typing import Any


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def merge_effective_config(
    *,
    defaults_by_stage: dict[str, Any],
    account_policy: dict[str, Any],
    strategy_overrides: dict[str, Any],
) -> dict[str, Any]:
    """Mescla configuração efetiva na ordem: defaults < policy < overrides."""
    stage = str(account_policy.get("stage") or "")
    stage_defaults = defaults_by_stage.get(stage, {})
    if not isinstance(stage_defaults, dict):
        stage_defaults = {}

    policy_config = account_policy.get("config", {})
    if not isinstance(policy_config, dict):
        policy_config = {}

    active_overrides = strategy_overrides.get("active", {})
    if not isinstance(active_overrides, dict):
        active_overrides = {}

    merged = _deep_merge(stage_defaults, policy_config)
    merged = _deep_merge(merged, active_overrides)
    return merged

