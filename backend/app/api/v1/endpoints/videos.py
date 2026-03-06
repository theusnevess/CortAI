import os
from fastapi import APIRouter, HTTPException, Depends # Importa dependências do FastAPI
from sqlalchemy.ext.asyncio import AsyncSession # Importa sessão assíncrona do SQLAlchemy
from sqlalchemy.future import select # Função select para consultas
from pydantic import BaseModel # BaseModel do Pydantic para validação de dados
from app.db.session import get_db # Função para obter a sessão do banco de dados
from app.db.models import User, Video # Importa os modelos User e Video
from app.tasks.collector_tasks import process_video_task # Task Celery para processar vídeos
import uuid # Biblioteca para manipulação de UUIDs

router = APIRouter() # Cria um roteador para os endpoints de vídeo

# Modelo de entrada
class VideoCreateRequest(BaseModel):
    url: str

# Função auxiliar para criar um usuário "admin" se não existir
async def get_default_user(db: AsyncSession):
    # Procura um usuário existente
    result = await db.execute(select(User).limit(1))
    user = result.scalars().first()
    
    if not user:
        # Se não tiver ninguém, cria o Admin
        user = User(
            email="admin@cortai.com",
            password_hash=os.getenv("BOOTSTRAP_ADMIN_PASSWORD_HASH", "bootstrap-disabled"),
            name="Admin User"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

# Endpoint para criar um novo vídeo
@router.post("/", status_code=201)
async def create_video(request: VideoCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    1. Cria registro no Banco de Dados (Status: Pending)
    2. Executa o Agente Coletor (Download + Upload)
    3. Atualiza o Banco com o resultado
    """
    try:
        # Pega o usuário padrão
        user = await get_default_user(db)

        # Cria o registro do vídeo "Pending" no banco
        new_video = Video(
            user_id=user.id,
            title="Processando...", # Será atualizado depois
            source_url=request.url,
            status="downloading"
        )
        db.add(new_video)
        await db.commit()
        await db.refresh(new_video)

        print(f"💾 Vídeo salvo no banco com ID: {new_video.id}")

        # Enfileira a task Celery para processar o vídeo em background
        process_video_task.delay(str(new_video.id), request.url)

        # Retorna a resposta inicial
        return {
            "id": str(new_video.id),
            "status": "processing",
            "message": "Vídeo enfileirado para processamento"
        }

    except Exception as e:
        # Se der erro, tenta marcar como falha no banco
        if 'new_video' in locals():
            new_video.status = "failed"
            db.add(new_video)
            await db.commit()
        raise HTTPException(status_code=500, detail=str(e))