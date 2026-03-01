from __future__ import annotations

from pathlib import Path
from time import perf_counter_ns

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.metrics import _emit_metrics_endpoint_timing
from app.db.session import get_db
from app.observability.decision_history import list_decision_history
from app.observability.runtime_health import should_include_internal_status

router = APIRouter(prefix="/internal", tags=["internal"])

_TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/decision-history", response_class=HTMLResponse)
async def get_internal_decisions_ui(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    UI interna read-only para inspecionar o Decision History.

    Regras:
    - mesmo gate interno dos outros painéis;
    - sem escrita, sem efeitos colaterais;
    - lista inicial server-side + detalhe/read refresh via API interna já existente.
    """
    started_ns = perf_counter_ns()
    status_code = 500
    try:
        if not should_include_internal_status(request):
            status_code = 404
            raise HTTPException(status_code=404, detail="Not Found")

        items = await list_decision_history(db, limit=20)
        status_code = 200
        response = templates.TemplateResponse(
            request,
            "internal_decisions.html",
            {
                "items": items,
                "decisions_api_url": "/internal/decisions",
                "detail_api_base": "/internal/decisions",
            },
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    finally:
        duration_ms = max(0, (perf_counter_ns() - started_ns) // 1_000_000)
        _emit_metrics_endpoint_timing(
            endpoint="/internal/decision-history",
            method="GET",
            status_code=status_code,
            duration_ms=int(duration_ms),
            query_fingerprint="ui_version=v1",
            db_us=0,
            db_queries=0,
            db_pool_wait_us=0,
        )
