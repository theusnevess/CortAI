from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.product.attribution.builder import AttributionDeps, build_evidence_summary
from app.product.attribution.schema import OPTIONAL_ENRICHMENT_FIELDS, REQUIRED_BASE_FIELDS
from app.product.attribution.service import generate_and_save_attribution
from app.product.attribution.store_jsonl import read_all_attributions


class FakePublishRecordsRepo:
    def __init__(self, rows: dict[str, dict[str, Any]]) -> None:
        self.rows = rows

    def get_by_publish_id(self, publish_id: str) -> dict[str, Any] | None:
        return self.rows.get(publish_id)


class FakeVideoMetricsRepo:
    def __init__(
        self,
        best_rows: dict[tuple[str, str, str], dict[str, Any]] | None = None,
        latest_rows: dict[tuple[str, str], dict[str, Any]] | None = None,
    ) -> None:
        self.best_rows = best_rows or {}
        self.latest_rows = latest_rows or {}

    def get_best(self, account_id: str, video_id: str, captured_window_id: str) -> dict[str, Any] | None:
        return self.best_rows.get((account_id, video_id, captured_window_id))

    def get_latest_for_video(self, account_id: str, video_id: str) -> dict[str, Any] | None:
        return self.latest_rows.get((account_id, video_id))


class FakeWindowMetricsRepo:
    def __init__(self, rows: dict[tuple[str, str], dict[str, Any]]) -> None:
        self.rows = rows

    def get_by_key(self, account_id: str, window_id: str) -> dict[str, Any] | None:
        return self.rows.get((account_id, window_id))


class FakeScorecardRepo:
    def __init__(self, rows: dict[tuple[str, str], dict[str, Any]]) -> None:
        self.rows = rows

    def get_by_key(self, account_id: str, window_id: str) -> dict[str, Any] | None:
        return self.rows.get((account_id, window_id))


def _base_publish() -> dict[str, Any]:
    return {
        "publish_id": "pub_001",
        "account_id": "acc_ca_001",
        "job_id": "job_001",
        "video_id": "vid_001",
        "publish_mode": "auto",
        "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "policy_stage": "GROWTH",
        "metadata": {
            "hook_strategy": "curiosity_gap",
        },
    }


def _base_metrics() -> dict[str, Any]:
    return {
        "account_id": "acc_ca_001",
        "video_id": "vid_001",
        "captured_window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "captured_at": "2026-03-05T00:02:00Z",
        "views": 12345,
        "retention_3s": 0.52,
        "completion_rate": 0.38,
    }


def _base_window_metrics() -> dict[str, Any]:
    return {
        "account_id": "acc_ca_001",
        "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "videos_considered": 8,
    }


class ContentAttributionPhaseBContractTests(unittest.TestCase):
    def test_contract_constants_are_explicit(self) -> None:
        self.assertIn("publish_id", REQUIRED_BASE_FIELDS)
        self.assertIn("views", REQUIRED_BASE_FIELDS)
        self.assertIn("rpm", OPTIONAL_ENRICHMENT_FIELDS)
        self.assertIn("effective_duration_s", OPTIONAL_ENRICHMENT_FIELDS)

    def test_evidence_summary_marks_required_only_when_scorecard_absent(self) -> None:
        summary = build_evidence_summary(
            publish_present=True,
            metrics_present=True,
            window_metrics_present=True,
            scorecard_present=False,
        )
        self.assertTrue(summary["required_evidence_complete"])
        self.assertEqual(summary["evidence_mode"], "REQUIRED_ONLY")
        self.assertFalse(summary["optional_present"]["scorecard"])

    def test_generate_and_save_returns_honest_written_result(self) -> None:
        publish = _base_publish()
        metrics = _base_metrics()
        window_metrics = _base_window_metrics()
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish["publish_id"]: publish}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish["account_id"], publish["video_id"], publish["window_id"]): metrics}
            ),
            window_metrics_repo=FakeWindowMetricsRepo({(publish["account_id"], publish["window_id"]): window_metrics}),
            scorecard_repo=FakeScorecardRepo({}),
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "content_attribution.jsonl"
            result = generate_and_save_attribution(publish_id=publish["publish_id"], deps=deps, path=path)
            rows = read_all_attributions(path)

        self.assertEqual(result["status"], "WRITTEN")
        self.assertEqual(result["reason_code"], "ATTRIBUTION_OK")
        self.assertTrue(result["record_written"])
        self.assertEqual(len(rows), 1)
        self.assertTrue(result["evidence_summary"]["required_evidence_complete"])
        self.assertEqual(result["evidence_summary"]["evidence_mode"], "REQUIRED_ONLY")

    def test_generate_and_save_returns_honest_skipped_result_when_metrics_missing(self) -> None:
        publish = _base_publish()
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish["publish_id"]: publish}),
            video_metrics_repo=FakeVideoMetricsRepo(),
            window_metrics_repo=FakeWindowMetricsRepo({}),
            scorecard_repo=None,
        )
        result = generate_and_save_attribution(publish_id=publish["publish_id"], deps=deps)

        self.assertEqual(result["status"], "SKIPPED")
        self.assertEqual(result["reason_code"], "ATTRIBUTION_METRICS_MISSING")
        self.assertFalse(result["record_written"])
        self.assertFalse(result["evidence_summary"]["required_evidence_complete"])
        self.assertFalse(result["evidence_summary"]["required_present"]["video_metrics"])


if __name__ == "__main__":
    unittest.main()
