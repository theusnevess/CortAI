from __future__ import annotations

from typing import Any

from app.api.v1.endpoints.observability import (
    _derive_action_recommendation,
    _derive_trust_banner,
    _harmonize_policy_trust_recommendation,
    _project_operational_decision,
)
from app.api.v1.endpoints.status import _extract_optional_policy_fields, _to_public_status_action
from app.observability.policy_engine import derive_operational_policy


def _make_collector_summary(
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


def _build_offline_response(
    *,
    collector_summary: dict[str, Any],
    overall_score: str = "PASS",
    overview_snapshot_status: str = "fresh",
    jobs_queued_count: int = 0,
    guardrail_events: dict[str, int] | None = None,
) -> dict[str, Any]:
    policy = derive_operational_policy(collector_summary)
    response = {
        "collector": collector_summary,
        "policy": policy,
        "operational_decision": _project_operational_decision(policy),
        "read_path": {
            "overview_snapshot_status": overview_snapshot_status,
            "jobs_queued_count": jobs_queued_count,
        },
        "guardrails": {"events": guardrail_events or {}},
        "overall": {"score": overall_score, "reasons": []},
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
    return response


def test_offline_flow_stable_monitor_keeps_shape_and_public_projection() -> None:
    response = _build_offline_response(
        collector_summary=_make_collector_summary(success=10, failed=0),
    )

    policy = response["policy"]
    trust = response["trust"]
    recommendation = response["recommendation"]
    operational_decision = response["operational_decision"]
    public_projection = _extract_optional_policy_fields({"policy": policy})

    assert policy["state"] == "stable"
    assert policy["decision"] == "monitor"
    assert isinstance(policy["score"], int)

    assert operational_decision == {
        "version": policy["version"],
        "score": policy["score"],
        "state": "stable",
        "decision": "monitor",
        "signals": policy["signals"],
    }

    assert trust["state"] == "green"
    assert trust["decision"] == "healthy"
    assert recommendation["action"] == "monitor"
    assert _to_public_status_action(recommendation["action"]) == "monitor"

    assert public_projection["decision_state"] == "stable"
    assert public_projection["decision_action"] == "monitor"
    assert public_projection["score"] == policy["score"]
    assert "signals" not in public_projection


def test_offline_flow_degraded_inspect_harmonizes_trust_and_recommendation() -> None:
    response = _build_offline_response(
        collector_summary=_make_collector_summary(
            success=4,
            failed=2,
            last_events=[
                {"status": "failed", "retryable": True},
                {"status": "failed", "retryable": True},
            ],
        ),
    )

    policy = response["policy"]
    trust = response["trust"]
    recommendation = response["recommendation"]
    public_projection = _extract_optional_policy_fields({"policy": policy})

    assert policy["state"] == "degraded"
    assert policy["decision"] == "inspect"
    assert 60 <= policy["score"] < 85

    assert trust["state"] == "yellow"
    assert trust["decision"] == "degraded"
    assert recommendation["action"] == "open_report"
    assert recommendation["derived_from"] == ["policy_harmonized"]

    assert public_projection["decision_state"] == "degraded"
    assert public_projection["decision_action"] == "inspect"
    assert public_projection["score"] == policy["score"]


def test_offline_flow_action_required_filters_forbidden_signal_tokens() -> None:
    response = _build_offline_response(
        collector_summary=_make_collector_summary(
            success=0,
            failed=5,
            by_error_type={"ssl_cert_verify_failed": 1},
            last_events=[{"status": "failed", "retryable": False}],
        ),
    )

    policy = dict(response["policy"])
    policy["signals"] = list(policy.get("signals") or []) + [
        "source_ref=https://secret.example/?token=abc",
        "minio_path=videos-raw/file.wav",
        "job_id=123",
        "key=SUPERSECRET",
        "/tmp/output.wav",
    ]

    trust = response["trust"]
    recommendation = response["recommendation"]
    public_projection = _extract_optional_policy_fields({"policy": policy})
    signals = public_projection["signals"]["items"]

    assert response["policy"]["state"] == "action_required"
    assert response["policy"]["decision"] == "investigate_now"

    assert trust["state"] == "red"
    assert trust["decision"] == "action_required"
    assert recommendation["action"] == "inspect_upstream_path"
    assert _to_public_status_action(recommendation["action"]) == "inspect"

    assert any(item.startswith("collector_failed=") for item in signals)
    assert all("source_ref" not in item.lower() for item in signals)
    assert all("minio" not in item.lower() for item in signals)
    assert all("job_id" not in item.lower() for item in signals)
    assert all("key=" not in item.lower() for item in signals)
    assert all("/tmp" not in item.lower() for item in signals)
