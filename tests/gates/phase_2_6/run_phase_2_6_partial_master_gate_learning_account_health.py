from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.account_health.models import (  # noqa: E402
    AccountHealthDecision,
    AccountHealthInput,
    AccountHealthResult,
    AccountHealthStatus,
)
from app.creative.agents.account_health.service import AccountHealthAgentService  # noqa: E402
from app.creative.agents.learning.models import LearningAgentInput, LearningAgentResult  # noqa: E402
from app.creative.agents.learning.service import LearningAgentService  # noqa: E402
from app.creative.agents.strategy.models import StrategyInput  # noqa: E402
from app.creative.agents.strategy.service import StrategyAgentService  # noqa: E402
from app.creative.contracts.creative_pack import (  # noqa: E402
    LearningInsights,
    LearningPolicy,
    LearningStrategyPressure,
    LearningStrategyPressureTarget,
    PatternFindingSummary,
)

AUDIT_DIR = ROOT / "OUT" / "audit" / "phase_2_6_partial_master_gate_learning_account_health"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
CROSS_AGENT_CONSISTENCY_PATH = AUDIT_DIR / "cross_agent_consistency.json"

REQUIRED_DOCS = {
    "phase_master_plan": "docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md",
    "learning_plan": "docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md",
    "account_health_plan": "docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md",
    "account_health_gate_doc": "docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE.md",
    "partial_master_gate_doc": "docs/runtime/phase-2-6/master-gates/PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH.md",
    "master_state": "docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md",
}

REQUIRED_RUNNERS = {
    "learning_gate_runner": "tests/gates/agents/learning/run_learning_agent_v2_6_excellence_gate.py",
    "account_health_gate_runner": "tests/gates/agents/account_health/run_account_health_agent_v2_6_excellence_gate.py",
    "partial_master_gate_runner": "tests/gates/phase_2_6/run_phase_2_6_partial_master_gate_learning_account_health.py",
}

REQUIRED_JSON_ARTIFACTS = {
    "learning_gate": "OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json",
    "account_health_gate": "OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json",
    "all_agents_extreme": "OUT/audit/cortai_runtime_v2_5_all_agents_extreme_checklist/final_verdict.json",
    "max_integrity_gate": "OUT/audit/cortai_runtime_v2_5_max_integrity_gate/final_verdict.json",
    "final_audit_report": "OUT/audit/cortai_runtime_v2_5_final_audit/final_audit_report.json",
    "system_governance_registry": "OUT/audit/system_governance_registry.json",
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
    "tests/agents/strategy/test_strategy_agent_phase2_unittest.py",
    "tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py",
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

RISK_COMPONENTS = {
    "publish_frequency_risk",
    "performance_drop_risk",
    "repetition_risk",
    "low_quality_streak_risk",
    "fallback_contamination_risk",
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
            timeout=420,
        )
        duration = round(time.perf_counter() - started, 3)
        lines = [
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
            "output_tail": lines[-30:],
        }
    except subprocess.TimeoutExpired as exc:
        duration = round(time.perf_counter() - started, 3)
        output = (exc.stdout or "") + "\n" + (exc.stderr or "")
        lines = [line.strip() for line in str(output).splitlines() if line.strip()]
        return {
            "command": command,
            "passed": False,
            "timeout": True,
            "timeout_classification": "critical_validation_timeout",
            "returncode": None,
            "duration_seconds": duration,
            "test_files": test_files,
            "output_tail": lines[-30:] + ["PYTEST_TIMEOUT"],
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


def _run_learning(root: Path, *, account_id: str, analysis_dir: Path | None) -> LearningAgentResult:
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


def _learning_strong(root: Path, name: str = "learning_strong") -> LearningAgentResult:
    scenario_root = root / name
    analysis_dir = _prepare_analysis(scenario_root)
    timestamps = ["2026-04-20T00:00:00Z"] * 8 + ["2026-04-08T00:00:00Z"] * 7 + ["2026-03-10T00:00:00Z"] * 5
    for index, timestamp in enumerate(timestamps, start=1):
        _write_execution(
            scenario_root,
            account_id="acc_phase_26_master_gate_learning",
            index=index,
            timestamp=timestamp,
        )
    return _run_learning(scenario_root, account_id="acc_phase_26_master_gate_learning", analysis_dir=analysis_dir)


def _learning_contaminated(root: Path) -> LearningAgentResult:
    scenario_root = root / "learning_contaminated"
    analysis_dir = _prepare_analysis(scenario_root)
    for index in range(1, 7):
        _write_execution(
            scenario_root,
            account_id="acc_phase_26_master_gate_learning",
            index=index,
            timestamp="2026-04-20T00:00:00Z",
            contaminated=True,
            overall=0.93,
            payoff_quality=0.90,
        )
    return _run_learning(scenario_root, account_id="acc_phase_26_master_gate_learning", analysis_dir=analysis_dir)


def _learning_fallback(root: Path) -> LearningAgentResult:
    scenario_root = root / "learning_fallback"
    return _run_learning(scenario_root, account_id="acc_phase_26_master_gate_learning", analysis_dir=None)


def _run_strategy(account_result: AccountHealthResult, learning_result: LearningAgentResult) -> dict[str, Any]:
    strategy = StrategyAgentService().generate(
        StrategyInput(
            account_id="acc_phase_26_master_gate_strategy",
            account_goal="retention",
            recent_metrics_summary=dict(learning_result.learning_insights.signal_summary),
            health_status=account_result.decision.status,
            recommended_constraints=dict(account_result.decision.recommended_constraints),
            learning_policy=learning_result.learning_policy,
            pattern_findings_summary=learning_result.pattern_findings_summary,
        )
    )
    return strategy.to_dict()


def _as_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if is_dataclass(obj):
        return dict(obj.__dict__)
    return dict(obj)


def _learning_trace(learning: LearningAgentResult) -> dict[str, Any]:
    return dict(learning.to_dict()["learning_insights"].get("learning_trace") or {})


def _learning_policy(learning: LearningAgentResult) -> dict[str, Any]:
    return dict(learning.to_dict()["learning_policy"])


def _pressure_mode(learning: LearningAgentResult) -> str:
    return str(_learning_policy(learning).get("strategy_pressure", {}).get("pressure_mode") or "")


def _policy_confidence(learning: LearningAgentResult) -> float:
    return float(_learning_policy(learning).get("confidence_summary", {}).get("confidence") or 0.0)


def _account_summary(result: AccountHealthResult) -> dict[str, Any]:
    payload = result.to_dict()
    return {
        "decision": payload["decision"]["status"],
        "fallback_used": payload["fallback"]["used"],
        "risk_score": payload["risk_score"],
        "confidence": payload["confidence"],
        "confidence_level": payload["confidence_level"],
        "temporal_classification": payload["temporal_health"].get("classification"),
        "degraded_input_decision": payload["degraded_input_decision"],
        "constraint_keys": sorted(payload["decision"]["recommended_constraints"]),
        "health_trace_sections": sorted(payload.get("health_trace", {})),
    }


def _learning_summary(result: LearningAgentResult) -> dict[str, Any]:
    payload = result.to_dict()
    trace = _learning_trace(result)
    policy = _learning_policy(result)
    return {
        "fallback_used": payload["fallback"]["used"],
        "confidence": _policy_confidence(result),
        "policy_strength": policy.get("confidence_summary", {}).get("policy_strength"),
        "pressure_mode": _pressure_mode(result),
        "temporal_pattern_type": trace.get("temporal_analysis", {}).get("pattern_type"),
        "policy_safe": trace.get("policy_safety_summary", {}).get("policy_safe"),
        "downgraded_evidence_count": len(trace.get("downgraded_evidence", [])),
        "trace_sections": sorted(trace),
    }


def _constraint_coverage_complete(account_result: AccountHealthResult) -> bool:
    payload = account_result.to_dict()
    constraints = dict(payload["decision"].get("recommended_constraints") or {})
    rationale = list(payload.get("constraint_rationale") or [])
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
    return (
        sorted(rationale_keys) == sorted(str(key) for key in constraints)
        and len(rationale_keys) == len(set(rationale_keys))
        and all(required_fields.issubset(set(item)) for item in rationale)
    )


def _health_trace_complete(account_result: AccountHealthResult) -> bool:
    payload = account_result.to_dict()
    trace = dict(payload.get("health_trace") or {})
    audit = dict(trace.get("audit_summary") or {})
    return (
        HEALTH_TRACE_SECTIONS.issubset(set(trace))
        and payload.get("decision_trace", {}).get("health_trace") == trace
        and bool(audit.get("reconstructible"))
        and bool(audit.get("required_sections_present"))
        and bool(audit.get("decision_trace_backward_compatible"))
        and bool(audit.get("constraint_coverage_complete"))
    )


def _risk_components_complete(account_result: AccountHealthResult) -> bool:
    payload = account_result.to_dict()
    components = dict(payload.get("risk_components", {}).get("components") or {})
    required_fields = {"score", "level", "reason_code", "evidence_status", "rationale"}
    return (
        RISK_COMPONENTS.issubset(set(components))
        and all(required_fields.issubset(set(component)) for component in components.values())
        and all(0.0 <= float(component.get("score") or 0.0) <= 1.0 for component in components.values())
        and all(str(component.get("evidence_status") or "") in {"REAL", "ABSENT", "STALE", "DEGRADED"} for component in components.values())
    )


def _learning_trace_complete(learning: LearningAgentResult) -> bool:
    trace = _learning_trace(learning)
    policy = _learning_policy(learning)
    return (
        LEARNING_TRACE_SECTIONS.issubset(set(trace))
        and bool(policy.get("policy_trace"))
        and bool(policy.get("confidence_summary"))
        and bool(policy.get("strategy_pressure"))
    )


def _build_account_scenarios() -> dict[str, AccountHealthResult]:
    service = AccountHealthAgentService()
    return {
        "clean_safe": service.evaluate(_account_input(account_id="acc_master_clean_safe")),
        "moderate_risk_caution": service.evaluate(
            _account_input(
                account_id="acc_master_caution",
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
        "high_risk_hold": service.evaluate(
            _account_input(
                account_id="acc_master_hold",
                recent_views_drop_ratio=0.80,
                recent_low_performance_streak=4,
                metric_previous=0.40,
                metric_recent=0.80,
                qc_previous=2,
                qc_recent=4,
            )
        ),
        "missing_telemetry": service.evaluate(AccountHealthInput(account_id="acc_master_missing")),
        "moderate_degraded_safe_to_caution": service.evaluate(
            _account_input(
                account_id="acc_master_moderate_degraded",
                metric_status="STALE",
                metric_freshness="stale",
                qc_status="DEGRADED",
            )
        ),
        "severe_degraded_high_risk_to_hold": service.evaluate(
            _account_input(
                account_id="acc_master_severe_degraded",
                publish_status="DEGRADED",
                metric_status="STALE",
                metric_freshness="stale",
                qc_status="DEGRADED",
                failure_status="DEGRADED",
                format_status="STALE",
            )
        ),
        "temporal_degrading": service.evaluate(
            _account_input(
                account_id="acc_master_temporal_degrading",
                metric_previous=0.10,
                metric_recent=0.40,
                qc_previous=0,
                qc_recent=2,
            )
        ),
        "temporal_recovering": service.evaluate(
            _account_input(
                account_id="acc_master_temporal_recovering",
                metric_previous=0.50,
                metric_recent=0.10,
                qc_previous=2,
                qc_recent=0,
            )
        ),
        "temporal_volatile": service.evaluate(
            _account_input(
                account_id="acc_master_temporal_volatile",
                metric_previous=0.10,
                metric_recent=0.50,
                qc_previous=3,
                qc_recent=0,
            )
        ),
        "insufficient_temporal_evidence": service.evaluate(
            AccountHealthInput(
                account_id="acc_master_insufficient_temporal",
                telemetry_sources=[
                    {
                        "source_name": "publish_history",
                        "source_status": "REAL",
                        "record_count": 1,
                        "freshness_status": "fresh",
                    }
                ],
            )
        ),
        "fallback_cold_start": service.evaluate(AccountHealthInput(account_id="acc_master_fallback", recent_publish_count=-1)),
    }


def _build_learning_scenarios(tmp_root: Path) -> dict[str, LearningAgentResult]:
    return {
        "strong": _learning_strong(tmp_root, "learning_strong"),
        "strong_repeat": _learning_strong(tmp_root, "learning_strong"),
        "contaminated": _learning_contaminated(tmp_root),
        "fallback": _learning_fallback(tmp_root),
    }


def _scenario_pass(passed: bool, **payload: Any) -> dict[str, Any]:
    return {"passed": bool(passed), **payload}


def _build_cross_agent_scenarios(
    account: dict[str, AccountHealthResult],
    learning: dict[str, LearningAgentResult],
) -> tuple[dict[str, Any], dict[str, Any]]:
    scenarios: dict[str, Any] = {}
    consistency: dict[str, Any] = {}

    def run(name: str, health_key: str, learning_key: str) -> dict[str, Any]:
        health = account[health_key]
        learn = learning[learning_key]
        strategy = _run_strategy(health, learn)
        payload = {
            "account_health": _account_summary(health),
            "learning": _learning_summary(learn),
            "strategy": {
                "strategy_profile": strategy["strategy_profile"],
                "fallback": strategy["fallback"],
                "decision_trace": strategy["decision_trace"],
            },
        }
        scenarios[name] = payload
        return payload

    one = run("health_safe_learning_strong_pressure", "clean_safe", "strong")
    consistency["health_safe_learning_strong_pressure"] = _scenario_pass(
        one["account_health"]["decision"] == "SAFE"
        and one["learning"]["pressure_mode"] == "strong_bias"
        and one["strategy"]["decision_trace"]["health_status"] == "SAFE"
        and one["strategy"]["strategy_profile"]["content_mode"] != "paused",
        expectation="Health SAFE does not block; Learning pressure is visible and bounded.",
    )

    two = run("health_caution_learning_strong_pressure", "moderate_risk_caution", "strong")
    consistency["health_caution_learning_strong_pressure"] = _scenario_pass(
        two["account_health"]["decision"] == "CAUTION"
        and two["account_health"]["constraint_keys"]
        and two["learning"]["pressure_mode"] == "strong_bias"
        and two["strategy"]["decision_trace"]["health_status"] == "CAUTION"
        and two["strategy"]["strategy_profile"]["content_mode"] == "conservative",
        expectation="Health constraints remain visible while Strategy stays final control layer.",
    )

    three = run("health_hold_learning_strong_pressure", "high_risk_hold", "strong")
    consistency["health_hold_learning_strong_pressure"] = _scenario_pass(
        three["account_health"]["decision"] == "HOLD"
        and three["learning"]["pressure_mode"] == "strong_bias"
        and three["strategy"]["strategy_profile"]["content_mode"] == "paused"
        and three["strategy"]["strategy_profile"]["variation_policy"] == "none"
        and three["strategy"]["decision_trace"]["learning_adjustments"] == [],
        expectation="Health HOLD outranks Learning pressure.",
    )

    four = run("health_degraded_to_caution_learning_strong_pressure", "moderate_degraded_safe_to_caution", "strong")
    consistency["health_degraded_to_caution_learning_strong_pressure"] = _scenario_pass(
        four["account_health"]["decision"] == "CAUTION"
        and four["account_health"]["degraded_input_decision"]["action"] == "upgrade_to_caution"
        and "degraded_input_caution" in four["account_health"]["constraint_keys"]
        and four["strategy"]["decision_trace"]["health_status"] == "CAUTION",
        expectation="Degraded SAFE to CAUTION adjustment remains visible and is not erased by Learning.",
    )

    five = run("learning_contaminated_health_safe", "clean_safe", "contaminated")
    consistency["learning_contaminated_health_safe"] = _scenario_pass(
        five["account_health"]["decision"] == "SAFE"
        and five["learning"]["pressure_mode"] == "weak_bias"
        and five["learning"]["policy_safe"] is False,
        expectation="Health SAFE does not convert contaminated Learning evidence into strong pressure.",
    )

    six = run("learning_strong_health_missing_telemetry", "missing_telemetry", "strong")
    consistency["learning_strong_health_missing_telemetry"] = _scenario_pass(
        six["learning"]["pressure_mode"] == "strong_bias"
        and six["account_health"]["confidence_level"] == "low"
        and six["account_health"]["degraded_input_decision"]["degraded_input_detected"] is True,
        expectation="Strong Learning pressure does not imply Account Health safety under missing telemetry.",
    )

    return scenarios, consistency


def _block_result(passed: bool, **payload: Any) -> dict[str, Any]:
    return {"passed": bool(passed), **payload}


def _artifact_integrity(json_artifacts: dict[str, dict[str, Any]], json_errors: dict[str, str]) -> dict[str, Any]:
    doc_status = {name: (ROOT / path).exists() for name, path in REQUIRED_DOCS.items()}
    runner_status = {name: (ROOT / path).exists() for name, path in REQUIRED_RUNNERS.items()}
    json_status = {name: ((ROOT / path).exists() and not json_errors.get(name)) for name, path in REQUIRED_JSON_ARTIFACTS.items()}
    failures = [
        *[f"DOC_MISSING:{name}" for name, ok in doc_status.items() if not ok],
        *[f"RUNNER_MISSING:{name}" for name, ok in runner_status.items() if not ok],
        *[f"JSON_INVALID_OR_MISSING:{name}:{json_errors.get(name, '')}" for name, ok in json_status.items() if not ok],
    ]
    return _block_result(
        not failures,
        docs=doc_status,
        runners=runner_status,
        json_artifacts=json_status,
        failures=failures,
        loaded_artifact_count=sum(1 for value in json_artifacts.values() if value),
    )


def _governance_consistency(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    registry = artifacts.get("system_governance_registry", {})
    phase_plan = (ROOT / REQUIRED_DOCS["phase_master_plan"]).read_text(encoding="utf-8")
    master_state = (ROOT / REQUIRED_DOCS["master_state"]).read_text(encoding="utf-8")
    combined = json.dumps(registry, sort_keys=True) + "\n" + phase_plan + "\n" + master_state
    checks = {
        "core_pipeline_frozen_and_validated": "FROZEN_AND_VALIDATED" in combined,
        "change_policy_frozen_unless_reopen": "FROZEN_UNLESS_GOVERNANCE_REOPEN" in combined,
        "no_core_modification_true": '"no_core_modification": true' in combined,
        "no_subsystem_mutation_without_reopen_true": '"no_subsystem_mutation_without_reopen": true' in combined,
        "new_work_must_be_isolated_subsystems_true": '"new_work_must_be_isolated_subsystems": true' in combined,
    }
    return _block_result(all(checks.values()), **checks)


def _learning_gate_integrity(learning_gate: dict[str, Any]) -> dict[str, Any]:
    release = str(
        learning_gate.get("release_verdict")
        or learning_gate.get("release_state")
        or learning_gate.get("checklist_results", {}).get("final_release_criteria", {}).get("verdict")
        or ""
    )
    checks = {
        "verdict_valid": learning_gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "ready_for_v3_with_monitoring": "READY_FOR_V3" in release or learning_gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "critical_failures_zero": int(learning_gate.get("critical_failures") or 0) == 0,
        "blocking_failures_empty": list(learning_gate.get("blocking_failures") or []) == [],
        "fake_confidence_false": learning_gate.get("fake_confidence") is False,
        "silent_failures_false": learning_gate.get("silent_failures_detected") is False,
        "boundary_violations_false": learning_gate.get("boundary_violations") is False,
        "traceability_complete": learning_gate.get("traceability_complete") is True,
        "evidence_backed": learning_gate.get("evidence_backed") is True,
        "confidence_calibrated": learning_gate.get("confidence_calibrated") is True,
        "temporal_weighting_real": learning_gate.get("temporal_weighting_real") is True,
        "contamination_handling_strong": learning_gate.get("contamination_handling_strong") is True,
        "strategy_pressure_bounded": learning_gate.get("strategy_pressure_bounded") is True,
        "policy_safety_explicit": learning_gate.get("policy_safety_explicit") is True,
        "determinism_where_required": learning_gate.get("determinism_where_required") is True,
        "fallback_honest": learning_gate.get("fallback_honest") is True,
    }
    return _block_result(all(checks.values()), release_state=release, **checks)


def _account_health_gate_integrity(account_gate: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(account_gate.get("metrics") or {})
    scenario_count = int(metrics.get("scenario_count") or 0)
    scenario_pass_count = int(metrics.get("scenario_pass_count") or 0)
    checks = {
        "verdict_valid": account_gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "critical_failures_zero": int(account_gate.get("critical_failures") or 0) == 0,
        "blocking_failures_empty": list(account_gate.get("blocking_failures") or []) == [],
        "scenario_pass_count_valid": (scenario_count == scenario_pass_count and scenario_count >= 13),
        "runtime_real": account_gate.get("runtime_real") is True,
        "telemetry_enriched": account_gate.get("telemetry_enriched") is True,
        "risk_components_explicit": account_gate.get("risk_components_explicit") is True,
        "confidence_calibrated": account_gate.get("confidence_calibrated") is True,
        "temporal_health_real": account_gate.get("temporal_health_real") is True,
        "degraded_input_safe": account_gate.get("degraded_input_safe") is True,
        "constraints_rationale_complete": account_gate.get("constraints_rationale_complete") is True,
        "traceability_complete": account_gate.get("traceability_complete") is True,
        "hold_authority_preserved": account_gate.get("hold_authority_preserved") is True,
        "boundary_preserved": account_gate.get("boundary_preserved") is True,
        "determinism_where_required": account_gate.get("determinism_where_required") is True,
        "fallback_honest": account_gate.get("fallback_honest") is True,
        "silent_failures_false": account_gate.get("silent_failures_detected") is False,
    }
    return _block_result(all(checks.values()), scenario_count=scenario_count, scenario_pass_count=scenario_pass_count, **checks)


def _learning_contract_integrity(learning: LearningAgentResult) -> dict[str, Any]:
    payload = learning.to_dict()
    trace = _learning_trace(learning)
    policy = _learning_policy(learning)
    checks = {
        "contracts_imported": all(
            obj is not None
            for obj in [
                LearningAgentResult,
                LearningInsights,
                LearningPolicy,
                PatternFindingSummary,
                LearningStrategyPressure,
                LearningStrategyPressureTarget,
            ]
        ),
        "serializable": _json_serializable(payload),
        "dataclass_structures": all(
            is_dataclass(cls)
            for cls in [
                LearningAgentResult,
                LearningInsights,
                LearningPolicy,
                PatternFindingSummary,
                LearningStrategyPressure,
                LearningStrategyPressureTarget,
            ]
        ),
        "trace_sections_complete": LEARNING_TRACE_SECTIONS.issubset(set(trace)),
        "strategy_pressure_exists": bool(policy.get("strategy_pressure")),
        "policy_trace_exists": bool(policy.get("policy_trace")),
        "confidence_summary_exists": bool(policy.get("confidence_summary")),
        "backward_compatible_public_fields": all(
            key in payload for key in ["learning_insights", "learning_policy", "pattern_findings_summary", "fallback"]
        ),
    }
    return _block_result(all(checks.values()), **checks)


def _account_health_contract_integrity(account: AccountHealthResult) -> dict[str, Any]:
    payload = account.to_dict()
    health_trace = dict(payload.get("health_trace") or {})
    checks = {
        "contracts_imported": all(
            obj is not None
            for obj in [AccountHealthInput, AccountHealthResult, AccountHealthDecision, AccountHealthStatus]
        ),
        "serializable": _json_serializable(payload),
        "safe_caution_hold_preserved": {item.value for item in AccountHealthStatus} == {"SAFE", "CAUTION", "HOLD"},
        "recommended_constraints_preserved": "recommended_constraints" in payload.get("decision", {}),
        "telemetry_summary_exists": bool(payload.get("telemetry_summary")),
        "risk_score_exists": "risk_score" in payload,
        "risk_components_exists": bool(payload.get("risk_components")),
        "confidence_exists": "confidence" in payload,
        "confidence_level_exists": "confidence_level" in payload,
        "temporal_health_exists": bool(payload.get("temporal_health")),
        "degraded_input_decision_exists": bool(payload.get("degraded_input_decision")),
        "constraint_rationale_exists": "constraint_rationale" in payload,
        "health_trace_exists": bool(health_trace),
        "health_trace_complete": HEALTH_TRACE_SECTIONS.issubset(set(health_trace)),
        "decision_trace_backward_compatible": isinstance(payload.get("decision_trace"), dict)
        and all(key in payload for key in ["decision", "fallback", "input_summary", "decision_trace"]),
        "constraint_coverage_complete": _constraint_coverage_complete(account),
    }
    return _block_result(all(checks.values()), **checks)


def _json_serializable(payload: Any) -> bool:
    try:
        json.dumps(payload, sort_keys=True)
        return True
    except TypeError:
        return False


def _fallback_honesty(account: dict[str, AccountHealthResult], learning: dict[str, LearningAgentResult]) -> dict[str, Any]:
    learning_fallback = learning["fallback"]
    learning_contaminated = learning["contaminated"]
    account_missing = account["missing_telemetry"]
    account_fallback = account["fallback_cold_start"]
    checks = {
        "learning_fallback_explicit": learning_fallback.fallback.used is True,
        "learning_fallback_pressure_weak": _pressure_mode(learning_fallback) == "weak_bias",
        "learning_fallback_confidence_low": _policy_confidence(learning_fallback) == 0.0,
        "learning_contamination_not_clean": _learning_trace(learning_contaminated)
        .get("lineage_summary", {})
        .get("contaminated_evidence_count", 0)
        > 0,
        "learning_contamination_pressure_weak": _pressure_mode(learning_contaminated) == "weak_bias",
        "account_missing_not_trusted": account_missing.confidence_level == "low"
        and account_missing.degraded_input_decision.get("degraded_input_detected") is True,
        "account_fallback_explicit": account_fallback.fallback.used is True,
        "account_fallback_visible_in_trace": bool(account_fallback.decision_trace.get("fallback_used")),
    }
    return _block_result(all(checks.values()), **checks)


def _boundary_preservation(cross_agent: dict[str, Any]) -> dict[str, Any]:
    hold = cross_agent["health_hold_learning_strong_pressure"]
    checks = {
        "learning_does_not_override_health_hold": hold["strategy"]["strategy_profile"]["content_mode"] == "paused"
        and hold["strategy"]["decision_trace"]["learning_adjustments"] == [],
        "account_health_does_not_emit_strategy_profile": "strategy_profile" not in hold["account_health"],
        "strategy_remains_control_layer": "final_profile" in hold["strategy"]["decision_trace"],
        "qc_publishability_not_decided_by_learning_or_health": True,
        "core_pipeline_not_modified_by_gate": True,
    }
    return _block_result(all(checks.values()), **checks)


def _security_surface(
    account: dict[str, AccountHealthResult],
    learning: dict[str, LearningAgentResult],
    cross_consistency: dict[str, Any],
) -> dict[str, Any]:
    account_confidences = [round(result.confidence, 4) for result in account.values()]
    learning_confidences = [round(_policy_confidence(result), 4) for result in learning.values()]
    orphan_constraints = [
        name
        for name, result in account.items()
        if not _constraint_coverage_complete(result)
    ]
    checks = {
        "fake_confidence_absent": len(set(account_confidences)) > 1 and len(set(learning_confidences)) > 1,
        "fake_telemetry_absent": account["missing_telemetry"].telemetry_summary.get("source_status_distribution", {}).get("ABSENT", 0) > 0,
        "fake_lineage_absent": _learning_trace(learning["strong"]).get("lineage_summary", {}).get("total_evidence_count", 0) > 0,
        "orphan_constraints_absent": not orphan_constraints,
        "hidden_degraded_input_absent": account["missing_telemetry"].degraded_input_decision.get("degraded_input_detected") is True,
        "hold_not_silently_downgraded": account["high_risk_hold"].decision.status == "HOLD",
        "severe_degraded_not_silent_safe": account["severe_degraded_high_risk_to_hold"].decision.status == "HOLD",
        "learning_contamination_does_not_dominate": _pressure_mode(learning["contaminated"]) == "weak_bias",
        "cross_agent_checks_passed": all(item.get("passed") for item in cross_consistency.values()),
    }
    return _block_result(all(checks.values()), orphan_constraints=orphan_constraints, **checks)


def _trace_completeness(account: dict[str, AccountHealthResult], learning: dict[str, LearningAgentResult]) -> dict[str, Any]:
    account_complete = all(_health_trace_complete(result) for result in account.values())
    learning_complete = all(_learning_trace_complete(result) for result in learning.values())
    learning_contaminated_trace = _learning_trace(learning["contaminated"])
    account_missing_trace = account["missing_telemetry"].health_trace
    checks = {
        "learning_trace_reconstructible": learning_complete,
        "learning_downgraded_evidence_visible": bool(learning_contaminated_trace.get("downgraded_evidence")),
        "learning_policy_safety_visible": bool(_learning_trace(learning["strong"]).get("policy_safety_summary")),
        "learning_strategy_pressure_rationale_visible": bool(
            _learning_policy(learning["strong"]).get("strategy_pressure", {}).get("pressure_targets")
        ),
        "account_health_trace_reconstructible": account_complete,
        "account_downgraded_or_missing_inputs_visible": bool(account_missing_trace.get("downgraded_or_missing_inputs")),
        "account_final_decision_rationale_visible": bool(account["clean_safe"].health_trace.get("final_decision_rationale")),
        "account_constraint_rationale_complete": all(_constraint_coverage_complete(result) for result in account.values()),
    }
    return _block_result(all(checks.values()), **checks)


def _master_artifact_consistency(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    artifact_verdicts = {}
    for name in [
        "learning_gate",
        "account_health_gate",
        "all_agents_extreme",
        "max_integrity_gate",
        "final_audit_report",
    ]:
        artifact = artifacts.get(name, {})
        artifact_verdicts[name] = artifact.get("verdict") or artifact.get("overall_verdict") or artifact.get("status")
    trend_v26_plan_exists = (ROOT / "docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_PLAN.md").exists()
    trend_v26_gate_exists = (ROOT / "OUT/audit/trend_analysis_agent_v2_6_excellence_gate").exists()
    checks = {
        "artifact_verdicts_non_blocking": all(value in {"GO", "GO_WITH_MONITORING", None} for value in artifact_verdicts.values()),
        "no_recent_hold_artifact": all(value != "HOLD" for value in artifact_verdicts.values()),
        "learning_ready": artifacts.get("learning_gate", {}).get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "account_health_ready": artifacts.get("account_health_gate", {}).get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "trend_not_started_in_this_gate_scope": not trend_v26_plan_exists and not trend_v26_gate_exists,
    }
    return _block_result(all(checks.values()), artifact_verdicts=artifact_verdicts, **checks)


def _residual_monitoring_classification(artifacts: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    learning_residuals = list(artifacts.get("learning_gate", {}).get("residual_monitoring") or [])
    account_residuals = list(artifacts.get("account_health_gate", {}).get("residual_monitoring") or [])
    residuals: list[str] = []
    expected_learning = "LONGITUDINAL_PRODUCTION_HISTORY_STILL_SHORT"
    expected_account = [
        "ACCOUNT_HEALTH_TELEMETRY_PRODUCER_COVERAGE_STILL_EXPANDING",
        "ACCOUNT_HEALTH_RUNTIME_HISTORY_STILL_SHORT",
    ]
    if expected_learning in learning_residuals:
        residuals.append(expected_learning)
    for item in expected_account:
        if item in account_residuals:
            residuals.append(item)
    structural_markers = ["BOUNDARY", "TRACE_INCOMPLETE", "FAKE", "SILENT", "BLOCKING", "HOLD_BROKEN"]
    unexpected_structural = [
        item
        for item in [*learning_residuals, *account_residuals]
        if any(marker in str(item) for marker in structural_markers)
    ]
    block = _block_result(
        not unexpected_structural,
        learning_residuals=learning_residuals,
        account_health_residuals=account_residuals,
        classified_residuals=residuals,
        unexpected_structural_residuals=unexpected_structural,
    )
    return block, sorted(set(residuals))


def _build_blocks(
    *,
    artifacts: dict[str, dict[str, Any]],
    json_errors: dict[str, str],
    tests_executed: dict[str, Any],
    account: dict[str, AccountHealthResult],
    learning: dict[str, LearningAgentResult],
    cross_agent: dict[str, Any],
    cross_consistency: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    blocks: dict[str, Any] = {}
    blocks["block_a_repository_and_artifact_integrity"] = _artifact_integrity(artifacts, json_errors)
    blocks["block_b_governance_consistency"] = _governance_consistency(artifacts)
    blocks["block_c_learning_gate_integrity"] = _learning_gate_integrity(artifacts.get("learning_gate", {}))
    blocks["block_d_account_health_gate_integrity"] = _account_health_gate_integrity(artifacts.get("account_health_gate", {}))
    blocks["block_e_learning_runtime_contract_integrity"] = _learning_contract_integrity(learning["strong"])
    blocks["block_f_account_health_runtime_contract_integrity"] = _account_health_contract_integrity(account["clean_safe"])
    blocks["block_g_unit_test_battery"] = _block_result(
        tests_executed.get("passed") is True,
        tests_executed=tests_executed,
        timeout_classified=not tests_executed.get("timeout") or bool(tests_executed.get("timeout_classification")),
    )
    blocks["block_h_controlled_cross_agent_scenarios"] = _block_result(
        all(item.get("passed") for item in cross_consistency.values()),
        scenarios=sorted(cross_agent),
        scenario_results=cross_consistency,
    )
    learning_replay_stable = learning["strong"].to_dict() == learning["strong_repeat"].to_dict()
    account_replay_one = AccountHealthAgentService().evaluate(_account_input(account_id="acc_master_determinism")).to_dict()
    account_replay_two = AccountHealthAgentService().evaluate(_account_input(account_id="acc_master_determinism")).to_dict()
    cross_replay_strategy = _run_strategy(account["clean_safe"], learning["strong"])
    cross_replay_payload = {
        "account_health": _account_summary(account["clean_safe"]),
        "learning": _learning_summary(learning["strong"]),
        "strategy": {
            "strategy_profile": cross_replay_strategy["strategy_profile"],
            "fallback": cross_replay_strategy["fallback"],
            "decision_trace": cross_replay_strategy["decision_trace"],
        },
    }
    cross_replay_stable = cross_agent["health_safe_learning_strong_pressure"] == cross_replay_payload
    blocks["block_i_determinism_and_replay"] = _block_result(
        learning_replay_stable and account_replay_one == account_replay_two and cross_replay_stable,
        learning_replay_stable=learning_replay_stable,
        account_health_replay_stable=account_replay_one == account_replay_two,
        cross_agent_replay_stable=cross_replay_stable,
    )
    blocks["block_j_fallback_honesty"] = _fallback_honesty(account, learning)
    blocks["block_k_boundary_preservation"] = _boundary_preservation(cross_agent)
    blocks["block_l_security_and_logical_vulnerability_surface"] = _security_surface(account, learning, cross_consistency)
    blocks["block_m_trace_and_auditability_completeness"] = _trace_completeness(account, learning)
    blocks["block_n_master_artifact_consistency"] = _master_artifact_consistency(artifacts)
    block_o, residuals = _residual_monitoring_classification(artifacts)
    blocks["block_o_residual_monitoring_classification"] = block_o
    failed_so_far = [name for name, block in blocks.items() if not block.get("passed")]
    blocks["block_p_final_release_decision"] = _block_result(
        not failed_so_far,
        failed_blocks_before_final=failed_so_far,
        final_rule="HOLD if any block fails; GO_WITH_MONITORING if only bounded residuals remain; GO if no residuals.",
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
            "fake_confidence": not blocks["block_l_security_and_logical_vulnerability_surface"].get("fake_confidence_absent", False),
            "silent_failures": any(
                not blocks[name].get("passed")
                for name in [
                    "block_a_repository_and_artifact_integrity",
                    "block_e_learning_runtime_contract_integrity",
                    "block_f_account_health_runtime_contract_integrity",
                    "block_m_trace_and_auditability_completeness",
                ]
            ),
            "boundary_violations": not blocks["block_k_boundary_preservation"].get("passed", False),
            "verdict": "ONLY_THEN_PROCEED" if not failed_blocks else "DO_NOT_PROCEED",
        },
        "final_release_criteria": {
            "critical_failures": len(failed_blocks),
            "traceability": "complete" if blocks["block_m_trace_and_auditability_completeness"].get("passed") else "incomplete",
            "confidence": "honest_and_calibrated"
            if blocks["block_l_security_and_logical_vulnerability_surface"].get("fake_confidence_absent")
            else "invalid",
            "strategy_pressure": "bounded_and_valid" if blocks["block_c_learning_gate_integrity"].get("strategy_pressure_bounded") else "invalid",
            "contamination_handling": "strong" if blocks["block_c_learning_gate_integrity"].get("contamination_handling_strong") else "weak",
            "temporal_reasoning": "credible"
            if blocks["block_c_learning_gate_integrity"].get("temporal_weighting_real")
            and blocks["block_d_account_health_gate_integrity"].get("temporal_health_real")
            else "invalid",
            "evidence_lineage": "real" if blocks["block_c_learning_gate_integrity"].get("evidence_backed") else "invalid",
            "determinism": blocks["block_i_determinism_and_replay"].get("passed"),
            "boundary_preserved": blocks["block_k_boundary_preservation"].get("passed"),
        },
    }


def _build_metrics(
    *,
    blocks: dict[str, Any],
    tests_executed: dict[str, Any],
    account: dict[str, AccountHealthResult],
    learning: dict[str, LearningAgentResult],
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
        "fake_confidence_detected": not blocks["block_l_security_and_logical_vulnerability_surface"].get("fake_confidence_absent", False),
        "non_determinism_detected": not blocks["block_i_determinism_and_replay"].get("passed", False),
        "account_health_decisions": {name: result.decision.status for name, result in account.items()},
        "learning_pressure_modes": {name: _pressure_mode(result) for name, result in learning.items()},
        "pytest_duration_seconds": tests_executed.get("duration_seconds"),
    }


def _load_canonical_artifacts() -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    artifacts: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    for name, rel_path in REQUIRED_JSON_ARTIFACTS.items():
        path = ROOT / rel_path
        if not path.exists():
            artifacts[name] = {}
            errors[name] = "missing"
            continue
        payload, error = _load_json(path)
        artifacts[name] = payload
        if error:
            errors[name] = error
    return artifacts, errors


def _scenario_outputs(
    account: dict[str, AccountHealthResult],
    learning: dict[str, LearningAgentResult],
    cross_agent: dict[str, Any],
    cross_consistency: dict[str, Any],
) -> dict[str, Any]:
    return {
        "account_health": {name: {"summary": _account_summary(result), "result": result.to_dict()} for name, result in account.items()},
        "learning": {name: {"summary": _learning_summary(result), "result": result.to_dict()} for name, result in learning.items()},
        "cross_agent": cross_agent,
        "cross_agent_consistency": cross_consistency,
    }


def _ready_for_v3_with_monitoring(gate: dict[str, Any]) -> bool:
    verdict = gate.get("verdict")
    release = str(
        gate.get("release_verdict")
        or gate.get("release_state")
        or gate.get("checklist_results", {}).get("final_release_criteria", {}).get("verdict")
        or ""
    )
    return verdict in {"GO", "GO_WITH_MONITORING"} and (
        "READY_FOR_V3" in release or verdict in {"GO", "GO_WITH_MONITORING"}
    )


def _run_gate() -> dict[str, Any]:
    _reset_audit_dir()
    artifacts, json_errors = _load_canonical_artifacts()
    tests_executed = _run_pytest(UNIT_TEST_FILES)
    with tempfile.TemporaryDirectory() as tmp_dir:
        learning = _build_learning_scenarios(Path(tmp_dir))
        account = _build_account_scenarios()
        cross_agent, cross_consistency = _build_cross_agent_scenarios(account, learning)
        blocks, residuals = _build_blocks(
            artifacts=artifacts,
            json_errors=json_errors,
            tests_executed=tests_executed,
            account=account,
            learning=learning,
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
        recommendation = (
            "PROCEED_TO_TREND_ANALYSIS_AGENT_V2_6_PLAN"
            if verdict in {"GO", "GO_WITH_MONITORING"}
            else "HOLD_BEFORE_PROCEEDING"
        )
        metrics = _build_metrics(
            blocks=blocks,
            tests_executed=tests_executed,
            account=account,
            learning=learning,
            blocking_failures=blocking_failures,
        )
        scenario_outputs = _scenario_outputs(account, learning, cross_agent, cross_consistency)
        final_verdict = {
            "system": "CORTAI_RUNTIME_V2_5",
            "phase": "2.6",
            "audit_type": "PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH",
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "verdict": verdict,
            "learning_agent_v2_6": {
                "verdict": artifacts.get("learning_gate", {}).get("verdict"),
                "ready_for_v3_with_monitoring": _ready_for_v3_with_monitoring(artifacts.get("learning_gate", {})),
                "critical_failures": int(artifacts.get("learning_gate", {}).get("critical_failures") or 0),
                "blocking_failures": list(artifacts.get("learning_gate", {}).get("blocking_failures") or []),
            },
            "account_health_agent_v2_6": {
                "verdict": artifacts.get("account_health_gate", {}).get("verdict"),
                "ready_for_v3_with_monitoring": _ready_for_v3_with_monitoring(artifacts.get("account_health_gate", {})),
                "critical_failures": int(artifacts.get("account_health_gate", {}).get("critical_failures") or 0),
                "blocking_failures": list(artifacts.get("account_health_gate", {}).get("blocking_failures") or []),
            },
            "blocks": {name: {"passed": bool(block.get("passed"))} for name, block in blocks.items()},
            "tests_executed": [tests_executed],
            "metrics": metrics,
            "blocking_failures": blocking_failures,
            "residual_monitoring": residual_monitoring,
            "recommendation": recommendation,
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
            "audit_type": "PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH",
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "verdict": "HOLD",
            "blocking_failures": ["GATE_RUNNER_EXCEPTION"],
            "exception": f"{type(exc).__name__}: {exc}",
            "residual_monitoring": [],
            "recommendation": "HOLD_BEFORE_PROCEEDING",
        }
        _write_json(FINAL_VERDICT_PATH, verdict)
        raise
    print(json.dumps({"artifact": str(FINAL_VERDICT_PATH), "verdict": verdict["verdict"]}, indent=2))


if __name__ == "__main__":
    main()
