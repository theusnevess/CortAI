import json
import os
from typing import Optional
from datetime import datetime

from app.schemas.observation import Observation

AUDIT_LOG_PATH = "storage/audit_log.jsonl"
OUTCOME_LOG_PATH = "storage/outcome_log.jsonl"
OBSERVATION_LOG_PATH = "storage/observation_log.jsonl"


def _outcome_exists(outcome_id: str) -> bool:
    """
    Verifica se um Outcome com o ID informado existe no audit_log.
    Garante rastreabilidade Observation -> Outcome.
    """
    def _scan_log(path: str, require_type: bool) -> bool:
        if not os.path.exists(path):
            return False
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


def persist_observation(observation: Observation) -> None:
    """
    Persiste uma Observation de forma append-only,
    apenas se o Outcome de origem existir.
    """
    if not _outcome_exists(observation.source_outcome_id):
        return

    os.makedirs(os.path.dirname(OBSERVATION_LOG_PATH), exist_ok=True)

    with open(OBSERVATION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(observation.dict()) + "\n")
