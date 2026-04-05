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
from app.content.pipeline.tts import StubTtsAdapter
from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.asset_selection.models import AssetSelectionResult
from app.creative.agents.novelty.service import NoveltyEngineService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan, ScriptPlan
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.runtime.asset_selector import AssetSelector


class _StructuredGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="A red phone rang inside the shuttered wing.",
                setup="The hallway lights died before anyone answered.",
                payoff="The final detail named door 16, removed from the floorplan.",
                generation_mode="test_structured",
            ),
            payload=StructuredScriptPayload(
                hook="A red phone rang inside the shuttered wing.",
                setup="The hallway lights died before anyone answered.",
                payoff="The final detail named door 16, removed from the floorplan.",
                narrative_mode="official_warning",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class _CapturingStrategyAgent(StrategyAgentService):
    def __init__(self) -> None:
        super().__init__()
        self.last_input = None

    def generate(self, data):  # type: ignore[override]
        self.last_input = data
        return super().generate(data)


class _StubAssetSelectionAgent:
    def select(self, data):  # noqa: ANN001
        _ = data
        return AssetSelectionResult(
            asset_selection=AssetPlan(
                hook_asset="assets/imports/pexels/warning_display/pexels_warning_display_panel_9.jpg",
                setup_asset="assets/imports/pexels/sealed_access/pexels_security_door_access_control_dark_4.jpg",
                payoff_asset="assets/imports/pexels/map_blueprint/pexels_old_architectural_blueprint_close_up_5.jpg",
                visual_style="dark_backgrounds",
                motion_profile="subtle_push_in",
            ),
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )

    def align_first_frame(self, *, niche, topic, hook_text, asset_plan):  # noqa: ANN001
        _ = (niche, topic, hook_text)
        return asset_plan


class StrategyAgentEvolutionV20IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

    def test_orchestrator_passes_trend_into_strategy_and_persists_decision_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out = root / "OUT"
            trends_dir = root / "trends"
            trends_dir.mkdir(parents=True, exist_ok=True)
            (trends_dir / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "dominant_hooks": ["story_opening"],
                        "avg_duration": "35-60",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                    }
                ),
                encoding="utf-8",
            )
            strategy_agent = _CapturingStrategyAgent()
            novelty_agent = NoveltyEngineService(history_dir=out / "novelty_history")
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
                novelty_agent=novelty_agent,
                strategy_agent=strategy_agent,
                asset_selection_agent=_StubAssetSelectionAgent(),
                script_agent=ScriptAgentService(generator=_StructuredGenerator()),
                voice_agent=VoiceAgentService(),
                video_qc_agent=VideoQcAgentService(),
                event_emitter=CreativeEventEmitter(event_path=out / "events" / "creative_events.jsonl"),
            )

            execution = orchestrator.execute(
                CreativeOrchestratorInput(
                    account_id="acc_strategy_v20",
                    niche="horror",
                    topic="mirror corridor",
                    publish_slot="2026-03-29T12:00:00Z",
                )
            )

            self.assertIsNotNone(strategy_agent.last_input)
            self.assertIsNotNone(strategy_agent.last_input.trend_profile)
            self.assertIsNotNone(strategy_agent.last_input.novelty_pressure_profile)
            self.assertEqual(strategy_agent.last_input.trend_profile.pacing, "fast_first_3s")
            self.assertIn("final_profile", execution.strategy.decision_trace)
            self.assertIn("trend_adjustments", execution.strategy.decision_trace)
            self.assertEqual(execution.creative_pack.strategy_profile.variation_policy, execution.strategy.strategy_profile.variation_policy)
            history = novelty_agent._load_recent_approved_executions(account_id="acc_strategy_v20")
            self.assertEqual(len(history), 1)


if __name__ == "__main__":
    unittest.main()
