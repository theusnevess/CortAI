from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.v1.schemas.ops_dashboard import (
    AlertsResponse,
    HealthSummaryResponse,
    RolloutStatusResponse,
    TasksResponse,
    WindowsResponse,
)
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventQueryFilters, QueryProfile
from app.observability.event_query.query_service import EventQueryService
from app.runtime.rollout.config import RolloutConfig, apply_runtime_rollout_overrides

router = APIRouter()

_TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _out_dir() -> Path:
    return Path(os.getenv("OPS_DASHBOARD_BASE_DIR", "OUT"))


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as reader:
        for line in reader:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def _read_slo_status() -> dict[str, Any]:
    return _load_json(_out_dir() / "ops" / "slo_status.json", {"overall_status": "UNKNOWN", "metrics": []})


def _read_alerts() -> list[dict[str, Any]]:
    alerts = _load_jsonl(_out_dir() / "ops" / "alerts.jsonl")
    acknowledgements = {
        item.get("alert_code"): item
        for item in _load_jsonl(_out_dir() / "ops" / "alert_acknowledgements.jsonl")
        if item.get("alert_code")
    }
    merged: list[dict[str, Any]] = []
    for alert in alerts:
        current = dict(alert)
        ack = acknowledgements.get(alert.get("alert_code"))
        if ack:
            current["acknowledged"] = True
            current["acknowledged_by"] = ack.get("operator_id")
            current["acknowledged_at"] = ack.get("acknowledged_at")
            current["acknowledge_reason"] = ack.get("reason")
        else:
            current["acknowledged"] = False
        merged.append(current)
    return merged


def _env_flag(name: str) -> bool:
    return bool(os.getenv(name, "false").strip().lower() in {"1", "true", "yes"})


def _read_rollout_control() -> dict[str, Any]:
    config = apply_runtime_rollout_overrides(RolloutConfig(enabled=_env_flag("ROLL_OUT_ENABLED")), base_dir=_out_dir())
    return {
        "rollout_enabled": config.enabled,
        "kill_switch_enabled": config.kill_switch_enabled,
    }


def _read_rollout_report() -> dict[str, Any]:
    return _load_json(
        _out_dir() / "rollout" / "pilot_rollout_report.json",
        {"rollout_name": "pilot_batch_72h", "batch_summary": {}, "alerts": []},
    )


def _extract_metric(status_payload: dict[str, Any], metric_name: str) -> float | None:
    for metric in status_payload.get("metrics", []):
        if metric.get("metric_name") == metric_name:
            value = metric.get("value")
            if isinstance(value, (int, float)):
                return float(value)
    return None


def _list_runtime_tasks() -> list[dict[str, Any]]:
    base_dir = _out_dir()
    service = EventQueryService(indexer=EventIndexer(base_dir=base_dir))
    # O serviço exige seletor forte; aqui usamos o indexer direto para não distorcer o contrato público de /events.
    events = service.indexer.scan(
        filters=EventQueryFilters(
            start_ts="2026-01-01T00:00:00Z",
            end_ts="2099-01-01T00:00:00Z",
            event_type_prefix="RUNTIME/",
            event_type=None,
            account_id=None,
            window_id=None,
            job_id=None,
            publish_id=None,
            op_key=None,
            severity=None,
            action_taken=None,
        ),
        limit=500,
    ).items

    tasks: dict[str, dict[str, Any]] = {}
    for event in sorted(events, key=lambda item: (item.ts, item.event_id)):
        details = event.details or {}
        task_id = details.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            continue
        current = tasks.setdefault(
            task_id,
            {
                "task_id": task_id,
                "task_type": (event.details or {}).get("task_type"),
                "account_id": event.account_id,
                "window_id": event.window_id,
                "op_key": event.op_key,
                "worker_id": (event.details or {}).get("worker_id"),
                "status": None,
                "attempt_count": None,
                "started_at": None,
                "ended_at": None,
            },
        )
        current["task_type"] = current["task_type"] or (event.details or {}).get("task_type")
        current["account_id"] = current["account_id"] or event.account_id
        current["window_id"] = current["window_id"] or event.window_id
        current["op_key"] = current["op_key"] or event.op_key
        current["worker_id"] = current["worker_id"] or (event.details or {}).get("worker_id")
        if event.event_type == "RUNTIME/task_started":
            current["started_at"] = event.ts
            current["status"] = "RUNNING"
        elif event.event_type == "RUNTIME/task_finished":
            current["ended_at"] = event.ts
            current["status"] = details.get("status") or current["status"]
    return list(tasks.values())


def _build_windows_items() -> list[dict[str, Any]]:
    rollout_report = _read_rollout_report()
    summary = rollout_report.get("batch_summary", {})
    if not isinstance(summary, dict) or not summary:
        return []
    return [
        {
            "window_id": str(summary.get("window_id") or "pilot_window"),
            "account_id": str(summary.get("account_id") or ""),
            "status": "READY" if summary else "UNKNOWN",
            "scorecard": bool(summary.get("scorecard")),
            "attribution": bool(summary.get("content_attribution")),
            "strategy_patch": bool(summary.get("strategy_patch")),
            "patch_application": str(summary.get("patch_applied") or ""),
        }
    ]


@router.get("/health-summary", response_model=HealthSummaryResponse)
def get_health_summary():
    slo_status = _read_slo_status()
    alerts = _read_alerts()
    criticals = [item for item in alerts if str(item.get("severity")).upper() == "CRITICAL"]
    rollout_control = _read_rollout_control()
    rollout_enabled = rollout_control["rollout_enabled"]
    kill_switch_enabled = rollout_control["kill_switch_enabled"]
    return {
        "rollout_enabled": rollout_enabled,
        "kill_switch_enabled": kill_switch_enabled,
        "active_critical_alerts": len(criticals),
        "active_alerts": len(alerts),
        "event_query_p95_ms": _extract_metric(slo_status, "event_query_p95_ms"),
        "fallback_rate": _extract_metric(slo_status, "event_query_fallback_rate"),
        "scheduler_status": "BLOCKED" if kill_switch_enabled else ("ENABLED" if rollout_enabled else "DISABLED"),
        "workers_status": "READY",
    }


@router.get("/rollout-status", response_model=RolloutStatusResponse)
def get_rollout_status():
    report = _read_rollout_report()
    return {
        "rollout_name": report.get("rollout_name") or "pilot_batch_72h",
        "batch_summary": report.get("batch_summary") or {},
        "alerts": report.get("alerts") or [],
    }


@router.get("/windows", response_model=WindowsResponse)
def get_windows():
    return {"items": _build_windows_items()}


@router.get("/tasks", response_model=TasksResponse)
def get_tasks():
    return {"items": _list_runtime_tasks()}


@router.get("/alerts", response_model=AlertsResponse)
def get_alerts():
    return {"items": _read_alerts()}


@router.get("/internal/operator-console", response_class=HTMLResponse)
def get_operator_console(request: Request):
    payload = {
        "health": get_health_summary(),
        "rollout": get_rollout_status(),
        "windows": get_windows(),
        "tasks": get_tasks(),
        "alerts": get_alerts(),
        "actions_base_url": "/api/v1/ops/actions",
        "events_quick_links": {
            "by_window": "/api/v1/events?time_from=2026-01-01T00:00:00Z&time_to=2099-01-01T00:00:00Z&window_id=<window_id>",
            "by_publish": "/api/v1/events?time_from=2026-01-01T00:00:00Z&time_to=2099-01-01T00:00:00Z&publish_id=<publish_id>",
            "by_job": "/api/v1/events?time_from=2026-01-01T00:00:00Z&time_to=2099-01-01T00:00:00Z&job_id=<job_id>",
        },
    }
    return templates.TemplateResponse(
        request,
        "operator_console.html",
        {"payload": payload},
    )
