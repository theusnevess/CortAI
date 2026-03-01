from __future__ import annotations

from app.decision_core.harmonization import harmonize_policy_trust_recommendation


def test_decision_core_harmonization_only_worsens_trust() -> None:
    response = {
        "policy": {"state": "action_required", "decision": "investigate_now"},
        "trust": {"state": "green", "decision": "healthy", "derived_from": ["snapshot"]},
        "recommendation": {"action": "none", "derived_from": ["legacy"]},
    }

    harmonize_policy_trust_recommendation(response)

    assert response["trust"]["state"] == "red"
    assert response["trust"]["decision"] == "action_required"
    assert response["recommendation"]["action"] == "inspect_upstream_path"


def test_decision_core_harmonization_never_improves_existing_action() -> None:
    response = {
        "policy": {"state": "stable", "decision": "monitor"},
        "trust": {"state": "red", "decision": "action_required", "derived_from": ["legacy"]},
        "recommendation": {"action": "run_warmup", "derived_from": ["legacy"]},
    }

    harmonize_policy_trust_recommendation(response)

    assert response["trust"]["state"] == "red"
    assert response["trust"]["decision"] == "action_required"
    assert response["recommendation"]["action"] == "run_warmup"
