import json
import os
import logging
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import CognitiveRun
from app.schemas.observation import Observation

try:
    import fcntl
except Exception:  
    fcntl = None

# Configuração de Logs
logger = logging.getLogger(__name__)

STATE_LOG_PATH = "storage/state_log.jsonl"

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cortai_admin:cortai_secret_pass_123@db:5432/cortai_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


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


def _read_last_state_for_process_id(process_id: str) -> dict | None:
    """
    Lê o arquivo de log de estado e retorna o último registro associado a um process_id específico. O arquivo de log é lido linha por linha, e cada linha é esperada ser um registro JSON contendo um campo "process_id". A função retorna o último registro encontrado no arquivo que corresponde ao process_id fornecido. Se o arquivo não existir ou estiver vazio, ou se nenhum registro corresponder ao process_id, a função retorna None.
    Args:
        process_id (str): O ID do processo para o qual o último estado deve ser recuperado.
    Returns:
        dict | None: O último registro do arquivo de log de estado que corresponde ao process_id fornecido, ou None se o arquivo não existir, estiver vazio ou se nenhum registro corresponder ao process_id.
    """
    if not os.path.exists(STATE_LOG_PATH):
        return None
    last = None
    with _jsonl_lock(STATE_LOG_PATH, exclusive=False):
        with open(STATE_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue
                if isinstance(record, dict) and record.get("process_id") == process_id:
                    last = record
    return last


def persist_cognitive_run_from_observation(observation: Observation) -> None:
    """
    Persiste um registro de CognitiveRun no banco de dados com base em uma observação recebida. A função verifica se a observação contém fatos relacionados ao término de um loop cognitivo e, em caso afirmativo, extrai as informações relevantes para criar ou atualizar um registro de CognitiveRun no banco de dados. O registro inclui o process_id, pipeline_status, termination_reason, terminated, source_observation_id, source_outcome_id, source_decision_id, execution_status, actions_executed, last_action_type e video_id (se disponível). A função lida com a criação de novos registros ou a atualização de registros existentes com base no process_id.
    Args:
        observation (Observation): A observação recebida que pode conter fatos relacionados ao término de um loop cognitivo. A função verifica os fatos da observação para determinar se um registro de CognitiveRun deve ser criado ou atualizado no banco de dados.
    Returns:
        None: Esta função não retorna nada, mas persiste um registro de CognitiveRun no banco de dados com base nas informações extraídas da observação, se aplicável.
    """
    facts = observation.facts or {}
    if facts.get("event_type") != "cognitive_loop_finished":
        return

    process_id = observation.process_id
    if not process_id:
        return

    pipeline_status = facts.get("pipeline_status") or "unknown"
    if pipeline_status not in ("completed", "failed", "blocked", "unknown"):
        pipeline_status = "unknown"

    last_state = _read_last_state_for_process_id(process_id)
    video_id = None
    if last_state:
        state_facts = last_state.get("facts") or {}
        video_id = state_facts.get("video_id")

    session = SessionLocal()
    try:
        existing = session.get(CognitiveRun, process_id)
        if existing:
            existing.pipeline_status = pipeline_status
            existing.termination_reason = facts.get("termination_reason")
            existing.terminated = bool(facts.get("terminated"))
            existing.source_observation_id = observation.observation_id
            existing.source_outcome_id = observation.source_outcome_id
            existing.source_decision_id = facts.get("source_decision_id")
            existing.execution_status = facts.get("execution_status")
            existing.actions_executed = facts.get("actions_executed")
            existing.last_action_type = facts.get("last_action_type")
            existing.video_id = video_id
            existing.updated_at = datetime.utcnow()
        else:
            run = CognitiveRun(
                process_id=process_id,
                pipeline_status=pipeline_status,
                termination_reason=facts.get("termination_reason"),
                terminated=bool(facts.get("terminated")),
                source_observation_id=observation.observation_id,
                source_outcome_id=observation.source_outcome_id,
                source_decision_id=facts.get("source_decision_id"),
                execution_status=facts.get("execution_status"),
                actions_executed=facts.get("actions_executed"),
                last_action_type=facts.get("last_action_type"),
                video_id=video_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(run)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to persist CognitiveRun for process_id={process_id}: {e}")
    finally:
        session.close()
