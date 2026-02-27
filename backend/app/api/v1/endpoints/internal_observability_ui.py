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
_ALLOWED_DEMO_SCENARIOS = {"missing", "429", "stale", "green"}


def _build_demo_panel_payload(scenario: str) -> dict:
    """
    Constroi payload visual de demonstracao sem consultas de DB.
    Afeta apenas a UI interna HTML.
    """
    labels = {
        "missing": "Missing Snapshot",
        "429": "Rate Limited (429)",
        "stale": "Stale Snapshot",
        "green": "Healthy",
    }
    base = {
        "as_of": "demo",
        "panel_version": "v1",
        "overall": {"score": "WARN", "decision": "degraded", "reasons": ["demo"]},
        "trust": {
            "state": "yellow",
            "decision": "degraded",
            "message": "Modo demonstracao ativo.",
            "derived_from": ["demo"],
        },
        "recommendation": {
            "action": "monitor",
            "priority": "medium",
            "message": "Cenario de demonstracao (demo).",
            "derived_from": ["demo"],
        },
        "c1_health": {
            "score": "WARN",
            "version": "v1.1",
            "meta": {"cached": True, "cache_age_seconds": 0, "compute_ms": 0},
            "rows": [
                {
                    "path": "demo",
                    "endpoint": "overview",
                    "decision": "WARN",
                    "p99_ms": 20,
                    "rps": 1.2,
                    "reasons": ["demo"],
                },
                {
                    "path": "demo",
                    "endpoint": "runs",
                    "decision": "WARN",
                    "p99_ms": 24,
                    "rps": 1.1,
                    "reasons": ["demo"],
                },
                {
                    "path": "demo",
                    "endpoint": "report",
                    "decision": "WARN",
                    "p99_ms": 0,
                    "rps": 1.0,
                    "reasons": ["demo"],
                },
            ],
            "reasons": ["demo"],
        },
        "read_path": {
            "overview_snapshot_status": "fresh",
            "overview_freshness_seconds": 12,
            "runs_snapshot_status": "fresh",
            "runs_freshness_seconds": 13,
            "runs_key_count": 1,
            "jobs_queued_count": 0,
        },
        "guardrails": {
            "window_minutes": 15,
            "events": {"accepted_202": 0, "rate_limited_429": 0, "snapshot_missing_503": 0},
            "last_events": [],
        },
    }
    if scenario == "missing":
        base["overall"] = {"score": "FAIL", "decision": "action_required", "reasons": ["snapshot_missing(demo)"]}
        base["trust"] = {
            "state": "red",
            "decision": "action_required",
            "message": "Snapshot ausente. Execute warm-up para restaurar dados. (demo)",
            "derived_from": ["read_path"],
        }
        base["recommendation"] = {
            "action": "run_warmup",
            "priority": "high",
            "message": "Snapshot ausente no cenario demo. Execute warm-up.",
            "derived_from": ["read_path"],
        }
        base["read_path"]["overview_snapshot_status"] = "missing"
        base["read_path"]["runs_snapshot_status"] = "missing"
        base["guardrails"]["events"]["snapshot_missing_503"] = 1
    elif scenario == "429":
        base["overall"] = {"score": "WARN", "decision": "degraded", "reasons": ["rate_limited_429(demo)"]}
        base["trust"] = {
            "state": "yellow",
            "decision": "degraded",
            "message": "Muitas solicitacoes recentes. Reduza chamadas force_live. (demo)",
            "derived_from": ["guardrails"],
        }
        base["recommendation"] = {
            "action": "reduce_force_live_burst",
            "priority": "medium",
            "message": "Rate limited no cenario demo. Reduza burst de force_live.",
            "derived_from": ["guardrails"],
        }
        base["guardrails"]["events"]["rate_limited_429"] = 3
    elif scenario == "stale":
        base["overall"] = {"score": "WARN", "decision": "degraded", "reasons": ["snapshot_stale(demo)"]}
        base["trust"] = {
            "state": "yellow",
            "decision": "degraded",
            "message": "Dados possivelmente desatualizados. Verifique atualizacao recente. (demo)",
            "derived_from": ["read_path"],
        }
        base["recommendation"] = {
            "action": "open_report",
            "priority": "medium",
            "message": "Snapshot stale no cenario demo. Abra report para diagnostico.",
            "derived_from": ["read_path"],
        }
        base["read_path"]["overview_snapshot_status"] = "stale"
        base["read_path"]["runs_snapshot_status"] = "stale"
        base["read_path"]["overview_freshness_seconds"] = 220
        base["read_path"]["runs_freshness_seconds"] = 215
    elif scenario == "green":
        base["overall"] = {"score": "PASS", "decision": "healthy", "reasons": ["healthy(demo)"]}
        base["trust"] = {
            "state": "green",
            "decision": "healthy",
            "message": "Sistema saudavel e responsivo. (demo)",
            "derived_from": ["c1_health", "read_path", "guardrails"],
        }
        base["recommendation"] = {
            "action": "none",
            "priority": "low",
            "message": "Sistema saudavel. Nenhuma acao necessaria. (demo)",
            "derived_from": ["trust"],
        }
        base["c1_health"]["score"] = "PASS"
        for row in base["c1_health"]["rows"]:
            row["decision"] = "PASS"
            row["reasons"] = ["demo"]

    base["demo"] = {"enabled": True, "scenario": scenario, "label": labels.get(scenario, scenario)}
    return base


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

        demo_scenario = request.query_params.get("demo_scenario")
        if demo_scenario not in _ALLOWED_DEMO_SCENARIOS:
            demo_scenario = None

        panel = (
            _build_demo_panel_payload(demo_scenario)
            if demo_scenario
            else await _build_observability_overview_payload(db=db, db_stats=db_stats)
        )
        demo = {
            "enabled": bool(demo_scenario),
            "scenario": demo_scenario,
            "label": panel.get("demo", {}).get("label") if isinstance(panel.get("demo"), dict) else None,
        }

        status_code = 200
        response = templates.TemplateResponse(
            request,
            "internal_observability.html",
            {"panel": panel, "demo": demo},
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
