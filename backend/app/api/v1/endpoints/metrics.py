import math
import json
import os
import uuid
import hashlib
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CognitiveMetricsDaily, ObservationRecord, PublishReceipt
from app.db.session import get_db
from app.observations import persist_observation
from app.schemas.observation import Observation

try:
    import fcntl
except Exception:
    fcntl = None

router = APIRouter()

# Cleanup SQL (nao executar automaticamente):
# DELETE FROM observations
# WHERE process_id LIKE 'P_METRICS_TEST_%'
#   AND facts->>'event_type' IN ('cognitive_metrics_alert');

# Chaves proibidas de facts para evitar exposicao acidental de paths.
PROHIBITED_FACT_KEYS = {
    "raw_video_minio_path",
    "audio_local_path",
    "video_local_path",
    "file_path",
    "thumbnail_path",
}

CES_DEFAULT_VERSION = "CES_v1"
CES_V1 = "CES_v1"
CES_V2 = "CES_v2"
CES_V3 = "CES_v3"
CES_RUN_V1 = "CES_run_v1"
CES_STATUS_WEIGHTS = {"blocked": 1.0, "failed": 0.6, "truncated": 0.3}
CES_COMPONENT_WEIGHTS = {"status": 0.55, "actions": 0.15, "latency": 0.25, "trunc": 0.05}
CES_ACTIONS_GOOD = 1.0
CES_ACTIONS_BAD = 6.0
CES_MIN_OBS_FOR_LATENCY = 10
CES_V2_LATENCY_SLOPE = 0.7
CES_LATENCY_ACTION_WHITELIST = {
    "collect_video",
    "extract_audio",
    "segment_audio",
    "transcribe_segments",
    "write_artifact",
    "publish_manifest",
}
CES_RUN_STATUS_SCORE = {
    "published": 1.00,
    "completed": 0.98,
    "truncated": 0.70,
    "failed": 0.35,
    "blocked": 0.10,
    "unknown": 0.00,
}
CES_RUN_LATENCY_MIN_OBS = 3
CES_RUN_LATENCY_SLOPE = 0.7
CES_RUN_BUDGETS_MS = {
    "collect_video": 20000,
    "extract_audio": 5000,
    "segment_audio": 8000,
    "transcribe_segments": 30000,
    "write_artifact": 3000,
    "publish_manifest": 3000,
}
CES_DYNAMIC_BASELINE_WINDOW_DAYS = 14
CES_DYNAMIC_BASELINE_MIN_N = 10
MANIFEST_OUTPUT_DIR = "agent_output"
METRICS_RUNS_LIMIT_MAX = 200
METRICS_RUNS_RANGE_MAX_DAYS = 31
METRICS_OVERVIEW_CACHE_TTL_SECONDS = 10
METRICS_OVERVIEW_CACHE_MAX_ENTRIES = 128
_metrics_overview_cache: dict[str, tuple[float, str]] = {}
_metrics_overview_cache_lock = Lock()


def _get_int_env(name: str, default: int) -> int:
    """
    Le inteiro de env com fallback deterministico.
    """
    import os

    raw = os.getenv(name)
    try:
        return int(raw) if raw is not None else default
    except Exception:
        return default


def _get_float_env(name: str, default: float) -> float:
    """
    Le float de env com fallback deterministico.
    """
    import os

    raw = os.getenv(name)
    try:
        return float(raw) if raw is not None else default
    except Exception:
        return default


def _parse_date(value: str | None, label: str) -> date | None:
    """
    Converte string YYYY-MM-DD em date.
    Args:
        value: String no formato YYYY-MM-DD ou None.
        label: Nome do campo para mensagem de erro.
    Returns:
        Data correspondente ou None quando value for None.
    Raises:
        HTTPException 400 se o formato for invalido.
    """
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail=f"{label} must be YYYY-MM-DD")


def _overview_cache_enabled() -> bool:
    """
    Habilita cache curto somente fora de pytest.
    """
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return METRICS_OVERVIEW_CACHE_TTL_SECONDS > 0


def _build_overview_cache_key(
    *,
    start: date,
    end: date,
    include_reasons: bool,
    include_baseline: bool,
) -> str:
    return (
        f"start={start.isoformat()}|end={end.isoformat()}"
        f"|reasons={int(include_reasons)}|baseline={int(include_baseline)}"
    )


def _overview_cache_key_hash(key: str) -> str:
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]


def _get_overview_cache(key: str) -> str | None:
    if not _overview_cache_enabled():
        return None
    now = perf_counter()
    with _metrics_overview_cache_lock:
        payload = _metrics_overview_cache.get(key)
        if payload is None:
            return None
        expires_at, data = payload
        if expires_at <= now:
            _metrics_overview_cache.pop(key, None)
            return None
        return data


def _set_overview_cache(key: str, payload_json: str) -> None:
    if not _overview_cache_enabled():
        return
    expires_at = perf_counter() + METRICS_OVERVIEW_CACHE_TTL_SECONDS
    with _metrics_overview_cache_lock:
        if len(_metrics_overview_cache) >= METRICS_OVERVIEW_CACHE_MAX_ENTRIES:
            # Remove entrada mais antiga para manter custo previsivel.
            oldest_key = next(iter(_metrics_overview_cache), None)
            if oldest_key is not None:
                _metrics_overview_cache.pop(oldest_key, None)
        _metrics_overview_cache[key] = (expires_at, payload_json)


def _filter_facts(facts: dict) -> dict:
    """
    Remove chaves proibidas do dicionario facts.
    """
    if not isinstance(facts, dict):
        return facts
    return {k: v for k, v in facts.items() if k not in PROHIBITED_FACT_KEYS}


def _dedup_and_sort_reasons(reasons: list) -> list:
    """
    Deduplica e ordena a lista de reasons.
    """
    if not isinstance(reasons, list):
        return []
    return sorted(set(str(r) for r in reasons))


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """
    Limita valor numerico no intervalo [min_value, max_value].
    """
    return max(min_value, min(max_value, value))


def _safe_int(value, default: int = 0) -> int:
    """
    Converte valor para int com fallback seguro.
    """
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value, default: float = 0.0) -> float:
    """
    Converte valor para float com fallback seguro.
    """
    try:
        return float(value)
    except Exception:
        return default


def _parse_ts(value: str | None) -> datetime | None:
    """
    Converte timestamp ISO para datetime.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


def _p95(values: list[int]) -> int:
    """
    Calcula p95 por nearest-rank.
    """
    if not values:
        return 0
    ordered = sorted(values)
    idx = int(0.95 * (len(ordered) - 1))
    return int(ordered[idx])


def _read_jsonl_rows(path: Path) -> list[dict]:
    """
    Le arquivo JSONL com fallback seguro.
    """
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


@contextmanager
def _jsonl_lock(path: Path, exclusive: bool):
    """
    Aplica lock em JSONL para escrita/leitura concorrente segura.
    """
    lock_dir = path.parent / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"{path.name}.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        if fcntl is not None:
            mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            fcntl.flock(lock_file.fileno(), mode)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _append_minimal_outcome(outcome_id: str, process_id: str) -> None:
    """
    Anexa outcome minimo para satisfazer guardrail de Observation.
    """
    storage_dir = Path(os.getenv("CORTAI_STORAGE_DIR", "storage"))
    outcome_path = storage_dir / "outcome_log.jsonl"
    outcome_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "outcome_id": outcome_id,
        "timestamp": datetime.utcnow().isoformat(),
        "process_id": process_id,
        "source_decision_id": "",
        "execution_status": "external",
        "metrics": {"origin": "metrics_api"},
    }
    with _jsonl_lock(outcome_path, exclusive=True):
        with outcome_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


def _build_runs_query_fingerprint(limit: int, offset: int, start: date, end: date) -> str:
    """
    Gera fingerprint curta e deterministica para /metrics/runs.
    """
    range_days = (end - start).days + 1
    return f"limit={limit}&offset={offset}&range={range_days}d"


def _emit_metrics_endpoint_timing(
    *,
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: int,
    query_fingerprint: str,
    process_id: str | None = None,
    cache_hit: bool | None = None,
    cache_key_hash: str | None = None,
) -> None:
    """
    Emite telemetria append-only por request dos endpoints de metricas.
    """
    try:
        event_ts = datetime.utcnow().isoformat()
        metric_date = event_ts[:10]
        synthetic_process_id = f"P_METRICS_ENDPOINT_{metric_date}"
        source_outcome_id = str(uuid.uuid4())
        _append_minimal_outcome(source_outcome_id, synthetic_process_id)
        facts: dict[str, Any] = {
            "event_type": "metrics_endpoint_timing",
            "endpoint": endpoint,
            "method": method,
            "status_code": int(status_code),
            "duration_ms": int(max(0, duration_ms)),
            "query_fingerprint": str(query_fingerprint),
            "metric_date": metric_date,
            "timestamp": event_ts,
        }
        if process_id:
            facts["process_id"] = process_id
        if cache_hit is not None:
            facts["cache_hit"] = bool(cache_hit)
        if cache_key_hash:
            facts["cache_key_hash"] = str(cache_key_hash)
        observation = Observation(
            observation_id=str(uuid.uuid4()),
            timestamp=event_ts,
            process_id=synthetic_process_id,
            source_outcome_id=source_outcome_id,
            facts=facts,
        )
        persist_observation(observation)
    except Exception:
        # Telemetria nunca deve quebrar o endpoint principal.
        return


def _get_storage_paths() -> tuple[Path, Path]:
    """
    Resolve caminhos dos logs de decision/outcome.
    """
    base = Path(os.getenv("CORTAI_STORAGE_DIR", "storage"))
    return base / "decision_log.jsonl", base / "outcome_log.jsonl"


def _build_run_latency_map(run_anchors: dict[str, dict]) -> dict[str, dict]:
    """
    Calcula latencia real por run a partir de decision/outcome logs.
    """
    if not run_anchors:
        return {}

    process_ids = set(run_anchors.keys())
    decision_path, outcome_path = _get_storage_paths()
    decisions = _read_jsonl_rows(decision_path)
    outcomes = _read_jsonl_rows(outcome_path)

    decisions_by_pid: dict[str, list[dict]] = {}
    for row in decisions:
        pid = row.get("process_id")
        did = row.get("decision_id")
        ts = _parse_ts(row.get("timestamp"))
        if pid not in process_ids or not isinstance(did, str) or ts is None:
            continue
        finished_ts = run_anchors[pid]["timestamp_finished"]
        if ts > finished_ts:
            continue
        action = row.get("action") if isinstance(row.get("action"), dict) else {}
        action_type = action.get("type") or row.get("action_type") or "unknown"
        decisions_by_pid.setdefault(pid, []).append(
            {"decision_id": did, "timestamp": ts, "action_type": str(action_type)}
        )

    latest_outcome_by_key: dict[tuple[str, str], dict] = {}
    for row in outcomes:
        pid = row.get("process_id")
        sid = row.get("source_decision_id")
        ots = _parse_ts(row.get("timestamp"))
        if pid not in process_ids or not isinstance(sid, str) or ots is None:
            continue
        finished_ts = run_anchors[pid]["timestamp_finished"]
        if ots > finished_ts:
            continue
        key = (pid, sid)
        prev = latest_outcome_by_key.get(key)
        if prev is None or ots >= prev["timestamp"]:
            metrics_payload = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
            latest_outcome_by_key[key] = {
                "timestamp": ots,
                "last_action_type": metrics_payload.get("last_action_type"),
            }

    result: dict[str, dict] = {}
    for pid in process_ids:
        action_durations: dict[str, list[int]] = {}
        pairs_used = 0
        pairs_ignored = 0
        pairs_inverted = 0

        decisions_for_pid = decisions_by_pid.get(pid, [])
        decision_ids = {d["decision_id"] for d in decisions_for_pid}
        for outcome_decision_id in latest_outcome_by_key.keys():
            out_pid, out_sid = outcome_decision_id
            if out_pid != pid:
                continue
            if out_sid not in decision_ids:
                pairs_ignored += 1

        for decision in decisions_for_pid:
            out = latest_outcome_by_key.get((pid, decision["decision_id"]))
            if not out:
                pairs_ignored += 1
                continue
            delta_ms = int((out["timestamp"] - decision["timestamp"]).total_seconds() * 1000)
            if delta_ms < 0:
                pairs_ignored += 1
                pairs_inverted += 1
                continue
            action_type = out.get("last_action_type") or decision["action_type"] or "unknown"
            if action_type not in CES_RUN_BUDGETS_MS:
                pairs_ignored += 1
                continue
            action_durations.setdefault(str(action_type), []).append(delta_ms)
            pairs_used += 1

        eligible = {
            action: durations
            for action, durations in action_durations.items()
            if len(durations) >= CES_RUN_LATENCY_MIN_OBS
        }
        if not eligible:
            result[pid] = {
                "latency_score": 1.0,
                "latency_measured": False,
                "budgets_used": {},
                "latency_pairs_used": pairs_used,
                "latency_pairs_ignored": pairs_ignored,
                "latency_pairs_inverted": pairs_inverted,
            }
            continue

        total_n = sum(len(v) for v in eligible.values())
        latency_score = 0.0
        budgets_used: dict[str, dict] = {}
        for action, durations in sorted(eligible.items()):
            n_obs = len(durations)
            p95_ms = _p95(durations)
            budget_ms = CES_RUN_BUDGETS_MS[action]
            ratio = p95_ms / budget_ms if budget_ms > 0 else 1.0
            if ratio <= 1.0:
                action_score = 1.0
            else:
                action_score = _clamp(1.0 - CES_RUN_LATENCY_SLOPE * (ratio - 1.0))
            weight = n_obs / total_n if total_n else 0.0
            latency_score += weight * action_score
            budgets_used[action] = {
                "n": n_obs,
                "p95_ms": p95_ms,
                "budget_ms": budget_ms,
                "ratio_a": round(ratio, 6),
                "score_a": round(action_score, 6),
                "weight": round(weight, 6),
            }

        result[pid] = {
            "latency_score": round(_clamp(latency_score), 4),
            "latency_measured": True,
            "budgets_used": budgets_used,
            "latency_pairs_used": pairs_used,
            "latency_pairs_ignored": pairs_ignored,
            "latency_pairs_inverted": pairs_inverted,
        }

    return result


def _compute_latency_inputs(item: dict, version: str) -> tuple[dict[str, dict], int]:
    """
    Normaliza entradas de latencia para acoes elegiveis do CES.
    """
    latency_by_action = item.get("latency_by_action") or {}
    eligible: dict[str, dict] = {}
    total_n = 0
    for action_name, payload in latency_by_action.items():
        if not isinstance(payload, dict):
            continue
        if action_name not in CES_LATENCY_ACTION_WHITELIST:
            continue
        n_obs = int(payload.get("n") or 0)
        p95_ms = int(payload.get("p95_ms") or 0)
        if n_obs < CES_MIN_OBS_FOR_LATENCY or p95_ms <= 0:
            continue
        baseline_payload = item.get("latency_dynamic_baseline", {})
        baseline_action = baseline_payload.get(action_name, {}) if isinstance(baseline_payload, dict) else {}
        if version == CES_V3:
            budget_ms = int(baseline_action.get("budget_ms") or CES_RUN_BUDGETS_MS[action_name])
            budget_source_raw = str(baseline_action.get("source") or "")
            budget_source = "dynamic_14d" if budget_source_raw == "dynamic_14d" else "fixed_v1"
        else:
            budget_ms = int(math.ceil((p95_ms * 1.10) - 1e-9))
            budget_source = "fixed_ceil_1p10"
        eligible[action_name] = {
            "n": n_obs,
            "p95_ms": p95_ms,
            "budget_ms": budget_ms,
            "budget_source": budget_source,
        }
        total_n += n_obs
    return eligible, total_n


def _compute_ces_version(item: dict, version: str) -> dict:
    """
    Calcula uma versao do CES diario com componentes e budgets auditaveis.
    """
    total_runs = int(item.get("total_runs") or 0)
    if total_runs <= 0:
        return {
            "ces": None,
            "ces_reason": "no_runs",
            "ces_version": version,
            "ces_components": {
                "status": None,
                "actions": None,
                "latency": None,
                "trunc": None,
            },
            "budgets_used": {},
        }

    blocked_runs = int(item.get("blocked_runs") or 0)
    failed_runs = int(item.get("failed_runs") or 0)
    truncated_runs = int(item.get("truncated_runs") or 0)

    r_b = blocked_runs / total_runs
    r_f = failed_runs / total_runs
    r_t = truncated_runs / total_runs

    s_status = _clamp(
        1.0
        - (
            CES_STATUS_WEIGHTS["blocked"] * r_b
            + CES_STATUS_WEIGHTS["failed"] * r_f
            + CES_STATUS_WEIGHTS["truncated"] * r_t
        )
    )

    avg_actions = float(item.get("avg_actions_executed") or 0.0)
    denom_actions = CES_ACTIONS_BAD - CES_ACTIONS_GOOD
    if denom_actions <= 0:
        s_actions = 1.0
    else:
        s_actions = _clamp((CES_ACTIONS_BAD - avg_actions) / denom_actions)

    s_trunc = _clamp(1.0 - r_t)

    eligible, total_n = _compute_latency_inputs(item, version)

    if total_n <= 0:
        s_latency = 1.0
        budgets_used = {}
    else:
        s_latency = 0.0
        budgets_used = {}
        for action_name, payload in sorted(eligible.items()):
            weight = payload["n"] / total_n
            if version == CES_V2:
                ratio = payload["p95_ms"] / payload["budget_ms"]
                if ratio <= 1.0:
                    action_score = 1.0
                else:
                    action_score = _clamp(1.0 - CES_V2_LATENCY_SLOPE * (ratio - 1.0))
            else:
                action_score = _clamp(payload["budget_ms"] / payload["p95_ms"])
            s_latency += weight * action_score
            budgets_used[action_name] = {
                "n": payload["n"],
                "p95_ms": payload["p95_ms"],
                "budget_ms": payload["budget_ms"],
                "source": payload["budget_source"],
                "weight": round(weight, 6),
            }
        s_latency = _clamp(s_latency)

    ces_value = 100.0 * (
        CES_COMPONENT_WEIGHTS["status"] * s_status
        + CES_COMPONENT_WEIGHTS["actions"] * s_actions
        + CES_COMPONENT_WEIGHTS["latency"] * s_latency
        + CES_COMPONENT_WEIGHTS["trunc"] * s_trunc
    )

    return {
        "ces": round(_clamp(ces_value, 0.0, 100.0), 2),
        "ces_reason": None,
        "ces_version": version,
        "ces_components": {
            "status": round(s_status, 4),
            "actions": round(s_actions, 4),
            "latency": round(s_latency, 4),
            "trunc": round(s_trunc, 4),
        },
        "budgets_used": budgets_used,
    }


def _compute_ces_fields(item: dict) -> dict:
    """
    Calcula CES versionado por item, mantendo CES_v1 como default.
    """
    ces_versions = {
        CES_V1: _compute_ces_version(item, CES_V1),
        CES_V2: _compute_ces_version(item, CES_V2),
        CES_V3: _compute_ces_version(item, CES_V3),
    }
    default_payload = ces_versions[CES_DEFAULT_VERSION]
    return {
        "ces_default_version": CES_DEFAULT_VERSION,
        "ces": default_payload["ces"],
        "ces_version": CES_DEFAULT_VERSION,
        "ces_reason": default_payload["ces_reason"],
        "ces_components": default_payload["ces_components"],
        "budgets_used": default_payload["budgets_used"],
        "ces_versions": ces_versions,
    }


def _median(values: list[int]) -> float:
    """
    Calcula mediana deterministica de inteiros.
    """
    if not values:
        return 0.0
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _build_dynamic_baseline_for_date(
    metric_date: date,
    history_rows: list[CognitiveMetricsDaily],
) -> dict[str, dict]:
    """
    Calcula baseline dinamico read-only por acao para a data alvo.
    """
    by_action: dict[str, list[int]] = {action: [] for action in CES_LATENCY_ACTION_WHITELIST}
    for row in history_rows:
        if row.metric_date >= metric_date:
            continue
        if row.metric_date < metric_date - timedelta(days=CES_DYNAMIC_BASELINE_WINDOW_DAYS):
            continue
        if int(row.total_runs or 0) <= 0:
            continue
        latency_payload = row.latency_by_action or {}
        if not isinstance(latency_payload, dict):
            continue
        for action in CES_LATENCY_ACTION_WHITELIST:
            action_payload = latency_payload.get(action)
            if not isinstance(action_payload, dict):
                continue
            n_obs = int(action_payload.get("n") or 0)
            p95_ms = int(action_payload.get("p95_ms") or 0)
            if n_obs < CES_DYNAMIC_BASELINE_MIN_N or p95_ms <= 0:
                continue
            by_action[action].append(p95_ms)

    baseline = {}
    for action in sorted(CES_LATENCY_ACTION_WHITELIST):
        samples = by_action.get(action, [])
        if samples:
            med = _median(samples)
            budget_ms = int(math.ceil((med * 1.10) - 1e-9))
            baseline[action] = {
                "budget_ms": budget_ms,
                "source": "dynamic_14d",
                "samples_used": len(samples),
            }
        else:
            baseline[action] = {
                "budget_ms": CES_RUN_BUDGETS_MS[action],
                "source": "fallback_fixed_v1",
                "samples_used": 0,
            }
    return baseline


def _compute_ces_window_summary(items: list[dict]) -> dict:
    """
    Calcula metadados de janela CES refletindo a regra do alerta.
    Regras:
    - considera apenas os ultimos W dias validos do range retornado
    - dia valido: ces != null e ces_reason != "no_runs"
    - dia ruim: ces < threshold
    """
    window_days = _get_int_env("COGNITIVE_ALERT_CES_WINDOW_DAYS", 7)
    if window_days < 1:
        window_days = 1
    threshold = _get_float_env("COGNITIVE_ALERT_CES_THRESHOLD", 85.0)
    bad_days_required = _get_int_env("COGNITIVE_ALERT_CES_BAD_DAYS", 3)
    if bad_days_required < 1:
        bad_days_required = 1

    valid_items = [
        item
        for item in items
        if item.get("ces") is not None and item.get("ces_reason") != "no_runs"
    ]
    window_items = valid_items[-window_days:]
    effective_days = len(window_items)
    bad_days = 0
    for item in window_items:
        if float(item.get("ces")) < threshold:
            bad_days += 1

    ratio = None
    if effective_days > 0:
        ratio = round(bad_days / effective_days, 4)

    return {
        "ces_window_days": window_days,
        "ces_window_effective_days": effective_days,
        "ces_threshold": threshold,
        "ces_bad_days_required": bad_days_required,
        "ces_bad_days_in_window": bad_days,
        "ces_bad_days_ratio": ratio,
    }


def _compute_ces_run_fields(facts: dict, latency_payload: dict | None = None) -> dict:
    """
    Calcula CES run-level v1 de forma deterministica.
    """
    pipeline_status = (facts or {}).get("pipeline_status")
    if not pipeline_status:
        return {
            "pipeline_status": "unknown",
            "ces_run": None,
            "ces_run_version": CES_RUN_V1,
            "ces_run_reason": "missing_pipeline_status",
            "ces_run_components": {
                "status": None,
                "actions": None,
                "latency": None,
                "trunc": None,
            },
            "latency_measured": False,
            "budgets_used": {},
            "latency_pairs_used": 0,
            "latency_pairs_ignored": 0,
            "latency_pairs_inverted": 0,
        }

    status_score = CES_RUN_STATUS_SCORE.get(str(pipeline_status), CES_RUN_STATUS_SCORE["unknown"])
    actions_value = (facts or {}).get("actions_executed")
    if actions_value is None:
        actions_score = 0.0
    else:
        actions_int = _safe_int(actions_value)
        actions_score = _clamp((6.0 - actions_int) / (6.0 - 1.0))
    trunc_score = 0.0 if str(pipeline_status) == "truncated" else 1.0
    latency_payload = latency_payload or {}
    latency_score = _safe_float(latency_payload.get("latency_score", 1.0), 1.0)
    latency_measured = bool(latency_payload.get("latency_measured", False))
    budgets_used = latency_payload.get("budgets_used")
    if not isinstance(budgets_used, dict):
        budgets_used = {}
    latency_pairs_used = _safe_int(latency_payload.get("latency_pairs_used"), 0)
    latency_pairs_ignored = _safe_int(latency_payload.get("latency_pairs_ignored"), 0)
    latency_pairs_inverted = _safe_int(latency_payload.get("latency_pairs_inverted"), 0)

    ces_run = 100.0 * (
        0.60 * status_score
        + 0.15 * actions_score
        + 0.20 * latency_score
        + 0.05 * trunc_score
    )
    return {
        "pipeline_status": str(pipeline_status),
        "ces_run": round(_clamp(ces_run, 0.0, 100.0), 2),
        "ces_run_version": CES_RUN_V1,
        "ces_run_reason": None,
        "ces_run_components": {
            "status": round(status_score, 4),
            "actions": round(actions_score, 4),
            "latency": round(_clamp(latency_score), 4),
            "trunc": round(trunc_score, 4),
        },
        "latency_measured": latency_measured,
        "budgets_used": budgets_used,
        "latency_pairs_used": latency_pairs_used,
        "latency_pairs_ignored": latency_pairs_ignored,
        "latency_pairs_inverted": latency_pairs_inverted,
    }


def _sanitize_error_message(message: Any) -> str | None:
    """
    Sanitiza mensagem de erro para evitar vazamento de paths sensiveis.
    """
    if not isinstance(message, str) or not message:
        return None
    sanitized = message
    sanitized = sanitized.replace("\\", "/")
    for token in ("/tmp/", "storage/", "videos-raw/", ".mp4", ".wav"):
        if token in sanitized:
            sanitized = sanitized.replace(token, "<path>/")
    return sanitized[:500]


def _find_outcome_for_process(
    process_id: str, source_outcome_id: str | None
) -> dict[str, Any] | None:
    """
    Busca outcome do processo no JSONL, preferindo o source_outcome_id do finished.
    """
    _, outcome_path = _get_storage_paths()
    rows = _read_jsonl_rows(outcome_path)
    if not rows:
        return None

    latest_for_process = None
    latest_ts = None
    target_by_id = None
    for row in rows:
        if row.get("process_id") != process_id:
            continue
        ts = _parse_ts(row.get("timestamp"))
        if ts and (latest_ts is None or ts >= latest_ts):
            latest_ts = ts
            latest_for_process = row
        if source_outcome_id and row.get("outcome_id") == source_outcome_id:
            target_by_id = row
    return target_by_id or latest_for_process


def _manifest_path_from_decision_id(manifest_decision_id: str | None) -> str | None:
    """
    Resolve path canonico do manifest por decision_id.
    """
    if not isinstance(manifest_decision_id, str) or not manifest_decision_id:
        return None
    base = Path(os.getenv("ARTIFACT_OUTPUT_DIR", f"storage/{MANIFEST_OUTPUT_DIR}"))
    return str(base / f"{manifest_decision_id}.json")


def _build_alerts_by_date(alert_rows: list[tuple]) -> dict[str, dict]:
    """
    Agrega alertas de forma deterministica por metric_date.
    Mantem:
      - alert_count: quantidade de alertas no dia
      - alert_reasons: dedupe + ordenacao
      - alert_observation_id: id mais recente por timestamp
    """
    alerts_by_date: dict[str, dict] = {}
    for obs_id, ts, facts in alert_rows:
        if not isinstance(facts, dict):
            continue
        metric_date = facts.get("metric_date")
        if not metric_date:
            continue
        reasons = _dedup_and_sort_reasons(facts.get("reasons", []))
        payload = alerts_by_date.setdefault(
            metric_date,
            {
                "alert_count": 0,
                "alert_reasons": set(),
                "alert_observation_id": None,
                "latest_ts": None,
            },
        )
        payload["alert_count"] += 1
        payload["alert_reasons"].update(reasons)
        if payload["latest_ts"] is None or (ts and ts >= payload["latest_ts"]):
            payload["latest_ts"] = ts
            payload["alert_observation_id"] = obs_id

    for metric_date, payload in alerts_by_date.items():
        payload["alert_reasons"] = sorted(payload["alert_reasons"])
        payload.pop("latest_ts", None)

    return alerts_by_date


@router.get("/daily")
async def get_daily_metrics(
    days: int = 7,
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna metricas diarias agregadas por data (read-only).
    Args:
        days: quantidade de dias para retornar (default 7, max 365)
        start_date: filtra metricas a partir dessa data (YYYY-MM-DD)
        end_date: filtra metricas ate essa data (YYYY-MM-DD)
    """
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")

    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date, "end_date")

    if end is None:
        end = datetime.utcnow().date()
    if start is None:
        start = end - timedelta(days=days - 1)

    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    stmt = (
        select(CognitiveMetricsDaily)
        .where(CognitiveMetricsDaily.metric_date >= start)
        .where(CognitiveMetricsDaily.metric_date <= end)
        .order_by(CognitiveMetricsDaily.metric_date.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    baseline_stmt = (
        select(CognitiveMetricsDaily)
        .where(CognitiveMetricsDaily.metric_date >= start - timedelta(days=CES_DYNAMIC_BASELINE_WINDOW_DAYS))
        .where(CognitiveMetricsDaily.metric_date <= end)
        .order_by(CognitiveMetricsDaily.metric_date.asc())
    )
    baseline_rows = (await db.execute(baseline_stmt)).scalars().all()

    alert_stmt = (
        select(
            ObservationRecord.observation_id,
            ObservationRecord.timestamp,
            ObservationRecord.facts,
        )
        .where(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
        .where(ObservationRecord.facts["metric_date"].astext >= start.isoformat())
        .where(ObservationRecord.facts["metric_date"].astext <= end.isoformat())
    )
    alert_rows = (await db.execute(alert_stmt)).all()
    alerts_by_date = _build_alerts_by_date(alert_rows)

    items = []
    for r in rows:
        metric_key = r.metric_date.isoformat()
        alert_info = alerts_by_date.get(metric_key, None)
        alert_count = alert_info["alert_count"] if alert_info else 0
        alerted = alert_count > 0
        item = {
            "metric_date": r.metric_date.isoformat(),
            "total_runs": r.total_runs,
            "completed_runs": r.completed_runs,
            "failed_runs": r.failed_runs,
            "blocked_runs": r.blocked_runs,
            "truncated_runs": getattr(r, "truncated_runs", 0),
            "truncated_ratio": float(r.truncated_ratio)
            if getattr(r, "truncated_ratio", None) is not None
            else None,
            "avg_actions_executed": float(r.avg_actions_executed)
            if r.avg_actions_executed is not None
            else None,
            "last_action_type_distribution": r.last_action_type_distribution,
            "latency_by_action": getattr(r, "latency_by_action", {}) or {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "alerted": alerted,
            "alert_count": alert_count,
            "alert_reasons": alert_info["alert_reasons"] if alert_info else [],
            "alert_observation_id": alert_info["alert_observation_id"] if alert_info else None,
            "latency_dynamic_baseline_window_days": CES_DYNAMIC_BASELINE_WINDOW_DAYS,
            "latency_dynamic_baseline": _build_dynamic_baseline_for_date(
                r.metric_date,
                baseline_rows,
            ),
        }
        # Invariantes do contrato de alerta.
        if not item["alerted"]:
            item["alert_count"] = 0
            item["alert_reasons"] = []
            item["alert_observation_id"] = None
        elif item["alert_observation_id"] is None:
            item["alerted"] = False
            item["alert_count"] = 0
            item["alert_reasons"] = []
        item.update(_compute_ces_fields(item))
        items.append(item)

    return {"items": items}


@router.get("/overview")
async def get_metrics_overview(
    days: int = 7,
    start_date: str | None = None,
    end_date: str | None = None,
    include_reasons: bool = Query(False),
    include_baseline: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna metricas diarias com resumo agregado.
    Args:
        days: quantidade de dias para retornar (default 7, max 365)
        start_date: filtra metricas a partir dessa data (YYYY-MM-DD)
        end_date: filtra metricas ate essa data (YYYY-MM-DD)
    """
    started_at = perf_counter()
    status_code = 500
    cache_hit_flag: bool | None = None
    cache_key_hash: str | None = None
    query_fingerprint = (
        f"days={days}&start_date={start_date or ''}&end_date={end_date or ''}"
        f"&include_reasons={str(include_reasons).lower()}"
        f"&include_baseline={str(include_baseline).lower()}"
    )
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="days must be between 1 and 365")

        start = _parse_date(start_date, "start_date")
        end = _parse_date(end_date, "end_date")

        if end is None:
            end = datetime.utcnow().date()
        if start is None:
            start = end - timedelta(days=days - 1)

        if start > end:
            raise HTTPException(status_code=400, detail="start_date must be <= end_date")

        cache_key = _build_overview_cache_key(
            start=start,
            end=end,
            include_reasons=include_reasons,
            include_baseline=include_baseline,
        )
        cache_key_hash = _overview_cache_key_hash(cache_key)
        cached_payload_json = _get_overview_cache(cache_key)
        if cached_payload_json is not None:
            cache_hit_flag = True
            status_code = 200
            return Response(content=cached_payload_json, media_type="application/json", status_code=200)
        cache_hit_flag = False

        stmt = (
            select(CognitiveMetricsDaily)
            .where(CognitiveMetricsDaily.metric_date >= start)
            .where(CognitiveMetricsDaily.metric_date <= end)
            .order_by(CognitiveMetricsDaily.metric_date.asc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        baseline_stmt = (
            select(CognitiveMetricsDaily)
            .where(CognitiveMetricsDaily.metric_date >= start - timedelta(days=CES_DYNAMIC_BASELINE_WINDOW_DAYS))
            .where(CognitiveMetricsDaily.metric_date <= end)
            .order_by(CognitiveMetricsDaily.metric_date.asc())
        )
        baseline_rows = (await db.execute(baseline_stmt)).scalars().all()
        baseline_cache_by_date: dict[date, dict[str, dict]] = {}

        # Overview é read-only DB-first: usa alertas já materializados no agregado diário.
        items = []
        for r in rows:
            alert_count = int(getattr(r, "alert_count", 0) or 0)
            alerted = alert_count > 0
            raw_reasons = getattr(r, "alert_reasons", []) or []
            reasons = _dedup_and_sort_reasons(raw_reasons) if include_reasons else []
            metric_date = r.metric_date
            baseline_for_day = baseline_cache_by_date.get(metric_date)
            if baseline_for_day is None:
                baseline_for_day = _build_dynamic_baseline_for_date(metric_date, baseline_rows)
                baseline_cache_by_date[metric_date] = baseline_for_day
            item = {
                "metric_date": metric_date.isoformat(),
                "total_runs": r.total_runs,
                "completed_runs": r.completed_runs,
                "failed_runs": r.failed_runs,
                "blocked_runs": r.blocked_runs,
                "truncated_runs": getattr(r, "truncated_runs", 0),
                "truncated_ratio": float(r.truncated_ratio)
                if getattr(r, "truncated_ratio", None) is not None
                else None,
                "avg_actions_executed": float(r.avg_actions_executed)
                if r.avg_actions_executed is not None
                else None,
                "last_action_type_distribution": r.last_action_type_distribution,
                "latency_by_action": getattr(r, "latency_by_action", {}) or {},
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "alerted": alerted,
                "alert_count": alert_count,
                "alert_reasons": reasons,
                "alert_observation_id": None,
                "latency_dynamic_baseline_window_days": CES_DYNAMIC_BASELINE_WINDOW_DAYS,
                "latency_dynamic_baseline": baseline_for_day,
            }
            if not item["alerted"]:
                item["alert_count"] = 0
                item["alert_reasons"] = []
                item["alert_observation_id"] = None
            item.update(_compute_ces_fields(item))
            if not include_baseline:
                item["latency_dynamic_baseline"] = {}
            items.append(item)

        # Resumo agregado do periodo.
        summary = {
            "total_runs": sum(item["total_runs"] for item in items),
            "completed_runs": sum(item["completed_runs"] for item in items),
            "failed_runs": sum(item["failed_runs"] for item in items),
            "blocked_runs": sum(item["blocked_runs"] for item in items),
            "truncated_runs": sum(item["truncated_runs"] for item in items),
            "alert_days": sum(1 for item in items if item["alerted"]),
        }

        total_runs = summary["total_runs"]
        if total_runs > 0:
            summary["failed_ratio"] = round(summary["failed_runs"] / total_runs, 4)
            summary["blocked_ratio"] = round(summary["blocked_runs"] / total_runs, 4)
            summary["truncated_ratio"] = round(summary["truncated_runs"] / total_runs, 4)
        else:
            summary["failed_ratio"] = 0.0
            summary["blocked_ratio"] = 0.0
            summary["truncated_ratio"] = 0.0

        # CES agregado do periodo (media ponderada por total_runs) por versao.
        ces_versions_summary: dict[str, dict] = {}
        for version in (CES_V1, CES_V2, CES_V3):
            items_with_runs = [
                item
                for item in items
                if item.get("total_runs", 0) > 0
                and isinstance(item.get("ces_versions", {}).get(version), dict)
                and item["ces_versions"][version].get("ces") is not None
            ]
            weighted_runs = sum(item["total_runs"] for item in items_with_runs)
            if weighted_runs > 0:
                ces_versions_summary[version] = {
                    "ces": round(
                        sum(float(item["ces_versions"][version]["ces"]) * item["total_runs"] for item in items_with_runs)
                        / weighted_runs,
                        2,
                    ),
                    "ces_reason": None,
                    "ces_components": {
                        key: round(
                            sum(
                                float(item["ces_versions"][version]["ces_components"][key]) * item["total_runs"]
                                for item in items_with_runs
                            )
                            / weighted_runs,
                            4,
                        )
                        for key in ("status", "actions", "latency", "trunc")
                    },
                    "budgets_used": {},
                }
            else:
                ces_versions_summary[version] = {
                    "ces": None,
                    "ces_reason": "no_runs",
                    "ces_components": {
                        "status": None,
                        "actions": None,
                        "latency": None,
                        "trunc": None,
                    },
                    "budgets_used": {},
                }

        default_summary = ces_versions_summary[CES_DEFAULT_VERSION]
        summary["ces_default_version"] = CES_DEFAULT_VERSION
        summary["ces"] = default_summary["ces"]
        summary["ces_reason"] = default_summary["ces_reason"]
        summary["ces_version"] = CES_DEFAULT_VERSION
        summary["ces_components"] = default_summary["ces_components"]
        summary["ces_versions"] = ces_versions_summary
        summary.update(_compute_ces_window_summary(items))

        status_code = 200
        response_payload = {"items": items, "summary": summary}
        _set_overview_cache(
            cache_key,
            json.dumps(response_payload, separators=(",", ":"), ensure_ascii=False),
        )
        return response_payload
    except HTTPException as exc:
        status_code = exc.status_code
        raise
    finally:
        duration_ms = int((perf_counter() - started_at) * 1000)
        _emit_metrics_endpoint_timing(
            endpoint="/api/v1/metrics/overview",
            method="GET",
            status_code=status_code,
            duration_ms=duration_ms,
            query_fingerprint=query_fingerprint,
            cache_hit=cache_hit_flag,
            cache_key_hash=cache_key_hash,
        )


@router.get("/alerts")
async def get_alerts(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna alertas de metricas cognitivas com paginacao.
    Args:
        start_date: filtra alertas a partir dessa data (YYYY-MM-DD)
        end_date: filtra alertas ate essa data (YYYY-MM-DD)
        limit: quantidade maxima de alertas a retornar
        offset: quantidade de alertas para pular (paginacao)
    """
    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date, "end_date")

    if end is None:
        end = datetime.utcnow().date()
    if start is None:
        start = end - timedelta(days=7)

    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    # Conta total para paginacao.
    count_stmt = (
        select(func.count(ObservationRecord.observation_id))
        .where(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
        .where(ObservationRecord.facts["metric_date"].astext >= start.isoformat())
        .where(ObservationRecord.facts["metric_date"].astext <= end.isoformat())
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    # Busca alertas paginados ordenados por timestamp DESC.
    stmt = (
        select(ObservationRecord)
        .where(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
        .where(ObservationRecord.facts["metric_date"].astext >= start.isoformat())
        .where(ObservationRecord.facts["metric_date"].astext <= end.isoformat())
        .order_by(desc(ObservationRecord.timestamp))
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()

    items = []
    for r in rows:
        facts = r.facts if isinstance(r.facts, dict) else {}
        metric_date = facts.get("metric_date", "")
        raw_reasons = facts.get("reasons", [])
        reasons = _dedup_and_sort_reasons(raw_reasons)

        items.append(
            {
                "observation_id": r.observation_id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "metric_date": metric_date,
                "reasons": reasons,
                "facts": _filter_facts(facts),
            }
        )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/runs")
async def get_runs(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna runs por process_id deduplicados pelo ultimo cognitive_loop_finished no range.
    """
    started_at = perf_counter()
    status_code = 500
    query_fingerprint = f"limit={limit}&offset={offset}&range=unknown"
    try:
        start = _parse_date(start_date, "start_date")
        end = _parse_date(end_date, "end_date")

        if end is None:
            end = datetime.utcnow().date()
        if start is None:
            start = end - timedelta(days=7)

        if start > end:
            raise HTTPException(status_code=400, detail="start_date must be <= end_date")

        if limit > METRICS_RUNS_LIMIT_MAX:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_type": "LimitTooHigh",
                    "limit_requested": limit,
                    "limit_max": METRICS_RUNS_LIMIT_MAX,
                },
            )

        range_days = (end - start).days + 1
        if range_days > METRICS_RUNS_RANGE_MAX_DAYS:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_type": "RangeTooLarge",
                    "range_days": range_days,
                    "range_max": METRICS_RUNS_RANGE_MAX_DAYS,
                },
            )

        query_fingerprint = _build_runs_query_fingerprint(limit, offset, start, end)

        count_stmt = (
            select(func.count(func.distinct(ObservationRecord.process_id)))
            .where(ObservationRecord.facts["event_type"].astext == "cognitive_loop_finished")
            .where(ObservationRecord.timestamp >= datetime.combine(start, datetime.min.time()))
            .where(ObservationRecord.timestamp < datetime.combine(end + timedelta(days=1), datetime.min.time()))
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(
                ObservationRecord.process_id,
                ObservationRecord.observation_id,
                ObservationRecord.timestamp,
                ObservationRecord.facts,
            )
            .where(ObservationRecord.facts["event_type"].astext == "cognitive_loop_finished")
            .where(ObservationRecord.timestamp >= datetime.combine(start, datetime.min.time()))
            .where(ObservationRecord.timestamp < datetime.combine(end + timedelta(days=1), datetime.min.time()))
            .order_by(desc(ObservationRecord.timestamp))
        )
        rows = (await db.execute(stmt)).all()

        latest_by_process: dict[str, tuple] = {}
        for process_id, observation_id, ts, facts in rows:
            if not process_id or process_id in latest_by_process:
                continue
            latest_by_process[process_id] = (observation_id, ts, facts if isinstance(facts, dict) else {})

        deduped = [
            {
                "process_id": pid,
                "observation_id": payload[0],
                "timestamp_finished": payload[1].isoformat() if payload[1] else None,
                "timestamp_finished_dt": payload[1],
                "facts": payload[2],
            }
            for pid, payload in latest_by_process.items()
        ]

        deduped.sort(key=lambda item: item["timestamp_finished"] or "", reverse=True)
        paged = deduped[offset : offset + limit]

        items = []
        for row in paged:
            # List endpoint permanece lean: sem calculo de latencia run-level pesada.
            ces_payload = _compute_ces_run_fields(row["facts"], None)
            items.append(
                {
                    "process_id": row["process_id"],
                    "timestamp_finished": row["timestamp_finished"],
                    "pipeline_status": ces_payload["pipeline_status"],
                    "ces_run": ces_payload["ces_run"],
                    "ces_run_version": ces_payload["ces_run_version"],
                    "ces_run_reason": ces_payload["ces_run_reason"],
                    "ces_run_components": ces_payload["ces_run_components"],
                    "latency_measured": ces_payload["latency_measured"],
                    "latency_pairs_inverted": ces_payload["latency_pairs_inverted"],
                }
            )

        status_code = 200
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException as exc:
        status_code = exc.status_code
        raise
    finally:
        duration_ms = int((perf_counter() - started_at) * 1000)
        _emit_metrics_endpoint_timing(
            endpoint="/api/v1/metrics/runs",
            method="GET",
            status_code=status_code,
            duration_ms=duration_ms,
            query_fingerprint=query_fingerprint,
        )


@router.get("/runs/{process_id}")
async def get_run_debug(
    process_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna visao de debug de um run por process_id.
    Fonte de verdade: ultimo cognitive_loop_finished no Postgres.
    """
    started_at = perf_counter()
    status_code = 500
    query_fingerprint = "process_id=present"
    try:
        stmt = (
            select(
                ObservationRecord.observation_id,
                ObservationRecord.timestamp,
                ObservationRecord.process_id,
                ObservationRecord.source_outcome_id,
                ObservationRecord.facts,
            )
            .where(ObservationRecord.process_id == process_id)
            .where(ObservationRecord.facts["event_type"].astext == "cognitive_loop_finished")
            .order_by(desc(ObservationRecord.timestamp))
            .limit(1)
        )
        row = (await db.execute(stmt)).first()
        if not row:
            raise HTTPException(status_code=404, detail="run_not_found")

        observation_id, ts, pid, source_outcome_id, facts = row
        facts = facts if isinstance(facts, dict) else {}
        ts_iso = ts.isoformat() if isinstance(ts, datetime) else None
        run_anchors = {}
        if isinstance(ts, datetime):
            ts_anchor = ts if ts.tzinfo is not None else ts.replace(tzinfo=timezone.utc)
            run_anchors[pid] = {"timestamp_finished": ts_anchor}
        run_latency = _build_run_latency_map(run_anchors).get(pid, {})
        ces_payload = _compute_ces_run_fields(facts, run_latency)

        outcome_row = _find_outcome_for_process(pid, source_outcome_id)
        outcome_error = outcome_row.get("error") if isinstance(outcome_row, dict) else {}
        if not isinstance(outcome_error, dict):
            outcome_error = {}
        execution_status = None
        if isinstance(outcome_row, dict):
            execution_status = outcome_row.get("execution_status")
        if not execution_status:
            execution_status = facts.get("execution_status")

        publish_receipt_stmt = (
            select(PublishReceipt)
            .where(PublishReceipt.process_id == pid)
            .order_by(desc(PublishReceipt.created_at))
            .limit(1)
        )
        publish_receipt = (await db.execute(publish_receipt_stmt)).scalars().first()

        manifest_decision_id = None
        publish_decision_id = None
        publish_receipt_id = None
        if publish_receipt:
            manifest_decision_id = publish_receipt.manifest_decision_id
            publish_decision_id = publish_receipt.publish_decision_id
            publish_receipt_id = publish_receipt.publish_decision_id

        if not manifest_decision_id and isinstance(facts.get("source_decision_id"), str):
            manifest_decision_id = facts.get("source_decision_id")

        missing_fields: list[str] = []
        if not isinstance(source_outcome_id, str) or not source_outcome_id:
            missing_fields.append("links.source_outcome_id")
        if execution_status is None:
            missing_fields.append("run_summary.execution_status")
        if publish_receipt is None:
            missing_fields.append("links.publish_decision_id")
            missing_fields.append("artifact_refs.publish_receipt_id")

        status_code = 200
        return {
            "run_summary": {
                "process_id": pid,
                "timestamp_finished": ts_iso,
                "pipeline_status": ces_payload["pipeline_status"],
                "execution_status": execution_status,
                "ces_run": ces_payload["ces_run"],
                "ces_run_version": ces_payload["ces_run_version"],
                "ces_run_components": ces_payload["ces_run_components"],
                "latency_measured": ces_payload["latency_measured"],
                "latency_pairs_used": ces_payload["latency_pairs_used"],
                "latency_pairs_ignored": ces_payload["latency_pairs_ignored"],
                "latency_pairs_inverted": ces_payload["latency_pairs_inverted"],
            },
            "links": {
                "observation_id": observation_id,
                "source_outcome_id": source_outcome_id,
                "source_decision_id": facts.get("source_decision_id"),
                "manifest_decision_id": manifest_decision_id,
                "publish_decision_id": publish_decision_id,
            },
            "artifact_refs": {
                "manifest_path": _manifest_path_from_decision_id(manifest_decision_id),
                "publish_receipt_id": publish_receipt_id,
            },
            "last_error": {
                "error_type": outcome_error.get("type") if outcome_error else None,
                "error_message": _sanitize_error_message(outcome_error.get("message")) if outcome_error else None,
            },
            "latency_breakdown": ces_payload.get("budgets_used", {}),
            "missing_fields": sorted(set(missing_fields)),
        }
    except HTTPException as exc:
        status_code = exc.status_code
        raise
    finally:
        duration_ms = int((perf_counter() - started_at) * 1000)
        _emit_metrics_endpoint_timing(
            endpoint="/api/v1/metrics/runs/{process_id}",
            method="GET",
            status_code=status_code,
            duration_ms=duration_ms,
            query_fingerprint=query_fingerprint,
            process_id=process_id,
        )
