import copy
import json
import os
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# Tenta importar fcntl para bloqueio de arquivos, mas se não estiver disponível (ex: em Windows), define como None para evitar erros. 
# O bloqueio de arquivos é usado para garantir que apenas um processo possa escrever no arquivo de log JSONL ao mesmo tempo, evitando corrupção de dados.
try:
    import fcntl
except Exception:  
    fcntl = None


from app.core.executor.cognitive_executor import run_once
from app.observations import persist_observation
from app.cognitive_runs import persist_cognitive_run_from_observation
from app.schemas.observation import Observation
from app.state_from_observation import persist_state_from_observation

# Define os caminhos para os arquivos de log JSONL onde o estado, decisões e resultados serão armazenados. 
# Esses arquivos são usados para registrar o histórico de execução do loop cognitivo, permitindo que o sistema acompanhe o progresso e tome decisões informadas com base no estado atual e nos resultados anteriores.
STATE_LOG_PATH = Path("storage/state_log.jsonl")
DECISION_LOG_PATH = Path("storage/decision_log.jsonl")
OUTCOME_LOG_PATH = Path("storage/outcome_log.jsonl")
OBS_LOG_PATH = Path("storage/observation_log.jsonl")


@contextmanager
def _jsonl_lock(path: Path, exclusive: bool):
    """
    Context manager para bloquear um arquivo JSONL usando fcntl (se disponível) para garantir que apenas um processo possa escrever no arquivo ao mesmo tempo.
    Args:
        path (Path): O caminho do arquivo JSONL a ser bloqueado.
        exclusive (bool): Se True, bloqueia o arquivo para escrita exclusiva. Se False, bloqueia para leitura compartilhada.
    Yields:
        None: O contexto bloqueado para o arquivo JSONL.
    """
    lock_dir = Path("storage") / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"{path.name}.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        if fcntl is not None:
            mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            fcntl.flock(lock_file.fileno(), mode)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _read_last_jsonl(path: Path) -> Dict[str, Any] | None:
    """
    Lê o último registro de um arquivo JSONL e retorna como um dicionário. Se o arquivo não existir ou estiver vazio, retorna None.
    Args:
        path (Path): O caminho do arquivo JSONL a ser lido.
    Returns:
        Dict[str, Any] | None: O último registro do arquivo JSONL como um dicionário, ou None se o arquivo não existir ou estiver vazio.
    """
    if not path.exists():
        return None
    last = None
    with _jsonl_lock(path, exclusive=False):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    last = line
    if not last:
        return None
    try:
        return json.loads(last)
    except Exception:
        return None


def _read_last_jsonl_for_process_id(path: Path, process_id: str) -> Dict[str, Any] | None:
    """
    Lê um arquivo JSONL e retorna o último registro que corresponde ao process_id fornecido. Se o arquivo não existir ou não houver registros correspondentes, retorna None.
    Args:
        path (Path): O caminho do arquivo JSONL a ser lido.
        process_id (str): O ID do processo para o qual o registro deve ser correspondido.
    Returns:
        Dict[str, Any] | None: O último registro do arquivo JSONL que corresponde ao process_id fornecido como um dicionário, ou None se o arquivo não existir ou não houver registros correspondentes.
    """
    if not path.exists():
        return None
    last = None
    with _jsonl_lock(path, exclusive=False):
        with path.open("r", encoding="utf-8") as f:
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


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    """
    Anexa um registro a um arquivo JSONL, garantindo que o diretório exista e usando bloqueio para evitar corrupção de dados.
    Args:
        path (Path): O caminho do arquivo JSONL ao qual o registro deve ser anexado.
        record (Dict[str, Any]): O registro a ser anexado ao arquivo JSONL como um dicionário.
    Returns:
        None: Este método não retorna nada, mas anexa o registro ao arquivo JSONL especificado.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with _jsonl_lock(path, exclusive=True):
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


def _observation_already_emitted(process_id: str, source_outcome_id: str) -> bool:
    """
    Dedupe minimo append-only: evita re-emissao de cognitive_loop_finished
    para o mesmo par (process_id, source_outcome_id).
    """
    if not OBS_LOG_PATH.exists():
        return False
    try:
        with _jsonl_lock(OBS_LOG_PATH, exclusive=False):
            with OBS_LOG_PATH.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except Exception:
                        continue
                    if not isinstance(record, dict):
                        continue
                    facts = record.get("facts")
                    if not isinstance(facts, dict):
                        continue
                    if (
                        record.get("process_id") == process_id
                        and record.get("source_outcome_id") == source_outcome_id
                        and facts.get("event_type") == "cognitive_loop_finished"
                    ):
                        return True
    except Exception:
        return False
    return False


def _compute_pipeline_status(
    outcome: Dict[str, Any], state: Dict[str, Any], stop_reason: Optional[str]
) -> str:
    """
    Enum canonico:
      completed | failed | blocked | truncated
    """
    execution_status = outcome.get("execution_status")
    artifacts = (state.get("artifacts") or {})
    termination_reason = artifacts.get("termination_reason")

    if execution_status == "blocked":
        return "blocked"
    if execution_status == "failed":
        return "failed"
    if termination_reason == "video_failed":
        return "failed"
    if termination_reason == "pipeline_complete":
        return "completed"
    if stop_reason in ("max_steps", "max_steps_reached"):
        return "truncated"
    if artifacts.get("terminated") is True:
        return "truncated"
    return "truncated"


def _build_next_action(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constrói a próxima ação a ser executada com base no estado atual. A função verifica o estado e os artefatos para determinar qual ação deve ser tomada a seguir no pipeline de processamento de vídeo, desde a coleta
    do vídeo até a transcrição dos segmentos de áudio. Se o pipeline estiver completo ou se ocorrer uma falha, a função retorna uma ação para escrever um artefato indicando o motivo da conclusão ou falha.    
    Args:
        state (Dict[str, Any]): O estado atual do processo, incluindo fatos e artefatos que indicam o progresso do pipeline.
    Returns:
        Dict[str, Any]: A próxima ação a ser executada, incluindo o tipo da ação e o payload necessário para executar essa ação.
    """
    facts = state.get("facts", {}) or {}
    artifacts = state.get("artifacts", {}) or {}

    if facts.get("status_final") == "failed":
        action_type = "write_artifact"
        payload = {
            "reason": "video_failed",
            "video_id": facts.get("video_id"),
            "error": facts.get("error"),
        }
    elif artifacts.get("raw_video_ready") is not True and isinstance(facts.get("source_url"), str) and facts.get("source_url"):
        action_type = "collect_video"
        payload = {"url": facts.get("source_url")}
    elif isinstance(artifacts.get("raw_video_minio_path"), str) and artifacts.get("raw_video_minio_path") and artifacts.get("audio_ready") is not True:
        action_type = "extract_audio"
        payload = {
            "raw_video_minio_path": artifacts.get("raw_video_minio_path"),
            "audio_format": "wav",
        }
    elif isinstance(artifacts.get("audio_local_path"), str) and artifacts.get("audio_local_path") and artifacts.get("segments_ready") is not True:
        action_type = "segment_audio"
        payload = {"audio_local_path": artifacts.get("audio_local_path")}
    elif isinstance(state.get("segments"), list) and artifacts.get("transcriptions_ready") is not True:
        action_type = "transcribe_segments"
        payload = {
            "audio_local_path": artifacts.get("audio_local_path") or state.get("audio_local_path")
        }
    else:
        action_type = "write_artifact"
        payload = {"reason": "pipeline_complete", "video_id": facts.get("video_id")}

    return {
        "action_id": str(uuid.uuid4()),
        "type": action_type,
        "payload": payload,
    }


def _emit_cognitive_loop_finished_observation(
    process_id: str,
    outcome: Dict[str, Any],
    state: Dict[str, Any],
    stop_reason: Optional[str] = None,
) -> None:
    """
    Emite uma observação indicando que o loop cognitivo foi concluído, incluindo métricas e artefatos relevantes do estado e do resultado final. Esta função é chamada quando o loop cognitivo atinge um estado de término, seja por conclusão bem-sucedida, falha ou bloqueio. A observação emitida inclui informações sobre o status da execução, a razão para a terminação (se aplicável) e outras métricas relevantes que podem ser usadas para análise posterior ou para acionar ações adicionais.
    Args:
        process_id (str): O ID do processo para o qual a observação de término do loop cognitivo está sendo emitida.
        outcome (Dict[str, Any]): O resultado final da execução do loop cognitivo, incluindo o status da execução e outras métricas relevantes.
        state (Dict[str, Any]): O estado final do processo no momento em que o loop cognitivo foi concluído, incluindo artefatos que indicam o motivo da terminação e o status do pipeline.
    Returns:
        None: Este método não retorna nada, mas emite uma observação que pode ser persistida e usada para análise ou ações futuras. A observação inclui informações detalhadas sobre o processo, o resultado e o estado no momento da conclusão do loop cognitivo.
    """
    metrics = outcome.get("metrics") or {}
    artifacts = state.get("artifacts") or {}
    termination_reason = artifacts.get("termination_reason")
    pipeline_status = _compute_pipeline_status(outcome, state, stop_reason)
    source_outcome_id = outcome.get("outcome_id")
    if not isinstance(source_outcome_id, str) or not source_outcome_id:
        return
    if _observation_already_emitted(process_id, source_outcome_id):
        print(
            f"COGNITIVE_LOOP finished_observation deduped process_id={process_id} "
            f"source_outcome_id={source_outcome_id}"
        )
        return

    obs = Observation(
        observation_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat(),
        process_id=process_id,
        source_outcome_id=source_outcome_id,
        facts={
            "event_type": "cognitive_loop_finished",
            "execution_status": outcome.get("execution_status"),
            "source_decision_id": outcome.get("source_decision_id"),
            "last_action_type": metrics.get("last_action_type"),
            "actions_executed": metrics.get("actions_executed"),
            "termination_reason": termination_reason,
            "terminated": artifacts.get("terminated"),
            "pipeline_status": pipeline_status,
        },
    )
    persist_observation(obs)
    persist_state_from_observation(obs)
    try:
        persist_cognitive_run_from_observation(obs)
    except Exception:
        pass


def _is_real_outcome_for_process(outcome: Dict[str, Any] | None, process_id: str) -> bool:
    if not outcome or not isinstance(outcome, dict):
        return False
    if outcome.get("process_id") != process_id:
        return False
    if outcome.get("execution_status") == "external":
        return False
    if not outcome.get("source_decision_id"):
        return False
    return True


def run_loop(max_steps: int = 10, process_id: str | None = None) -> int:
    """
    Executa um loop cognitivo para um processo específico, lendo o estado atual, decidindo a próxima ação a ser tomada, executando essa ação e avaliando o resultado. O loop continua até que um estado de término seja alcançado (conclusão, falha ou bloqueio) ou até que o número máximo de etapas seja atingido. O loop é projetado para ser idempotente e pode ser executado várias vezes sem causar efeitos colaterais indesejados, graças ao uso de arquivos de log JSONL para rastrear o estado, decisões e resultados.
    Args:
        max_steps (int): O número máximo de etapas que o loop cognitivo deve executar antes de parar. O valor padrão é 10.
        process_id (str | None): O ID do processo para o qual o loop cognitivo deve ser executado. Se None, o loop não será executado e a função retornará imediatamente. O valor padrão é None.
    Returns:
        int: O número de etapas executadas no loop cognitivo antes de atingir um estado de término ou atingir o número máximo de etapas.
    """
    steps = 0
    stop_reason: Optional[str] = None
    target_process_id = process_id

    if not target_process_id:
        print("COGNITIVE_LOOP done process_id=None steps_executed=0 stop_reason=no_state")
        return 0

    print(f"COGNITIVE_LOOP start process_id={target_process_id} max_steps={max_steps}")

    current_state = _read_last_jsonl_for_process_id(STATE_LOG_PATH, target_process_id)
    if not current_state:
        print(f"COGNITIVE_LOOP done process_id={target_process_id} steps_executed=0 stop_reason=no_state")
        return 0
    current_artifacts = current_state.get("artifacts", {}) or {}
    current_facts = current_state.get("facts", {}) or {}
    current_terminated = (
        current_artifacts.get("terminated")
        if "terminated" in current_artifacts
        else current_facts.get("terminated")
    )
    current_termination_reason = (
        current_artifacts.get("termination_reason")
        if "termination_reason" in current_artifacts
        else current_facts.get("termination_reason")
    )
    current_outcome = _read_last_jsonl_for_process_id(OUTCOME_LOG_PATH, target_process_id)
    skip_loop = False
    if current_terminated is True:
        reason = current_termination_reason
        print(f"COGNITIVE_LOOP skip (already terminated) process_id={target_process_id} termination_reason={reason}")
        stop_reason = "already_terminated"
        skip_loop = True
    elif current_outcome and current_outcome.get("execution_status") in ("failed", "blocked"):
        status = current_outcome.get("execution_status")
        print(f"COGNITIVE_LOOP skip (last outcome failed/blocked) process_id={target_process_id} status={status}")
        stop_reason = status
        skip_loop = True
    if skip_loop:
        if current_state and _is_real_outcome_for_process(current_outcome, target_process_id):
            _emit_cognitive_loop_finished_observation(
                target_process_id,
                current_outcome,
                current_state,
                stop_reason=stop_reason,
            )
        print(
            f"COGNITIVE_LOOP done process_id={target_process_id} steps_executed=0 stop_reason={stop_reason}"
        )
        return 0

    # O loop principal do processo cognitivo, que continua até atingir um estado de término ou atingir o número máximo de etapas. 
    # Em cada etapa, o loop lê o estado atual, decide a próxima ação a ser tomada, executa essa ação e avalia o resultado para determinar se deve continuar ou parar.
    last_state: Optional[Dict[str, Any]] = None
    last_outcome: Optional[Dict[str, Any]] = None
    for step_index in range(1, max_steps + 1):
        state = _read_last_jsonl_for_process_id(STATE_LOG_PATH, target_process_id)
        if not state:
            stop_reason = "no_state"
            break

        current_process_id = state.get("process_id")
        state_id = state.get("state_id")
        if not current_process_id or not state_id:
            stop_reason = "no_state"
            break

        action = _build_next_action(state)
        new_state = copy.deepcopy(state)
        new_state["state_id"] = str(uuid.uuid4())
        new_state["timestamp"] = datetime.utcnow().isoformat()
        new_state["previous_state_id"] = state_id
        new_state["_action"] = {"type": action["type"], "payload": action.get("payload", {})}
        if action["type"] == "write_artifact":
            reason = (action.get("payload", {}) or {}).get("reason")
            if reason in ("pipeline_complete", "video_failed"):
                new_state.setdefault("artifacts", {})
                new_state["artifacts"]["terminated"] = True
                new_state["artifacts"]["termination_reason"] = reason
        _append_jsonl(STATE_LOG_PATH, new_state)

        decision = {
            "decision_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "process_id": current_process_id,
            "source_state_id": new_state["state_id"],
            "status": "pending",
            "actions": [action],
        }
        _append_jsonl(DECISION_LOG_PATH, decision)
        print(
            f"COGNITIVE_LOOP step process_id={current_process_id} step_index={step_index} "
            f"decision_id={decision['decision_id']} action_type={action.get('type')}"
        )

        run_once()
        steps += 1

        outcome = _read_last_jsonl_for_process_id(OUTCOME_LOG_PATH, current_process_id)
        last_state = new_state
        last_outcome = outcome
        if outcome:
            if outcome.get("source_decision_id") != decision["decision_id"]:
                print("OutcomeMismatch: last outcome not from current decision")
                stop_reason = "failed"
                break
            status = outcome.get("execution_status")
            if status in ("blocked", "failed"):
                stop_reason = status
                break

        if action["type"] == "write_artifact":
            payload = action.get("payload", {}) or {}
            if payload.get("reason") in ("pipeline_complete", "video_failed"):
                stop_reason = payload.get("reason")
                break

    if stop_reason is None and steps >= max_steps:
        stop_reason = "max_steps"
            
    # Após o loop, verifica se o processo atingiu um estado de término (conclusão, falha ou bloqueio) e emite uma observação de término do loop cognitivo com as métricas e artefatos relevantes do estado e do resultado final.
    if target_process_id:
        final_state = last_state or _read_last_jsonl_for_process_id(STATE_LOG_PATH, target_process_id)
        final_outcome = last_outcome or _read_last_jsonl_for_process_id(OUTCOME_LOG_PATH, target_process_id)
        if final_state and _is_real_outcome_for_process(final_outcome, target_process_id):
            artifacts = final_state.get("artifacts") or {}
            if (
                final_outcome.get("execution_status") in ("failed", "blocked")
                or artifacts.get("terminated") is True
                or stop_reason in ("max_steps", "max_steps_reached", "already_terminated", "failed", "blocked")
                or artifacts.get("transcriptions_ready") is True
            ):
                _emit_cognitive_loop_finished_observation(
                    target_process_id,
                    final_outcome,
                    final_state,
                    stop_reason=stop_reason,
                )

    print(f"COGNITIVE_LOOP done process_id={target_process_id} steps_executed={steps} stop_reason={stop_reason}")
    return steps


def main() -> None:
    # Exemplo de execução do loop cognitivo para um processo específico. O ID do processo pode ser passado como argumento ou definido diretamente no código. 
    # O loop continuará executando até atingir um estado de término ou atingir o número máximo de etapas, e as métricas de execução serão impressas no console.
    steps = run_loop(max_steps=10)
    print(f"auto-loop finalizado: {steps} step(s)")


if __name__ == "__main__":
    main()
