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
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.learning.service import LearningAgentService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.experiments.service import ExperimentCapabilityService
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")


class Phase2Block4SmokeTests(unittest.TestCase):
    def test_learning_and_experiment_context_flow_reaches_pipeline_and_qc(self) -> None:
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

            publish_path = root / "data" / "publish_records" / "publish_records.jsonl"
            metrics_path = root / "metrics" / "video_metrics.jsonl"
            analysis_dir = root / "analysis"
            _write_jsonl(publish_path, [{"account_id": "acc_block4", "publish_id": "pub_001"}])
            _write_jsonl(metrics_path, [{"account_id": "acc_block4", "views": 240, "completion_rate": 0.61, "duration_s": 9.4}])
            analysis_dir.mkdir(parents=True, exist_ok=True)
            (analysis_dir / "hook_performance_summary.json").write_text(
                json.dumps({"hooks": [{"hook_style": "question"}]}),
                encoding="utf-8",
            )

            experiments_dir = root / "experiments"
            experiments_dir.mkdir(parents=True, exist_ok=True)
            (experiments_dir / "experiment_config.json").write_text(
                json.dumps(
                    {
                        "name": "creative_pack_baseline",
                        "scope": "CREATIVE_PACK",
                        "variant_a": {"variant_type": "hook_style", "hook_style": "question"},
                        "variant_b": {"variant_type": "hook_style", "hook_style": "story_opening"},
                        "status": "ACTIVE",
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
                learning_agent=LearningAgentService(
                    default_publish_records_path=publish_path,
                    default_video_metrics_path=metrics_path,
                    default_analysis_dir=analysis_dir,
                    default_output_path=root / "learning" / "learning_insights.json",
                ),
                strategy_agent=StrategyAgentService(),
                experiment_capability=ExperimentCapabilityService(
                    default_config_path=experiments_dir / "experiment_config.json",
                    default_output_path=experiments_dir / "experiment_plan.json",
                    default_experiments_path=experiments_dir / "experiments.jsonl",
                    default_assignments_path=experiments_dir / "assignments.jsonl",
                    default_results_path=experiments_dir / "results.jsonl",
                ),
                asset_selection_agent=AssetSelectionAgentService(),
                script_agent=ScriptAgentService(),
                voice_agent=VoiceAgentService(),
                video_qc_agent=VideoQcAgentService(),
                event_emitter=CreativeEventEmitter(event_path=out / "events" / "creative_events.jsonl"),
            )

            execution = orchestrator.execute(
                CreativeOrchestratorInput(
                    account_id="acc_block4",
                    niche="horror",
                    topic="sealed mirror tunnel",
                    publish_slot="2026-03-17T12:00:00Z",
                )
            )

            self.assertEqual(execution.account_health.decision.status, "SAFE")
            self.assertFalse(execution.learning.fallback.used)
            self.assertFalse(execution.experiment.fallback.used)
            self.assertTrue(execution.creative_pack.learning_insights.recommendations)
            self.assertTrue(execution.creative_pack.experiment_plan.experiment_id.startswith("exp_"))
            self.assertEqual(execution.pipeline_output["result"]["status"], "READY")
            self.assertEqual(execution.video_qc.status, "APPROVE")


if __name__ == "__main__":
    unittest.main()
