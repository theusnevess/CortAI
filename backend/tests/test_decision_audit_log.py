from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from app.observability.decision_audit_log import (
    append_decision_audit,
    maybe_append_decision_audit,
    sanitize_decision_payload,
)


class FakeSession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.committed = False
        self.rolled_back = False

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


def test_sanitize_removes_blocked_keys_and_strings() -> None:
    payload = {
        "policy": {
            "signals": {
                "ok": 1,
                "leak": {"source_ref": "http://x", "minio_path": "bucket/key"},
                "bad_list": [{"job_id": "123"}],
            }
        },
        "as_of": "2026-01-01T00:00:00Z",
        "operational_decision": {"action": "monitor"},
        "source_ref": "should_drop",
        "some_str": "contains key=SECRET",
    }
    out = sanitize_decision_payload(payload)
    assert "source_ref" not in out
    assert out["some_str"] == "[redacted]"
    assert out["policy"]["signals"]["leak"] == "[redacted]"
    assert out["policy"]["signals"]["bad_list"] == "[redacted]"


def test_append_writes_sanitized_row_best_effort(monkeypatch) -> None:
    class DummyRow:
        def __init__(self, **kwargs: Any) -> None:
            self.payload = kwargs["payload"]
            self.kwargs = kwargs

    import app.observability.decision_audit_log as mod

    monkeypatch.setattr(mod, "DecisionAuditLog", DummyRow)

    session = FakeSession()
    policy = {
        "version": "v0.2",
        "state": "degraded",
        "score": 55,
        "decision": "monitor",
        "signals": {"ok": True, "source_ref": "drop-me"},
    }
    operational_decision = {"state": "degraded", "action": "monitor"}

    asyncio.run(
        append_decision_audit(
            session,
            source="observability_overview",
            request_id=None,
            policy=policy,
            operational_decision=operational_decision,
            as_of="2026-01-01T00:00:00Z",
        )
    )

    assert session.committed is True
    assert len(session.added) == 1
    assert "source_ref" not in session.added[0].payload["policy"]["signals"]


def test_maybe_append_respects_flag_off(monkeypatch) -> None:
    import app.observability.decision_audit_log as mod

    called = False

    async def _fake_append(*args: Any, **kwargs: Any) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(mod, "append_decision_audit", _fake_append)
    monkeypatch.setenv("DECISION_AUDIT_LOG", "0")

    wrote = asyncio.run(
        maybe_append_decision_audit(
            FakeSession(),
            source="observability_overview",
            request_id=None,
            response={"policy": {"version": "v0.2"}},
        )
    )

    assert wrote is False
    assert called is False


def test_maybe_append_calls_writer_once_when_flag_on(monkeypatch) -> None:
    import app.observability.decision_audit_log as mod

    called = 0

    async def _fake_append(*args: Any, **kwargs: Any) -> None:
        nonlocal called
        called += 1

    monkeypatch.setattr(mod, "append_decision_audit", _fake_append)
    monkeypatch.setenv("DECISION_AUDIT_LOG", "1")

    wrote = asyncio.run(
        maybe_append_decision_audit(
            FakeSession(),
            source="observability_overview",
            request_id=None,
            response={
                "policy": {"version": "v0.2", "state": "degraded", "decision": "monitor", "score": 55},
                "operational_decision": {"state": "degraded", "action": "monitor"},
                "as_of": "2026-03-01T00:00:00Z",
            },
        )
    )

    assert wrote is True
    assert called == 1


def test_append_skips_duplicate_inside_dedup_window(monkeypatch) -> None:
    class DummyRow:
        def __init__(self, **kwargs: Any) -> None:
            self.payload = kwargs["payload"]
            self.kwargs = kwargs

    import app.observability.decision_audit_log as mod

    monkeypatch.setattr(mod, "DecisionAuditLog", DummyRow)

    now = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

    async def _fake_latest(session: Any):
        return (now - timedelta(seconds=30), "degraded", "monitor", 11)

    monkeypatch.setattr(mod, "_load_latest_audit_signature", _fake_latest)

    session = FakeSession()
    policy = {
        "version": "v0.2",
        "state": "degraded",
        "score": 55,
        "decision": "monitor",
        "signals": {"ok": True},
    }

    asyncio.run(
        append_decision_audit(
            session,
            source="observability_overview",
            request_id=None,
            policy=policy,
            operational_decision={"state": "degraded", "action": "monitor"},
            as_of="2026-03-01T12:00:00Z",
            now=now,
        )
    )

    assert session.committed is False
    assert session.rolled_back is False
    assert session.added == []


def test_append_writes_again_outside_dedup_window(monkeypatch) -> None:
    class DummyRow:
        def __init__(self, **kwargs: Any) -> None:
            self.payload = kwargs["payload"]
            self.kwargs = kwargs

    import app.observability.decision_audit_log as mod

    monkeypatch.setattr(mod, "DecisionAuditLog", DummyRow)

    now = datetime(2026, 3, 1, 12, 2, 0, tzinfo=timezone.utc)

    async def _fake_latest(session: Any):
        return (now - timedelta(seconds=61), "degraded", "monitor", 11)

    monkeypatch.setattr(mod, "_load_latest_audit_signature", _fake_latest)

    session = FakeSession()
    policy = {
        "version": "v0.2",
        "state": "degraded",
        "score": 55,
        "decision": "monitor",
        "signals": {"ok": True},
    }

    asyncio.run(
        append_decision_audit(
            session,
            source="observability_overview",
            request_id=None,
            policy=policy,
            operational_decision={"state": "degraded", "action": "monitor"},
            as_of="2026-03-01T12:02:00Z",
            now=now,
        )
    )

    assert session.committed is True
    assert len(session.added) == 1


def test_append_is_best_effort_when_commit_fails(monkeypatch) -> None:
    class DummyRow:
        def __init__(self, **kwargs: Any) -> None:
            self.payload = kwargs["payload"]
            self.kwargs = kwargs

    class BrokenCommitSession(FakeSession):
        async def commit(self) -> None:
            raise RuntimeError("db write failed")

    import app.observability.decision_audit_log as mod

    monkeypatch.setattr(mod, "DecisionAuditLog", DummyRow)

    session = BrokenCommitSession()
    policy = {
        "version": "v0.2",
        "state": "degraded",
        "score": 55,
        "decision": "monitor",
        "signals": {"ok": True},
    }

    asyncio.run(
        append_decision_audit(
            session,
            source="observability_overview",
            request_id=None,
            policy=policy,
            operational_decision={"state": "degraded", "action": "monitor"},
            as_of="2026-03-01T12:04:00Z",
        )
    )

    assert session.rolled_back is True
    assert len(session.added) == 1


def test_append_writes_when_fingerprint_changes_inside_window(monkeypatch) -> None:
    class DummyRow:
        def __init__(self, **kwargs: Any) -> None:
            self.payload = kwargs["payload"]
            self.kwargs = kwargs

    import app.observability.decision_audit_log as mod

    monkeypatch.setattr(mod, "DecisionAuditLog", DummyRow)

    now = datetime(2026, 3, 1, 12, 3, 0, tzinfo=timezone.utc)

    async def _fake_latest(session: Any):
        return (now - timedelta(seconds=10), "degraded", "monitor", 11)

    monkeypatch.setattr(mod, "_load_latest_audit_signature", _fake_latest)

    session = FakeSession()
    policy = {
        "version": "v0.2",
        "state": "action_required",
        "score": 55,
        "decision": "investigate_now",
        "signals": {"ok": True},
    }

    asyncio.run(
        append_decision_audit(
            session,
            source="observability_overview",
            request_id=None,
            policy=policy,
            operational_decision={"state": "action_required", "action": "inspect_upstream_path"},
            as_of="2026-03-01T12:03:00Z",
            now=now,
        )
    )

    assert session.committed is True
    assert len(session.added) == 1
