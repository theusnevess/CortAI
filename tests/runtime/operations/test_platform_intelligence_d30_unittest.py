from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.data.publish_records.writer import write_publish_record
from app.data.video_metrics.writer import write_video_metrics
from app.intelligence.service import PlatformIntelligenceService


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class PlatformIntelligenceD30Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.publish_path = self.out / "data" / "publish_records" / "publish_records.jsonl"
        self.metrics_path = self.out / "data" / "video_metrics" / "video_metrics.jsonl"
        self.events_path = self.out / "events" / "events.jsonl"
        self.intelligence_dir = self.out / "intelligence"
        self.service = PlatformIntelligenceService(
            publish_records_path=self.publish_path,
            video_metrics_path=self.metrics_path,
            events_path=self.events_path,
            intelligence_dir=self.intelligence_dir,
        )

    def _seed_publish_and_metrics(self) -> None:
        write_publish_record(
            {
                "publish_id": "pub_1",
                "account_id": "acc_001",
                "job_id": "job_1",
                "video_id": "ext_1",
                "platform": "tiktok",
                "publish_mode": "auto",
                "status": "posted",
                "published_at": "2026-03-07T14:05:00Z",
                "created_at": "2026-03-07T14:05:00Z",
                "metadata": {},
            },
            path=self.publish_path,
        )
        write_publish_record(
            {
                "publish_id": "pub_2",
                "account_id": "acc_001",
                "job_id": "job_2",
                "video_id": "ext_2",
                "platform": "tiktok",
                "publish_mode": "auto",
                "status": "posted",
                "published_at": "2026-03-07T14:40:00Z",
                "created_at": "2026-03-07T14:40:00Z",
                "metadata": {},
            },
            path=self.publish_path,
        )
        write_publish_record(
            {
                "publish_id": "pub_3",
                "account_id": "acc_001",
                "job_id": "job_3",
                "video_id": "ext_3",
                "platform": "tiktok",
                "publish_mode": "auto",
                "status": "posted",
                "published_at": "2026-03-07T19:10:00Z",
                "created_at": "2026-03-07T19:10:00Z",
                "metadata": {},
            },
            path=self.publish_path,
        )
        for idx, views, completion in ((1, 2000, 0.52), (2, 1800, 0.49), (3, 500, 0.21)):
            write_video_metrics(
                {
                    "video_id": f"ext_{idx}",
                    "provider": "tiktok",
                    "external_video_id": f"ext_{idx}",
                    "account_id": "acc_001",
                    "captured_window_id": "w_001",
                    "views": views,
                    "likes": 100,
                    "completion_rate": completion,
                    "follows": 5,
                    "retention_3s": 0.7,
                    "captured_at": f"2026-03-07T2{idx}:00:00Z",
                    "ingested_at": f"2026-03-07T2{idx}:05:00Z",
                    "source_kind": "PLATFORM_ANALYTICS",
                },
                path=self.metrics_path,
            )

    def _seed_safety_events(self) -> None:
        _write_jsonl(
            self.events_path,
            [
                {"event_type": "SAFETY/pacing_delay", "account_id": "acc_001", "ts": "2026-03-07T15:00:00Z"},
                {"event_type": "SAFETY/risk_detected", "account_id": "acc_001", "ts": "2026-03-07T16:00:00Z"},
                {"event_type": "SAFETY/cooldown_started", "account_id": "acc_001", "ts": "2026-03-07T17:00:00Z"},
            ],
        )

    def _rows(self, name: str) -> list[dict]:
        path = self.intelligence_dir / name
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def test_gera_janela_recomendada(self) -> None:
        self._seed_publish_and_metrics()
        bundle = self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        self.assertEqual(bundle.publish_window.best_publish_windows[0], "14:00")
        self.assertEqual(bundle.actions["publish_window"], "WRITTEN")

    def test_gera_pacing_recomendado(self) -> None:
        self._seed_publish_and_metrics()
        self._seed_safety_events()
        bundle = self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        self.assertEqual(bundle.pacing.recommended_min_interval_minutes, 180)
        self.assertIn("COOLDOWN_SEEN", bundle.pacing.reason_codes)

    def test_conta_com_sinais_de_risco(self) -> None:
        self._seed_safety_events()
        bundle = self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        self.assertEqual(bundle.risk_profile.risk_level, "HIGH")
        self.assertEqual(bundle.account_health.account_health, "AT_RISK")

    def test_estabilidade_deterministica(self) -> None:
        self._seed_publish_and_metrics()
        self._seed_safety_events()
        first = self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        second = self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        self.assertEqual(first.publish_window.to_dict(), second.publish_window.to_dict())
        self.assertEqual(first.pacing.to_dict(), second.pacing.to_dict())
        self.assertEqual(first.risk_profile.to_dict(), second.risk_profile.to_dict())
        self.assertEqual(first.account_health.to_dict(), second.account_health.to_dict())
        self.assertEqual(second.actions["publish_window"], "NOOP")

    def test_persistencia_append_only(self) -> None:
        self._seed_publish_and_metrics()
        self._seed_safety_events()
        self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        self.assertEqual(len(self._rows("publish_windows.jsonl")), 1)
        self.assertEqual(len(self._rows("pacing_profiles.jsonl")), 1)
        self.assertEqual(len(self._rows("risk_profiles.jsonl")), 1)
        self.assertEqual(len(self._rows("account_health.jsonl")), 1)

    def test_recomputacao_nao_duplica_registros(self) -> None:
        self._seed_publish_and_metrics()
        self._seed_safety_events()
        self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        self.assertEqual(len(self._rows("publish_windows.jsonl")), 1)
        self.assertEqual(len(self._rows("pacing_profiles.jsonl")), 1)
        self.assertEqual(len(self._rows("risk_profiles.jsonl")), 1)
        self.assertEqual(len(self._rows("account_health.jsonl")), 1)


if __name__ == "__main__":
    unittest.main()
