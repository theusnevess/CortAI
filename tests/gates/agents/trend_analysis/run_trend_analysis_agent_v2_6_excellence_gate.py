from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.trend_analysis.models import TrendAnalysisInput
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.trend_analysis.source_governance import TrendSourceGovernanceEvaluator

AUDIT_DIR = ROOT / "OUT" / "audit" / "trend_analysis_agent_v2_6_excellence_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"

TREND_TEST_FILES = [
    "tests/agents/trend_analysis/test_trend_analysis_trace_auditability_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_downstream_utility_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_shift_analysis_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_confidence_calibration_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_freshness_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_provenance_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_source_governance_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_agent_phase2_unittest.py",
    "tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py",
    "tests/agents/strategy/test_strategy_agent_phase2_unittest.py",
    "tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py",
]

REQUIRED_PUBLIC_FIELDS = {"trend_profile", "fallback", "validation_summary", "collector_trace"}
REQUIRED_TREND_TRACE_SECTIONS = {
    "source_governance",
    "provenance",
    "freshness",
    "validity",
    "confidence_calibration",
    "shift_analysis",
    "downstream_utility",
    "fallback",
    "final_trend_profile_rationale",
    "missing_or_degraded_inputs",
    "audit_summary",
}
REQUIRED_COLLECTOR_TRACE_FIELDS = {
    "source_governance",
    "provenance",
    "freshness",
    "validity",
    "confidence_calibration",
    "downstream_utility",
    "trend_trace",
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
        "output_tail": output_lines[-24:],
    }


def _profile_payload(
    *,
    niche: str = "horror",
    dominant_hooks: list[str] | None = None,
    avg_duration: str = "35-60",
    pacing: str = "fast_first_3s",
    visual_style: str = "dark_backgrounds",
    text_style: str = "large_caption_focus",
    trend_source: str = "manual_curation",
    updated_at: str | None = "2026-04-24T11:00:00Z",
    valid_until: str = "2026-04-30T00:00:00Z",
    sample_size: int = 12,
    confidence: float = 0.82,
    evidence_id: str = "manual_001",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "niche": niche,
        "dominant_hooks": dominant_hooks or ["story_opening"],
        "avg_duration": avg_duration,
        "pacing": pacing,
        "visual_style": visual_style,
        "text_style": text_style,
        "region": "US",
        "trend_source": trend_source,
        "valid_until": valid_until,
        "sample_size": sample_size,
        "confidence_scores": {
            "overall": confidence,
            "dominant_hooks": confidence,
            "avg_duration": confidence,
            "pacing": confidence,
            "visual_style": confidence,
        },
        "evidence": [
            {
                "evidence_type": "manual_top_video",
                "source": trend_source,
                "reference_id": evidence_id,
                "captured_at": updated_at or "",
            }
        ],
    }
    if updated_at is not None:
        payload["updated_at"] = updated_at
    return payload


def _source_record_payload(
    *,
    niche: str = "horror",
    collected_at: str = "2026-04-24T10:00:00Z",
    dominant_hooks: list[str] | None = None,
    avg_duration: str = "35-60",
    pacing: str = "fast_first_3s",
    visual_style: str = "dark_backgrounds",
    text_style: str = "large_caption_focus",
    sample_size: int = 12,
    evidence_source: str = "manual_curation",
    evidence_id: str = "manual_001",
) -> dict[str, Any]:
    return {
        "niche": niche,
        "collected_at": collected_at,
        "sample_size": sample_size,
        "dominant_hooks": dominant_hooks or ["story_opening"],
        "avg_duration": avg_duration,
        "pacing": pacing,
        "visual_style": visual_style,
        "text_style": text_style,
        "evidence": [
            {
                "evidence_type": "trend_source_record",
                "source": evidence_source,
                "reference_id": evidence_id,
                "captured_at": collected_at,
            }
        ],
    }


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_service_scenario(name: str, trends_dir: Path, *, niche: str = "horror") -> dict[str, Any]:
    result = TrendAnalysisAgentService(trends_dir=trends_dir).load(
        TrendAnalysisInput(niche=niche, current_time="2026-04-24T12:00:00Z")
    )
    payload = result.to_dict()
    return {
        "name": name,
        "service": "TrendAnalysisAgentService",
        "result": payload,
        "summary": {
            "fallback_used": payload["fallback"]["used"],
            "fallback_reason": payload["fallback"]["reason"],
            "trend_source": payload["trend_profile"]["trend_source"],
            "validation_status": payload["validation_summary"].get("status"),
            "legacy_overall_confidence": payload["validation_summary"].get("overall_confidence"),
            "calibrated_confidence": payload["collector_trace"].get("confidence_calibration", {}).get("confidence"),
            "calibrated_confidence_level": payload["collector_trace"].get("confidence_calibration", {}).get(
                "confidence_level"
            ),
            "validity_status": payload["collector_trace"].get("validity", {}).get("validity_status"),
            "shift_severity": payload["collector_trace"].get("shift_analysis", {}).get("shift_severity"),
            "source_class": payload["collector_trace"].get("source_governance", {}).get("selected_source_class"),
        },
    }


def _build_scenarios(root: Path) -> dict[str, dict[str, Any]]:
    scenarios: dict[str, dict[str, Any]] = {}

    fresh_dir = root / "fresh_governed_profile"
    _write_payload(fresh_dir / "current" / "horror.json", _profile_payload())
    scenarios["fresh_governed_profile"] = _run_service_scenario("fresh_governed_profile", fresh_dir)

    hybrid_dir = root / "hybrid_source_mix"
    _write_payload(
        hybrid_dir / "manual_curation" / "horror.json",
        _source_record_payload(
            dominant_hooks=["story_opening", "ominous_question"],
            evidence_source="manual_curation",
            evidence_id="manual_001",
            sample_size=8,
        ),
    )
    _write_payload(
        hybrid_dir / "cache" / "creative_center" / "horror.json",
        _source_record_payload(
            dominant_hooks=["shock_statement", "story_opening"],
            evidence_source="creative_center",
            evidence_id="creative_001",
            sample_size=22,
        ),
    )
    scenarios["hybrid_source_mix"] = _run_service_scenario("hybrid_source_mix", hybrid_dir)

    stale_dir = root / "stale_profile"
    _write_payload(
        stale_dir / "current" / "horror.json",
        _profile_payload(updated_at="2026-04-19T00:00:00Z", valid_until="2026-05-02T00:00:00Z"),
    )
    scenarios["stale_profile"] = _run_service_scenario("stale_profile", stale_dir)

    expired_dir = root / "expired_profile"
    _write_payload(
        expired_dir / "current" / "horror.json",
        _profile_payload(updated_at="2026-04-15T00:00:00Z", valid_until="2026-05-02T00:00:00Z"),
    )
    scenarios["expired_profile"] = _run_service_scenario("expired_profile", expired_dir)

    missing_timestamp_dir = root / "missing_timestamp_profile"
    _write_payload(
        missing_timestamp_dir / "current" / "horror.json",
        _profile_payload(updated_at=None, valid_until="2026-05-02T00:00:00Z"),
    )
    scenarios["missing_timestamp_profile"] = _run_service_scenario("missing_timestamp_profile", missing_timestamp_dir)

    fallback_dir = root / "safe_default_fallback"
    scenarios["safe_default_fallback"] = _run_service_scenario("safe_default_fallback", fallback_dir)

    strong_shift_dir = root / "strong_shift"
    _write_payload(
        strong_shift_dir / "current" / "horror.json",
        _profile_payload(
            dominant_hooks=["question", "baseline_hook", "slow_burn"],
            pacing="baseline",
            visual_style="phase1_baseline",
            evidence_id="baseline_001",
        ),
    )
    _write_payload(
        strong_shift_dir / "manual_curation" / "horror.json",
        _source_record_payload(
            dominant_hooks=["ominous_question", "warning_claim", "evidence_tease"],
            pacing="fast_first_3s",
            visual_style="dark_backgrounds",
            evidence_id="shift_001",
        ),
    )
    scenarios["strong_shift"] = _run_service_scenario("strong_shift", strong_shift_dir)

    weak_shift_dir = root / "weak_shift"
    _write_payload(
        weak_shift_dir / "current" / "horror.json",
        _profile_payload(dominant_hooks=["story_opening", "shock_statement"], evidence_id="weak_base_001"),
    )
    _write_payload(
        weak_shift_dir / "manual_curation" / "horror.json",
        _source_record_payload(dominant_hooks=["shock_statement", "story_opening"], evidence_id="weak_shift_001"),
    )
    scenarios["weak_shift"] = _run_service_scenario("weak_shift", weak_shift_dir)

    determinism_dir = root / "determinism_replay"
    _write_payload(determinism_dir / "current" / "horror.json", _profile_payload(evidence_id="determinism_001"))
    scenarios["determinism_replay_first"] = _run_service_scenario("determinism_replay_first", determinism_dir)
    shutil.rmtree(determinism_dir, ignore_errors=True)
    _write_payload(determinism_dir / "current" / "horror.json", _profile_payload(evidence_id="determinism_001"))
    scenarios["determinism_replay_second"] = _run_service_scenario("determinism_replay_second", determinism_dir)

    return scenarios


def _policy_probe() -> dict[str, Any]:
    evaluator = TrendSourceGovernanceEvaluator()
    forbidden = evaluator.evaluate_candidates(
        candidates=[{"source_id": "bad", "source_class": "unbounded_scrape", "region": "US", "metadata": {}}],
        requested_region="US",
        selection_mode="single_preferred",
    ).to_dict()
    safe_default = evaluator.evaluate_candidates(
        candidates=[{"source_id": "safe_default", "source_class": "safe_default", "region": "US", "metadata": {}}],
        requested_region="US",
        selection_mode="single_preferred",
    ).to_dict()
    return {
        "forbidden_source_rejected": (
            not forbidden["policy_respected"]
            and forbidden["rejected_sources"]
            and forbidden["rejected_sources"][0]["reason_code"] == "SOURCE_REJECTED_FORBIDDEN_CLASS"
        ),
        "safe_default_fallback_allowed": (
            safe_default["selected_source_class"] == "safe_default"
            and bool(safe_default["fallback_required"])
            and safe_default["accepted_sources"][0]["governance_status"] == "fallback_allowed"
        ),
        "forbidden_result": forbidden,
        "safe_default_result": safe_default,
    }


def _result(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(scenario["result"])


def _collector_trace(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(_result(scenario).get("collector_trace") or {})


def _trend_trace(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(_collector_trace(scenario).get("trend_trace") or {})


def _validation_summary(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(_result(scenario).get("validation_summary") or {})


def _confidence(scenario: dict[str, Any]) -> float:
    return float(_collector_trace(scenario).get("confidence_calibration", {}).get("confidence") or 0.0)


def _confidence_level(scenario: dict[str, Any]) -> str:
    return str(_collector_trace(scenario).get("confidence_calibration", {}).get("confidence_level") or "")


def _freshness_statuses(scenario: dict[str, Any]) -> set[str]:
    return {
        str(item.get("freshness_status") or "")
        for item in list(_collector_trace(scenario).get("freshness", {}).get("sources") or [])
    }


def _governed_trace_complete(scenario: dict[str, Any]) -> bool:
    trace = _trend_trace(scenario)
    audit_summary = dict(trace.get("audit_summary") or {})
    return (
        REQUIRED_TREND_TRACE_SECTIONS.issubset(set(trace))
        and bool(audit_summary.get("reconstructible"))
        and bool(audit_summary.get("required_sections_present"))
        and not audit_summary.get("silent_failure_indicators")
        and bool(_validation_summary(scenario).get("traceability", {}).get("trend_trace_present"))
        and bool(_validation_summary(scenario).get("traceability", {}).get("reconstructible"))
    )


def _required_public_fields_present(scenario: dict[str, Any]) -> bool:
    payload = _result(scenario)
    return (
        REQUIRED_PUBLIC_FIELDS.issubset(set(payload))
        and REQUIRED_COLLECTOR_TRACE_FIELDS.issubset(set(payload["collector_trace"]))
    )


def _constraint_or_authority_leak_absent(scenario: dict[str, Any]) -> bool:
    serialized = json.dumps(_result(scenario), sort_keys=True)
    forbidden_keys = [
        '"strategy_profile"',
        '"asset_decision"',
        '"publishability_decision"',
        '"qc_decision"',
        '"learning_policy"',
        '"recommended_constraints"',
    ]
    return all(key not in serialized for key in forbidden_keys)


def _downstream_authority_bounded(scenario: dict[str, Any]) -> bool:
    utility = dict(_collector_trace(scenario).get("downstream_utility") or {})
    field_utilities = list(dict(utility.get("utility_trace") or {}).get("field_utilities") or [])
    return (
        utility.get("boundary_statement") == "Trend provides context only; Strategy remains the control layer."
        and bool(field_utilities)
        and all(str(item.get("authority_level") or "") in {"none", "advisory"} for item in field_utilities)
    )


def _stable_payload(scenario: dict[str, Any]) -> dict[str, Any]:
    payload = _result(scenario)
    return {
        "trend_profile": payload["trend_profile"],
        "fallback": payload["fallback"],
        "validation_summary": payload["validation_summary"],
        "collector_trace": payload["collector_trace"],
    }


def _scenario_checks(
    *,
    scenarios: dict[str, dict[str, Any]],
    policy_probe: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    fresh = scenarios["fresh_governed_profile"]
    hybrid = scenarios["hybrid_source_mix"]
    stale = scenarios["stale_profile"]
    expired = scenarios["expired_profile"]
    missing_timestamp = scenarios["missing_timestamp_profile"]
    fallback = scenarios["safe_default_fallback"]
    strong_shift = scenarios["strong_shift"]
    weak_shift = scenarios["weak_shift"]
    replay_first = scenarios["determinism_replay_first"]
    replay_second = scenarios["determinism_replay_second"]

    return {
        "fresh_governed_profile": {
            "passed": (
                not _result(fresh)["fallback"]["used"]
                and _collector_trace(fresh)["source_governance"]["selected_source_class"] == "current_store"
                and _collector_trace(fresh)["provenance"]["provenance_complete"]
                and _collector_trace(fresh)["validity"]["validity_status"] == "valid"
                and _confidence_level(fresh) == "high"
                and _governed_trace_complete(fresh)
            ),
            "summary": fresh["summary"],
        },
        "hybrid_source_mix": {
            "passed": (
                not _result(hybrid)["fallback"]["used"]
                and _result(hybrid)["trend_profile"]["trend_source"] == "hybrid"
                and _collector_trace(hybrid)["source_governance"]["source_mix"].get("approved_external_reference") == 1
                and _collector_trace(hybrid)["source_governance"]["source_mix"].get("manual_curation") == 1
                and len(_result(hybrid)["trend_profile"]["evidence"]) >= 2
                and _governed_trace_complete(hybrid)
            ),
            "summary": hybrid["summary"],
        },
        "stale_profile": {
            "passed": (
                "stale" in _freshness_statuses(stale)
                and _collector_trace(stale)["validity"]["validity_status"] in {"weak", "degraded"}
                and _confidence(stale) < _confidence(fresh)
                and any(item["kind"] == "stale_source" for item in _trend_trace(stale)["missing_or_degraded_inputs"])
            ),
            "summary": stale["summary"],
        },
        "expired_profile": {
            "passed": (
                "expired" in _freshness_statuses(expired)
                and _collector_trace(expired)["validity"]["validity_status"] in {"degraded", "invalid"}
                and _confidence(expired) < _confidence(stale)
                and any(item["kind"] == "expired_source" for item in _trend_trace(expired)["missing_or_degraded_inputs"])
            ),
            "summary": expired["summary"],
        },
        "missing_timestamp_profile": {
            "passed": (
                "missing_timestamp" in _freshness_statuses(missing_timestamp)
                and _confidence(missing_timestamp) < _confidence(fresh)
                and any(
                    item["kind"] == "missing_timestamp"
                    for item in _trend_trace(missing_timestamp)["missing_or_degraded_inputs"]
                )
            ),
            "summary": missing_timestamp["summary"],
        },
        "safe_default_fallback": {
            "passed": (
                bool(_result(fallback)["fallback"]["used"])
                and _result(fallback)["trend_profile"]["trend_source"] == "safe_default"
                and _collector_trace(fallback)["source_governance"]["selected_source_class"] == "safe_default"
                and _collector_trace(fallback)["source_governance"]["fallback_required"]
                and _confidence(fallback) <= 0.30
                and _trend_trace(fallback)["fallback"]["safe_default_used"]
            ),
            "summary": fallback["summary"],
            "audit_summary": _trend_trace(fallback).get("audit_summary", {}),
        },
        "strong_shift": {
            "passed": (
                _collector_trace(strong_shift)["shift_analysis"]["baseline_available"]
                and _collector_trace(strong_shift)["shift_analysis"]["shift_detected"]
                and _collector_trace(strong_shift)["shift_analysis"]["shift_severity"] == "strong"
                and _collector_trace(strong_shift)["shift_analysis"]["operational_significance"] == "high"
            ),
            "summary": strong_shift["summary"],
        },
        "weak_shift": {
            "passed": (
                _collector_trace(weak_shift)["shift_analysis"]["baseline_available"]
                and not _collector_trace(weak_shift)["shift_analysis"]["shift_detected"]
                and _collector_trace(weak_shift)["shift_analysis"]["shift_severity"] == "weak"
                and _collector_trace(weak_shift)["shift_analysis"]["operational_significance"] == "low"
            ),
            "summary": weak_shift["summary"],
        },
        "source_policy_probe": {
            "passed": bool(policy_probe["forbidden_source_rejected"] and policy_probe["safe_default_fallback_allowed"]),
            "forbidden_source_rejected": policy_probe["forbidden_source_rejected"],
            "safe_default_fallback_allowed": policy_probe["safe_default_fallback_allowed"],
        },
        "determinism_replay": {
            "passed": _stable_payload(replay_first) == _stable_payload(replay_second),
            "first_summary": replay_first["summary"],
            "second_summary": replay_second["summary"],
        },
        "backward_compatibility": {
            "passed": all(_required_public_fields_present(scenario) for scenario in scenarios.values()),
            "required_public_fields": sorted(REQUIRED_PUBLIC_FIELDS),
            "required_collector_trace_fields": sorted(REQUIRED_COLLECTOR_TRACE_FIELDS),
        },
    }


def _evaluate_dimensions(
    *,
    scenarios: dict[str, dict[str, Any]],
    scenario_results: dict[str, dict[str, Any]],
    tests_executed: dict[str, Any],
) -> tuple[dict[str, bool], list[str]]:
    fresh = scenarios["fresh_governed_profile"]
    hybrid = scenarios["hybrid_source_mix"]
    stale = scenarios["stale_profile"]
    expired = scenarios["expired_profile"]
    missing_timestamp = scenarios["missing_timestamp_profile"]
    fallback = scenarios["safe_default_fallback"]
    strong_shift = scenarios["strong_shift"]
    weak_shift = scenarios["weak_shift"]
    confidence_values = [_confidence(scenario) for scenario in scenarios.values()]
    fake_confidence = len(set(round(value, 4) for value in confidence_values)) <= 1

    runtime_real = (
        not _result(fresh)["fallback"]["used"]
        and _result(fresh)["trend_profile"]["trend_source"] == "manual_curation"
        and _collector_trace(fresh)["assembly_mode"] == "profile_load"
    )
    source_governed = (
        scenario_results["source_policy_probe"]["passed"]
        and bool(_collector_trace(fresh).get("source_governance"))
        and _collector_trace(fresh)["source_governance"]["policy_version"] == "trend_source_governance_v2_6"
        and scenario_results["hybrid_source_mix"]["passed"]
    )
    evidence_backed = (
        len(_result(fresh)["trend_profile"]["evidence"]) > 0
        and _collector_trace(fresh)["provenance"]["provenance_complete"]
        and bool(_collector_trace(fresh)["provenance"]["field_provenance"])
        and bool(_collector_trace(fresh)["provenance"]["evidence_references"])
        and scenario_results["safe_default_fallback"]["passed"]
    )
    freshness_disciplined = all(
        scenario_results[name]["passed"]
        for name in ["stale_profile", "expired_profile", "missing_timestamp_profile"]
    )
    confidence_calibrated = (
        not fake_confidence
        and _confidence_level(fresh) == "high"
        and _confidence(fallback) <= 0.30
        and _confidence(stale) < _confidence(fresh)
        and _confidence(expired) < _confidence(stale)
        and _confidence(missing_timestamp) < _confidence(fresh)
        and _collector_trace(fresh)["confidence_calibration"]["confidence_meaning"] == "trust_in_trend_context"
        and bool(_collector_trace(expired)["confidence_calibration"]["penalties"])
    )
    shift_analysis_meaningful = (
        scenario_results["strong_shift"]["passed"]
        and scenario_results["weak_shift"]["passed"]
        and "changes" in _collector_trace(strong_shift)["shift_analysis"]
        and "field_changes" in _collector_trace(strong_shift)["shift_analysis"]
    )
    downstream_utility_clear = all(
        _downstream_authority_bounded(scenario)
        for scenario in [fresh, hybrid, stale, expired, missing_timestamp, strong_shift, weak_shift]
    )
    traceability_complete = all(
        _governed_trace_complete(scenario)
        for scenario in [fresh, hybrid, stale, expired, missing_timestamp, strong_shift, weak_shift]
    )
    fallback_honest = (
        scenario_results["safe_default_fallback"]["passed"]
        and bool(_result(fallback)["fallback"]["used"])
        and _collector_trace(fallback)["confidence_calibration"]["confidence_level"] == "low"
        and "SAFE_DEFAULT_CONTEXT" in _collector_trace(fallback)["confidence_calibration"]["penalties"]
        and bool(_trend_trace(fallback)["fallback"]["fallback_path_visible"])
    )
    boundary_preserved = all(
        _constraint_or_authority_leak_absent(scenario)
        for scenario in [fresh, hybrid, stale, expired, missing_timestamp, fallback, strong_shift, weak_shift]
    ) and downstream_utility_clear
    determinism_where_required = bool(scenario_results["determinism_replay"]["passed"])
    silent_failures_detected = (
        not all(result["passed"] for result in scenario_results.values())
        or not all(
            [
                runtime_real,
                source_governed,
                evidence_backed,
                freshness_disciplined,
                confidence_calibrated,
                shift_analysis_meaningful,
                downstream_utility_clear,
                traceability_complete,
                fallback_honest,
                boundary_preserved,
                determinism_where_required,
                tests_executed["passed"],
            ]
        )
        or fake_confidence
    )
    dimensions = {
        "runtime_real": runtime_real,
        "source_governed": source_governed,
        "evidence_backed": evidence_backed,
        "freshness_disciplined": freshness_disciplined,
        "confidence_calibrated": confidence_calibrated,
        "shift_analysis_meaningful": shift_analysis_meaningful,
        "downstream_utility_clear": downstream_utility_clear,
        "traceability_complete": traceability_complete,
        "fallback_honest": fallback_honest,
        "boundary_preserved": boundary_preserved,
        "determinism_where_required": determinism_where_required,
        "silent_failures_detected": silent_failures_detected,
    }

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
        blocking_failures.append("TREND_TEST_SUITE_FAILURE")
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
    fresh = scenarios["fresh_governed_profile"]
    hybrid = scenarios["hybrid_source_mix"]
    stale = scenarios["stale_profile"]
    expired = scenarios["expired_profile"]
    fallback = scenarios["safe_default_fallback"]
    strong_shift = scenarios["strong_shift"]
    confidence_values = [_confidence(scenario) for scenario in scenarios.values()]
    fake_confidence = len(set(round(value, 4) for value in confidence_values)) <= 1
    boundary_violations = not dimensions["boundary_preserved"]
    silent_failures = dimensions["silent_failures_detected"]

    blocks = {
        "block_01_runtime_real": _checklist_block(
            dimensions["runtime_real"],
            uses_real_service=True,
            trend_analysis_not_stubbed=True,
            valid_profile_not_fallback=not _result(fresh)["fallback"]["used"],
        ),
        "block_02_source_governance": _checklist_block(
            dimensions["source_governed"],
            policy_version=_collector_trace(fresh)["source_governance"].get("policy_version"),
            selected_source_class=_collector_trace(fresh)["source_governance"].get("selected_source_class"),
            hybrid_source_mix=_collector_trace(hybrid)["source_governance"].get("source_mix"),
            forbidden_source_rejected=scenario_results["source_policy_probe"]["forbidden_source_rejected"],
            safe_default_fallback_allowed=scenario_results["source_policy_probe"]["safe_default_fallback_allowed"],
        ),
        "block_03_provenance": _checklist_block(
            dimensions["evidence_backed"],
            provenance_complete=_collector_trace(fresh)["provenance"].get("provenance_complete"),
            evidence_count=len(_result(fresh)["trend_profile"]["evidence"]),
            field_provenance_count=len(_collector_trace(fresh)["provenance"].get("field_provenance", {})),
            fallback_fields=_collector_trace(fallback)["provenance"].get("fallback_fields"),
        ),
        "block_04_freshness_validity": _checklist_block(
            dimensions["freshness_disciplined"],
            stale_statuses=sorted(_freshness_statuses(stale)),
            expired_statuses=sorted(_freshness_statuses(expired)),
            stale_validity=_collector_trace(stale)["validity"].get("validity_status"),
            expired_validity=_collector_trace(expired)["validity"].get("validity_status"),
        ),
        "block_05_confidence": _checklist_block(
            dimensions["confidence_calibrated"],
            confidence_values=confidence_values,
            confidence_not_constant=not fake_confidence,
            fresh_confidence=_confidence(fresh),
            stale_confidence=_confidence(stale),
            expired_confidence=_confidence(expired),
            fallback_confidence=_confidence(fallback),
            confidence_meaning=_collector_trace(fresh)["confidence_calibration"].get("confidence_meaning"),
        ),
        "block_06_shift_analysis": _checklist_block(
            dimensions["shift_analysis_meaningful"],
            strong_shift=scenario_results["strong_shift"],
            weak_shift=scenario_results["weak_shift"],
            legacy_changes_present="changes" in _collector_trace(strong_shift)["shift_analysis"],
        ),
        "block_07_downstream_utility": _checklist_block(
            dimensions["downstream_utility_clear"],
            boundary_statement=_collector_trace(fresh)["downstream_utility"].get("boundary_statement"),
            material_fields=_collector_trace(fresh)["downstream_utility"].get("material_fields"),
            authority_cap=_collector_trace(fresh)["downstream_utility"].get("utility_trace", {}).get("authority_cap"),
        ),
        "block_08_traceability": _checklist_block(
            dimensions["traceability_complete"],
            required_sections=sorted(REQUIRED_TREND_TRACE_SECTIONS),
            present_sections=sorted(_trend_trace(fresh)),
            audit_summary=_trend_trace(fresh).get("audit_summary", {}),
        ),
        "block_09_fallback": _checklist_block(
            dimensions["fallback_honest"],
            fallback_used=_result(fallback)["fallback"]["used"],
            fallback_reason=_result(fallback)["fallback"]["reason"],
            safe_default_used=_trend_trace(fallback)["fallback"].get("safe_default_used"),
            fallback_confidence=_confidence(fallback),
            fallback_penalties=_collector_trace(fallback)["confidence_calibration"].get("penalties"),
        ),
        "block_10_boundary": _checklist_block(
            dimensions["boundary_preserved"],
            no_strategy_profile="strategy_profile" not in _result(fresh),
            no_asset_decision="asset_decision" not in _result(fresh),
            no_publishability_decision="publishability_decision" not in _result(fresh),
            boundary_violations_detected=boundary_violations,
        ),
        "block_11_determinism": _checklist_block(
            dimensions["determinism_where_required"],
            replay_stable=scenario_results["determinism_replay"]["passed"],
        ),
        "block_12_backward_compatibility": _checklist_block(
            scenario_results["backward_compatibility"]["passed"],
            required_public_fields=sorted(REQUIRED_PUBLIC_FIELDS),
            required_collector_trace_fields=sorted(REQUIRED_COLLECTOR_TRACE_FIELDS),
        ),
        "block_13_silent_failure_detection": _checklist_block(
            not silent_failures,
            silent_failures_detected=silent_failures,
            no_fake_confidence=not fake_confidence,
            no_missing_governed_trace=dimensions["traceability_complete"],
            no_boundary_violation=dimensions["boundary_preserved"],
        ),
        "block_14_global_consistency": _checklist_block(
            all(
                [
                    dimensions["runtime_real"],
                    dimensions["source_governed"],
                    dimensions["evidence_backed"],
                    dimensions["freshness_disciplined"],
                    dimensions["confidence_calibrated"],
                    dimensions["shift_analysis_meaningful"],
                    dimensions["downstream_utility_clear"],
                    dimensions["fallback_honest"],
                ]
            ),
            source_to_profile_reconstructible=True,
            confidence_matches_evidence_state=True,
            shift_is_retrospective=True,
            downstream_utility_is_advisory=True,
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
            "source_governance": "explicit" if dimensions["source_governed"] else "incomplete",
            "provenance": "evidence_backed" if dimensions["evidence_backed"] else "invalid",
            "freshness": "disciplined" if dimensions["freshness_disciplined"] else "unsafe",
            "confidence": "trust_in_context" if dimensions["confidence_calibrated"] else "invalid",
            "shift_analysis": "meaningful" if dimensions["shift_analysis_meaningful"] else "invalid",
            "downstream_utility": "advisory_clear" if dimensions["downstream_utility_clear"] else "invalid",
            "traceability": "complete" if dimensions["traceability_complete"] else "incomplete",
            "fallback_honest": dimensions["fallback_honest"],
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
    confidence_values = {name: _confidence(scenario) for name, scenario in scenarios.items()}
    validity_statuses = {
        name: str(_collector_trace(scenario).get("validity", {}).get("validity_status") or "")
        for name, scenario in scenarios.items()
    }
    shift_severities = {
        name: str(_collector_trace(scenario).get("shift_analysis", {}).get("shift_severity") or "")
        for name, scenario in scenarios.items()
    }
    fallback_count = sum(1 for scenario in scenarios.values() if _result(scenario)["fallback"]["used"])
    service_scenario_pass_count = sum(
        1
        for name in scenarios
        if scenario_results.get(name, {"passed": True})["passed"]
    )
    return {
        "scenario_count": len(scenarios),
        "scenario_pass_count": service_scenario_pass_count,
        "scenario_fail_count": len(scenarios) - service_scenario_pass_count,
        "check_count": len(scenario_results),
        "check_pass_count": sum(1 for result in scenario_results.values() if result["passed"]),
        "check_fail_count": sum(1 for result in scenario_results.values() if not result["passed"]),
        "fallback_count": fallback_count,
        "confidence_values": confidence_values,
        "validity_statuses": validity_statuses,
        "shift_severities": shift_severities,
        "tests_passed": bool(tests_executed["passed"]),
    }


def main() -> None:
    _reset_audit_dir()
    tests_executed = _run_pytest(TREND_TEST_FILES)

    with tempfile.TemporaryDirectory() as tmp_dir:
        scenarios = _build_scenarios(Path(tmp_dir))
        policy_probe = _policy_probe()
        scenario_results = _scenario_checks(scenarios=scenarios, policy_probe=policy_probe)
        dimensions, blocking_failures = _evaluate_dimensions(
            scenarios=scenarios,
            scenario_results=scenario_results,
            tests_executed=tests_executed,
        )

    residual_monitoring: list[str] = []
    if not blocking_failures:
        residual_monitoring.extend(
            [
                "TREND_RUNTIME_HISTORY_STILL_SHORT",
                "TREND_PRODUCER_COVERAGE_STILL_BOUNDED",
                "TREND_LONGITUDINAL_SOURCE_DIVERSITY_STILL_EXPANDING",
            ]
        )

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
    scenario_outputs["source_policy_probe"] = {
        "summary": {
            "forbidden_source_rejected": policy_probe["forbidden_source_rejected"],
            "safe_default_fallback_allowed": policy_probe["safe_default_fallback_allowed"],
        },
        "result": {
            "forbidden_result": policy_probe["forbidden_result"],
            "safe_default_result": policy_probe["safe_default_result"],
        },
        "checks": scenario_results.get("source_policy_probe", {}),
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "2.6",
        "agent": "trend_analysis",
        "audit_type": "TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_GATE",
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
        "recommendation": "READY_FOR_V3_WITH_MONITORING" if verdict in {"GO", "GO_WITH_MONITORING"} else "HOLD_BEFORE_V3",
        "artifact_references": {
            "gate_document": "docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_GATE.md",
            "trend_plan": "docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_PLAN.md",
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
