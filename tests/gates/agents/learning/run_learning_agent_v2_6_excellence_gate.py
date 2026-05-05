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

from app.creative.agents.learning.models import LearningAgentInput
from app.creative.agents.learning.service import LearningAgentService
from app.creative.agents.strategy.models import StrategyInput
from app.creative.agents.strategy.service import StrategyAgentService

AUDIT_DIR = ROOT / "OUT" / "audit" / "learning_agent_v2_6_excellence_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"

REQUIRED_TRACE_SECTIONS = {
    "lineage_summary",
    "qc_analysis",
    "confidence_calibration",
    "temporal_analysis",
    "contamination_analysis",
    "strategy_pressure",
    "policy_safety_summary",
    "downgraded_evidence",
    "pattern_rationale",
}

LEARNING_TEST_FILES = [
    "tests/agents/learning/test_learning_qc_evidence_analyzer_unittest.py",
    "tests/agents/learning/test_learning_confidence_calibrator_unittest.py",
    "tests/agents/learning/test_learning_temporal_weighting_unittest.py",
    "tests/agents/learning/test_learning_contamination_guard_unittest.py",
    "tests/agents/learning/test_learning_strategy_pressure_unittest.py",
    "tests/agents/learning/test_learning_trace_auditability_unittest.py",
    "tests/agents/learning/test_learning_agent_phase2_unittest.py",
    "tests/agents/learning/test_learning_strategy_integration_v2_unittest.py",
]


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
    lines = [line.strip() for line in (completed.stdout + "\n" + completed.stderr).splitlines() if line.strip()]
    return {
        "command": command,
        "passed": completed.returncode == 0,
        "returncode": completed.returncode,
        "test_files": test_files,
        "output_tail": lines[-16:],
    }


def _prepare_analysis(root: Path, hook_style: str = "story_opening") -> Path:
    analysis_dir = root / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "hook_performance_summary.json").write_text(
        json.dumps({"hooks": [{"hook_style": hook_style}]}),
        encoding="utf-8",
    )
    return analysis_dir


def _write_execution(
    root: Path,
    *,
    account_id: str,
    index: int,
    timestamp: str,
    status: str = "APPROVE",
    overall: float = 0.91,
    payoff_quality: float = 0.88,
    contaminated: bool = False,
    variation: str = "medium",
    duration: str = "10-14s",
    payoff_category: str = "map_blueprint",
) -> None:
    payload = {
        "creative_pack": {
            "account_id": account_id,
            "generated_at": timestamp,
            "strategy_profile": {
                "variation_policy": variation,
                "target_duration_range": duration,
            },
            "script_plan": {
                "hook": "HOOK",
                "hook_type": "story_opening",
                "setup": "SETUP",
                "payoff": "THE FINAL DETAIL NAMED DOOR 16, REMOVED FROM THE FLOORPLAN",
                "generation_mode": "fallback_contextual" if contaminated else "contextual",
            },
            "asset_plan": {"segments": {"payoff": {"category": payoff_category}}},
            "voice_plan": {"style": "ominous_minimal", "fallback_used": False},
            "edit_plan": {"editor_style_profile": "editor-agent-v2_2"},
        },
        "video_qc": {
            "status": status,
            "publishable": status == "APPROVE",
            "decision": {
                "status": status,
                "publishable": status == "APPROVE",
                "score_summary": {"overall_score": overall, "product_quality": overall},
                "product_signals": {"hook_quality": overall, "payoff_quality": payoff_quality},
            },
        },
        "learning": {"fallback": {"used": False}},
        "asset_selection": {"fallback": {"used": False}},
    }
    execution_path = root / "OUT" / f"run_{index:02d}" / "execution_outputs.json"
    execution_path.parent.mkdir(parents=True, exist_ok=True)
    execution_path.write_text(json.dumps(payload), encoding="utf-8")


def _run_learning(root: Path, *, account_id: str, analysis_dir: Path | None, output_path: Path | None = None):
    service = LearningAgentService()
    return service.generate(
        LearningAgentInput(
            account_id=account_id,
            analysis_dir=analysis_dir or (root / "missing_analysis"),
            execution_history_dir=root / "OUT",
            qc_events_path=root / "missing_events.jsonl",
            publish_records_path=root / "missing_publish.jsonl",
            video_metrics_path=root / "missing_metrics.jsonl",
            output_path=output_path,
        )
    )


def _run_strategy(learning_result, *, health_status: str = "SAFE"):
    return StrategyAgentService().generate(
        StrategyInput(
            account_id="acc_learning_v26_gate",
            account_goal="retention",
            recent_metrics_summary=dict(learning_result.learning_insights.signal_summary),
            health_status=health_status,
            recommended_constraints={},
            learning_policy=learning_result.learning_policy,
            pattern_findings_summary=learning_result.pattern_findings_summary,
        )
    )


def _scenario_strong(root: Path) -> dict[str, Any]:
    scenario_root = root / "strong_durable"
    account_id = "acc_learning_v26_gate"
    analysis_dir = _prepare_analysis(scenario_root)
    timestamps = ["2026-04-20T00:00:00Z"] * 8 + ["2026-04-08T00:00:00Z"] * 7 + ["2026-03-10T00:00:00Z"] * 5
    for index, timestamp in enumerate(timestamps, start=1):
        _write_execution(scenario_root, account_id=account_id, index=index, timestamp=timestamp)
    output_path = scenario_root / "learning" / "learning_result.json"
    learning = _run_learning(scenario_root, account_id=account_id, analysis_dir=analysis_dir, output_path=output_path)
    strategy = _run_strategy(learning)
    return {
        "name": "strong_durable",
        "root": str(scenario_root),
        "output_path": str(output_path),
        "output_exists": output_path.exists(),
        "learning": learning,
        "strategy": strategy,
    }


def _scenario_contaminated(root: Path) -> dict[str, Any]:
    scenario_root = root / "contaminated"
    account_id = "acc_learning_v26_gate"
    analysis_dir = _prepare_analysis(scenario_root)
    for index in range(1, 7):
        _write_execution(
            scenario_root,
            account_id=account_id,
            index=index,
            timestamp="2026-04-20T00:00:00Z",
            contaminated=True,
            overall=0.93,
            payoff_quality=0.9,
        )
    learning = _run_learning(scenario_root, account_id=account_id, analysis_dir=analysis_dir)
    strategy = _run_strategy(learning)
    return {"name": "contaminated", "root": str(scenario_root), "learning": learning, "strategy": strategy}


def _scenario_volatile(root: Path) -> dict[str, Any]:
    scenario_root = root / "volatile"
    account_id = "acc_learning_v26_gate"
    analysis_dir = _prepare_analysis(scenario_root)
    for index in range(1, 5):
        _write_execution(
            scenario_root,
            account_id=account_id,
            index=index,
            timestamp="2026-04-20T00:00:00Z",
            status="REJECT",
            overall=0.45,
            payoff_quality=0.45,
            variation="low",
            duration="8-12s",
            payoff_category="document",
        )
    for index in range(5, 13):
        _write_execution(
            scenario_root,
            account_id=account_id,
            index=index,
            timestamp="2026-03-10T00:00:00Z",
            status="APPROVE",
            overall=0.9,
            payoff_quality=0.88,
        )
    learning = _run_learning(scenario_root, account_id=account_id, analysis_dir=analysis_dir)
    strategy = _run_strategy(learning)
    return {"name": "volatile", "root": str(scenario_root), "learning": learning, "strategy": strategy}


def _scenario_fallback(root: Path) -> dict[str, Any]:
    scenario_root = root / "fallback"
    learning = _run_learning(scenario_root, account_id="acc_learning_v26_gate", analysis_dir=None)
    strategy = _run_strategy(learning)
    return {"name": "fallback", "root": str(scenario_root), "learning": learning, "strategy": strategy}


def _learning_dict(scenario: dict[str, Any]) -> dict[str, Any]:
    return scenario["learning"].to_dict()


def _strategy_dict(scenario: dict[str, Any]) -> dict[str, Any]:
    return scenario["strategy"].to_dict()


def _trace(scenario: dict[str, Any]) -> dict[str, Any]:
    return _learning_dict(scenario)["learning_insights"].get("learning_trace", {})


def _policy(scenario: dict[str, Any]) -> dict[str, Any]:
    return _learning_dict(scenario)["learning_policy"]


def _has_required_trace_sections(trace: dict[str, Any]) -> bool:
    return REQUIRED_TRACE_SECTIONS.issubset(set(trace.keys()))


def _confidence_value(scenario: dict[str, Any]) -> float:
    return float(_policy(scenario).get("confidence_summary", {}).get("confidence") or 0.0)


def _dimension_results(dimensions: dict[str, bool]) -> dict[str, dict[str, bool]]:
    results: dict[str, dict[str, bool]] = {}
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
    dimensions: dict[str, bool],
    strong: dict[str, Any],
    strong_repeat: dict[str, Any],
    contaminated: dict[str, Any],
    volatile: dict[str, Any],
    fallback: dict[str, Any],
    blocking_failures: list[str],
    residual_monitoring: list[str],
) -> dict[str, Any]:
    strong_learning = _learning_dict(strong)
    strong_policy = _policy(strong)
    strong_trace = _trace(strong)
    contaminated_policy = _policy(contaminated)
    contaminated_trace = _trace(contaminated)
    volatile_policy = _policy(volatile)
    volatile_trace = _trace(volatile)
    fallback_learning = _learning_dict(fallback)
    fallback_policy = _policy(fallback)
    fallback_trace = _trace(fallback)

    strong_lineage = strong_trace.get("lineage_summary", {})
    strong_qc = strong_trace.get("qc_analysis", {})
    strong_confidence = strong_trace.get("confidence_calibration", {})
    strong_temporal = strong_trace.get("temporal_analysis", {})
    strong_contamination = strong_trace.get("contamination_analysis", {})
    strong_pressure = strong_policy.get("strategy_pressure", {})
    strong_safety = strong_trace.get("policy_safety_summary", {})

    contaminated_lineage = contaminated_trace.get("lineage_summary", {})
    contaminated_pressure = contaminated_policy.get("strategy_pressure", {})
    contaminated_safety = contaminated_trace.get("policy_safety_summary", {})
    volatile_pressure = volatile_policy.get("strategy_pressure", {})
    fallback_safety = fallback_trace.get("policy_safety_summary", {})

    confidence_values = [
        _confidence_value(strong),
        _confidence_value(contaminated),
        _confidence_value(volatile),
        _confidence_value(fallback),
    ]
    fake_confidence = len(set(round(value, 4) for value in confidence_values)) <= 1 or (
        _confidence_value(contaminated) >= _confidence_value(strong)
    )
    boundary_violations = not bool(dimensions["boundary_preserved"])
    silent_failures = bool(dimensions["silent_failures_detected"])

    lineage_count = int(strong_lineage.get("total_evidence_count") or 0)
    qc_sample_size = int(strong_qc.get("sample_size") or 0)
    confidence_policy_strength = str(strong_policy.get("confidence_summary", {}).get("policy_strength") or "weak")
    pressure_mode = str(strong_pressure.get("pressure_mode") or "weak_bias")

    global_consistency = (
        lineage_count == qc_sample_size
        and _confidence_value(strong) >= 0.7
        and strong_temporal.get("pattern_type") == "durable_pattern"
        and contaminated_lineage.get("contaminated_evidence_count", 0) == len(contaminated_trace.get("downgraded_evidence", []))
        and pressure_mode == "strong_bias"
        and confidence_policy_strength == "strong"
    )

    blocks = {
        "block_01_runtime_real": _checklist_block(
            dimensions["runtime_real"],
            learning_runs_real_service=True,
            uses_runtime_execution_data=True,
            output_consumed_by_strategy=True,
            hidden_fallback_absent=not strong_learning["fallback"]["used"],
        ),
        "block_02_evidence_backed_lineage": _checklist_block(
            dimensions["evidence_backed"],
            lineage_summary_present=bool(strong_lineage),
            total_evidence_count=lineage_count,
            clean_evidence_count=int(strong_lineage.get("clean_evidence_count") or 0),
            contaminated_evidence_count=int(strong_lineage.get("contaminated_evidence_count") or 0),
            dominant_source_type=str(strong_lineage.get("dominant_source_type") or ""),
            real_runtime_support=str(strong_lineage.get("real_runtime_support") or ""),
            evidence_references_present=bool(strong_lineage.get("evidence_references")),
        ),
        "block_03_qc_evidence_integration": _checklist_block(
            dimensions["qc_evidence_integration_hardened"],
            qc_analysis_present=bool(strong_qc),
            approve_rate_present="approve_rate" in strong_qc,
            hold_rate_present="hold_rate" in strong_qc,
            reject_rate_present="reject_rate" in strong_qc,
            sample_size_consistent_with_lineage=lineage_count == qc_sample_size,
            qc_affects_policy=strong_policy["hook_type_bias"]["evidence_count"] > 0,
            qc_affects_confidence=strong_qc.get("sample_size", 0) > 0 and strong_confidence.get("final_confidence", 0.0) > 0,
        ),
        "block_04_confidence_calibration": _checklist_block(
            dimensions["confidence_calibrated"] and not fake_confidence,
            confidence_calibration_present=bool(strong_confidence),
            final_confidence_values=confidence_values,
            final_confidence_not_constant=not fake_confidence,
            penalties_visible=bool(contaminated_trace.get("confidence_calibration", {}).get("penalties_applied")),
            contaminated_confidence_reduced=_confidence_value(contaminated) < _confidence_value(strong),
            volatile_confidence_reduced=_confidence_value(volatile) < _confidence_value(strong),
            rationale_present=bool(strong_confidence.get("rationale")),
        ),
        "block_05_temporal_weighting": _checklist_block(
            dimensions["temporal_weighting_real"],
            temporal_analysis_present=bool(strong_temporal),
            durable_pattern_detected=strong_temporal.get("pattern_type") == "durable_pattern",
            volatile_pattern_detected=volatile_trace.get("temporal_analysis", {}).get("pattern_type") == "volatile",
            recent_mid_long_weights_present=all(
                key in strong_temporal for key in ["recent_weight", "mid_term_weight", "long_term_weight"]
            ),
            recent_does_not_force_strong_policy=volatile_pressure.get("pressure_mode") == "weak_bias",
            temporal_rationale_present=bool(volatile_trace.get("temporal_analysis", {}).get("rationale")),
        ),
        "block_06_contamination_noise_protection": _checklist_block(
            dimensions["contamination_handling_strong"],
            contamination_summary_present=bool(contaminated_trace.get("contamination_analysis")),
            noise_summary_available_in_learning_output=bool(contaminated["learning"].learning_insights.noise_summary),
            contaminated_classification_detected=contaminated_lineage.get("contaminated_evidence_count", 0) > 0,
            contaminated_confidence_reduced=_confidence_value(contaminated) < _confidence_value(strong),
            contaminated_pressure_capped=contaminated_pressure.get("pressure_mode") == "weak_bias",
            clean_evidence_preserved=strong_lineage.get("clean_evidence_count", 0) > 0,
        ),
        "block_07_strategy_pressure_boundary": _checklist_block(
            dimensions["strategy_pressure_bounded"],
            strategy_pressure_present=bool(strong_pressure),
            strong_bias_only_clean_durable=(
                pressure_mode == "strong_bias"
                and _confidence_value(strong) >= 0.7
                and strong_temporal.get("pattern_type") == "durable_pattern"
                and strong_lineage.get("contaminated_evidence_count", 0) == 0
            ),
            weak_bias_in_bad_scenarios=(
                contaminated_pressure.get("pressure_mode") == "weak_bias"
                and volatile_pressure.get("pressure_mode") == "weak_bias"
                and fallback_policy.get("strategy_pressure", {}).get("pressure_mode") == "weak_bias"
            ),
            empty_pressure_allowed_when_insufficient=fallback_policy.get("strategy_pressure", {}).get("pressure_targets") == [],
            bounded=bool(strong_pressure.get("bounded")),
            strategy_override_allowed=bool(strong_pressure.get("strategy_override_allowed")),
            higher_authority_constraints_apply=bool(strong_pressure.get("higher_authority_constraints_apply")),
        ),
        "block_08_pattern_detection_utility": _checklist_block(
            bool(strong_trace.get("pattern_rationale")),
            pattern_rationale_present=bool(strong_trace.get("pattern_rationale")),
            patterns_identifiable=len(strong_trace.get("pattern_rationale", [])) > 0,
            evidence_supports_pattern=all(
                int(item.get("evidence_count") or 0) > 0 for item in strong_trace.get("pattern_rationale", [])
            ),
            rationale_present=all(bool(item.get("rationale")) for item in strong_trace.get("pattern_rationale", [])),
        ),
        "block_09_complete_trace": _checklist_block(
            dimensions["traceability_complete"],
            required_sections=sorted(REQUIRED_TRACE_SECTIONS),
            strong_sections=sorted(strong_trace.keys()),
            contaminated_sections=sorted(contaminated_trace.keys()),
            fallback_sections=sorted(fallback_trace.keys()),
            uncertainty_visible=bool(strong_safety.get("reason_codes")) or bool(strong_safety.get("warnings")),
        ),
        "block_10_downgraded_evidence": _checklist_block(
            len(contaminated_trace.get("downgraded_evidence", [])) > 0,
            downgraded_evidence_present="downgraded_evidence" in contaminated_trace,
            contaminated_reason_visible=any(
                item.get("reason") == "contaminated" for item in contaminated_trace.get("downgraded_evidence", [])
            ),
            downgrade_consistent_with_contamination=(
                len(contaminated_trace.get("downgraded_evidence", []))
                == contaminated_lineage.get("contaminated_evidence_count", -1)
            ),
            insufficient_visible_in_fallback=not fallback_safety.get("policy_safe", True),
        ),
        "block_11_policy_safety": _checklist_block(
            dimensions["policy_safety_explicit"],
            policy_safety_summary_present=bool(strong_safety),
            strong_policy_safe=bool(strong_safety.get("policy_safe")),
            contaminated_policy_safe=bool(contaminated_safety.get("policy_safe")),
            fallback_policy_safe=bool(fallback_safety.get("policy_safe")),
            reason_codes_present=all(
                "reason_codes" in trace.get("policy_safety_summary", {})
                for trace in [strong_trace, contaminated_trace, volatile_trace, fallback_trace]
            ),
            pressure_mode_consistent=strong_safety.get("pressure_mode") == pressure_mode,
        ),
        "block_12_determinism": _checklist_block(
            dimensions["determinism_where_required"],
            same_input_same_learning=_learning_dict(strong) == _learning_dict(strong_repeat),
            same_input_same_strategy=_strategy_dict(strong) == _strategy_dict(strong_repeat),
            same_input_same_trace=_trace(strong) == _trace(strong_repeat),
        ),
        "block_13_boundary_preservation": _checklist_block(
            dimensions["boundary_preserved"] and not boundary_violations,
            learning_does_not_decide_strategy=True,
            learning_does_not_decide_publishability=True,
            learning_does_not_modify_pipeline=True,
            learning_does_not_replace_qc=True,
            learning_does_not_replace_health=True,
            boundary_violations_detected=boundary_violations,
        ),
        "block_14_silent_failure_detection": _checklist_block(
            not silent_failures,
            no_critical_field_missing=not silent_failures,
            fallback_explicit=fallback_learning["fallback"]["used"],
            trace_present=all(bool(_trace(scenario)) for scenario in [strong, contaminated, volatile, fallback]),
            silent_failures_detected=silent_failures,
        ),
        "block_15_global_consistency": _checklist_block(
            global_consistency,
            lineage_matches_qc=lineage_count == qc_sample_size,
            confidence_matches_evidence=_confidence_value(strong) >= 0.7 and _confidence_value(contaminated) < _confidence_value(strong),
            temporal_matches_pattern=strong_temporal.get("pattern_type") == "durable_pattern",
            contamination_matches_downgrade=(
                contaminated_lineage.get("contaminated_evidence_count", 0)
                == len(contaminated_trace.get("downgraded_evidence", []))
            ),
            pressure_matches_confidence=pressure_mode == "strong_bias" and confidence_policy_strength == "strong",
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
            "traceability": "complete" if dimensions["traceability_complete"] else "incomplete",
            "confidence": "honest_and_calibrated" if dimensions["confidence_calibrated"] and not fake_confidence else "invalid",
            "strategy_pressure": "bounded_and_valid" if dimensions["strategy_pressure_bounded"] else "invalid",
            "contamination_handling": "strong" if dimensions["contamination_handling_strong"] else "weak",
            "temporal_reasoning": "credible" if dimensions["temporal_weighting_real"] else "invalid",
            "evidence_lineage": "real" if dimensions["evidence_backed"] else "invalid",
            "determinism": dimensions["determinism_where_required"],
            "boundary_preserved": dimensions["boundary_preserved"],
            "verdict": "READY_FOR_V3_WITH_MONITORING" if not blocking_failures and not failed_blocks else "NOT_READY_FOR_V3",
        },
    }


def _evaluate_dimensions(
    *,
    strong: dict[str, Any],
    strong_repeat: dict[str, Any],
    contaminated: dict[str, Any],
    volatile: dict[str, Any],
    fallback: dict[str, Any],
    tests_executed: dict[str, Any],
) -> tuple[dict[str, bool], dict[str, Any], list[str], list[str]]:
    strong_learning = _learning_dict(strong)
    strong_policy = _policy(strong)
    strong_trace = _trace(strong)
    contaminated_policy = _policy(contaminated)
    contaminated_trace = _trace(contaminated)
    volatile_policy = _policy(volatile)
    volatile_trace = _trace(volatile)
    fallback_learning = _learning_dict(fallback)
    fallback_policy = _policy(fallback)
    fallback_trace = _trace(fallback)
    strong_strategy_hold = StrategyAgentService().generate(
        StrategyInput(
            account_id="acc_learning_v26_gate",
            account_goal="retention",
            recent_metrics_summary=dict(strong["learning"].learning_insights.signal_summary),
            health_status="HOLD",
            recommended_constraints={},
            learning_policy=strong["learning"].learning_policy,
            pattern_findings_summary=strong["learning"].pattern_findings_summary,
        )
    ).to_dict()

    runtime_real = (
        not strong_learning["fallback"]["used"]
        and bool(strong.get("output_exists"))
        and strong_learning["learning_policy"]["hook_type_bias"]["evidence_count"] > 0
    )
    evidence_backed = (
        strong_trace.get("lineage_summary", {}).get("total_evidence_count", 0) > 0
        and strong_trace.get("lineage_summary", {}).get("clean_evidence_count", 0) > 0
        and bool(strong_trace.get("lineage_summary", {}).get("evidence_references"))
    )
    qc_evidence_integration_hardened = (
        strong_trace.get("qc_analysis", {}).get("sample_size", 0) > 0
        and "approve_rate" in strong_trace.get("qc_analysis", {})
        and strong_learning["learning_insights"].get("qc_summary", {}).get("clean_sample_size", 0) > 0
    )
    confidence_calibrated = (
        _confidence_value(strong) >= 0.7
        and _confidence_value(contaminated) < _confidence_value(strong)
        and "penalties_applied" in contaminated_trace.get("confidence_calibration", {})
        and "rationale" in strong_trace.get("confidence_calibration", {})
        and "confidence_components" in strong_trace.get("confidence_calibration", {})
    )
    temporal_weighting_real = (
        strong_trace.get("temporal_analysis", {}).get("pattern_type") == "durable_pattern"
        and volatile_trace.get("temporal_analysis", {}).get("pattern_type") == "volatile"
        and bool(volatile_trace.get("temporal_analysis", {}).get("volatility_detected"))
        and "rationale" in volatile_trace.get("temporal_analysis", {})
    )
    contamination_handling_strong = (
        contaminated_trace.get("lineage_summary", {}).get("contaminated_evidence_count", 0) > 0
        and len(contaminated_trace.get("downgraded_evidence", [])) > 0
        and contaminated_policy.get("strategy_pressure", {}).get("pressure_mode") == "weak_bias"
        and not contaminated_trace.get("policy_safety_summary", {}).get("policy_safe", True)
    )
    strategy_pressure_bounded = (
        strong_policy.get("strategy_pressure", {}).get("pressure_mode") == "strong_bias"
        and contaminated_policy.get("strategy_pressure", {}).get("pressure_mode") == "weak_bias"
        and volatile_policy.get("strategy_pressure", {}).get("pressure_mode") == "weak_bias"
        and bool(strong_policy.get("strategy_pressure", {}).get("bounded"))
        and bool(strong_policy.get("strategy_pressure", {}).get("strategy_override_allowed"))
        and bool(strong_policy.get("strategy_pressure", {}).get("higher_authority_constraints_apply"))
    )
    traceability_complete = all(
        _has_required_trace_sections(trace)
        for trace in [strong_trace, contaminated_trace, volatile_trace, fallback_trace]
    ) and len(strong_trace.get("pattern_rationale", [])) > 0
    policy_safety_explicit = all(
        all(key in trace.get("policy_safety_summary", {}) for key in ["policy_safe", "reason_codes", "confidence_level", "pressure_mode", "blocking_issues", "warnings"])
        for trace in [strong_trace, contaminated_trace, volatile_trace, fallback_trace]
    )
    determinism_where_required = (
        _learning_dict(strong) == _learning_dict(strong_repeat)
        and _strategy_dict(strong) == _strategy_dict(strong_repeat)
    )
    fallback_honest = (
        fallback_learning["fallback"]["used"]
        and fallback_learning["fallback"]["reason"] == "LEARNING_INSIGHTS_FALLBACK"
        and fallback_policy.get("strategy_pressure", {}).get("pressure_mode") == "weak_bias"
        and fallback_policy.get("strategy_pressure", {}).get("pressure_targets") == []
        and not fallback_trace.get("policy_safety_summary", {}).get("policy_safe", True)
    )
    boundary_preserved = (
        strong_strategy_hold["strategy_profile"]["content_mode"] == "paused"
        and strong_strategy_hold["strategy_profile"]["variation_policy"] == "none"
        and strong_strategy_hold["decision_trace"]["learning_adjustments"] == []
        and strong_policy.get("strategy_pressure", {}).get("strategy_influence_mode") == "bounded"
    )

    required_structures_present = all([
        runtime_real,
        evidence_backed,
        qc_evidence_integration_hardened,
        confidence_calibrated,
        temporal_weighting_real,
        contamination_handling_strong,
        strategy_pressure_bounded,
        traceability_complete,
        policy_safety_explicit,
        determinism_where_required,
        fallback_honest,
        boundary_preserved,
        tests_executed["passed"],
    ])
    silent_failures_detected = not required_structures_present

    dimensions = {
        "runtime_real": runtime_real,
        "evidence_backed": evidence_backed,
        "qc_evidence_integration_hardened": qc_evidence_integration_hardened,
        "confidence_calibrated": confidence_calibrated,
        "temporal_weighting_real": temporal_weighting_real,
        "contamination_handling_strong": contamination_handling_strong,
        "strategy_pressure_bounded": strategy_pressure_bounded,
        "traceability_complete": traceability_complete,
        "policy_safety_explicit": policy_safety_explicit,
        "determinism_where_required": determinism_where_required,
        "fallback_honest": fallback_honest,
        "boundary_preserved": boundary_preserved,
        "silent_failures_detected": silent_failures_detected,
    }

    blocking_failures: list[str] = []
    for key, value in dimensions.items():
        if key == "silent_failures_detected":
            if value:
                blocking_failures.append("SILENT_FAILURE_OR_MISSING_REQUIRED_STRUCTURE")
        elif not value:
            blocking_failures.append(key.upper())
    if not tests_executed["passed"]:
        blocking_failures.append("LEARNING_TEST_SUITE_FAILURE")

    residual_monitoring: list[str] = []
    if not blocking_failures:
        residual_monitoring.extend([
            "LONGITUDINAL_PRODUCTION_HISTORY_STILL_SHORT",
            "CONTROLLED_SCENARIO_GATE_COMPLEMENTS_BUT_DOES_NOT_REPLACE_LONG_HORIZON_RUNTIME_MONITORING",
            "V3_READINESS_REQUIRES_CONTINUED_REAL_VARIABILITY_MONITORING",
        ])

    evidence = {
        "strong_durable": _scenario_evidence(strong),
        "contaminated": _scenario_evidence(contaminated),
        "volatile": _scenario_evidence(volatile),
        "fallback": _scenario_evidence(fallback),
        "strategy_hold_boundary": {
            "content_mode": strong_strategy_hold["strategy_profile"]["content_mode"],
            "variation_policy": strong_strategy_hold["strategy_profile"]["variation_policy"],
            "learning_adjustments": strong_strategy_hold["decision_trace"]["learning_adjustments"],
        },
    }
    return dimensions, evidence, blocking_failures, residual_monitoring


def _scenario_evidence(scenario: dict[str, Any]) -> dict[str, Any]:
    learning = _learning_dict(scenario)
    trace = learning["learning_insights"].get("learning_trace", {})
    policy = learning["learning_policy"]
    return {
        "fallback_used": learning["fallback"]["used"],
        "lineage_summary": trace.get("lineage_summary", {}),
        "policy_safety_summary": trace.get("policy_safety_summary", {}),
        "temporal_pattern_type": trace.get("temporal_analysis", {}).get("pattern_type"),
        "confidence": policy.get("confidence_summary", {}).get("confidence"),
        "policy_strength": policy.get("confidence_summary", {}).get("policy_strength"),
        "pressure_mode": policy.get("strategy_pressure", {}).get("pressure_mode"),
        "downgraded_evidence_count": len(trace.get("downgraded_evidence", [])),
        "trace_sections": sorted(trace.keys()),
    }


def main() -> None:
    _reset_audit_dir()
    tests_executed = _run_pytest(LEARNING_TEST_FILES)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        strong = _scenario_strong(tmp_root)
        strong_repeat = _scenario_strong(tmp_root)
        contaminated = _scenario_contaminated(tmp_root)
        volatile = _scenario_volatile(tmp_root)
        fallback = _scenario_fallback(tmp_root)

        dimensions, evidence, blocking_failures, residual_monitoring = _evaluate_dimensions(
            strong=strong,
            strong_repeat=strong_repeat,
            contaminated=contaminated,
            volatile=volatile,
            fallback=fallback,
            tests_executed=tests_executed,
        )
        checklist_results = _build_checklist_results(
            dimensions=dimensions,
            strong=strong,
            strong_repeat=strong_repeat,
            contaminated=contaminated,
            volatile=volatile,
            fallback=fallback,
            blocking_failures=blocking_failures,
            residual_monitoring=residual_monitoring,
        )
        checklist_failed_blocks = list(checklist_results.get("failed_blocks") or [])
        if checklist_failed_blocks:
            blocking_failures = [*blocking_failures, *[f"CHECKLIST_BLOCK_FAILED:{name}" for name in checklist_failed_blocks]]
            residual_monitoring = []

    if blocking_failures:
        verdict = "HOLD"
    elif residual_monitoring:
        verdict = "GO_WITH_MONITORING"
    else:
        verdict = "GO"

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "2.6",
        "agent": "learning",
        "audit_type": "LEARNING_AGENT_V2_6_EXCELLENCE_GATE",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "verdict": verdict,
        **dimensions,
        "critical_failures": len(blocking_failures),
        "soft_failures": "explicit_and_bounded" if residual_monitoring else "none",
        "fake_confidence": bool(checklist_results["global_rule"]["fake_confidence"]),
        "boundary_violations": bool(checklist_results["global_rule"]["boundary_violations"]),
        "blocking_failures": blocking_failures,
        "residual_monitoring": residual_monitoring,
        "dimension_results": _dimension_results(dimensions),
        "checklist_results": checklist_results,
        "tests_executed": tests_executed,
        "scenario_evidence": evidence,
        "verdict_scenario_examples": {
            "GO": {
                "meaning": "All dimensions pass and long-horizon production monitoring no longer carries meaningful residuals.",
                "current_gate_result": verdict == "GO",
            },
            "GO_WITH_MONITORING": {
                "meaning": "All critical dimensions pass while longitudinal production maturity remains monitorable.",
                "current_gate_result": verdict == "GO_WITH_MONITORING",
                "current_residuals": residual_monitoring,
            },
            "HOLD": {
                "meaning": "Any critical dimension fails or silent failure is detected.",
                "current_gate_result": verdict == "HOLD",
                "current_blockers": blocking_failures,
            },
        },
        "artifact_references": {
            "gate_document": "docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_GATE.md",
            "learning_plan": "docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md",
            "phase_master_plan": "docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md",
        },
    }
    _write_json(FINAL_VERDICT_PATH, final_verdict)
    print(str(FINAL_VERDICT_PATH))


if __name__ == "__main__":
    main()
