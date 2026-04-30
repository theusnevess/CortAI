from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.account_health.models import AccountHealthInput
from app.creative.agents.account_health.service import AccountHealthAgentService

AUDIT_DIR = ROOT / "OUT" / "audit" / "account_health_agent_v2_6_excellence_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"

ACCOUNT_HEALTH_TEST_FILES = [
    "tests/agents/account_health/test_account_health_trace_auditability_unittest.py",
    "tests/agents/account_health/test_account_health_constraint_rationale_unittest.py",
    "tests/agents/account_health/test_account_health_degraded_input_policy_unittest.py",
    "tests/agents/account_health/test_account_health_temporal_health_unittest.py",
    "tests/agents/account_health/test_account_health_confidence_calibrator_unittest.py",
    "tests/agents/account_health/test_account_health_risk_components_unittest.py",
    "tests/agents/account_health/test_account_health_telemetry_enrichment_unittest.py",
    "tests/agents/account_health/test_account_health_agent_phase2_unittest.py",
    "tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py",
]

REQUIRED_RISK_COMPONENTS = {
    "publish_frequency_risk",
    "performance_drop_risk",
    "repetition_risk",
    "low_quality_streak_risk",
    "fallback_contamination_risk",
}

REQUIRED_RISK_COMPONENT_FIELDS = {
    "score",
    "level",
    "reason_code",
    "evidence_status",
    "rationale",
}

REQUIRED_HEALTH_TRACE_SECTIONS = {
    "telemetry_lineage",
    "risk_assessment",
    "confidence_calibration",
    "temporal_health",
    "degraded_input_policy",
    "constraint_rationale",
    "final_decision_rationale",
    "downgraded_or_missing_inputs",
    "audit_summary",
}

REQUIRED_PUBLIC_FIELDS = {
    "decision",
    "fallback",
    "input_summary",
    "decision_trace",
}


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _run_pytest(test_files: list[str]) -> dict[str, Any]:
    command = [sys.executable, "-m", "pytest", "-q", *test_files]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output_lines = [
        line.strip()
        for line in (completed.stdout + "\n" + completed.stderr).splitlines()
        if line.strip()
    ]
    return {
        "command": command,
        "passed": completed.returncode == 0,
        "returncode": completed.returncode,
        "test_files": test_files,
        "output_tail": output_lines[-20:],
    }


def _account_input(
    *,
    account_id: str,
    recent_publish_count: int = 2,
    recent_views_drop_ratio: float = 0.05,
    recent_format_repetition_ratio: float = 0.10,
    recent_low_performance_streak: int = 0,
    publish_status: str = "REAL",
    metric_status: str = "REAL",
    metric_freshness: str = "fresh",
    metric_previous: float | None = None,
    metric_recent: float | None = None,
    qc_status: str = "REAL",
    qc_previous: int | None = None,
    qc_recent: int | None = None,
    failure_status: str = "REAL",
    failure_previous: float = 0.0,
    failure_recent: float = 0.0,
    format_status: str = "REAL",
    format_previous: float | None = None,
    format_recent: float | None = None,
) -> AccountHealthInput:
    metric_previous = recent_views_drop_ratio if metric_previous is None else metric_previous
    metric_recent = recent_views_drop_ratio if metric_recent is None else metric_recent
    qc_previous = recent_low_performance_streak if qc_previous is None else qc_previous
    qc_recent = recent_low_performance_streak if qc_recent is None else qc_recent
    format_previous = recent_format_repetition_ratio if format_previous is None else format_previous
    format_recent = recent_format_repetition_ratio if format_recent is None else format_recent
    return AccountHealthInput(
        account_id=account_id,
        recent_publish_count=recent_publish_count,
        recent_views_drop_ratio=recent_views_drop_ratio,
        recent_format_repetition_ratio=recent_format_repetition_ratio,
        recent_low_performance_streak=recent_low_performance_streak,
        telemetry_sources=[
            {
                "source_name": "publish_history",
                "source_status": publish_status,
                "record_count": max(recent_publish_count, 1),
                "freshness_status": "fresh",
            }
        ],
        metric_window_summary={
            "source_status": metric_status,
            "record_count": 8,
            "freshness_status": metric_freshness,
            "previous_window": {"views_drop_ratio": metric_previous},
            "recent_window": {"views_drop_ratio": metric_recent},
        },
        qc_history_summary={
            "source_status": qc_status,
            "record_count": 8,
            "freshness_status": "fresh",
            "previous_window": {"low_quality_streak": qc_previous},
            "recent_window": {"low_quality_streak": qc_recent},
        },
        failure_history_summary={
            "source_status": failure_status,
            "record_count": 8,
            "freshness_status": "fresh",
            "previous_window": {"fallback_rate": failure_previous},
            "recent_window": {"fallback_rate": failure_recent},
        },
        format_repetition_summary={
            "source_status": format_status,
            "record_count": 8,
            "freshness_status": "fresh",
            "previous_window": {"repetition_ratio": format_previous},
            "recent_window": {"repetition_ratio": format_recent},
        },
    )


def _run_scenario(name: str, data: AccountHealthInput) -> dict[str, Any]:
    result = AccountHealthAgentService().evaluate(data)
    payload = result.to_dict()
    return {
        "name": name,
        "service": "AccountHealthAgentService",
        "input": data.to_dict(),
        "result": payload,
        "summary": {
            "decision": payload["decision"]["status"],
            "fallback_used": payload["fallback"]["used"],
            "risk_score": payload["risk_score"],
            "confidence": payload["confidence"],
            "confidence_level": payload["confidence_level"],
            "temporal_classification": payload["temporal_health"].get("classification"),
            "degraded_input_severity": payload["degraded_input_decision"].get("severity"),
            "degraded_input_action": payload["degraded_input_decision"].get("action"),
            "constraint_keys": sorted(payload["decision"]["recommended_constraints"].keys()),
        },
    }


def _build_scenarios() -> dict[str, dict[str, Any]]:
    scenarios: dict[str, dict[str, Any]] = {}
    scenarios["clean_safe"] = _run_scenario(
        "clean_safe",
        _account_input(account_id="acc_gate_clean_safe"),
    )
    scenarios["moderate_risk_caution"] = _run_scenario(
        "moderate_risk_caution",
        _account_input(
            account_id="acc_gate_caution",
            recent_views_drop_ratio=0.45,
            recent_format_repetition_ratio=0.70,
            recent_low_performance_streak=2,
            metric_previous=0.20,
            metric_recent=0.45,
            qc_previous=1,
            qc_recent=2,
            format_previous=0.30,
            format_recent=0.70,
        ),
    )
    scenarios["high_risk_hold"] = _run_scenario(
        "high_risk_hold",
        _account_input(
            account_id="acc_gate_hold",
            recent_views_drop_ratio=0.80,
            recent_low_performance_streak=4,
            metric_previous=0.40,
            metric_recent=0.80,
            qc_previous=2,
            qc_recent=4,
        ),
    )
    scenarios["missing_telemetry_safe_not_trusted"] = _run_scenario(
        "missing_telemetry_safe_not_trusted",
        AccountHealthInput(account_id="acc_gate_missing"),
    )
    scenarios["moderate_degraded_safe_to_caution"] = _run_scenario(
        "moderate_degraded_safe_to_caution",
        _account_input(
            account_id="acc_gate_moderate_degraded",
            metric_status="STALE",
            metric_freshness="stale",
            qc_status="DEGRADED",
        ),
    )
    scenarios["severe_degraded_high_risk_to_hold"] = _run_scenario(
        "severe_degraded_high_risk_to_hold",
        _account_input(
            account_id="acc_gate_severe_degraded",
            publish_status="DEGRADED",
            metric_status="STALE",
            metric_freshness="stale",
            qc_status="DEGRADED",
            failure_status="DEGRADED",
            format_status="STALE",
        ),
    )
    scenarios["temporal_degrading"] = _run_scenario(
        "temporal_degrading",
        _account_input(
            account_id="acc_gate_temporal_degrading",
            metric_previous=0.10,
            metric_recent=0.40,
            qc_previous=0,
            qc_recent=2,
        ),
    )
    scenarios["temporal_recovering"] = _run_scenario(
        "temporal_recovering",
        _account_input(
            account_id="acc_gate_temporal_recovering",
            metric_previous=0.50,
            metric_recent=0.10,
            qc_previous=2,
            qc_recent=0,
        ),
    )
    scenarios["temporal_volatile"] = _run_scenario(
        "temporal_volatile",
        _account_input(
            account_id="acc_gate_temporal_volatile",
            metric_previous=0.10,
            metric_recent=0.50,
            qc_previous=3,
            qc_recent=0,
        ),
    )
    scenarios["insufficient_temporal_evidence"] = _run_scenario(
        "insufficient_temporal_evidence",
        AccountHealthInput(
            account_id="acc_gate_insufficient_temporal",
            telemetry_sources=[
                {
                    "source_name": "publish_history",
                    "source_status": "REAL",
                    "record_count": 1,
                    "freshness_status": "fresh",
                }
            ],
        ),
    )
    scenarios["fallback_cold_start"] = _run_scenario(
        "fallback_cold_start",
        AccountHealthInput(account_id="acc_gate_fallback", recent_publish_count=-1),
    )
    scenarios["determinism_replay_first"] = _run_scenario(
        "determinism_replay_first",
        _account_input(account_id="acc_gate_determinism"),
    )
    scenarios["determinism_replay_second"] = _run_scenario(
        "determinism_replay_second",
        _account_input(account_id="acc_gate_determinism"),
    )
    return scenarios


def _result(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(scenario["result"])


def _decision(scenario: dict[str, Any]) -> str:
    return str(_result(scenario)["decision"]["status"])


def _health_trace(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(_result(scenario).get("health_trace") or {})


def _decision_trace(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(_result(scenario).get("decision_trace") or {})


def _constraint_rationale(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in list(_result(scenario).get("constraint_rationale") or [])]


def _constraints(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(_result(scenario)["decision"].get("recommended_constraints") or {})


def _confidence(scenario: dict[str, Any]) -> float:
    return float(_result(scenario).get("confidence") or 0.0)


def _risk_components_complete(result: dict[str, Any]) -> bool:
    risk_summary = dict(result.get("risk_components") or {})
    components = dict(risk_summary.get("components") or {})
    if set(components) != REQUIRED_RISK_COMPONENTS:
        return False
    for component in components.values():
        if not REQUIRED_RISK_COMPONENT_FIELDS.issubset(set(component)):
            return False
        if not (0.0 <= float(component.get("score") or 0.0) <= 1.0):
            return False
        if str(component.get("level") or "") not in {"low", "medium", "high"}:
            return False
        if str(component.get("evidence_status") or "") not in {"REAL", "ABSENT", "STALE", "DEGRADED"}:
            return False
    return True


def _telemetry_complete(result: dict[str, Any]) -> bool:
    telemetry = dict(result.get("telemetry_summary") or {})
    health_trace = dict(result.get("health_trace") or {})
    return all(
        key in telemetry
        for key in [
            "lineage_summary",
            "freshness_summary",
            "source_status_distribution",
            "available_signals",
            "missing_signals",
            "degraded_input_mode",
        ]
    ) and bool(health_trace.get("telemetry_lineage"))


def _constraint_coverage_complete(scenario: dict[str, Any]) -> bool:
    constraints = _constraints(scenario)
    rationale = _constraint_rationale(scenario)
    rationale_keys = [str(item.get("constraint_key") or "") for item in rationale]
    required_fields = {
        "constraint_key",
        "value",
        "interpretation_mode",
        "severity",
        "source",
        "evidence_summary",
        "downstream_interpretation",
        "rationale",
    }
    if sorted(rationale_keys) != sorted(str(key) for key in constraints):
        return False
    if len(rationale_keys) != len(set(rationale_keys)):
        return False
    for item in rationale:
        if not required_fields.issubset(set(item)):
            return False
        if item["interpretation_mode"] not in {"advisory", "cautionary", "blocking"}:
            return False
        if item["severity"] not in {"low", "medium", "high"}:
            return False
        if not item["downstream_interpretation"] or not item["rationale"]:
            return False
    return True


def _health_trace_complete(scenario: dict[str, Any]) -> bool:
    trace = _health_trace(scenario)
    audit = dict(trace.get("audit_summary") or {})
    return (
        REQUIRED_HEALTH_TRACE_SECTIONS.issubset(set(trace))
        and bool(audit.get("reconstructible"))
        and bool(audit.get("required_sections_present"))
        and bool(audit.get("decision_trace_backward_compatible"))
        and bool(audit.get("constraint_coverage_complete"))
        and not audit.get("silent_failure_indicators")
        and _decision_trace(scenario).get("health_trace") == trace
    )


def _required_public_fields_present(scenario: dict[str, Any]) -> bool:
    result = _result(scenario)
    decision = dict(result.get("decision") or {})
    return (
        REQUIRED_PUBLIC_FIELDS.issubset(set(result))
        and "recommended_constraints" in decision
        and "status" in decision
        and isinstance(result.get("decision_trace"), dict)
    )


def _selected_stable_payload(scenario: dict[str, Any]) -> dict[str, Any]:
    result = _result(scenario)
    return {
        "decision": result["decision"],
        "risk_score": result["risk_score"],
        "risk_components": result["risk_components"],
        "confidence": result["confidence"],
        "confidence_level": result["confidence_level"],
        "confidence_components": result["confidence_components"],
        "confidence_rationale": result["confidence_rationale"],
        "temporal_health": result["temporal_health"],
        "degraded_input_decision": result["degraded_input_decision"],
        "constraint_rationale": result["constraint_rationale"],
        "health_trace": result["health_trace"],
    }


def _scenario_checks(scenarios: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    clean = scenarios["clean_safe"]
    caution = scenarios["moderate_risk_caution"]
    hold = scenarios["high_risk_hold"]
    missing = scenarios["missing_telemetry_safe_not_trusted"]
    moderate_degraded = scenarios["moderate_degraded_safe_to_caution"]
    severe = scenarios["severe_degraded_high_risk_to_hold"]
    degrading = scenarios["temporal_degrading"]
    recovering = scenarios["temporal_recovering"]
    volatile = scenarios["temporal_volatile"]
    insufficient = scenarios["insufficient_temporal_evidence"]
    replay_first = scenarios["determinism_replay_first"]
    replay_second = scenarios["determinism_replay_second"]

    hold_blocking = next(
        (
            item
            for item in _constraint_rationale(hold)
            if item.get("constraint_key") == "block_generation"
        ),
        {},
    )
    severe_blocking = next(
        (
            item
            for item in _constraint_rationale(severe)
            if item.get("constraint_key") == "block_generation"
        ),
        {},
    )

    checks = {
        "clean_safe": {
            "passed": (
                _decision(clean) == "SAFE"
                and not _result(clean)["fallback"]["used"]
                and _confidence(clean) >= 0.70
                and _result(clean)["degraded_input_decision"]["action"] == "no_change"
                and _constraints(clean) == {}
            ),
            "decision": _decision(clean),
            "confidence": _confidence(clean),
        },
        "moderate_risk_caution": {
            "passed": (
                _decision(caution) == "CAUTION"
                and bool(_constraints(caution))
                and _constraint_coverage_complete(caution)
            ),
            "decision": _decision(caution),
            "constraint_keys": sorted(_constraints(caution)),
        },
        "high_risk_hold": {
            "passed": (
                _decision(hold) == "HOLD"
                and bool(_constraints(hold).get("block_generation"))
                and hold_blocking.get("interpretation_mode") == "blocking"
                and bool(_health_trace(hold).get("final_decision_rationale", {}).get("hold_authority_invoked"))
            ),
            "decision": _decision(hold),
            "hold_authority_invoked": _health_trace(hold).get("final_decision_rationale", {}).get(
                "hold_authority_invoked"
            ),
        },
        "missing_telemetry_safe_not_trusted": {
            "passed": (
                _decision(missing) in {"SAFE", "CAUTION"}
                and _result(missing)["confidence_level"] != "high"
                and bool(_result(missing)["degraded_input_decision"]["degraded_input_detected"])
                and any(item["status"] == "ABSENT" for item in _health_trace(missing)["downgraded_or_missing_inputs"])
            ),
            "decision": _decision(missing),
            "confidence": _confidence(missing),
            "confidence_level": _result(missing)["confidence_level"],
        },
        "moderate_degraded_safe_to_caution": {
            "passed": (
                _decision(moderate_degraded) == "CAUTION"
                and _result(moderate_degraded)["degraded_input_decision"]["original_decision"] == "SAFE"
                and _result(moderate_degraded)["degraded_input_decision"]["action"] == "upgrade_to_caution"
                and _decision_trace(moderate_degraded)["decision_adjustment"]["changed"]
            ),
            "decision": _decision(moderate_degraded),
            "degraded_input_decision": _result(moderate_degraded)["degraded_input_decision"],
        },
        "severe_degraded_high_risk_to_hold": {
            "passed": (
                _decision(severe) == "HOLD"
                and _result(severe)["degraded_input_decision"]["original_decision"] == "SAFE"
                and _result(severe)["degraded_input_decision"]["action"] == "upgrade_to_hold"
                and severe_blocking.get("interpretation_mode") == "blocking"
            ),
            "decision": _decision(severe),
            "degraded_input_decision": _result(severe)["degraded_input_decision"],
        },
        "temporal_degrading": {
            "passed": _result(degrading)["temporal_health"]["classification"] == "degrading",
            "classification": _result(degrading)["temporal_health"]["classification"],
        },
        "temporal_recovering": {
            "passed": _result(recovering)["temporal_health"]["classification"] == "recovering",
            "classification": _result(recovering)["temporal_health"]["classification"],
        },
        "temporal_volatile": {
            "passed": _result(volatile)["temporal_health"]["classification"] == "volatile",
            "classification": _result(volatile)["temporal_health"]["classification"],
        },
        "insufficient_temporal_evidence": {
            "passed": _result(insufficient)["temporal_health"]["classification"] == "insufficient_evidence",
            "classification": _result(insufficient)["temporal_health"]["classification"],
        },
        "determinism_replay": {
            "passed": _selected_stable_payload(replay_first) == _selected_stable_payload(replay_second),
        },
        "backward_compatibility": {
            "passed": all(_required_public_fields_present(scenario) for scenario in scenarios.values()),
        },
        "fallback_honest": {
            "passed": (
                _result(scenarios["fallback_cold_start"])["fallback"]["used"]
                and _decision_trace(scenarios["fallback_cold_start"])["fallback_used"]
                and _health_trace(scenarios["fallback_cold_start"])["final_decision_rationale"]["fallback_used"]
            ),
            "fallback_reason": _result(scenarios["fallback_cold_start"])["fallback"]["reason"],
        },
    }
    return checks


def _evaluate_dimensions(
    scenarios: dict[str, dict[str, Any]],
    scenario_results: dict[str, dict[str, Any]],
    tests_executed: dict[str, Any],
) -> tuple[dict[str, bool], list[str]]:
    clean = scenarios["clean_safe"]
    missing = scenarios["missing_telemetry_safe_not_trusted"]
    moderate_degraded = scenarios["moderate_degraded_safe_to_caution"]
    severe = scenarios["severe_degraded_high_risk_to_hold"]
    hold = scenarios["high_risk_hold"]
    fallback = scenarios["fallback_cold_start"]

    confidence_values = [_confidence(scenario) for scenario in scenarios.values()]
    fake_confidence = len(set(round(value, 4) for value in confidence_values)) <= 1

    runtime_real = all(
        not _result(scenarios[name])["fallback"]["used"]
        for name in [
            "clean_safe",
            "moderate_risk_caution",
            "high_risk_hold",
            "moderate_degraded_safe_to_caution",
        ]
    )
    telemetry_enriched = all(_telemetry_complete(_result(scenario)) for scenario in scenarios.values())
    risk_components_explicit = all(_risk_components_complete(_result(scenario)) for scenario in scenarios.values())
    confidence_calibrated = (
        not fake_confidence
        and _confidence(clean) >= 0.70
        and _result(missing)["confidence_level"] == "low"
        and _result(severe)["confidence_level"] == "low"
        and bool(_result(clean).get("confidence_components"))
        and bool(_result(clean).get("confidence_rationale"))
    )
    temporal_health_real = all(
        scenario_results[name]["passed"]
        for name in [
            "temporal_degrading",
            "temporal_recovering",
            "temporal_volatile",
            "insufficient_temporal_evidence",
        ]
    )
    degraded_input_safe = all(
        scenario_results[name]["passed"]
        for name in [
            "missing_telemetry_safe_not_trusted",
            "moderate_degraded_safe_to_caution",
            "severe_degraded_high_risk_to_hold",
        ]
    )
    constraints_rationale_complete = all(_constraint_coverage_complete(scenario) for scenario in scenarios.values())
    traceability_complete = all(_health_trace_complete(scenario) for scenario in scenarios.values())
    hold_authority_preserved = (
        scenario_results["high_risk_hold"]["passed"]
        and scenario_results["severe_degraded_high_risk_to_hold"]["passed"]
        and _result(hold)["degraded_input_decision"]["final_decision"] == "HOLD"
        and _health_trace(hold)["final_decision_rationale"]["hold_authority_invoked"]
    )
    boundary_preserved = all(
        key not in _result(clean)
        for key in ["strategy_profile", "learning_policy", "qc_decision", "publishability_decision"]
    ) and all(
        key in {"reduce_hook_aggressiveness", "max_daily_posts", "degraded_input_caution", "require_monitoring", "block_generation"}
        for scenario in scenarios.values()
        for key in _constraints(scenario)
    )
    determinism_where_required = bool(scenario_results["determinism_replay"]["passed"])
    fallback_honest = bool(scenario_results["fallback_honest"]["passed"]) and _result(fallback)["fallback"]["reason"]

    dimensions = {
        "runtime_real": runtime_real,
        "telemetry_enriched": telemetry_enriched,
        "risk_components_explicit": risk_components_explicit,
        "confidence_calibrated": confidence_calibrated,
        "temporal_health_real": temporal_health_real,
        "degraded_input_safe": degraded_input_safe,
        "constraints_rationale_complete": constraints_rationale_complete,
        "traceability_complete": traceability_complete,
        "hold_authority_preserved": hold_authority_preserved,
        "boundary_preserved": boundary_preserved,
        "determinism_where_required": determinism_where_required,
        "fallback_honest": bool(fallback_honest),
        "silent_failures_detected": False,
    }
    silent_failure = (
        not all(scenario["passed"] for scenario in scenario_results.values())
        or not all(value for key, value in dimensions.items() if key != "silent_failures_detected")
        or fake_confidence
        or not tests_executed["passed"]
    )
    dimensions["silent_failures_detected"] = silent_failure

    blocking_failures: list[str] = []
    for key, value in dimensions.items():
        if key == "silent_failures_detected":
            if value:
                blocking_failures.append("SILENT_FAILURE_DETECTED")
        elif not value:
            blocking_failures.append(key.upper())
    if fake_confidence:
        blocking_failures.append("FAKE_CONFIDENCE_OR_CONSTANT_CONFIDENCE")
    if not tests_executed["passed"]:
        blocking_failures.append("ACCOUNT_HEALTH_TEST_SUITE_FAILURE")
    for name, result in scenario_results.items():
        if not result["passed"]:
            blocking_failures.append(f"SCENARIO_FAILED:{name}")
    return dimensions, sorted(set(blocking_failures))


def _dimension_results(dimensions: dict[str, bool]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for key, value in dimensions.items():
        if key == "silent_failures_detected":
            results[key] = {"passed": not bool(value), "detected": bool(value)}
        else:
            results[key] = {"passed": bool(value)}
    return results


def _checklist_block(passed: bool, **payload: Any) -> dict[str, Any]:
    return {"passed": bool(passed), **payload}


def _build_checklist_results(
    *,
    scenarios: dict[str, dict[str, Any]],
    scenario_results: dict[str, dict[str, Any]],
    dimensions: dict[str, bool],
    blocking_failures: list[str],
    residual_monitoring: list[str],
) -> dict[str, Any]:
    clean = scenarios["clean_safe"]
    caution = scenarios["moderate_risk_caution"]
    hold = scenarios["high_risk_hold"]
    missing = scenarios["missing_telemetry_safe_not_trusted"]
    moderate_degraded = scenarios["moderate_degraded_safe_to_caution"]
    severe = scenarios["severe_degraded_high_risk_to_hold"]
    volatile = scenarios["temporal_volatile"]
    fallback = scenarios["fallback_cold_start"]
    confidence_values = [_confidence(scenario) for scenario in scenarios.values()]
    fake_confidence = len(set(round(value, 4) for value in confidence_values)) <= 1
    boundary_violations = not dimensions["boundary_preserved"]
    silent_failures = dimensions["silent_failures_detected"]

    telemetry = _result(clean)["telemetry_summary"]
    risk_components = _result(clean)["risk_components"]["components"]
    health_trace = _health_trace(clean)

    blocks = {
        "block_01_runtime_real": _checklist_block(
            dimensions["runtime_real"],
            uses_real_service=True,
            account_health_not_stubbed=True,
            valid_scenarios_not_fallback=True,
        ),
        "block_02_telemetry": _checklist_block(
            dimensions["telemetry_enriched"],
            telemetry_summary_exists=bool(_result(clean).get("telemetry_summary")),
            lineage_summary_exists=bool(telemetry.get("lineage_summary")),
            freshness_summary_exists=bool(telemetry.get("freshness_summary")),
            source_status_distribution_exists=bool(telemetry.get("source_status_distribution")),
            available_signals_exist="available_signals" in telemetry,
            missing_signals_exist="missing_signals" in telemetry,
        ),
        "block_03_risk": _checklist_block(
            dimensions["risk_components_explicit"],
            risk_score_exists="risk_score" in _result(clean),
            required_components_present=sorted(risk_components) == sorted(REQUIRED_RISK_COMPONENTS),
            component_fields_complete=all(
                REQUIRED_RISK_COMPONENT_FIELDS.issubset(set(component))
                for component in risk_components.values()
            ),
        ),
        "block_04_confidence": _checklist_block(
            dimensions["confidence_calibrated"] and not fake_confidence,
            confidence_values=confidence_values,
            confidence_not_constant=not fake_confidence,
            clean_confidence=_confidence(clean),
            missing_confidence=_confidence(missing),
            severe_confidence=_confidence(severe),
            low_confidence_degraded_or_missing_exists=(
                _result(missing)["confidence_level"] == "low"
                or _result(severe)["confidence_level"] == "low"
            ),
        ),
        "block_05_temporal": _checklist_block(
            dimensions["temporal_health_real"],
            degrading=scenario_results["temporal_degrading"]["classification"],
            recovering=scenario_results["temporal_recovering"]["classification"],
            volatile=scenario_results["temporal_volatile"]["classification"],
            insufficient=scenario_results["insufficient_temporal_evidence"]["classification"],
            insufficient_not_stable=scenario_results["insufficient_temporal_evidence"]["classification"] != "stable",
        ),
        "block_06_degraded_input": _checklist_block(
            dimensions["degraded_input_safe"],
            missing_degraded_visible=bool(_result(missing)["degraded_input_decision"]["degraded_input_detected"]),
            moderate_safe_to_caution=scenario_results["moderate_degraded_safe_to_caution"]["passed"],
            severe_to_hold=scenario_results["severe_degraded_high_risk_to_hold"]["passed"],
            decision_adjustment_trace_present="decision_adjustment" in _decision_trace(moderate_degraded),
        ),
        "block_07_constraints": _checklist_block(
            dimensions["constraints_rationale_complete"],
            caution_constraints_have_rationale=_constraint_coverage_complete(caution),
            hold_constraints_have_rationale=_constraint_coverage_complete(hold),
            degraded_constraints_have_rationale=_constraint_coverage_complete(moderate_degraded),
            every_recommended_constraint_has_one_rationale=all(
                _constraint_coverage_complete(scenario) for scenario in scenarios.values()
            ),
        ),
        "block_08_trace": _checklist_block(
            dimensions["traceability_complete"],
            health_trace_exists=bool(health_trace),
            required_sections=sorted(REQUIRED_HEALTH_TRACE_SECTIONS),
            present_sections=sorted(health_trace),
            audit_summary=health_trace.get("audit_summary", {}),
        ),
        "block_09_authority": _checklist_block(
            dimensions["hold_authority_preserved"],
            hold_never_downgraded=_decision(hold) == "HOLD",
            severe_degraded_hold=_decision(severe) == "HOLD",
            hold_blocking_constraint=bool(_constraints(hold).get("block_generation")),
            hold_authority_visible=bool(_health_trace(hold)["final_decision_rationale"]["hold_authority_invoked"]),
        ),
        "block_10_determinism": _checklist_block(
            dimensions["determinism_where_required"],
            replay_stable=scenario_results["determinism_replay"]["passed"],
        ),
        "block_11_fallback": _checklist_block(
            dimensions["fallback_honest"],
            fallback_used=bool(_result(fallback)["fallback"]["used"]),
            fallback_reason=_result(fallback)["fallback"]["reason"],
            fallback_visible_in_decision_trace=bool(_decision_trace(fallback)["fallback_used"]),
            fallback_visible_in_health_trace=bool(_health_trace(fallback)["final_decision_rationale"]["fallback_used"]),
        ),
        "block_12_boundary": _checklist_block(
            dimensions["boundary_preserved"],
            account_health_does_not_emit_strategy_profile="strategy_profile" not in _result(clean),
            account_health_does_not_emit_learning_policy="learning_policy" not in _result(clean),
            account_health_does_not_emit_qc_decision="qc_decision" not in _result(clean),
            boundary_violations_detected=boundary_violations,
        ),
        "block_13_backward_compatibility": _checklist_block(
            scenario_results["backward_compatibility"]["passed"],
            required_public_fields=sorted(REQUIRED_PUBLIC_FIELDS),
            recommended_constraints_still_on_decision=True,
            decision_trace_backward_compatible=bool(
                _health_trace(clean).get("audit_summary", {}).get("decision_trace_backward_compatible")
            ),
        ),
        "block_14_silent_failure_detection": _checklist_block(
            not silent_failures,
            silent_failures_detected=silent_failures,
            no_constraint_without_rationale=dimensions["constraints_rationale_complete"],
            no_missing_health_trace=dimensions["traceability_complete"],
            no_fake_confidence=not fake_confidence,
        ),
        "block_15_global_consistency": _checklist_block(
            all(
                [
                    _decision(clean) == "SAFE",
                    _decision(caution) == "CAUTION",
                    _decision(hold) == "HOLD",
                    _result(volatile)["temporal_health"]["classification"] == "volatile",
                    _health_trace(missing)["downgraded_or_missing_inputs"],
                    dimensions["constraints_rationale_complete"],
                ]
            ),
            safe_caution_hold_consistent=True,
            temporal_matches_scenario=True,
            degraded_inputs_visible=True,
            pressure_boundary_not_applicable_to_account_health=True,
        ),
    }
    failed_blocks = [name for name, block in blocks.items() if not block["passed"]]
    return {
        "global_rule": {
            "critical_failures": len(blocking_failures) + len(failed_blocks),
            "soft_failures": "explicit_and_bounded" if residual_monitoring else "none",
            "fake_confidence": fake_confidence,
            "silent_failures": silent_failures,
            "boundary_violations": boundary_violations,
            "verdict": "ONLY_THEN_PROCEED" if not blocking_failures and not failed_blocks else "DO_NOT_PROCEED",
        },
        "blocks": blocks,
        "failed_blocks": failed_blocks,
        "final_release_criteria": {
            "critical_failures": len(blocking_failures) + len(failed_blocks),
            "telemetry": "enriched" if dimensions["telemetry_enriched"] else "incomplete",
            "risk_components": "explicit" if dimensions["risk_components_explicit"] else "incomplete",
            "confidence": "honest_and_calibrated" if dimensions["confidence_calibrated"] else "invalid",
            "temporal_health": "credible" if dimensions["temporal_health_real"] else "invalid",
            "degraded_input": "safe" if dimensions["degraded_input_safe"] else "unsafe",
            "constraints": "rationale_complete" if dimensions["constraints_rationale_complete"] else "incomplete",
            "traceability": "complete" if dimensions["traceability_complete"] else "incomplete",
            "hold_authority_preserved": dimensions["hold_authority_preserved"],
            "determinism": dimensions["determinism_where_required"],
            "boundary_preserved": dimensions["boundary_preserved"],
            "verdict": "READY_FOR_V3_WITH_MONITORING"
            if not blocking_failures and not failed_blocks
            else "NOT_READY_FOR_V3",
        },
    }


def _build_metrics(
    *,
    scenarios: dict[str, dict[str, Any]],
    scenario_results: dict[str, dict[str, Any]],
    tests_executed: dict[str, Any],
) -> dict[str, Any]:
    decisions: dict[str, int] = {}
    confidence_values: dict[str, float] = {}
    temporal_classifications: dict[str, str] = {}
    for name, scenario in scenarios.items():
        decisions[_decision(scenario)] = decisions.get(_decision(scenario), 0) + 1
        confidence_values[name] = _confidence(scenario)
        temporal_classifications[name] = str(_result(scenario)["temporal_health"].get("classification"))
    return {
        "scenario_count": len(scenarios),
        "scenario_pass_count": sum(1 for result in scenario_results.values() if result["passed"]),
        "scenario_fail_count": sum(1 for result in scenario_results.values() if not result["passed"]),
        "decision_distribution": decisions,
        "confidence_values": confidence_values,
        "temporal_classifications": temporal_classifications,
        "tests_passed": bool(tests_executed["passed"]),
    }


def main() -> None:
    _reset_audit_dir()
    tests_executed = _run_pytest(ACCOUNT_HEALTH_TEST_FILES)
    scenarios = _build_scenarios()
    scenario_results = _scenario_checks(scenarios)
    dimensions, blocking_failures = _evaluate_dimensions(
        scenarios=scenarios,
        scenario_results=scenario_results,
        tests_executed=tests_executed,
    )

    residual_monitoring: list[str] = []
    if not blocking_failures:
        if scenarios["missing_telemetry_safe_not_trusted"]["result"]["telemetry_summary"]["missing_signals"]:
            residual_monitoring.append("ACCOUNT_HEALTH_TELEMETRY_PRODUCER_COVERAGE_STILL_EXPANDING")
        residual_monitoring.append("ACCOUNT_HEALTH_RUNTIME_HISTORY_STILL_SHORT")

    checklist_results = _build_checklist_results(
        scenarios=scenarios,
        scenario_results=scenario_results,
        dimensions=dimensions,
        blocking_failures=blocking_failures,
        residual_monitoring=residual_monitoring,
    )
    failed_blocks = list(checklist_results.get("failed_blocks") or [])
    if failed_blocks:
        blocking_failures = sorted(
            set([*blocking_failures, *[f"CHECKLIST_BLOCK_FAILED:{name}" for name in failed_blocks]])
        )
        residual_monitoring = []

    if blocking_failures:
        verdict = "HOLD"
    elif residual_monitoring:
        verdict = "GO_WITH_MONITORING"
    else:
        verdict = "GO"

    metrics = _build_metrics(
        scenarios=scenarios,
        scenario_results=scenario_results,
        tests_executed=tests_executed,
    )
    scenario_outputs = {
        name: {
            "summary": scenario["summary"],
            "result": scenario["result"],
            "checks": scenario_results.get(name, {}),
        }
        for name, scenario in scenarios.items()
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "2.6",
        "agent": "account_health",
        "audit_type": "ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "verdict": verdict,
        **dimensions,
        "critical_failures": len(blocking_failures),
        "soft_failures": "explicit_and_bounded" if residual_monitoring else "none",
        "fake_confidence": bool(checklist_results["global_rule"]["fake_confidence"]),
        "boundary_violations": bool(checklist_results["global_rule"]["boundary_violations"]),
        "scenario_results": scenario_results,
        "checklist_results": checklist_results,
        "metrics": metrics,
        "dimension_results": _dimension_results(dimensions),
        "tests_executed": tests_executed,
        "blocking_failures": blocking_failures,
        "residual_monitoring": residual_monitoring,
        "verdict_scenario_examples": {
            "GO": {
                "meaning": "All critical dimensions pass and no meaningful residual monitoring remains.",
                "current_gate_result": verdict == "GO",
            },
            "GO_WITH_MONITORING": {
                "meaning": "All critical dimensions pass while runtime history or producer coverage remains monitorable.",
                "current_gate_result": verdict == "GO_WITH_MONITORING",
                "current_residuals": residual_monitoring,
            },
            "HOLD": {
                "meaning": "Any critical dimension, scenario, checklist block, or supporting test fails.",
                "current_gate_result": verdict == "HOLD",
                "current_blockers": blocking_failures,
            },
        },
        "artifact_references": {
            "gate_document": "docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE.md",
            "account_health_plan": "docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md",
            "phase_master_plan": "docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md",
        },
    }

    _write_json(SCENARIO_OUTPUTS_PATH, scenario_outputs)
    _write_json(CHECKLIST_RESULTS_PATH, checklist_results)
    _write_json(METRICS_PATH, metrics)
    _write_json(FINAL_VERDICT_PATH, final_verdict)
    print(str(FINAL_VERDICT_PATH))


if __name__ == "__main__":
    main()
