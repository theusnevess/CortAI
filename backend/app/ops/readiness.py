from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.observability.event_query.index_store.writer import EventIndexWriter
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventQueryFilters
from app.observability.hot_store.writer import HotStoreWriter
from app.runtime.paths import resolve_out_dir
from app.runtime.queue import InMemoryTaskQueue


@dataclass(frozen=True)
class ReadinessStatus:
    """Estado consolidado de readiness operacional."""

    ready: bool
    scheduler: str
    workers: int
    queue: str
    event_index: str
    hot_store: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "scheduler": self.scheduler,
            "workers": self.workers,
            "queue": self.queue,
            "event_index": self.event_index,
            "hot_store": self.hot_store,
        }


def evaluate_readiness(*, base_dir: Path | None = None, min_workers: int = 1) -> ReadinessStatus:
    """Avalia readiness do runtime usando dependências locais e heartbeats observáveis."""
    out_dir = base_dir or resolve_out_dir()
    scheduler_status = "ok"
    queue_status = "ok"
    event_index_status = "ok"
    hot_store_status = "ok"

    try:
        InMemoryTaskQueue()
    except Exception:  # noqa: BLE001
        queue_status = "error"

    try:
        EventIndexWriter(out_dir / "index" / "event_index.sqlite3").ensure_schema()
    except Exception:  # noqa: BLE001
        event_index_status = "error"

    try:
        HotStoreWriter(out_dir / "hot_store" / "events_hot.sqlite3").ensure_schema()
    except Exception:  # noqa: BLE001
        hot_store_status = "error"

    workers = _count_runtime_workers(out_dir)
    ready = (
        scheduler_status == "ok"
        and queue_status == "ok"
        and event_index_status == "ok"
        and hot_store_status == "ok"
        and workers >= min_workers
    )
    return ReadinessStatus(
        ready=ready,
        scheduler=scheduler_status,
        workers=workers,
        queue=queue_status,
        event_index=event_index_status,
        hot_store=hot_store_status,
    )


def _count_runtime_workers(base_dir: Path) -> int:
    indexer = EventIndexer(base_dir=base_dir)
    result = indexer.scan(
        EventQueryFilters(
            start_ts="2026-01-01T00:00:00Z",
            end_ts="2099-01-01T00:00:00Z",
            event_type=None,
            event_type_prefix="RUNTIME/",
            account_id=None,
            window_id=None,
            job_id=None,
            publish_id=None,
            op_key=None,
            severity=None,
            action_taken=None,
        ),
        limit=1000,
    )
    workers: set[str] = set()
    for item in result.items:
        details = item.details or {}
        worker_id = details.get("worker_id")
        if isinstance(worker_id, str) and worker_id:
            workers.add(worker_id)
    return len(workers)
