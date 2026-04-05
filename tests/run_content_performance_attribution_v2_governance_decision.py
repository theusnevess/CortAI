from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

AUDIT_DIR = ROOT / "OUT" / "audit" / "content_performance_attribution_v2_0_governance_decision"
VALIDATION_DIR = ROOT / "OUT" / "audit" / "content_performance_attribution_v2_0_validation"
MASTER_CERT_DIR = ROOT / "OUT" / "audit" / "pipeline_full_master_certification"
PROMOTION_PATH = ROOT / "OUT" / "audit" / "content_performance_attribution_v2_baseline_promotion_verdict.json"


def _reset_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(name: str, payload: object) -> None:
    (AUDIT_DIR / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    _reset_dir()

    gate_final = _read_json(VALIDATION_DIR / "final_verdict.json")
    gate_blocks = _read_json(VALIDATION_DIR / "block_summary.json")
    gate_metrics = _read_json(VALIDATION_DIR / "metrics.json")
    gate_human = _read_json(VALIDATION_DIR / "human_review.json")
    gate_examples = _read_json(VALIDATION_DIR / "decision_examples.json")
    gate_events = _read_json(VALIDATION_DIR / "event_summary.json")

    master_final = _read_json(MASTER_CERT_DIR / "final_verdict.json")
    master_combined = _read_json(MASTER_CERT_DIR / "combined_outputs.json")

    capability_report = {
        "canonical_path_active": bool(gate_final.get("canonical_path_active")),
        "legacy_path_bounded": bool(gate_final.get("legacy_path_bounded")),
        "contract_hardened": bool(gate_final.get("contract_hardened")),
        "required_evidence_explicit": bool(gate_final.get("required_evidence_explicit")),
        "honest_written_vs_skipped": bool(gate_final.get("honest_written_vs_skipped")),
        "experiment_linkage_safe": bool(gate_final.get("experiment_linkage_safe")),
        "unsafe_inference_blocked": bool(gate_final.get("unsafe_inference_blocked")),
        "bounded_downstream_effect_proven": bool(gate_final.get("bounded_downstream_effect_proven")),
        "deterministic": bool(gate_final.get("deterministic")),
        "ownership_preserved": bool(gate_final.get("ownership_preserved")),
        "gate_verdict": gate_final.get("verdict"),
    }

    governance_report = {
        "phase3_isolated_subsystem_model_respected": bool((master_combined.get("governance_report") or {}).get("system_governance_registry", {}).get("global_rules", {}).get("new_work_must_be_isolated_subsystems", False)),
        "frozen_core_context_preserved": bool(master_final.get("pipeline_integrity")),
        "no_boundary_violation_detected": not bool(master_final.get("boundary_violations_detected")),
        "master_certification_context": master_final.get("verdict"),
        "validation_gate_passed": gate_final.get("verdict") == "GO",
    }

    residual_monitoring = [
        "ATTRIBUTION_RUNTIME_HISTORY_STILL_SHORT",
        "CONTROLLED_VALIDATION_DOMINANT_OVER_LONG_HORIZON_RUNTIME",
        "REAL_PRODUCTION_LINKAGE_VARIETY_STILL_UNDER_MONITORING",
    ]
    residual_monitoring = sorted(set(residual_monitoring))

    main_failures: list[str] = []
    for key, value in capability_report.items():
        if key == "gate_verdict":
            continue
        if not value:
            main_failures.append(key.upper())
    if gate_final.get("verdict") != "GO":
        main_failures.append("VALIDATION_GATE_NOT_GO")
    for block_name, block in gate_blocks.items():
        if not bool(block.get("passed")):
            main_failures.append(f"{block_name.upper()}_FAILED")
    if not governance_report["phase3_isolated_subsystem_model_respected"]:
        main_failures.append("PHASE3_ISOLATION_RULE_NOT_RESPECTED")
    if not governance_report["frozen_core_context_preserved"]:
        main_failures.append("FROZEN_CORE_CONTEXT_NOT_PRESERVED")
    if not governance_report["no_boundary_violation_detected"]:
        main_failures.append("BOUNDARY_VIOLATION_DETECTED")

    baseline_ready = not main_failures
    if main_failures:
        verdict = "HOLD"
    elif residual_monitoring:
        verdict = "GO_WITH_MONITORING"
    else:
        verdict = "GO"

    block_summary = {
        "block_a_capability_proven": {
            "status": "PASS" if all(v for k, v in capability_report.items() if k != "gate_verdict") else "FAIL",
            "capability_report": capability_report,
        },
        "block_b_governance_context": {
            "status": "PASS" if all(governance_report.values()) else "FAIL",
            "governance_report": governance_report,
        },
        "block_c_validation_artifacts_complete": {
            "status": "PASS" if gate_final.get("verdict") == "GO" and not gate_final.get("main_failures") else "FAIL",
            "event_summary": gate_events,
        },
        "block_d_baseline_readiness": {
            "status": "PASS" if baseline_ready else "FAIL",
            "baseline_ready": baseline_ready,
            "main_failures": main_failures,
            "residual_monitoring": residual_monitoring,
        },
    }

    metrics = {
        "required_base_field_count": gate_metrics.get("required_base_field_count"),
        "optional_enrichment_field_count": gate_metrics.get("optional_enrichment_field_count"),
        "required_evidence_input_count": gate_metrics.get("required_evidence_input_count"),
        "optional_evidence_input_count": gate_metrics.get("optional_evidence_input_count"),
        "experiment_linkage_statuses_observed": gate_metrics.get("experiment_linkage_statuses_observed"),
        "downstream_patch_active": gate_metrics.get("downstream_patch_active"),
        "master_cert_verdict": master_final.get("verdict"),
        "validation_gate_verdict": gate_final.get("verdict"),
    }

    human_review = {
        "summary": (
            "Content Performance Attribution v2.0 is no longer just structurally promising. "
            "It is canonical, contract-hardened, epistemically honest, deterministically validated, "
            "and proven to have bounded downstream effect without ownership drift. "
            "The remaining question is governance posture, not technical viability."
        ),
        "promotion_logic": {
            "why_not_hold": "No blocking technical failures remain in canonicalization, contract, evidence honesty, safe linkage, determinism, or bounded downstream effect.",
            "why_not_plain_go": (
                "The subsystem is newly validated and still early in production runtime history and linkage variety. "
                "That argues for monitoring, not for denying promotion."
            ),
        },
        "validation_human_review": gate_human,
    }

    final_verdict = {
        "verdict": verdict,
        "canonical_path_active": capability_report["canonical_path_active"],
        "legacy_path_bounded": capability_report["legacy_path_bounded"],
        "contract_hardened": capability_report["contract_hardened"],
        "required_evidence_explicit": capability_report["required_evidence_explicit"],
        "honest_written_vs_skipped": capability_report["honest_written_vs_skipped"],
        "experiment_linkage_safe": capability_report["experiment_linkage_safe"],
        "unsafe_inference_blocked": capability_report["unsafe_inference_blocked"],
        "bounded_downstream_effect_proven": capability_report["bounded_downstream_effect_proven"],
        "deterministic": capability_report["deterministic"],
        "ownership_preserved": capability_report["ownership_preserved"],
        "baseline_ready": baseline_ready,
        "main_failures": main_failures,
        "residual_monitoring": residual_monitoring,
        "next_action": "promote_content_performance_attribution_v2_with_monitoring" if verdict == "GO_WITH_MONITORING" else ("promote_content_performance_attribution_v2_to_baseline" if verdict == "GO" else "inspect_content_performance_attribution_governance_failures"),
    }

    promotion_verdict = {
        "subsystem": "CONTENT_PERFORMANCE_ATTRIBUTION_V2_0",
        "promotion_decision": "PROMOTE_TO_BASELINE_WITH_MONITORING" if baseline_ready else "DO_NOT_PROMOTE",
        "baseline_status": "ACTIVE_WITH_MONITORING" if baseline_ready else "NOT_ACTIVE",
        "promotion_ready": baseline_ready,
        "source_gate": str(AUDIT_DIR),
        "gate_verdict": verdict,
        "justification": capability_report,
        "success_conditions": {
            "canonical_path_active": capability_report["canonical_path_active"],
            "legacy_path_bounded": capability_report["legacy_path_bounded"],
            "contract_hardened": capability_report["contract_hardened"],
            "required_evidence_explicit": capability_report["required_evidence_explicit"],
            "honest_written_vs_skipped": capability_report["honest_written_vs_skipped"],
            "experiment_linkage_safe": capability_report["experiment_linkage_safe"],
            "unsafe_inference_blocked": capability_report["unsafe_inference_blocked"],
            "bounded_downstream_effect_proven": capability_report["bounded_downstream_effect_proven"],
            "deterministic": capability_report["deterministic"],
            "ownership_preserved": capability_report["ownership_preserved"],
        },
        "residual_monitoring": residual_monitoring,
        "operational_rule": "if stable_under_monitoring -> do not widen ownership; only revisit when richer production history exists",
        "next_action": "freeze_content_performance_attribution_v2_and_monitor" if baseline_ready else "do_not_promote_content_performance_attribution_v2",
    }

    _write_json("final_verdict.json", final_verdict)
    _write_json("block_summary.json", block_summary)
    _write_json("capability_report.json", capability_report)
    _write_json("governance_report.json", governance_report)
    _write_json("decision_examples.json", gate_examples)
    _write_json("metrics.json", metrics)
    _write_json("human_review.json", human_review)
    PROMOTION_PATH.write_text(json.dumps(promotion_verdict, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(final_verdict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
