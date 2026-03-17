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

from app.creative.agents.learning.models import LearningAgentInput
from app.creative.agents.learning.service import LearningAgentService


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")


class LearningAgentPhase2Tests(unittest.TestCase):
    def test_generates_learning_insights_from_existing_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            publish_path = root / "data" / "publish_records" / "publish_records.jsonl"
            metrics_path = root / "metrics" / "video_metrics.jsonl"
            analysis_dir = root / "analysis"
            output_path = root / "learning" / "learning_insights.json"

            _write_jsonl(
                publish_path,
                [
                    {"account_id": "acc_1", "publish_id": "pub_1"},
                    {"account_id": "acc_1", "publish_id": "pub_2"},
                ],
            )
            _write_jsonl(
                metrics_path,
                [
                    {"account_id": "acc_1", "views": 220, "completion_rate": 0.62, "duration_s": 9.8},
                    {"account_id": "acc_1", "views": 180, "completion_rate": 0.57, "duration_s": 10.4},
                ],
            )
            analysis_dir.mkdir(parents=True, exist_ok=True)
            (analysis_dir / "hook_performance_summary.json").write_text(
                json.dumps({"hooks": [{"hook_style": "question"}]}),
                encoding="utf-8",
            )

            service = LearningAgentService()
            result = service.generate(
                LearningAgentInput(
                    account_id="acc_1",
                    publish_records_path=publish_path,
                    video_metrics_path=metrics_path,
                    analysis_dir=analysis_dir,
                    output_path=output_path,
                )
            )

            self.assertFalse(result.fallback.used)
            self.assertEqual(result.learning_insights.recommended_hook_type, "question")
            self.assertEqual(result.learning_insights.target_duration_range, "8-12s")
            self.assertGreater(result.learning_insights.signal_summary["avg_views"], 0)
            self.assertTrue(output_path.exists())

    def test_falls_back_when_history_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            service = LearningAgentService()

            result = service.generate(
                LearningAgentInput(
                    account_id="acc_1",
                    publish_records_path=root / "missing_publish.jsonl",
                    video_metrics_path=root / "missing_metrics.jsonl",
                    analysis_dir=root / "missing_analysis",
                    output_path=root / "learning" / "learning_insights.json",
                )
            )

            self.assertTrue(result.fallback.used)
            self.assertEqual(result.fallback.reason, "LEARNING_INSIGHTS_FALLBACK")
            self.assertEqual(result.learning_insights.recommendations, ["fallback_default"])


if __name__ == "__main__":
    unittest.main()
