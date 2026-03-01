from __future__ import annotations

from typing import Any

_PUBLIC_ACTION_MAP = {
    "run_warmup": "inspect",
    "reduce_force_live_burst": "monitor",
    "inspect_upstream_path": "inspect",
    "open_report": "monitor",
    "monitor": "monitor",
    "none": "none",
}
_PUBLIC_SIGNAL_FORBIDDEN_SUBSTRINGS = (
    "source_ref",
    "minio",
    "job_id",
    "query_key",
    "key=",
    "/tmp",
    "/storage/",
)


def to_public_status_action(action: str | None) -> str:
    """Mapeia recommendation.action para o enum publico estavel."""
    normalized = str(action or "").strip().lower()
    return _PUBLIC_ACTION_MAP.get(normalized, "inspect")


def project_operational_decision(policy: dict[str, Any] | None) -> dict[str, Any] | None:
    """Projeta um bloco read-only a partir do policy sem recalcular regra."""
    if not isinstance(policy, dict):
        return None
    return {
        "version": policy.get("version"),
        "score": policy.get("score"),
        "state": policy.get("state"),
        "decision": policy.get("decision"),
        "signals": policy.get("signals"),
    }


def extract_optional_policy_fields(panel: dict[str, Any]) -> dict[str, Any]:
    """
    Projeta campos opcionais e sanitizados de policy para o contrato publico.
    """
    policy = panel.get("policy")
    if not isinstance(policy, dict):
        return {}

    out: dict[str, Any] = {}

    state = policy.get("state")
    decision = policy.get("decision")
    score = policy.get("score")
    signals = policy.get("signals")

    if isinstance(state, str) and state:
        out["decision_state"] = state
    else:
        legacy_state = policy.get("system_state")
        if isinstance(legacy_state, str) and legacy_state:
            out["decision_state"] = legacy_state

    if isinstance(decision, str) and decision:
        out["decision_action"] = decision

    if isinstance(score, int):
        out["score"] = score
    else:
        legacy_score = policy.get("trust_score")
        if isinstance(legacy_score, int):
            out["score"] = legacy_score

    safe_signals: dict[str, Any] = {}
    if isinstance(signals, dict):
        for key, value in signals.items():
            if not isinstance(key, str) or not key:
                continue
            if any(token in key.lower() for token in _PUBLIC_SIGNAL_FORBIDDEN_SUBSTRINGS):
                continue
            if value is None:
                continue
            if isinstance(value, (bool, int, float, str)):
                safe_signals[key] = value
                continue
            if isinstance(value, list) and all(isinstance(item, (bool, int, float, str)) for item in value):
                safe_signals[key] = value
    elif isinstance(signals, list):
        sanitized_list = [
            item
            for item in signals
            if isinstance(item, str)
            and item
            and not any(token in item.lower() for token in _PUBLIC_SIGNAL_FORBIDDEN_SUBSTRINGS)
        ]
        if sanitized_list:
            safe_signals["items"] = sanitized_list

    if safe_signals:
        out["signals"] = safe_signals

    return out
