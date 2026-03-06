from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MaestroJobModel
from app.maestro.models import MaestroJob


async def create_running_job(
    db: AsyncSession,
    *,
    job_id: str,
    source_ref: str,
    demo_mode: bool,
) -> MaestroJobModel:
    """Cria o registro inicial de um job do Maestro com status running."""

    record = MaestroJobModel(
        job_id=job_id,
        source_ref=source_ref,
        status="running",
        step=None,
        error=None,
        started_at=datetime.utcnow(),
        finished_at=None,
        duration_ms=None,
        demo_mode=bool(demo_mode),
        step_durations_json={},
    )
    db.add(record)
    await db.flush()
    return record


async def update_job_success(
    db: AsyncSession,
    *,
    job_id: str,
    job: MaestroJob,
) -> MaestroJobModel:
    """Atualiza um job persistido para o estado final de sucesso."""

    record = await db.get(MaestroJobModel, job_id)
    if record is None:
        raise LookupError(f"MaestroJobNotFound: {job_id}")
    record.status = "done"
    record.step = job.step
    record.error = None
    record.finished_at = job.finished_at
    record.duration_ms = job.duration_ms
    record.step_durations_json = dict(job.step_durations_ms)
    await db.flush()
    return record


async def update_job_failure(
    db: AsyncSession,
    *,
    job_id: str,
    job: MaestroJob | None = None,
    step: str | None = None,
    error: str | None = None,
) -> MaestroJobModel:
    """Atualiza um job persistido para failed, com step e erro finais."""

    record = await db.get(MaestroJobModel, job_id)
    if record is None:
        raise LookupError(f"MaestroJobNotFound: {job_id}")
    record.status = "failed"
    record.step = job.step if job is not None else step
    record.error = job.error if job is not None else error
    record.finished_at = job.finished_at if job is not None else datetime.utcnow()
    record.duration_ms = job.duration_ms if job is not None else None
    record.step_durations_json = dict(job.step_durations_ms) if job is not None else {}
    await db.flush()
    return record


async def get_job_by_id(db: AsyncSession, job_id: str) -> MaestroJobModel | None:
    """Busca um job persistido pelo identificador externo do Maestro."""

    return await db.get(MaestroJobModel, job_id)
