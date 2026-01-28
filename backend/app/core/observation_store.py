import json
import os
from typing import Optional
from datetime import datetime

from schemas.observation import Observation 

# Define os caminhos dos arquivos de log
AUDIT_LOG_PATH = "storage/audit_log.jsonl"
OBSERVATION_LOG_PATH = "storage/observation_log.jsonl"


def _outcome_exists(outcome_id: str) -> bool:
    """
    Verifica se um resultado com o ID fornecido existe no log de auditoria.
    Args:
        outcome_id (str): O ID do resultado a ser verificado.   
    Returns:
        bool: True se o resultado existir, False caso contrário.
    """
    if not os.path.exists(AUDIT_LOG_PATH):
        return False

    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record.get("type") == "Outcome" and record.get("outcome_id") == outcome_id:
                return True
    return False


def persist_observation(observation: Observation) -> None:
    """
    Persiste uma observação no log de observações se o resultado associado existir.
    Args:
        observation (Observation): A observação a ser persistida.   
    """
    if not _outcome_exists(observation.source_outcome_id):
        return

    os.makedirs(os.path.dirname(OBSERVATION_LOG_PATH), exist_ok=True)

    with open(OBSERVATION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(observation.dict()) + "\n")
