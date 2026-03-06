from __future__ import annotations

from app.observability.policy_engine import derive_operational_policy


def test_policy_decision_no_summary_is_stable() -> None:
    policy = derive_operational_policy(None)
    assert policy["version"] == "v0.2"
    assert policy["score"] == 100
    assert policy["state"] == "stable"
    assert policy["decision"] == "monitor"
    assert isinstance(policy["signals"], list)


def test_policy_decision_degraded_with_some_failures() -> None:
    summary = {
        "window_minutes": 15,
        "events": {"success": 3, "failed": 2},
        "by_error_type": {"http_4xx": 2},
        "last_events": [],
    }
    policy = derive_operational_policy(summary)
    assert policy["version"] == "v0.2"
    assert policy["score"] == 80
    assert policy["state"] == "degraded"
    assert policy["decision"] == "inspect"
    assert "collector_failed=2" in policy["signals"]


def test_policy_decision_action_required_on_many_failures() -> None:
    summary = {
        "window_minutes": 15,
        "events": {"success": 0, "failed": 5},
        "by_error_type": {"ssl_cert_verify_failed": 3, "timeout": 2},
        "last_events": [],
    }
    policy = derive_operational_policy(summary)
    assert policy["state"] == "action_required"
    assert policy["decision"] == "investigate_now"
    assert "collector_failed=5" in policy["signals"]
    assert any(signal.startswith("collector_error_type:") for signal in policy["signals"])


def test_policy_decision_signals_are_sanitized_and_small() -> None:
    summary = {
        "window_minutes": 15,
        "events": {"success": 1, "failed": 1},
        "by_error_type": {
            "http_4xx": 1,
            "dns_failed": 1,
            "unknown": 1,
        },
        "last_events": [],
    }
    policy = derive_operational_policy(summary)
    assert isinstance(policy["signals"], list)
    assert len(policy["signals"]) <= 3
