from __future__ import annotations

from app.decision_core.projection import (
    extract_optional_policy_fields,
    project_operational_decision,
    to_public_status_action,
)


def test_decision_core_projection_operational_decision_mirrors_policy() -> None:
    policy = {
        "version": "v0.2",
        "score": 72,
        "state": "degraded",
        "decision": "inspect",
        "signals": ["collector_failed=2"],
    }

    projected = project_operational_decision(policy)

    assert projected == {
        "version": "v0.2",
        "score": 72,
        "state": "degraded",
        "decision": "inspect",
        "signals": ["collector_failed=2"],
    }


def test_decision_core_projection_public_fields_are_sanitized() -> None:
    panel = {
        "policy": {
            "version": "v0.2",
            "score": 42,
            "state": "action_required",
            "decision": "investigate_now",
            "signals": {
                "collector_failed": 3,
                "job_id": "SHOULD_NOT_LEAK",
                "nested": {"nope": True},
            },
        }
    }

    out = extract_optional_policy_fields(panel)

    assert out["decision_state"] == "action_required"
    assert out["decision_action"] == "investigate_now"
    assert out["score"] == 42
    assert out["signals"]["collector_failed"] == 3
    assert "job_id" not in out["signals"]
    assert "nested" not in out["signals"]


def test_decision_core_projection_maps_public_action_stably() -> None:
    assert to_public_status_action("run_warmup") == "inspect"
    assert to_public_status_action("reduce_force_live_burst") == "monitor"
    assert to_public_status_action("unknown-action") == "inspect"
