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
from app.guard.data_consistency.errors import ConsistencyViolationBlocked
from app.product.scorecard.generator import generate_real_batch_scorecard
from app.product.scorecard.repo import ScorecardInvariantError
from app.product.scorecard.service import generate_scorecard_for_window
from app.product.scorecard.store_jsonl import read_all_records


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


def _metrics(
    video_id: str,
    *,
    account_id: str = "acc_ca_001",
    views: int = 300,
    retention: float = 0.45,
    completion: float = 0.33,
    rpm: float = 0.9,
) -> dict[str, object]:
    return {
        "video_id": video_id,
        "account_id": account_id,
        "captured_at": "2026-03-04T10:00:00Z",
        "captured_window_id": _window_id(),
        "source_kind": "PLATFORM_ANALYTICS",
        "views": views,
        "retention_3s": retention,
        "completion_rate": completion,
        "likes": 10,
        "follows": 2,
        "rpm": rpm,
        "ingested_at": "2026-03-05T00:01:00Z",
    }


def _window_metrics(
    *,
    videos_considered: int = 2,
    avg_views: float = 300.0,
    avg_retention_3s: float = 0.45,
    avg_completion_rate: float = 0.33,
    avg_rpm: float = 0.9,
    with_missing_fields: bool = False,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "window_id": _window_id(),
        "account_id": "acc_ca_001",
        "videos_considered": videos_considered,
        "avg_views": avg_views,
        "avg_retention_3s": avg_retention_3s,
        "avg_completion_rate": avg_completion_rate,
        "avg_rpm": avg_rpm,
        "total_views": int(avg_views * max(videos_considered, 1)),
        "total_follows": 4,
        "computed_at": "2026-03-05T00:10:00Z",
    }
    if with_missing_fields:
        payload["videos_with_metrics"] = 1
        payload["videos_missing_metrics"] = 1
    return payload


class RealBatchScorecardD7Tests(unittest.TestCase):
    def test_gera_scorecard_quando_guard_passa(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            publish_path = base / "publish_records.jsonl"
            metrics_path = base / "video_metrics.jsonl"
            window_path = base / "window_metrics.jsonl"
            scorecard_path = base / "scorecards.jsonl"

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

            result = generate_scorecard_for_window(
                account_id="acc_ca_001",
                window_id=_window_id(),
                generated_at="2026-03-05T02:00:00Z",
                deps={
                    "publish_records_path": publish_path,
                    "video_metrics_path": metrics_path,
                    "window_metrics_path": window_path,
                },
                scorecard_path=scorecard_path,
            )
            self.assertEqual(result["write_action"], "WRITTEN")
            self.assertEqual(result["scorecard"]["window_id"], _window_id())

    def test_bloqueia_geracao_quando_guard_falha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            publish_path = base / "publish_records.jsonl"
            metrics_path = base / "video_metrics.jsonl"
            window_path = base / "window_metrics.jsonl"
            scorecard_path = base / "scorecards.jsonl"

            write_publish_record(
                _publish_record(
                    publish_id="pub_1",
                    job_id="job_1",
                    video_id="vid_1",
                    published_at="2026-03-03T00:01:00Z",
                ),
                path=publish_path,
            )
            write_video_metrics(_metrics("vid_orfao"), path=metrics_path)
            save_window_metrics(_window_metrics(videos_considered=1), path=window_path)

            with self.assertRaises(ConsistencyViolationBlocked):
                generate_scorecard_for_window(
                    account_id="acc_ca_001",
                    window_id=_window_id(),
                    generated_at="2026-03-05T02:00:00Z",
                    deps={
                        "publish_records_path": publish_path,
                        "video_metrics_path": metrics_path,
                        "window_metrics_path": window_path,
                    },
                    scorecard_path=scorecard_path,
                )

    def test_idempotencia_por_account_e_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            publish_path = base / "publish_records.jsonl"
            metrics_path = base / "video_metrics.jsonl"
            window_path = base / "window_metrics.jsonl"
            scorecard_path = base / "scorecards.jsonl"

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

            first = generate_scorecard_for_window(
                account_id="acc_ca_001",
                window_id=_window_id(),
                generated_at="2026-03-05T02:00:00Z",
                deps={
                    "publish_records_path": publish_path,
                    "video_metrics_path": metrics_path,
                    "window_metrics_path": window_path,
                },
                scorecard_path=scorecard_path,
            )
            second = generate_scorecard_for_window(
                account_id="acc_ca_001",
                window_id=_window_id(),
                generated_at="2026-03-05T02:00:00Z",
                deps={
                    "publish_records_path": publish_path,
                    "video_metrics_path": metrics_path,
                    "window_metrics_path": window_path,
                },
                scorecard_path=scorecard_path,
            )
            self.assertEqual(first["write_action"], "WRITTEN")
            self.assertEqual(second["write_action"], "NOOP")

    def test_recomendacao_e_status_sao_gerados_por_metricas(self) -> None:
        recovery = generate_real_batch_scorecard(
            window_metrics=_window_metrics(avg_retention_3s=0.30),
            generated_at="2026-03-05T02:00:00Z",
        )
        optimize = generate_real_batch_scorecard(
            window_metrics=_window_metrics(avg_retention_3s=0.42, avg_completion_rate=0.20),
            generated_at="2026-03-05T02:00:00Z",
        )
        stable = generate_real_batch_scorecard(
            window_metrics=_window_metrics(avg_retention_3s=0.45, avg_completion_rate=0.35, avg_views=450.0),
            generated_at="2026-03-05T02:00:00Z",
        )

        self.assertEqual(recovery["status"], "RECOVERY")
        self.assertEqual(optimize["status"], "OPTIMIZE")
        self.assertEqual(stable["status"], "STABLE")

    def test_persistencia_append_only_e_conflito_explicito(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            publish_path = base / "publish_records.jsonl"
            metrics_path = base / "video_metrics.jsonl"
            window_path = base / "window_metrics.jsonl"
            scorecard_path = base / "scorecards.jsonl"

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

            generate_scorecard_for_window(
                account_id="acc_ca_001",
                window_id=_window_id(),
                generated_at="2026-03-05T02:00:00Z",
                deps={
                    "publish_records_path": publish_path,
                    "video_metrics_path": metrics_path,
                    "window_metrics_path": window_path,
                },
                scorecard_path=scorecard_path,
            )
            rows = read_all_records(scorecard_path)
            self.assertEqual(len(rows), 1)

            # Muda generated_at para forçar payload diferente na mesma chave.
            with self.assertRaises(ScorecardInvariantError):
                generate_scorecard_for_window(
                    account_id="acc_ca_001",
                    window_id=_window_id(),
                    generated_at="2026-03-05T03:00:00Z",
                    deps={
                        "publish_records_path": publish_path,
                        "video_metrics_path": metrics_path,
                        "window_metrics_path": window_path,
                    },
                    scorecard_path=scorecard_path,
                )
            rows_after = read_all_records(scorecard_path)
            self.assertEqual(len(rows_after), 1)


if __name__ == "__main__":
    unittest.main()
