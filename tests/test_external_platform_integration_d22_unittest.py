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

from app.data.publish_records.store_jsonl import read_all_records as read_publish_records
from app.data.publish_records.writer import write_publish_record
from app.data.video_metrics.store_jsonl import read_all_records as read_video_metrics
from app.data.video_metrics.writer import VideoMetricsConflictError, write_video_metrics
from app.integrations.base_client import (
    ProviderInvalidPayloadError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.integrations.providers.tiktok.adapter import TikTokNormalizedAdapter
from app.integrations.providers.tiktok.client import TikTokPlatformClient
from app.integrations.service import ExternalPlatformIntegrationService, ProviderIntegrationDeps


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def __call__(self, endpoint: str, payload: dict) -> dict:
        self.calls += 1
        current = self.responses.pop(0)
        if isinstance(current, Exception):
            raise current
        return dict(current)


class ExternalPlatformIntegrationD22Tests(unittest.TestCase):
    def _service(self, responses, *, events=None, publish_path=None, metrics_path=None, sleep_calls=None):
        transport = FakeTransport(responses)
        captured_sleep = sleep_calls if sleep_calls is not None else []
        client = TikTokPlatformClient(
            transport=transport,
            sleep_fn=lambda seconds: captured_sleep.append(seconds),
        )
        return (
            ExternalPlatformIntegrationService(
                ProviderIntegrationDeps(
                    client=client,
                    adapter=TikTokNormalizedAdapter(),
                    event_sink=(events.append if events is not None else None),
                    publish_record_writer=(
                        (lambda record: write_publish_record(record, path=publish_path))
                        if publish_path is not None
                        else write_publish_record
                    ),
                    video_metrics_writer=(
                        (lambda record: write_video_metrics(record, path=metrics_path))
                        if metrics_path is not None
                        else write_video_metrics
                    ),
                )
            ),
            transport,
            captured_sleep,
        )

    def test_resposta_valida_gera_video_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            metrics_path = Path(tmp_dir) / "video_metrics.jsonl"
            service, _, _ = self._service(
                [
                    {
                        "status_code": 200,
                        "request_id": "req_1",
                        "external_video_id": "tt_001",
                        "captured_at": "2026-03-06T10:00:00Z",
                        "views": 123,
                        "retention_3s": 0.55,
                        "completion_rate": 0.31,
                        "likes": 10,
                        "follows": 2,
                        "rpm": 1.2,
                    }
                ],
                metrics_path=metrics_path,
            )

            result = service.ingest_video_metrics(
                account_id="acc_001",
                external_video_id="tt_001",
                captured_window_id="w_2026-03-03T00:00:00Z_2026-03-06T00:00:00Z",
            )

            self.assertEqual(result.status, "WRITTEN")
            rows = read_video_metrics(metrics_path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["provider"], "tiktok")

    def test_retry_em_timeout_transitorio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            metrics_path = Path(tmp_dir) / "video_metrics.jsonl"
            service, transport, sleeps = self._service(
                [
                    TimeoutError("timeout"),
                    {
                        "status_code": 200,
                        "request_id": "req_2",
                        "external_video_id": "tt_002",
                        "captured_at": "2026-03-06T10:00:00Z",
                        "views": 200,
                    },
                ],
                metrics_path=metrics_path,
            )

            result = service.ingest_video_metrics(
                account_id="acc_001",
                external_video_id="tt_002",
                captured_window_id="w_2026-03-03T00:00:00Z_2026-03-06T00:00:00Z",
            )

            self.assertEqual(result.retry_count, 1)
            self.assertEqual(transport.calls, 2)
            self.assertEqual(sleeps, [0.05])

    def test_rate_limit_respeita_backoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            metrics_path = Path(tmp_dir) / "video_metrics.jsonl"
            service, transport, sleeps = self._service(
                [
                    {"status_code": 429},
                    {
                        "status_code": 200,
                        "request_id": "req_3",
                        "external_video_id": "tt_003",
                        "captured_at": "2026-03-06T10:00:00Z",
                        "views": 210,
                    },
                ],
                metrics_path=metrics_path,
            )

            service.ingest_video_metrics(
                account_id="acc_001",
                external_video_id="tt_003",
                captured_window_id="w_2026-03-03T00:00:00Z_2026-03-06T00:00:00Z",
            )

            self.assertEqual(transport.calls, 2)
            self.assertEqual(sleeps, [0.05])

    def test_resposta_duplicada_vira_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            metrics_path = Path(tmp_dir) / "video_metrics.jsonl"
            service, _, _ = self._service(
                [
                    {
                        "status_code": 200,
                        "request_id": "req_4a",
                        "external_video_id": "tt_004",
                        "captured_at": "2026-03-06T10:00:00Z",
                        "views": 220,
                    },
                    {
                        "status_code": 200,
                        "request_id": "req_4b",
                        "external_video_id": "tt_004",
                        "captured_at": "2026-03-06T10:00:00Z",
                        "views": 220,
                    },
                ],
                metrics_path=metrics_path,
            )

            service.ingest_video_metrics(
                account_id="acc_001",
                external_video_id="tt_004",
                captured_window_id="w_2026-03-03T00:00:00Z_2026-03-06T00:00:00Z",
            )
            service.ingest_video_metrics(
                account_id="acc_001",
                external_video_id="tt_004",
                captured_window_id="w_2026-03-03T00:00:00Z_2026-03-06T00:00:00Z",
            )

            rows = read_video_metrics(metrics_path)
            self.assertEqual(len(rows), 1)

    def test_payload_externo_invalido_falha_explicita(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            metrics_path = Path(tmp_dir) / "video_metrics.jsonl"
            service, _, _ = self._service(
                [{"status_code": 200, "request_id": "req_5", "external_video_id": "tt_005"}],
                metrics_path=metrics_path,
            )

            with self.assertRaises(ProviderInvalidPayloadError):
                service.ingest_video_metrics(
                    account_id="acc_001",
                    external_video_id="tt_005",
                    captured_window_id="w_2026-03-03T00:00:00Z_2026-03-06T00:00:00Z",
                )

    def test_observabilidade_registra_provider_call_e_publish_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            publish_path = Path(tmp_dir) / "publish_records.jsonl"
            events: list[dict] = []
            service, _, _ = self._service(
                [
                    {
                        "status_code": 200,
                        "request_id": "req_6",
                        "external_post_id": "pub_ext_001",
                        "job_id": "job_001",
                        "video_id": "vid_001",
                        "published_at": "2026-03-06T12:00:00Z",
                        "status": "posted",
                        "publish_mode": "replay",
                    }
                ],
                publish_path=publish_path,
                events=events,
            )

            result = service.ingest_publish_record(
                account_id="acc_001",
                external_post_id="pub_ext_001",
            )

            self.assertEqual(result.status, "WRITTEN")
            records = read_publish_records(publish_path)
            self.assertEqual(len(records), 1)
            self.assertTrue(any(event.get("event_type") == "INTEGRATION/provider_call" for event in events))


if __name__ == "__main__":
    unittest.main()
