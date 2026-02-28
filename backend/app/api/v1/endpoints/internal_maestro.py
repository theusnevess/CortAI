from time import perf_counter_ns

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.api.v1.endpoints.metrics import _emit_metrics_endpoint_timing
from app.maestro.orchestrator import MaestroOrchestrator
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


@router.post("/maestro/run")
async def run_internal_maestro(request: Request, payload: MaestroRunRequest):
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
    try:
        if not should_include_internal_status(request):
            status_code = 404
            raise HTTPException(status_code=404, detail="Not Found")

        demo_mode = str(request.query_params.get("demo", "")).strip() == "1"
        orchestrator = _build_demo_orchestrator() if demo_mode else MaestroOrchestrator()
        result = await orchestrator.run(
            {
                "input_ref": payload.source_ref,
                "job_id": payload.job_id,
            }
        )
        status_code = 200
        return {
            "job_id": result.job.id,
            "status": result.job.status,
            "step": result.job.step,
            "error": result.job.error,
            "duration_ms": result.job.duration_ms,
        }
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
