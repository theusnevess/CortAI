from __future__ import annotations

import os

import pytest
import requests

from app.agents.collector.service import CollectorAgent
from app.agents.collector.utils import parse_minio_path
from app.services.storage import MinioService


KNOWN_GOOD_URL = os.getenv("COLLECTOR_KNOWN_GOOD_URL")
KNOWN_BAD_URL = os.getenv(
    "COLLECTOR_KNOWN_BAD_URL",
    "https://example.com/video.mp4",
)


def _resolve_good_url() -> str:
    if KNOWN_GOOD_URL:
        return KNOWN_GOOD_URL

    candidates = (
        "http://localhost:8001/smoke-assets/audio_1s.wav",
        "http://cortai_edge:8080/smoke-assets/audio_1s.wav",
    )
    for candidate in candidates:
        try:
            response = requests.get(candidate, timeout=5)
        except Exception:
            continue
        if response.status_code == 200:
            return candidate
    pytest.skip("Smoke asset indisponivel nos endpoints conhecidos")


def _ensure_smoke_stack() -> str:
    good_url = _resolve_good_url()

    try:
        MinioService().client.list_buckets()
    except Exception as exc:
        pytest.skip(f"MinIO indisponivel para smoke do coletor: {exc}")

    return good_url


def test_collector_smoke_known_good_url_persists_object():
    good_url = _ensure_smoke_stack()

    result = CollectorAgent().process(good_url)

    assert result["error"] is None
    assert result["source_type"] in ("audio", "video")
    assert result.get("minio_path")
    assert result["metadata"]["original_url"] == good_url

    parsed = parse_minio_path(result["minio_path"])
    stat = MinioService().client.stat_object(parsed.bucket, parsed.key)
    assert stat.size > 0


def test_collector_smoke_known_bad_url_classifies_http_4xx():
    _ensure_smoke_stack()

    result = CollectorAgent().process(KNOWN_BAD_URL)

    assert result.get("minio_path") in (None, "")
    error = result.get("error")
    assert error is not None
    assert error["error_type"] == "http_4xx"
    assert error["http_status"] == 404
    assert error["message"]
    assert result["metadata"]["original_url"] == KNOWN_BAD_URL


def test_collector_invalid_input_classifies_invalid_input():
    result = CollectorAgent().process("")

    assert result.get("minio_path") is None
    error = result.get("error")
    assert error is not None
    assert error["error_type"] == "invalid_input"
    assert error["message"]
