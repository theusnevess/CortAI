from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.video_qc.models import VideoQcDecision, VideoQcResult
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService


class _StructuredGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="The platform called a train that should not exist.",
                setup="Witnesses said the station lights had been dead for years.",
                payoff="The route number matched a city removed from every map.",
                generation_mode="test_structured",
            ),
            payload=StructuredScriptPayload(
                hook="The platform called a train that should not exist.",
                setup="Witnesses said the station lights had been dead for years.",
                payoff="The route number matched a city removed from every map.",
                narrative_mode="test_mode",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class _FixedQcAgent(VideoQcAgentService):
    def __init__(self, status: str) -> None:
        self._status = status

    def evaluate(self, **kwargs):  # type: ignore[override]
        _ = kwargs
        decision = VideoQcDecision(
            status=self._status,  # type: ignore[arg-type]
            publishable=self._status == "APPROVE",
            hard_failures=[] if self._status != "REJECT" else ["QC_FORCED_REJECT"],
            soft_failures=[] if self._status != "HOLD" else ["QC_FORCED_HOLD"],
            product_vetoes=[],
            score_summary={"overall_score": 0.92 if self._status == "APPROVE" else 0.62 if self._status == "HOLD" else 0.31},
            product_signals={"hook_quality": 0.9, "payoff_quality": 0.9, "publishable": self._status == "APPROVE"},
            decision_trace={"mode": "fixed"},
            checked_at="2026-03-28T00:00:00Z",
        )
        reasons = [*decision.hard_failures, *decision.soft_failures, *decision.product_vetoes]
        return VideoQcResult(
            decision=decision,
            status=decision.status,
            reasons=reasons,
            checked_at=decision.checked_at,
            publishable=decision.publishable,
            details={"mode": "fixed"},
        )


class _FakePipelineService:
    def run_pipeline(self, **kwargs):  # noqa: ANN003
        _ = kwargs
        return {
            "job": {"render_job_id": "rj_test", "status": "RENDER_DONE"},
            "result": {
                "status": "RENDER_DONE",
                "publishable": False,
                "publish_manifest": None,
                "artifacts": {"audio": "OUT/audio.wav", "video": "OUT/video.mp4"},
                "events_emitted": [
                    "CONTENT/tts_started",
                    "CONTENT/tts_completed",
                    "CONTENT/render_started",
                    "CONTENT/render_completed",
                ],
                "error_code": None,
                "render_job_id": "rj_test",
                "tts_trace": {"segment_durations": [2.1, 2.4, 2.8]},
                "visual_trace": {"trace": True},
                "edit_trace": {"trace": True},
            },
        }

    def finalize_publish(self, **kwargs):  # noqa: ANN003
        _ = kwargs
        return {
            "job": {"render_job_id": "rj_test", "status": "READY"},
            "result": {
                "status": "READY",
                "publishable": True,
                "publish_manifest": {
                    "publish_id": "pub_test",
                    "account_id": "acc",
                    "video_path": "OUT/video.mp4",
                    "caption": "",
                    "hashtags": [],
                    "scheduled_time": "2026-03-28T10:00:00Z",
                },
                "artifacts": {"audio": "OUT/audio.wav", "video": "OUT/video.mp4"},
                "events_emitted": ["CONTENT/publish_manifest_created"],
                "error_code": None,
                "render_job_id": "rj_test",
            },
        }

    def mark_non_publishable(self, **kwargs):  # noqa: ANN003
        decision = kwargs["decision"]
        return {
            "job": {"render_job_id": "rj_test", "status": decision},
            "result": {
                "status": decision,
                "publishable": False,
                "publish_manifest": None,
                "artifacts": {"audio": "OUT/audio.wav", "video": "OUT/video.mp4"},
                "events_emitted": [],
                "error_code": None,
                "render_job_id": "rj_test",
            },
        }


class QcAgentEvolutionV20IntegrationTests(unittest.TestCase):
    def _build_orchestrator(self, *, qc_status: str) -> CreativeOrchestratorService:
        return CreativeOrchestratorService(
            pipeline_service=_FakePipelineService(),  # type: ignore[arg-type]
            script_agent=ScriptAgentService(generator=_StructuredGenerator()),
            voice_agent=VoiceAgentService(),
            video_qc_agent=_FixedQcAgent(qc_status),
            event_emitter=CreativeEventEmitter(event_path=Path("OUT/events/test_qc_governor.jsonl")),
        )

    def test_approve_allows_publishable_progression(self) -> None:
        orchestrator = self._build_orchestrator(qc_status="APPROVE")
        execution = orchestrator.execute(
            CreativeOrchestratorInput(
                account_id="acc_qc_approve",
                niche="horror",
                topic="dead station",
                publish_slot="2026-03-28T10:00:00Z",
            )
        )

        self.assertEqual(execution.video_qc.status, "APPROVE")
        self.assertTrue(execution.pipeline_output["result"]["publishable"])
        self.assertEqual(execution.pipeline_output["result"]["status"], "READY")
        self.assertIsNotNone(execution.pipeline_output["result"]["publish_manifest"])

    def test_hold_blocks_publishable_progression(self) -> None:
        orchestrator = self._build_orchestrator(qc_status="HOLD")
        execution = orchestrator.execute(
            CreativeOrchestratorInput(
                account_id="acc_qc_hold",
                niche="horror",
                topic="dead station",
                publish_slot="2026-03-28T10:00:00Z",
            )
        )

        self.assertEqual(execution.video_qc.status, "HOLD")
        self.assertFalse(execution.pipeline_output["result"]["publishable"])
        self.assertEqual(execution.pipeline_output["result"]["status"], "HOLD")
        self.assertIsNone(execution.pipeline_output["result"]["publish_manifest"])

    def test_reject_blocks_publishable_progression(self) -> None:
        orchestrator = self._build_orchestrator(qc_status="REJECT")
        execution = orchestrator.execute(
            CreativeOrchestratorInput(
                account_id="acc_qc_reject",
                niche="horror",
                topic="dead station",
                publish_slot="2026-03-28T10:00:00Z",
            )
        )

        self.assertEqual(execution.video_qc.status, "REJECT")
        self.assertFalse(execution.pipeline_output["result"]["publishable"])
        self.assertEqual(execution.pipeline_output["result"]["status"], "REJECT")
        self.assertIsNone(execution.pipeline_output["result"]["publish_manifest"])


if __name__ == "__main__":
    unittest.main()
