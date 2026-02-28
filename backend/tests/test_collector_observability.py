from __future__ import annotations

from app.agents.adapters.collector_adapter import CollectorAdapter


class _CollectorSuccess:
    def process(self, url: str) -> dict:
        return {
            "title": "audio-1s",
            "duration": 1.0,
            "minio_path": "videos-raw/smoke/very-long-audio-object-name-1234567890abcdef.wav",
            "source_type": "audio",
            "metadata": {"original_url": url},
            "error": None,
        }


class _CollectorFailure:
    def process(self, url: str) -> dict:
        return {
            "title": None,
            "duration": None,
            "minio_path": None,
            "source_type": None,
            "metadata": {"original_url": url},
            "error": {
                "error_type": "http_4xx",
                "message": "Origem respondeu HTTP 404.",
                "http_status": 404,
                "retryable": False,
                "cause": "HTTP Error 404",
            },
        }


def test_collector_run_emits_success_event_with_sanitized_payload(monkeypatch):
    emitted: list[tuple[str, str, dict]] = []

    monkeypatch.setattr(
        "app.agents.adapters.collector_adapter.CollectorAgent",
        lambda: _CollectorSuccess(),
    )
    monkeypatch.setattr(
        "app.agents.adapters.collector_adapter.collector_observability_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "app.agents.adapters.collector_adapter.persist_collector_run_observation",
        lambda *, process_id, source_outcome_id, facts: emitted.append(
            (process_id, source_outcome_id, facts)
        ),
    )

    state = {"job_id": "job-123"}
    payload = {"url": "https://example.com/file.wav?token=secret&foo=bar"}

    result = CollectorAdapter().process(state, payload=payload)

    assert result["artifacts"]["raw_video_minio_path"] == "videos-raw/smoke/very-long-audio-object-name-1234567890abcdef.wav"
    assert len(emitted) == 1
    process_id, source_outcome_id, facts = emitted[0]
    assert process_id == "job-123"
    assert source_outcome_id == "job-123"
    assert facts["event_type"] == "collector_run"
    assert facts["status"] == "success"
    assert facts["error_type"] is None
    assert facts["source_type"] == "audio"
    assert facts["minio_bucket"] == "videos-raw"
    assert facts["minio_key_prefix"] == "smoke/very-long-audio-object-nam"
    assert facts["minio_key_prefix"] != "smoke/very-long-audio-object-name-1234567890abcdef.wav"
    assert "token=secret" not in facts["source_ref"]
    assert facts["source_ref"].endswith("foo=bar")


def test_collector_run_sanitizes_multiple_sensitive_query_keys():
    from app.agents.collector.observability import sanitize_source_ref

    source_ref = "https://example.com/file.wav?sig=abc123&token=secret&foo=bar&access_token=hidden"

    sanitized = sanitize_source_ref(source_ref)

    assert sanitized == "https://example.com/file.wav?foo=bar"


def test_collector_run_emits_failure_event_and_raises_typed_failure(monkeypatch):
    emitted: list[dict] = []

    monkeypatch.setattr(
        "app.agents.adapters.collector_adapter.CollectorAgent",
        lambda: _CollectorFailure(),
    )
    monkeypatch.setattr(
        "app.agents.adapters.collector_adapter.collector_observability_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "app.agents.adapters.collector_adapter.persist_collector_run_observation",
        lambda *, process_id, source_outcome_id, facts: emitted.append(facts),
    )

    state = {"job_id": "job-err"}
    payload = {"url": "https://example.com/video.mp4"}

    try:
        CollectorAdapter().process(state, payload=payload)
        raise AssertionError("Expected CollectorAdapter to raise on typed collector error")
    except OSError as exc:
        assert "CollectorFailed:http_4xx" in str(exc)

    assert len(emitted) == 1
    facts = emitted[0]
    assert facts["status"] == "failed"
    assert facts["error_type"] == "http_4xx"
    assert facts["http_status"] == 404
    assert facts["retryable"] is False
    assert facts["minio_bucket"] is None
    assert facts["minio_key_prefix"] is None


def test_collector_run_observability_can_be_disabled(monkeypatch):
    emitted: list[dict] = []

    monkeypatch.setattr(
        "app.agents.adapters.collector_adapter.CollectorAgent",
        lambda: _CollectorSuccess(),
    )
    monkeypatch.setattr(
        "app.agents.adapters.collector_adapter.collector_observability_enabled",
        lambda: False,
    )
    monkeypatch.setattr(
        "app.agents.adapters.collector_adapter.persist_collector_run_observation",
        lambda *, process_id, source_outcome_id, facts: emitted.append(facts),
    )

    state = {"job_id": "job-noobs"}
    payload = {"url": "https://example.com/file.wav"}

    CollectorAdapter().process(state, payload=payload)

    assert emitted == []
