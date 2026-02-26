from pathlib import Path
from time import perf_counter_ns

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.metrics import _emit_metrics_endpoint_timing
from app.api.v1.endpoints.observability import _build_observability_overview_payload, _new_db_stats
from app.db.session import get_db
from app.observability.runtime_health import should_include_internal_status

router = APIRouter(prefix="/internal", tags=["internal"])

_TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/observability", response_class=HTMLResponse)
async def get_internal_observability_ui(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    UI interna minimalista para o Operational Insights Panel.

    Regras:
    - mesmo gate restrito do painel JSON (404 quando nao autorizado);
    - nenhuma query nova alem das usadas pelo builder JSON do painel;
    - render server-side com template robusto a campos ausentes.
    """
    started_ns = perf_counter_ns()
    status_code = 500
    db_stats = _new_db_stats()
    try:
        if not should_include_internal_status(request):
            status_code = 404
            raise HTTPException(status_code=404, detail="Not Found")

        panel = await _build_observability_overview_payload(db=db, db_stats=db_stats)
        status_code = 200
        response = templates.TemplateResponse(
            "internal_observability.html",
            {"request": request, "panel": panel},
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    finally:
        duration_ms = max(0, (perf_counter_ns() - started_ns) // 1_000_000)
        _emit_metrics_endpoint_timing(
            endpoint="/internal/observability",
            method="GET",
            status_code=status_code,
            duration_ms=int(duration_ms),
            query_fingerprint="ui_version=v1",
            db_us=db_stats["db_us"],
            db_queries=db_stats["db_queries"],
            db_pool_wait_us=db_stats["db_pool_wait_us"],
        )
