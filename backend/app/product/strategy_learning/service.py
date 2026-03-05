from __future__ import annotations

from typing import Any

from app.product.strategy_learning.learner import learn_strategy_patch
from app.product.strategy_learning.repo import save_if_absent
from app.product.strategy_learning.schema import validate_strategy_patch

_ALLOWED_OVERRIDE_KEYS = {"a1_prefs_override", "a4_defaults_override", "a5_rewrite_defaults_override"}


def _apply_override_whitelist(
    patch: dict[str, Any],
    proposed_overrides: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    if not proposed_overrides:
        return patch

    forbidden = [key for key in proposed_overrides if key not in _ALLOWED_OVERRIDE_KEYS]
    if forbidden:
        reasons = set(str(item) for item in patch.get("reason_codes", []))
        reasons.add("SL_OVERRIDE_NOT_ALLOWED")
        patch["active"] = False
        patch["layers_applied"] = []
        patch["overrides"] = {
            "a1_prefs_override": {},
            "a4_defaults_override": {},
            "a5_rewrite_defaults_override": {},
        }
        patch["reason_codes"] = sorted(reasons)
        return patch

    merged_overrides = dict(patch.get("overrides", {}))
    layers = set(str(item) for item in patch.get("layers_applied", []))
    for key, value in proposed_overrides.items():
        if value:
            current = merged_overrides.get(key, {})
            if not isinstance(current, dict):
                current = {}
            merged = dict(current)
            merged.update(value)
            merged_overrides[key] = merged
            if key == "a1_prefs_override":
                layers.add("A1")
            elif key == "a4_defaults_override":
                layers.add("A4")
            elif key == "a5_rewrite_defaults_override":
                layers.add("A5")

    patch["overrides"] = merged_overrides
    patch["layers_applied"] = sorted(layers)
    if patch["layers_applied"]:
        patch["active"] = True
    return patch


def generate_and_save_strategy_patch(
    *,
    scorecard: dict[str, Any] | None,
    window_metrics: dict[str, Any] | None,
    attributions: list[dict[str, Any]],
    policy_stage: str,
    generated_at: str | None = None,
    path: Any = None,
    proposed_overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Orquestra learner + whitelist + persistência idempotente."""
    patch = learn_strategy_patch(
        scorecard=scorecard,
        window_metrics=window_metrics,
        attributions=attributions,
        policy_stage=policy_stage,
        generated_at=generated_at,
    )
    patch = _apply_override_whitelist(patch, proposed_overrides)
    patch = validate_strategy_patch(patch)
    write_action = save_if_absent(patch, path=path)
    return {"patch": patch, "write_action": write_action}

