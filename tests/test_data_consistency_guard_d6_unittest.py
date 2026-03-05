from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.data.publish_records.writer import write_publish_record
from app.data.video_metrics.writer import write_video_metrics
from app.data.window_metrics.repo import save_window_metrics
from app.guard.data_consistency.guard import run_data_consistency_guard


def _window_id() -> str:
    return "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"


def _publish_record(
    *,
    publish_id: str,
    job_id: str,
    video_id: str,
    published_at: str,
    account_id: str = "acc_ca_001",
) -> dict[str, str]:
    return {
        "publish_id": publish_id,
        "account_id": account_id,
        "job_id": job_id,
        "video_id": video_id,
        "platform": "tiktok",
        "publish_mode": "auto",
        "status": "posted",
        "published_at": published_at,
        "created_at": published_at,
        "metadata": {},
    }


def _metrics(video_id: str, *, account_id: str = "acc_ca_001", views: int = 100) -> dict[str, object]:
    return {
        "video_id": video_id,
        "account_id": account_id,
        "captured_at": "2026-03-04T10:00:00Z",
        "captured_window_id": _window_id(),
        "source_kind": "PLATFORM_ANALYTICS",
        "views": views,
        "retention_3s": 0.5,
        "completion_rate": 0.3,
        "likes": 8,
        "follows": 1,
        "rpm": 0.8,
        "ingested_at": "2026-03-05T00:01:00Z",
    }


def _window_metrics(
    *,
    videos_considered: int,
    videos_with_metrics: int | None = None,
    videos_missing_metrics: int | None = None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "window_id": _window_id(),
        "account_id": "acc_ca_001",
        "videos_considered": videos_considered,
        "avg_views": 100.0,
        "avg_retention_3s": 0.5,
        "avg_completion_rate": 0.3,
        "avg_rpm": 0.8,
        "total_views": 200,
        "total_follows": 2,
        "computed_at": "2026-03-05T00:10:00Z",
    }
    if videos_with_metrics is not None:
        data["videos_with_metrics"] = videos_with_metrics
    if videos_missing_metrics is not None:
        data["videos_missing_metrics"] = videos_missing_metrics
    return data


class DataConsistencyGuardD6Tests(unittest.TestCase):
    def test_pass_quando_publish_metrics_e_window_sao_consistentes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            publish_path = base / "publish_records.jsonl"
            metrics_path = base / "video_metrics.jsonl"
            window_path = base / "window_metrics.jsonl"

            write_publish_record(
                _publish_record(
                    publish_id="pub_1",
                    job_id="job_1",
                    video_id="vid_1",
                    published_at="2026-03-03T00:01:00Z",
                ),
                path=publish_path,
            )
            write_publish_record(
                _publish_record(
                    publish_id="pub_2",
                    job_id="job_2",
                    video_id="vid_2",
                    published_at="2026-03-03T00:02:00Z",
                ),
                path=publish_path,
            )
            write_video_metrics(_metrics("vid_1"), path=metrics_path)
            write_video_metrics(_metrics("vid_2"), path=metrics_path)
            save_window_metrics(_window_metrics(videos_considered=2), path=window_path)

            result = run_data_consistency_guard(
                "acc_ca_001",
                _window_id(),
                {
                    "publish_records_path": publish_path,
                    "video_metrics_path": metrics_path,
                    "window_metrics_path": window_path,
                },
            )
            self.assertTrue(result.ok)
            self.assertFalse(result.blocked)

    def test_block_quando_metrics_tem_video_sem_publish_record_vcg001(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            publish_path = base / "publish_records.jsonl"
            metrics_path = base / "video_metrics.jsonl"
            window_path = base / "window_metrics.jsonl"

            write_publish_record(
                _publish_record(
                    publish_id="pub_1",
                    job_id="job_1",
                    video_id="vid_1",
                    published_at="2026-03-03T00:01:00Z",
                ),
                path=publish_path,
            )
            write_video_metrics(_metrics("vid_1"), path=metrics_path)
            write_video_metrics(_metrics("vid_orfao"), path=metrics_path)
            save_window_metrics(_window_metrics(videos_considered=1), path=window_path)

            result = run_data_consistency_guard(
                "acc_ca_001",
                _window_id(),
                {
                    "publish_records_path": publish_path,
                    "video_metrics_path": metrics_path,
                    "window_metrics_path": window_path,
                },
            )
            self.assertTrue(result.blocked)
            self.assertEqual(result.reason_code, "CONSISTENCY_VIOLATION_BLOCKED")
            self.assertTrue(any(item.check_id == "VCG_001" for item in result.violations))

    def test_block_quando_videos_considered_diverge_do_publish_count_vcg003(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            publish_path = base / "publish_records.jsonl"
            metrics_path = base / "video_metrics.jsonl"
            window_path = base / "window_metrics.jsonl"

            write_publish_record(
                _publish_record(
                    publish_id="pub_1",
                    job_id="job_1",
                    video_id="vid_1",
                    published_at="2026-03-03T00:01:00Z",
                ),
                path=publish_path,
            )
            write_video_metrics(_metrics("vid_1"), path=metrics_path)
            save_window_metrics(_window_metrics(videos_considered=3), path=window_path)

            result = run_data_consistency_guard(
                "acc_ca_001",
                _window_id(),
                {
                    "publish_records_path": publish_path,
                    "video_metrics_path": metrics_path,
                    "window_metrics_path": window_path,
                },
            )
            self.assertTrue(result.blocked)
            self.assertTrue(any(item.check_id == "VCG_003" for item in result.violations))

    def test_block_quando_contabilizacao_missing_esta_inconsistente_vcg004(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            publish_path = base / "publish_records.jsonl"
            metrics_path = base / "video_metrics.jsonl"
            window_path = base / "window_metrics.jsonl"

            write_publish_record(
                _publish_record(
                    publish_id="pub_1",
                    job_id="job_1",
                    video_id="vid_1",
                    published_at="2026-03-03T00:01:00Z",
                ),
                path=publish_path,
            )
            write_publish_record(
                _publish_record(
                    publish_id="pub_2",
                    job_id="job_2",
                    video_id="vid_2",
                    published_at="2026-03-03T00:02:00Z",
                ),
                path=publish_path,
            )
            write_video_metrics(_metrics("vid_1"), path=metrics_path)
            save_window_metrics(
                _window_metrics(videos_considered=2, videos_with_metrics=2, videos_missing_metrics=2),
                path=window_path,
            )

            result = run_data_consistency_guard(
                "acc_ca_001",
                _window_id(),
                {
                    "publish_records_path": publish_path,
                    "video_metrics_path": metrics_path,
                    "window_metrics_path": window_path,
                },
            )
            self.assertTrue(result.blocked)
            self.assertTrue(any(item.check_id == "VCG_004" for item in result.violations))

    def test_skip_quando_repo_job_specs_nao_esta_disponivel_vcg002(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            publish_path = base / "publish_records.jsonl"
            metrics_path = base / "video_metrics.jsonl"
            window_path = base / "window_metrics.jsonl"

            write_publish_record(
                _publish_record(
                    publish_id="pub_1",
                    job_id="job_1",
                    video_id="vid_1",
                    published_at="2026-03-03T00:01:00Z",
                ),
                path=publish_path,
            )
            write_video_metrics(_metrics("vid_1"), path=metrics_path)
            save_window_metrics(_window_metrics(videos_considered=1), path=window_path)

            result = run_data_consistency_guard(
                "acc_ca_001",
                _window_id(),
                {
                    "publish_records_path": publish_path,
                    "video_metrics_path": metrics_path,
                    "window_metrics_path": window_path,
                },
            )
            skipped = [item for item in result.violations if item.check_id == "VCG_002"]
            self.assertEqual(len(skipped), 1)
            self.assertEqual(skipped[0].status, "SKIPPED_NOT_AVAILABLE")


if __name__ == "__main__":
    unittest.main()
