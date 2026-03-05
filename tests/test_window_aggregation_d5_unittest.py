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
from app.data.window_metrics.aggregator import aggregate_window_metrics
from app.data.window_metrics.invariants import WindowMetricsInvariantError
from app.data.window_metrics.repo import get_by_key, save_window_metrics
from app.data.window_metrics.selector import build_window_id, select_window_video_ids


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


def _metrics(
    *,
    video_id: str,
    views: int,
    retention_3s: float | None,
    completion_rate: float | None,
    rpm: float | None,
    follows: int | None = None,
    account_id: str = "acc_ca_001",
) -> dict[str, object]:
    return {
        "video_id": video_id,
        "account_id": account_id,
        "captured_at": "2026-03-04T10:00:00Z",
        "captured_window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "source_kind": "PLATFORM_ANALYTICS",
        "views": views,
        "retention_3s": retention_3s,
        "completion_rate": completion_rate,
        "likes": 10,
        "follows": follows,
        "rpm": rpm,
        "ingested_at": "2026-03-05T00:01:00Z",
    }


class WindowAggregationD5Tests(unittest.TestCase):
    def test_agregacao_basica_com_medias_corretas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            publish_path = base / "publish_records.jsonl"
            metrics_path = base / "video_metrics.jsonl"

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
            write_publish_record(
                _publish_record(
                    publish_id="pub_3",
                    job_id="job_3",
                    video_id="vid_3",
                    published_at="2026-03-03T00:03:00Z",
                ),
                path=publish_path,
            )

            write_video_metrics(_metrics(video_id="vid_1", views=100, retention_3s=0.5, completion_rate=0.3, rpm=1.0), path=metrics_path)
            write_video_metrics(_metrics(video_id="vid_2", views=200, retention_3s=0.4, completion_rate=0.2, rpm=0.8), path=metrics_path)
            write_video_metrics(_metrics(video_id="vid_3", views=300, retention_3s=0.6, completion_rate=0.4, rpm=1.2), path=metrics_path)

            window_id = build_window_id("2026-03-02T00:00:00Z", "2026-03-05T00:00:00Z")
            video_ids = select_window_video_ids(
                "acc_ca_001",
                "2026-03-02T00:00:00Z",
                "2026-03-05T00:00:00Z",
                path=publish_path,
            )
            aggregated = aggregate_window_metrics(
                account_id="acc_ca_001",
                window_id=window_id,
                video_ids=video_ids,
                computed_at="2026-03-05T00:10:00Z",
                video_metrics_path=metrics_path,
            )

            self.assertEqual(aggregated["videos_considered"], 3)
            self.assertEqual(aggregated["avg_views"], 200.0)
            self.assertEqual(aggregated["total_views"], 600)
            self.assertAlmostEqual(aggregated["avg_retention_3s"], 0.5, places=6)
            self.assertAlmostEqual(aggregated["avg_completion_rate"], 0.3, places=6)
            self.assertAlmostEqual(aggregated["avg_rpm"], 1.0, places=6)

    def test_ignora_metricas_ausentes_nas_medias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metrics_path = Path(tmp) / "video_metrics.jsonl"
            window_id = "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"
            video_ids = ["vid_1", "vid_2"]

            write_video_metrics(
                _metrics(video_id="vid_1", views=100, retention_3s=None, completion_rate=0.4, rpm=1.0),
                path=metrics_path,
            )
            write_video_metrics(
                _metrics(video_id="vid_2", views=300, retention_3s=0.6, completion_rate=0.2, rpm=1.2),
                path=metrics_path,
            )

            aggregated = aggregate_window_metrics(
                account_id="acc_ca_001",
                window_id=window_id,
                video_ids=video_ids,
                computed_at="2026-03-05T00:10:00Z",
                video_metrics_path=metrics_path,
            )

            self.assertAlmostEqual(aggregated["avg_retention_3s"], 0.6, places=6)
            self.assertAlmostEqual(aggregated["avg_completion_rate"], 0.3, places=6)

    def test_determinismo_mesmos_inputs_mesmo_resultado(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metrics_path = Path(tmp) / "video_metrics.jsonl"
            window_id = "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"
            video_ids = ["vid_1", "vid_2"]

            write_video_metrics(
                _metrics(video_id="vid_1", views=100, retention_3s=0.5, completion_rate=0.3, rpm=1.1),
                path=metrics_path,
            )
            write_video_metrics(
                _metrics(video_id="vid_2", views=200, retention_3s=0.4, completion_rate=0.2, rpm=0.9),
                path=metrics_path,
            )

            first = aggregate_window_metrics(
                account_id="acc_ca_001",
                window_id=window_id,
                video_ids=video_ids,
                computed_at="2026-03-05T00:10:00Z",
                video_metrics_path=metrics_path,
            )
            second = aggregate_window_metrics(
                account_id="acc_ca_001",
                window_id=window_id,
                video_ids=video_ids,
                computed_at="2026-03-05T00:10:00Z",
                video_metrics_path=metrics_path,
            )

            self.assertEqual(first, second)

    def test_idempotencia_reexecucao_gera_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "window_metrics.jsonl"
            record = {
                "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
                "account_id": "acc_ca_001",
                "videos_considered": 2,
                "avg_views": 150.0,
                "avg_retention_3s": 0.45,
                "avg_completion_rate": 0.25,
                "avg_rpm": 1.0,
                "total_views": 300,
                "total_follows": 5,
                "computed_at": "2026-03-05T00:10:00Z",
            }

            first = save_window_metrics(record, path=store_path)
            second = save_window_metrics(record, path=store_path)

            self.assertEqual(first, "WRITTEN")
            self.assertEqual(second, "NOOP")
            saved = get_by_key("acc_ca_001", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z", path=store_path)
            self.assertIsNotNone(saved)

    def test_erro_para_conflito_mesma_chave_dados_diferentes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "window_metrics.jsonl"
            first_record = {
                "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
                "account_id": "acc_ca_001",
                "videos_considered": 2,
                "avg_views": 150.0,
                "avg_retention_3s": 0.45,
                "avg_completion_rate": 0.25,
                "avg_rpm": 1.0,
                "total_views": 300,
                "total_follows": 5,
                "computed_at": "2026-03-05T00:10:00Z",
            }
            conflicting_record = dict(first_record)
            conflicting_record["total_views"] = 301

            save_window_metrics(first_record, path=store_path)
            with self.assertRaises(WindowMetricsInvariantError):
                save_window_metrics(conflicting_record, path=store_path)


if __name__ == "__main__":
    unittest.main()
