from time import perf_counter_ns

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.api.v1.endpoints.metrics import _emit_metrics_endpoint_timing
from app.maestro.orchestrator import MaestroOrchestrator
from app.observability.runtime_health import should_include_internal_status

router = APIRouter(prefix="/internal", tags=["internal"])


class MaestroRunRequest(BaseModel):
    """Payload minimo aceito para disparar uma execucao linear do Maestro."""

    source_ref: str
    job_id: str | None = None


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
    try:
        if not should_include_internal_status(request):
            status_code = 404
            raise HTTPException(status_code=404, detail="Not Found")

        orchestrator = MaestroOrchestrator()
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
            query_fingerprint="maestro_version=v0.1",
            db_us=0,
            db_queries=0,
            db_pool_wait_us=0,
        )
