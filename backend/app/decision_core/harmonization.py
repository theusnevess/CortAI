from __future__ import annotations

from typing import Any

_TRUST_DECISION_RANK: dict[str, int] = {"healthy": 0, "degraded": 1, "action_required": 2}
_TRUST_STATE_RANK: dict[str, int] = {"green": 0, "yellow": 1, "red": 2}
_POLICY_STATE_TO_TRUST_DECISION: dict[str, str] = {
    "stable": "healthy",
    "degraded": "degraded",
    "action_required": "action_required",
}
_POLICY_STATE_TO_TRUST_STATE: dict[str, str] = {
    "stable": "green",
    "degraded": "yellow",
    "action_required": "red",
}
_POLICY_DECISION_TO_RECO_ACTION: dict[str, str] = {
    "monitor": "monitor",
    "inspect": "open_report",
    "investigate_now": "inspect_upstream_path",
}


def _rank(mapping: dict[str, int], value: str | None) -> int:
    if not value:
        return -1
    return mapping.get(str(value), -1)


def harmonize_policy_trust_recommendation(response: dict[str, Any]) -> None:
    """
    Harmoniza trust e recommendation de forma conservadora.

    `policy.state` so pode piorar trust; `policy.decision` so preenche
    recommendation quando ela estiver ausente ou `none`.
    """
    policy = response.get("policy") or {}
    trust = response.get("trust") or {}
    recommendation = response.get("recommendation") or {}

    policy_state = policy.get("state")
    policy_decision = policy.get("decision")

    desired_trust_decision = _POLICY_STATE_TO_TRUST_DECISION.get(str(policy_state), None)
    desired_trust_state = _POLICY_STATE_TO_TRUST_STATE.get(str(policy_state), None)

    if desired_trust_decision:
        current = trust.get("decision")
        if _rank(_TRUST_DECISION_RANK, desired_trust_decision) > _rank(_TRUST_DECISION_RANK, current):
            trust["decision"] = desired_trust_decision
            trust["derived_from"] = ["policy_harmonized"]

    if desired_trust_state:
        current = trust.get("state")
        if _rank(_TRUST_STATE_RANK, desired_trust_state) > _rank(_TRUST_STATE_RANK, current):
            trust["state"] = desired_trust_state
            trust["derived_from"] = ["policy_harmonized"]

    desired_action = _POLICY_DECISION_TO_RECO_ACTION.get(str(policy_decision), None)
    if desired_action:
        current_action = recommendation.get("action")
        if (not current_action) or (str(current_action) == "none"):
            recommendation["action"] = desired_action
            recommendation["derived_from"] = ["policy_harmonized"]

    response["trust"] = trust
    response["recommendation"] = recommendation
