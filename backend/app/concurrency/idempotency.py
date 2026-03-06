from __future__ import annotations

import hashlib
from time import time
from typing import Any, Callable

from app.concurrency.store_jsonl import append_concurrency_event, read_concurrency_events


class IdempotencyManager:
    """Gerencia reserva idempotente de operacoes criticas por op_key."""

    def __init__(
        self,
        *,
        event_sink: Callable[[dict[str, Any]], None] | None = None,
        event_source: Callable[[], list[dict[str, Any]]] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._event_sink = event_sink or append_concurrency_event
        self._event_source = event_source or (lambda: read_concurrency_events())
        self._clock = clock or time

    def idempotency_check_or_reserve(self, op_key: str, payload_hash: str) -> str:
        """Reserva operacao por op_key retornando WRITTEN, NOOP ou CONFLICT."""
        state = self._latest_state().get(op_key)
        now = self._clock()
        if state is None:
            self._event_sink(
                {
                    "event_type": "IDEMPOTENCY/op_reserved",
                    "reason_code": "IDEMPOTENCY_RESERVED",
                    "op_key": op_key,
                    "payload_hash": payload_hash,
                    "status": "WRITTEN",
                    "ts": now,
                }
            )
            return "WRITTEN"

        existing_hash = str(state.get("payload_hash", ""))
        if existing_hash == payload_hash:
            self._event_sink(
                {
                    "event_type": "IDEMPOTENCY/op_noop",
                    "reason_code": "IDEMPOTENCY_NOOP",
                    "op_key": op_key,
                    "payload_hash": payload_hash,
                    "status": "NOOP",
                    "ts": now,
                }
            )
            return "NOOP"

        self._event_sink(
            {
                "event_type": "IDEMPOTENCY/op_conflict",
                "reason_code": "IDEMPOTENCY_CONFLICT",
                "op_key": op_key,
                "payload_hash": payload_hash,
                "existing_payload_hash": existing_hash,
                "status": "CONFLICT",
                "ts": now,
            }
        )
        return "CONFLICT"

    def finalize_op(self, op_key: str, status: str) -> None:
        """Marca conclusao de operacao reservada para auditoria."""
        self._event_sink(
            {
                "event_type": "IDEMPOTENCY/op_finalized",
                "reason_code": "IDEMPOTENCY_FINALIZED",
                "op_key": op_key,
                "status": status,
                "ts": self._clock(),
            }
        )

    def _latest_state(self) -> dict[str, dict[str, Any]]:
        state: dict[str, dict[str, Any]] = {}
        for event in self._event_source():
            op_key = event.get("op_key")
            if not isinstance(op_key, str) or not op_key:
                continue
            if str(event.get("event_type", "")).startswith("IDEMPOTENCY/"):
                state[op_key] = dict(event)
        return state


def payload_hash(payload: dict[str, Any]) -> str:
    """Calcula hash canonico para payload usado nas reservas idempotentes."""
    raw = repr(sorted(payload.items())).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
