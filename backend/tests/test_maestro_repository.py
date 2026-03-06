from datetime import datetime

import pytest

from app.maestro.models import MaestroJob
from app.maestro.repository import (
    create_running_job,
    get_job_by_id,
    update_job_failure,
    update_job_success,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


class _FakeAsyncSession:
    def __init__(self):
        self.records = {}

    def add(self, record):
        self.records[record.job_id] = record

    async def flush(self):
        return None

    async def get(self, model, job_id):
        return self.records.get(job_id)


@pytest.mark.anyio
async def test_maestro_repository_create_and_get_job():
    db = _FakeAsyncSession()

    created = await create_running_job(
        db,
        job_id="job-1",
        source_ref="https://example.com/video",
        demo_mode=True,
    )
    fetched = await get_job_by_id(db, "job-1")

    assert created.job_id == "job-1"
    assert created.status == "running"
    assert created.demo_mode is True
    assert fetched is created


@pytest.mark.anyio
async def test_maestro_repository_updates_success_and_failure():
    db = _FakeAsyncSession()
    await create_running_job(
        db,
        job_id="job-1",
        source_ref="https://example.com/video",
        demo_mode=False,
    )

    success_job = MaestroJob(
        id="job-1",
        input_ref="https://example.com/video",
        status="done",
        step=None,
        error=None,
        started_at=datetime(2026, 2, 28, 1, 0, 0),
        finished_at=datetime(2026, 2, 28, 1, 0, 1),
        duration_ms=100,
        step_durations_ms={"collector": 5},
    )
    updated = await update_job_success(db, job_id="job-1", job=success_job)
    assert updated.status == "done"
    assert updated.duration_ms == 100
    assert updated.step_durations_json == {"collector": 5}

    failure_job = MaestroJob(
        id="job-1",
        input_ref="https://example.com/video",
        status="failed",
        step="segmenter",
        error="segmenter exploded",
        started_at=datetime(2026, 2, 28, 1, 0, 0),
        finished_at=datetime(2026, 2, 28, 1, 0, 2),
        duration_ms=120,
        step_durations_ms={"collector": 5, "audio_extractor": 10},
    )
    failed = await update_job_failure(db, job_id="job-1", job=failure_job)
    assert failed.status == "failed"
    assert failed.step == "segmenter"
    assert failed.error == "segmenter exploded"
    assert failed.step_durations_json == {"collector": 5, "audio_extractor": 10}
