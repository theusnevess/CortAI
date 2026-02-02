from app.worker import celery_app # Importa a instância do Celery
from app.agents.collector.service import CollectorAgent # Importa o agente coletor
from app.agents.segmenter.service import SegmenterAgent # Importa o agente segmentador
from app.agents.transcriber.service import TranscriberAgent # Importa o agente transcritor
from app.db.models import Video, VideoSegment # Importa os modelos Video e VideoSegment
from app.services.storage import MinioService # Serviço de armazenamento MinIO
from app.observations import persist_observation
from app.schemas.observation import Observation
from app.state_from_observation import persist_state_from_observation
import os
import uuid
import json
from datetime import datetime
from sqlalchemy import create_engine # create_engine para criar engine de DB
from sqlalchemy.orm import sessionmaker # sessionmaker para criar sessões
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Logs cognitivos
OUTCOME_LOG_PATH = "storage/outcome_log.jsonl"


def _get_last_outcome_id() -> str | None:
    if not os.path.exists(OUTCOME_LOG_PATH):
        return None
    last_id = None
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
    os.makedirs(os.path.dirname(OUTCOME_LOG_PATH), exist_ok=True)
    record = {
        "outcome_id": outcome_id,
        "timestamp": datetime.utcnow().isoformat(),
        "process_id": process_id,
        "source_decision_id": "",
        "execution_status": "external",
        "metrics": {"origin": "celery"},
    }
    with open(OUTCOME_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


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
            source_outcome_id = _get_last_outcome_id()
            if not source_outcome_id:
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
                    "raw_video_minio_path": video.file_path,
                    "segments_count": len(segments),
                    "transcriptions_count": len(transcriptions),
                    "duration": video.duration,
                },
            )
            persist_observation(observation)
            try:
                persist_state_from_observation(observation)
            except Exception as e:
                logger.error(f"Failed to persist state from observation: {e}")

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
            source_outcome_id = _get_last_outcome_id()
            if not source_outcome_id:
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
                    "raw_video_minio_path": (video.file_path if video else None),
                },
            )
            persist_observation(observation)
            try:
                persist_state_from_observation(observation)
            except Exception as e:
                logger.error(f"Failed to persist state from observation: {e}")
        except Exception:
            pass
        raise e
    finally:
        session.close()
