import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import ObservationRecord
from app.schemas.observation import Observation

try:
    import fcntl
except Exception:
    fcntl = None

AUDIT_LOG_PATH = "storage/audit_log.jsonl"
OUTCOME_LOG_PATH = "storage/outcome_log.jsonl"
OBSERVATION_LOG_PATH = "storage/observation_log.jsonl"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cortai_admin:cortai_secret_pass_123@db:5432/cortai_db",
)
_engine = None
_SessionLocal = None
logger = logging.getLogger(__name__)


@contextmanager
def _jsonl_lock(path: str, exclusive: bool):
    """
    Aplica lock em arquivo JSONL para leitura/escrita concorrente segura.
    Args:
        path: Caminho do arquivo JSONL.
        exclusive: True para lock exclusivo (escrita), False para lock compartilhado.
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


def _outcome_exists(outcome_id: str) -> bool:
    """
    Verifica se source_outcome_id existe em audit_log ou outcome_log.
    """

    def _scan_log(path: str, require_type: bool) -> bool:
        if not os.path.exists(path):
            return False
        with _jsonl_lock(path, exclusive=False):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except Exception:
                        continue
                    if require_type:
                        if record.get("type") == "Outcome" and record.get("outcome_id") == outcome_id:
                            return True
                    else:
                        if record.get("outcome_id") == outcome_id:
                            return True
        return False

    if _scan_log(AUDIT_LOG_PATH, require_type=True):
        return True
    return _scan_log(OUTCOME_LOG_PATH, require_type=False)


def _persist_observation_postgres(observation: Observation) -> None:
    """
    Persiste Observation no Postgres com semantica de upsert por observation_id.
    """
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(DATABASE_URL)
        _SessionLocal = sessionmaker(bind=_engine)

    session = _SessionLocal()
    try:
        ts = datetime.fromisoformat(observation.timestamp.replace("Z", "+00:00"))
        existing = session.get(ObservationRecord, observation.observation_id)
        if existing:
            existing.timestamp = ts
            existing.process_id = observation.process_id
            existing.source_outcome_id = observation.source_outcome_id
            existing.facts = observation.facts or {}
        else:
            session.add(
                ObservationRecord(
                    observation_id=observation.observation_id,
                    timestamp=ts,
                    process_id=observation.process_id,
                    source_outcome_id=observation.source_outcome_id,
                    facts=observation.facts or {},
                )
            )
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(
            "Failed to persist Observation in Postgres observation_id=%s err=%s",
            observation.observation_id,
            e,
        )
    finally:
        session.close()


def persist_observation(observation: Observation) -> None:
    """
    Persiste Observation em JSONL e Postgres mantendo guardrail de causalidade.
    """
    if not _outcome_exists(observation.source_outcome_id):
        return

    os.makedirs(os.path.dirname(OBSERVATION_LOG_PATH), exist_ok=True)

    with _jsonl_lock(OBSERVATION_LOG_PATH, exclusive=True):
        with open(OBSERVATION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation.dict()) + "\n")

    _persist_observation_postgres(observation)
