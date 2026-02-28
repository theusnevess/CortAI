from __future__ import annotations

from app.api.v1.endpoints.observability import _harmonize_policy_trust_recommendation


def test_policy_state_pior_que_trust_piora_trust_conservador():
    response = {
        "policy": {"state": "action_required", "decision": "investigate_now"},
        "trust": {
            "state": "green",
            "decision": "healthy",
            "message": "ok",
            "derived_from": ["snapshot"],
        },
        "recommendation": {"action": "none", "message": "n/a", "derived_from": ["legacy"]},
        "operational_decision": {"state": "action_required", "decision": "investigate_now"},
    }

    _harmonize_policy_trust_recommendation(response)

    assert response["trust"]["decision"] == "action_required"
    assert response["trust"]["state"] == "red"
    assert response["trust"]["derived_from"] == ["policy_harmonized"]
    assert response["recommendation"]["action"] == "inspect_upstream_path"
    assert response["recommendation"]["derived_from"] == ["policy_harmonized"]


def test_policy_degraded_piora_trust_apenas_se_trust_estiver_melhor():
    response = {
        "policy": {"state": "degraded", "decision": "monitor"},
        "trust": {
            "state": "yellow",
            "decision": "degraded",
            "message": "degraded",
            "derived_from": ["stale"],
        },
        "recommendation": {"action": "monitor", "derived_from": ["legacy"]},
    }

    _harmonize_policy_trust_recommendation(response)

    assert response["trust"]["decision"] == "degraded"
    assert response["trust"]["state"] == "yellow"
    assert response["recommendation"]["action"] == "monitor"


def test_policy_stable_nao_melhora_trust():
    response = {
        "policy": {"state": "stable", "decision": "monitor"},
        "trust": {
            "state": "red",
            "decision": "action_required",
            "message": "bad",
            "derived_from": ["missing"],
        },
        "recommendation": {"action": "run_warmup", "derived_from": ["legacy"]},
    }

    _harmonize_policy_trust_recommendation(response)

    assert response["trust"]["decision"] == "action_required"
    assert response["trust"]["state"] == "red"
    assert response["recommendation"]["action"] == "run_warmup"


def test_policy_decision_mapeia_para_recommendation_enum():
    response = {
        "policy": {"state": "degraded", "decision": "inspect"},
        "trust": {"state": "green", "decision": "healthy", "derived_from": ["snapshot"]},
        "recommendation": {"action": "none", "derived_from": ["legacy"]},
    }

    _harmonize_policy_trust_recommendation(response)

    assert response["recommendation"]["action"] == "open_report"
    assert response["trust"]["state"] == "yellow"
    assert response["trust"]["decision"] == "degraded"
