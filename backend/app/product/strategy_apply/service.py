from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from app.product.strategy_apply.errors import StrategyApplyConflictError, StrategyApplyWhitelistError
from app.product.strategy_apply.models import StrategyPatchApplyResult
from app.product.strategy_learning.schema import validate_strategy_patch
from app.registry.merge_effective_config import merge_effective_config
from app.registry.strategy_overrides import apply_strategy_overrides, validate_strategy_overrides_whitelist
from app.observability.event_append.service import append_event, build_event_record


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_payload(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _default_event_sink(event_type: str, payload: dict[str, Any]) -> None:
    event = build_event_record(event_type, payload, writer_id="strategy_apply")
    append_event(event)


@dataclass(frozen=True)
class StrategyApplyDeps:
    """Dependências injetáveis para aplicação de patch."""

    get_registry: Callable[[str], dict[str, Any]]
    save_registry: Callable[[str, dict[str, Any]], None]
    get_existing_application: Callable[[str, str, str], dict[str, Any] | None]
    save_application_record: Callable[[dict[str, Any]], None]
    emit_event: Callable[[str, dict[str, Any]], None] = _default_event_sink


def apply_strategy_patch(
    *,
    account_id: str,
    window_id: str,
    patch: dict[str, Any],
    deps: StrategyApplyDeps,
    next_window_scorecard: dict[str, Any] | None = None,
) -> StrategyPatchApplyResult:
    """Aplica strategy patch no registry com idempotência e rollback."""
    normalized_patch = validate_strategy_patch(patch)
    patch_stage = str(normalized_patch["policy_stage"])
    patch_id = str(normalized_patch["patch_id"])

    registry = deps.get_registry(account_id)
    account_policy = registry.get("account_policy", {})
    current_stage = str(account_policy.get("stage") or "")
    if current_stage != patch_stage:
        event_type = "SL/strategy_patch_noop"
        deps.emit_event(
            event_type,
            {
                "account_id": account_id,
                "window_id": window_id,
                "policy_stage": patch_stage,
                "patch_id": patch_id,
                "timestamp": _now_utc_iso(),
                "reason_code": "STAGE_MISMATCH",
            },
        )
        return StrategyPatchApplyResult(
            status="NOOP",
            reason_code="STAGE_MISMATCH",
            account_id=account_id,
            window_id=window_id,
            policy_stage=patch_stage,
            patch_id=patch_id,
            event_type=event_type,
            details={},
        )

    try:
        validate_strategy_overrides_whitelist(normalized_patch.get("overrides", {}))
    except ValueError as exc:
        raise StrategyApplyWhitelistError() from exc

    existing = deps.get_existing_application(account_id, window_id, patch_stage)
    if existing is not None:
        existing_payload = existing.get("patch_payload", {})
        if _canonical_payload(existing_payload) == _canonical_payload(normalized_patch):
            event_type = "SL/strategy_patch_noop"
            deps.emit_event(
                event_type,
                {
                    "account_id": account_id,
                    "window_id": window_id,
                    "policy_stage": patch_stage,
                    "patch_id": patch_id,
                    "timestamp": _now_utc_iso(),
                    "reason_code": "IDEMPOTENT_NOOP",
                },
            )
            return StrategyPatchApplyResult(
                status="NOOP",
                reason_code="IDEMPOTENT_NOOP",
                account_id=account_id,
                window_id=window_id,
                policy_stage=patch_stage,
                patch_id=patch_id,
                event_type=event_type,
                details={},
            )
        deps.emit_event(
            "SL/strategy_patch_conflict",
            {
                "account_id": account_id,
                "window_id": window_id,
                "policy_stage": patch_stage,
                "patch_id": patch_id,
                "timestamp": _now_utc_iso(),
            },
        )
        raise StrategyApplyConflictError()

    updated_registry = apply_strategy_overrides(registry=registry, patch=normalized_patch)
    updated_registry["effective_config"] = merge_effective_config(
        defaults_by_stage=updated_registry.get("defaults_by_stage", {}),
        account_policy=updated_registry.get("account_policy", {}),
        strategy_overrides=updated_registry.get("strategy_overrides", {}),
    )
    deps.save_registry(account_id, updated_registry)

    application_record = {
        "account_id": account_id,
        "window_id": window_id,
        "policy_stage": patch_stage,
        "patch_id": patch_id,
        "patch_payload": normalized_patch,
        "applied_at": _now_utc_iso(),
        "status": "APPLIED",
    }
    deps.save_application_record(application_record)
    deps.emit_event(
        "SL/strategy_patch_applied",
        {
            "account_id": account_id,
            "window_id": window_id,
            "policy_stage": patch_stage,
            "patch_id": patch_id,
            "timestamp": _now_utc_iso(),
        },
    )

    if normalized_patch.get("active") and next_window_scorecard is not None:
        performance_color = str(next_window_scorecard.get("performance_color") or "").upper()
        if performance_color == "RED":
            rollback_registry = dict(updated_registry)
            rollback_state = dict(rollback_registry.get("strategy_overrides", {}))
            rollback_state["active"] = {}
            rollback_state["last_action"] = "ROLLBACK"
            rollback_registry["strategy_overrides"] = rollback_state
            rollback_registry["effective_config"] = merge_effective_config(
                defaults_by_stage=rollback_registry.get("defaults_by_stage", {}),
                account_policy=rollback_registry.get("account_policy", {}),
                strategy_overrides=rollback_registry.get("strategy_overrides", {}),
            )
            deps.save_registry(account_id, rollback_registry)
            deps.save_application_record(
                {
                    "account_id": account_id,
                    "window_id": window_id,
                    "policy_stage": patch_stage,
                    "patch_id": patch_id,
                    "patch_payload": normalized_patch,
                    "applied_at": _now_utc_iso(),
                    "status": "ROLLED_BACK",
                    "rollback_reason": "NEXT_WINDOW_RED",
                }
            )
            deps.emit_event(
                "SL/strategy_patch_rolled_back",
                {
                    "account_id": account_id,
                    "window_id": window_id,
                    "policy_stage": patch_stage,
                    "patch_id": patch_id,
                    "timestamp": _now_utc_iso(),
                },
            )
            return StrategyPatchApplyResult(
                status="ROLLED_BACK",
                reason_code="NEXT_WINDOW_RED",
                account_id=account_id,
                window_id=window_id,
                policy_stage=patch_stage,
                patch_id=patch_id,
                event_type="SL/strategy_patch_rolled_back",
                details={},
            )

    return StrategyPatchApplyResult(
        status="APPLIED",
        reason_code="PATCH_APPLIED",
        account_id=account_id,
        window_id=window_id,
        policy_stage=patch_stage,
        patch_id=patch_id,
        event_type="SL/strategy_patch_applied",
        details={},
    )

