from __future__ import annotations

from app.observability.policy_engine import derive_policy_bridge


def test_policy_bridge_none_when_no_collector_summary() -> None:
    assert derive_policy_bridge(None) is None


def test_policy_bridge_info_on_all_success() -> None:
    collector_summary = {
        "window_minutes": 15,
        "events": {"success": 5, "failed": 0},
        "by_error_type": {},
        "last_events": [],
    }

    out = derive_policy_bridge(collector_summary)

    assert out is not None
    assert out["version"] == "v0.2"
    assert out["severity"] == "info"
    assert isinstance(out["headline"], str) and out["headline"]
    assert isinstance(out["next_actions"], list) and len(out["next_actions"]) == 1


def test_policy_bridge_warn_on_some_failures() -> None:
    collector_summary = {
        "window_minutes": 15,
        "events": {"success": 9, "failed": 1},
        "by_error_type": {"timeout": 1},
        "last_events": [],
    }

    out = derive_policy_bridge(collector_summary)

    assert out is not None
    assert out["severity"] == "warn"
    assert "coleta" in out["headline"].lower()
    assert len(out["next_actions"]) <= 3


def test_policy_bridge_critical_on_tls_ca_failures() -> None:
    collector_summary = {
        "window_minutes": 15,
        "events": {"success": 1, "failed": 1},
        "by_error_type": {"ssl_cert_verify_failed": 1},
        "last_events": [],
    }

    out = derive_policy_bridge(collector_summary)

    assert out is not None
    assert out["severity"] == "critical"
    assert "tls" in out["headline"].lower() or "ca" in out["headline"].lower()
    assert len(out["next_actions"]) <= 3
    assert "ca" in out["next_actions"][0].lower() or "bundle" in out["next_actions"][0].lower()
