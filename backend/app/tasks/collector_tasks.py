from app.worker import celery_app # Importa a instância do Celery
from app.agents.collector.service import CollectorAgent # Importa o agente coletor
from app.agents.segmenter.service import SegmenterAgent # Importa o agente segmentador
from app.agents.transcriber.service import TranscriberAgent # Importa o agente transcritor
from app.db.models import Video, VideoSegment # Importa os modelos Video e VideoSegment
from app.services.storage import MinioService # Serviço de armazenamento MinIO
from app.observations import persist_observation
from app.schemas.observation import Observation
from app.state_from_observation import persist_state_from_observation
from app.cognitive.cognitive_loop_runner import run_loop as run_cognitive_loop
import os
import uuid
import json
from contextlib import contextmanager # Importa contextmanager para criar gerenciadores de contexto personalizados
from datetime import datetime
from sqlalchemy import create_engine # create_engine para criar engine de DB
from sqlalchemy.orm import sessionmaker # sessionmaker para criar sessões
import logging # Importa logging para registro de logs

# Importa fcntl para bloqueio de arquivos, mas lida com a ausência em sistemas não Unix (como Windows) definindo fcntl como None se a importação falhar. 
# O bloqueio de arquivos é usado para garantir que apenas um processo acesse um arquivo JSONL específico por vez, evitando corrupção de dados em cenários de concorrência.
try:
    import fcntl
except Exception:  
    fcntl = None

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Logs cognitivos
OUTCOME_LOG_PATH = "storage/outcome_log.jsonl"
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


def _get_last_outcome_id() -> str | None:
    """
    Lê o arquivo de log de resultados e retorna o ID do resultado mais recente registrado. O arquivo de log é lido linha por linha, e cada linha é esperada ser um registro JSON contendo um campo "outcome_id". A função retorna o valor do campo "outcome_id" do último registro encontrado no arquivo. Se o arquivo não existir ou estiver vazio, a função retorna None.
    Returns:
        str | None: O ID do resultado mais recente registrado no arquivo de log de resultados, ou None se o arquivo não existir ou estiver vazio.
    """
    if not os.path.exists(OUTCOME_LOG_PATH):
        return None
    last_id = None
    with _jsonl_lock(OUTCOME_LOG_PATH, exclusive=False):
        with open(OUTCOME_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue
                if isinstance(record, dict) and record.get("outcome_id"):
                    last_id = record.get("outcome_id")
    return last_id


def _append_minimal_outcome(outcome_id: str, process_id: str) -> None:
    """
    Anexa um registro mínimo de resultado ao arquivo de log de resultados, garantindo que o diretório exista e usando bloqueio para evitar corrupção de dados. Este registro mínimo é usado para garantir que haja um resultado associado a um processo específico, mesmo que o loop cognitivo seja iniciado antes que um resultado completo seja registrado. O registro inclui o outcome_id, timestamp, process_id, source_decision_id vazio, execution_status "external" e métricas indicando a origem como "celery".
    Args:
        outcome_id (str): O ID do resultado a ser registrado.
        process_id (str): O ID do processo associado a este resultado.  
    Returns:
        None: Este método não retorna nada, mas anexa um registro mínimo de resultado ao arquivo de log de resultados para garantir que haja um resultado associado ao processo específico, mesmo que o loop cognitivo seja iniciado antes que um resultado completo seja registrado.
    """
    os.makedirs(os.path.dirname(OUTCOME_LOG_PATH), exist_ok=True)
    record = {
        "outcome_id": outcome_id,
        "timestamp": datetime.utcnow().isoformat(),
        "process_id": process_id,
        "source_decision_id": "",
        "execution_status": "external",
        "metrics": {"origin": "celery"},
    }
    with _jsonl_lock(OUTCOME_LOG_PATH, exclusive=True):
        with open(OUTCOME_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


def _get_last_state_process_id() -> str | None:
    """
    Lê o último registro do arquivo de log de estado e retorna o process_id associado a esse registro. Se o arquivo não existir ou estiver vazio, retorna None. Esta função é usada para verificar o ID do processo do último estado registrado, o que pode ser útil para garantir que as ações subsequentes sejam associadas ao processo correto.
    Returns:
        str | None: O process_id do último registro no arquivo de log de estado, ou None se o arquivo não existir ou estiver vazio.
    """
    if not os.path.exists(STATE_LOG_PATH):
        return None
    last = None
    with _jsonl_lock(STATE_LOG_PATH, exclusive=False):
        with open(STATE_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    last = line
    if not last:
        return None
    try:
        record = json.loads(last)
    except Exception:
        return None
    if isinstance(record, dict):
        return record.get("process_id")
    return None


def _is_cognitive_loop_enabled() -> bool:
    """
    Verifica se o loop cognitivo está habilitado por meio de uma variável de ambiente. A função lê a variável de ambiente "COGNITIVE_LOOP_ENABLED" e retorna True se o valor for "1", "true" ou "yes" (ignorando maiúsculas), indicando que o loop cognitivo deve ser executado. Caso contrário, retorna False, indicando que o loop cognitivo está desabilitado.
    Returns:
        bool: True se o loop cognitivo estiver habilitado, False caso contrário.
    """
    flag = os.getenv("COGNITIVE_LOOP_ENABLED", "0")
    return flag.lower() in ("1", "true", "yes")


def _get_cognitive_loop_max_steps() -> int:
    """
    Obtém o número máximo de etapas que o loop cognitivo deve executar antes de parar, a partir de uma variável de ambiente. Se a variável de ambiente não estiver definida ou não for um inteiro válido, retorna um valor padrão de 10.
    Returns:
        int: O número máximo de etapas para o loop cognitivo, obtido da variável de ambiente ou o valor padrão de 10 se a variável não for definida ou inválida.
    """
    raw = os.getenv("COGNITIVE_LOOP_MAX_STEPS", "10")
    try:
        return int(raw)
    except Exception:
        return 10


def _maybe_run_cognitive_loop(process_id: str) -> None:
    """
    Verifica se o loop cognitivo está habilitado e, se estiver, enfileira uma task Celery para executar o loop cognitivo para o processo especificado. A função verifica se o loop cognitivo está habilitado por meio de uma variável de ambiente, garante que apenas uma instância do loop seja executada por vez para o mesmo process_id e registra as ações tomadas nos logs.
    Args:
        process_id (str): O ID do processo para o qual o loop cognitivo deve ser executado.
    Returns:
        None: Esta função não retorna nada, mas pode enfileirar uma task Celery para executar o loop cognitivo se as condições forem atendidas. Se o loop cognitivo estiver desabilitado ou se já houver uma instância em execução para o process_id fornecido, a função registrará essa informação nos logs e não enfileirará a task.
    """
    if not _is_cognitive_loop_enabled():
        logger.info("COGNITIVE_LOOP skipped (disabled)")
        return
    last_pid = _get_last_state_process_id()
    if last_pid != process_id:
        logger.info(f"COGNITIVE_LOOP skipped (state process_id mismatch): {last_pid} != {process_id}")
        return
    max_steps = _get_cognitive_loop_max_steps()
    logger.info(f"COGNITIVE_LOOP enqueue process_id={process_id} max_steps={max_steps}")
    try:
        cognitive_loop_task.delay(process_id, max_steps)
    except Exception as e:
        logger.error(f"COGNITIVE_LOOP error process_id={process_id} err={e}")

# Define a task Celery para executar o loop cognitivo para um processo específico. 
# Esta task é responsável por garantir que apenas uma instância do loop cognitivo
@celery_app.task(name="cognitive.run_loop_for_process")
def cognitive_loop_task(process_id: str, max_steps: int | None = None):
    """
    Task Celery que executa o loop cognitivo para um processo específico, garantindo que apenas uma instância do loop seja executada por vez para o mesmo process_id. A função adquire um bloqueio baseado em arquivo para garantir exclusividade, verifica se o loop cognitivo já está em execução para o process_id fornecido e, se não estiver, executa o loop cognitivo com o número máximo de etapas especificado. O resultado da execução do loop cognitivo é registrado nos logs, incluindo o status de conclusão ou erro.
    Args:
        process_id (str): O ID do processo para o qual o loop cognitivo deve ser executado.
        max_steps (int | None): O número máximo de etapas que o loop cognitivo deve executar antes de parar. Se None, o valor padrão será usado.    
    Returns:
        dict: Um dicionário contendo o status da execução do loop cognitivo, o ID do processo e, em caso de erro, a mensagem de erro. O status pode ser "skipped" se o loop já estiver em execução para o process_id fornecido, "done" se o loop for concluído com sucesso ou "error" se ocorrer um erro durante a execução do loop.
    """
    lock_dir = os.path.join("storage", "locks")
    os.makedirs(lock_dir, exist_ok=True)
    lock_file_path = os.path.join(lock_dir, f"process_{process_id}.lock")
    lock_handle = open(lock_file_path, "a+", encoding="utf-8")
    try:
        if fcntl is not None:
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                logger.info(f"COGNITIVE_LOOP skipped (already running) process_id={process_id}")
                return {"status": "skipped", "reason": "already_running", "process_id": process_id}

        steps = max_steps if isinstance(max_steps, int) else _get_cognitive_loop_max_steps()
        logger.info(f"COGNITIVE_LOOP start process_id={process_id} max_steps={steps}")
        run_cognitive_loop(max_steps=steps, process_id=process_id)
        logger.info(f"COGNITIVE_LOOP done process_id={process_id}")
        return {"status": "done", "process_id": process_id, "max_steps": steps}
    except Exception as e:
        logger.error(f"COGNITIVE_LOOP error process_id={process_id} err={e}")
        return {"status": "error", "process_id": process_id, "error": str(e)}
    finally:
        if fcntl is not None:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()


# Cria engine síncrona usando DATABASE_URL (para uso em workers)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cortai_admin:cortai_secret_pass_123@db:5432/cortai_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Define a task Celery para processar vídeos
@celery_app.task(name="collector.process_video")
def process_video_task(video_id: str, url: str):
    """
    Task Celery que executa o CollectorAgent e atualiza o registro do Video.

    Parâmetros:
    - video_id: UUID string do registro Video
    - url: URL a ser baixada
    """
    agent = CollectorAgent()
    session = SessionLocal()
    try:
        # Marca como downloading (caso não esteja)
        try:
            vid_uuid = uuid.UUID(video_id)
        except Exception:
            vid_uuid = video_id

        # Busca o registro do vídeo
        video = session.get(Video, vid_uuid)
        if video:
            video.status = "downloading"
            session.add(video)
            session.commit()

        # Executa o processamento (download + upload)
        result = agent.process(url)

        # Atualiza o registro com resultados
        if video:
            video.title = result.get("title")
            video.duration = result.get("duration")
            video.file_path = result.get("minio_path")
            video.metadata_info = result.get("metadata")
            video.status = "transcribing"
            session.add(video)
            session.commit()

            # Segmentar o vídeo
            storage = MinioService()
            temp_dir = "/tmp"
            os.makedirs(temp_dir, exist_ok=True)
            local_file_path = os.path.join(temp_dir, f"{video_id}.mp4")
            object_name = video.file_path.split('/', 1)[1]
            logger.info(f"Downloading file from MinIO: {object_name} to {local_file_path}")
            storage.download_file(object_name, local_file_path)

            logger.info(f"Starting segmentation for: {local_file_path}")
            segmenter = SegmenterAgent()
            segments = segmenter.process(local_file_path)

            logger.info(f"Segmentation finished. Found {len(segments)} segments.")
            
            # Armazenar segmentos no banco de dados
            db_segments = []
            for seg in segments:
                logger.info(f"Persisting segment: {seg}")
                segment = VideoSegment(
                    video_id=video.id,
                    start_time=seg['start_time'],
                    end_time=seg['end_time'],
                    transcript_text=None
                )
                session.add(segment)
                db_segments.append(segment)
            session.commit()
            
            # Refresh para garantir que os IDs sejam carregados
            for s in db_segments:
                session.refresh(s)
            
            # Adiciona o db_id aos segmentos para referência futura 
            for i, seg in enumerate(segments):
                if i < len(db_segments):
                    seg['db_id'] = str(db_segments[i].id)

            logger.info("Segments committed to DB.")
            
            # Prepara input para transcrição
            transcriber_input = []
            for i, seg in enumerate(segments):
                transcriber_input.append({
                    "segment_id": str(db_segments[i].id), # Usa o UUID do DB
                    "start_time": seg["start_time"],
                    "end_time": seg["end_time"]
                })

            transcriber = TranscriberAgent()
            transcriptions = transcriber.transcribe(local_file_path, transcriber_input)

            # Atualizar transcrições no banco de dados
            for trans in transcriptions:
                seg_uuid = trans['segment_id']
                text = trans['text']
                
                if text:
                    logger.info(f"Updating segment {seg_uuid} (Type: {type(seg_uuid)}) with text length: {len(text)}")
                    try:
                        # Garante que seg_uuid é um UUID válido
                        real_uuid = uuid.UUID(str(seg_uuid))
                        
                        # Atualiza usando query update
                        updated_rows = session.query(VideoSegment).filter(VideoSegment.id == real_uuid).update({"transcript_text": text})
                        logger.info(f"Updated {updated_rows} rows for segment {real_uuid}")
                        
                        if updated_rows == 0:
                            logger.warning(f"⚠️ Initial update failed for {real_uuid}. Trying commit and retry.")
                            session.commit()
                            # Tenta novamente após commit
                            seg_obj = session.get(VideoSegment, real_uuid)
                            if seg_obj:
                                seg_obj.transcript_text = text
                                session.add(seg_obj)
                                logger.info(f"Fallback update success for {real_uuid}")
                            else:
                                logger.error(f"❌ Could not find segment {real_uuid} in DB even after commit check.")

                    except Exception as e:
                        logger.error(f"❌ Error updating segment {seg_uuid}: {e}")
                else:
                    logger.warning(f"⚠️ Skipping update for segment {seg_uuid}: Text is empty.")
            
            session.commit()

            # Atualizar status para analyzing
            video.status = "analyzing"
            session.add(video)
            session.commit()

            # Remove arquivo temporário
            os.remove(local_file_path)
            # --- Observation (sucesso) ---
            process_id = f"P_VIDEO_{video_id}"
            source_outcome_id = str(uuid.uuid4())
            _append_minimal_outcome(source_outcome_id, process_id)

            observation = Observation(
                observation_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow().isoformat(),
                process_id=process_id,
                source_outcome_id=source_outcome_id,
                facts={
                    "video_id": str(video.id),
                    "source_url": url,
                    "status_final": video.status,
                    "segments_count": len(segments),
                    "transcriptions_count": len(transcriptions),
                    "duration": video.duration,
                },
            )
            persist_observation(observation)
            state_ok = True
            try:
                persist_state_from_observation(observation)
            except Exception as e:
                state_ok = False
                logger.error(f"Failed to persist state from observation: {e}")
            if state_ok:
                _maybe_run_cognitive_loop(process_id)

        return {"status": "completed", "data": result}

    except Exception as e:
        # Marca falha no banco se possível e armazena o motivo no metadata_info
        try:
            if video:
                video.status = "failed"
                # preserva metadata existente, adiciona motivo de erro
                meta = video.metadata_info or {}
                try:
                    meta['error'] = str(e)
                except Exception:
                    meta['error'] = "Erro ao serializar a mensagem de erro"
                video.metadata_info = meta
                session.add(video)
                session.commit()
        except Exception:
            pass
        # Repropaga para visibilidade (Celery / logs)
        # --- Observation (falha) ---
        try:
            process_id = f"P_VIDEO_{video_id}"
            source_outcome_id = str(uuid.uuid4())
            _append_minimal_outcome(source_outcome_id, process_id)

            observation = Observation(
                observation_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow().isoformat(),
                process_id=process_id,
                source_outcome_id=source_outcome_id,
                facts={
                    "video_id": str(video_id),
                    "source_url": url,
                    "status_final": "failed",
                    "error": str(e),
                },
            )
            persist_observation(observation)
            state_ok = True
            try:
                persist_state_from_observation(observation)
            except Exception as e:
                state_ok = False
                logger.error(f"Failed to persist state from observation: {e}")
            if state_ok:
                _maybe_run_cognitive_loop(process_id)
        except Exception:
            pass
        raise e
    finally:
        session.close()
