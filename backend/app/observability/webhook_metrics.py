from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any

_LATENCY_WINDOW = 100


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _p95(values: list[int]) -> int | None:
    """
    Deterministic p95 using nearest-rank.
    """
    if not values:
        return None
    ordered = sorted(values)
    rank = int((95 * len(ordered) + 99) // 100)
    index = max(0, min(len(ordered) - 1, rank - 1))
    return int(ordered[index])


class WebhookMetrics:
    """
    Best-effort in-memory metrics for public status webhook delivery.
    In v0.1 this is intentionally process-local.
    """

    _lock = Lock()
    _sent = 0
    _success = 0
    _error = 0
    _last_error_status: int | None = None
    _last_error_ts: str | None = None
    _latencies_ms = deque(maxlen=_LATENCY_WINDOW)

    @classmethod
    def record_attempt(cls) -> None:
        with cls._lock:
            cls._sent += 1

    @classmethod
    def record_success(cls, *, latency_ms: int, status: int) -> None:
        with cls._lock:
            cls._success += 1
            cls._latencies_ms.append(max(0, int(latency_ms)))

    @classmethod
    def record_error(cls, *, latency_ms: int, status: int | None) -> None:
        with cls._lock:
            cls._error += 1
            cls._latencies_ms.append(max(0, int(latency_ms)))
            cls._last_error_status = int(status) if status is not None else None
            cls._last_error_ts = _utc_now_iso()

    @classmethod
    def snapshot(cls) -> dict[str, Any]:
        with cls._lock:
            sent = int(cls._sent)
            error = int(cls._error)
            latencies = list(cls._latencies_ms)
            return {
                "sent": sent,
                "success": int(cls._success),
                "error": error,
                "error_rate": float(error / sent) if sent > 0 else 0.0,
                "p95_latency_ms": _p95(latencies),
                "last_error_status": cls._last_error_status,
                "last_error_ts": cls._last_error_ts,
            }

    @classmethod
    def _reset_for_tests(cls) -> None:
        with cls._lock:
            cls._sent = 0
            cls._success = 0
            cls._error = 0
            cls._last_error_status = None
            cls._last_error_ts = None
            cls._latencies_ms = deque(maxlen=_LATENCY_WINDOW)
