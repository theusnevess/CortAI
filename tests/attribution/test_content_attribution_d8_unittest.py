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

from app.product.attribution.builder import AttributionDeps, build_attribution
from app.product.attribution.errors import (
    AttributionConflictError,
    AttributionMetricsMissingError,
    AttributionWindowMissingError,
    PublishRecordNotFoundError,
)
from app.product.attribution.repo import save_if_absent
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


def _base_publish(*, publish_id: str = "pub_001", publish_mode: str = "auto") -> dict[str, Any]:
    return {
        "publish_id": publish_id,
        "account_id": "acc_ca_001",
        "job_id": "job_001",
        "video_id": "vid_001",
        "platform": "tiktok",
        "publish_mode": publish_mode,
        "status": "posted",
        "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "policy_stage": "GROWTH",
        "metadata": {
            "hook_strategy": "curiosity_gap",
            "effective_duration_s": 33,
            "rare_fact_placement_s": 18,
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
        "likes": 420,
        "follows": 45,
        "rpm": 1.1,
        "source_kind": "PLATFORM_ANALYTICS",
    }


def _base_window_metrics() -> dict[str, Any]:
    return {
        "account_id": "acc_ca_001",
        "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "videos_considered": 8,
        "avg_views": 3200.0,
    }


class ContentAttributionD8Tests(unittest.TestCase):
    def test_happy_path_builder_e_repo(self) -> None:
        publish = _base_publish(publish_mode="auto")
        metrics = _base_metrics()
        window_metrics = _base_window_metrics()
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish["publish_id"]: publish}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish["account_id"], publish["video_id"], publish["window_id"]): metrics}
            ),
            window_metrics_repo=FakeWindowMetricsRepo({(publish["account_id"], publish["window_id"]): window_metrics}),
            scorecard_repo=None,
        )

        attribution = build_attribution(publish["publish_id"], deps)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "content_attribution.jsonl"
            action = save_if_absent(attribution, path=path)
            rows = read_all_attributions(path)

        self.assertEqual(action, "WRITTEN")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["publish_id"], publish["publish_id"])
        self.assertEqual(row["job_id"], publish["job_id"])
        self.assertEqual(row["account_id"], publish["account_id"])
        self.assertEqual(row["video_id"], publish["video_id"])
        self.assertEqual(row["window_id"], publish["window_id"])
        self.assertEqual(row["policy_stage"], "GROWTH")
        self.assertFalse(row["human_patch_detected"])

    def test_metrics_missing_falha_explicita(self) -> None:
        publish = _base_publish()
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish["publish_id"]: publish}),
            video_metrics_repo=FakeVideoMetricsRepo(),
            window_metrics_repo=FakeWindowMetricsRepo({}),
            scorecard_repo=None,
        )
        with self.assertRaises(AttributionMetricsMissingError) as ctx:
            build_attribution(publish["publish_id"], deps)
        self.assertEqual(str(ctx.exception), "ATTRIBUTION_METRICS_MISSING")

    def test_publish_record_not_found_falha_explicita(self) -> None:
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({}),
            video_metrics_repo=FakeVideoMetricsRepo(),
            window_metrics_repo=FakeWindowMetricsRepo({}),
            scorecard_repo=None,
        )
        with self.assertRaises(PublishRecordNotFoundError) as ctx:
            build_attribution("pub_inexistente", deps)
        self.assertEqual(str(ctx.exception), "PUBLISH_RECORD_NOT_FOUND")

    def test_window_metrics_missing_falha_explicita(self) -> None:
        publish = _base_publish()
        metrics = _base_metrics()
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish["publish_id"]: publish}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish["account_id"], publish["video_id"], publish["window_id"]): metrics}
            ),
            window_metrics_repo=FakeWindowMetricsRepo({}),
            scorecard_repo=None,
        )
        with self.assertRaises(AttributionWindowMissingError) as ctx:
            build_attribution(publish["publish_id"], deps)
        self.assertEqual(str(ctx.exception), "WINDOW_METRICS_NOT_FOUND")

    def test_idempotencia_noop_payload_igual(self) -> None:
        publish = _base_publish()
        metrics = _base_metrics()
        window_metrics = _base_window_metrics()
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish["publish_id"]: publish}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish["account_id"], publish["video_id"], publish["window_id"]): metrics}
            ),
            window_metrics_repo=FakeWindowMetricsRepo({(publish["account_id"], publish["window_id"]): window_metrics}),
            scorecard_repo=None,
        )
        attribution = build_attribution(publish["publish_id"], deps)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "content_attribution.jsonl"
            first = save_if_absent(attribution, path=path)
            second = save_if_absent(attribution, path=path)
            rows = read_all_attributions(path)

        self.assertEqual(first, "WRITTEN")
        self.assertEqual(second, "NOOP")
        self.assertEqual(len(rows), 1)

    def test_idempotencia_conflict_payload_diferente(self) -> None:
        publish = _base_publish()
        metrics = _base_metrics()
        window_metrics = _base_window_metrics()
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish["publish_id"]: publish}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish["account_id"], publish["video_id"], publish["window_id"]): metrics}
            ),
            window_metrics_repo=FakeWindowMetricsRepo({(publish["account_id"], publish["window_id"]): window_metrics}),
            scorecard_repo=None,
        )
        attribution_a = build_attribution(publish["publish_id"], deps)
        attribution_b = dict(attribution_a)
        attribution_b["views"] = int(attribution_b["views"]) + 1

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "content_attribution.jsonl"
            first = save_if_absent(attribution_a, path=path)
            with self.assertRaises(AttributionConflictError) as ctx:
                save_if_absent(attribution_b, path=path)
            rows = read_all_attributions(path)

        self.assertEqual(first, "WRITTEN")
        self.assertEqual(str(ctx.exception), "ATTRIBUTION_CONFLICT")
        self.assertEqual(len(rows), 1)

    def test_human_patch_detected_manual_true_auto_false(self) -> None:
        metrics = _base_metrics()
        window_metrics = _base_window_metrics()

        publish_auto = _base_publish(publish_id="pub_auto", publish_mode="auto")
        deps_auto = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish_auto["publish_id"]: publish_auto}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish_auto["account_id"], publish_auto["video_id"], publish_auto["window_id"]): metrics}
            ),
            window_metrics_repo=FakeWindowMetricsRepo(
                {(publish_auto["account_id"], publish_auto["window_id"]): window_metrics}
            ),
            scorecard_repo=None,
        )

        publish_manual = _base_publish(publish_id="pub_manual", publish_mode="manual")
        deps_manual = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish_manual["publish_id"]: publish_manual}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish_manual["account_id"], publish_manual["video_id"], publish_manual["window_id"]): metrics}
            ),
            window_metrics_repo=FakeWindowMetricsRepo(
                {(publish_manual["account_id"], publish_manual["window_id"]): window_metrics}
            ),
            scorecard_repo=None,
        )

        auto_attr = build_attribution("pub_auto", deps_auto)
        manual_attr = build_attribution("pub_manual", deps_manual)

        self.assertFalse(auto_attr["human_patch_detected"])
        self.assertTrue(manual_attr["human_patch_detected"])


if __name__ == "__main__":
    unittest.main()
