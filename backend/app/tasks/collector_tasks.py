from app.worker import celery_app # Importa a instância do Celery
from app.agents.collector.service import CollectorAgent # Importa o agente coletor
from app.agents.segmenter.service import SegmenterAgent # Importa o agente segmentador
from app.agents.transcriber.service import TranscriberAgent # Importa o agente transcritor
from app.db.models import Video, VideoSegment # Importa os modelos Video e VideoSegment
from app.services.storage import MinioService # Serviço de armazenamento MinIO
import os
import uuid
from sqlalchemy import create_engine # create_engine para criar engine de DB
from sqlalchemy.orm import sessionmaker # sessionmaker para criar sessões
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            
            # Store segment objects to map IDs later
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
            
            # Refresh to get IDs
            for s in db_segments:
                session.refresh(s)
            
            # Map internal segment_id (0, 1, 2...) to DB UUID
            # segments list from SegmenterAgent has 'segment_id': 0, 1...
            # We need to pass the DB UUID to the transcriber or map it back.
            # Simpler approach: construct a map based on index since order is preserved
            
            # Add DB UUID to the segments list passed to transcriber
            for i, seg in enumerate(segments):
                if i < len(db_segments):
                    seg['db_id'] = str(db_segments[i].id)

            logger.info("Segments committed to DB.")

            # Validate transcriptions structure

            # Better approach: 
            # The TranscriberAgent takes 'segment_id' from input and returns it.
            # So if we put the DB UUID into 'segment_id' field of the input dict, we get it back.
            
            # Prepare segments for transcriber with UUID as identification
            transcriber_input = []
            for i, seg in enumerate(segments):
                transcriber_input.append({
                    "segment_id": str(db_segments[i].id), # Pass UUID here!
                    "start_time": seg["start_time"],
                    "end_time": seg["end_time"]
                })

            transcriber = TranscriberAgent()
            transcriptions = transcriber.transcribe(local_file_path, transcriber_input)

            # Update segments using UUID
            for trans in transcriptions:
                seg_uuid = trans['segment_id']
                text = trans['text']
                
                if text:
                    logger.info(f"Updating segment {seg_uuid} (Type: {type(seg_uuid)}) with text length: {len(text)}")
                    try:
                        # Ensure UUID format
                        real_uuid = uuid.UUID(str(seg_uuid))
                        
                        # Execute Update
                        updated_rows = session.query(VideoSegment).filter(VideoSegment.id == real_uuid).update({"transcript_text": text})
                        logger.info(f"Updated {updated_rows} rows for segment {real_uuid}")
                        
                        if updated_rows == 0:
                            logger.warning(f"⚠️ Initial update failed for {real_uuid}. Trying commit and retry.")
                            session.commit()
                            # Fallback: fetch and update object directly
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
        raise e
    finally:
        session.close()
