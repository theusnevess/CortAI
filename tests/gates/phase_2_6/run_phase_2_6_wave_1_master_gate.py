from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.account_health.models import AccountHealthInput
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.learning.models import LearningAgentInput
from app.creative.agents.learning.service import LearningAgentService
from app.creative.agents.strategy.models import StrategyInput
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.models import TrendAnalysisInput
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService

AUDIT_DIR = ROOT / "OUT" / "audit" / "phase_2_6_wave_1_master_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
CROSS_AGENT_CONSISTENCY_PATH = AUDIT_DIR / "cross_agent_consistency.json"

REQUIRED_DOCS = {
    "phase_master_plan": "docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md",
    "learning_plan": "docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md",
    "account_health_plan": "docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md",
    "trend_plan": "docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_PLAN.md",
    "wave_1_master_gate_doc": "docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_1_MASTER_GATE.md",
    "master_state": "docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md",
}

REQUIRED_RUNNERS = {
    "learning_gate_runner": "tests/gates/agents/learning/run_learning_agent_v2_6_excellence_gate.py",
    "account_health_gate_runner": "tests/gates/agents/account_health/run_account_health_agent_v2_6_excellence_gate.py",
    "trend_gate_runner": "tests/gates/agents/trend_analysis/run_trend_analysis_agent_v2_6_excellence_gate.py",
    "partial_master_gate_runner": "tests/gates/phase_2_6/run_phase_2_6_partial_master_gate_learning_account_health.py",
    "wave_1_master_gate_runner": "tests/gates/phase_2_6/run_phase_2_6_wave_1_master_gate.py",
}

REQUIRED_JSON_ARTIFACTS = {
    "learning_gate": "OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json",
    "account_health_gate": "OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json",
    "trend_gate": "OUT/audit/trend_analysis_agent_v2_6_excellence_gate/final_verdict.json",
    "partial_master_gate": "OUT/audit/phase_2_6_partial_master_gate_learning_account_health/final_verdict.json",
    "system_governance_registry": "OUT/audit/system_governance_registry.json",
}

OPTIONAL_JSON_ARTIFACTS = {
    "all_agents_extreme": "OUT/audit/cortai_runtime_v2_5_all_agents_extreme_checklist/final_verdict.json",
    "max_integrity_gate": "OUT/audit/cortai_runtime_v2_5_max_integrity_gate/final_verdict.json",
    "final_audit_report": "OUT/audit/cortai_runtime_v2_5_final_audit/final_audit_report.json",
}

UNIT_TEST_FILES = [
    "tests/agents/learning/test_learning_qc_evidence_analyzer_unittest.py",
    "tests/agents/learning/test_learning_confidence_calibrator_unittest.py",
    "tests/agents/learning/test_learning_temporal_weighting_unittest.py",
    "tests/agents/learning/test_learning_contamination_guard_unittest.py",
    "tests/agents/learning/test_learning_strategy_pressure_unittest.py",
    "tests/agents/learning/test_learning_trace_auditability_unittest.py",
    "tests/agents/learning/test_learning_agent_phase2_unittest.py",
    "tests/agents/learning/test_learning_strategy_integration_v2_unittest.py",
    "tests/agents/account_health/test_account_health_telemetry_enrichment_unittest.py",
    "tests/agents/account_health/test_account_health_risk_components_unittest.py",
    "tests/agents/account_health/test_account_health_confidence_calibrator_unittest.py",
    "tests/agents/account_health/test_account_health_temporal_health_unittest.py",
    "tests/agents/account_health/test_account_health_degraded_input_policy_unittest.py",
    "tests/agents/account_health/test_account_health_constraint_rationale_unittest.py",
    "tests/agents/account_health/test_account_health_trace_auditability_unittest.py",
    "tests/agents/account_health/test_account_health_agent_phase2_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_trace_auditability_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_downstream_utility_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_shift_analysis_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_confidence_calibration_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_freshness_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_provenance_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_source_governance_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_agent_phase2_unittest.py",
    "tests/agents/strategy/test_strategy_agent_phase2_unittest.py",
    "tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py",
    "tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py",
    "tests/experiment/test_experiment_capability_phase2_unittest.py",
    "tests/attribution/test_content_attribution_phase_d_bounded_integration_unittest.py",
    "tests/content/test_content_pipeline_d27_unittest.py",
]

LEARNING_TRACE_SECTIONS = {
    "lineage_summary",
    "qc_analysis",
    "confidence_calibration",
    "temporal_analysis",
    "contamination_analysis",
    "strategy_pressure",
    "policy_safety_summary",
    "pattern_rationale",
    "downgraded_evidence",
}

HEALTH_TRACE_SECTIONS = {
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

TREND_TRACE_SECTIONS = {
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


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as exc:  # noqa: BLE001
        return {}, f"{type(exc).__name__}: {exc}"


def _run_pytest(test_files: list[str]) -> dict[str, Any]:
    command = [sys.executable, "-m", "pytest", "-q", *test_files]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=720,
        )
        duration = round(time.perf_counter() - started, 3)
        output_lines = [
            line.strip()
            for line in (completed.stdout + "\n" + completed.stderr).splitlines()
            if line.strip()
        ]
        return {
            "command": command,
            "passed": completed.returncode == 0,
            "timeout": False,
            "returncode": completed.returncode,
            "duration_seconds": duration,
            "test_files": test_files,
            "output_tail": output_lines[-30:],
        }
    except subprocess.TimeoutExpired as exc:
        duration = round(time.perf_counter() - started, 3)
        output = f"{exc.stdout or ''}\n{exc.stderr or ''}"
        output_lines = [line.strip() for line in output.splitlines() if line.strip()]
        return {
            "command": command,
            "passed": False,
            "timeout": True,
            "timeout_classification": "critical_validation_timeout",
            "returncode": None,
            "duration_seconds": duration,
            "test_files": test_files,
            "output_tail": output_lines[-30:] + ["PYTEST_TIMEOUT"],
        }


def _load_canonical_artifacts() -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, bool]]:
    artifacts: dict[str, dict[str, Any]] = {}
    json_errors: dict[str, str] = {}
    existence: dict[str, bool] = {}
    for name, rel_path in {**REQUIRED_JSON_ARTIFACTS, **OPTIONAL_JSON_ARTIFACTS}.items():
        path = ROOT / rel_path
        existence[name] = path.exists()
        if not path.exists():
            artifacts[name] = {}
            if name in REQUIRED_JSON_ARTIFACTS:
                json_errors[name] = "missing"
            continue
        payload, error = _load_json(path)
        artifacts[name] = payload
        if error:
            json_errors[name] = error
    return artifacts, json_errors, existence


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
    qc_status: str = "REAL",
    failure_status: str = "REAL",
    format_status: str = "REAL",
    metric_previous: float | None = None,
    metric_recent: float | None = None,
    qc_previous: int | None = None,
    qc_recent: int | None = None,
    failure_previous: float = 0.0,
    failure_recent: float = 0.0,
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


def _prepare_analysis(root: Path) -> Path:
    analysis_dir = root / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "hook_performance_summary.json").write_text(
        json.dumps({"hooks": [{"hook_style": "story_opening"}]}),
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
            "asset_plan": {"segments": {"payoff": {"category": "map_blueprint"}}},
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


def _run_learning(root: Path, *, account_id: str, analysis_dir: Path | None) -> Any:
    return LearningAgentService().generate(
        LearningAgentInput(
            account_id=account_id,
            analysis_dir=analysis_dir or (root / "missing_analysis"),
            execution_history_dir=root / "OUT",
            qc_events_path=root / "missing_events.jsonl",
            publish_records_path=root / "missing_publish.jsonl",
            video_metrics_path=root / "missing_metrics.jsonl",
            output_path=root / "learning_result.json",
        )
    )


def _learning_strong(root: Path, name: str = "learning_strong") -> Any:
    scenario_root = root / name
    analysis_dir = _prepare_analysis(scenario_root)
    timestamps = ["2026-04-20T00:00:00Z"] * 8 + ["2026-04-08T00:00:00Z"] * 7 + ["2026-03-10T00:00:00Z"] * 5
    for index, timestamp in enumerate(timestamps, start=1):
        _write_execution(
            scenario_root,
            account_id="acc_wave1_learning",
            index=index,
            timestamp=timestamp,
        )
    return _run_learning(scenario_root, account_id="acc_wave1_learning", analysis_dir=analysis_dir)


def _learning_contaminated(root: Path) -> Any:
    scenario_root = root / "learning_contaminated"
    analysis_dir = _prepare_analysis(scenario_root)
    for index in range(1, 7):
        _write_execution(
            scenario_root,
            account_id="acc_wave1_learning",
            index=index,
            timestamp="2026-04-20T00:00:00Z",
            contaminated=True,
            overall=0.93,
            payoff_quality=0.90,
        )
    return _run_learning(scenario_root, account_id="acc_wave1_learning", analysis_dir=analysis_dir)


def _learning_fallback(root: Path) -> Any:
    scenario_root = root / "learning_fallback"
    return _run_learning(scenario_root, account_id="acc_wave1_learning", analysis_dir=None)


def _profile_payload(
    *,
    updated_at: str | None = "2026-04-24T11:00:00Z",
    valid_until: str = "2026-04-30T00:00:00Z",
    confidence: float = 0.82,
    trend_source: str = "manual_curation",
    evidence_id: str = "manual_001",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "niche": "horror",
        "dominant_hooks": ["story_opening", "shock_statement"],
        "avg_duration": "35-60",
        "pacing": "fast_first_3s",
        "visual_style": "dark_backgrounds",
        "text_style": "large_caption_focus",
        "region": "US",
        "trend_source": trend_source,
        "valid_until": valid_until,
        "sample_size": 12,
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


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _trend_result(root: Path, *, stale: bool = False, expired: bool = False, fallback: bool = False) -> Any:
    trends_dir = root / ("trend_fallback" if fallback else "trend_expired" if expired else "trend_stale" if stale else "trend_fresh")
    if not fallback:
        if stale:
            payload = _profile_payload(updated_at="2026-04-19T00:00:00Z", valid_until="2026-05-02T00:00:00Z")
        elif expired:
            payload = _profile_payload(updated_at="2026-04-15T00:00:00Z", valid_until="2026-05-02T00:00:00Z")
        else:
            payload = _profile_payload()
        _write_payload(trends_dir / "current" / "horror.json", payload)
    return TrendAnalysisAgentService(trends_dir=trends_dir).load(
        TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z")
    )


def _build_learning_scenarios(root: Path) -> dict[str, Any]:
    strong = _learning_strong(root, "learning_strong")
    shutil.rmtree(root / "learning_strong", ignore_errors=True)
    strong_repeat = _learning_strong(root, "learning_strong")
    return {
        "strong": strong,
        "strong_repeat": strong_repeat,
        "contaminated": _learning_contaminated(root),
        "fallback": _learning_fallback(root),
    }


def _build_account_scenarios() -> dict[str, Any]:
    service = AccountHealthAgentService()
    return {
        "clean_safe": service.evaluate(_account_input(account_id="acc_wave1_clean")),
        "caution": service.evaluate(
            _account_input(
                account_id="acc_wave1_caution",
                recent_views_drop_ratio=0.45,
                recent_format_repetition_ratio=0.70,
                recent_low_performance_streak=2,
                metric_previous=0.20,
                metric_recent=0.45,
                qc_previous=1,
                qc_recent=2,
                format_previous=0.30,
                format_recent=0.70,
            )
        ),
        "hold": service.evaluate(
            _account_input(
                account_id="acc_wave1_hold",
                recent_views_drop_ratio=0.80,
                recent_low_performance_streak=4,
                metric_previous=0.40,
                metric_recent=0.80,
                qc_previous=2,
                qc_recent=4,
            )
        ),
        "missing_telemetry": service.evaluate(AccountHealthInput(account_id="acc_wave1_missing")),
        "severe_degraded": service.evaluate(
            _account_input(
                account_id="acc_wave1_severe_degraded",
                publish_status="DEGRADED",
                metric_status="STALE",
                metric_freshness="stale",
                qc_status="DEGRADED",
                failure_status="DEGRADED",
                format_status="STALE",
            )
        ),
    }


def _build_trend_scenarios(root: Path) -> dict[str, Any]:
    fresh = _trend_result(root)
    shutil.rmtree(root / "trend_fresh", ignore_errors=True)
    fresh_repeat = _trend_result(root)
    return {
        "fresh": fresh,
        "stale": _trend_result(root, stale=True),
        "expired": _trend_result(root, expired=True),
        "fallback": _trend_result(root, fallback=True),
        "fresh_repeat": fresh_repeat,
    }


def _strategy(account_result: Any, learning_result: Any, trend_result: Any | None) -> dict[str, Any]:
    result = StrategyAgentService().generate(
        StrategyInput(
            account_id="acc_wave1_strategy",
            account_goal="retention",
            recent_metrics_summary=dict(learning_result.learning_insights.signal_summary),
            health_status=account_result.decision.status,
            recommended_constraints=dict(account_result.decision.recommended_constraints),
            trend_profile=None if trend_result is None else trend_result.trend_profile,
            learning_policy=learning_result.learning_policy,
            pattern_findings_summary=learning_result.pattern_findings_summary,
        )
    )
    return result.to_dict()


def _learning_trace(result: Any) -> dict[str, Any]:
    return dict(result.to_dict()["learning_insights"].get("learning_trace") or {})


def _learning_policy(result: Any) -> dict[str, Any]:
    return dict(result.to_dict()["learning_policy"])


def _pressure_mode(result: Any) -> str:
    return str(_learning_policy(result).get("strategy_pressure", {}).get("pressure_mode") or "")


def _policy_confidence(result: Any) -> float:
    return float(_learning_policy(result).get("confidence_summary", {}).get("confidence") or 0.0)


def _account_summary(result: Any) -> dict[str, Any]:
    payload = result.to_dict()
    return {
        "decision": payload["decision"]["status"],
        "fallback_used": payload["fallback"]["used"],
        "risk_score": payload["risk_score"],
        "confidence": payload["confidence"],
        "confidence_level": payload["confidence_level"],
        "constraint_keys": sorted(payload["decision"]["recommended_constraints"]),
        "health_trace_sections": sorted(payload.get("health_trace", {})),
    }


def _learning_summary(result: Any) -> dict[str, Any]:
    trace = _learning_trace(result)
    policy = _learning_policy(result)
    return {
        "fallback_used": result.to_dict()["fallback"]["used"],
        "confidence": _policy_confidence(result),
        "policy_strength": policy.get("confidence_summary", {}).get("policy_strength"),
        "pressure_mode": _pressure_mode(result),
        "policy_safe": trace.get("policy_safety_summary", {}).get("policy_safe"),
        "downgraded_evidence_count": len(trace.get("downgraded_evidence", [])),
        "trace_sections": sorted(trace),
    }


def _trend_summary(result: Any) -> dict[str, Any]:
    payload = result.to_dict()
    collector = payload["collector_trace"]
    return {
        "fallback_used": payload["fallback"]["used"],
        "trend_source": payload["trend_profile"]["trend_source"],
        "calibrated_confidence": collector.get("confidence_calibration", {}).get("confidence"),
        "confidence_level": collector.get("confidence_calibration", {}).get("confidence_level"),
        "validity_status": collector.get("validity", {}).get("validity_status"),
        "source_class": collector.get("source_governance", {}).get("selected_source_class"),
        "trend_trace_sections": sorted(collector.get("trend_trace", {})),
    }


def _constraint_coverage_complete(account_result: Any) -> bool:
    payload = account_result.to_dict()
    constraints = dict(payload["decision"].get("recommended_constraints") or {})
    rationale = list(payload.get("constraint_rationale") or [])
    rationale_keys = [str(item.get("constraint_key") or "") for item in rationale]
    return sorted(rationale_keys) == sorted(str(key) for key in constraints) and len(rationale_keys) == len(set(rationale_keys))


def _health_trace_complete(account_result: Any) -> bool:
    payload = account_result.to_dict()
    trace = dict(payload.get("health_trace") or {})
    audit = dict(trace.get("audit_summary") or {})
    return (
        HEALTH_TRACE_SECTIONS.issubset(set(trace))
        and payload.get("decision_trace", {}).get("health_trace") == trace
        and bool(audit.get("reconstructible"))
        and bool(audit.get("required_sections_present"))
    )


def _learning_trace_complete(learning_result: Any) -> bool:
    trace = _learning_trace(learning_result)
    return LEARNING_TRACE_SECTIONS.issubset(set(trace))


def _trend_trace_complete(trend_result: Any) -> bool:
    payload = trend_result.to_dict()
    trace = dict(payload["collector_trace"].get("trend_trace") or {})
    audit = dict(trace.get("audit_summary") or {})
    if payload["fallback"]["used"]:
        return bool(trace.get("fallback", {}).get("fallback_path_visible"))
    return (
        TREND_TRACE_SECTIONS.issubset(set(trace))
        and bool(audit.get("reconstructible"))
        and bool(audit.get("required_sections_present"))
    )


def _block_result(passed: bool, **payload: Any) -> dict[str, Any]:
    return {"passed": bool(passed), **payload}


def _gate_ready(gate: dict[str, Any]) -> bool:
    return (
        gate.get("verdict") in {"GO", "GO_WITH_MONITORING"}
        and int(gate.get("critical_failures") or 0) == 0
        and not list(gate.get("blocking_failures") or [])
        and not bool(gate.get("silent_failures_detected", False))
        and not bool(gate.get("boundary_violations", False))
        and not bool(gate.get("fake_confidence", False))
    )


def _artifact_integrity(artifacts: dict[str, dict[str, Any]], json_errors: dict[str, str], existence: dict[str, bool]) -> dict[str, Any]:
    docs = {name: (ROOT / path).exists() for name, path in REQUIRED_DOCS.items()}
    runners = {name: (ROOT / path).exists() for name, path in REQUIRED_RUNNERS.items()}
    required_json = {name: existence.get(name, False) and name not in json_errors for name in REQUIRED_JSON_ARTIFACTS}
    checks = {
        "required_docs_exist": all(docs.values()),
        "required_runners_exist": all(runners.values()),
        "required_json_artifacts_valid": all(required_json.values()),
        "json_errors_absent": not json_errors,
    }
    return _block_result(all(checks.values()), docs=docs, runners=runners, required_json=required_json, json_errors=json_errors, **checks)


def _governance_consistency(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    registry = artifacts.get("system_governance_registry", {})
    core = dict(registry.get("core_pipeline") or {})
    rules = dict(registry.get("global_rules") or {})
    artifact_text = json.dumps(artifacts, sort_keys=True)
    checks = {
        "core_frozen": core.get("status") == "FROZEN_AND_VALIDATED",
        "governance_model_preserved": registry.get("governance_model") == "SUBSYSTEM_BASELINE_WITH_MONITORING",
        "change_policy_frozen": core.get("change_policy") == "FROZEN_UNLESS_GOVERNANCE_REOPEN",
        "no_core_modification": rules.get("no_core_modification") is True,
        "no_subsystem_mutation_without_reopen": rules.get("no_subsystem_mutation_without_reopen") is True,
        "isolated_subsystem_work": rules.get("new_work_must_be_isolated_subsystems") is True,
        "no_unauthorized_mutation_implied": "unauthorized_core_modification" not in artifact_text.lower(),
    }
    return _block_result(all(checks.values()), **checks)


def _learning_gate_integrity(gate: dict[str, Any]) -> dict[str, Any]:
    required = {
        "verdict_ready": gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "blocking_failures_empty": list(gate.get("blocking_failures") or []) == [],
        "critical_failures_zero": int(gate.get("critical_failures") or 0) == 0,
        "evidence_backed": gate.get("evidence_backed") is True,
        "confidence_calibrated": gate.get("confidence_calibrated") is True,
        "temporal_weighting_real": gate.get("temporal_weighting_real") is True,
        "contamination_handling_strong": gate.get("contamination_handling_strong") is True,
        "strategy_pressure_bounded": gate.get("strategy_pressure_bounded") is True,
        "traceability_complete": gate.get("traceability_complete") is True,
        "fallback_honest": gate.get("fallback_honest") is True,
        "boundary_preserved": gate.get("boundary_preserved") is True,
        "silent_failures_absent": gate.get("silent_failures_detected") is False,
    }
    return _block_result(all(required.values()), **required)


def _account_health_gate_integrity(gate: dict[str, Any]) -> dict[str, Any]:
    required = {
        "verdict_ready": gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "blocking_failures_empty": list(gate.get("blocking_failures") or []) == [],
        "critical_failures_zero": int(gate.get("critical_failures") or 0) == 0,
        "telemetry_enriched": gate.get("telemetry_enriched") is True,
        "risk_components_explicit": gate.get("risk_components_explicit") is True,
        "confidence_calibrated": gate.get("confidence_calibrated") is True,
        "temporal_health_real": gate.get("temporal_health_real") is True,
        "degraded_input_safe": gate.get("degraded_input_safe") is True,
        "constraints_rationale_complete": gate.get("constraints_rationale_complete") is True,
        "traceability_complete": gate.get("traceability_complete") is True,
        "hold_authority_preserved": gate.get("hold_authority_preserved") is True,
        "fallback_honest": gate.get("fallback_honest") is True,
        "boundary_preserved": gate.get("boundary_preserved") is True,
        "silent_failures_absent": gate.get("silent_failures_detected") is False,
    }
    return _block_result(all(required.values()), **required)


def _trend_gate_integrity(gate: dict[str, Any]) -> dict[str, Any]:
    required = {
        "verdict_ready": gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "blocking_failures_empty": list(gate.get("blocking_failures") or []) == [],
        "critical_failures_zero": int(gate.get("critical_failures") or 0) == 0,
        "runtime_real": gate.get("runtime_real") is True,
        "source_governed": gate.get("source_governed") is True,
        "evidence_backed": gate.get("evidence_backed") is True,
        "freshness_disciplined": gate.get("freshness_disciplined") is True,
        "confidence_calibrated": gate.get("confidence_calibrated") is True,
        "shift_analysis_meaningful": gate.get("shift_analysis_meaningful") is True,
        "downstream_utility_clear": gate.get("downstream_utility_clear") is True,
        "traceability_complete": gate.get("traceability_complete") is True,
        "fallback_honest": gate.get("fallback_honest") is True,
        "boundary_preserved": gate.get("boundary_preserved") is True,
        "determinism_where_required": gate.get("determinism_where_required") is True,
        "silent_failures_absent": gate.get("silent_failures_detected") is False,
    }
    return _block_result(all(required.values()), **required)


def _contract_integrity(learning: dict[str, Any], account: dict[str, Any], trend: dict[str, Any]) -> dict[str, Any]:
    strategy_result = _strategy(account["clean_safe"], learning["strong"], trend["fresh"])
    learning_payload = learning["strong"].to_dict()
    account_payload = account["clean_safe"].to_dict()
    trend_payload = trend["fresh"].to_dict()
    checks = {
        "learning_serializes": bool(json.dumps(learning_payload, sort_keys=True)),
        "account_health_serializes": bool(json.dumps(account_payload, sort_keys=True)),
        "trend_serializes": bool(json.dumps(trend_payload, sort_keys=True)),
        "strategy_serializes": bool(json.dumps(strategy_result, sort_keys=True)),
        "learning_trace_present": _learning_trace_complete(learning["strong"]),
        "health_trace_present": _health_trace_complete(account["clean_safe"]),
        "trend_trace_present": _trend_trace_complete(trend["fresh"]),
        "strategy_trace_present": bool(strategy_result.get("decision_trace")),
        "trend_result_backward_compatible": set(trend_payload) == {"trend_profile", "fallback", "validation_summary", "collector_trace"},
    }
    return _block_result(all(checks.values()), **checks)


def _build_cross_agent_scenarios(account: dict[str, Any], learning: dict[str, Any], trend: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    scenarios: dict[str, Any] = {}
    consistency: dict[str, Any] = {}

    hold_strategy = _strategy(account["hold"], learning["strong"], trend["fresh"])
    scenarios["health_hold_outranks_learning_and_trend"] = hold_strategy
    consistency["health_hold_outranks_learning_and_trend"] = _block_result(
        hold_strategy["strategy_profile"]["content_mode"] == "paused"
        and hold_strategy["strategy_profile"]["variation_policy"] == "none"
        and hold_strategy["decision_trace"]["learning_adjustments"] == []
        and hold_strategy["decision_trace"]["trend_adjustments"] == [],
        content_mode=hold_strategy["strategy_profile"]["content_mode"],
        learning_adjustments=hold_strategy["decision_trace"]["learning_adjustments"],
        trend_adjustments=hold_strategy["decision_trace"]["trend_adjustments"],
    )

    caution_strategy = _strategy(account["caution"], learning["strong"], trend["fresh"])
    scenarios["health_caution_constrains_without_becoming_strategy"] = caution_strategy
    consistency["health_caution_constrains_without_becoming_strategy"] = _block_result(
        caution_strategy["decision_trace"]["health_status"] == "CAUTION"
        and caution_strategy["strategy_profile"]["content_mode"] == "conservative"
        and bool(caution_strategy["decision_trace"]["constraint_adjustments"]),
        health_status=caution_strategy["decision_trace"]["health_status"],
        constraint_adjustments=caution_strategy["decision_trace"]["constraint_adjustments"],
    )

    safe_strategy = _strategy(account["clean_safe"], learning["strong"], trend["fresh"])
    scenarios["learning_strong_pressure_bounded"] = safe_strategy
    consistency["learning_strong_pressure_bounded"] = _block_result(
        _pressure_mode(learning["strong"]) == "strong_bias"
        and safe_strategy["decision_trace"]["learning_adjustments"] != []
        and safe_strategy["strategy_profile"]["content_mode"] != "paused",
        pressure_mode=_pressure_mode(learning["strong"]),
        learning_adjustments=safe_strategy["decision_trace"]["learning_adjustments"],
    )

    scenarios["trend_high_confidence_context_only"] = safe_strategy
    consistency["trend_high_confidence_context_only"] = _block_result(
        trend["fresh"].collector_trace["confidence_calibration"]["confidence_level"] == "high"
        and bool(safe_strategy["decision_trace"]["trend_adjustments"])
        and trend["fresh"].collector_trace["downstream_utility"]["utility_trace"]["authority_cap"] == "advisory",
        trend_adjustments=safe_strategy["decision_trace"]["trend_adjustments"],
        authority_cap=trend["fresh"].collector_trace["downstream_utility"]["utility_trace"]["authority_cap"],
    )

    fallback_trend_strategy = _strategy(account["clean_safe"], learning["strong"], trend["fallback"])
    scenarios["trend_fallback_low_confidence_no_strong_strategy_authority"] = fallback_trend_strategy
    consistency["trend_fallback_low_confidence_no_strong_strategy_authority"] = _block_result(
        trend["fallback"].fallback.used
        and trend["fallback"].collector_trace["confidence_calibration"]["confidence_level"] == "low"
        and fallback_trend_strategy["decision_trace"]["trend_adjustments"] == [],
        trend_confidence_level=trend["fallback"].collector_trace["confidence_calibration"]["confidence_level"],
        trend_adjustments=fallback_trend_strategy["decision_trace"]["trend_adjustments"],
    )

    contaminated_strategy = _strategy(account["clean_safe"], learning["contaminated"], trend["fresh"])
    scenarios["learning_contaminated_evidence_stays_weak_even_if_trend_strong"] = contaminated_strategy
    consistency["learning_contaminated_evidence_stays_weak_even_if_trend_strong"] = _block_result(
        _pressure_mode(learning["contaminated"]) == "weak_bias"
        and _policy_confidence(learning["contaminated"]) < _policy_confidence(learning["strong"])
        and trend["fresh"].collector_trace["confidence_calibration"]["confidence_level"] == "high",
        contaminated_pressure=_pressure_mode(learning["contaminated"]),
        contaminated_confidence=_policy_confidence(learning["contaminated"]),
        trend_confidence=trend["fresh"].collector_trace["confidence_calibration"]["confidence_level"],
    )

    scenarios["trend_stale_expired_context_visible"] = {
        "stale": trend["stale"].to_dict(),
        "expired": trend["expired"].to_dict(),
    }
    stale_items = trend["stale"].collector_trace["trend_trace"]["missing_or_degraded_inputs"]
    expired_items = trend["expired"].collector_trace["trend_trace"]["missing_or_degraded_inputs"]
    consistency["trend_stale_expired_context_visible"] = _block_result(
        any(item["kind"] == "stale_source" for item in stale_items)
        and any(item["kind"] == "expired_source" for item in expired_items),
        stale_missing_or_degraded=stale_items,
        expired_missing_or_degraded=expired_items,
    )

    consistency["combined_upstream_traces_not_contradictory"] = _block_result(
        _health_trace_complete(account["clean_safe"])
        and _learning_trace_complete(learning["strong"])
        and _trend_trace_complete(trend["fresh"])
        and safe_strategy["decision_trace"]["signals_seen"]["trend_present"]
        and safe_strategy["decision_trace"]["signals_seen"]["learning_policy_present"],
        health_trace_sections=sorted(account["clean_safe"].health_trace),
        learning_trace_sections=sorted(_learning_trace(learning["strong"])),
        trend_trace_sections=sorted(trend["fresh"].collector_trace["trend_trace"]),
    )

    return scenarios, consistency


def _fallback_honesty(account: dict[str, Any], learning: dict[str, Any], trend: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "learning_fallback_visible": learning["fallback"].fallback.used
        and _pressure_mode(learning["fallback"]) == "weak_bias",
        "learning_contamination_visible": bool(_learning_trace(learning["contaminated"]).get("downgraded_evidence")),
        "account_degraded_visible": account["missing_telemetry"].degraded_input_decision.get("degraded_input_detected") is True,
        "trend_fallback_visible": trend["fallback"].fallback.used
        and trend["fallback"].collector_trace["confidence_calibration"]["confidence_level"] == "low",
        "fallback_not_strong_evidence": _policy_confidence(learning["fallback"]) < _policy_confidence(learning["strong"])
        and trend["fallback"].collector_trace["confidence_calibration"]["confidence"] <= 0.30
        and account["missing_telemetry"].confidence_level == "low",
    }
    return _block_result(all(checks.values()), **checks)


def _boundary_preservation(cross_consistency: dict[str, Any], trend: dict[str, Any]) -> dict[str, Any]:
    trend_payload = json.dumps(trend["fresh"].to_dict(), sort_keys=True)
    checks = {
        "learning_does_not_override_health": cross_consistency["health_hold_outranks_learning_and_trend"]["passed"],
        "account_health_does_not_become_strategy": cross_consistency["health_caution_constrains_without_becoming_strategy"]["passed"],
        "trend_context_only": cross_consistency["trend_high_confidence_context_only"]["passed"],
        "strategy_control_layer_preserved": all(item.get("passed") for item in cross_consistency.values()),
        "trend_no_hidden_authority": all(
            token not in trend_payload
            for token in ['"strategy_profile"', '"asset_decision"', '"publishability_decision"', '"recommended_constraints"']
        ),
    }
    return _block_result(all(checks.values()), **checks)


def _security_surface(account: dict[str, Any], learning: dict[str, Any], trend: dict[str, Any], cross_consistency: dict[str, Any]) -> dict[str, Any]:
    account_confidences = {round(result.confidence, 4) for result in account.values()}
    learning_confidences = {round(_policy_confidence(result), 4) for result in learning.values()}
    trend_confidences = {
        round(float(result.collector_trace["confidence_calibration"]["confidence"]), 4)
        for result in trend.values()
    }
    checks = {
        "fake_confidence_absent": len(account_confidences) > 1 and len(learning_confidences) > 1 and len(trend_confidences) > 1,
        "fake_telemetry_absent": account["missing_telemetry"].telemetry_summary.get("source_status_distribution", {}).get("ABSENT", 0) > 0,
        "fake_provenance_absent": bool(trend["fresh"].collector_trace["provenance"].get("field_provenance")),
        "hidden_degraded_input_absent": account["missing_telemetry"].degraded_input_decision.get("degraded_input_detected") is True,
        "hidden_fallback_absent": learning["fallback"].fallback.used and trend["fallback"].fallback.used,
        "orphan_constraints_absent": all(_constraint_coverage_complete(result) for result in account.values()),
        "silent_hold_downgrade_absent": account["hold"].decision.status == "HOLD" and account["severe_degraded"].decision.status == "HOLD",
        "trend_fallback_not_inflated": trend["fallback"].collector_trace["confidence_calibration"]["confidence_level"] == "low",
        "learning_contamination_does_not_dominate": _pressure_mode(learning["contaminated"]) == "weak_bias",
        "cross_agent_checks_pass": all(item.get("passed") for item in cross_consistency.values()),
    }
    return _block_result(all(checks.values()), **checks)


def _trace_auditability(account: dict[str, Any], learning: dict[str, Any], trend: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "learning_trace_reconstructs_policy": all(_learning_trace_complete(result) for result in learning.values()),
        "account_health_trace_reconstructs_decision": all(_health_trace_complete(result) for result in account.values()),
        "trend_trace_reconstructs_profile": _trend_trace_complete(trend["fresh"])
        and _trend_trace_complete(trend["stale"])
        and _trend_trace_complete(trend["expired"]),
        "learning_downgraded_evidence_visible": bool(_learning_trace(learning["contaminated"]).get("downgraded_evidence")),
        "health_missing_inputs_visible": bool(account["missing_telemetry"].health_trace.get("downgraded_or_missing_inputs")),
        "trend_missing_or_degraded_visible": bool(trend["stale"].collector_trace["trend_trace"].get("missing_or_degraded_inputs")),
    }
    return _block_result(all(checks.values()), **checks)


def _residual_monitoring_classification(artifacts: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    child_residuals = []
    for name in ["learning_gate", "account_health_gate", "trend_gate", "partial_master_gate"]:
        child_residuals.extend(str(item) for item in list(artifacts.get(name, {}).get("residual_monitoring") or []))
    allowed_markers = [
        "HISTORY_STILL_SHORT",
        "RUNTIME_HISTORY_STILL_SHORT",
        "PRODUCER_COVERAGE_STILL_EXPANDING",
        "PRODUCER_COVERAGE_STILL_BOUNDED",
        "LONGITUDINAL",
        "PRODUCTION_HISTORY",
        "PRODUCTION_MATURITY",
        "REAL_VARIABILITY_MONITORING",
        "CONTROLLED_SCENARIO_GATE",
        "SOURCE_DIVERSITY_STILL_EXPANDING",
    ]
    structural_markers = ["BOUNDARY", "TRACE_INCOMPLETE", "FAKE", "SILENT", "BLOCKING", "HOLD_BROKEN", "UNAUTHORIZED"]
    unexpected = [
        item
        for item in child_residuals
        if not any(marker in item for marker in allowed_markers) or any(marker in item for marker in structural_markers)
    ]
    return _block_result(not unexpected, child_residuals=sorted(set(child_residuals)), unexpected_residuals=unexpected), sorted(set(child_residuals))


def _master_consistency(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    partial = artifacts.get("partial_master_gate", {})
    registry = artifacts.get("system_governance_registry", {})
    optional_verdicts = {}
    for name in OPTIONAL_JSON_ARTIFACTS:
        artifact = artifacts.get(name, {})
        optional_verdicts[name] = artifact.get("verdict") or artifact.get("overall_verdict") or artifact.get("status")
    checks = {
        "partial_master_non_blocking": partial.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "partial_master_recommended_trend": partial.get("recommendation") == "PROCEED_TO_TREND_ANALYSIS_AGENT_V2_6_PLAN",
        "governance_registry_present": registry.get("system_version") == "CORTAI_RUNTIME_V2_5",
        "no_optional_recent_hold": all(value != "HOLD" for value in optional_verdicts.values()),
        "master_state_doc_exists": (ROOT / "docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md").exists(),
    }
    return _block_result(all(checks.values()), optional_verdicts=optional_verdicts, **checks)


def _build_blocks(
    *,
    artifacts: dict[str, dict[str, Any]],
    json_errors: dict[str, str],
    existence: dict[str, bool],
    tests_executed: dict[str, Any],
    account: dict[str, Any],
    learning: dict[str, Any],
    trend: dict[str, Any],
    cross_agent: dict[str, Any],
    cross_consistency: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    blocks: dict[str, Any] = {}
    blocks["block_a_artifact_integrity"] = _artifact_integrity(artifacts, json_errors, existence)
    blocks["block_b_governance_consistency"] = _governance_consistency(artifacts)
    blocks["block_c_learning_gate_integrity"] = _learning_gate_integrity(artifacts.get("learning_gate", {}))
    blocks["block_d_account_health_gate_integrity"] = _account_health_gate_integrity(artifacts.get("account_health_gate", {}))
    blocks["block_e_trend_analysis_gate_integrity"] = _trend_gate_integrity(artifacts.get("trend_gate", {}))
    blocks["block_f_contract_integrity"] = _contract_integrity(learning, account, trend)
    blocks["block_g_test_battery"] = _block_result(
        tests_executed.get("passed") is True,
        tests_executed=tests_executed,
        timeout_classified=not tests_executed.get("timeout") or bool(tests_executed.get("timeout_classification")),
    )
    blocks["block_h_cross_agent_upstream_scenarios"] = _block_result(
        all(item.get("passed") for item in cross_consistency.values()),
        scenario_results=cross_consistency,
        scenarios=sorted(cross_agent),
    )
    account_replay_one = AccountHealthAgentService().evaluate(_account_input(account_id="acc_wave1_replay")).to_dict()
    account_replay_two = AccountHealthAgentService().evaluate(_account_input(account_id="acc_wave1_replay")).to_dict()
    cross_replay = _strategy(account["clean_safe"], learning["strong"], trend["fresh"])
    blocks["block_i_determinism_and_replay"] = _block_result(
        learning["strong"].to_dict() == learning["strong_repeat"].to_dict()
        and account_replay_one == account_replay_two
        and trend["fresh"].to_dict() == trend["fresh_repeat"].to_dict()
        and cross_agent["trend_high_confidence_context_only"] == cross_replay,
        learning_replay_stable=learning["strong"].to_dict() == learning["strong_repeat"].to_dict(),
        account_health_replay_stable=account_replay_one == account_replay_two,
        trend_replay_stable=trend["fresh"].to_dict() == trend["fresh_repeat"].to_dict(),
        combined_upstream_replay_stable=cross_agent["trend_high_confidence_context_only"] == cross_replay,
    )
    blocks["block_j_fallback_honesty"] = _fallback_honesty(account, learning, trend)
    blocks["block_k_boundary_preservation"] = _boundary_preservation(cross_consistency, trend)
    blocks["block_l_security_logical_surface"] = _security_surface(account, learning, trend, cross_consistency)
    blocks["block_m_trace_auditability"] = _trace_auditability(account, learning, trend)
    block_n, residuals = _residual_monitoring_classification(artifacts)
    blocks["block_n_residual_monitoring_classification"] = block_n
    blocks["block_o_master_consistency"] = _master_consistency(artifacts)
    failed_before_final = [name for name, block in blocks.items() if not block.get("passed")]
    blocks["block_p_final_release_decision"] = _block_result(
        not failed_before_final,
        failed_blocks_before_final=failed_before_final,
        final_rule="HOLD on any critical block; GO_WITH_MONITORING on bounded residuals; GO only without residuals.",
    )
    return blocks, residuals


def _build_checklist_results(blocks: dict[str, Any]) -> dict[str, Any]:
    failed_blocks = [name for name, block in blocks.items() if not block.get("passed")]
    return {
        "blocks": blocks,
        "failed_blocks": failed_blocks,
        "global_rule": {
            "critical_failures": len(failed_blocks),
            "soft_failures": "explicit_and_bounded",
            "fake_confidence": not blocks["block_l_security_logical_surface"].get("fake_confidence_absent", False),
            "silent_failures": any(
                not blocks[name].get("passed")
                for name in [
                    "block_a_artifact_integrity",
                    "block_f_contract_integrity",
                    "block_m_trace_auditability",
                ]
            ),
            "boundary_violations": not blocks["block_k_boundary_preservation"].get("passed", False),
            "verdict": "ONLY_THEN_PROCEED" if not failed_blocks else "DO_NOT_PROCEED",
        },
        "final_release_criteria": {
            "critical_failures": len(failed_blocks),
            "wave_1_ready": not failed_blocks,
            "traceability": "complete" if blocks["block_m_trace_auditability"].get("passed") else "incomplete",
            "boundary_preserved": blocks["block_k_boundary_preservation"].get("passed"),
            "determinism": blocks["block_i_determinism_and_replay"].get("passed"),
        },
    }


def _build_metrics(
    *,
    blocks: dict[str, Any],
    tests_executed: dict[str, Any],
    account: dict[str, Any],
    learning: dict[str, Any],
    trend: dict[str, Any],
    blocking_failures: list[str],
) -> dict[str, Any]:
    return {
        "block_count": len(blocks),
        "block_pass_count": sum(1 for block in blocks.values() if block.get("passed")),
        "block_fail_count": sum(1 for block in blocks.values() if not block.get("passed")),
        "critical_failures": len(blocking_failures),
        "blocking_failures_count": len(blocking_failures),
        "test_failures": 0 if tests_executed.get("passed") else 1,
        "boundary_violations_detected": not blocks["block_k_boundary_preservation"].get("passed", False),
        "silent_failures_detected": any(not block.get("passed") for block in blocks.values()),
        "fake_confidence_detected": not blocks["block_l_security_logical_surface"].get("fake_confidence_absent", False),
        "non_determinism_detected": not blocks["block_i_determinism_and_replay"].get("passed", False),
        "account_health_decisions": {name: result.decision.status for name, result in account.items()},
        "learning_pressure_modes": {name: _pressure_mode(result) for name, result in learning.items()},
        "trend_validity_statuses": {name: result.collector_trace.get("validity", {}).get("validity_status") for name, result in trend.items()},
        "pytest_duration_seconds": tests_executed.get("duration_seconds"),
    }


def _scenario_outputs(account: dict[str, Any], learning: dict[str, Any], trend: dict[str, Any], cross_agent: dict[str, Any], cross_consistency: dict[str, Any]) -> dict[str, Any]:
    return {
        "account_health": {name: {"summary": _account_summary(result), "result": result.to_dict()} for name, result in account.items()},
        "learning": {name: {"summary": _learning_summary(result), "result": result.to_dict()} for name, result in learning.items()},
        "trend_analysis": {name: {"summary": _trend_summary(result), "result": result.to_dict()} for name, result in trend.items()},
        "cross_agent": cross_agent,
        "cross_agent_consistency": cross_consistency,
    }


def _agent_summary(gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "verdict": gate.get("verdict"),
        "ready_for_v3_with_monitoring": _gate_ready(gate),
        "critical_failures": int(gate.get("critical_failures") or 0),
        "blocking_failures": list(gate.get("blocking_failures") or []),
    }


def _run_gate() -> dict[str, Any]:
    _reset_audit_dir()
    artifacts, json_errors, existence = _load_canonical_artifacts()
    tests_executed = _run_pytest(UNIT_TEST_FILES)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        learning = _build_learning_scenarios(tmp_root)
        account = _build_account_scenarios()
        trend = _build_trend_scenarios(tmp_root)
        cross_agent, cross_consistency = _build_cross_agent_scenarios(account, learning, trend)
        blocks, residuals = _build_blocks(
            artifacts=artifacts,
            json_errors=json_errors,
            existence=existence,
            tests_executed=tests_executed,
            account=account,
            learning=learning,
            trend=trend,
            cross_agent=cross_agent,
            cross_consistency=cross_consistency,
        )
        checklist_results = _build_checklist_results(blocks)
        blocking_failures = [f"BLOCK_FAILED:{name}" for name in checklist_results["failed_blocks"]]
        if tests_executed.get("timeout"):
            blocking_failures.append("UNIT_TEST_BATTERY_TIMEOUT")
        if not tests_executed.get("passed"):
            blocking_failures.append("UNIT_TEST_BATTERY_FAILED")
        residual_monitoring = [] if blocking_failures else residuals
        if blocking_failures:
            verdict = "HOLD"
        elif residual_monitoring:
            verdict = "GO_WITH_MONITORING"
        else:
            verdict = "GO"
        metrics = _build_metrics(
            blocks=blocks,
            tests_executed=tests_executed,
            account=account,
            learning=learning,
            trend=trend,
            blocking_failures=blocking_failures,
        )
        scenario_outputs = _scenario_outputs(account, learning, trend, cross_agent, cross_consistency)
        final_verdict = {
            "system": "CORTAI_RUNTIME_V2_5",
            "phase": "2.6",
            "audit_type": "PHASE_2_6_WAVE_1_MASTER_GATE",
            "verdict": verdict,
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "wave_1_agents": {
                "learning_agent_v2_6": _agent_summary(artifacts.get("learning_gate", {})),
                "account_health_agent_v2_6": _agent_summary(artifacts.get("account_health_gate", {})),
                "trend_analysis_agent_v2_6": _agent_summary(artifacts.get("trend_gate", {})),
            },
            "blocks": {name: {"passed": bool(block.get("passed"))} for name, block in blocks.items()},
            "tests_executed": [tests_executed],
            "metrics": metrics,
            "blocking_failures": blocking_failures,
            "residual_monitoring": residual_monitoring,
            "recommendation": "PROCEED_TO_PHASE_2_6_WAVE_2_PLAN"
            if verdict in {"GO", "GO_WITH_MONITORING"}
            else "HOLD_BEFORE_WAVE_2",
        }
        _write_json(CHECKLIST_RESULTS_PATH, checklist_results)
        _write_json(SCENARIO_OUTPUTS_PATH, scenario_outputs)
        _write_json(METRICS_PATH, metrics)
        _write_json(CROSS_AGENT_CONSISTENCY_PATH, cross_consistency)
        _write_json(FINAL_VERDICT_PATH, final_verdict)
        return final_verdict


def main() -> None:
    try:
        verdict = _run_gate()
    except Exception as exc:  # noqa: BLE001
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        verdict = {
            "system": "CORTAI_RUNTIME_V2_5",
            "phase": "2.6",
            "audit_type": "PHASE_2_6_WAVE_1_MASTER_GATE",
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "verdict": "HOLD",
            "blocking_failures": ["GATE_RUNNER_EXCEPTION"],
            "exception": f"{type(exc).__name__}: {exc}",
            "residual_monitoring": [],
            "recommendation": "HOLD_BEFORE_WAVE_2",
        }
        _write_json(FINAL_VERDICT_PATH, verdict)
        raise
    print(json.dumps({"artifact": str(FINAL_VERDICT_PATH), "verdict": verdict["verdict"]}, indent=2))


if __name__ == "__main__":
    main()
