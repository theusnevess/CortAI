from __future__ import annotations

import asyncio
import sys
import types
from pathlib import Path

import pytest
from fastapi import HTTPException

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agents.collector import service as collector_service
from app.security.ssrf import SSRFValidationError, validate_external_fetch_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/video.mp4",
        "http://localhost/video.mp4",
        "http://0.0.0.0/video.mp4",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.1/video.mp4",
        "http://172.16.0.1/video.mp4",
        "http://192.168.0.1/video.mp4",
        "http://[::1]/video.mp4",
        "file:///etc/passwd",
        "gopher://example.com",
        "http://user:pass@example.com/video.mp4",
    ],
)
def test_ssrf_policy_rejects_unsafe_urls(url: str):
    with pytest.raises(SSRFValidationError):
        validate_external_fetch_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/video.mp4",
        "https://www.youtube.com/watch?v=example",
    ],
)
def test_ssrf_policy_allows_public_candidates_without_fetch(url: str):
    result = validate_external_fetch_url(url)

    assert result.normalized_url == url


def test_collector_rejects_unsafe_url_before_downloader(monkeypatch):
    calls = []

    class FakeYoutubeDL:
        def __init__(self, *args, **kwargs):
            calls.append(("init", args, kwargs))

    monkeypatch.setattr(collector_service.yt_dlp, "YoutubeDL", FakeYoutubeDL)

    result = collector_service.CollectorAgent().process("http://127.0.0.1/video.mp4")

    assert calls == []
    assert result["minio_path"] is None
    assert result["error"]["error_type"] == "invalid_input"


def test_collector_preserves_safe_pre_crossing_block_for_public_candidate(monkeypatch):
    calls = []

    class FakeYoutubeDL:
        def __init__(self, *args, **kwargs):
            calls.append(("init", args, kwargs))

    monkeypatch.setattr(collector_service.yt_dlp, "YoutubeDL", FakeYoutubeDL)

    result = collector_service.CollectorAgent().process("https://example.com/video.mp4")

    assert calls == []
    assert result["error"]["error_type"] == "external_boundary_blocked"
    assert result["error"]["cause"] == "CORTAI_EXTERNAL_BOUNDARY_BLOCKED_SAFE_PRE_CROSSING"


def test_videos_endpoint_rejects_unsafe_url_before_db_or_enqueue(monkeypatch):
    fake_tasks = types.ModuleType("app.tasks.collector_tasks")

    class FakeTask:
        calls = []

        def delay(self, *args, **kwargs):
            self.calls.append((args, kwargs))

    fake_task = FakeTask()
    fake_tasks.process_video_task = fake_task
    monkeypatch.setitem(sys.modules, "app.tasks.collector_tasks", fake_tasks)
    sys.modules.pop("app.api.v1.endpoints.videos", None)

    from app.api.v1.endpoints import videos

    class RejectDb:
        async def execute(self, *args, **kwargs):
            raise AssertionError("DB should not be touched for SSRF-rejected URLs")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            videos.create_video(
                videos.VideoCreateRequest(url="http://169.254.169.254/latest/meta-data"),
                db=RejectDb(),
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"] == "unsafe_source_url"
    assert fake_task.calls == []
