from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.concurrency.errors import LeaseDeniedError
from app.concurrency.lease import LeaseManager


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class LeaseManagerD12Tests(unittest.TestCase):
    def test_acquire_e_deny_quando_owner_ativo(self) -> None:
        clock = FakeClock()
        manager = LeaseManager(clock=clock, event_sink=lambda _: None)
        manager.acquire_lease("LEASE_WINDOW:acc:w1", 30, "owner-a")

        with self.assertRaises(LeaseDeniedError):
            manager.acquire_lease("LEASE_WINDOW:acc:w1", 30, "owner-b")

    def test_acquire_apos_expiry(self) -> None:
        clock = FakeClock()
        manager = LeaseManager(clock=clock, event_sink=lambda _: None)
        manager.acquire_lease("LEASE_WINDOW:acc:w1", 10, "owner-a")
        clock.advance(11)

        handle_b = manager.acquire_lease("LEASE_WINDOW:acc:w1", 10, "owner-b")
        self.assertEqual(handle_b.owner_id, "owner-b")

    def test_renew_retorna_false_quando_expirada(self) -> None:
        clock = FakeClock()
        manager = LeaseManager(clock=clock, event_sink=lambda _: None)
        handle = manager.acquire_lease("LEASE_WINDOW:acc:w1", 10, "owner-a")
        clock.advance(11)

        self.assertFalse(manager.renew_lease(handle))


if __name__ == "__main__":
    unittest.main()
