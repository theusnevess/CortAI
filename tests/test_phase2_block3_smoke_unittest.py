from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.content.pipeline.tts import StubTtsAdapter
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.runtime.asset_selector import AssetSelector


class _StructuredGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="A red phone rang inside the shuttered wing.",
                setup="The hallway lights died before anyone answered.",
                payoff="The caller whispered the number of an empty room.",
                generation_mode="test_structured",
            ),
            payload=StructuredScriptPayload(
                hook="A red phone rang inside the shuttered wing.",
                setup="The hallway lights died before anyone answered.",
                payoff="The caller whispered the number of an empty room.",
                narrative_mode="official_warning",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class Phase2Block3SmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

    def test_trend_and_asset_context_flow_reaches_pipeline_and_qc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out = root / "OUT"
            trends_dir = root / "trends"
            trends_dir.mkdir(parents=True, exist_ok=True)
            (trends_dir / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "dominant_hooks": ["question", "story_opening"],
                        "avg_duration": "35-60",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                    }
                ),
                encoding="utf-8",
            )

            pipeline = ContentPipelineService(
                tts_adapter=StubTtsAdapter(base_dir=out / "content"),
                render_adapter=StubRenderAdapter(base_dir=out / "content"),
                publish_adapter=StubPublishAdapter(),
                event_path=out / "events" / "events.jsonl",
            )
            orchestrator = CreativeOrchestratorService(
                pipeline_service=pipeline,
                account_health_agent=AccountHealthAgentService(),
                trend_analysis_agent=TrendAnalysisAgentService(trends_dir=trends_dir),
                strategy_agent=StrategyAgentService(),
                asset_selection_agent=AssetSelectionAgentService(),
                script_agent=ScriptAgentService(generator=_StructuredGenerator()),
                voice_agent=VoiceAgentService(),
                video_qc_agent=VideoQcAgentService(),
                event_emitter=CreativeEventEmitter(event_path=out / "events" / "creative_events.jsonl"),
            )

            execution = orchestrator.execute(
                CreativeOrchestratorInput(
                    account_id="acc_block3",
                    niche="horror",
                    topic="mirror corridor",
                    publish_slot="2026-03-16T12:00:00Z",
                )
            )

            self.assertEqual(execution.account_health.decision.status, "SAFE")
            self.assertFalse(execution.trend_analysis.fallback.used)
            self.assertEqual(execution.trend_analysis.trend_profile.niche, "horror")
            self.assertFalse(execution.asset_selection.fallback.used)
            self.assertTrue(execution.creative_pack.asset_plan.hook_asset)
            self.assertIn(execution.pipeline_output["result"]["status"], {"READY", "HOLD"})
            self.assertIsNotNone(execution.video_qc)
            self.assertIn(execution.video_qc.status, {"APPROVE", "HOLD"})


if __name__ == "__main__":
    unittest.main()
