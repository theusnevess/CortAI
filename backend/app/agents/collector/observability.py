from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.collector.utils import parse_minio_path
from app.config.runtime import require_database_url
from app.db.models import ObservationRecord

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None
_SENSITIVE_QUERY_KEYS = {"token", "sig", "signature", "key", "auth", "access_token"}


def collector_observability_enabled() -> bool:
    """Retorna se a emissao de eventos do coletor esta habilitada."""
    raw = os.getenv("COLLECTOR_OBSERVABILITY", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _get_sessionmaker():
    """Cria a sessao sincrona de forma lazy para emissao best-effort."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(require_database_url())
        _SessionLocal = sessionmaker(bind=_engine)
    return _SessionLocal


def sanitize_source_ref(source_ref: str | None) -> str | None:
    """Remove querystrings sensiveis antes de persistir a URL da coleta."""
    if not isinstance(source_ref, str) or not source_ref:
        return source_ref

    parts = urlsplit(source_ref)
    if not parts.query:
        return source_ref

    query_items = []
    stripped = False
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() in _SENSITIVE_QUERY_KEYS:
            stripped = True
            continue
        query_items.append((key, value))

    if stripped:
        query = urlencode(query_items)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))
    return source_ref


def build_collector_run_facts(
    *,
    source_ref: str,
    result: dict[str, Any],
    duration_ms: int,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Constroi o payload compacto de observability para uma execucao do coletor."""
    error = result.get("error") if isinstance(result, dict) else None
    minio_path = result.get("minio_path") if isinstance(result, dict) else None
    source_type = result.get("source_type") if isinstance(result, dict) else None

    bucket = None
    key_prefix = None
    if isinstance(minio_path, str) and minio_path:
        try:
            parsed = parse_minio_path(minio_path)
            bucket = parsed.bucket
            key_prefix = parsed.key[:32]
        except ValueError:
            bucket = None
            key_prefix = None

    facts = {
        "event_type": "collector_run",
        "status": "failed" if isinstance(error, dict) and error.get("error_type") else "success",
        "source_type": source_type if isinstance(source_type, str) else None,
        "duration_ms": int(max(0, duration_ms)),
        "error_type": error.get("error_type") if isinstance(error, dict) else None,
        "http_status": error.get("http_status") if isinstance(error, dict) else None,
        "retryable": bool(error.get("retryable")) if isinstance(error, dict) else False,
        "job_id": job_id,
        "source_ref": sanitize_source_ref(source_ref),
        "minio_bucket": bucket,
        "minio_key_prefix": key_prefix,
    }
    return facts


def persist_collector_run_observation(
    *,
    process_id: str,
    source_outcome_id: str,
    facts: dict[str, Any],
) -> None:
    """Persiste um evento collector_run em observations com custo O(1)."""
    SessionLocal = _get_sessionmaker()
    session = SessionLocal()
    try:
        session.add(
            ObservationRecord(
                observation_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                process_id=process_id,
                source_outcome_id=source_outcome_id,
                facts=facts,
            )
        )
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error("collector_run_observation_failed err=%s", exc)
    finally:
        session.close()
