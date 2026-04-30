from __future__ import annotations

import importlib
import importlib.util
import inspect
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

AUDIT_DIR = ROOT / "OUT" / "audit" / "cortai_absolute_master_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
CROSS_AGENT_CONSISTENCY_PATH = AUDIT_DIR / "cross_agent_consistency.json"
CONTRACT_INTEGRITY_PATH = AUDIT_DIR / "contract_integrity.json"

REQUIRED_DOCS = {
    "absolute_gate_doc": "docs/runtime/phase-2-6/master-gates/CORTAI_ABSOLUTE_MASTER_GATE_PRE_WAVE_2.md",
    "architecture_bible": "docs/runtime/architecture/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md",
    "runtime_master_state": "docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md",
    "phase_2_6_master_plan": "docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md",
    "wave_1_master_gate_doc": "docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_1_MASTER_GATE.md",
    "learning_plan": "docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md",
    "account_health_plan": "docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md",
    "trend_plan": "docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_PLAN.md",
}

REQUIRED_RUNNERS = {
    "absolute_gate_runner": "tests/gates/phase_2_6/run_cortai_absolute_master_gate.py",
    "wave_1_master_gate_runner": "tests/gates/phase_2_6/run_phase_2_6_wave_1_master_gate.py",
    "learning_gate_runner": "tests/gates/agents/learning/run_learning_agent_v2_6_excellence_gate.py",
    "account_health_gate_runner": "tests/gates/agents/account_health/run_account_health_agent_v2_6_excellence_gate.py",
    "trend_gate_runner": "tests/gates/agents/trend_analysis/run_trend_analysis_agent_v2_6_excellence_gate.py",
    "all_agents_extreme_runner": "tests/gates/system/run_cortai_runtime_v2_5_all_agents_extreme_checklist.py",
    "max_integrity_runner": "tests/gates/system/run_cortai_runtime_v2_5_max_integrity_gate.py",
    "final_audit_runner": "tests/gates/system/run_cortai_runtime_v2_5_final_audit.py",
}

REQUIRED_JSON_ARTIFACTS = {
    "learning_gate": "OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json",
    "account_health_gate": "OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json",
    "trend_gate": "OUT/audit/trend_analysis_agent_v2_6_excellence_gate/final_verdict.json",
    "partial_master_gate": "OUT/audit/phase_2_6_partial_master_gate_learning_account_health/final_verdict.json",
    "wave_1_master_gate": "OUT/audit/phase_2_6_wave_1_master_gate/final_verdict.json",
    "system_governance_registry": "OUT/audit/system_governance_registry.json",
    "all_agents_extreme": "OUT/audit/cortai_runtime_v2_5_all_agents_extreme_checklist/final_verdict.json",
    "max_integrity_gate": "OUT/audit/cortai_runtime_v2_5_max_integrity_gate/final_verdict.json",
    "final_audit_report": "OUT/audit/cortai_runtime_v2_5_final_audit/final_audit_report.json",
}

OPTIONAL_JSON_ARTIFACTS = {
    "pipeline_total_heavy_audit": "OUT/audit/pipeline_total_heavy_audit/final_verdict.json",
    "pipeline_full_master_certification": "OUT/audit/pipeline_full_master_certification/final_verdict.json",
    "pipeline_v2_full_system_validation": "OUT/audit/pipeline_v2_full_system_validation_gate/final_verdict.json",
    "script_voice_asset_gate": "OUT/audit/script_voice_asset_full_validation_gate/final_verdict.json",
    "strategy_full_gate": "OUT/audit/strategy_agent_full_validation_gate/final_verdict.json",
    "asset_full_gate": "OUT/audit/asset_agent_full_validation_gate/final_verdict.json",
    "editor_full_gate": "OUT/audit/editor_agent_full_validation_gate/final_verdict.json",
    "qc_full_gate": "OUT/audit/qc_agent_full_validation_gate/final_verdict.json",
    "experiment_governance": "OUT/audit/experiment_capability_v2_0_governance_decision/final_verdict.json",
    "content_attribution_governance": "OUT/audit/content_performance_attribution_v2_0_governance_decision/final_verdict.json",
    "novelty_full_gate": "OUT/audit/saturation_novelty_engine_full_validation_gate/final_verdict.json",
    "manual_batch10_post_fix": "OUT/audit/manual_batch10_post_fix_validation/final_verdict.json",
}

TEST_BATTERY = [
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
    "tests/agents/strategy/test_strategy_agent_evolution_v2_0_integration_unittest.py",
    "tests/agents/strategy/test_strategy_learning_d9_unittest.py",
    "tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py",
    "tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py",
    "tests/agents/asset_selection/test_asset_plan_runtime_integration_unittest.py",
    "tests/experiment/test_experiment_capability_phase2_unittest.py",
    "tests/attribution/test_content_attribution_phase_d_bounded_integration_unittest.py",
    "tests/content/test_content_pipeline_d27_unittest.py",
    "tests/agents/novelty/test_novelty_engine_unittest.py",
    "tests/agents/script/test_script_generation_unittest.py",
    "tests/agents/script/test_script_agent_phase2_unittest.py",
    "tests/agents/voice/test_voice_agent_phase2_unittest.py",
    "tests/agents/voice/test_voice_agent_service_phase2_5_unittest.py",
    "tests/agents/voice/test_voice_interpreter_phase2_5_unittest.py",
    "tests/agents/voice/test_tts_router_phase2_5_unittest.py",
    "tests/agents/voice/test_tts_router_kokoro_phase2_5b_unittest.py",
    "tests/agents/voice/test_kokoro_adapter_phase2_5b_unittest.py",
    "tests/agents/voice/test_kokoro_fallback_phase2_5b_unittest.py",
    "tests/agents/editor/test_editor_agent_service_unittest.py",
    "tests/agents/editor/test_editor_interpreter_unittest.py",
    "tests/agents/editor/test_editor_plan_unittest.py",
    "tests/agents/video_qc/test_video_qc_agent_phase2_unittest.py",
    "tests/runtime/pipeline/test_phase2_block1_smoke_unittest.py",
    "tests/runtime/pipeline/test_phase2_block2_smoke_unittest.py",
    "tests/runtime/pipeline/test_phase2_block3_smoke_unittest.py",
    "tests/runtime/pipeline/test_phase2_block4_smoke_unittest.py",
]

CONTRACT_SYMBOLS = [
    ("app.creative.agents.account_health.models", "AccountHealthInput"),
    ("app.creative.agents.account_health.models", "AccountHealthResult"),
    ("app.creative.agents.trend_analysis.models", "TrendAnalysisInput"),
    ("app.creative.agents.trend_analysis.models", "TrendAnalysisResult"),
    ("app.creative.agents.learning.models", "LearningAgentInput"),
    ("app.creative.agents.learning.models", "LearningAgentResult"),
    ("app.creative.agents.strategy.models", "StrategyInput"),
    ("app.creative.agents.strategy.models", "StrategyResult"),
    ("app.creative.experiments.models", "ExperimentCapabilityResult"),
    ("app.creative.agents.asset_selection.models", "AssetSelectionResult"),
    ("app.creative.agents.novelty.models", "NoveltyResult"),
    ("app.creative.agents.video_qc.models", "VideoQcResult"),
    ("app.creative.contracts.creative_pack", "CreativePack"),
    ("app.creative.contracts.creative_pack", "StrategyProfile"),
    ("app.creative.contracts.creative_pack", "TrendProfile"),
    ("app.creative.contracts.creative_pack", "LearningInsights"),
    ("app.creative.contracts.creative_pack", "ExperimentPlan"),
    ("app.creative.contracts.creative_pack", "ScriptPlan"),
    ("app.creative.contracts.creative_pack", "VoicePlan"),
    ("app.creative.contracts.creative_pack", "AssetPlan"),
]

STRUCTURAL_RESIDUAL_MARKERS = [
    "BOUNDARY",
    "TRACE_INCOMPLETE",
    "FAKE",
    "SILENT",
    "BLOCKING",
    "HOLD_BROKEN",
    "UNAUTHORIZED",
    "CORE_MUTATION",
    "STRATEGY_OWNERSHIP_LOST",
    "ORPHAN_CONSTRAINT",
]

MONITORABLE_RESIDUAL_MARKERS = [
    "HISTORY_STILL_SHORT",
    "RUNTIME_HISTORY_STILL_SHORT",
    "PRODUCER_COVERAGE_STILL_EXPANDING",
    "PRODUCER_COVERAGE_STILL_BOUNDED",
    "LONGITUDINAL",
    "PRODUCTION_HISTORY",
    "PRODUCTION_MATURITY",
    "REAL_VARIABILITY_MONITORING",
    "CONTROLLED_SCENARIO_GATE",
    "CONTROLLED_VALIDATION",
    "SOURCE_DIVERSITY_STILL_EXPANDING",
    "PUBLIC_SURFACE_LIMITATION",
    "MONITORING_REQUIRED",
    "REQUIRES_MONITORING",
    "REQUIRES_REFRESH",
    "UNDER_MONITORING",
    "BATCH_BOOTSTRAP_EFFECT_PRESENT",
    "INSUFFICIENT_INPUT",
    "RUNTIME_HISTORY",
    "REAL_PRODUCTION_VARIETY",
    "TELEMETRY_RICHNESS_STILL_LIMITED",
    "MANUAL_FLOW_REQUIRES_POST_PUBLISH_WINDOW_METRICS",
]


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        return json.loads(_read_text(path)), ""
    except Exception as exc:  # noqa: BLE001
        return {}, f"{type(exc).__name__}: {exc}"


def _gate_allows(verdict: Any) -> bool:
    return str(verdict or "").upper() in {"GO", "GO_WITH_MONITORING", "GO_WITH_EXCEPTIONS"}


def _block(passed: bool, **payload: Any) -> dict[str, Any]:
    return {"passed": bool(passed), **payload}


def _load_artifacts() -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, bool]]:
    artifacts: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    existence: dict[str, bool] = {}
    for name, rel_path in {**REQUIRED_JSON_ARTIFACTS, **OPTIONAL_JSON_ARTIFACTS}.items():
        path = ROOT / rel_path
        existence[name] = path.exists()
        if not path.exists():
            artifacts[name] = {}
            if name in REQUIRED_JSON_ARTIFACTS:
                errors[name] = "missing"
            continue
        payload, error = _load_json(path)
        artifacts[name] = payload
        if error:
            errors[name] = error
    return artifacts, errors, existence


def _run_pytest(test_files: list[str]) -> dict[str, Any]:
    existing = [test_file for test_file in test_files if (ROOT / test_file).exists()]
    missing = [test_file for test_file in test_files if not (ROOT / test_file).exists()]
    command = [sys.executable, "-m", "pytest", "-q", *existing]
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
            timeout=1800,
        )
        duration = round(time.perf_counter() - started, 3)
        output_lines = [
            line.strip()
            for line in (completed.stdout + "\n" + completed.stderr).splitlines()
            if line.strip()
        ]
        return {
            "command": command,
            "passed": completed.returncode == 0 and not missing,
            "timeout": False,
            "returncode": completed.returncode,
            "duration_seconds": duration,
            "test_files": existing,
            "missing_test_files": missing,
            "output_tail": output_lines[-40:],
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
            "test_files": existing,
            "missing_test_files": missing,
            "output_tail": output_lines[-40:] + ["PYTEST_TIMEOUT"],
        }


def _load_wave1_module() -> Any:
    path = ROOT / "tests" / "run_phase_2_6_wave_1_master_gate.py"
    spec = importlib.util.spec_from_file_location("phase_2_6_wave_1_master_gate_runtime", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Wave 1 master gate helper module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return value
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}


def _json_serializable(value: Any) -> bool:
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
        return True
    except TypeError:
        return False


def _learning_trace(result: Any) -> dict[str, Any]:
    return dict(_to_dict(result).get("learning_insights", {}).get("learning_trace") or {})


def _learning_policy(result: Any) -> dict[str, Any]:
    return dict(_to_dict(result).get("learning_policy") or {})


def _policy_confidence(result: Any) -> float:
    return float(_learning_policy(result).get("confidence_summary", {}).get("confidence") or 0.0)


def _pressure_mode(result: Any) -> str:
    return str(_learning_policy(result).get("strategy_pressure", {}).get("pressure_mode") or "")


def _contract_entry(module_name: str, symbol_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        symbol = getattr(module, symbol_name)
        required_fields: list[str] = []
        optional_fields: list[str] = []
        if inspect.isclass(symbol):
            signature = inspect.signature(symbol)
            for name, parameter in signature.parameters.items():
                if parameter.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                    continue
                if parameter.default is inspect._empty:
                    required_fields.append(name)
                else:
                    optional_fields.append(name)
        return {
            "module": module_name,
            "symbol": symbol_name,
            "importable": True,
            "is_dataclass": bool(is_dataclass(symbol)),
            "required_init_fields": required_fields,
            "optional_init_fields": optional_fields,
            "signature_serializable": _json_serializable({"required": required_fields, "optional": optional_fields}),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "module": module_name,
            "symbol": symbol_name,
            "importable": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _contract_integrity(
    learning: dict[str, Any],
    account: dict[str, Any],
    trend: dict[str, Any],
    strategy: dict[str, Any],
) -> dict[str, Any]:
    entries = [_contract_entry(module, symbol) for module, symbol in CONTRACT_SYMBOLS]
    representative_outputs = {
        "learning_result": _to_dict(learning["strong"]),
        "account_health_result": _to_dict(account["clean_safe"]),
        "trend_result": _to_dict(trend["fresh"]),
        "strategy_result": strategy,
    }
    representative_serializable = {
        name: _json_serializable(payload) for name, payload in representative_outputs.items()
    }
    required_additive_fields = {
        "learning_trace": bool(representative_outputs["learning_result"].get("learning_insights", {}).get("learning_trace")),
        "health_trace": bool(representative_outputs["account_health_result"].get("health_trace")),
        "risk_components": bool(representative_outputs["account_health_result"].get("risk_components")),
        "trend_trace": bool(
            representative_outputs["trend_result"].get("collector_trace", {}).get("trend_trace")
        ),
        "trend_confidence_calibration": bool(
            representative_outputs["trend_result"].get("collector_trace", {}).get("confidence_calibration")
        ),
        "strategy_decision_trace": bool(representative_outputs["strategy_result"].get("decision_trace")),
    }
    return {
        "contracts_importable": all(entry.get("importable") for entry in entries),
        "contracts_dataclass_backed": all(entry.get("is_dataclass") for entry in entries if entry.get("importable")),
        "representative_outputs_serializable": all(representative_serializable.values()),
        "required_additive_fields_present": all(required_additive_fields.values()),
        "entries": entries,
        "representative_outputs_serializable_by_surface": representative_serializable,
        "required_additive_fields": required_additive_fields,
    }


def _collect_residuals(artifacts: dict[str, dict[str, Any]]) -> list[str]:
    residuals: list[str] = []
    for name in [
        "learning_gate",
        "account_health_gate",
        "trend_gate",
        "partial_master_gate",
        "wave_1_master_gate",
        "all_agents_extreme",
        "max_integrity_gate",
        "final_audit_report",
        "manual_batch10_post_fix",
    ]:
        payload = artifacts.get(name, {})
        residuals.extend(str(item) for item in list(payload.get("residual_monitoring") or []))
    strategy_full_gate = artifacts.get("strategy_full_gate", {})
    all_agents_extreme = artifacts.get("all_agents_extreme", {})
    strategy_editor_proven = bool(
        (strategy_full_gate.get("strong_downstream_effect") or {}).get("editor")
        or (all_agents_extreme.get("key_metrics") or {}).get("strategy_editor_effect_proven")
    )
    if strategy_editor_proven:
        residuals = [item for item in residuals if item != "STRATEGY_EDITOR_EFFECT_STILL_WEAK"]
    return sorted(set(residuals))


def _residuals_are_monitorable(residuals: list[str]) -> tuple[bool, list[str]]:
    unexpected: list[str] = []
    for item in residuals:
        if any(marker in item for marker in STRUCTURAL_RESIDUAL_MARKERS):
            unexpected.append(item)
            continue
        if not any(marker in item for marker in MONITORABLE_RESIDUAL_MARKERS):
            unexpected.append(item)
    return not unexpected, unexpected


def _child_gate_ok(payload: dict[str, Any], required_true: list[str]) -> bool:
    return (
        _gate_allows(payload.get("verdict"))
        and int(payload.get("critical_failures") or 0) == 0
        and list(payload.get("blocking_failures") or []) == []
        and payload.get("silent_failures_detected") is False
        and all(payload.get(field) is True for field in required_true)
    )


def _artifact_integrity(
    artifacts: dict[str, dict[str, Any]],
    errors: dict[str, str],
    existence: dict[str, bool],
) -> dict[str, Any]:
    docs = {name: (ROOT / path).exists() for name, path in REQUIRED_DOCS.items()}
    runners = {name: (ROOT / path).exists() for name, path in REQUIRED_RUNNERS.items()}
    return _block(
        all(docs.values()) and all(runners.values()) and not errors,
        docs=docs,
        runners=runners,
        json_artifact_presence=existence,
        json_errors=errors,
        required_json_payloads_present=all(existence.get(name) for name in REQUIRED_JSON_ARTIFACTS),
    )


def _governance_and_kernel(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    registry = artifacts.get("system_governance_registry", {})
    master_state_path = ROOT / "docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md"
    architecture_path = ROOT / "docs/runtime/architecture/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md"
    master_state = _read_text(master_state_path) if master_state_path.exists() else ""
    architecture = _read_text(architecture_path) if architecture_path.exists() else ""
    global_rules = dict(registry.get("global_rules") or {})
    core = dict(registry.get("core_pipeline") or {})
    checks = {
        "system_version": registry.get("system_version") == "CORTAI_RUNTIME_V2_5",
        "governance_model": registry.get("governance_model") == "SUBSYSTEM_BASELINE_WITH_MONITORING",
        "core_frozen": core.get("status") == "FROZEN_AND_VALIDATED",
        "change_policy_frozen": core.get("change_policy") == "FROZEN_UNLESS_GOVERNANCE_REOPEN",
        "no_core_modification": global_rules.get("no_core_modification") is True,
        "no_subsystem_mutation_without_reopen": global_rules.get("no_subsystem_mutation_without_reopen") is True,
        "new_work_isolated": global_rules.get("new_work_must_be_isolated_subsystems") is True,
        "kernel_neutral_documented": "governed runtime" in master_state.lower() and "FROZEN_AND_VALIDATED" in master_state,
        "architecture_boundary_documented": "Fase 1 executa" in architecture or "Phase 1" in architecture,
    }
    return _block(all(checks.values()), **checks)


def _run_controlled_scenarios() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    wave1 = _load_wave1_module()
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        learning = wave1._build_learning_scenarios(root)
        account = wave1._build_account_scenarios()
        trend = wave1._build_trend_scenarios(root)
        cross_agent, cross_consistency = wave1._build_cross_agent_scenarios(account, learning, trend)
        strategy = wave1._strategy(account["clean_safe"], learning["strong"], trend["fresh"])
        scenario_outputs = {
            "learning": {name: wave1._learning_summary(result) for name, result in learning.items()},
            "account_health": {name: wave1._account_summary(result) for name, result in account.items()},
            "trend_analysis": {name: wave1._trend_summary(result) for name, result in trend.items()},
            "cross_agent": cross_agent,
            "cross_agent_consistency": cross_consistency,
        }
        return learning, account, trend, strategy, scenario_outputs, cross_consistency


def _telemetry_evidence_integrity(
    learning: dict[str, Any],
    account: dict[str, Any],
    trend: dict[str, Any],
) -> dict[str, Any]:
    learning_trace = _learning_trace(learning["strong"])
    missing_health = account["missing_telemetry"]
    fresh_trend_trace = trend["fresh"].collector_trace["trend_trace"]
    checks = {
        "learning_real_evidence": learning_trace.get("lineage_summary", {}).get("clean_evidence_count", 0) > 0,
        "learning_contamination_explicit": bool(_learning_trace(learning["contaminated"]).get("downgraded_evidence")),
        "learning_fallback_explicit": learning["fallback"].fallback.used is True,
        "account_telemetry_status_visible": "source_status_distribution" in missing_health.telemetry_summary,
        "account_absent_visible": missing_health.telemetry_summary.get("source_status_distribution", {}).get("ABSENT", 0) > 0,
        "trend_source_governance_present": bool(fresh_trend_trace.get("source_governance")),
        "trend_provenance_present": bool(fresh_trend_trace.get("provenance")),
        "trend_evidence_references_present": bool(fresh_trend_trace.get("provenance", {}).get("evidence_references")),
    }
    return _block(all(checks.values()), **checks)


def _confidence_honesty(
    learning: dict[str, Any],
    account: dict[str, Any],
    trend: dict[str, Any],
) -> dict[str, Any]:
    learning_conf = {name: _policy_confidence(result) for name, result in learning.items()}
    account_conf = {name: float(result.confidence) for name, result in account.items()}
    trend_conf = {
        name: float(result.collector_trace.get("confidence_calibration", {}).get("confidence", 0.0))
        for name, result in trend.items()
    }
    checks = {
        "learning_confidence_not_constant": len({round(v, 4) for v in learning_conf.values()}) > 1,
        "account_confidence_not_constant": len({round(v, 4) for v in account_conf.values()}) > 1,
        "trend_confidence_not_constant": len({round(v, 4) for v in trend_conf.values()}) > 1,
        "learning_fallback_low": learning_conf["fallback"] <= 0.35,
        "learning_contaminated_low": learning_conf["contaminated"] <= 0.35,
        "account_missing_low": account_conf["missing_telemetry"] <= 0.35,
        "trend_fallback_low": trend_conf["fallback"] <= 0.35,
        "trend_expired_lower_than_fresh": trend_conf["expired"] < trend_conf["fresh"],
        "confidence_rationales_present": bool(trend["fresh"].collector_trace.get("confidence_calibration", {}).get("rationale")),
    }
    return _block(
        all(checks.values()),
        learning_confidence=learning_conf,
        account_confidence=account_conf,
        trend_confidence=trend_conf,
        **checks,
    )


def _temporal_freshness(account: dict[str, Any], trend: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "account_temporal_present": bool(account["clean_safe"].temporal_health),
        "account_insufficient_not_stable": account["missing_telemetry"].temporal_health.get("classification") == "insufficient_evidence",
        "trend_fresh_valid": trend["fresh"].collector_trace.get("validity", {}).get("validity_status") == "valid",
        "trend_stale_degraded": trend["stale"].collector_trace.get("validity", {}).get("validity_status") == "degraded",
        "trend_expired_invalid": trend["expired"].collector_trace.get("validity", {}).get("validity_status") == "invalid",
        "stale_visible": any(
            item.get("kind") == "stale_source"
            for item in trend["stale"].collector_trace["trend_trace"].get("missing_or_degraded_inputs", [])
        ),
        "expired_visible": any(
            item.get("kind") == "expired_source"
            for item in trend["expired"].collector_trace["trend_trace"].get("missing_or_degraded_inputs", [])
        ),
    }
    return _block(all(checks.values()), **checks)


def _degraded_fail_safety(account: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "missing_safe_not_fully_trusted": account["missing_telemetry"].decision.status == "SAFE"
        and account["missing_telemetry"].confidence_level == "low",
        "severe_degraded_to_hold": account["severe_degraded"].decision.status == "HOLD",
        "hold_never_downgraded": account["hold"].decision.status == "HOLD",
        "degraded_policy_visible": bool(account["severe_degraded"].degraded_input_decision),
        "decision_adjustment_trace_visible": "decision_adjustment" in account["severe_degraded"].decision_trace,
    }
    return _block(all(checks.values()), **checks)


def _risk_components(account: dict[str, Any]) -> dict[str, Any]:
    required = {
        "publish_frequency_risk",
        "performance_drop_risk",
        "repetition_risk",
        "low_quality_streak_risk",
        "fallback_contamination_risk",
    }
    risk_summary = account["clean_safe"].risk_components or {}
    components = dict(risk_summary.get("components") or {})
    component_fields_complete = all(
        all(field in component for field in ["score", "level", "reason_code", "evidence_status", "rationale"])
        for component in components.values()
    )
    checks = {
        "required_components_present": required.issubset(set(components)),
        "component_fields_complete": component_fields_complete,
        "risk_score_present": isinstance(account["clean_safe"].risk_score, float),
        "missing_not_fake_healthy": any(
            component.get("evidence_status") == "ABSENT"
            for component in ((account["missing_telemetry"].risk_components or {}).get("components") or {}).values()
        ),
    }
    return _block(all(checks.values()), required_components=sorted(required), present_components=sorted(components), **checks)


def _trend_complete(trend: dict[str, Any]) -> dict[str, Any]:
    fresh_trace = trend["fresh"].collector_trace.get("trend_trace", {})
    fallback_trace = trend["fallback"].collector_trace.get("trend_trace", {})
    required = {
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
    checks = {
        "fresh_required_sections_present": required.issubset(set(fresh_trace)),
        "fresh_reconstructible": fresh_trace.get("audit_summary", {}).get("reconstructible") is True,
        "fallback_visible": trend["fallback"].fallback.used is True and bool(fallback_trace.get("fallback")),
        "safe_default_low_authority": trend["fallback"].collector_trace.get("confidence_calibration", {}).get("confidence_level") == "low",
        "source_governance_policy_respected": fresh_trace.get("source_governance", {}).get("policy_respected") is True,
        "provenance_present": bool(fresh_trace.get("provenance", {}).get("field_provenance")),
        "downstream_advisory": fresh_trace.get("downstream_utility", {}).get("boundary_statement")
        == "Trend provides context only; Strategy remains the control layer.",
        "shift_retrospective": "predicted" not in json.dumps(fresh_trace.get("shift_analysis", {})).lower(),
    }
    return _block(
        all(checks.values()),
        fresh_sections=sorted(fresh_trace),
        fallback_audit_summary=fallback_trace.get("audit_summary", {}),
        **checks,
    )


def _trace_auditability(
    learning: dict[str, Any],
    account: dict[str, Any],
    trend: dict[str, Any],
) -> dict[str, Any]:
    learning_sections = set(_learning_trace(learning["strong"]))
    health_sections = set(account["clean_safe"].health_trace)
    trend_sections = set(trend["fresh"].collector_trace.get("trend_trace", {}))
    required_learning = {
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
    required_health = {
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
    required_trend = {
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
    checks = {
        "learning_trace_complete": required_learning.issubset(learning_sections),
        "health_trace_complete": required_health.issubset(health_sections),
        "trend_trace_complete": required_trend.issubset(trend_sections),
        "health_reconstructible": account["clean_safe"].health_trace.get("audit_summary", {}).get("reconstructible") is True,
        "trend_reconstructible": trend["fresh"].collector_trace.get("trend_trace", {}).get("audit_summary", {}).get("reconstructible") is True,
        "fallback_paths_visible": learning["fallback"].fallback.used and trend["fallback"].fallback.used,
    }
    return _block(
        all(checks.values()),
        learning_sections=sorted(learning_sections),
        health_sections=sorted(health_sections),
        trend_sections=sorted(trend_sections),
        **checks,
    )


def _hold_authority(account: dict[str, Any], cross_consistency: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "hold_decision_preserved": account["hold"].decision.status == "HOLD",
        "severe_degraded_hold": account["severe_degraded"].decision.status == "HOLD",
        "hold_authority_invoked_visible": account["hold"].health_trace.get("final_decision_rationale", {}).get("hold_authority_invoked") is True,
        "cross_agent_hold_outranks": cross_consistency.get("health_hold_outranks_learning_and_trend", {}).get("passed") is True,
    }
    return _block(all(checks.values()), **checks)


def _determinism(
    learning: dict[str, Any],
    account: dict[str, Any],
    trend: dict[str, Any],
    cross_consistency: dict[str, Any],
) -> dict[str, Any]:
    checks = {
        "learning_replay_stable": _to_dict(learning["strong"]) == _to_dict(learning["strong_repeat"]),
        "trend_replay_stable": _to_dict(trend["fresh"]) == _to_dict(trend["fresh_repeat"]),
        "account_health_replay_represented": account["clean_safe"].decision.status == "SAFE",
        "combined_upstream_not_contradictory": cross_consistency.get("combined_upstream_traces_not_contradictory", {}).get("passed") is True,
    }
    return _block(all(checks.values()), **checks)


def _boundary_preservation(cross_consistency: dict[str, Any], trend: dict[str, Any]) -> dict[str, Any]:
    trend_payload = json.dumps(_to_dict(trend["fresh"]), sort_keys=True)
    checks = {
        "learning_not_strategy": cross_consistency.get("learning_strong_pressure_bounded", {}).get("passed") is True,
        "health_not_strategy": cross_consistency.get("health_caution_constrains_without_becoming_strategy", {}).get("passed") is True,
        "trend_context_only": cross_consistency.get("trend_high_confidence_context_only", {}).get("passed") is True,
        "strategy_control_layer_preserved": all(payload.get("passed") for payload in cross_consistency.values()),
        "trend_no_publishability_decision": "publishability_decision" not in trend_payload,
        "trend_no_constraints_authority": "recommended_constraints" not in trend_payload,
    }
    return _block(all(checks.values()), **checks)


def _silent_failure_surface(
    learning: dict[str, Any],
    account: dict[str, Any],
    trend: dict[str, Any],
    cross_consistency: dict[str, Any],
) -> dict[str, Any]:
    checks = {
        "hidden_learning_fallback_absent": learning["fallback"].fallback.used is True,
        "hidden_trend_fallback_absent": trend["fallback"].fallback.used is True,
        "hidden_degraded_input_absent": account["missing_telemetry"].degraded_input_decision.get("degraded_input_detected") is True,
        "fake_confidence_absent": _confidence_honesty(learning, account, trend).get("passed") is True,
        "orphan_constraints_absent": all(
            len(result.decision.recommended_constraints or {}) == len(result.constraint_rationale or [])
            for result in account.values()
        ),
        "silent_hold_downgrade_absent": account["hold"].decision.status == "HOLD",
        "trend_fallback_not_inflated": trend["fallback"].collector_trace.get("confidence_calibration", {}).get("confidence_level") == "low",
        "learning_contamination_not_dominant": _pressure_mode(learning["contaminated"]) == "weak_bias",
        "cross_agent_no_contradiction": cross_consistency.get("combined_upstream_traces_not_contradictory", {}).get("passed") is True,
    }
    return _block(all(checks.values()), **checks)


def _master_consistency(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    optional_verdicts = {
        name: payload.get("verdict") or payload.get("overall_verdict") or payload.get("status")
        for name, payload in artifacts.items()
        if name in {**OPTIONAL_JSON_ARTIFACTS, **REQUIRED_JSON_ARTIFACTS}
    }
    checks = {
        "wave_1_non_blocking": _gate_allows(artifacts.get("wave_1_master_gate", {}).get("verdict")),
        "wave_1_recommends_wave_2": artifacts.get("wave_1_master_gate", {}).get("recommendation")
        == "PROCEED_TO_PHASE_2_6_WAVE_2_PLAN",
        "partial_master_non_blocking": _gate_allows(artifacts.get("partial_master_gate", {}).get("verdict")),
        "all_agents_extreme_non_blocking": _gate_allows(artifacts.get("all_agents_extreme", {}).get("verdict")),
        "max_integrity_non_blocking": _gate_allows(artifacts.get("max_integrity_gate", {}).get("verdict")),
        "final_audit_non_blocking": _gate_allows(artifacts.get("final_audit_report", {}).get("verdict")),
        "no_recent_hold": all(value != "HOLD" for value in optional_verdicts.values() if value),
    }
    return _block(all(checks.values()), optional_verdicts=optional_verdicts, **checks)


def _build_blocks(
    *,
    artifacts: dict[str, dict[str, Any]],
    errors: dict[str, str],
    existence: dict[str, bool],
    tests: dict[str, Any],
    learning: dict[str, Any],
    account: dict[str, Any],
    trend: dict[str, Any],
    cross_consistency: dict[str, Any],
    contract_report: dict[str, Any],
    residuals: list[str],
) -> dict[str, Any]:
    learning_required = [
        "runtime_real",
        "evidence_backed",
        "confidence_calibrated",
        "temporal_weighting_real",
        "contamination_handling_strong",
        "strategy_pressure_bounded",
        "traceability_complete",
        "fallback_honest",
        "boundary_preserved",
        "determinism_where_required",
    ]
    health_required = [
        "runtime_real",
        "telemetry_enriched",
        "risk_components_explicit",
        "confidence_calibrated",
        "temporal_health_real",
        "degraded_input_safe",
        "constraints_rationale_complete",
        "traceability_complete",
        "hold_authority_preserved",
        "fallback_honest",
        "boundary_preserved",
        "determinism_where_required",
    ]
    trend_required = [
        "runtime_real",
        "source_governed",
        "evidence_backed",
        "freshness_disciplined",
        "confidence_calibrated",
        "shift_analysis_meaningful",
        "downstream_utility_clear",
        "traceability_complete",
        "fallback_honest",
        "boundary_preserved",
        "determinism_where_required",
    ]
    residuals_ok, unexpected_residuals = _residuals_are_monitorable(residuals)
    wave1_blocks = artifacts.get("wave_1_master_gate", {}).get("blocks", {})
    all_agents = artifacts.get("all_agents_extreme", {})
    max_gate = artifacts.get("max_integrity_gate", {})
    final_audit = artifacts.get("final_audit_report", {})

    blocks: dict[str, Any] = {}
    blocks["block_a_governance_and_kernel_neutrality"] = _governance_and_kernel(artifacts)
    blocks["block_b_artifact_integrity"] = _artifact_integrity(artifacts, errors, existence)
    blocks["block_c_contract_integrity_across_agents"] = _block(
        contract_report["contracts_importable"]
        and contract_report["representative_outputs_serializable"]
        and contract_report["required_additive_fields_present"],
        **contract_report,
    )
    blocks["block_d_runtime_reality"] = _block(
        _child_gate_ok(artifacts.get("learning_gate", {}), ["runtime_real"])
        and _child_gate_ok(artifacts.get("account_health_gate", {}), ["runtime_real"])
        and _child_gate_ok(artifacts.get("trend_gate", {}), ["runtime_real"])
        and all(payload.get("passed") for payload in cross_consistency.values()),
        wave_1_uses_real_services=True,
        learning_runtime_real=artifacts.get("learning_gate", {}).get("runtime_real"),
        account_health_runtime_real=artifacts.get("account_health_gate", {}).get("runtime_real"),
        trend_runtime_real=artifacts.get("trend_gate", {}).get("runtime_real"),
        cross_agent_real_service_scenarios=all(payload.get("passed") for payload in cross_consistency.values()),
    )
    blocks["block_e_telemetry_and_evidence_integrity"] = _telemetry_evidence_integrity(learning, account, trend)
    blocks["block_f_confidence_honesty"] = _confidence_honesty(learning, account, trend)
    blocks["block_g_temporal_and_freshness_discipline"] = _temporal_freshness(account, trend)
    blocks["block_h_degraded_input_and_fail_safety"] = _degraded_fail_safety(account)
    blocks["block_i_risk_components"] = _risk_components(account)
    blocks["block_j_trend_analysis_complete_check"] = _trend_complete(trend)
    blocks["block_k_trace_and_auditability"] = _trace_auditability(learning, account, trend)
    blocks["block_l_hold_authority"] = _hold_authority(account, cross_consistency)
    blocks["block_m_determinism_and_replay"] = _determinism(learning, account, trend, cross_consistency)
    blocks["block_n_boundary_preservation"] = _boundary_preservation(cross_consistency, trend)
    blocks["block_o_full_test_battery"] = _block(
        tests.get("passed") is True,
        tests_executed=tests,
        timeout_classified=not tests.get("timeout") or bool(tests.get("timeout_classification")),
    )
    blocks["block_p_cross_agent_consistency"] = _block(
        all(payload.get("passed") for payload in cross_consistency.values()),
        scenario_results=cross_consistency,
    )
    blocks["block_q_silent_failure_detection"] = _silent_failure_surface(learning, account, trend, cross_consistency)
    blocks["block_r_backward_compatibility"] = _block(
        contract_report["required_additive_fields_present"]
        and artifacts.get("account_health_gate", {})
        .get("checklist_results", {})
        .get("blocks", {})
        .get("block_13_backward_compatibility", {})
        .get("passed")
        is True
        and artifacts.get("trend_gate", {})
        .get("checklist_results", {})
        .get("blocks", {})
        .get("block_12_backward_compatibility", {})
        .get("passed")
        is True,
        account_health_backward_compatible=artifacts.get("account_health_gate", {})
        .get("checklist_results", {})
        .get("blocks", {})
        .get("block_13_backward_compatibility", {})
        .get("passed"),
        trend_backward_compatible=artifacts.get("trend_gate", {})
        .get("checklist_results", {})
        .get("blocks", {})
        .get("block_12_backward_compatibility", {})
        .get("passed"),
        additive_fields_present=contract_report["required_additive_fields"],
    )
    blocks["block_s_residual_monitoring_classification"] = _block(
        residuals_ok,
        residual_monitoring=residuals,
        unexpected_residuals=unexpected_residuals,
    )
    blocks["block_t_master_consistency"] = _master_consistency(artifacts)
    structural_preconditions = {
        "learning_gate_integrity": _child_gate_ok(artifacts.get("learning_gate", {}), learning_required),
        "account_health_gate_integrity": _child_gate_ok(artifacts.get("account_health_gate", {}), health_required),
        "trend_gate_integrity": _child_gate_ok(artifacts.get("trend_gate", {}), trend_required),
        "wave_1_blocks_passed": all(block.get("passed") for block in wave1_blocks.values()),
        "all_agents_extreme_non_blocking": _gate_allows(all_agents.get("verdict")) and not all_agents.get("blocking_failures"),
        "max_integrity_non_blocking": _gate_allows(max_gate.get("verdict")) and not max_gate.get("blocking_failures"),
        "final_audit_non_blocking": _gate_allows(final_audit.get("verdict")) and not final_audit.get("blocking_failures"),
    }
    failed_before_final = [name for name, block in blocks.items() if not block.get("passed")]
    blocks["block_u_final_release_decision"] = _block(
        not failed_before_final and all(structural_preconditions.values()),
        failed_blocks_before_final=failed_before_final,
        structural_preconditions=structural_preconditions,
        final_rule="HOLD on any hard stop; GO_WITH_MONITORING on bounded non-structural residuals; GO only without residuals.",
    )
    return blocks


def _hard_stop_summary(blocks: dict[str, Any], tests: dict[str, Any]) -> dict[str, Any]:
    return {
        "critical_failures": sum(1 for block in blocks.values() if not block.get("passed")),
        "silent_failures": not blocks.get("block_q_silent_failure_detection", {}).get("passed", False),
        "fake_confidence": not blocks.get("block_f_confidence_honesty", {}).get("passed", False),
        "boundary_violations": not blocks.get("block_n_boundary_preservation", {}).get("passed", False),
        "non_determinism": not blocks.get("block_m_determinism_and_replay", {}).get("passed", False),
        "trace_incomplete": not blocks.get("block_k_trace_and_auditability", {}).get("passed", False),
        "test_failure": not tests.get("passed", False),
    }


def _build_metrics(
    blocks: dict[str, Any],
    tests: dict[str, Any],
    learning: dict[str, Any],
    account: dict[str, Any],
    trend: dict[str, Any],
    blocking_failures: list[str],
) -> dict[str, Any]:
    return {
        "block_count": len(blocks),
        "block_pass_count": sum(1 for block in blocks.values() if block.get("passed")),
        "block_fail_count": sum(1 for block in blocks.values() if not block.get("passed")),
        "critical_failures": len(blocking_failures),
        "blocking_failures_count": len(blocking_failures),
        "test_failures": 0 if tests.get("passed") else 1,
        "boundary_violations_detected": not blocks["block_n_boundary_preservation"].get("passed", False),
        "silent_failures_detected": not blocks["block_q_silent_failure_detection"].get("passed", False),
        "fake_confidence_detected": not blocks["block_f_confidence_honesty"].get("passed", False),
        "non_determinism_detected": not blocks["block_m_determinism_and_replay"].get("passed", False),
        "trace_incomplete_detected": not blocks["block_k_trace_and_auditability"].get("passed", False),
        "pytest_duration_seconds": tests.get("duration_seconds"),
        "pytest_test_files_count": len(tests.get("test_files") or []),
        "account_health_decisions": {name: result.decision.status for name, result in account.items()},
        "learning_pressure_modes": {name: _pressure_mode(result) for name, result in learning.items()},
        "trend_validity_statuses": {
            name: result.collector_trace.get("validity", {}).get("validity_status") for name, result in trend.items()
        },
    }


def _agent_summary(gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "verdict": gate.get("verdict"),
        "ready_for_v3_with_monitoring": _gate_allows(gate.get("verdict")) and not gate.get("blocking_failures"),
        "critical_failures": int(gate.get("critical_failures") or 0),
        "blocking_failures": list(gate.get("blocking_failures") or []),
    }


def _run_gate() -> dict[str, Any]:
    _reset_audit_dir()
    artifacts, errors, existence = _load_artifacts()
    tests = _run_pytest(TEST_BATTERY)
    learning, account, trend, strategy, scenario_outputs, cross_consistency = _run_controlled_scenarios()
    contract_report = _contract_integrity(learning, account, trend, strategy)
    residuals = _collect_residuals(artifacts)
    blocks = _build_blocks(
        artifacts=artifacts,
        errors=errors,
        existence=existence,
        tests=tests,
        learning=learning,
        account=account,
        trend=trend,
        cross_consistency=cross_consistency,
        contract_report=contract_report,
        residuals=residuals,
    )
    hard_stop = _hard_stop_summary(blocks, tests)
    failed_blocks = [name for name, block in blocks.items() if not block.get("passed")]
    blocking_failures = [f"BLOCK_FAILED:{name}" for name in failed_blocks]
    if tests.get("timeout"):
        blocking_failures.append("UNIT_TEST_BATTERY_TIMEOUT")
    if not tests.get("passed"):
        blocking_failures.append("UNIT_TEST_BATTERY_FAILED")
    if any(value is True for key, value in hard_stop.items() if key != "critical_failures"):
        for key, value in hard_stop.items():
            if key != "critical_failures" and value is True:
                marker = f"HARD_STOP:{key.upper()}"
                if marker not in blocking_failures:
                    blocking_failures.append(marker)
    residual_monitoring = [] if blocking_failures else residuals
    if blocking_failures:
        verdict = "HOLD"
    elif residual_monitoring:
        verdict = "GO_WITH_MONITORING"
    else:
        verdict = "GO"
    metrics = _build_metrics(blocks, tests, learning, account, trend, blocking_failures)
    checklist_results = {
        "global_hard_stop_rule": hard_stop,
        "blocks": blocks,
        "failed_blocks": failed_blocks,
        "final_release_criteria": {
            "no_critical_failures": hard_stop["critical_failures"] == 0,
            "no_silent_failures": hard_stop["silent_failures"] is False,
            "no_fake_confidence": hard_stop["fake_confidence"] is False,
            "no_boundary_violations": hard_stop["boundary_violations"] is False,
            "no_non_determinism": hard_stop["non_determinism"] is False,
            "trace_complete": hard_stop["trace_incomplete"] is False,
            "tests_passed": hard_stop["test_failure"] is False,
            "residuals_monitorable": blocks["block_s_residual_monitoring_classification"].get("passed"),
        },
    }
    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "2.6",
        "audit_type": "CORTAI_ABSOLUTE_MASTER_GATE_PRE_WAVE_2",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "global_hard_stop_rule": hard_stop,
        "wave_1_agents": {
            "learning_agent_v2_6": _agent_summary(artifacts.get("learning_gate", {})),
            "account_health_agent_v2_6": _agent_summary(artifacts.get("account_health_gate", {})),
            "trend_analysis_agent_v2_6": _agent_summary(artifacts.get("trend_gate", {})),
        },
        "blocks": {name: {"passed": bool(block.get("passed"))} for name, block in blocks.items()},
        "tests_executed": [tests],
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
    _write_json(CONTRACT_INTEGRITY_PATH, contract_report)
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
            "audit_type": "CORTAI_ABSOLUTE_MASTER_GATE_PRE_WAVE_2",
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
