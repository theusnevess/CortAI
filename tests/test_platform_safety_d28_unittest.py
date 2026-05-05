from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.safety.models import AccountMode, AccountSafetyState, RiskLevel
from app.safety.service import SafetyService
from app.safety.store_jsonl import append_account_state, read_all


class PlatformSafetyD28Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.events_path = self.out / "events" / "events.jsonl"
        self.safety_dir = self.out / "safety"
        self.safety = SafetyService(safety_dir=self.safety_dir, event_path=self.events_path)

    def _event_types(self) -> list[str]:
        rows = read_all(self.events_path) if self.events_path.exists() else []
        return [str(row.get("event_type")) for row in rows]

    def test_allow_returns_allow_without_safety_events(self) -> None:
        state, decision = self.safety.evaluate_before_publish(
            account_id="acc_allow",
            now=datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(state.account_id, "acc_allow")
        self.assertEqual(decision.decision.value, "ALLOW")
        self.assertEqual(decision.reason_code, "SAFETY_ALLOW")
        self.assertEqual(self._event_types(), [])

    def test_delay_due_to_pacing_emits_pacing_delay(self) -> None:
        append_account_state(
            AccountSafetyState(
                account_id="acc_delay",
                mode=AccountMode.NORMAL,
                cooldown_until=None,
                last_publish_at="2026-03-07T11:30:00Z",
                posts_last_hour=1,
                posts_last_day=1,
                risk_level=RiskLevel.LOW,
                updated_at="2026-03-07T11:30:00Z",
            ),
            path=self.safety.account_state_path,
        )

        _, decision = self.safety.evaluate_before_publish(
            account_id="acc_delay",
            now=datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(decision.decision.value, "DELAY")
        self.assertTrue(decision.next_allowed_time)
        self.assertIn("SAFETY/pacing_delay", self._event_types())
        self.assertGreaterEqual(len(read_all(self.safety.pacing_events_path)), 1)

    def test_block_due_to_cooldown_emits_publish_blocked(self) -> None:
        append_account_state(
            AccountSafetyState(
                account_id="acc_block",
                mode=AccountMode.COOLDOWN,
                cooldown_until="2026-03-08T12:00:00Z",
                last_publish_at=None,
                posts_last_hour=0,
                posts_last_day=0,
                risk_level=RiskLevel.HIGH,
                updated_at="2026-03-07T11:00:00Z",
            ),
            path=self.safety.account_state_path,
        )

        _, decision = self.safety.evaluate_before_publish(
            account_id="acc_block",
            now=datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(decision.decision.value, "BLOCK")
        self.assertEqual(decision.reason_code, "COOLDOWN_ACTIVE")
        self.assertIn("SAFETY/publish_blocked", self._event_types())

    def test_provider_signal_starts_cooldown_and_future_publish_blocks(self) -> None:
        updated = self.safety.record_provider_signal(
            account_id="acc_risk",
            risk_type="PUBLISH_RATE_LIMIT",
            severity="HIGH",
            ts=datetime(2026, 3, 7, 12, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(updated.risk_level.value, "HIGH")
        self.assertEqual(updated.mode.value, "COOLDOWN")
        self.assertGreaterEqual(len(read_all(self.safety.cooldowns_path)), 1)
        self.assertIn("SAFETY/risk_detected", self._event_types())

        _, decision = self.safety.evaluate_before_publish(
            account_id="acc_risk",
            now=datetime(2026, 3, 7, 12, 35, tzinfo=timezone.utc),
        )
        self.assertEqual(decision.decision.value, "BLOCK")
        self.assertEqual(decision.reason_code, "COOLDOWN_ACTIVE")

    def test_record_publish_success_updates_account_state(self) -> None:
        published_at = datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc)
        updated = self.safety.record_publish_success(account_id="acc_pub", published_at=published_at)
        self.assertEqual(updated.last_publish_at, "2026-03-07T12:00:00Z")
        self.assertEqual(updated.posts_last_hour, 1)
        self.assertEqual(updated.posts_last_day, 1)

        latest = read_all(self.safety.account_state_path)[-1]
        self.assertEqual(latest["account_id"], "acc_pub")
        self.assertEqual(latest["last_publish_at"], "2026-03-07T12:00:00Z")

    def test_persistence_is_append_only_under_out_safety(self) -> None:
        self.safety.evaluate_before_publish(
            account_id="acc_state",
            now=datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc),
        )
        self.safety.record_provider_signal(
            account_id="acc_state",
            risk_type="PUBLISH_RATE_LIMIT",
            severity="HIGH",
            ts=datetime(2026, 3, 7, 12, 45, tzinfo=timezone.utc),
        )

        self.assertGreaterEqual(len(read_all(self.safety.account_state_path)), 2)
        self.assertGreaterEqual(len(read_all(self.safety.cooldowns_path)), 1)
        self.assertTrue(str(self.safety.account_state_path).endswith("OUT\\safety\\account_state.jsonl"))


if __name__ == "__main__":
    unittest.main()
