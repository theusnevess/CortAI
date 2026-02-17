import json
import logging
import math
import os
import uuid
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.db.models import CognitiveMetricsDaily, MetricsEndpointDaily, ObservationRecord
from app.observations import persist_observation
from app.schemas.observation import Observation
from app.state_from_observation import persist_state_from_observation

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cortai_admin:cortai_secret_pass_123@db:5432/cortai_db",
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

DECISION_LOG_PATH = "storage/decision_log.jsonl"
OUTCOME_LOG_PATH = "storage/outcome_log.jsonl"

logger = logging.getLogger(__name__)

CES_V1_REASON = "ces_regression:CES_v1"
METRICS_ENDPOINT_TIMING_EVENT = "metrics_endpoint_timing"
METRICS_SLO_ALERT_EVENT = "metrics_slo_alert"
METRICS_SLO_THRESHOLDS = {
    "/api/v1/metrics/runs": {"p95_ms": 800, "p99_ms": 1500},
    "/api/v1/metrics/runs/{process_id}": {"p95_ms": 400, "p99_ms": 900},
}
CES_LATENCY_ACTION_WHITELIST = {
    "collect_video",
    "extract_audio",
    "segment_audio",
    "transcribe_segments",
    "write_artifact",
    "publish_manifest",
}

try:
    import fcntl
except Exception:
    fcntl = None


@contextmanager
def _jsonl_lock(path: str, exclusive: bool):
    """
    Bloqueia arquivo JSONL para leitura/escrita concorrente segura.
    Args:
        path (str): Caminho do arquivo JSONL.
        exclusive (bool): True para lock exclusivo, False para compartilhado.
    """
    lock_dir = os.path.join("storage", "locks")
    os.makedirs(lock_dir, exist_ok=True)
    lock_path = os.path.join(lock_dir, f"{os.path.basename(path)}.lock")
    with open(lock_path, "a+", encoding="utf-8") as lock_file:
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
    Adiciona outcome minimo para manter guardrail de observacoes.
    Args:
        outcome_id (str): ID do outcome.
        process_id (str): ID do processo.
    """
    os.makedirs(os.path.dirname(OUTCOME_LOG_PATH), exist_ok=True)
    record = {
        "outcome_id": outcome_id,
        "timestamp": datetime.utcnow().isoformat(),
        "process_id": process_id,
        "source_decision_id": "",
        "execution_status": "external",
        "metrics": {"origin": "telemetry"},
    }
    with _jsonl_lock(OUTCOME_LOG_PATH, exclusive=True):
        with open(OUTCOME_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


def _alert_already_emitted(session, metric_date: date, reason: str) -> bool:
    """
    Verifica se ja existe alerta para a combinacao (data, motivo).
    Args:
        session: Sessao SQLAlchemy.
        metric_date (date): Data alvo.
        reason (str): Motivo do alerta.
    """
    target = metric_date.isoformat()
    rows = (
        session.query(ObservationRecord)
        .filter(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
        .filter(ObservationRecord.facts["metric_date"].astext == target)
        .all()
    )
    for row in rows:
        facts = row.facts or {}
        reasons = facts.get("reasons")
        if isinstance(reasons, list) and reason in reasons:
            return True
    return False


def _alert_count_for_date(session, metric_date: date) -> int:
    """
    Conta alertas existentes para a data.
    Args:
        session: Sessao SQLAlchemy.
        metric_date (date): Data alvo.
    Returns:
        int: Quantidade de alertas no dia.
    """
    target = metric_date.isoformat()
    count = (
        session.query(ObservationRecord)
        .filter(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
        .filter(ObservationRecord.facts["metric_date"].astext == target)
        .count()
    )
    return int(count or 0)


def _slo_alert_already_emitted(session, metric_date: date, endpoint: str, reason: str) -> bool:
    """
    Verifica dedupe de alerta SLO por (metric_date, endpoint, reason).
    """
    target = metric_date.isoformat()
    rows = (
        session.query(ObservationRecord)
        .filter(ObservationRecord.facts["event_type"].astext == METRICS_SLO_ALERT_EVENT)
        .filter(ObservationRecord.facts["metric_date"].astext == target)
        .all()
    )
    for row in rows:
        facts = row.facts or {}
        if str(facts.get("endpoint") or "") != endpoint:
            continue
        reasons = facts.get("reasons")
        if isinstance(reasons, list) and reason in reasons:
            return True
    return False


def _slo_alert_count_for_date(session, metric_date: date) -> int:
    """
    Conta alertas SLO ja emitidos no dia.
    """
    target = metric_date.isoformat()
    count = (
        session.query(ObservationRecord)
        .filter(ObservationRecord.facts["event_type"].astext == METRICS_SLO_ALERT_EVENT)
        .filter(ObservationRecord.facts["metric_date"].astext == target)
        .count()
    )
    return int(count or 0)


def _safe_int(value) -> int:
    """
    Converte valor para int com fallback seguro.
    """
    try:
        return int(value)
    except Exception:
        return 0


def _safe_float(value, default: float = 0.0) -> float:
    """
    Converte valor para float com fallback seguro.
    """
    try:
        return float(value)
    except Exception:
        return default


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """
    Limita valor numerico no intervalo [min_value, max_value].
    """
    return max(min_value, min(max_value, value))


def _get_int_env(name: str, default: int) -> int:
    """
    Le inteiro de env com fallback deterministico.
    """
    raw = os.getenv(name)
    try:
        return int(raw) if raw is not None else default
    except Exception:
        return default


def _compute_ces_v1(
    total_runs: int,
    failed_runs: int,
    blocked_runs: int,
    truncated_runs: int,
    avg_actions_executed: float,
    latency_by_action: dict[str, dict[str, int]],
) -> float | None:
    """
    Calcula CES_v1 diario de forma deterministica.
    """
    if total_runs <= 0:
        return None

    r_b = blocked_runs / total_runs
    r_f = failed_runs / total_runs
    r_t = truncated_runs / total_runs
    s_status = _clamp(1.0 - (1.0 * r_b + 0.6 * r_f + 0.3 * r_t))
    s_actions = _clamp((6.0 - avg_actions_executed) / (6.0 - 1.0))
    s_trunc = _clamp(1.0 - r_t)

    eligible: dict[str, dict[str, int]] = {}
    total_n = 0
    for action_name, payload in (latency_by_action or {}).items():
        if action_name not in CES_LATENCY_ACTION_WHITELIST:
            continue
        n_obs = _safe_int(payload.get("n"))
        p95_ms = _safe_int(payload.get("p95_ms"))
        if n_obs < 10 or p95_ms <= 0:
            continue
        budget_ms = int(math.ceil(p95_ms * 1.10))
        eligible[action_name] = {"n": n_obs, "p95_ms": p95_ms, "budget_ms": budget_ms}
        total_n += n_obs

    if total_n <= 0:
        s_latency = 1.0
    else:
        s_latency = 0.0
        for payload in eligible.values():
            weight = payload["n"] / total_n
            action_score = _clamp(payload["budget_ms"] / payload["p95_ms"])
            s_latency += weight * action_score
        s_latency = _clamp(s_latency)

    ces = 100.0 * (0.55 * s_status + 0.15 * s_actions + 0.25 * s_latency + 0.05 * s_trunc)
    return round(_clamp(ces, 0.0, 100.0), 2)


def _parse_ts(value: str) -> datetime | None:
    """
    Faz parse de timestamp ISO em UTC.
    """
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _read_jsonl_rows(path: str) -> list[dict[str, Any]]:
    """
    Le registros JSONL com lock compartilhado.
    """
    if not os.path.exists(path):
        return []
    rows: list[dict[str, Any]] = []
    with _jsonl_lock(path, exclusive=False):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        rows.append(obj)
                except Exception:
                    continue
    return rows


def _p95(values: list[int]) -> int:
    """
    Calcula p95 por nearest-rank.
    """
    if not values:
        return 0
    values_sorted = sorted(values)
    k = int(0.95 * (len(values_sorted) - 1))
    return int(values_sorted[k])


def _percentile(values: list[int], p: float) -> int:
    """
    Calcula percentil por nearest-rank em [0, 1].
    """
    if not values:
        return 0
    if p <= 0:
        return int(min(values))
    if p >= 1:
        return int(max(values))
    values_sorted = sorted(values)
    k = int(p * (len(values_sorted) - 1))
    return int(values_sorted[k])


def _to_endpoint_slug(endpoint: str) -> str:
    """
    Converte endpoint em slug seguro para process_id.
    """
    raw = str(endpoint or "unknown")
    return (
        raw.replace("/", "_")
        .replace("{", "")
        .replace("}", "")
        .replace("-", "_")
        .strip("_")
        or "unknown"
    )


def _aggregate_metrics_endpoint_daily_and_alerts(
    session,
    metric_date: date,
    rows: list[ObservationRecord],
) -> list[dict[str, Any]]:
    """
    Agrega p50/p95/p99 e error_rate por endpoint e emite alertas SLO idempotentes.
    """
    if not inspect(session.bind).has_table("metrics_endpoint_daily"):
        return []

    timings_by_endpoint: dict[str, list[dict[str, int]]] = defaultdict(list)
    for row in rows:
        facts = row.facts if isinstance(row.facts, dict) else {}
        if facts.get("event_type") != METRICS_ENDPOINT_TIMING_EVENT:
            continue
        endpoint = str(facts.get("endpoint") or "").strip()
        if not endpoint:
            continue
        duration_ms = _safe_int(facts.get("duration_ms"))
        status_code = _safe_int(facts.get("status_code"))
        timings_by_endpoint[endpoint].append(
            {"duration_ms": max(0, duration_ms), "status_code": status_code}
        )

    # Recalcula deterministamente para a data alvo.
    (
        session.query(MetricsEndpointDaily)
        .filter(MetricsEndpointDaily.metric_date == metric_date)
        .delete(synchronize_session=False)
    )

    aggregate_rows: list[dict[str, Any]] = []
    for endpoint, entries in sorted(timings_by_endpoint.items()):
        durations = [item["duration_ms"] for item in entries]
        total = len(entries)
        errors = sum(1 for item in entries if item["status_code"] >= 400)
        error_rate = round((errors / total), 4) if total > 0 else 0.0
        payload = {
            "metric_date": metric_date.isoformat(),
            "endpoint": endpoint,
            "count_requests": total,
            "p50_ms": _percentile(durations, 0.50),
            "p95_ms": _percentile(durations, 0.95),
            "p99_ms": _percentile(durations, 0.99),
            "error_rate": error_rate,
        }
        aggregate_rows.append(payload)
        session.add(
            MetricsEndpointDaily(
                id=uuid.uuid4(),
                metric_date=metric_date,
                endpoint=endpoint,
                count_requests=payload["count_requests"],
                p50_ms=payload["p50_ms"],
                p95_ms=payload["p95_ms"],
                p99_ms=payload["p99_ms"],
                error_rate=Decimal(str(payload["error_rate"])).quantize(Decimal("0.0001")),
            )
        )

    session.commit()

    max_alerts_raw = os.getenv("METRICS_ALERT_MAX_PER_DAY", "5")
    try:
        max_alerts_per_day = int(max_alerts_raw)
    except Exception:
        max_alerts_per_day = 5

    for payload in aggregate_rows:
        thresholds = METRICS_SLO_THRESHOLDS.get(payload["endpoint"])
        if not thresholds:
            continue

        reasons: list[str] = []
        if payload["p95_ms"] > thresholds["p95_ms"]:
            reasons.append("p95_slo_breach")
        if payload["p99_ms"] > thresholds["p99_ms"]:
            reasons.append("p99_slo_breach")
        if payload["error_rate"] > 0.01:
            reasons.append("error_rate_breach")
        if not reasons:
            continue

        reasons_to_emit = [
            reason
            for reason in reasons
            if not _slo_alert_already_emitted(session, metric_date, payload["endpoint"], reason)
        ]
        if not reasons_to_emit:
            continue
        if _slo_alert_count_for_date(session, metric_date) >= max_alerts_per_day:
            break

        endpoint_slug = _to_endpoint_slug(payload["endpoint"])
        process_id = f"P_METRICS_SLO_{metric_date.isoformat()}_{endpoint_slug}"
        source_outcome_id = str(uuid.uuid4())
        _append_minimal_outcome(source_outcome_id, process_id)
        observation = Observation(
            observation_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            process_id=process_id,
            source_outcome_id=source_outcome_id,
            facts={
                "event_type": METRICS_SLO_ALERT_EVENT,
                "metric_date": metric_date.isoformat(),
                "endpoint": payload["endpoint"],
                "count_requests": payload["count_requests"],
                "p95_ms": payload["p95_ms"],
                "p99_ms": payload["p99_ms"],
                "error_rate": payload["error_rate"],
                "thresholds": thresholds,
                "reasons": reasons_to_emit,
            },
        )
        persist_observation(observation)
        try:
            persist_state_from_observation(observation)
        except Exception as e:
            logger.error(
                "METRICS_SLO alert state persist failed date=%s endpoint=%s err=%s",
                metric_date.isoformat(),
                payload["endpoint"],
                e,
            )
        logger.warning(
            "METRICS_SLO alert emitted date=%s endpoint=%s reasons=%s",
            metric_date.isoformat(),
            payload["endpoint"],
            reasons_to_emit,
        )

    return aggregate_rows


def aggregate_daily_metrics_for_date(metric_date: date) -> dict:
    """
    Agrega metricas diarias a partir de Observations (Postgres).
    Aplica dedupe por process_id e faz upsert em cognitive_metrics_daily.
    """
    start_dt = datetime.combine(metric_date, time.min)
    end_dt = start_dt + timedelta(days=1)

    session = SessionLocal()
    try:
        rows = (
            session.query(ObservationRecord)
            .filter(ObservationRecord.timestamp >= start_dt)
            .filter(ObservationRecord.timestamp < end_dt)
            .all()
        )

        loop_finished = [
            row
            for row in rows
            if isinstance(row.facts, dict)
            and row.facts.get("event_type") == "cognitive_loop_finished"
        ]

        latest_by_process: dict[str, ObservationRecord] = {}
        for row in loop_finished:
            pid = row.process_id
            if not pid:
                continue
            prev = latest_by_process.get(pid)
            if prev is None or (row.timestamp and row.timestamp > prev.timestamp):
                latest_by_process[pid] = row

        loop_finished = list(latest_by_process.values())

        total_runs = len(loop_finished)
        completed_runs = 0
        failed_runs = 0
        blocked_runs = 0
        truncated_runs = 0
        actions_total = 0
        action_counter: Counter[str] = Counter()

        max_steps_env = os.getenv("COGNITIVE_LOOP_MAX_STEPS", "10")
        try:
            max_steps = int(max_steps_env)
        except Exception:
            max_steps = 10

        for row in loop_finished:
            facts = row.facts or {}
            pipeline_status = facts.get("pipeline_status")
            termination_reason = facts.get("termination_reason")
            execution_status = facts.get("execution_status")

            if execution_status == "blocked":
                blocked_runs += 1
            elif pipeline_status == "failed" or termination_reason == "video_failed":
                failed_runs += 1
            elif pipeline_status in ("completed", "published") or termination_reason == "pipeline_complete":
                completed_runs += 1

            actions_total += _safe_int(facts.get("actions_executed"))
            action_type = facts.get("last_action_type") or "unknown"
            action_counter[action_type] += 1

            terminated = facts.get("terminated")
            actions_executed = _safe_int(facts.get("actions_executed"))
            if (
                execution_status == "success"
                and terminated is not True
                and actions_executed >= max_steps
            ):
                truncated_runs += 1

        avg_actions = Decimal("0.00")
        if total_runs > 0:
            avg_actions = (Decimal(actions_total) / Decimal(total_runs)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        truncated_ratio = Decimal("0.00")
        if total_runs > 0:
            truncated_ratio = (Decimal(truncated_runs) / Decimal(total_runs)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        # latency_by_action a partir de decision/outcome logs (janela UTC)
        decisions = _read_jsonl_rows(DECISION_LOG_PATH)
        outcomes = _read_jsonl_rows(OUTCOME_LOG_PATH)

        decision_ts_by_id: dict[str, datetime] = {}
        for d in decisions:
            ts = _parse_ts(str(d.get("timestamp", "")))
            if not ts:
                continue
            if not (start_dt <= ts < end_dt):
                continue
            did = d.get("decision_id")
            if isinstance(did, str) and did:
                decision_ts_by_id[did] = ts

        latencies_ms: dict[str, list[int]] = defaultdict(list)
        for o in outcomes:
            ots = _parse_ts(str(o.get("timestamp", "")))
            if not ots:
                continue
            if not (start_dt <= ots < end_dt):
                continue
            did = o.get("source_decision_id")
            if not isinstance(did, str) or did not in decision_ts_by_id:
                continue
            metrics = o.get("metrics") or {}
            action_type = metrics.get("last_action_type") or "unknown"
            dts = decision_ts_by_id[did]
            delta_ms = int((ots - dts).total_seconds() * 1000)
            if delta_ms < 0:
                continue
            latencies_ms[str(action_type)].append(delta_ms)

        latency_by_action: dict[str, dict[str, int]] = {}
        for action_type, values in latencies_ms.items():
            if not values:
                continue
            avg_ms = int(sum(values) / max(len(values), 1))
            latency_by_action[action_type] = {
                "n": len(values),
                "avg_ms": avg_ms,
                "p95_ms": _p95(values),
            }

        payload = {
            "metric_date": metric_date,
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "blocked_runs": blocked_runs,
            "truncated_runs": truncated_runs,
            "truncated_ratio": truncated_ratio,
            "avg_actions_executed": avg_actions,
            "last_action_type_distribution": dict(action_counter),
            "latency_by_action": latency_by_action,
        }

        existing = (
            session.query(CognitiveMetricsDaily)
            .filter(CognitiveMetricsDaily.metric_date == metric_date)
            .one_or_none()
        )
        if existing:
            existing.total_runs = payload["total_runs"]
            existing.completed_runs = payload["completed_runs"]
            existing.failed_runs = payload["failed_runs"]
            existing.blocked_runs = payload["blocked_runs"]
            existing.truncated_runs = payload["truncated_runs"]
            existing.truncated_ratio = payload["truncated_ratio"]
            existing.avg_actions_executed = payload["avg_actions_executed"]
            existing.last_action_type_distribution = payload["last_action_type_distribution"]
            existing.latency_by_action = payload["latency_by_action"]
        else:
            session.add(
                CognitiveMetricsDaily(
                    id=uuid.uuid4(),
                    metric_date=metric_date,
                    total_runs=payload["total_runs"],
                    completed_runs=payload["completed_runs"],
                    failed_runs=payload["failed_runs"],
                    blocked_runs=payload["blocked_runs"],
                    truncated_runs=payload["truncated_runs"],
                    truncated_ratio=payload["truncated_ratio"],
                    avg_actions_executed=payload["avg_actions_executed"],
                    last_action_type_distribution=payload["last_action_type_distribution"],
                    latency_by_action=payload["latency_by_action"],
                )
            )
        session.commit()

        total_runs = payload["total_runs"]
        blocked_runs = payload["blocked_runs"]
        failed_runs = payload["failed_runs"]
        failed_ratio = (failed_runs / total_runs) if total_runs else 0.0

        if total_runs and (blocked_runs > 0 or failed_ratio > 0.2):
            max_alerts_raw = os.getenv("COGNITIVE_ALERT_MAX_PER_DAY", "5")
            try:
                max_alerts_per_day = int(max_alerts_raw)
            except Exception:
                max_alerts_per_day = 5

            reasons_to_emit: list[str] = []
            if blocked_runs > 0:
                reasons_to_emit.append("blocked_runs")
            if failed_ratio > 0.2:
                reasons_to_emit.append("failed_ratio")

            for reason in reasons_to_emit:
                current_alerts = _alert_count_for_date(session, metric_date)
                if current_alerts >= max_alerts_per_day:
                    break
                if _alert_already_emitted(session, metric_date, reason):
                    continue

                process_id = f"P_METRICS_DAILY_{metric_date.isoformat()}"
                source_outcome_id = str(uuid.uuid4())
                _append_minimal_outcome(source_outcome_id, process_id)
                observation = Observation(
                    observation_id=str(uuid.uuid4()),
                    timestamp=datetime.utcnow().isoformat(),
                    process_id=process_id,
                    source_outcome_id=source_outcome_id,
                    facts={
                        "event_type": "cognitive_metrics_alert",
                        "metric_date": metric_date.isoformat(),
                        "total_runs": total_runs,
                        "completed_runs": payload["completed_runs"],
                        "failed_runs": failed_runs,
                        "blocked_runs": blocked_runs,
                        "failed_ratio": round(failed_ratio, 4),
                        "threshold": 0.2,
                        "reasons": [reason],
                    },
                )
                persist_observation(observation)
                try:
                    persist_state_from_observation(observation)
                except Exception as e:
                    logger.error(
                        "COGNITIVE_METRICS alert state persist failed date=%s err=%s",
                        metric_date.isoformat(),
                        e,
                    )
                logger.warning(
                    "COGNITIVE_METRICS alert emitted date=%s reason=%s",
                    metric_date.isoformat(),
                    reason,
                )

        # Avalia regressao de CES_v1 por janela movel (sem heuristica).
        ces_alert_enabled = os.getenv("COGNITIVE_ALERT_CES_ENABLED", "1") == "1"
        if ces_alert_enabled:
            ces_threshold = _safe_float(os.getenv("COGNITIVE_ALERT_CES_THRESHOLD", "85"), 85.0)
            ces_bad_days = _get_int_env("COGNITIVE_ALERT_CES_BAD_DAYS", 3)
            ces_window_days = _get_int_env("COGNITIVE_ALERT_CES_WINDOW_DAYS", 7)
            if ces_bad_days < 1:
                ces_bad_days = 1
            if ces_window_days < ces_bad_days:
                ces_window_days = ces_bad_days

            win_start = metric_date - timedelta(days=ces_window_days - 1)
            window_rows = (
                session.query(CognitiveMetricsDaily)
                .filter(CognitiveMetricsDaily.metric_date >= win_start)
                .filter(CognitiveMetricsDaily.metric_date <= metric_date)
                .order_by(CognitiveMetricsDaily.metric_date.asc())
                .all()
            )

            ces_samples: list[dict[str, Any]] = []
            days_with_runs = 0
            bad_days_in_window = 0
            for row in window_rows:
                row_total_runs = _safe_int(row.total_runs)
                row_ces = _compute_ces_v1(
                    total_runs=row_total_runs,
                    failed_runs=_safe_int(row.failed_runs),
                    blocked_runs=_safe_int(row.blocked_runs),
                    truncated_runs=_safe_int(getattr(row, "truncated_runs", 0)),
                    avg_actions_executed=_safe_float(getattr(row, "avg_actions_executed", 0)),
                    latency_by_action=(getattr(row, "latency_by_action", {}) or {}),
                )
                if row_total_runs > 0:
                    days_with_runs += 1
                    if row_ces is not None:
                        ces_samples.append({"date": row.metric_date.isoformat(), "ces": row_ces})
                    if row_ces is not None and row_ces < ces_threshold:
                        bad_days_in_window += 1

            if days_with_runs >= 7 and bad_days_in_window >= ces_bad_days:
                max_alerts_raw = os.getenv("COGNITIVE_ALERT_MAX_PER_DAY", "5")
                try:
                    max_alerts_per_day = int(max_alerts_raw)
                except Exception:
                    max_alerts_per_day = 5

                current_alerts = _alert_count_for_date(session, metric_date)
                if (
                    current_alerts < max_alerts_per_day
                    and not _alert_already_emitted(session, metric_date, CES_V1_REASON)
                ):
                    process_id = f"P_METRICS_DAILY_{metric_date.isoformat()}"
                    source_outcome_id = str(uuid.uuid4())
                    _append_minimal_outcome(source_outcome_id, process_id)
                    observation = Observation(
                        observation_id=str(uuid.uuid4()),
                        timestamp=datetime.utcnow().isoformat(),
                        process_id=process_id,
                        source_outcome_id=source_outcome_id,
                        facts={
                            "event_type": "cognitive_metrics_alert",
                            "metric_date": metric_date.isoformat(),
                            "reasons": [CES_V1_REASON],
                            "ces_version": "CES_v1",
                            "threshold": ces_threshold,
                            "window_days": ces_window_days,
                            "required_bad_days": ces_bad_days,
                            "bad_days_in_window": bad_days_in_window,
                            "days_with_runs_in_window": days_with_runs,
                            "ces_samples": ces_samples[-ces_window_days:],
                        },
                    )
                    persist_observation(observation)
                    try:
                        persist_state_from_observation(observation)
                    except Exception as e:
                        logger.error(
                            "COGNITIVE_METRICS ces alert state persist failed date=%s err=%s",
                            metric_date.isoformat(),
                            e,
                        )
                    logger.warning(
                        "COGNITIVE_METRICS alert emitted date=%s reason=%s bad_days=%s window=%s",
                        metric_date.isoformat(),
                        CES_V1_REASON,
                        bad_days_in_window,
                        ces_window_days,
                    )
        endpoint_daily_rows = _aggregate_metrics_endpoint_daily_and_alerts(session, metric_date, rows)
        payload["metrics_endpoint_daily"] = endpoint_daily_rows
        return payload
    finally:
        session.close()
