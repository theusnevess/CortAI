import uuid # Gerar UUIDs únicos
from datetime import datetime # Marcação de tempo
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float, Integer, Text, JSON # Tipos de colunas
from sqlalchemy.dialects.postgresql import UUID # Tipo UUID específico do PostgreSQL
from sqlalchemy.orm import relationship # Relacionamentos entre tabelas 
from app.db.base import Base # Importa a base dos modelos 

# --- Tabela de Usuários ---
class User(Base):
    __tablename__ = "users"

    # Usa UUID em vez de ID numérico (1, 2, 3) por segurança.
    # Ninguém consegue adivinhar o ID do próximo usuário.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    email = Column(String, unique=True, index=True, nullable=False) # Email único
    password_hash = Column(String, nullable=False) # Senha hasheada
    name = Column(String) # Nome do usuário
    
    is_active = Column(Boolean, default=True) # Conta ativa ou desativada
    created_at = Column(DateTime, default=datetime.utcnow) # Data de criação
    
    # Relacionamento: "Um Usuário tem muitos Vídeos"
    videos = relationship("Video", back_populates="owner")


# --- Tabela de Vídeos ---
class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) # ID único do vídeo
    
    # Chave Estrangeira: Aponta para a tabela users
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    title = Column(String, nullable=False) # Título do vídeo
    source_url = Column(String, nullable=False) # Link do YouTube ou Caminho do Upload
    duration = Column(Integer) # Duração em segundos
    
    # O Status é vital para nossa arquitetura assíncrona.
    # pending -> downloading -> transcribing -> analyzing -> completed
    status = Column(String, default="pending", index=True)
    
    # Onde o arquivo bruto está salvo no MinIO
    file_path = Column(String)
    
    # Metadados técnicos (resolução, codec, fps) salvos como JSON
    metadata_info = Column(JSON, default={})
    
    # Data de criação do registro
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    owner = relationship("User", back_populates="videos")
    segments = relationship("VideoSegment", back_populates="video")
    clips = relationship("Clip", back_populates="video")


# --- Tabela de Segmentos (Chunks) ---
# Representa as frases ou cenas detectadas pela IA
class VideoSegment(Base):
    __tablename__ = "video_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) # ID único do segmento
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id")) # Chave estrangeira para o vídeo
    
    start_time = Column(Float, nullable=False) # Ex: 10.5 segundos
    end_time = Column(Float, nullable=False)   # Ex: 25.0 segundos
    transcript_text = Column(Text)             # O que foi falado nesse trecho
    
    video = relationship("Video", back_populates="segments") # Relacionamento com Vídeo


# --- Tabela de Cortes Finais (Clipes) ---
# O produto final pronto para postar
class Clip(Base):
    __tablename__ = "clips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) # ID único do clipe
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id")) # Chave estrangeira para o vídeo
    
    title = Column(String) # Título do clipe
    viral_score = Column(Float) # Nota de 0 a 100 dada pela IA
    
    file_path = Column(String) # Onde o clipe está salvo no MinIO
    thumbnail_path = Column(String) # Caminho da miniatura do clipe
    
    status = Column(String, default="created") # created -> uploaded
    
    created_at = Column(DateTime, default=datetime.utcnow) # Data de criação do clipe
    
    video = relationship("Video", back_populates="clips") # Relacionamento com Vídeo