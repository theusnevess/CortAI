from __future__ import annotations

from app.observability.policy_engine import derive_operational_policy


def test_policy_engine_none_summary_is_neutral_healthy():
    policy = derive_operational_policy(None)
    assert policy["trust_score"] == 100
    assert policy["system_state"] == "healthy"
    assert policy["recommendation"] == "normal_operation"
    assert isinstance(policy["as_of"], str) and policy["as_of"]


def test_policy_engine_healthy_when_no_failures():
    collector_summary = {
        "events": {"success": 5, "failed": 0},
        "by_error_type": {},
        "last_events": [],
    }
    policy = derive_operational_policy(collector_summary)
    assert policy["trust_score"] == 100
    assert policy["system_state"] == "healthy"
    assert policy["recommendation"] == "normal_operation"


def test_policy_engine_degraded_is_deterministic():
    collector_summary = {
        "events": {"success": 10, "failed": 0},
        "by_error_type": {},
        "last_events": [
            {"status": "failed", "retryable": False, "error_type": "http_4xx"},
            {"status": "failed", "retryable": False, "error_type": "timeout"},
        ],
    }
    policy = derive_operational_policy(collector_summary)
    assert policy["trust_score"] == 70
    assert policy["system_state"] == "degraded"
    assert policy["recommendation"] == "monitor_collector"


def test_policy_engine_action_required_on_high_failure_rate_and_non_retryable():
    collector_summary = {
        "events": {"success": 2, "failed": 3},
        "by_error_type": {"ssl_cert_verify_failed": 1},
        "last_events": [
            {"status": "failed", "retryable": False, "error_type": "ssl_cert_verify_failed"},
            {"status": "failed", "retryable": False, "error_type": "http_5xx"},
        ],
    }
    policy = derive_operational_policy(collector_summary)
    assert policy["trust_score"] == 15
    assert policy["system_state"] == "action_required"
    assert policy["recommendation"] == "manual_intervention_required"
