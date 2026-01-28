import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any

from schemas.observation import Observation

STATE_LOG_PATH = "storage/state_log.jsonl"


def persist_state_from_observation(observation: Observation) -> None:
    """
    Persiste o estado derivado de uma observação em um arquivo de log.
    Args: 
        observation (Observation): A observação a partir da qual o estado será derivado.
    Returns:
        None
    """
    os.makedirs(os.path.dirname(STATE_LOG_PATH), exist_ok=True)

    state: Dict[str, Any] = {
        "state_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "process_id": observation.process_id,
        "source_observation_id": observation.observation_id,
        "facts": observation.facts,
    }

    with open(STATE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(state) + "\n")