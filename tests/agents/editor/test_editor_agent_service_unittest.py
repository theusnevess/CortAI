from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.editor.models import EditorAgentInput
from app.creative.agents.editor.service import EditorAgentService
from app.creative.contracts.creative_pack import (
    AssetPlan,
    ScriptPlan,
    StrategyProfile,
    TrendProfile,
    VoiceDeliveryProfile,
    VoicePlan,
    VoiceRuntimeConstraints,
)


class EditorAgentServiceTests(unittest.TestCase):
    def test_returns_edit_plan_without_fallback(self) -> None:
        service = EditorAgentService()
        result = service.plan(
            EditorAgentInput(
                account_id="acc_1",
                niche="horror",
                topic="sealed corridor signal",
                script_plan=ScriptPlan(hook="Hook", setup="Setup", payoff="Payoff", generation_mode="test"),
                voice_plan=VoicePlan(
                    provider="kokoro",
                    voice_id="af_heart",
                    style="ominous_minimal",
                    delivery_profile=VoiceDeliveryProfile(),
                    runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
                ),
                asset_plan=AssetPlan(visual_anchor="warning_display", semantic_pattern="active_signal", entity="panel"),
                strategy_profile=StrategyProfile(),
                trend_profile=TrendProfile(niche="horror"),
            )
        )

        self.assertFalse(result.fallback.used)
        self.assertEqual(result.edit_plan.editor_version, "editor-agent-v2_2")
        self.assertTrue(result.edit_plan.editor_style_profile)
        self.assertTrue(result.edit_plan.caption_plan.segment_caption_blocks["hook"])


if __name__ == "__main__":
    unittest.main()
