from __future__ import annotations

"""Congela o shape das projecoes public-ish do fluxo de decisao offline.

Se este teste falhar por mudanca deliberada de contrato, atualize os snapshots
em `backend/tests/snapshots/*.json` somente apos revisar o diff manualmente.
Nao atualize snapshots para esconder regressao. Garanta que `policy.as_of`
continue normalizado e que nao entrem campos instaveis (`ts`, `uuid`, `job_id`,
`trace_id`) nem dados sensiveis.
"""

import json
from pathlib import Path
from typing import Any

from app.api.v1.endpoints.observability import (
    _derive_action_recommendation,
    _derive_trust_banner,
    _harmonize_policy_trust_recommendation,
)
from app.decision_core.policy import derive_operational_policy
from app.decision_core.projection import extract_optional_policy_fields, project_operational_decision

SNAPSHOT_DIR = Path(__file__).with_name("snapshots")


def _make_summary(
    *,
    success: int,
    failed: int,
    by_error_type: dict[str, int] | None = None,
    last_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "window_minutes": 15,
        "events": {"success": success, "failed": failed},
        "by_error_type": by_error_type or {},
        "last_events": last_events or [],
    }


def _normalize_dynamic_fields(value: Any) -> Any:
    if isinstance(value, dict):
        out = {key: _normalize_dynamic_fields(inner) for key, inner in value.items()}
        policy = out.get("policy")
        if isinstance(policy, dict) and isinstance(policy.get("as_of"), str):
            policy["as_of"] = "<normalized>"
        return out
    if isinstance(value, list):
        return [_normalize_dynamic_fields(item) for item in value]
    return value


def _build_snapshot_payload(summary: dict[str, Any]) -> dict[str, Any]:
    policy = derive_operational_policy(summary)
    response = {
        "policy": policy,
        "operational_decision": project_operational_decision(policy),
        "read_path": {"overview_snapshot_status": "fresh", "jobs_queued_count": 0},
        "guardrails": {"events": {}},
        "overall": {"score": "PASS", "reasons": []},
    }
    response["trust"] = _derive_trust_banner(
        overall=response["overall"],
        read_path=response["read_path"],
        guardrails=response["guardrails"],
    )
    response["recommendation"] = _derive_action_recommendation(
        trust=response["trust"],
        read_path=response["read_path"],
        guardrails=response["guardrails"],
        c1_health=response["overall"],
    )
    _harmonize_policy_trust_recommendation(response)

    return _normalize_dynamic_fields(
        {
            "policy": response["policy"],
            "operational_decision": response["operational_decision"],
            "trust": response["trust"],
            "recommendation": response["recommendation"],
            "status_public_optional": extract_optional_policy_fields({"policy": response["policy"]}),
        }
    )


def _load_snapshot(name: str) -> dict[str, Any]:
    return json.loads((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def test_contract_freeze_stable_snapshot() -> None:
    payload = _build_snapshot_payload(_make_summary(success=10, failed=0))
    assert payload == _load_snapshot("decision_flow_stable.json")


def test_contract_freeze_degraded_snapshot() -> None:
    payload = _build_snapshot_payload(
        _make_summary(
            success=4,
            failed=2,
            last_events=[
                {"status": "failed", "retryable": True},
                {"status": "failed", "retryable": True},
            ],
        )
    )
    assert payload == _load_snapshot("decision_flow_degraded.json")


def test_contract_freeze_action_required_snapshot() -> None:
    payload = _build_snapshot_payload(
        _make_summary(
            success=0,
            failed=5,
            by_error_type={"ssl_cert_verify_failed": 1},
            last_events=[{"status": "failed", "retryable": False}],
        )
    )
    assert payload == _load_snapshot("decision_flow_action_required.json")
