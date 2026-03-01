from __future__ import annotations

from app.decision_core.policy import derive_operational_policy, derive_policy_bridge


def test_decision_core_policy_none_summary_is_neutral() -> None:
    policy = derive_operational_policy(None)

    assert policy["version"] == "v0.2"
    assert policy["score"] == 100
    assert policy["state"] == "stable"
    assert policy["decision"] == "monitor"
    assert policy["trust_score"] == 100
    assert policy["system_state"] == "healthy"


def test_decision_core_policy_degraded_is_deterministic() -> None:
    collector_summary = {
        "events": {"success": 10, "failed": 0},
        "by_error_type": {},
        "last_events": [
            {"status": "failed", "retryable": False, "error_type": "http_4xx"},
            {"status": "failed", "retryable": False, "error_type": "timeout"},
        ],
    }

    policy = derive_operational_policy(collector_summary)

    assert policy["score"] == 70
    assert policy["state"] == "degraded"
    assert policy["decision"] == "inspect"
    assert policy["signals"] == []


def test_decision_core_policy_bridge_is_aditive_and_sanitized() -> None:
    collector_summary = {
        "events": {"success": 1, "failed": 3},
        "by_error_type": {"ssl_cert_verify_failed": 1},
        "last_events": [],
    }

    bridge = derive_policy_bridge(collector_summary, as_of="2026-02-28T00:00:00+00:00")

    assert bridge is not None
    assert bridge["version"] == "v0.2"
    assert bridge["severity"] == "critical"
    assert isinstance(bridge["next_actions"], list)
    assert bridge["as_of"] == "2026-02-28T00:00:00+00:00"
