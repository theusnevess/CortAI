import json
import logging
import os
import uuid
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import CognitiveMetricsDaily, ObservationRecord
from app.observations import persist_observation
from app.schemas.observation import Observation
from app.state_from_observation import persist_state_from_observation

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cortai_admin:cortai_secret_pass_123@db:5432/cortai_db",
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

OUTCOME_LOG_PATH = "storage/outcome_log.jsonl"

logger = logging.getLogger(__name__)

try:
    import fcntl
except Exception:
    fcntl = None


@contextmanager
def _jsonl_lock(path: str, exclusive: bool):
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


def _alert_already_emitted(session, metric_date: date) -> bool:
    target = metric_date.isoformat()
    existing = (
        session.query(ObservationRecord)
        .filter(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
        .filter(ObservationRecord.facts["metric_date"].astext == target)
        .first()
    )
    return existing is not None


def _safe_int(value) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def aggregate_daily_metrics_for_date(metric_date: date) -> dict:
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
        actions_total = 0
        action_counter: Counter[str] = Counter()

        for row in loop_finished:
            facts = row.facts or {}
            pipeline_status = facts.get("pipeline_status")
            termination_reason = facts.get("termination_reason")
            execution_status = facts.get("execution_status")

            if execution_status == "blocked":
                blocked_runs += 1
            elif pipeline_status == "failed" or termination_reason == "video_failed":
                failed_runs += 1
            elif pipeline_status == "completed" or termination_reason == "pipeline_complete":
                completed_runs += 1

            actions_total += _safe_int(facts.get("actions_executed"))
            action_type = facts.get("last_action_type") or "unknown"
            action_counter[action_type] += 1

        avg_actions = Decimal("0.00")
        if total_runs > 0:
            avg_actions = (Decimal(actions_total) / Decimal(total_runs)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        payload = {
            "metric_date": metric_date,
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "blocked_runs": blocked_runs,
            "avg_actions_executed": avg_actions,
            "last_action_type_distribution": dict(action_counter),
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
            existing.avg_actions_executed = payload["avg_actions_executed"]
            existing.last_action_type_distribution = payload["last_action_type_distribution"]
        else:
            session.add(
                CognitiveMetricsDaily(
                    id=uuid.uuid4(),
                    metric_date=metric_date,
                    total_runs=payload["total_runs"],
                    completed_runs=payload["completed_runs"],
                    failed_runs=payload["failed_runs"],
                    blocked_runs=payload["blocked_runs"],
                    avg_actions_executed=payload["avg_actions_executed"],
                    last_action_type_distribution=payload["last_action_type_distribution"],
                )
            )
        session.commit()

        total_runs = payload["total_runs"]
        blocked_runs = payload["blocked_runs"]
        failed_runs = payload["failed_runs"]
        failed_ratio = (failed_runs / total_runs) if total_runs else 0.0

        if total_runs and (blocked_runs > 0 or failed_ratio > 0.2):
            if not _alert_already_emitted(session, metric_date):
                process_id = f"P_METRICS_DAILY_{metric_date.isoformat()}"
                source_outcome_id = str(uuid.uuid4())
                _append_minimal_outcome(source_outcome_id, process_id)
                reasons = []
                if blocked_runs > 0:
                    reasons.append("blocked_runs")
                if failed_ratio > 0.2:
                    reasons.append("failed_ratio")
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
                        "reasons": reasons,
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
                    "COGNITIVE_METRICS alert emitted date=%s reasons=%s",
                    metric_date.isoformat(),
                    ",".join(reasons),
                )
        return payload
    finally:
        session.close()
