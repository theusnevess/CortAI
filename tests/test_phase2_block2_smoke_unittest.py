from __future__ import annotations

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
from app.creative.agents.account_health.models import AccountHealthDecision, AccountHealthResult
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput


class _HoldAccountHealthAgent(AccountHealthAgentService):
    def evaluate(self, data):  # type: ignore[override]
        return AccountHealthResult(
            decision=AccountHealthDecision(
                status="HOLD",
                reasons=["RECENT_VIEWS_DROP"],
                recommended_constraints={"block_generation": True},
            ),
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class Phase2Block2SmokeTests(unittest.TestCase):
    def _build_orchestrator(self, out: Path, *, account_health_agent: AccountHealthAgentService | None = None) -> CreativeOrchestratorService:
        pipeline = ContentPipelineService(
            tts_adapter=StubTtsAdapter(base_dir=out / "content"),
            render_adapter=StubRenderAdapter(base_dir=out / "content"),
            publish_adapter=StubPublishAdapter(),
            event_path=out / "events" / "events.jsonl",
        )
        return CreativeOrchestratorService(
            pipeline_service=pipeline,
            account_health_agent=account_health_agent or AccountHealthAgentService(),
            strategy_agent=StrategyAgentService(),
            script_agent=ScriptAgentService(),
            voice_agent=VoiceAgentService(),
            video_qc_agent=VideoQcAgentService(),
            event_emitter=CreativeEventEmitter(event_path=out / "events" / "creative_events.jsonl"),
        )

    def test_safe_flow_reaches_pipeline_and_video_qc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir) / "OUT"
            orchestrator = self._build_orchestrator(out)

            execution = orchestrator.execute(
                CreativeOrchestratorInput(
                    account_id="acc_safe",
                    niche="horror",
                    topic="closed station",
                    publish_slot="2026-03-17T12:00:00Z",
                )
            )

            self.assertEqual(execution.account_health.decision.status, "SAFE")
            self.assertEqual(execution.strategy.strategy_profile.goal, "retention")
            self.assertEqual(execution.pipeline_output["result"]["status"], "READY")
            self.assertEqual(execution.video_qc.status, "APPROVE")

    def test_hold_stops_before_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir) / "OUT"
            orchestrator = self._build_orchestrator(out, account_health_agent=_HoldAccountHealthAgent())

            execution = orchestrator.execute(
                CreativeOrchestratorInput(
                    account_id="acc_hold",
                    niche="horror",
                    topic="mirror warning",
                    publish_slot="2026-03-17T12:00:00Z",
                )
            )

            self.assertEqual(execution.account_health.decision.status, "HOLD")
            self.assertEqual(execution.pipeline_output["result"]["status"], "HOLD")
            self.assertIsNone(execution.creative_pack)
            self.assertIsNone(execution.video_qc)


if __name__ == "__main__":
    unittest.main()
