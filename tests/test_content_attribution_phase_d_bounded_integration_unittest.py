from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.product.attribution.builder import AttributionDeps
from app.product.attribution.service import generate_and_save_attribution
from app.product.strategy_learning.errors import StrategyAttributionEmptyError
from app.product.strategy_learning.service import generate_and_save_strategy_patch


class FakePublishRecordsRepo:
    def __init__(self, rows: dict[str, dict[str, Any]]) -> None:
        self.rows = rows

    def get_by_publish_id(self, publish_id: str) -> dict[str, Any] | None:
        return self.rows.get(publish_id)


class FakeVideoMetricsRepo:
    def __init__(self, best_rows: dict[tuple[str, str, str], dict[str, Any]]) -> None:
        self.best_rows = best_rows

    def get_best(self, account_id: str, video_id: str, captured_window_id: str) -> dict[str, Any] | None:
        return self.best_rows.get((account_id, video_id, captured_window_id))

    def get_latest_for_video(self, account_id: str, video_id: str) -> dict[str, Any] | None:
        return None


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


def _publish(*, publish_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "publish_id": publish_id,
        "account_id": "acc_ca_001",
        "job_id": f"job_{publish_id}",
        "video_id": f"vid_{publish_id}",
        "publish_mode": "auto",
        "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "policy_stage": "GROWTH",
        "metadata": metadata or {
            "hook_strategy": "curiosity_gap",
            "effective_duration_s": 33,
        },
    }


def _metrics(*, publish_id: str) -> dict[str, Any]:
    return {
        "account_id": "acc_ca_001",
        "video_id": f"vid_{publish_id}",
        "captured_window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "captured_at": "2026-03-05T00:02:00Z",
        "views": 12345,
        "retention_3s": 0.52,
        "completion_rate": 0.38,
    }


def _window_metrics() -> dict[str, Any]:
    return {
        "account_id": "acc_ca_001",
        "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "videos_with_metrics": 8,
    }


def _scorecard() -> dict[str, Any]:
    return {
        "scorecard_id": "sc_001",
        "account_id": "acc_ca_001",
        "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "status": "STABLE",
    }


class ContentAttributionPhaseDBoundedIntegrationTests(unittest.TestCase):
    def test_valid_attribution_rows_create_real_but_bounded_strategy_effect(self) -> None:
        publishes = {f"pub_{index}": _publish(publish_id=f"pub_{index}") for index in range(1, 6)}
        metrics = {
            ("acc_ca_001", f"vid_pub_{index}", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"): _metrics(publish_id=f"pub_{index}")
            for index in range(1, 6)
        }
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo(publishes),
            video_metrics_repo=FakeVideoMetricsRepo(metrics),
            window_metrics_repo=FakeWindowMetricsRepo({("acc_ca_001", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"): _window_metrics()}),
        )

        attribution_rows = []
        with tempfile.TemporaryDirectory() as tmp:
            attribution_path = Path(tmp) / "content_attribution.jsonl"
            patch_path = Path(tmp) / "strategy_patches.jsonl"
            for publish_id in sorted(publishes):
                payload = generate_and_save_attribution(publish_id=publish_id, deps=deps, path=attribution_path)
                self.assertEqual(payload["status"], "WRITTEN")
                attribution_rows.append(dict(payload["attribution"], dominant_failure_reason="missing_number", hook_strategy="curiosity_gap"))

            result = generate_and_save_strategy_patch(
                scorecard=_scorecard(),
                window_metrics=_window_metrics(),
                attributions=attribution_rows,
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
                path=patch_path,
            )

        patch = result["patch"]
        self.assertTrue(patch["active"])
        self.assertEqual(result["write_action"], "WRITTEN")
        self.assertIn("A1", patch["layers_applied"])
        self.assertIn("A4", patch["layers_applied"])
        self.assertEqual(set(patch["overrides"].keys()), {"a1_prefs_override", "a4_defaults_override", "a5_rewrite_defaults_override"})
        self.assertNotIn("experiment_id", patch)
        self.assertNotIn("assignment_id", patch)
        self.assertEqual(patch["inputs"]["attribution_count"], 5)

    def test_missing_metrics_do_not_produce_false_downstream_patch(self) -> None:
        publish = _publish(publish_id="pub_missing")
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish["publish_id"]: publish}),
            video_metrics_repo=FakeVideoMetricsRepo({}),
            window_metrics_repo=FakeWindowMetricsRepo({}),
        )
        payload = generate_and_save_attribution(publish_id=publish["publish_id"], deps=deps)

        self.assertEqual(payload["status"], "SKIPPED")
        self.assertIsNone(payload["attribution"])

        with self.assertRaises(StrategyAttributionEmptyError):
            generate_and_save_strategy_patch(
                scorecard=_scorecard(),
                window_metrics=_window_metrics(),
                attributions=[],
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
            )

    def test_experiment_linked_and_not_present_paths_do_not_change_patch_ownership(self) -> None:
        linked_publish = _publish(
            publish_id="pub_linked",
            metadata={
                "hook_strategy": "curiosity_gap",
                "experiment_assignment_id": "asg_001",
                "experiment_result_id": "res_001",
            },
        )
        plain_publish = _publish(
            publish_id="pub_plain",
            metadata={
                "hook_strategy": "curiosity_gap",
            },
        )
        metrics = {
            ("acc_ca_001", "vid_pub_linked", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"): _metrics(publish_id="pub_linked"),
            ("acc_ca_001", "vid_pub_plain", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"): _metrics(publish_id="pub_plain"),
        }
        assignment = {
            "assignment_id": "asg_001",
            "experiment_id": "exp_001",
            "subject_key": "acc_ca_001|2026-03-02T10:15:00Z|sealed tunnel",
            "variant": "B",
        }
        result_row = {
            "result_id": "res_001",
            "experiment_id": "exp_001",
            "subject_key": assignment["subject_key"],
            "variant": "B",
            "window_id": linked_publish["window_id"],
        }
        deps = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({
                linked_publish["publish_id"]: linked_publish,
                plain_publish["publish_id"]: plain_publish,
            }),
            video_metrics_repo=FakeVideoMetricsRepo(metrics),
            window_metrics_repo=FakeWindowMetricsRepo({("acc_ca_001", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"): _window_metrics()}),
            experiment_assignments_repo=FakeKeyRepo("assignment_id", {"asg_001": assignment}),
            experiment_results_repo=FakeKeyRepo("result_id", {"res_001": result_row}),
        )

        with tempfile.TemporaryDirectory() as tmp:
            attribution_path = Path(tmp) / "content_attribution.jsonl"
            linked_payload = generate_and_save_attribution(publish_id="pub_linked", deps=deps, path=attribution_path)
            plain_payload = generate_and_save_attribution(publish_id="pub_plain", deps=deps, path=attribution_path)

            linked_rows = [dict(linked_payload["attribution"], dominant_failure_reason="missing_number", hook_strategy="curiosity_gap") for _ in range(5)]
            plain_rows = [dict(plain_payload["attribution"], dominant_failure_reason="missing_number", hook_strategy="curiosity_gap") for _ in range(5)]

            linked_patch = generate_and_save_strategy_patch(
                scorecard=_scorecard(),
                window_metrics=_window_metrics(),
                attributions=linked_rows,
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
                path=Path(tmp) / "linked_strategy_patches.jsonl",
            )["patch"]
            plain_patch = generate_and_save_strategy_patch(
                scorecard=_scorecard(),
                window_metrics=_window_metrics(),
                attributions=plain_rows,
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
                path=Path(tmp) / "plain_strategy_patches.jsonl",
            )["patch"]

        self.assertEqual(linked_payload["experiment_linkage_status"], "LINKED")
        self.assertEqual(plain_payload["experiment_linkage_status"], "NOT_PRESENT")
        self.assertEqual(linked_patch["layers_applied"], plain_patch["layers_applied"])
        self.assertEqual(linked_patch["reason_codes"], plain_patch["reason_codes"])
        self.assertNotIn("experiment_id", linked_patch)
        self.assertNotIn("experiment_id", plain_patch)


if __name__ == "__main__":
    unittest.main()
