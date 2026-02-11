import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

try:
    import fcntl
except Exception:  # pragma: no cover
    fcntl = None

# Permite imports do pacote "app" quando executado via `python backend/app/cognitive_executor.py`
APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.append(str(APP_ROOT))

# Caminhos dos arquivos de log
DECISION_LOG_PATH = Path("storage/decision_log.jsonl")
STATE_LOG_PATH = Path("storage/state_log.jsonl")
OUTCOME_LOG_PATH = Path("storage/outcome_log.jsonl")


@contextmanager
def _jsonl_lock(path: Path, exclusive: bool):
    lock_path = path.with_name(f"{path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        if fcntl is not None:
            mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            fcntl.flock(lock_file.fileno(), mode)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _utc_iso() -> str:
    """
    Retorna a data e hora atual em formato ISO 8601 UTC.
    """
    return datetime.utcnow().isoformat()


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    """
    Adiciona um registro JSONL ao arquivo especificado, garantindo que cada registro
    comece em uma nova linha.   
    Args:
        path (Path): O caminho do arquivo JSONL.
        record (Dict[str, Any]): O registro a ser adicionado.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with _jsonl_lock(path, exclusive=True):
        with path.open("a+", encoding="utf-8") as f:
            if path.exists() and path.stat().st_size > 0:
                f.seek(0, 2)
                f.seek(f.tell() - 1)
                if f.read(1) != "\n":
                    f.write("\n")
            f.write(json.dumps(record) + "\n")


def _append_state(state: Dict[str, Any]) -> None:
    """
    Adiciona um estado ao log de estados.
    """
    _append_jsonl(STATE_LOG_PATH, state)


def _read_last_jsonl_record(path: Path) -> Optional[Dict[str, Any]]:
    """
    Lê o último registro de um arquivo JSONL.
    Args:
        path (Path): O caminho do arquivo JSONL.    
    Returns:
        Optional[Dict[str, Any]]: O último registro como um dicionário, ou None se o arquivo 
        não existir ou estiver vazio.
    """
    if not path.exists():
        return None
    last = None
    with _jsonl_lock(path, exclusive=False):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = line
    return json.loads(last) if last else None


def _build_outcome(
    process_id: str,
    decision_id: str,
    status: str,
    metrics: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Constrói um registro de resultado ()
    Args:   
        process_id (str): O ID do processo.
        decision_id (str): O ID da decisão fonte.
        status (str): O status da execução ("success", "failed", "blocked").
        metrics (Optional[Dict[str, Any]]): Métricas associadas ao resultado.
        error (Optional[Dict[str, str]]): Informações de erro, se houver.
    Returns:
        Dict[str, Any]: O registro de resultado construído. 
    """
    out = {
        "outcome_id": str(uuid.uuid4()),
        "timestamp": _utc_iso(),
        "process_id": process_id,
        "source_decision_id": decision_id,
        "execution_status": status,
        "metrics": metrics or {},
    }
    if status != "success":
        out["error"] = error or {"type": "UnknownError", "message": "Unspecified error"}
    return out


def _blocked(pid: str, did: str, t: str, m: str) -> Dict[str, Any]:
    """
    Constrói um registro de resultado bloqueado.
    Args:
        pid (str): O ID do processo.
        did (str): O ID da decisão fonte.
        t (str): O tipo de erro.
        m (str): A mensagem de erro.
    Returns:
        Dict[str, Any]: O registro de resultado bloqueado.
    """
    return _build_outcome(pid, did, "blocked", {}, {"type": t, "message": m})


def _failed(pid: str, did: str, t: str, m: str) -> Dict[str, Any]:
    """
    Constrói um registro de resultado falhado.
    Args:
        pid (str): O ID do processo.
        did (str): O ID da decisão fonte.
        t (str): O tipo de erro.
        m (str): A mensagem de erro.
    Returns:
        Dict[str, Any]: O registro de resultado falhado.    
    """
    return _build_outcome(pid, did, "failed", {}, {"type": t, "message": m})


def _validate_decision(dec: Dict[str, Any]) -> Optional[str]:
    """
    Valida a estrutura de uma decisão.
    Args:
        dec (Dict[str, Any]): A decisão a ser validada.   
    Returns:        
        Optional[str]: Uma mensagem de erro se a decisão for inválida, ou None se for válida.
    """
    for k in ("decision_id", "process_id", "source_state_id", "status", "actions"):
        if k not in dec:
            return f"MissingField: decision.{k}"
    if not isinstance(dec["actions"], list) or not dec["actions"]:
        return "MissingField: decision.actions"
    if dec.get("status") != "pending":
        return "InvalidField: decision.status"
    return None


def _ordered(actions: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """
    Ordena as ações com base no campo "order", se presente.
    Args:   
        actions (List[Dict[str, Any]]): A lista de ações a ser ordenada.   
    Returns:    
        Optional[List[Dict[str, Any]]]: A lista ordenada de ações, ou None se houver um erro de ordenação.
    """
    if any("order" in a for a in actions):
        if not all(isinstance(a.get("order"), int) for a in actions):
            return None
        return sorted(actions, key=lambda a: a["order"])
    return actions


def _validate_action(a: Dict[str, Any]) -> Optional[str]:
    """
    Valida a estrutura de uma ação.
    Args:
        a (Dict[str, Any]): A ação a ser validada.   
    Returns:    
        Optional[str]: Uma mensagem de erro se a ação for inválida, ou None se for válida.
    """
    for k in ("action_id", "type", "payload"):
        if k not in a:
            return f"MissingField: action.{k}"
    if not isinstance(a["payload"], dict):
        return "InvalidField: action.payload"
    return None


def _get_state(dec: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Recupera o estado associado a uma decisão.
    Args:
        dec (Dict[str, Any]): A decisão da qual recuperar o estado.
    Returns:
        Tuple[Optional[Dict[str, Any]], Optional[str]]: Uma tupla contendo o estado (ou None se não 
        encontrado) e uma mensagem de erro (ou None se bem-sucedido).
    """
    embedded = dec.get("state")
    if isinstance(embedded, dict):
        return embedded, None
    st = _read_last_jsonl_record(STATE_LOG_PATH)
    if not st:
        return None, "InvalidState: no state found"
    if st.get("state_id") != dec.get("source_state_id"):
        return None, "StateMismatch"
    return st, None


def _load_registry():
    """
    Carrega o registro de agentes.
    Returns:    
        AgentRegistry: O registro de agentes carregado.
    """
    from app.cognitive.agent_registry import AgentRegistry  # type: ignore
    return AgentRegistry()


def run_once() -> None:
    """
    Executa uma única iteração do executor cognitivo, processando a última decisão
    pendente e registrando o resultado.
    """

    # Lê a última decisão
    dec = _read_last_jsonl_record(DECISION_LOG_PATH)
    if not dec:
        _append_jsonl(OUTCOME_LOG_PATH, _blocked("", "", "IOError", "No Decision found"))
        return

    # Valida a decisão
    err = _validate_decision(dec)
    if err:
        _append_jsonl(
            OUTCOME_LOG_PATH,
            _blocked(dec.get("process_id", ""), dec.get("decision_id", ""), "MissingField", err),
        )
        return

    # Recupera o estado associado
    state, serr = _get_state(dec)
    if not state:
        _append_jsonl(
            OUTCOME_LOG_PATH,
            _blocked(dec["process_id"], dec["decision_id"], "InvalidState", serr or ""),
        )
        return

    # Processa as ações na ordem correta
    actions = _ordered(dec["actions"])
    if actions is None:
        _append_jsonl(
            OUTCOME_LOG_PATH,
            _blocked(dec["process_id"], dec["decision_id"], "MissingField", "Invalid action order"),
        )
        return

    # Carrega o registro de agentes
    try:
        registry = _load_registry()
    except Exception as e:
        _append_jsonl(
            OUTCOME_LOG_PATH,
            _blocked(dec["process_id"], dec["decision_id"], "MissingField", str(e)),
        )
        return

    # Inicializa contadores e variáveis
    executed = 0
    last_type = ""

    # Executa cada ação sequencialmente
    for a in actions:
        aerr = _validate_action(a)

        # Verifica erros de validação da ação
        if aerr:
            _append_jsonl(
                OUTCOME_LOG_PATH,
                _blocked(dec["process_id"], dec["decision_id"], "MissingField", aerr),
            )
            return
        try:
            agent = registry.resolve(a)
        except Exception as e:
            _append_jsonl(
                OUTCOME_LOG_PATH,
                _blocked(dec["process_id"], dec["decision_id"], "UnknownActionType", str(e)),
            )
            return

        # Verifica se o agente possui o método 'process'
        if not hasattr(agent, "process"):
            _append_jsonl(
                OUTCOME_LOG_PATH,
                _blocked(dec["process_id"], dec["decision_id"], "MissingField", "Agent lacks process"),
            )
            return

        # Processa a ação
        try:
            state["_action"] = {
                "type": a["type"],
                "payload": a.get("payload", {}),
                # Metadados para artefatos finais (manifest).
                "decision_id": dec.get("decision_id"),
                "process_id": dec.get("process_id"),
            }
            state = agent.process(state, a["payload"])
        except TypeError as e:
            _append_jsonl(
                OUTCOME_LOG_PATH,
                _blocked(dec["process_id"], dec["decision_id"], "MissingField", str(e)),
            )
            return
        except OSError as e:
            _append_jsonl(
                OUTCOME_LOG_PATH,
                _failed(dec["process_id"], dec["decision_id"], "IOError", str(e)),
            )
            return
        except Exception as e:
            _append_jsonl(
                OUTCOME_LOG_PATH,
                _failed(dec["process_id"], dec["decision_id"], "AgentFailure", str(e)),
            )
            return

        # Verifica se o estado retornado é um dicionário
        if not isinstance(state, dict):
            _append_jsonl(
                OUTCOME_LOG_PATH,
                _blocked(dec["process_id"], dec["decision_id"], "InvalidState", "Agent returned non-dict"),
            )
            return

        # Atualiza contadores
        executed += 1

        # Registra o tipo da última ação executada
        last_type = a["type"]

    # Persist updated state (append-only) after actions
    if isinstance(state, dict):
        _append_state(state)

    # Registra o resultado de sucesso
    _append_jsonl(
        OUTCOME_LOG_PATH,
        _build_outcome(
            dec["process_id"],
            dec["decision_id"],
            "success",
            {"actions_executed": executed, "last_action_type": last_type},
        ),
    )


def main() -> None:
    run_once()


if __name__ == "__main__":
    main()
