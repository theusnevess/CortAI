from __future__ import annotations

from app.observability.webhook_metrics import WebhookMetrics


def setup_function() -> None:
    WebhookMetrics._reset_for_tests()


def test_snapshot_initial_is_zeroed() -> None:
    snapshot = WebhookMetrics.snapshot()
    assert snapshot["sent"] == 0
    assert snapshot["success"] == 0
    assert snapshot["error"] == 0
    assert snapshot["error_rate"] == 0.0
    assert snapshot["p95_latency_ms"] is None
    assert snapshot["last_error_status"] is None
    assert snapshot["last_error_ts"] is None


def test_records_success_and_error_rate() -> None:
    WebhookMetrics.record_attempt()
    WebhookMetrics.record_success(latency_ms=10, status=200)

    WebhookMetrics.record_attempt()
    WebhookMetrics.record_error(latency_ms=20, status=500)

    snapshot = WebhookMetrics.snapshot()
    assert snapshot["sent"] == 2
    assert snapshot["success"] == 1
    assert snapshot["error"] == 1
    assert snapshot["error_rate"] == 0.5
    assert snapshot["p95_latency_ms"] is not None
    assert snapshot["last_error_status"] == 500
    assert isinstance(snapshot["last_error_ts"], str)


def test_p95_nearest_rank_is_deterministic() -> None:
    for latency_ms in range(20):
        WebhookMetrics.record_attempt()
        WebhookMetrics.record_success(latency_ms=latency_ms, status=200)

    snapshot = WebhookMetrics.snapshot()
    assert snapshot["sent"] == 20
    assert snapshot["success"] == 20
    assert snapshot["error"] == 0
    assert snapshot["error_rate"] == 0.0
    assert snapshot["p95_latency_ms"] == 18


def test_error_with_status_none_sets_last_error_fields() -> None:
    WebhookMetrics.record_attempt()
    WebhookMetrics.record_error(latency_ms=7, status=None)

    snapshot = WebhookMetrics.snapshot()
    assert snapshot["sent"] == 1
    assert snapshot["error"] == 1
    assert snapshot["last_error_status"] is None
    assert isinstance(snapshot["last_error_ts"], str)
