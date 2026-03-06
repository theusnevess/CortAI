import logging

import pytest

from app.maestro.orchestrator import MaestroOrchestrator


@pytest.fixture
def anyio_backend():
    return "asyncio"


class _CollectorVideoOk:
    def process(self, state, payload=None):
        next_state = dict(state)
        next_state.setdefault("artifacts", {})
        next_state["raw_video_minio_path"] = "videos/sample.mp4"
        next_state["artifacts"]["raw_video_minio_path"] = "videos/sample.mp4"
        next_state["artifacts"]["raw_video_ready"] = True
        return next_state


class _CollectorAudioReadyOk:
    def process(self, state, payload=None):
        next_state = dict(state)
        next_state["audio_local_path"] = "/tmp/sample.wav"
        next_state["audio_minio_path"] = "audio-raw/sample.wav"
        next_state.setdefault("artifacts", {})
        next_state["artifacts"]["audio_ready"] = True
        next_state["artifacts"]["audio_local_path"] = next_state["audio_local_path"]
        next_state["artifacts"]["audio_minio_path"] = next_state["audio_minio_path"]
        return next_state


class _AudioExtractorOk:
    def __init__(self):
        self.calls = 0

    def process(self, state, payload=None):
        self.calls += 1
        next_state = dict(state)
        next_state["audio_local_path"] = "/tmp/sample.wav"
        next_state["audio_minio_path"] = "audio-raw/sample.wav"
        next_state.setdefault("artifacts", {})
        next_state["artifacts"]["audio_ready"] = True
        next_state["artifacts"]["audio_local_path"] = next_state["audio_local_path"]
        next_state["artifacts"]["audio_minio_path"] = next_state["audio_minio_path"]
        return next_state


class _AudioExtractorFail:
    def process(self, state, payload=None):
        raise RuntimeError("audio extractor exploded")


class _SegmenterOk:
    def process(self, state, payload=None):
        next_state = dict(state)
        next_state["segments"] = [
            {
                "segment_id": 0,
                "start_time": 0.0,
                "end_time": 1.0,
                "start_ms": 0,
                "end_ms": 1000,
                "energy_score": 0.9,
            }
        ]
        next_state.setdefault("artifacts", {})
        next_state["artifacts"]["segments_ready"] = True
        return next_state


class _TranscriberOk:
    def process(self, state, payload=None):
        next_state = dict(state)
        next_state["transcriptions"] = [
            {"segment_id": 0, "start_time": 0.0, "end_time": 1.0, "text": "hello"}
        ]
        next_state.setdefault("artifacts", {})
        next_state["artifacts"]["transcriptions_ready"] = True
        return next_state


class _TranscriberFail:
    def process(self, state, payload=None):
        raise RuntimeError("transcriber exploded")


@pytest.mark.anyio
async def test_maestro_orchestrator_runs_linear_pipeline_with_audio_extractor(caplog):
    caplog.set_level(logging.INFO)
    audio_extractor = _AudioExtractorOk()
    orchestrator = MaestroOrchestrator(
        collector=_CollectorVideoOk(),
        audio_extractor=audio_extractor,
        segmenter=_SegmenterOk(),
        transcriber=_TranscriberOk(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/video"})

    assert result.job.status == "done"
    assert result.job.step is None
    assert result.job.error is None
    assert result.job.duration_ms is not None
    assert set(result.job.step_durations_ms) == {
        "collector",
        "audio_extractor",
        "segmenter",
        "transcriber",
    }
    assert audio_extractor.calls == 1
    assert result.state["audio_local_path"] == "/tmp/sample.wav"
    assert result.state["audio_minio_path"] == "audio-raw/sample.wav"
    assert result.state["segments"][0]["segment_id"] == 0
    assert result.state["transcriptions"][0]["text"] == "hello"
    assert result.state["job_id"] == result.job.id
    assert any(record.message == "maestro_step_started" for record in caplog.records)
    assert any(getattr(record, "job_id", None) == result.job.id for record in caplog.records)


@pytest.mark.anyio
async def test_maestro_orchestrator_skips_audio_extractor_when_audio_is_already_ready():
    audio_extractor = _AudioExtractorOk()
    orchestrator = MaestroOrchestrator(
        collector=_CollectorAudioReadyOk(),
        audio_extractor=audio_extractor,
        segmenter=_SegmenterOk(),
        transcriber=_TranscriberOk(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/audio"})

    assert result.job.status == "done"
    assert set(result.job.step_durations_ms) == {"collector", "segmenter", "transcriber"}
    assert audio_extractor.calls == 0
    assert result.state["audio_local_path"] == "/tmp/sample.wav"
    assert result.state["audio_minio_path"] == "audio-raw/sample.wav"


@pytest.mark.anyio
async def test_maestro_orchestrator_materializes_local_audio_from_audio_minio_path_input():
    audio_extractor = _AudioExtractorOk()
    orchestrator = MaestroOrchestrator(
        collector=_CollectorVideoOk(),
        audio_extractor=audio_extractor,
        segmenter=_SegmenterOk(),
        transcriber=_TranscriberOk(),
    )

    result = await orchestrator.run(
        {
            "input_ref": "https://example.com/video",
            "audio_minio_path": "audio-raw/from-input.wav",
        }
    )

    assert result.job.status == "done"
    assert audio_extractor.calls == 1
    assert result.state["audio_local_path"] == "/tmp/sample.wav"
    assert result.state["audio_minio_path"] == "audio-raw/sample.wav"


@pytest.mark.anyio
async def test_maestro_orchestrator_marks_failed_when_audio_extractor_breaks():
    orchestrator = MaestroOrchestrator(
        collector=_CollectorVideoOk(),
        audio_extractor=_AudioExtractorFail(),
        segmenter=_SegmenterOk(),
        transcriber=_TranscriberOk(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/video"})

    assert result.job.status == "failed"
    assert result.job.step == "audio_extractor"
    assert result.job.error == "audio extractor exploded"
    assert "segments" not in result.state
    assert set(result.job.step_durations_ms) == {"collector"}


@pytest.mark.anyio
async def test_maestro_orchestrator_marks_failed_when_transcriber_breaks():
    orchestrator = MaestroOrchestrator(
        collector=_CollectorAudioReadyOk(),
        audio_extractor=_AudioExtractorOk(),
        segmenter=_SegmenterOk(),
        transcriber=_TranscriberFail(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/audio"})

    assert result.job.status == "failed"
    assert result.job.step == "transcriber"
    assert result.job.error == "transcriber exploded"
    assert "segments" in result.state
    assert "transcriptions" not in result.state
    assert set(result.job.step_durations_ms) == {"collector", "segmenter"}


@pytest.mark.anyio
async def test_maestro_contract_hardening_fails_when_segments_missing():
    class _SegmenterNoSegments:
        def process(self, state, payload=None):
            next_state = dict(state)
            next_state.setdefault("artifacts", {})
            next_state["artifacts"]["segments_ready"] = False
            return next_state

    orchestrator = MaestroOrchestrator(
        collector=_CollectorVideoOk(),
        audio_extractor=_AudioExtractorOk(),
        segmenter=_SegmenterNoSegments(),
        transcriber=_TranscriberOk(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/video"})

    assert result.job.status == "failed"
    assert result.job.step == "segmenter"
    assert "ContractViolation: segmenter must provide non-empty segments" in (
        result.job.error or ""
    )


@pytest.mark.anyio
async def test_maestro_contract_hardening_fails_when_segments_invalid():
    class _SegmenterBadSegments:
        def process(self, state, payload=None):
            next_state = dict(state)
            next_state.setdefault("artifacts", {})
            next_state["segments"] = [{"start_ms": 1000, "end_ms": 1000}]
            next_state["artifacts"]["segments_ready"] = True
            return next_state

    orchestrator = MaestroOrchestrator(
        collector=_CollectorVideoOk(),
        audio_extractor=_AudioExtractorOk(),
        segmenter=_SegmenterBadSegments(),
        transcriber=_TranscriberOk(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/video"})

    assert result.job.status == "failed"
    assert result.job.step == "segmenter"
    assert "ContractViolation: segment.end_ms must be int>start_ms" in (result.job.error or "")


@pytest.mark.anyio
async def test_maestro_contract_hardening_fails_when_transcriptions_missing():
    class _TranscriberNoTranscriptions:
        def process(self, state, payload=None):
            next_state = dict(state)
            next_state.setdefault("artifacts", {})
            return next_state

    orchestrator = MaestroOrchestrator(
        collector=_CollectorAudioReadyOk(),
        audio_extractor=_AudioExtractorOk(),
        segmenter=_SegmenterOk(),
        transcriber=_TranscriberNoTranscriptions(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/audio"})

    assert result.job.status == "failed"
    assert result.job.step == "transcriber"
    assert "ContractViolation: transcriber must provide transcriptions as list" in (
        result.job.error or ""
    )


@pytest.mark.anyio
async def test_maestro_contract_hardening_fails_when_transcriptions_empty():
    class _TranscriberEmptyTranscriptions:
        def process(self, state, payload=None):
            next_state = dict(state)
            next_state["transcriptions"] = []
            next_state.setdefault("artifacts", {})
            return next_state

    orchestrator = MaestroOrchestrator(
        collector=_CollectorAudioReadyOk(),
        audio_extractor=_AudioExtractorOk(),
        segmenter=_SegmenterOk(),
        transcriber=_TranscriberEmptyTranscriptions(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/audio"})

    assert result.job.status == "failed"
    assert result.job.step == "transcriber"
    assert "ContractViolation: transcriber transcriptions must be non-empty list" in (
        result.job.error or ""
    )


@pytest.mark.anyio
async def test_maestro_contract_hardening_fails_when_transcription_item_invalid():
    class _TranscriberInvalidItem:
        def process(self, state, payload=None):
            next_state = dict(state)
            next_state["transcriptions"] = [{}]
            next_state.setdefault("artifacts", {})
            return next_state

    orchestrator = MaestroOrchestrator(
        collector=_CollectorAudioReadyOk(),
        audio_extractor=_AudioExtractorOk(),
        segmenter=_SegmenterOk(),
        transcriber=_TranscriberInvalidItem(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/audio"})

    assert result.job.status == "failed"
    assert result.job.step == "transcriber"
    assert (
        "ContractViolation: transcriber transcriptions[0].text must be non-empty string"
        in (result.job.error or "")
    )


@pytest.mark.anyio
async def test_maestro_contract_hardening_fails_when_transcriber_optional_invalid():
    class _TranscriberInvalidOptional:
        def process(self, state, payload=None):
            next_state = dict(state)
            next_state["transcriptions"] = [{"text": "ok"}]
            next_state["language"] = 123
            next_state.setdefault("artifacts", {})
            return next_state

    orchestrator = MaestroOrchestrator(
        collector=_CollectorAudioReadyOk(),
        audio_extractor=_AudioExtractorOk(),
        segmenter=_SegmenterOk(),
        transcriber=_TranscriberInvalidOptional(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/audio"})

    assert result.job.status == "failed"
    assert result.job.step == "transcriber"
    assert "ContractViolation: transcriber language must be non-empty string when present" in (
        result.job.error or ""
    )
