import os
import re
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import PublishReceipt

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cortai_admin:cortai_secret_pass_123@db:5432/cortai_db",
)
_engine = None
_SessionLocal = None


def _get_sessionmaker():
    """
    Cria SessionLocal de forma lazy para persistencia sincrona de recibos.
    """
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(DATABASE_URL)
        _SessionLocal = sessionmaker(bind=_engine)
    return _SessionLocal


def _sanitize_error_message(message: Optional[str]) -> Optional[str]:
    """
    Remove paths sensiveis da mensagem de erro para manter contrato sem caminhos.
    """
    if not isinstance(message, str) or not message:
        return None
    sanitized = message
    # Remove caminhos unix/windows comuns.
    sanitized = re.sub(r"([A-Za-z]:\\\\[^\s]+)", "<path>", sanitized)
    sanitized = re.sub(r"(/[^\s]+)", "<path>", sanitized)
    return sanitized[:500]


def upsert_publish_receipt(
    *,
    publish_decision_id: str,
    process_id: str,
    manifest_decision_id: Optional[str],
    execution_status: str,
    target: str = "unknown",
    external_post_id: Optional[str] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """
    Persiste recibo de publish com idempotencia por publish_decision_id.
    Usa update deterministico quando ja existir.
    """
    if execution_status == "success":
        pipeline_status = "published"
        published_at = datetime.utcnow()
    elif execution_status == "blocked":
        pipeline_status = "blocked"
        published_at = None
    else:
        pipeline_status = "failed"
        published_at = None

    SessionLocal = _get_sessionmaker()
    session = SessionLocal()
    try:
        existing = session.get(PublishReceipt, publish_decision_id)
        if existing:
            existing.process_id = process_id
            existing.manifest_decision_id = manifest_decision_id
            existing.pipeline_status = pipeline_status
            existing.execution_status = execution_status
            existing.target = target or "unknown"
            existing.external_post_id = external_post_id
            existing.error_type = error_type
            existing.error_message = _sanitize_error_message(error_message)
            existing.published_at = published_at
        else:
            session.add(
                PublishReceipt(
                    publish_decision_id=publish_decision_id,
                    process_id=process_id,
                    manifest_decision_id=manifest_decision_id,
                    pipeline_status=pipeline_status,
                    execution_status=execution_status,
                    target=target or "unknown",
                    external_post_id=external_post_id,
                    error_type=error_type,
                    error_message=_sanitize_error_message(error_message),
                    published_at=published_at,
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
