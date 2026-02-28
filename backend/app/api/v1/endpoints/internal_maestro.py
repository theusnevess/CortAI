from time import perf_counter_ns
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.metrics import _emit_metrics_endpoint_timing
from app.db.session import get_db
from app.maestro.orchestrator import MaestroOrchestrator
from app.maestro.repository import (
    create_running_job,
    get_job_by_id,
    update_job_failure,
    update_job_success,
)
from app.observability.runtime_health import should_include_internal_status

router = APIRouter(prefix="/internal", tags=["internal"])


class _DemoCollector:
    """Double local para smoke controlado do coletor."""

    def process(self, state: dict, payload: dict | None = None) -> dict:
        next_state = dict(state)
        next_state.setdefault("artifacts", {})
        next_state["artifacts"]["raw_video_minio_path"] = "demo/video.mp4"
        next_state["artifacts"]["raw_video_ready"] = True
        return next_state


class _DemoAudioExtractor:
    """Double local que fecha o contrato de audio_local_path no smoke interno."""

    def process(self, state: dict, payload: dict | None = None) -> dict:
        next_state = dict(state)
        next_state["audio_local_path"] = "/tmp/demo.wav"
        next_state.setdefault("artifacts", {})
        next_state["artifacts"]["audio_local_path"] = next_state["audio_local_path"]
        next_state["artifacts"]["audio_ready"] = True
        return next_state


class _DemoSegmenter:
    """Double local que produz uma segmentacao minima e deterministica."""

    def process(self, state: dict, payload: dict | None = None) -> dict:
        next_state = dict(state)
        next_state["segments"] = [
            {"segment_id": 0, "start_time": 0.0, "end_time": 1.0, "energy_score": 0.9}
        ]
        next_state.setdefault("artifacts", {})
        next_state["artifacts"]["segments_ready"] = True
        return next_state


class _DemoTranscriber:
    """Double local que finaliza o smoke com uma transcricao minima."""

    def process(self, state: dict, payload: dict | None = None) -> dict:
        next_state = dict(state)
        next_state["transcriptions"] = [
            {"segment_id": 0, "start_time": 0.0, "end_time": 1.0, "text": "demo transcript"}
        ]
        next_state.setdefault("artifacts", {})
        next_state["artifacts"]["transcriptions_ready"] = True
        return next_state


class MaestroRunRequest(BaseModel):
    """Payload minimo aceito para disparar uma execucao linear do Maestro."""

    source_ref: str
    job_id: str | None = None


def _build_demo_orchestrator() -> MaestroOrchestrator:
    """Monta um orquestrador deterministico para smoke interno do endpoint."""

    return MaestroOrchestrator(
        collector=_DemoCollector(),
        audio_extractor=_DemoAudioExtractor(),
        segmenter=_DemoSegmenter(),
        transcriber=_DemoTranscriber(),
    )


def _serialize_job(record) -> dict:
    """Normaliza a resposta publica do runtime interno do Maestro."""

    return {
        "job_id": record.job_id,
        "source_ref": record.source_ref,
        "status": record.status,
        "step": record.step,
        "error": record.error,
        "started_at": record.started_at.isoformat() + "Z" if record.started_at else None,
        "finished_at": record.finished_at.isoformat() + "Z" if record.finished_at else None,
        "duration_ms": record.duration_ms,
        "demo_mode": bool(record.demo_mode),
    }


@router.post("/maestro/run")
async def run_internal_maestro(
    request: Request,
    payload: MaestroRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Executa o pipeline linear do Maestro via endpoint interno restrito.

    Regras:
    - usa o mesmo gate interno do painel de observabilidade;
    - executa de forma sincrona no request;
    - nao expande superficie publica nem cria fila nova.
    """
    started_ns = perf_counter_ns()
    status_code = 500
    demo_mode = False
    persisted_job_id: str | None = None
    try:
        if not should_include_internal_status(request):
            status_code = 404
            raise HTTPException(status_code=404, detail="Not Found")

        demo_mode = str(request.query_params.get("demo", "")).strip() == "1"
        source_ref = payload.source_ref
        persisted_job_id = (
            payload.job_id.strip()
            if isinstance(payload.job_id, str) and payload.job_id.strip()
            else str(uuid.uuid4())
        )
        await create_running_job(
            db,
            job_id=persisted_job_id,
            source_ref=source_ref,
            demo_mode=demo_mode,
        )
        await db.commit()

        orchestrator = _build_demo_orchestrator() if demo_mode else MaestroOrchestrator()
        result = await orchestrator.run({"input_ref": source_ref, "job_id": persisted_job_id})

        if result.job.status == "done":
            record = await update_job_success(db, job_id=result.job.id, job=result.job)
        else:
            record = await update_job_failure(db, job_id=result.job.id, job=result.job)
        await db.commit()
        status_code = 200
        response_payload = {
            "job_id": record.job_id,
            "status": record.status,
            "step": record.step,
            "error": record.error,
            "duration_ms": record.duration_ms,
        }
        response = JSONResponse(response_payload)
        response.headers["Cache-Control"] = "no-store"
        return response
    except HTTPException:
        raise
    except Exception as exc:
        if persisted_job_id:
            try:
                await update_job_failure(
                    db,
                    job_id=persisted_job_id,
                    step="unknown",
                    error=str(exc),
                )
                await db.commit()
            except Exception:
                await db.rollback()
        raise
    finally:
        duration_ms = max(0, (perf_counter_ns() - started_ns) // 1_000_000)
        _emit_metrics_endpoint_timing(
            endpoint="/internal/maestro/run",
            method="POST",
            status_code=status_code,
            duration_ms=int(duration_ms),
            query_fingerprint="maestro_version=v0.1&demo=1" if demo_mode else "maestro_version=v0.1",
            db_us=0,
            db_queries=0,
            db_pool_wait_us=0,
        )


@router.get("/maestro/jobs/{job_id}")
async def get_internal_maestro_job(
    job_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Consulta o estado persistido de um job do Maestro via endpoint interno."""

    if not should_include_internal_status(request):
        raise HTTPException(status_code=404, detail="Not Found")

    record = await get_job_by_id(db, job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found")

    response = JSONResponse(_serialize_job(record))
    response.headers["Cache-Control"] = "no-store"
    return response
