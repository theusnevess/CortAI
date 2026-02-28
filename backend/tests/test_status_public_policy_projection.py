from __future__ import annotations

from app.api.v1.endpoints.status import _extract_optional_policy_fields


def test_extract_optional_policy_fields_v02_shape_and_sanitization() -> None:
    panel = {
        "policy": {
            "version": "v0.2",
            "score": 42,
            "state": "action_required",
            "decision": "investigate_now",
            "signals": {
                "collector_failed": 3,
                "collector_success": 1,
                "retryable_failures": 2,
                "last_events": [{"ts": "leak"}],
                "nested": {"nope": True},
                "job_id": "SHOULD_NOT_LEAK",
            },
        },
        "collector": {"last_events": [{"job_id": "SHOULD_NOT_LEAK"}]},
        "policy_bridge": {"debug": "SHOULD_NOT_LEAK"},
        "operational_decision": {"debug": "SHOULD_NOT_LEAK"},
    }

    out = _extract_optional_policy_fields(panel)

    assert out["decision_state"] == "action_required"
    assert out["decision_action"] == "investigate_now"
    assert out["score"] == 42
    assert out["signals"]["collector_failed"] == 3
    assert out["signals"]["collector_success"] == 1
    assert out["signals"]["retryable_failures"] == 2
    assert "last_events" not in out["signals"]
    assert "nested" not in out["signals"]
    assert "job_id" not in out["signals"]
    assert "collector" not in out
    assert "policy_bridge" not in out
    assert "operational_decision" not in out


def test_extract_optional_policy_fields_legacy_fallback_and_list_signal_sanitization() -> None:
    panel = {
        "policy": {
            "system_state": "degraded",
            "trust_score": 73,
            "signals": [
                "collector_failed=2",
                "source_ref=https://should-not-leak",
                "collector_error_type:http_4xx=2",
            ],
        }
    }

    out = _extract_optional_policy_fields(panel)

    assert out["decision_state"] == "degraded"
    assert out["score"] == 73
    assert out["signals"]["items"] == [
        "collector_failed=2",
        "collector_error_type:http_4xx=2",
    ]


def test_extract_optional_policy_fields_empty_without_policy() -> None:
    assert _extract_optional_policy_fields({}) == {}
