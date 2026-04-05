from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.novelty.models import NoveltyInput
from app.creative.agents.novelty.service import NoveltyEngineService


def _approved_execution(*, payoff: str, payoff_category: str, variation_policy: str = "low") -> dict[str, object]:
    return {
        "creative_pack": {
            "script_plan": {
                "hook": "A witness saw the corridor breathe.",
                "setup": "The second sound came from behind the wall.",
                "payoff": payoff,
            },
            "asset_plan": {
                "segments": {
                    "payoff": {
                        "category": payoff_category,
                    }
                }
            },
            "strategy_profile": {
                "variation_policy": variation_policy,
                "content_mode": "standard",
            },
        },
        "video_qc": {
            "status": "APPROVE",
        },
    }


class NoveltyEngineTests(unittest.TestCase):
    def test_detects_repeated_payoff_structure_and_visual_family(self) -> None:
        service = NoveltyEngineService()
        executions = [
            _approved_execution(payoff="THE FINAL DETAIL NAMED DOOR 16, REMOVED FROM THE FLOORPLAN", payoff_category="map_blueprint")
            for _ in range(4)
        ]

        result = service.generate(NoveltyInput(account_id="acc_1", recent_approved_executions=executions))

        self.assertIn(result.novelty_pressure_profile.structural_saturation_level, {"high", "critical"})
        self.assertIn("named_location_removed", result.novelty_pressure_profile.blocked_payoff_structures)
        self.assertIn("map_blueprint", result.novelty_pressure_profile.blocked_visual_payoff_categories)
        self.assertEqual(result.novelty_pressure_profile.recommended_variation_policy, "medium")

    def test_registers_only_approved_executions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = NoveltyEngineService(history_dir=Path(tmp_dir))
            service.register_approved_execution(
                account_id="acc_1",
                execution_payload=_approved_execution(
                    payoff="THE FINAL DETAIL NAMED DOOR 16, REMOVED FROM THE FLOORPLAN",
                    payoff_category="map_blueprint",
                ),
            )
            service.register_approved_execution(
                account_id="acc_1",
                execution_payload={
                    "creative_pack": {},
                    "video_qc": {"status": "HOLD"},
                },
            )

            history = service._load_recent_approved_executions(account_id="acc_1")

            self.assertEqual(len(history), 1)


if __name__ == "__main__":
    unittest.main()
