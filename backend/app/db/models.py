import uuid # Gerar UUIDs únicos
from datetime import datetime # Marcação de tempo
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float, Integer, Text, JSON, Date, Numeric, Index # Tipos de colunas
from sqlalchemy.dialects.postgresql import UUID, JSONB # Tipo UUID específico do PostgreSQL
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


# --- Tabela de Execuções Cognitivas (Resumo) ---
class CognitiveRun(Base):
    __tablename__ = "cognitive_runs"

    # process_id é único por execução cognitiva
    process_id = Column(String, primary_key=True)

    pipeline_status = Column(String, nullable=False, default="unknown")
    termination_reason = Column(String, nullable=True)
    terminated = Column(Boolean, default=False)

    source_observation_id = Column(String, nullable=False)
    source_outcome_id = Column(String, nullable=True)
    source_decision_id = Column(String, nullable=True)

    execution_status = Column(String, nullable=True)
    actions_executed = Column(Integer, nullable=True)
    last_action_type = Column(String, nullable=True)

    video_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_cognitive_runs_video_id", "video_id"),
        Index("ix_cognitive_runs_created_at", "created_at"),
    )

# --- Tabela de Observações (Facts) ---
class ObservationRecord(Base):
    __tablename__ = "observations"

    observation_id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    process_id = Column(String, nullable=False, index=True)
    source_outcome_id = Column(String, nullable=False)
    facts = Column(JSONB, nullable=False)  # Facts sem paths, apenas resumo.
    created_at = Column(DateTime, default=datetime.utcnow)

# --- Tabela de Métricas Diárias ---
class CognitiveMetricsDaily(Base):
    __tablename__ = "cognitive_metrics_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_date = Column(Date, nullable=False, unique=True)

    total_runs = Column(Integer, nullable=False)
    completed_runs = Column(Integer, nullable=False)
    failed_runs = Column(Integer, nullable=False)
    blocked_runs = Column(Integer, nullable=False)

    truncated_runs = Column(Integer, nullable=False, default=0)  # Runs truncados.
    truncated_ratio = Column(Numeric(5, 2), nullable=True)  # Razao truncada.

    avg_actions_executed = Column(Numeric(5, 2), nullable=True)
    last_action_type_distribution = Column(JSONB, nullable=False)
    latency_by_action = Column(JSONB, nullable=False, default=dict)  # p95/avg por acao.
    alert_count = Column(Integer, nullable=False, default=0)
    alert_reasons = Column(JSONB, nullable=False, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)


class MetricsEndpointDaily(Base):
    __tablename__ = "metrics_endpoint_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_date = Column(Date, nullable=False)
    endpoint = Column(String, nullable=False)

    count_requests = Column(Integer, nullable=False, default=0)
    p50_ms = Column(Integer, nullable=False, default=0)
    p95_ms = Column(Integer, nullable=False, default=0)
    p99_ms = Column(Integer, nullable=False, default=0)
    error_rate = Column(Numeric(6, 4), nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_metrics_endpoint_daily_metric_date", "metric_date"),
        Index("ix_metrics_endpoint_daily_endpoint", "endpoint"),
        Index(
            "ux_metrics_endpoint_daily_metric_date_endpoint",
            "metric_date",
            "endpoint",
            unique=True,
        ),
    )


class MetricsOverviewReadModel(Base):
    __tablename__ = "metrics_overview_read_model"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    include_reasons = Column(Boolean, nullable=False, default=False)
    include_baseline = Column(Boolean, nullable=False, default=False)
    payload = Column(JSONB, nullable=False, default=dict)
    refreshed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_overview_read_model_start_date", "start_date"),
        Index("ix_overview_read_model_end_date", "end_date"),
        Index(
            "ux_overview_read_model_key",
            "start_date",
            "end_date",
            "include_reasons",
            "include_baseline",
            unique=True,
        ),
    )


# --- Tabela de Recibos de Publicacao ---
class PublishReceipt(Base):
    __tablename__ = "publish_receipts"

    # Chave de idempotencia: uma linha por decisao de publicacao.
    publish_decision_id = Column(String, primary_key=True)

    process_id = Column(String, nullable=False, index=True)
    manifest_decision_id = Column(String, nullable=True, index=True)

    # Status objetivo do publish: published | blocked | failed.
    pipeline_status = Column(String, nullable=False)
    execution_status = Column(String, nullable=False)  # success | blocked | failed

    target = Column(String, nullable=False, default="unknown")
    external_post_id = Column(String, nullable=True)

    error_type = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_publish_receipts_process_id", "process_id"),
        Index("ix_publish_receipts_manifest_decision_id", "manifest_decision_id"),
        Index("ix_publish_receipts_created_at", "created_at"),
    )
