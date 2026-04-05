from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.content.pipeline.tts import StubTtsAdapter
from app.creative.agents.asset_selection.models import AssetSelectionResult
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.trend_analysis.models import TrendAnalysisResult
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan, ScriptPlan, TrendProfile
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput


class _StructuredGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="The sealed corridor answered after midnight.",
                setup="A warning appeared on the dusted mirror.",
                payoff="The last lock clicked from inside the wall.",
                generation_mode="test_structured",
            ),
            payload=StructuredScriptPayload(
                hook="The sealed corridor answered after midnight.",
                setup="A warning appeared on the dusted mirror.",
                payoff="The last lock clicked from inside the wall.",
                narrative_mode="official_warning",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class _StubTrendAgent:
    def load(self, data):  # noqa: ANN001
        _ = data
        return TrendAnalysisResult(
            trend_profile=TrendProfile(
                niche="horror",
                dominant_hooks=["story_opening"],
                avg_duration="8-12s",
                pacing="fast_first_3s",
                visual_style="dark_backgrounds",
                text_style="large_caption_focus",
                trend_source="creative_center",
                confidence_scores={"overall": 0.81},
                updated_at="2026-04-03T00:00:00Z",
                valid_until="2026-04-10T00:00:00Z",
                sample_size=10,
                evidence=[],
            ),
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
            validation_summary={
                "status": "APPROVE",
                "valid": True,
                "warnings": [],
                "errors": [],
                "overall_confidence": 0.81,
                "freshness_state": "fresh",
            },
            collector_trace={
                "source_mix": ["creative_center"],
                "shift_analysis": {
                    "shift_detected": True,
                    "comparison_source": "manual_curation",
                    "changes": [
                        {
                            "field": "visual_style",
                            "old": "phase1_baseline",
                            "new": "dark_backgrounds",
                            "significance": "medium",
                        }
                    ],
                },
                "creative_center_refresh": {
                    "trace": {
                        "source": "creative_center",
                        "collector_version": "creative-center-public-v1",
                        "status": "COLLECTED",
                    }
                }
            },
        )


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


class CreativeOrchestratorPhase2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.pipeline = ContentPipelineService(
            tts_adapter=StubTtsAdapter(base_dir=self.out / "content"),
            render_adapter=StubRenderAdapter(base_dir=self.out / "content"),
            publish_adapter=StubPublishAdapter(),
            event_path=self.out / "events" / "events.jsonl",
        )
        self.orchestrator = CreativeOrchestratorService(
            pipeline_service=self.pipeline,
            script_agent=ScriptAgentService(generator=_StructuredGenerator()),
            asset_selection_agent=_StubAssetSelectionAgent(),
            voice_agent=VoiceAgentService(),
            video_qc_agent=VideoQcAgentService(),
            event_emitter=CreativeEventEmitter(event_path=self.out / "events" / "creative_events.jsonl"),
        )
        self.original_env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def _write_json(self, path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _seed_publish_records(self, account_id: str, count: int) -> None:
        path = self.out / "data" / "publish_records" / "publish_records.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [{"account_id": account_id, "publish_id": f"pub_{index}"} for index in range(count)]
        path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    def _seed_metrics(self, account_id: str, views: list[int]) -> None:
        path = self.out / "metrics" / "video_metrics.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [{"account_id": account_id, "views": value} for value in views]
        path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    def _seed_execution_history(self, account_id: str, rows: list[dict[str, object]]) -> None:
        for index, row in enumerate(rows, start=1):
            payload = {
                "creative_pack": {
                    "account_id": account_id,
                    "generated_at": row.get("generated_at", f"2026-04-03T00:0{index}:00Z"),
                    "learning_insights": {
                        "signal_summary": {
                            "recent_hold_or_reject_rate": row.get("recent_hold_or_reject_rate", 0.0),
                            "avg_overall_score": row.get("learning_avg_overall_score", 0.0),
                        }
                    },
                    "asset_plan": {
                        "payoff_asset": row.get("payoff_asset", "assets/imports/pexels/map_blueprint/example.jpg"),
                    },
                },
                "video_qc": {
                    "status": row.get("qc_status", "APPROVE"),
                    "decision": {
                        "status": row.get("qc_status", "APPROVE"),
                        "score_summary": {
                            "overall_score": row.get("overall_score", 0.9),
                        },
                    },
                },
            }
            self._write_json(self.out / "history" / f"run_{index}" / "execution_outputs.json", payload)

    def test_builds_minimal_creative_pack(self) -> None:
        data = CreativeOrchestratorInput(
            account_id="acc_1",
            niche="horror",
            topic="mirror warning",
            publish_slot="2026-03-16T12:00:00Z",
        )

        result = self.orchestrator.build_creative_pack(data)

        self.assertEqual(result.creative_pack.account_id, "acc_1")
        self.assertEqual(result.creative_pack.niche, "horror")
        self.assertTrue(result.creative_pack.script_plan.hook)
        self.assertTrue(result.creative_pack.voice_plan.voice_id)
        self.assertIn("CREATIVE/orchestrator_started", result.events_emitted)
        self.assertIn("CREATIVE/orchestrator_completed", result.events_emitted)

    def test_executes_pipeline_and_qc_without_touching_publish_record_contracts(self) -> None:
        data = CreativeOrchestratorInput(
            account_id="acc_1",
            niche="horror",
            topic="sealed tunnel",
            publish_slot="2026-03-16T12:00:00Z",
        )

        execution = self.orchestrator.execute(data)

        self.assertEqual(execution.pipeline_output["result"]["status"], "READY")
        self.assertEqual(execution.video_qc.status, "APPROVE")
        publish_records_path = self.out / "data" / "publish_records" / "publish_records.jsonl"
        self.assertFalse(publish_records_path.exists())

    def test_emits_trend_validation_and_collection_events(self) -> None:
        orchestrator = CreativeOrchestratorService(
            pipeline_service=self.pipeline,
            trend_analysis_agent=_StubTrendAgent(),
            script_agent=ScriptAgentService(generator=_StructuredGenerator()),
            asset_selection_agent=_StubAssetSelectionAgent(),
            voice_agent=VoiceAgentService(),
            video_qc_agent=VideoQcAgentService(),
            event_emitter=CreativeEventEmitter(event_path=self.out / "events" / "creative_events.jsonl"),
        )

        result = orchestrator.build_creative_pack(
            CreativeOrchestratorInput(
                account_id="acc_1",
                niche="horror",
                topic="mirror warning",
                publish_slot="2026-03-16T12:00:00Z",
            )
        )

        self.assertIn("CREATIVE/trend_collection_completed", result.events_emitted)
        self.assertIn("CREATIVE/trend_collection_started", result.events_emitted)
        self.assertIn("CREATIVE/trend_validation_approved", result.events_emitted)
        self.assertIn("CREATIVE/trend_shift_detected", result.events_emitted)
        events_path = self.out / "events" / "creative_events.jsonl"
        rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        event_types = [row.get("event_type") for row in rows]
        self.assertIn("CREATIVE/trend_collection_started", event_types)
        self.assertIn("CREATIVE/trend_collection_completed", event_types)
        self.assertIn("CREATIVE/trend_validation_approved", event_types)
        self.assertIn("CREATIVE/trend_shift_detected", event_types)
        collection_event = next(row for row in rows if row.get("event_type") == "CREATIVE/trend_collection_completed")
        validation_event = next(row for row in rows if row.get("event_type") == "CREATIVE/trend_validation_approved")
        loaded_event = next(row for row in rows if row.get("event_type") == "CREATIVE/trend_profile_loaded")
        shift_event = next(row for row in rows if row.get("event_type") == "CREATIVE/trend_shift_detected")
        self.assertEqual(collection_event["details"]["source"], "creative_center")
        self.assertEqual(collection_event["details"]["collector_version"], "creative-center-public-v1")
        self.assertEqual(validation_event["details"]["status"], "APPROVE")
        self.assertEqual(validation_event["details"]["trend_source"], "creative_center")
        self.assertIn("source_mix", validation_event["details"])
        self.assertEqual(loaded_event["details"]["validation_status"], "APPROVE")
        self.assertEqual(loaded_event["details"]["trend_source"], "creative_center")
        self.assertEqual(loaded_event["details"]["pacing"], "fast_first_3s")
        self.assertEqual(shift_event["details"]["comparison_source"], "manual_curation")

    def test_activates_real_health_inputs_and_reaches_caution(self) -> None:
        account_id = "acc_health_inputs_caution"
        self._seed_publish_records(account_id, 5)
        self._seed_metrics(account_id, [200, 210, 220, 120, 110, 100])
        self._seed_execution_history(
            account_id,
            [
                {
                    "qc_status": "APPROVE",
                    "overall_score": 0.9,
                    "payoff_asset": "assets/imports/pexels/map_blueprint/example_a.jpg",
                },
                {
                    "qc_status": "APPROVE",
                    "overall_score": 0.79,
                    "payoff_asset": "assets/imports/pexels/map_blueprint/example_b.jpg",
                },
                {
                    "qc_status": "APPROVE",
                    "overall_score": 0.78,
                    "payoff_asset": "assets/imports/pexels/map_blueprint/example_c.jpg",
                },
            ],
        )

        execution = self.orchestrator.execute(
            CreativeOrchestratorInput(
                account_id=account_id,
                niche="horror",
                topic="mirror warning",
                publish_slot="2026-03-16T12:00:00Z",
            )
        )

        self.assertEqual(execution.account_health.decision.status, "CAUTION")
        self.assertIn("RECENT_VIEWS_DROP", execution.account_health.decision.reasons)
        self.assertIn("LOW_PERFORMANCE_STREAK", execution.account_health.decision.reasons)
        self.assertTrue(execution.account_health.decision.recommended_constraints["reduce_hook_aggressiveness"])
        self.assertEqual(execution.account_health.input_summary["recent_publish_count"], 5)
        self.assertGreater(execution.account_health.input_summary["recent_views_drop_ratio"], 0.4)
        self.assertEqual(execution.account_health.decision_trace["final_status"], "CAUTION")
        self.assertIn("recent_views_drop_ratio>=0.40", execution.account_health.decision_trace["triggered_conditions"])
        self.assertEqual(execution.strategy.strategy_profile.content_mode, "conservative")
        self.assertEqual(execution.pipeline_output["result"]["status"], "READY")
        payload = execution.to_dict()
        self.assertEqual(payload["account_health"]["decision_trace"]["final_status"], "CAUTION")
        self.assertEqual(payload["account_health"]["input_summary"]["recent_publish_count"], 5)
        events_path = self.out / "events" / "creative_events.jsonl"
        rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        caution_event = next(row for row in rows if row.get("event_type") == "CREATIVE/account_health_caution")
        self.assertEqual(caution_event["details"]["decision_trace"]["final_status"], "CAUTION")
        self.assertEqual(caution_event["details"]["input_summary"]["recent_publish_count"], 5)

    def test_activated_health_inputs_can_hold_before_pipeline(self) -> None:
        account_id = "acc_health_inputs_hold"
        self._seed_publish_records(account_id, 6)
        self._seed_metrics(account_id, [300, 320, 310, 40, 35, 30])
        self._seed_execution_history(
            account_id,
            [
                {"qc_status": "HOLD", "overall_score": 0.7},
                {"qc_status": "REJECT", "overall_score": 0.68},
                {"qc_status": "HOLD", "overall_score": 0.71},
                {"qc_status": "REJECT", "overall_score": 0.69},
            ],
        )

        execution = self.orchestrator.execute(
            CreativeOrchestratorInput(
                account_id=account_id,
                niche="horror",
                topic="sealed tunnel",
                publish_slot="2026-03-16T12:00:00Z",
            )
        )

        self.assertEqual(execution.account_health.decision.status, "HOLD")
        self.assertIn("LOW_PERFORMANCE_STREAK", execution.account_health.decision.reasons)
        self.assertEqual(execution.account_health.decision_trace["final_status"], "HOLD")
        self.assertTrue(execution.account_health.decision_trace["threshold_evaluations"]["hold_on_views_drop"])
        self.assertEqual(execution.pipeline_output["result"]["status"], "HOLD")
        self.assertIsNone(execution.creative_pack)
        self.assertIsNone(execution.video_qc)
        rows = [
            json.loads(line)
            for line in (self.out / "events" / "creative_events.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        hold_event = next(row for row in rows if row.get("event_type") == "CREATIVE/account_health_hold")
        self.assertEqual(hold_event["details"]["decision_trace"]["final_status"], "HOLD")
        self.assertFalse(hold_event["details"]["fallback_used"])


if __name__ == "__main__":
    unittest.main()
