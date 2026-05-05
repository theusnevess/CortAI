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

from app.product.attribution.builder import AttributionDeps
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


class FakeKeyRepo:
    def __init__(self, key_field: str, rows: dict[str, dict[str, Any]]) -> None:
        self.key_field = key_field
        self.rows = rows

    def get_by_key(self, field: str, value: str) -> dict[str, Any] | None:
        if field != self.key_field:
            return None
        return self.rows.get(value)


def _base_publish(*, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "publish_id": "pub_001",
        "account_id": "acc_ca_001",
        "job_id": "job_001",
        "video_id": "vid_001",
        "publish_mode": "auto",
        "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "policy_stage": "GROWTH",
        "metadata": metadata or {"hook_strategy": "curiosity_gap"},
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


class ContentAttributionPhaseCExperimentAwareTests(unittest.TestCase):
    def test_experiment_linkage_linked_when_explicit_ids_are_present(self) -> None:
        publish = _base_publish(
            metadata={
                "hook_strategy": "curiosity_gap",
                "experiment_assignment_id": "asg_001",
                "experiment_result_id": "res_001",
            }
        )
        metrics = _base_metrics()
        window_metrics = _base_window_metrics()
        assignment = {
            "assignment_id": "asg_001",
            "experiment_id": "exp_001",
            "subject_key": "acc_ca_001|2026-03-02T10:15:00Z|sealed tunnel",
            "variant": "B",
        }
        result = {
            "result_id": "res_001",
            "experiment_id": "exp_001",
            "subject_key": assignment["subject_key"],
            "variant": "B",
            "window_id": publish["window_id"],
        }
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish["publish_id"]: publish}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish["account_id"], publish["video_id"], publish["window_id"]): metrics}
            ),
            window_metrics_repo=FakeWindowMetricsRepo({(publish["account_id"], publish["window_id"]): window_metrics}),
            scorecard_repo=None,
            experiment_assignments_repo=FakeKeyRepo("assignment_id", {"asg_001": assignment}),
            experiment_results_repo=FakeKeyRepo("result_id", {"res_001": result}),
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "content_attribution.jsonl"
            payload = generate_and_save_attribution(publish_id=publish["publish_id"], deps=deps, path=path)
            rows = read_all_attributions(path)

        self.assertEqual(payload["status"], "WRITTEN")
        self.assertEqual(payload["experiment_linkage_status"], "LINKED")
        self.assertTrue(payload["experiment_result_available"])
        self.assertEqual(payload["experiment_context"]["assignment_id"], "asg_001")
        self.assertEqual(payload["experiment_context"]["result_id"], "res_001")
        self.assertEqual(payload["experiment_context"]["experiment_id"], "exp_001")
        self.assertEqual(payload["experiment_context"]["variant_id"], "B")
        self.assertEqual(len(rows), 1)
        self.assertTrue(payload["evidence_summary"]["optional_present"]["experiment_assignment_record"])
        self.assertTrue(payload["evidence_summary"]["optional_present"]["experiment_result_record"])

    def test_experiment_linkage_marks_missing_assignment_honestly(self) -> None:
        publish = _base_publish(
            metadata={
                "hook_strategy": "curiosity_gap",
                "experiment_assignment_id": "asg_missing",
            }
        )
        metrics = _base_metrics()
        window_metrics = _base_window_metrics()
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish["publish_id"]: publish}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish["account_id"], publish["video_id"], publish["window_id"]): metrics}
            ),
            window_metrics_repo=FakeWindowMetricsRepo({(publish["account_id"], publish["window_id"]): window_metrics}),
            experiment_assignments_repo=FakeKeyRepo("assignment_id", {}),
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "content_attribution.jsonl"
            payload = generate_and_save_attribution(publish_id=publish["publish_id"], deps=deps, path=path)

        self.assertEqual(payload["status"], "WRITTEN")
        self.assertEqual(payload["experiment_linkage_status"], "MISSING_ASSIGNMENT")
        self.assertFalse(payload["experiment_result_available"])
        self.assertEqual(payload["experiment_context"]["assignment_id"], "asg_missing")

    def test_experiment_linkage_marks_unsafe_to_infer_when_only_creative_pack_id_exists(self) -> None:
        publish = _base_publish(
            metadata={
                "hook_strategy": "curiosity_gap",
                "creative_pack_id": "cp_001",
            }
        )
        metrics = _base_metrics()
        window_metrics = _base_window_metrics()
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish["publish_id"]: publish}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish["account_id"], publish["video_id"], publish["window_id"]): metrics}
            ),
            window_metrics_repo=FakeWindowMetricsRepo({(publish["account_id"], publish["window_id"]): window_metrics}),
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "content_attribution.jsonl"
            payload = generate_and_save_attribution(publish_id=publish["publish_id"], deps=deps, path=path)

        self.assertEqual(payload["status"], "WRITTEN")
        self.assertEqual(payload["experiment_linkage_status"], "UNSAFE_TO_INFER")
        self.assertIsNone(payload["experiment_context"])
        self.assertFalse(payload["experiment_result_available"])


if __name__ == "__main__":
    unittest.main()
