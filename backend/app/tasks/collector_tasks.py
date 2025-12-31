from app.worker import celery_app # Importa a instância do Celery
from app.agents.collector.service import CollectorAgent # Importa o agente coletor
from app.db.models import Video # Importa o modelo Video
import os
import uuid
from sqlalchemy import create_engine # create_engine para criar engine de DB
from sqlalchemy.orm import sessionmaker # sessionmaker para criar sessões   

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
            video.status = "completed"
            session.add(video)
            session.commit()

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
