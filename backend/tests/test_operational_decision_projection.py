from __future__ import annotations

from app.api.v1.endpoints.observability import _project_operational_decision


def test_operational_decision_projection_from_policy() -> None:
    policy = {
        "version": "v0.2",
        "score": 80,
        "state": "healthy",
        "decision": "continue",
        "signals": {"collector_failed_recent": False},
    }

    projected = _project_operational_decision(policy)

    assert projected is not None
    assert projected["version"] == "v0.2"
    assert projected["score"] == 80
    assert projected["state"] == "healthy"
    assert projected["decision"] == "continue"
    assert projected["signals"]["collector_failed_recent"] is False


def test_operational_decision_projection_returns_none_for_invalid_policy() -> None:
    assert _project_operational_decision(None) is None
