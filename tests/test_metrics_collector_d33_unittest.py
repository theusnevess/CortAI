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

from app.data.publish_records.writer import write_publish_record
from app.metrics.collector import MetricsCollectorService
from app.metrics.provider_adapter import (
    MetricsProviderRateLimit,
    MetricsProviderTimeout,
    StubMetricsProviderAdapter,
)
from app.metrics.store_jsonl import read_all_records


class FlakyTimeoutProvider(StubMetricsProviderAdapter):
    def __init__(self, fail_times: int = 1) -> None:
        super().__init__()
        self.fail_times = fail_times
        self.calls = 0

    def fetch_video_metrics(self, **kwargs):  # type: ignore[override]
        self.calls += 1
        if self.calls <= self.fail_times:
            raise MetricsProviderTimeout("PROVIDER_TIMEOUT")
        return super().fetch_video_metrics(**kwargs)


class FlakyRateLimitProvider(StubMetricsProviderAdapter):
    def __init__(self, fail_times: int = 3) -> None:
        super().__init__()
        self.fail_times = fail_times
        self.calls = 0

    def fetch_video_metrics(self, **kwargs):  # type: ignore[override]
        self.calls += 1
        if self.calls <= self.fail_times:
            raise MetricsProviderRateLimit("PROVIDER_RATE_LIMIT")
        return super().fetch_video_metrics(**kwargs)


class MetricsCollectorD33Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.metrics_path = self.out / "metrics" / "video_metrics.jsonl"
        self.publish_path = self.out / "data" / "publish_records" / "publish_records.jsonl"
        self.events_path = self.out / "events" / "events.jsonl"
        write_publish_record(
            {
                "publish_id": "pub_001",
                "account_id": "acc_001",
                "job_id": "job_001",
                "video_id": "vid_001",
                "platform": "tiktok",
                "publish_mode": "auto",
                "status": "posted",
                "published_at": "2026-03-07T12:00:00Z",
                "created_at": "2026-03-07T12:00:00Z",
                "metadata": {},
            },
            path=self.publish_path,
        )

    def _service(self, provider=None) -> MetricsCollectorService:
        return MetricsCollectorService(
            provider=provider or StubMetricsProviderAdapter(),
            metrics_path=self.metrics_path,
            publish_records_path=self.publish_path,
            event_path=self.events_path,
        )

    def _event_types(self) -> list[str]:
        if not self.events_path.exists():
            return []
        with self.events_path.open("r", encoding="utf-8") as handle:
            return [json.loads(line).get("event_type") for line in handle if line.strip()]

    def test_coleta_normal(self) -> None:
        result = self._service().collect_for_publish(
            publish_id="pub_001",
            collected_at="2026-03-07T13:15:00Z",
        )
        self.assertEqual(result["status"], "WRITTEN")
        self.assertEqual(len(read_all_records(self.metrics_path)), 1)
        self.assertIn("METRICS/collection_completed", self._event_types())

    def test_idempotencia(self) -> None:
        service = self._service()
        first = service.collect_for_publish(
            publish_id="pub_001",
            collected_at="2026-03-07T13:15:00Z",
        )
        second = service.collect_for_publish(
            publish_id="pub_001",
            collected_at="2026-03-07T13:45:00Z",
        )
        self.assertEqual(first["status"], "WRITTEN")
        self.assertEqual(second["status"], "NOOP")
        self.assertEqual(len(read_all_records(self.metrics_path)), 1)

    def test_erro_de_api(self) -> None:
        service = self._service(provider=FlakyRateLimitProvider(fail_times=3))
        with self.assertRaises(MetricsProviderRateLimit):
            service.collect_for_publish(
                publish_id="pub_001",
                collected_at="2026-03-07T13:15:00Z",
            )
        self.assertIn("METRICS/api_rate_limited", self._event_types())
        self.assertIn("METRICS/collection_failed", self._event_types())

    def test_retry(self) -> None:
        provider = FlakyTimeoutProvider(fail_times=1)
        result = self._service(provider=provider).collect_for_publish(
            publish_id="pub_001",
            collected_at="2026-03-07T13:15:00Z",
        )
        self.assertEqual(provider.calls, 2)
        self.assertEqual(result["status"], "WRITTEN")

    def test_persistencia_append_only(self) -> None:
        service = self._service()
        service.collect_for_publish(publish_id="pub_001", collected_at="2026-03-07T13:15:00Z")
        service.collect_for_publish(publish_id="pub_001", collected_at="2026-03-07T14:15:00Z")
        self.assertEqual(len(read_all_records(self.metrics_path)), 2)

    def test_compatibilidade_com_publish_record(self) -> None:
        result = self._service().collect_for_publish(
            publish_id="pub_001",
            collected_at="2026-03-07T13:15:00Z",
        )
        record = result["record"]
        self.assertEqual(record["publish_id"], "pub_001")
        self.assertEqual(record["account_id"], "acc_001")
        self.assertEqual(record["video_id"], "vid_001")


if __name__ == "__main__":
    unittest.main()
