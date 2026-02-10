import json
import os
from typing import Optional
from datetime import datetime
from contextlib import contextmanager

# Importa fcntl para bloqueio de arquivos, mas lida com a ausência em sistemas não Unix (como Windows) definindo fcntl como None se a importação falhar. 
# O bloqueio de arquivos é usado para garantir que apenas um processo acesse um arquivo JSONL específico por vez, evitando corrupção de dados em cenários de concorrência.
try:
    import fcntl
except Exception:  
    fcntl = None

from app.schemas.observation import Observation

AUDIT_LOG_PATH = "storage/audit_log.jsonl"
OUTCOME_LOG_PATH = "storage/outcome_log.jsonl"
OBSERVATION_LOG_PATH = "storage/observation_log.jsonl"


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


def _outcome_exists(outcome_id: str) -> bool:
    """
    Verifica se um Outcome com o ID informado existe no audit_log.
    Garante rastreabilidade Observation -> Outcome.
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


def persist_observation(observation: Observation) -> None:
    """
    Persiste uma Observation de forma append-only,
    apenas se o Outcome de origem existir.
    """
    if not _outcome_exists(observation.source_outcome_id):
        return

    os.makedirs(os.path.dirname(OBSERVATION_LOG_PATH), exist_ok=True)

    with _jsonl_lock(OBSERVATION_LOG_PATH, exclusive=True):
        with open(OBSERVATION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation.dict()) + "\n")
