from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.product.strategy_apply.errors import StrategyApplyConflictError, StrategyApplyWhitelistError
from app.product.strategy_apply.service import StrategyApplyDeps, apply_strategy_patch
from app.product.strategy_learning.schema import StrategyPatchValidationError


def _patch(*, patch_id: str = "sp_1", policy_stage: str = "GROWTH", active: bool = True) -> dict[str, Any]:
    return {
        "patch_id": patch_id,
        "account_id": "acc_001",
        "window_id": "w_001",
        "policy_stage": policy_stage,
        "inputs": {"window_metrics_id": "wm_1", "scorecard_id": "sc_1", "attribution_count": 8},
        "overrides": {
            "a1_prefs_override": {"topic_bias": "misterio"},
            "a4_defaults_override": {"hook_style": "curiosity_gap"},
            "a5_rewrite_defaults_override": {"rewrite_flags": {"tighten": True}},
        },
        "active": active,
        "layers_applied": ["A1", "A4", "A5"] if active else [],
        "reason_codes": ["HOOK_STRATEGY_CONSISTENT"] if active else ["NO_STRONG_SIGNAL"],
        "patch_kind": "STRATEGY_V1",
        "generated_at": "2026-03-05T03:00:00Z",
    }


def _registry(*, stage: str = "GROWTH") -> dict[str, Any]:
    return {
        "account_id": "acc_001",
        "account_policy": {"stage": stage, "config": {"a4_defaults_override": {"hook_style": "neutral"}}},
        "defaults_by_stage": {
            "GROWTH": {
                "a1_prefs_override": {"topic_bias": "base"},
                "a4_defaults_override": {"hook_style": "default", "max_words_preferred": 12},
            }
        },
        "strategy_overrides": {"active": {}, "history": []},
        "effective_config": {},
    }


class InMemoryDeps:
    def __init__(self, registry: dict[str, Any]) -> None:
        self.registry = registry
        self.applications: list[dict[str, Any]] = []
        self.events: list[tuple[str, dict[str, Any]]] = []

    def get_registry(self, account_id: str) -> dict[str, Any]:
        return dict(self.registry)

    def save_registry(self, account_id: str, state: dict[str, Any]) -> None:
        self.registry = dict(state)

    def get_existing_application(self, account_id: str, window_id: str, policy_stage: str) -> dict[str, Any] | None:
        for row in reversed(self.applications):
            if (
                row.get("account_id") == account_id
                and row.get("window_id") == window_id
                and row.get("policy_stage") == policy_stage
                and row.get("status") in {"APPLIED", "ROLLED_BACK"}
            ):
                return row
        return None

    def save_application_record(self, record: dict[str, Any]) -> None:
        self.applications.append(dict(record))

    def emit_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append((event_type, dict(payload)))

    def to_deps(self) -> StrategyApplyDeps:
        return StrategyApplyDeps(
            get_registry=self.get_registry,
            save_registry=self.save_registry,
            get_existing_application=self.get_existing_application,
            save_application_record=self.save_application_record,
            emit_event=self.emit_event,
        )


class StrategyPatchApplicationD11Tests(unittest.TestCase):
    def test_happy_path_aplica_patch(self) -> None:
        memory = InMemoryDeps(_registry(stage="GROWTH"))
        result = apply_strategy_patch(
            account_id="acc_001",
            window_id="w_001",
            patch=_patch(),
            deps=memory.to_deps(),
        )
        self.assertEqual(result.status, "APPLIED")
        self.assertEqual(memory.registry["strategy_overrides"]["last_action"], "APPLY")
        self.assertEqual(memory.registry["effective_config"]["a4_defaults_override"]["hook_style"], "curiosity_gap")
        self.assertTrue(any(evt == "SL/strategy_patch_applied" for evt, _ in memory.events))

    def test_stage_mismatch_retorna_noop(self) -> None:
        memory = InMemoryDeps(_registry(stage="MONETIZATION"))
        result = apply_strategy_patch(
            account_id="acc_001",
            window_id="w_001",
            patch=_patch(policy_stage="GROWTH"),
            deps=memory.to_deps(),
        )
        self.assertEqual(result.status, "NOOP")
        self.assertEqual(result.reason_code, "STAGE_MISMATCH")

    def test_whitelist_violation_erro_explicito(self) -> None:
        memory = InMemoryDeps(_registry(stage="GROWTH"))
        invalid = _patch()
        invalid["overrides"]["a4_defaults_override"]["max_retry"] = 9
        with self.assertRaises(StrategyApplyWhitelistError):
            apply_strategy_patch(
                account_id="acc_001",
                window_id="w_001",
                patch=invalid,
                deps=memory.to_deps(),
            )

    def test_idempotencia_noop_payload_igual(self) -> None:
        memory = InMemoryDeps(_registry(stage="GROWTH"))
        first = apply_strategy_patch(
            account_id="acc_001",
            window_id="w_001",
            patch=_patch(),
            deps=memory.to_deps(),
        )
        second = apply_strategy_patch(
            account_id="acc_001",
            window_id="w_001",
            patch=_patch(),
            deps=memory.to_deps(),
        )
        self.assertEqual(first.status, "APPLIED")
        self.assertEqual(second.status, "NOOP")
        self.assertEqual(second.reason_code, "IDEMPOTENT_NOOP")

    def test_conflict_payload_diferente(self) -> None:
        memory = InMemoryDeps(_registry(stage="GROWTH"))
        first_patch = _patch(patch_id="sp_1")
        second_patch = _patch(patch_id="sp_1")
        second_patch["overrides"]["a4_defaults_override"]["hook_style"] = "shock"
        apply_strategy_patch(
            account_id="acc_001",
            window_id="w_001",
            patch=first_patch,
            deps=memory.to_deps(),
        )
        with self.assertRaises(StrategyApplyConflictError):
            apply_strategy_patch(
                account_id="acc_001",
                window_id="w_001",
                patch=second_patch,
                deps=memory.to_deps(),
            )

    def test_rollback_quando_proxima_janela_red(self) -> None:
        memory = InMemoryDeps(_registry(stage="GROWTH"))
        result = apply_strategy_patch(
            account_id="acc_001",
            window_id="w_001",
            patch=_patch(active=True),
            deps=memory.to_deps(),
            next_window_scorecard={"performance_color": "RED"},
        )
        self.assertEqual(result.status, "ROLLED_BACK")
        self.assertEqual(memory.registry["strategy_overrides"]["active"], {})
        self.assertTrue(any(evt == "SL/strategy_patch_rolled_back" for evt, _ in memory.events))

    def test_merge_precedence_defaults_policy_overrides(self) -> None:
        memory = InMemoryDeps(_registry(stage="GROWTH"))
        patch = _patch()
        patch["overrides"]["a4_defaults_override"]["hook_style"] = "override_final"
        result = apply_strategy_patch(
            account_id="acc_001",
            window_id="w_001",
            patch=patch,
            deps=memory.to_deps(),
        )
        effective = memory.registry["effective_config"]["a4_defaults_override"]
        self.assertEqual(result.status, "APPLIED")
        self.assertEqual(effective["hook_style"], "override_final")
        self.assertEqual(effective["max_words_preferred"], 12)

    def test_stage_invalido_retorna_erro_canonic(self) -> None:
        memory = InMemoryDeps(_registry(stage="GROWTH"))
        with self.assertRaises(StrategyPatchValidationError) as ctx:
            apply_strategy_patch(
                account_id="acc_001",
                window_id="w_001",
                patch=_patch(policy_stage="INVALID_STAGE"),
                deps=memory.to_deps(),
            )
        self.assertEqual(str(ctx.exception), "SL_POLICY_STAGE_INVALID")


if __name__ == "__main__":
    unittest.main()
