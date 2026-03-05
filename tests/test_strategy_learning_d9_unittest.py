from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.product.strategy_learning.errors import StrategyPatchConflictError
from app.product.strategy_learning.schema import StrategyPatchValidationError
from app.product.strategy_learning.service import generate_and_save_strategy_patch
from app.product.strategy_learning.store_jsonl import read_all_patches


def _scorecard(status: str) -> dict[str, Any]:
    return {"scorecard_id": "sc_001", "account_id": "acc_ca_001", "window_id": "w_001", "status": status}


def _window_metrics(videos_with_metrics: int = 8) -> dict[str, Any]:
    return {
        "account_id": "acc_ca_001",
        "window_id": "w_001",
        "videos_with_metrics": videos_with_metrics,
    }


def _attributions_for_green() -> list[dict[str, Any]]:
    return [
        {"hook_strategy": "curiosity_gap", "dominant_failure_reason": "missing_number"},
        {"hook_strategy": "curiosity_gap", "dominant_failure_reason": "missing_number"},
        {"hook_strategy": "curiosity_gap", "dominant_failure_reason": "missing_number"},
        {"hook_strategy": "curiosity_gap", "dominant_failure_reason": "missing_number"},
        {"hook_strategy": "curiosity_gap", "dominant_failure_reason": "missing_number"},
    ]


def _attributions_low_signal() -> list[dict[str, Any]]:
    return [
        {"hook_strategy": "curiosity_gap", "dominant_failure_reason": "none"},
        {"hook_strategy": "story_arc", "dominant_failure_reason": "none"},
        {"hook_strategy": "listicle", "dominant_failure_reason": "none"},
        {"hook_strategy": "story_arc", "dominant_failure_reason": "none"},
        {"hook_strategy": "listicle", "dominant_failure_reason": "none"},
    ]


class StrategyLearningD9Tests(unittest.TestCase):
    def test_green_com_dados_suficientes_gera_patch_ativo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "strategy_patches.jsonl"
            result = generate_and_save_strategy_patch(
                scorecard=_scorecard("STABLE"),
                window_metrics=_window_metrics(8),
                attributions=_attributions_for_green(),
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
                path=path,
            )
            patch = result["patch"]

            self.assertTrue(patch["active"])
            self.assertIn("A4", patch["layers_applied"])
            self.assertEqual(result["write_action"], "WRITTEN")

    def test_red_gera_noop_com_reason_scorecard_red(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "strategy_patches.jsonl"
            result = generate_and_save_strategy_patch(
                scorecard=_scorecard("RED"),
                window_metrics=_window_metrics(8),
                attributions=_attributions_for_green(),
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
                path=path,
            )
            patch = result["patch"]
            self.assertFalse(patch["active"])
            self.assertEqual(patch["layers_applied"], [])
            self.assertIn("SCORECARD_RED", patch["reason_codes"])

    def test_blocked_tambem_noop_com_reason_scorecard_red(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "strategy_patches.jsonl"
            result = generate_and_save_strategy_patch(
                scorecard=_scorecard("BLOCKED"),
                window_metrics=_window_metrics(8),
                attributions=_attributions_for_green(),
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
                path=path,
            )
            patch = result["patch"]
            self.assertFalse(patch["active"])
            self.assertIn("SCORECARD_RED", patch["reason_codes"])

    def test_idempotencia_noop_mesmo_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "strategy_patches.jsonl"
            first = generate_and_save_strategy_patch(
                scorecard=_scorecard("STABLE"),
                window_metrics=_window_metrics(8),
                attributions=_attributions_low_signal(),
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
                path=path,
            )
            second = generate_and_save_strategy_patch(
                scorecard=_scorecard("STABLE"),
                window_metrics=_window_metrics(8),
                attributions=_attributions_low_signal(),
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
                path=path,
            )
            self.assertEqual(first["write_action"], "WRITTEN")
            self.assertEqual(second["write_action"], "NOOP")
            self.assertEqual(len(read_all_patches(path)), 1)

    def test_conflict_payload_diferente_mesma_chave(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "strategy_patches.jsonl"
            generate_and_save_strategy_patch(
                scorecard=_scorecard("STABLE"),
                window_metrics=_window_metrics(8),
                attributions=_attributions_low_signal(),
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
                path=path,
            )
            with self.assertRaises(StrategyPatchConflictError):
                generate_and_save_strategy_patch(
                    scorecard=_scorecard("STABLE"),
                    window_metrics=_window_metrics(8),
                    attributions=_attributions_for_green(),
                    policy_stage="GROWTH",
                    generated_at="2026-03-05T03:00:00Z",
                    path=path,
                )
            self.assertEqual(len(read_all_patches(path)), 1)

    def test_whitelist_override_fora_do_escopo_forca_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "strategy_patches.jsonl"
            result = generate_and_save_strategy_patch(
                scorecard=_scorecard("STABLE"),
                window_metrics=_window_metrics(8),
                attributions=_attributions_for_green(),
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
                path=path,
                proposed_overrides={"a8_forbidden_override": {"x": True}},
            )
            patch = result["patch"]
            self.assertFalse(patch["active"])
            self.assertEqual(patch["layers_applied"], [])
            self.assertIn("SL_OVERRIDE_NOT_ALLOWED", patch["reason_codes"])

    def test_stage_invalido_falha_com_codigo_canonic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "strategy_patches.jsonl"
            with self.assertRaises(StrategyPatchValidationError) as ctx:
                generate_and_save_strategy_patch(
                    scorecard=_scorecard("STABLE"),
                    window_metrics=_window_metrics(8),
                    attributions=_attributions_for_green(),
                    policy_stage="INVALID_STAGE",
                    generated_at="2026-03-05T03:00:00Z",
                    path=path,
                )
            self.assertEqual(str(ctx.exception), "SL_POLICY_STAGE_INVALID")


if __name__ == "__main__":
    unittest.main()
