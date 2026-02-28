import logging

import pytest

from app.maestro.orchestrator import MaestroOrchestrator


@pytest.fixture
def anyio_backend():
    return "asyncio"


class _CollectorOk:
    def process(self, state, payload=None):
        next_state = dict(state)
        next_state["audio_local_path"] = "/tmp/sample.wav"
        next_state.setdefault("artifacts", {})
        next_state["artifacts"]["raw_video_minio_path"] = "videos/sample.mp4"
        return next_state


class _SegmenterOk:
    def process(self, state, payload=None):
        next_state = dict(state)
        next_state["segments"] = [
            {"segment_id": 0, "start_time": 0.0, "end_time": 1.0, "energy_score": 0.9}
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


class _SegmenterFail:
    def process(self, state, payload=None):
        raise RuntimeError("segmenter exploded")


class _TranscriberFail:
    def process(self, state, payload=None):
        raise RuntimeError("transcriber exploded")


@pytest.mark.anyio
async def test_maestro_orchestrator_runs_linear_pipeline_success(caplog):
    caplog.set_level(logging.INFO)
    orchestrator = MaestroOrchestrator(
        collector=_CollectorOk(),
        segmenter=_SegmenterOk(),
        transcriber=_TranscriberOk(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/video"})

    assert result.job.status == "done"
    assert result.job.step is None
    assert result.job.error is None
    assert result.job.duration_ms is not None
    assert set(result.job.step_durations_ms) == {"collector", "segmenter", "transcriber"}
    assert result.state["audio_local_path"] == "/tmp/sample.wav"
    assert result.state["segments"][0]["segment_id"] == 0
    assert result.state["transcriptions"][0]["text"] == "hello"
    assert result.state["job_id"] == result.job.id
    assert any(record.message == "maestro_step_started" for record in caplog.records)
    assert any(getattr(record, "job_id", None) == result.job.id for record in caplog.records)


@pytest.mark.anyio
async def test_maestro_orchestrator_marks_failed_when_segmenter_breaks():
    orchestrator = MaestroOrchestrator(
        collector=_CollectorOk(),
        segmenter=_SegmenterFail(),
        transcriber=_TranscriberOk(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/video"})

    assert result.job.status == "failed"
    assert result.job.step == "segmenter"
    assert result.job.error == "segmenter exploded"
    assert "transcriptions" not in result.state
    assert set(result.job.step_durations_ms) == {"collector"}


@pytest.mark.anyio
async def test_maestro_orchestrator_marks_failed_when_transcriber_breaks():
    orchestrator = MaestroOrchestrator(
        collector=_CollectorOk(),
        segmenter=_SegmenterOk(),
        transcriber=_TranscriberFail(),
    )

    result = await orchestrator.run({"input_ref": "https://example.com/video"})

    assert result.job.status == "failed"
    assert result.job.step == "transcriber"
    assert result.job.error == "transcriber exploded"
    assert "segments" in result.state
    assert "transcriptions" not in result.state
    assert set(result.job.step_durations_ms) == {"collector", "segmenter"}
