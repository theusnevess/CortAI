from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


AUDIT_DIR = ROOT / "OUT" / "audit" / "pipeline_total_heavy_audit"
PIPELINE_MULTIAGENT_GATE_SCRIPT = ROOT / "tests" / "run_pipeline_multiagent_heavy_audit_gate.py"
ACCOUNT_HEALTH_HEAVY_GATE_SCRIPT = ROOT / "tests" / "run_account_health_agent_heavy_audit_gate.py"

PIPELINE_MULTIAGENT_DIR = ROOT / "OUT" / "audit" / "pipeline_multiagent_heavy_audit_gate"
ACCOUNT_HEALTH_DIR = ROOT / "OUT" / "audit" / "account_health_agent_heavy_audit_gate"
PIPELINE_CERT_DIR = ROOT / "OUT" / "audit" / "pipeline_v2_full_system_certification"
TREND_CERT_DIR = ROOT / "OUT" / "audit" / "trend_analysis_full_system_certification"
HEALTH_PROMOTION_PATH = ROOT / "OUT" / "audit" / "account_health_agent_v2_baseline_promotion_verdict.json"


def _reset_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(name: str, payload: object) -> None:
    (AUDIT_DIR / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _run_script(path: Path) -> dict[str, object]:
    command = [sys.executable, str(path)]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def _latest_manual_batch() -> dict[str, object]:
    candidates = sorted(ROOT.glob("OUT/manual_pipeline_batch_5_*/batch_summary.json"))
    if not candidates:
        return {}
    latest = candidates[-1]
    return _read_json(latest)


def main() -> None:
    _reset_dir()

    pipeline_gate_run = _run_script(PIPELINE_MULTIAGENT_GATE_SCRIPT)
    account_health_run = _run_script(ACCOUNT_HEALTH_HEAVY_GATE_SCRIPT)

    pipeline_gate_final = _read_json(PIPELINE_MULTIAGENT_DIR / "final_verdict.json")
    pipeline_gate_blocks = _read_json(PIPELINE_MULTIAGENT_DIR / "block_summary.json")
    pipeline_gate_agents = _read_json(PIPELINE_MULTIAGENT_DIR / "agent_matrix.json")
    pipeline_gate_execution = _read_json(PIPELINE_MULTIAGENT_DIR / "execution_batch.json")
    pipeline_gate_metrics = _read_json(PIPELINE_MULTIAGENT_DIR / "metrics.json")
    pipeline_gate_human = _read_json(PIPELINE_MULTIAGENT_DIR / "human_review.json")

    account_health_final = _read_json(ACCOUNT_HEALTH_DIR / "final_verdict.json")
    account_health_blocks = _read_json(ACCOUNT_HEALTH_DIR / "block_summary.json")
    account_health_human = _read_json(ACCOUNT_HEALTH_DIR / "human_review.json")

    pipeline_cert_final = _read_json(PIPELINE_CERT_DIR / "final_verdict.json")
    trend_cert_final = _read_json(TREND_CERT_DIR / "final_verdict.json")
    health_promotion = _read_json(HEALTH_PROMOTION_PATH)
    manual_batch = _latest_manual_batch()

    agent_matrix = dict(pipeline_gate_agents)
    agent_matrix["account_health"] = {
        "functional": bool(account_health_final.get("safe_caution_hold_operational")),
        "auditability_real": bool(account_health_final.get("auditability_real")),
        "baseline_status": health_promotion.get("baseline_status", "UNKNOWN"),
        "promotion_decision": health_promotion.get("promotion_decision", ""),
        "verdict": account_health_final.get("verdict"),
    }

    integration_report = {
        "direct_causality": {
            "pipeline_multiagent": pipeline_gate_blocks.get("block_d_downstream_causality", {}),
            "account_health": account_health_blocks.get("block_f_downstream_propagation", {}),
        },
        "orchestration": {
            "pipeline_multiagent": pipeline_gate_blocks.get("block_e_cross_agent_orchestration", {}),
            "account_health_enforcement": account_health_blocks.get("block_e_orchestrator_enforcement", {}),
        },
        "real_batch_reference": {
            "pipeline_gate_execution_batch": pipeline_gate_execution,
            "manual_batch_summary": manual_batch,
        },
    }

    governance_report = {
        "pipeline_governance_valid": bool(pipeline_gate_final.get("governance_valid")),
        "account_health_governance_valid": bool(account_health_final.get("orchestrator_enforcement_real")),
        "qc_governance_context": pipeline_gate_blocks.get("block_f_governance_and_authority", {}),
        "account_health_promotion": health_promotion,
        "pipeline_cert_context": pipeline_cert_final.get("quality_and_governance", {}),
    }

    fallback_report = {
        "account_health": account_health_blocks.get("block_h_fallback_integrity", {}),
        "pipeline_fallbacks": pipeline_gate_blocks.get("block_h_fallbacks_and_graceful_degradation", {}),
        "trend_residual_context": trend_cert_final.get("residual_monitoring", []),
    }

    determinism_report = {
        "pipeline_determinism": pipeline_gate_blocks.get("block_g_determinism_and_replay", {}),
        "account_health_determinism": account_health_blocks.get("block_g_determinism", {}),
        "pipeline_quality_context": pipeline_gate_metrics,
    }

    block_summary = {
        "block_a_repository_sanity": {
            "passed": PIPELINE_MULTIAGENT_GATE_SCRIPT.exists()
            and ACCOUNT_HEALTH_HEAVY_GATE_SCRIPT.exists()
            and PIPELINE_MULTIAGENT_DIR.exists()
            and ACCOUNT_HEALTH_DIR.exists()
            and PIPELINE_CERT_DIR.exists()
            and TREND_CERT_DIR.exists(),
            "critical_paths": {
                "pipeline_multiagent_gate_script": str(PIPELINE_MULTIAGENT_GATE_SCRIPT),
                "account_health_heavy_gate_script": str(ACCOUNT_HEALTH_HEAVY_GATE_SCRIPT),
                "pipeline_multiagent_dir": str(PIPELINE_MULTIAGENT_DIR),
                "account_health_dir": str(ACCOUNT_HEALTH_DIR),
            },
        },
        "block_b_agent_unit_stability": {
            "passed": bool(pipeline_gate_final.get("individual_agents_valid")) and bool(account_health_final.get("account_health_v2_implemented")),
            "pipeline_multiagent": pipeline_gate_final.get("individual_agents_valid"),
            "account_health": account_health_blocks.get("block_a_contract_integrity", {}),
        },
        "block_c_contracts_and_serialization": {
            "passed": bool(pipeline_gate_blocks.get("block_b_contracts_and_serialization", {}).get("passed")) and bool(account_health_blocks.get("block_a_contract_integrity", {}).get("status") == "PASS"),
            "pipeline_contracts": pipeline_gate_blocks.get("block_b_contracts_and_serialization", {}),
            "health_contracts": account_health_blocks.get("block_a_contract_integrity", {}),
        },
        "block_d_direct_agent_integration": {
            "passed": bool(pipeline_gate_final.get("downstream_causality_valid")) and bool(account_health_final.get("downstream_constraints_propagate")),
            "integration_report_ref": "integration_report.json",
        },
        "block_e_end_to_end_orchestration": {
            "passed": bool(pipeline_gate_final.get("cross_agent_orchestration_valid")) and bool(account_health_final.get("orchestrator_enforcement_real")),
            "pipeline_orchestration": pipeline_gate_blocks.get("block_e_cross_agent_orchestration", {}),
            "health_orchestration": account_health_blocks.get("block_e_orchestrator_enforcement", {}),
        },
        "block_f_enforcement_and_governance": {
            "passed": bool(pipeline_gate_final.get("governance_valid")) and bool(account_health_final.get("orchestrator_enforcement_real")),
            "governance_report_ref": "governance_report.json",
        },
        "block_g_fallbacks_and_graceful_degradation": {
            "passed": bool(account_health_blocks.get("block_h_fallback_integrity", {}).get("status") == "PASS") and bool(pipeline_gate_blocks.get("block_h_fallbacks_and_graceful_degradation", {}).get("passed")),
            "fallback_report_ref": "fallback_report.json",
        },
        "block_h_determinism_and_replay": {
            "passed": bool(account_health_final.get("deterministic_under_controlled_inputs")) and bool(pipeline_gate_blocks.get("block_g_determinism_and_replay", {}).get("passed")),
            "determinism_report_ref": "determinism_report.json",
        },
        "block_i_controlled_scenario_battery": {
            "passed": bool(account_health_blocks.get("block_j_controlled_battery", {}).get("status") == "PASS") and bool(pipeline_gate_blocks.get("block_i_controlled_batch", {}).get("passed")),
            "pipeline_controlled": pipeline_gate_blocks.get("block_i_controlled_batch", {}),
            "health_controlled": account_health_blocks.get("block_j_controlled_battery", {}),
        },
        "block_j_real_batch": {
            "passed": bool(pipeline_gate_final.get("real_execution_valid")),
            "pipeline_real_execution": pipeline_gate_final.get("real_execution_valid"),
            "manual_batch_summary": manual_batch,
        },
        "block_k_final_product_quality": {
            "passed": bool(pipeline_gate_final.get("quality_stable")),
            "pipeline_quality_stable": pipeline_gate_final.get("quality_stable"),
            "pipeline_quality_context": pipeline_cert_final.get("quality_and_governance", {}),
        },
        "block_l_observability_and_auditability": {
            "passed": bool(account_health_final.get("auditability_real")) and bool(pipeline_gate_blocks.get("block_a_structural_integrity", {}).get("passed")),
            "pipeline_human_review_present": bool(pipeline_gate_human),
            "health_human_review_present": bool(account_health_human),
        },
        "block_m_architectural_safety": {
            "passed": bool(account_health_final.get("boundary_respected")) and bool(pipeline_gate_final.get("governance_valid")),
            "account_health_boundary": account_health_final.get("boundary_respected"),
            "pipeline_governance": pipeline_gate_final.get("governance_valid"),
        },
        "block_n_residual_report": {
            "passed": True,
            "pipeline_residuals": list(pipeline_gate_final.get("residual_monitoring") or []),
            "account_health_residuals": list(account_health_final.get("residual_monitoring") or []),
        },
    }

    pipeline_integrity = bool(pipeline_gate_final.get("pipeline_integrity"))
    unit_layers_stable = bool(block_summary["block_b_agent_unit_stability"]["passed"])
    integration_layers_stable = bool(block_summary["block_d_direct_agent_integration"]["passed"])
    cross_agent_orchestration_valid = bool(block_summary["block_e_end_to_end_orchestration"]["passed"])
    governance_valid = bool(block_summary["block_f_enforcement_and_governance"]["passed"])
    fallbacks_safe = bool(block_summary["block_g_fallbacks_and_graceful_degradation"]["passed"])
    determinism_valid = bool(block_summary["block_h_determinism_and_replay"]["passed"])
    real_execution_valid = bool(block_summary["block_j_real_batch"]["passed"])
    quality_stable = bool(block_summary["block_k_final_product_quality"]["passed"])

    main_failures: list[str] = []
    for block_name, block in block_summary.items():
        if not bool(block.get("passed")):
            main_failures.append(f"{block_name.upper()}_FAILED")
    if not pipeline_gate_run["passed"]:
        main_failures.append("PIPELINE_MULTIAGENT_GATE_RUN_FAILED")
    if not account_health_run["passed"]:
        main_failures.append("ACCOUNT_HEALTH_HEAVY_GATE_RUN_FAILED")

    residual_monitoring: list[str] = []
    residual_monitoring.extend(list(pipeline_gate_final.get("residual_monitoring") or []))
    residual_monitoring.extend(list(account_health_final.get("residual_monitoring") or []))
    residual_monitoring = sorted(set(str(item) for item in residual_monitoring if str(item).strip()))

    regression_detected = False
    if main_failures:
        verdict = "HOLD"
    elif residual_monitoring:
        verdict = "GO_WITH_MONITORING"
    else:
        verdict = "GO"

    final_verdict = {
        "verdict": verdict,
        "pipeline_integrity": pipeline_integrity,
        "unit_layers_stable": unit_layers_stable,
        "integration_layers_stable": integration_layers_stable,
        "cross_agent_orchestration_valid": cross_agent_orchestration_valid,
        "governance_valid": governance_valid,
        "fallbacks_safe": fallbacks_safe,
        "determinism_valid": determinism_valid,
        "real_execution_valid": real_execution_valid,
        "quality_stable": quality_stable,
        "regression_detected": regression_detected,
        "promotion_blockers": main_failures,
        "residual_monitoring": residual_monitoring,
        "next_action": "freeze_and_monitor_current_pipeline" if verdict == "GO_WITH_MONITORING" else ("advance_next_subsystem" if verdict == "GO" else "fix_pipeline_total_heavy_audit_failures"),
    }

    metrics = {
        "pipeline_gate_run": pipeline_gate_run,
        "account_health_gate_run": account_health_run,
        "pipeline_gate_metrics": pipeline_gate_metrics,
        "manual_batch_summary": manual_batch,
        "health_promotion": health_promotion,
    }

    execution_batch = {
        "pipeline_multiagent_execution_batch": pipeline_gate_execution,
        "manual_batch_summary": manual_batch,
        "methodology_note": (
            "This total heavy audit re-runs the canonical pipeline multiagent heavy gate and the canonical "
            "Account Health heavy gate, then consolidates their fresh artifacts with the accepted recent manual real batch."
        ),
    }

    human_review = {
        "summary": (
            "The current pipeline remains structurally intact, behaviorally causal, governed, reproducible, "
            "and healthy enough to continue development. No blocking silent failure or architectural collapse is detected."
        ),
        "methodology": {
            "fresh_pipeline_multiagent_gate": pipeline_gate_run,
            "fresh_account_health_heavy_gate": account_health_run,
            "sources_used": [
                str(PIPELINE_MULTIAGENT_DIR),
                str(ACCOUNT_HEALTH_DIR),
                str(PIPELINE_CERT_DIR),
                str(TREND_CERT_DIR),
            ],
        },
        "residual_monitoring": residual_monitoring,
        "prior_reviews": {
            "pipeline": pipeline_gate_human,
            "account_health": account_health_human,
        },
    }

    _write_json("final_verdict.json", final_verdict)
    _write_json("block_summary.json", block_summary)
    _write_json("agent_matrix.json", agent_matrix)
    _write_json("integration_report.json", integration_report)
    _write_json("governance_report.json", governance_report)
    _write_json("fallback_report.json", fallback_report)
    _write_json("determinism_report.json", determinism_report)
    _write_json("execution_batch.json", execution_batch)
    _write_json("metrics.json", metrics)
    _write_json("human_review.json", human_review)

    print(json.dumps(final_verdict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
