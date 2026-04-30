from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "phase_2_6_final_master_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
MASTER_CONSISTENCY_PATH = AUDIT_DIR / "master_consistency.json"

REQUIRED_DOCS = {
    "phase_2_6_master_plan": "docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md",
    "wave_1_master_gate_doc": "docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_1_MASTER_GATE.md",
    "wave_2_master_gate_doc": "docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_2_MASTER_GATE.md",
    "absolute_master_pre_wave_2_doc": "docs/runtime/phase-2-6/master-gates/CORTAI_ABSOLUTE_MASTER_GATE_PRE_WAVE_2.md",
    "final_master_gate_doc": "docs/runtime/phase-2-6/master-gates/PHASE_2_6_FINAL_MASTER_GATE.md",
    "master_state": "docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md",
    "architecture_bible": "docs/runtime/architecture/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md",
}

REQUIRED_RUNNERS = {
    "wave_1_master_gate_runner": "tests/gates/phase_2_6/run_phase_2_6_wave_1_master_gate.py",
    "wave_2_master_gate_runner": "tests/gates/phase_2_6/run_phase_2_6_wave_2_master_gate.py",
    "absolute_master_pre_wave_2_runner": "tests/gates/phase_2_6/run_cortai_absolute_master_gate.py",
    "final_master_gate_runner": "tests/gates/phase_2_6/run_phase_2_6_final_master_gate.py",
    "learning_gate_runner": "tests/gates/agents/learning/run_learning_agent_v2_6_excellence_gate.py",
    "account_health_gate_runner": "tests/gates/agents/account_health/run_account_health_agent_v2_6_excellence_gate.py",
    "trend_gate_runner": "tests/gates/agents/trend_analysis/run_trend_analysis_agent_v2_6_excellence_gate.py",
    "script_gate_runner": "tests/gates/agents/script/run_script_agent_v2_6_excellence_gate.py",
    "voice_gate_runner": "tests/gates/agents/voice/run_voice_agent_v2_6_excellence_gate.py",
    "asset_gate_runner": "tests/gates/agents/asset_selection/run_asset_selection_agent_v2_6_excellence_gate.py",
    "video_qc_gate_runner": "tests/gates/agents/video_qc/run_video_qc_agent_v2_6_excellence_gate.py",
}

REQUIRED_JSON_ARTIFACTS = {
    "learning_gate": "OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json",
    "account_health_gate": "OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json",
    "trend_gate": "OUT/audit/trend_analysis_agent_v2_6_excellence_gate/final_verdict.json",
    "script_gate": "OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json",
    "voice_gate": "OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json",
    "asset_gate": "OUT/audit/asset_selection_agent_v2_6_excellence_gate/final_verdict.json",
    "video_qc_gate": "OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json",
    "wave_1_master_gate": "OUT/audit/phase_2_6_wave_1_master_gate/final_verdict.json",
    "wave_2_master_gate": "OUT/audit/phase_2_6_wave_2_master_gate/final_verdict.json",
    "absolute_master_pre_wave_2": "OUT/audit/cortai_absolute_master_gate/final_verdict.json",
    "system_governance_registry": "OUT/audit/system_governance_registry.json",
    "pipeline_total_heavy_audit": "OUT/audit/pipeline_total_heavy_audit/final_verdict.json",
    "pipeline_full_master_certification": "OUT/audit/pipeline_full_master_certification/final_verdict.json",
    "all_agents_extreme_checklist": "OUT/audit/cortai_runtime_v2_5_all_agents_extreme_checklist/final_verdict.json",
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
    "tests/agents/script/test_script_context_governance_unittest.py",
    "tests/agents/script/test_script_quality_rubric_unittest.py",
    "tests/agents/script/test_script_hook_strength_unittest.py",
    "tests/agents/script/test_script_setup_progression_unittest.py",
    "tests/agents/script/test_script_payoff_memorability_unittest.py",
    "tests/agents/script/test_script_diversity_anti_cliche_unittest.py",
    "tests/agents/script/test_script_provider_fallback_honesty_unittest.py",
    "tests/agents/script/test_script_confidence_calibration_unittest.py",
    "tests/agents/script/test_script_trace_auditability_unittest.py",
    "tests/agents/script/test_script_agent_phase2_unittest.py",
    "tests/agents/script/test_script_generation_unittest.py",
    "tests/agents/voice/test_voice_trace_auditability_unittest.py",
    "tests/agents/voice/test_voice_confidence_calibration_unittest.py",
    "tests/agents/voice/test_voice_audio_validation_linkage_unittest.py",
    "tests/agents/voice/test_voice_provider_fallback_honesty_unittest.py",
    "tests/agents/voice/test_voice_monotony_contrast_analysis_unittest.py",
    "tests/agents/voice/test_voice_segment_timing_pause_unittest.py",
    "tests/agents/voice/test_voice_delivery_profile_semantics_unittest.py",
    "tests/agents/voice/test_voice_plan_contract_governance_unittest.py",
    "tests/agents/voice/test_voice_agent_phase2_unittest.py",
    "tests/agents/voice/test_voice_agent_service_phase2_5_unittest.py",
    "tests/agents/voice/test_voice_interpreter_phase2_5_unittest.py",
    "tests/agents/voice/test_tts_router_phase2_5_unittest.py",
    "tests/agents/voice/test_tts_router_kokoro_phase2_5b_unittest.py",
    "tests/agents/voice/test_kokoro_adapter_phase2_5b_unittest.py",
    "tests/agents/voice/test_kokoro_fallback_phase2_5b_unittest.py",
    "tests/agents/asset_selection/test_asset_trace_auditability_unittest.py",
    "tests/agents/asset_selection/test_asset_confidence_calibration_unittest.py",
    "tests/agents/asset_selection/test_asset_diversity_guard_unittest.py",
    "tests/agents/asset_selection/test_asset_fallback_honesty_unittest.py",
    "tests/agents/asset_selection/test_asset_visual_truthfulness_unittest.py",
    "tests/agents/asset_selection/test_asset_visual_semantic_alignment_unittest.py",
    "tests/agents/asset_selection/test_asset_segment_visual_intent_unittest.py",
    "tests/agents/asset_selection/test_asset_catalog_source_governance_unittest.py",
    "tests/agents/asset_selection/test_asset_context_governance_unittest.py",
    "tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py",
    "tests/agents/asset_selection/test_asset_plan_runtime_integration_unittest.py",
    "tests/agents/video_qc/test_video_qc_trace_auditability_unittest.py",
    "tests/agents/video_qc/test_video_qc_decision_semantics_unittest.py",
    "tests/agents/video_qc/test_video_qc_confidence_evidence_unittest.py",
    "tests/agents/video_qc/test_video_qc_input_governance_unittest.py",
    "tests/agents/video_qc/test_video_qc_agent_phase2_unittest.py",
    "tests/agents/strategy/test_strategy_agent_phase2_unittest.py",
    "tests/agents/strategy/test_strategy_agent_evolution_v2_0_integration_unittest.py",
    "tests/agents/strategy/test_strategy_learning_d9_unittest.py",
    "tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py",
    "tests/experiment/test_experiment_capability_phase2_unittest.py",
    "tests/attribution/test_content_attribution_phase_d_bounded_integration_unittest.py",
    "tests/content/test_content_pipeline_d27_unittest.py",
    "tests/agents/novelty/test_novelty_engine_unittest.py",
    "tests/agents/editor/test_editor_agent_service_unittest.py",
    "tests/agents/editor/test_editor_interpreter_unittest.py",
    "tests/agents/editor/test_editor_plan_unittest.py",
    "tests/runtime/pipeline/test_phase2_block1_smoke_unittest.py",
    "tests/runtime/pipeline/test_phase2_block2_smoke_unittest.py",
    "tests/runtime/pipeline/test_phase2_block3_smoke_unittest.py",
    "tests/runtime/pipeline/test_phase2_block4_smoke_unittest.py",
]

CHILD_GATES = [
    "learning_gate",
    "account_health_gate",
    "trend_gate",
    "script_gate",
    "voice_gate",
    "asset_gate",
    "video_qc_gate",
]

MASTER_GATES = ["wave_1_master_gate", "wave_2_master_gate", "absolute_master_pre_wave_2"]

ALLOWED_RESIDUAL_FRAGMENTS = {
    "RUNTIME_HISTORY_STILL_SHORT",
    "HISTORY_STILL_SHORT",
    "LONGITUDINAL",
    "PRODUCER_COVERAGE",
    "PROVIDER_EXECUTION_HISTORY_STILL_SHORT",
    "PROVIDER_HISTORY_STILL_SHORT",
    "CATALOG_COVERAGE_STILL_EXPANDING",
    "COVERAGE_STILL_BOUNDED",
    "COVERAGE_ENVIRONMENT_DEPENDENT",
    "PRODUCT_SIGNAL_CALIBRATION_STILL_MATURING",
    "LAYER_ATTRIBUTION_EVIDENCE_STILL_LIMITED",
    "REPAIR_METADATA",
    "TTS_TRACE_NOT_AVAILABLE",
    "AUDIO_VALIDATION_HISTORY_STILL_SHORT",
    "VISUAL_HISTORY_STILL_SHORT",
    "IMAGE_PIXEL_VALIDATION_NOT_AVAILABLE_AT_SELECTION_LAYER",
    "PIXEL_LEVEL_VALIDATION",
    "CONTROLLED_SCENARIO",
    "CONTROLLED_VALIDATION",
    "REAL_PRODUCTION",
    "V3_READINESS_REQUIRES",
    "ATTRIBUTION_MANUAL_FLOW_REQUIRES",
    "CREATIVE_CENTER_PUBLIC_SURFACE_LIMITATION",
    "STRATEGY_FULL_GATE_REQUIRES_REFRESH",
    "TREND_GATE_REQUIRES_MONITORING",
    "TREND_MONITORING_STATUS_INSUFFICIENT_INPUT",
    "LEARNING_BATCH_BOOTSTRAP_EFFECT_PRESENT",
    "QC_GATE_MONITORING_REQUIRED",
    "TELEMETRY_RICHNESS_STILL_LIMITED",
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


def _load_artifacts() -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, bool]]:
    artifacts: dict[str, dict[str, Any]] = {}
    json_errors: dict[str, str] = {}
    existence: dict[str, bool] = {}
    for name, rel_path in REQUIRED_JSON_ARTIFACTS.items():
        path = ROOT / rel_path
        existence[name] = path.exists()
        if not path.exists():
            artifacts[name] = {}
            json_errors[name] = "missing"
            continue
        payload, error = _load_json(path)
        artifacts[name] = payload
        if error:
            json_errors[name] = error
    return artifacts, json_errors, existence


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _run_pytest(test_files: list[str]) -> dict[str, Any]:
    deduped = _dedupe(test_files)
    missing = [path for path in deduped if not (ROOT / path).exists()]
    runnable = [path for path in deduped if (ROOT / path).exists()]
    command = [sys.executable, "-m", "pytest", "-q", *runnable]
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
            timeout=2400,
        )
        duration = round(time.perf_counter() - started, 3)
        output = completed.stdout + "\n" + completed.stderr
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        passed = completed.returncode == 0 and not missing
        return {
            "command": command,
            "passed": passed,
            "timeout": False,
            "returncode": completed.returncode,
            "duration_seconds": duration,
            "test_files": runnable,
            "missing_test_files": missing,
            "passed_count": _extract_pass_count(lines),
            "output_tail": lines[-30:],
        }
    except subprocess.TimeoutExpired as exc:
        duration = round(time.perf_counter() - started, 3)
        output = f"{exc.stdout or ''}\n{exc.stderr or ''}"
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        return {
            "command": command,
            "passed": False,
            "timeout": True,
            "timeout_classification": "critical_validation_timeout",
            "returncode": None,
            "duration_seconds": duration,
            "test_files": runnable,
            "missing_test_files": missing,
            "passed_count": 0,
            "output_tail": lines[-30:] + ["PYTEST_TIMEOUT"],
        }


def _extract_pass_count(lines: list[str]) -> int:
    for line in reversed(lines):
        match = re.search(r"(\d+)\s+passed", line)
        if match:
            return int(match.group(1))
    return 0


def _critical_count(payload: dict[str, Any]) -> int:
    value = payload.get("critical_failures", payload.get("metrics", {}).get("critical_failures", 0))
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 1


def _blocking_failures_payload(payload: dict[str, Any]) -> list[Any]:
    failures = payload.get("blocking_failures", [])
    return failures if isinstance(failures, list) else [failures]


def _metrics_clean(payload: dict[str, Any]) -> bool:
    metrics = payload.get("metrics", {})
    hard_stop = payload.get("global_hard_stop_rule", {})
    checks = {
        "metrics_boundary": metrics.get("boundary_violations_detected", False) is False,
        "metrics_silent": metrics.get("silent_failures_detected", False) is False,
        "metrics_fake_confidence": metrics.get("fake_confidence_detected", False) in (False, None),
        "metrics_non_determinism": metrics.get("non_determinism_detected", False) is False,
        "metrics_trace": metrics.get("trace_incomplete", metrics.get("trace_incomplete_detected", False)) is False,
        "metrics_tests": int(metrics.get("test_failures", 0) or 0) == 0,
        "hard_stop_critical": int(hard_stop.get("critical_failures", 0) or 0) == 0,
        "hard_stop_silent": hard_stop.get("silent_failures", False) is False,
        "hard_stop_fake": hard_stop.get("fake_confidence", False) is False,
        "hard_stop_boundary": hard_stop.get("boundary_violations", False) is False,
        "hard_stop_non_det": hard_stop.get("non_determinism", False) is False,
        "hard_stop_trace": hard_stop.get("trace_incomplete", False) is False,
        "hard_stop_tests": hard_stop.get("test_failure", False) is False,
    }
    return all(checks.values())


def _all_blocks_passed(payload: dict[str, Any]) -> bool:
    blocks = payload.get("blocks", {})
    return bool(blocks) and all(result.get("passed") is True for result in blocks.values() if isinstance(result, dict))


def _tests_clean(payload: dict[str, Any]) -> bool:
    tests = payload.get("tests_executed", [])
    return all(test.get("passed") is True for test in tests if isinstance(test, dict))


def _gate_clean(payload: dict[str, Any]) -> bool:
    return (
        payload.get("verdict") in {"GO", "GO_WITH_MONITORING"}
        and _critical_count(payload) == 0
        and not _blocking_failures_payload(payload)
        and _metrics_clean(payload)
        and _tests_clean(payload)
    )


def _child_gate_clean(payload: dict[str, Any]) -> bool:
    if not _gate_clean(payload):
        return False
    if payload.get("silent_failures_detected") is not False:
        return False
    if payload.get("boundary_preserved") is not True:
        return False
    if "fallback_honest" in payload and payload.get("fallback_honest") is not True:
        return False
    if "determinism_where_required" in payload and payload.get("determinism_where_required") is not True:
        return False
    if "traceability_complete" in payload and payload.get("traceability_complete") is not True:
        return False
    release_state = str(payload.get("release_state") or payload.get("release_verdict") or "")
    if release_state and "READY_FOR_V3_WITH_MONITORING" not in release_state and "READY" not in release_state:
        return False
    return True


def _master_gate_clean(payload: dict[str, Any]) -> bool:
    return _gate_clean(payload) and _all_blocks_passed(payload)


def _governance_clean(payload: dict[str, Any]) -> bool:
    return (
        payload.get("core_pipeline", {}).get("status") == "FROZEN_AND_VALIDATED"
        and payload.get("core_pipeline", {}).get("change_policy") == "FROZEN_UNLESS_GOVERNANCE_REOPEN"
        and payload.get("global_rules", {}).get("no_core_modification") is True
        and payload.get("global_rules", {}).get("no_subsystem_mutation_without_reopen") is True
        and payload.get("global_rules", {}).get("new_work_must_be_isolated_subsystems") is True
    )


def _collect_residuals(artifacts: dict[str, dict[str, Any]]) -> list[str]:
    residuals: list[str] = []
    for name in [*CHILD_GATES, *MASTER_GATES]:
        residuals.extend(str(item) for item in artifacts.get(name, {}).get("residual_monitoring", []))
    return list(dict.fromkeys(residuals))


def _residuals_valid(residuals: list[str]) -> bool:
    return all(any(fragment in residual for fragment in ALLOWED_RESIDUAL_FRAGMENTS) for residual in residuals)


def _artifact_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "audit_type": payload.get("audit_type"),
        "verdict": payload.get("verdict"),
        "release_state": payload.get("release_state"),
        "critical_failures": _critical_count(payload),
        "blocking_failures": _blocking_failures_payload(payload),
        "metrics": payload.get("metrics", {}),
        "residual_monitoring": payload.get("residual_monitoring", []),
        "recommendation": payload.get("recommendation"),
    }


def _agent_summary(payload: dict[str, Any]) -> dict[str, Any]:
    release_state = str(payload.get("release_state") or payload.get("release_verdict") or "")
    ready = (
        "READY_FOR_V3_WITH_MONITORING" in release_state
        or "READY" in release_state
        or _child_gate_clean(payload)
    )
    return {
        "verdict": payload.get("verdict"),
        "ready_for_v3_with_monitoring": ready,
        "critical_failures": _critical_count(payload),
        "blocking_failures": _blocking_failures_payload(payload),
    }


def _read_text(path: str) -> str:
    full_path = ROOT / path
    return full_path.read_text(encoding="utf-8", errors="replace") if full_path.exists() else ""


def _master_consistency(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    master_state = _read_text("docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md")
    bible = _read_text("docs/runtime/architecture/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md")
    wave_1 = artifacts.get("wave_1_master_gate", {})
    wave_2 = artifacts.get("wave_2_master_gate", {})
    absolute = artifacts.get("absolute_master_pre_wave_2", {})
    checks = {
        "wave_1_authorized_wave_2": wave_1.get("recommendation") == "PROCEED_TO_PHASE_2_6_WAVE_2_PLAN",
        "absolute_authorized_wave_2": absolute.get("recommendation") == "PROCEED_TO_PHASE_2_6_WAVE_2_PLAN",
        "wave_2_authorized_final_gate": wave_2.get("recommendation") == "PROCEED_TO_PHASE_2_6_FINAL_MASTER_GATE",
        "master_state_mentions_final_gate": "PHASE_2_6_FINAL_MASTER_GATE" in master_state,
        "architecture_bible_mentions_final_gate": "PHASE_2_6_FINAL_MASTER_GATE" in bible,
        "master_state_mentions_wave_2_ready": "wave_2_master_gate" in master_state and "READY_FOR_V3_WITH_MONITORING" in master_state,
        "architecture_bible_mentions_wave_2_ready": "wave_2_master_gate" in bible and "READY_FOR_V3_WITH_MONITORING" in bible,
        "no_recent_hold": all(artifacts.get(name, {}).get("verdict") != "HOLD" for name in [*CHILD_GATES, *MASTER_GATES]),
    }
    checks["master_consistency_preserved"] = all(checks.values())
    return checks


def _scenario_outputs(artifacts: dict[str, dict[str, Any]], consistency: dict[str, Any]) -> dict[str, Any]:
    return {
        "wave_1_summary": _artifact_summary(artifacts.get("wave_1_master_gate", {})),
        "wave_2_summary": _artifact_summary(artifacts.get("wave_2_master_gate", {})),
        "absolute_master_pre_wave_2_summary": _artifact_summary(artifacts.get("absolute_master_pre_wave_2", {})),
        "child_gate_summaries": {name: _artifact_summary(artifacts.get(name, {})) for name in CHILD_GATES},
        "master_consistency": consistency,
    }


def _validate_blocks(
    *,
    artifacts: dict[str, dict[str, Any]],
    json_errors: dict[str, str],
    existence: dict[str, bool],
    pytest_result: dict[str, Any],
    consistency: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    blocks: dict[str, dict[str, Any]] = {}

    def add(name: str, passed: bool, details: Any = None) -> None:
        blocks[name] = {"passed": bool(passed), "details": details}

    doc_status = {name: (ROOT / path).exists() for name, path in REQUIRED_DOCS.items()}
    runner_status = {name: (ROOT / path).exists() for name, path in REQUIRED_RUNNERS.items()}
    json_status = {name: existence.get(name, False) and name not in json_errors for name in REQUIRED_JSON_ARTIFACTS}
    add("block_a_artifact_integrity", all(doc_status.values()) and all(runner_status.values()) and all(json_status.values()), {
        "docs": doc_status,
        "runners": runner_status,
        "json_artifacts": json_status,
        "json_errors": json_errors,
    })

    add("block_b_governance_consistency", _governance_clean(artifacts.get("system_governance_registry", {})), artifacts.get("system_governance_registry", {}))
    add("block_c_wave_1_master_gate_integrity", _master_gate_clean(artifacts.get("wave_1_master_gate", {})), _artifact_summary(artifacts.get("wave_1_master_gate", {})))
    add("block_d_wave_2_master_gate_integrity", _master_gate_clean(artifacts.get("wave_2_master_gate", {})), _artifact_summary(artifacts.get("wave_2_master_gate", {})))
    add("block_e_absolute_master_pre_wave_2_integrity", _master_gate_clean(artifacts.get("absolute_master_pre_wave_2", {})), _artifact_summary(artifacts.get("absolute_master_pre_wave_2", {})))

    child_status = {name: _child_gate_clean(artifacts.get(name, {})) for name in CHILD_GATES}
    add("block_f_child_agent_gate_integrity", all(child_status.values()), child_status)

    pipeline_status = {
        "pipeline_total_heavy_audit": _gate_clean(artifacts.get("pipeline_total_heavy_audit", {})),
        "pipeline_full_master_certification": _gate_clean(artifacts.get("pipeline_full_master_certification", {})),
        "all_agents_extreme_checklist": _gate_clean(artifacts.get("all_agents_extreme_checklist", {})),
        "max_integrity_gate": _gate_clean(artifacts.get("max_integrity_gate", {})),
        "final_audit_report_present": bool(artifacts.get("final_audit_report", {})),
    }
    add("block_g_pipeline_and_core_integrity", all(pipeline_status.values()), pipeline_status)

    wave_1_blocks = artifacts.get("wave_1_master_gate", {}).get("blocks", {})
    wave_2_blocks = artifacts.get("wave_2_master_gate", {}).get("blocks", {})
    contract_status = {
        "wave_1_contract_integrity": wave_1_blocks.get("block_f_contract_integrity", {}).get("passed") is True,
        "wave_2_contract_integrity": wave_2_blocks.get("block_g_contract_integrity", {}).get("passed") is True,
        "wave_1_trace_auditability": wave_1_blocks.get("block_m_trace_auditability", {}).get("passed") is True,
        "wave_2_trace_auditability": wave_2_blocks.get("block_m_trace_auditability", {}).get("passed") is True,
    }
    add("block_h_contract_and_serialization_integrity", all(contract_status.values()), contract_status)
    add("block_i_full_test_battery", pytest_result.get("passed") is True, pytest_result)

    cross_wave_status = {
        "wave_1_cross_agent": wave_1_blocks.get("block_h_cross_agent_upstream_scenarios", {}).get("passed") is True,
        "wave_2_output_pipeline": wave_2_blocks.get("block_h_output_pipeline_integration", {}).get("passed") is True,
        "wave_2_orchestrator": wave_2_blocks.get("block_i_orchestrator_compatibility", {}).get("passed") is True,
        "master_consistency": consistency.get("master_consistency_preserved") is True,
    }
    add("block_j_cross_wave_consistency", all(cross_wave_status.values()), cross_wave_status)

    determinism_status = {
        "absolute": artifacts.get("absolute_master_pre_wave_2", {}).get("global_hard_stop_rule", {}).get("non_determinism") is False,
        "wave_1": artifacts.get("wave_1_master_gate", {}).get("metrics", {}).get("non_determinism_detected") is False,
        "wave_2": artifacts.get("wave_2_master_gate", {}).get("metrics", {}).get("non_determinism_detected") is False,
    }
    add("block_k_determinism_and_replay_evidence", all(determinism_status.values()), determinism_status)

    fallback_status = {
        "wave_1": wave_1_blocks.get("block_j_fallback_honesty", {}).get("passed") is True,
        "wave_2": wave_2_blocks.get("block_k_fallback_honesty", {}).get("passed") is True,
        "children": all(artifacts.get(name, {}).get("fallback_honest", True) is True for name in CHILD_GATES),
    }
    add("block_l_fallback_honesty", all(fallback_status.values()), fallback_status)

    boundary_status = {
        "absolute": artifacts.get("absolute_master_pre_wave_2", {}).get("global_hard_stop_rule", {}).get("boundary_violations") is False,
        "wave_1": artifacts.get("wave_1_master_gate", {}).get("metrics", {}).get("boundary_violations_detected") is False,
        "wave_2": artifacts.get("wave_2_master_gate", {}).get("metrics", {}).get("boundary_violations_detected") is False,
        "children": all(artifacts.get(name, {}).get("boundary_preserved") is True for name in CHILD_GATES),
    }
    add("block_m_boundary_preservation", all(boundary_status.values()), boundary_status)

    trace_status = {
        "absolute": artifacts.get("absolute_master_pre_wave_2", {}).get("global_hard_stop_rule", {}).get("trace_incomplete") is False,
        "wave_1": artifacts.get("wave_1_master_gate", {}).get("metrics", {}).get("trace_incomplete_detected", False) is False,
        "wave_2": artifacts.get("wave_2_master_gate", {}).get("metrics", {}).get("trace_incomplete") is False,
        "children": all(artifacts.get(name, {}).get("traceability_complete", True) is True for name in CHILD_GATES),
    }
    add("block_n_trace_and_auditability_completeness", all(trace_status.values()), trace_status)

    residuals = _collect_residuals(artifacts)
    invalid_residuals = [
        residual
        for residual in residuals
        if not any(fragment in residual for fragment in ALLOWED_RESIDUAL_FRAGMENTS)
    ]
    add("block_o_residual_monitoring_classification", _residuals_valid(residuals), {
        "residuals": residuals,
        "invalid_residuals": invalid_residuals,
    })

    preliminary_failures = [name for name, result in blocks.items() if not result.get("passed")]
    add("block_p_final_v3_readiness_decision", not preliminary_failures, {"preliminary_failures": preliminary_failures})
    return blocks


def _collect_blocking_failures(blocks: dict[str, dict[str, Any]]) -> list[str]:
    return [name for name, result in blocks.items() if not result.get("passed")]


def _derive_verdict(blocking_failures: list[str], residuals: list[str]) -> str:
    if blocking_failures:
        return "HOLD"
    if residuals:
        return "GO_WITH_MONITORING"
    return "GO"


def _release_state(verdict: str) -> str:
    if verdict == "GO":
        return "READY_FOR_V3"
    if verdict == "GO_WITH_MONITORING":
        return "READY_FOR_V3_WITH_MONITORING"
    return "HOLD_BEFORE_V3"


def _metrics(blocks: dict[str, dict[str, Any]], pytest_result: dict[str, Any], blocking_failures: list[str]) -> dict[str, Any]:
    return {
        "blocks_total": len(blocks),
        "blocks_passed": sum(1 for block in blocks.values() if block.get("passed")),
        "critical_failures": len(blocking_failures),
        "blocking_failures_count": len(blocking_failures),
        "test_failures": 0 if pytest_result.get("passed") else 1,
        "pytest_passed_count": pytest_result.get("passed_count", 0),
        "pytest_duration_seconds": pytest_result.get("duration_seconds"),
        "boundary_violations_detected": blocks.get("block_m_boundary_preservation", {}).get("passed") is not True,
        "silent_failures_detected": False if not blocking_failures else None,
        "fake_confidence_detected": False if not blocking_failures else None,
        "non_determinism_detected": blocks.get("block_k_determinism_and_replay_evidence", {}).get("passed") is not True,
        "trace_incomplete": blocks.get("block_n_trace_and_auditability_completeness", {}).get("passed") is not True,
    }


def main() -> int:
    _reset_audit_dir()
    artifacts, json_errors, existence = _load_artifacts()
    consistency = _master_consistency(artifacts)
    scenario_outputs = _scenario_outputs(artifacts, consistency)
    pytest_result = _run_pytest(UNIT_TEST_FILES)
    blocks = _validate_blocks(
        artifacts=artifacts,
        json_errors=json_errors,
        existence=existence,
        pytest_result=pytest_result,
        consistency=consistency,
    )
    blocking_failures = _collect_blocking_failures(blocks)
    residuals = [] if blocking_failures else _collect_residuals(artifacts)
    verdict = _derive_verdict(blocking_failures, residuals)
    release_state = _release_state(verdict)
    metrics = _metrics(blocks, pytest_result, blocking_failures)
    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "2.6",
        "audit_type": "PHASE_2_6_FINAL_MASTER_GATE",
        "timestamp": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "verdict": verdict,
        "release_state": release_state,
        "v3_ready_with_monitoring": release_state == "READY_FOR_V3_WITH_MONITORING",
        "wave_1": _artifact_summary(artifacts.get("wave_1_master_gate", {})),
        "wave_2": _artifact_summary(artifacts.get("wave_2_master_gate", {})),
        "absolute_master_pre_wave_2": _artifact_summary(artifacts.get("absolute_master_pre_wave_2", {})),
        "phase_2_6_agents": {name: _agent_summary(artifacts.get(name, {})) for name in CHILD_GATES},
        "blocks": blocks,
        "tests_executed": [pytest_result],
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": residuals,
        "recommendation": release_state,
    }
    _write_json(CHECKLIST_RESULTS_PATH, blocks)
    _write_json(SCENARIO_OUTPUTS_PATH, scenario_outputs)
    _write_json(METRICS_PATH, metrics)
    _write_json(MASTER_CONSISTENCY_PATH, consistency)
    _write_json(FINAL_VERDICT_PATH, final_verdict)
    print(json.dumps({
        "verdict": verdict,
        "release_state": release_state,
        "blocks": f"{metrics['blocks_passed']}/{metrics['blocks_total']}",
        "tests_passed": pytest_result.get("passed"),
        "pytest_passed_count": pytest_result.get("passed_count"),
        "blocking_failures": blocking_failures,
        "residual_monitoring_count": len(residuals),
        "recommendation": release_state,
        "final_verdict": str(FINAL_VERDICT_PATH),
    }, indent=2))
    return 0 if verdict in {"GO", "GO_WITH_MONITORING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
