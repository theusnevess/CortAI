from __future__ import annotations

from pathlib import Path

import pytest

from app.agents.adapters.audio_extractor_adapter import AudioExtractorAdapter


def _base_state() -> dict:
    return {
        "job_id": "job-audio-1",
        "input_ref": "http://localhost:8001/smoke-assets/video_1s.mp4",
        "artifacts": {},
    }


def test_audio_extractor_raw_video_minio_path_returns_complete_state(monkeypatch, tmp_path):
    calls: dict[str, list] = {"download": [], "upload": [], "ensure": []}

    class _FakeMinioService:
        def __init__(self):
            self.bucket_name = "videos-raw"

        def _ensure_bucket_exists(self):
            calls["ensure"].append(self.bucket_name)

        def download_file(self, object_name, file_path):
            calls["download"].append((self.bucket_name, object_name, file_path))
            Path(file_path).write_bytes(b"fake-video")
            return file_path

        def upload_file(self, file_path, object_name):
            calls["upload"].append((self.bucket_name, file_path, object_name))
            return f"{self.bucket_name}/{object_name}"

    def _fake_extract(self, local_video_path):
        output = tmp_path / "output.wav"
        output.write_bytes(b"RIFFfakewav")
        return str(output)

    monkeypatch.setattr("app.agents.adapters.audio_extractor_adapter.TMP_DIR", tmp_path)
    monkeypatch.setattr("app.agents.adapters.audio_extractor_adapter.MinioService", _FakeMinioService)
    monkeypatch.setattr(AudioExtractorAdapter, "_extract_wav", _fake_extract)

    adapter = AudioExtractorAdapter()
    state = _base_state()
    payload = {"raw_video_minio_path": "videos-raw/sample/video_1s.mp4"}

    result = adapter.process(state, payload=payload)

    assert result["job_id"] == state["job_id"]
    assert result["input_ref"] == state["input_ref"]
    assert result["source_type"] == "audio"
    assert result["audio_local_path"]
    assert result["audio_minio_path"].startswith("audio-raw/")
    assert result["raw_video_minio_path"] == payload["raw_video_minio_path"]
    assert result["artifacts"]["raw_video_minio_path"] == payload["raw_video_minio_path"]
    assert result["artifacts"]["audio_local_path"] == result["audio_local_path"]
    assert result["artifacts"]["audio_minio_path"] == result["audio_minio_path"]
    assert calls["download"] == [("videos-raw", "sample/video_1s.mp4", calls["download"][0][2])]
    assert calls["upload"][0][0] == "audio-raw"
    assert "audio-raw" in calls["ensure"]


def test_audio_extractor_audio_minio_path_materializes_local_without_ffmpeg(monkeypatch, tmp_path):
    calls: dict[str, list] = {"download": [], "upload": [], "ensure": [], "ffmpeg": []}

    class _FakeMinioService:
        def __init__(self):
            self.bucket_name = "videos-raw"

        def _ensure_bucket_exists(self):
            calls["ensure"].append(self.bucket_name)

        def download_file(self, object_name, file_path):
            calls["download"].append((self.bucket_name, object_name, file_path))
            Path(file_path).write_bytes(b"RIFFfakewav")
            return file_path

        def upload_file(self, file_path, object_name):
            calls["upload"].append((self.bucket_name, file_path, object_name))
            return f"{self.bucket_name}/{object_name}"

    def _boom_ffmpeg(*args, **kwargs):
        calls["ffmpeg"].append((args, kwargs))
        raise AssertionError("ffmpeg nao deveria ser chamado no modo audio_minio_path")

    monkeypatch.setattr("app.agents.adapters.audio_extractor_adapter.TMP_DIR", tmp_path)
    monkeypatch.setattr("app.agents.adapters.audio_extractor_adapter.MinioService", _FakeMinioService)
    monkeypatch.setattr(
        "app.agents.adapters.audio_extractor_adapter.subprocess.run",
        _boom_ffmpeg,
    )

    adapter = AudioExtractorAdapter()
    state = _base_state()
    payload = {"audio_minio_path": "audio-raw/sample/audio_1s.wav"}

    result = adapter.process(state, payload=payload)

    assert result["job_id"] == state["job_id"]
    assert result["input_ref"] == state["input_ref"]
    assert result["source_type"] == "audio"
    assert result["audio_local_path"]
    assert result["audio_minio_path"] == payload["audio_minio_path"]
    assert result["artifacts"]["audio_local_path"] == result["audio_local_path"]
    assert result["artifacts"]["audio_minio_path"] == payload["audio_minio_path"]
    assert "raw_video_minio_path" not in result
    assert calls["download"] == [("audio-raw", "sample/audio_1s.wav", calls["download"][0][2])]
    assert calls["upload"] == []
    assert calls["ffmpeg"] == []


@pytest.mark.parametrize(
    ("payload", "expected_message"),
    [
        ({}, "ContractViolation"),
        (
            {
                "raw_video_minio_path": "videos-raw/sample/video_1s.mp4",
                "audio_minio_path": "audio-raw/sample/audio_1s.wav",
            },
            "ContractViolation",
        ),
    ],
)
def test_audio_extractor_invalid_contract_inputs_raise_value_error(payload, expected_message):
    adapter = AudioExtractorAdapter()

    with pytest.raises(ValueError) as exc:
        adapter.process(_base_state(), payload=payload)

    assert expected_message in str(exc.value)
