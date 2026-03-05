from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any, Callable
from uuid import uuid4

from app.concurrency.errors import LeaseDeniedError
from app.concurrency.store_jsonl import append_concurrency_event


@dataclass(frozen=True)
class LeaseHandle:
    """Representa lease ativa para chave de exclusao mutua."""

    key: str
    owner_id: str
    lease_id: str
    ttl_s: int
    expires_at: float


class LeaseManager:
    """Controla leases em memoria com trilha append-only de eventos."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] | None = None,
        event_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self._clock = clock or time
        self._event_sink = event_sink or append_concurrency_event
        self._leases: dict[str, LeaseHandle] = {}

    def acquire_lease(self, key: str, ttl_s: int, owner_id: str) -> LeaseHandle:
        """Adquire lease se nao existir owner ativo para a mesma chave."""
        now = self._clock()
        current = self._leases.get(key)
        if current is not None and current.expires_at > now and current.owner_id != owner_id:
            self._emit(
                {
                    "event_type": "LOCK/lease_denied",
                    "reason_code": "LEASE_DENIED",
                    "key": key,
                    "owner_id": owner_id,
                    "current_owner_id": current.owner_id,
                    "ts": now,
                }
            )
            raise LeaseDeniedError("LEASE_DENIED")

        handle = LeaseHandle(
            key=key,
            owner_id=owner_id,
            lease_id=uuid4().hex,
            ttl_s=ttl_s,
            expires_at=now + ttl_s,
        )
        self._leases[key] = handle
        self._emit(
            {
                "event_type": "LOCK/lease_acquired",
                "reason_code": "LEASE_ACQUIRED",
                "key": key,
                "owner_id": owner_id,
                "lease_id": handle.lease_id,
                "expires_at": handle.expires_at,
                "ts": now,
            }
        )
        return handle

    def renew_lease(self, handle: LeaseHandle) -> bool:
        """Renova lease apenas quando o handle ainda e valido e ativo."""
        now = self._clock()
        current = self._leases.get(handle.key)
        if current is None:
            return False
        if current.lease_id != handle.lease_id or current.owner_id != handle.owner_id:
            return False
        if current.expires_at <= now:
            return False

        renewed = LeaseHandle(
            key=current.key,
            owner_id=current.owner_id,
            lease_id=current.lease_id,
            ttl_s=current.ttl_s,
            expires_at=now + current.ttl_s,
        )
        self._leases[handle.key] = renewed
        self._emit(
            {
                "event_type": "LOCK/lease_renewed",
                "reason_code": "LEASE_RENEWED",
                "key": renewed.key,
                "owner_id": renewed.owner_id,
                "lease_id": renewed.lease_id,
                "expires_at": renewed.expires_at,
                "ts": now,
            }
        )
        return True

    def release_lease(self, handle: LeaseHandle) -> None:
        """Libera lease ativa; release defensivo para handles antigos."""
        now = self._clock()
        current = self._leases.get(handle.key)
        if current is None:
            return
        if current.lease_id == handle.lease_id and current.owner_id == handle.owner_id:
            self._leases.pop(handle.key, None)
            self._emit(
                {
                    "event_type": "LOCK/lease_released",
                    "reason_code": "LEASE_RELEASED",
                    "key": handle.key,
                    "owner_id": handle.owner_id,
                    "lease_id": handle.lease_id,
                    "ts": now,
                }
            )

    def is_lease_active(self, handle: LeaseHandle) -> bool:
        """Indica se o handle continua valido e nao expirou."""
        current = self._leases.get(handle.key)
        if current is None:
            return False
        if current.lease_id != handle.lease_id or current.owner_id != handle.owner_id:
            return False
        return current.expires_at > self._clock()

    def _emit(self, payload: dict[str, Any]) -> None:
        self._event_sink(dict(payload))
