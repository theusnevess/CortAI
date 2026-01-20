import json # Manipula objetos json 
import os # Interaje com o sistema operacional
import uuid 
from datetime import datetime
from typing import Any, Dict, Optional # Tipagem para tipos genéricos

AUDIT_LOG_PATH = "storage/audit_log.jsonl" # Caminho do arquivo de log de auditoria
PROCESS_ID_PATH = "storage/process_id.txt" # Caminho do arquivo de ID do processo


def _now_iso():
    """
    Retorna o timestamp atual em formato ISO 8601
    """
    return datetime.utcnow().isoformat()


def _append(record: Dict[str, Any]):
    """
    Anexa um registro ao arquivo de log de auditoria
    """
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _load_last_state_id() -> Optional[str]:
    """
    Carrega o ID do último estado registrado no log de auditoria
    """
    if not os.path.exists(AUDIT_LOG_PATH):
        return None

    last_state_id = None
    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line) # Carrega cada linha como um objeto JSON
            if record.get("type") == "State": # Verifica se o tipo do registro é "State"
                last_state_id = record.get("state_id") # Atualiza o último ID do estado
    return last_state_id


def _load_last_outcome_id() -> Optional[str]:
    """
    Carrega o ID do último resultado registrado no log de auditoria
    """
    if not os.path.exists(AUDIT_LOG_PATH):
        return None

    last_outcome_id = None
    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record.get("type") == "Outcome": # Verifica se o tipo do registro é "Outcome"
                last_outcome_id = record.get("outcome_id") # Atualiza o último ID do resultado
    return last_outcome_id


def _load_or_create_process_id() -> str:
    """
    Carrega o ID do processo de um arquivo ou cria um novo se não existir
    """
    os.makedirs(os.path.dirname(PROCESS_ID_PATH), exist_ok=True)

    # Tenta carregar o ID do processo existente
    if os.path.exists(PROCESS_ID_PATH):
        with open(PROCESS_ID_PATH, "r", encoding="utf-8") as f:
            value = f.read().strip()
            if value:
                return value

    # Cria um novo ID do processo
    process_id = str(uuid.uuid4())
    with open(PROCESS_ID_PATH, "w", encoding="utf-8") as f:
        f.write(process_id) # Salva o novo ID do processo no arquivo
    return process_id


def run_cognitive_cycle(observation_payload: Dict[str, Any], executor_callback):
    """
    Executa um ciclo cognitivo completo: registra o estado, toma uma decisão,
    executa a ação e registra o resultado.
    """
    previous_state_id = _load_last_state_id()
    previous_outcome_id = _load_last_outcome_id()
    process_id = _load_or_create_process_id()

    # Registra o novo estado
    state_id = str(uuid.uuid4())
    state = {
        "state_id": state_id,
        "timestamp": _now_iso(),
        "process_id": process_id,
        "observation_payload": observation_payload,
        "previous_state_id": previous_state_id,
        "previous_outcome_id": previous_outcome_id,
    }
    _append({"type": "State", **state}) # Anexa o registro do estado ao log de auditoria

    # Toma uma decisão determinística (NOOP) com base no estado
    decision_id = str(uuid.uuid4())
    decision = {
        "decision_id": decision_id,
        "state_id": state_id,
        "decision_type": "NOOP",
        "rationale": "Initial deterministic decision",
        "timestamp": _now_iso(),
    }
    _append({"type": "Decision", **decision}) 

    # Executa a ação decidida usando o callback fornecido
    feedback = executor_callback(
        decision_id=decision_id,
        action_type="NOOP",
        action_payload={} 
    )

    # Registra o resultado da execução
    outcome = {
        "outcome_id": str(uuid.uuid4()),
        "decision_id": decision_id,
        "execution_status": feedback.get("execution_status"),
        "metrics": feedback.get("metrics", {}),
        "timestamp": _now_iso(),
    }
    _append({"type": "Outcome", **outcome}) 
