import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any
from contextlib import contextmanager

try:
    import fcntl
except Exception:  
    fcntl = None

from app.schemas.observation import Observation

STATE_LOG_PATH = "storage/state_log.jsonl"


@contextmanager
def _jsonl_lock(path: str, exclusive: bool):
    """
    Context manager para criar um bloqueio baseado em arquivo para operações de leitura e escrita em arquivos JSONL. O bloqueio é implementado usando a biblioteca fcntl, que é compatível com sistemas Unix. O bloqueio pode ser exclusivo (para escrita) ou compartilhado (para leitura), dependendo do parâmetro 'exclusive'. O contexto garante que o bloqueio seja adquirido antes de acessar o arquivo e liberado após a operação, mesmo que ocorra uma exceção durante o acesso ao arquivo.      
    Args:
        path (str): O caminho do arquivo JSONL para o qual o bloqueio deve ser criado.
        exclusive (bool): Indica se o bloqueio deve ser exclusivo (True) para escrita ou compartilhado (False) para leitura.
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

    with _jsonl_lock(STATE_LOG_PATH, exclusive=True):
        with open(STATE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(state) + "\n")
