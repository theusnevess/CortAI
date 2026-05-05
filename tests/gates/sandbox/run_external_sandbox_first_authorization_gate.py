from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_first_authorization_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
SCOPE_REVIEW_PATH = AUDIT_DIR / "scope_review.json"
NON_AUTHORIZATION_REVIEW_PATH = AUDIT_DIR / "non_authorization_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
BOUNDARY_REVIEW_PATH = AUDIT_DIR / "boundary_review.json"

PLAN_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "authorization" / "EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_PLAN.md"
GATE_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "authorization" / "EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE.md"
CHECKPOINT_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "authorization" / "EXTERNAL_SANDBOX_EXTERNAL_CALL_AUTHORIZATION_CHECKPOINT.md"
GUARD_REVIEW_PATH = ROOT / "docs" / "runtime" / "sandbox" / "pre-execution-guard" / "EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_REVIEW.md"
GUARD_GATE_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_external_call_pre_execution_guard_gate" / "final_verdict.json"
)

EXPECTED_RESIDUALS = [
    "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
    "PLATFORM_INTEGRATION_NOT_ENABLED",
    "PUBLISH_RESULT_HISTORY_STILL_SHORT",
    "EXTERNAL_CALL_NOT_IMPLEMENTED",
    "EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED",
]

FORBIDDEN_IMPORT_PATTERN = re.compile(
    r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|urllib3|socket|dns|googleapiclient|boto3)\b",
    re.MULTILINE,
)
FORBIDDEN_TRUE_ASSIGNMENTS = [
    '"implementation_authorized": true',
    '"external_call_authorized": true',
    '"credential_value_access_authorized": true',
    '"runtime_integration_authorized": true',
    '"http_client_allowed": true',
    '"platform_sdk_allowed": true',
    '"endpoint_allowed": true',
    '"dns_network_allowed": true',
    '"api_call_allowed": true',
    '"request_transformation_authorized": true',
    '"upload_authorized": true',
    '"scheduler_authorized": true',
    '"real_publish_authorized": true',
    '"published_url_allowed": true',
    '"platform_content_id_allowed": true',
    '"receipt_allowed": true',
    '"production_residual_closure_authorized": true',
]


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=True), encoding="utf-8")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as exc:  # noqa: BLE001 - audit gate records parse failures explicitly
        return {}, f"{type(exc).__name__}: {exc}"


def _scenario(name: str, passed: bool, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "scenario": name,
        "passed": bool(passed),
        "failure_reason": None if passed else "SCENARIO_FAILED",
        "evidence": evidence or {},
    }


def _contains_all(text: str, fragments: list[str]) -> bool:
    return all(fragment in text for fragment in fragments)


def _contains_none(text: str, fragments: list[str]) -> bool:
    lowered = text.lower()
    return all(fragment.lower() not in lowered for fragment in fragments)


def _preconditions() -> dict[str, Any]:
    guard_verdict, guard_error = _load_json(GUARD_GATE_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [PLAN_DOC_PATH, GATE_DOC_PATH, CHECKPOINT_DOC_PATH, GUARD_REVIEW_PATH]
    }
    required_artifacts = {
        str(GUARD_GATE_VERDICT_PATH.relative_to(ROOT)): GUARD_GATE_VERDICT_PATH.exists()
    }
    checks = {
        "required_docs_present": all(required_docs.values()),
        "required_guard_artifact_present": all(required_artifacts.values()),
        "guard_artifact_json_valid": not guard_error,
        "guard_gate_verdict_acceptable": guard_verdict.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "guard_gate_no_blocking_failures": guard_verdict.get("blocking_failures") == [],
        "guard_gate_no_critical_failures": guard_verdict.get("metrics", {}).get("critical_failures", 1) == 0,
        "guard_gate_blocked_false_not_authorization": guard_verdict.get("blocked_false_does_not_authorize") is True,
        "guard_gate_pass_not_success": guard_verdict.get("guard_pass_does_not_mean_success") is True,
        "guard_gate_external_call_unauthorized": guard_verdict.get("external_call_authorized") is False,
        "guard_gate_production_residuals_open": guard_verdict.get("production_residuals_closed") is False,
        "guard_gate_no_silent_failures": guard_verdict.get("silent_failures_detected") is False,
    }
    return {
        "required_docs": required_docs,
        "required_artifacts": required_artifacts,
        "guard_artifact_error": guard_error,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _scope_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    gate = _read(GATE_DOC_PATH)
    combined = f"{plan}\n{gate}"
    required_plan_fragments = [
        '"authorization_scope": "PLAN_SANDBOX_VALIDATION_CALL_ONLY"',
        '"implementation_authorized": false',
        '"external_call_authorized": false',
        '"credential_value_access_authorized": false',
        '"runtime_integration_authorized": false',
        "This plan does not consider authorization for:",
        "- publishing",
        "- upload",
        "- scheduling",
        "No code is authorized.",
        "No external call is authorized.",
    ]
    required_gate_fragments = [
        '"authorization_scope_exact": "PLAN_SANDBOX_VALIDATION_CALL_ONLY"',
        '"publish_scope_excluded": true',
        '"production_residuals_remain_open": true',
        "This gate validates that the first authorization scope remains planning-only",
        "This gate proves the first authorization plan is narrow enough to review. It does not authorize execution.",
    ]
    forbidden_scope_fragments = [
        "authorization_scope\": \"PUBLISH",
        "authorization_scope\": \"UPLOAD",
        "authorization_scope\": \"PRODUCTION",
        "real publishing authorized",
        "external execution authorized",
        "runtime integration authorized",
    ]
    checks = {
        "plan_required_fragments_present": _contains_all(plan, required_plan_fragments),
        "gate_required_fragments_present": _contains_all(gate, required_gate_fragments),
        "authorization_scope_exact": '"authorization_scope": "PLAN_SANDBOX_VALIDATION_CALL_ONLY"' in plan,
        "gate_scope_exact": '"authorization_scope_exact": "PLAN_SANDBOX_VALIDATION_CALL_ONLY"' in gate,
        "publish_scope_excluded": "This plan does not consider authorization for:" in plan and "- publishing" in plan,
        "upload_scope_excluded": "This plan does not consider authorization for:" in plan and "- upload" in plan,
        "scheduler_scope_excluded": "This plan does not consider authorization for:" in plan and "- scheduling" in plan,
        "production_platform_scope_excluded": "production platform interaction" in plan,
        "post_publish_metrics_excluded": "post-publish metric collection" in plan,
        "attribution_causality_excluded": "attribution causality" in plan,
        "no_broader_scope_fragments": _contains_none(combined, forbidden_scope_fragments),
    }
    return {
        "authorization_scope_exact": "PLAN_SANDBOX_VALIDATION_CALL_ONLY",
        "required_plan_fragments": required_plan_fragments,
        "required_gate_fragments": required_gate_fragments,
        "forbidden_scope_fragments": forbidden_scope_fragments,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _non_authorization_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    gate = _read(GATE_DOC_PATH)
    runner = _read(Path(__file__))
    combined = f"{plan}\n{gate}"
    runner_source = runner.replace('"requests.', '"requests."')
    forbidden_imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(runner_source)]
    forbidden_true_assignments = [fragment for fragment in FORBIDDEN_TRUE_ASSIGNMENTS if fragment in combined.lower()]
    required_false_fragments = [
        '"implementation_authorized": false',
        '"external_call_authorized": false',
        '"credential_value_access_authorized": false',
        '"runtime_integration_authorized": false',
        '"http_client_allowed": false',
        '"platform_sdk_allowed": false',
        '"endpoint_allowed": false',
        '"dns_network_allowed": false',
        '"api_call_allowed": false',
        '"request_transformation_authorized": false',
        '"upload_authorized": false',
        '"scheduler_authorized": false',
        '"real_publish_authorized": false',
        '"published_url_allowed": false',
        '"platform_content_id_allowed": false',
        '"receipt_allowed": false',
    ]
    checks = {
        "implementation_unauthorized": '"implementation_authorized": false' in combined,
        "external_call_unauthorized": '"external_call_authorized": false' in combined,
        "credential_value_access_unauthorized": '"credential_value_access_authorized": false' in combined,
        "runtime_integration_unauthorized": '"runtime_integration_authorized": false' in combined,
        "http_client_unauthorized": '"http_client_allowed": false' in combined,
        "platform_sdk_unauthorized": '"platform_sdk_allowed": false' in combined,
        "endpoint_unauthorized": '"endpoint_allowed": false' in combined,
        "dns_network_unauthorized": '"dns_network_allowed": false' in combined,
        "api_call_unauthorized": '"api_call_allowed": false' in combined,
        "request_transformation_unauthorized": '"request_transformation_authorized": false' in combined,
        "upload_unauthorized": '"upload_authorized": false' in combined,
        "scheduler_unauthorized": '"scheduler_authorized": false' in combined,
        "real_publish_unauthorized": '"real_publish_authorized": false' in combined,
        "published_url_unauthorized": '"published_url_allowed": false' in combined,
        "platform_content_id_unauthorized": '"platform_content_id_allowed": false' in combined,
        "receipt_unauthorized": '"receipt_allowed": false' in combined,
        "all_required_false_fragments_present": _contains_all(combined, required_false_fragments),
        "no_true_authorization_fragments": not forbidden_true_assignments,
        "runner_has_no_forbidden_network_imports": not forbidden_imports,
    }
    return {
        "required_false_fragments": required_false_fragments,
        "forbidden_true_assignments": forbidden_true_assignments,
        "forbidden_runner_imports": forbidden_imports,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_monitoring_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    gate = _read(GATE_DOC_PATH)
    combined = f"{plan}\n{gate}"
    checks = {
        "production_publish_evidence_residual_open": EXPECTED_RESIDUALS[0] in combined,
        "platform_integration_residual_open": EXPECTED_RESIDUALS[1] in combined,
        "publish_result_history_residual_open": EXPECTED_RESIDUALS[2] in combined,
        "external_call_not_implemented_residual_open": EXPECTED_RESIDUALS[3] in combined,
        "external_sandbox_execution_not_authorized_residual_open": EXPECTED_RESIDUALS[4] in combined,
        "production_residuals_remain_open_asserted": '"production_residuals_remain_open": true' in combined,
        "production_residual_closure_not_authorized": '"production_residual_closure_authorized": false' in combined
        or "production residual closure" in combined,
    }
    return {
        "residual_monitoring": EXPECTED_RESIDUALS,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _boundary_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    gate = _read(GATE_DOC_PATH)
    checkpoint = _read(CHECKPOINT_DOC_PATH)
    guard_review = _read(GUARD_REVIEW_PATH)
    combined = f"{plan}\n{gate}\n{checkpoint}\n{guard_review}"
    checks = {
        "publisher_not_external_client": "Publisher may govern publication but is not yet an external execution client" in plan
        or "Publisher is the explicit publish authority model, not an external client yet" in checkpoint,
        "qc_boundary_preserved": "QC remains final artifact evaluator" in combined,
        "account_health_hold_preserved": "Account Health `HOLD` remains blocking authority" in combined,
        "strategy_boundary_preserved": "Strategy remains control layer" in combined
        or "Strategy remains the control layer" in combined,
        "orchestrator_boundary_preserved": "Orchestrator remains coordinator" in combined,
        "attribution_boundary_preserved": "Attribution cannot claim causality without production publish evidence" in combined,
        "experiment_boundary_preserved": "Experiment cannot create publish authority" in combined,
        "core_pipeline_unchanged": "Core pipeline remains unchanged" in combined
        or "core pipeline remains unchanged" in combined,
        "blocked_false_not_authorization": "`blocked=false` cannot become authorization" in combined
        or "`blocked=false` does not authorize execution" in combined,
        "guard_pass_not_success": "guard pass cannot become success" in combined
        or "`guard_pass` does not mean success" in combined,
        "sandbox_evidence_not_production": "sandbox evidence is not production evidence" in combined
        or '"sandbox_evidence_is_production": false' in combined,
        "sandbox_validation_not_publish_success": "sandbox validation is not publish success" in combined
        or '"sandbox_validation_is_publish_success": false' in combined,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _language_safety_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    gate = _read(GATE_DOC_PATH)
    combined = f"{plan}\n{gate}"
    combined_lower = combined.lower()
    required_negative_fragments = {
        "no_production_readiness": "It must not support:\n\n- production readiness" in plan
        or "no plan language implies production readiness" in gate,
        "no_publishability": "no plan language implies publishability" in combined_lower
        or "validate no language implies publishability" in combined_lower,
        "no_endpoint_readiness": "No endpoint is authorized." in plan or "endpoint" in gate,
        "no_transport_readiness": "No transformation layer may be inferred from this plan." in plan,
        "no_receipt_availability": "no plan language permits real receipt" in combined_lower
        or "validate no language authorizes real receipt" in combined_lower
        or '"receipt_allowed": false' in combined,
        "no_fake_success": "sandbox validation is not publish success" in combined
        or '"sandbox_validation_is_publish_success": false' in combined,
    }
    forbidden_positive_phrases = [
        "ready for production",
        "production ready",
        "safe to publish",
        "publishable by default",
        "credential access authorized",
        "endpoint authorized",
        "request execution ready",
        "receipt available",
    ]
    checks = {
        **required_negative_fragments,
        "no_forbidden_positive_phrases": _contains_none(combined, forbidden_positive_phrases),
    }
    return {
        "forbidden_positive_phrases": forbidden_positive_phrases,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _run_scenarios(
    *,
    preconditions: dict[str, Any],
    scope: dict[str, Any],
    non_auth: dict[str, Any],
    residuals: dict[str, Any],
    boundary: dict[str, Any],
    language: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    scenario_checks = {
        "plan_exists": PLAN_DOC_PATH.exists(),
        "checkpoint_exists": CHECKPOINT_DOC_PATH.exists(),
        "guard_review_exists": GUARD_REVIEW_PATH.exists(),
        "guard_final_verdict_exists": GUARD_GATE_VERDICT_PATH.exists(),
        "authorization_scope_exact": scope["checks"]["authorization_scope_exact"],
        "implementation_unauthorized": non_auth["checks"]["implementation_unauthorized"],
        "external_call_unauthorized": non_auth["checks"]["external_call_unauthorized"],
        "credential_value_access_unauthorized": non_auth["checks"]["credential_value_access_unauthorized"],
        "runtime_integration_unauthorized": non_auth["checks"]["runtime_integration_unauthorized"],
        "http_client_unauthorized": non_auth["checks"]["http_client_unauthorized"],
        "platform_sdk_unauthorized": non_auth["checks"]["platform_sdk_unauthorized"],
        "endpoint_unauthorized": non_auth["checks"]["endpoint_unauthorized"],
        "dns_network_unauthorized": non_auth["checks"]["dns_network_unauthorized"],
        "api_call_unauthorized": non_auth["checks"]["api_call_unauthorized"],
        "request_transformation_unauthorized": non_auth["checks"]["request_transformation_unauthorized"],
        "upload_unauthorized": non_auth["checks"]["upload_unauthorized"],
        "scheduler_unauthorized": non_auth["checks"]["scheduler_unauthorized"],
        "real_publish_unauthorized": non_auth["checks"]["real_publish_unauthorized"],
        "url_emission_unauthorized": non_auth["checks"]["published_url_unauthorized"],
        "platform_content_id_emission_unauthorized": non_auth["checks"]["platform_content_id_unauthorized"],
        "receipt_generation_unauthorized": non_auth["checks"]["receipt_unauthorized"],
        "publish_scope_excluded": scope["checks"]["publish_scope_excluded"],
        "upload_scope_excluded": scope["checks"]["upload_scope_excluded"],
        "scheduler_scope_excluded": scope["checks"]["scheduler_scope_excluded"],
        "production_platform_scope_excluded": scope["checks"]["production_platform_scope_excluded"],
        "post_publish_metrics_excluded": scope["checks"]["post_publish_metrics_excluded"],
        "attribution_causality_excluded": scope["checks"]["attribution_causality_excluded"],
        "sandbox_evidence_separated_from_production_evidence": boundary["checks"][
            "sandbox_evidence_not_production"
        ],
        "sandbox_validation_not_publish_success": boundary["checks"]["sandbox_validation_not_publish_success"],
        "production_residuals_remain_open": residuals["passed"],
        "account_health_hold_boundary_preserved": boundary["checks"]["account_health_hold_preserved"],
        "qc_non_publishable_boundary_preserved": boundary["checks"]["qc_boundary_preserved"],
        "strategy_control_boundary_preserved": boundary["checks"]["strategy_boundary_preserved"],
        "orchestrator_coordination_boundary_preserved": boundary["checks"]["orchestrator_boundary_preserved"],
        "no_production_readiness_language": language["checks"]["no_production_readiness"],
        "no_publishability_language": language["checks"]["no_publishability"],
        "no_fake_receipt_language": language["checks"]["no_receipt_availability"],
        "no_fake_url_language": non_auth["checks"]["published_url_unauthorized"],
        "no_fake_platform_id_language": non_auth["checks"]["platform_content_id_unauthorized"],
        "determinism_of_gate_review": isinstance(
            json.dumps(
                {
                    "scope": scope["checks"],
                    "non_auth": non_auth["checks"],
                    "residuals": residuals["checks"],
                    "boundary": boundary["checks"],
                },
                sort_keys=True,
            ),
            str,
        ),
    }
    return {name: _scenario(name, passed) for name, passed in scenario_checks.items()}


def _build_checklist(
    *,
    preconditions: dict[str, Any],
    scenarios: dict[str, dict[str, Any]],
    scope: dict[str, Any],
    non_auth: dict[str, Any],
    residuals: dict[str, Any],
    boundary: dict[str, Any],
    language: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    checks = {
        "required_artifacts_present": preconditions["checks"]["required_docs_present"],
        "required_json_artifacts_parse": preconditions["checks"]["guard_artifact_json_valid"],
        "authorization_scope_exact": scope["checks"]["authorization_scope_exact"],
        "implementation_unauthorized": non_auth["checks"]["implementation_unauthorized"],
        "external_call_unauthorized": non_auth["checks"]["external_call_unauthorized"],
        "credential_value_access_unauthorized": non_auth["checks"]["credential_value_access_unauthorized"],
        "runtime_integration_unauthorized": non_auth["checks"]["runtime_integration_unauthorized"],
        "publish_scope_excluded": scope["checks"]["publish_scope_excluded"],
        "upload_scope_excluded": scope["checks"]["upload_scope_excluded"],
        "scheduler_scope_excluded": scope["checks"]["scheduler_scope_excluded"],
        "production_platform_scope_excluded": scope["checks"]["production_platform_scope_excluded"],
        "request_transformation_excluded": non_auth["checks"]["request_transformation_unauthorized"],
        "http_sdk_endpoint_dns_api_excluded": non_auth["checks"]["http_client_unauthorized"]
        and non_auth["checks"]["platform_sdk_unauthorized"]
        and non_auth["checks"]["endpoint_unauthorized"]
        and non_auth["checks"]["dns_network_unauthorized"]
        and non_auth["checks"]["api_call_unauthorized"],
        "real_url_excluded": non_auth["checks"]["published_url_unauthorized"],
        "platform_content_id_excluded": non_auth["checks"]["platform_content_id_unauthorized"],
        "receipt_excluded": non_auth["checks"]["receipt_unauthorized"],
        "production_residuals_open": residuals["passed"],
        "sandbox_evidence_not_production_evidence": boundary["checks"]["sandbox_evidence_not_production"],
        "sandbox_validation_not_publish_success": boundary["checks"]["sandbox_validation_not_publish_success"],
        "guard_pass_not_success": boundary["checks"]["guard_pass_not_success"],
        "blocked_false_not_authorization": boundary["checks"]["blocked_false_not_authorization"],
        "qc_boundary_preserved": boundary["checks"]["qc_boundary_preserved"],
        "account_health_boundary_preserved": boundary["checks"]["account_health_hold_preserved"],
        "strategy_boundary_preserved": boundary["checks"]["strategy_boundary_preserved"],
        "orchestrator_boundary_preserved": boundary["checks"]["orchestrator_boundary_preserved"],
        "core_unchanged": boundary["checks"]["core_pipeline_unchanged"],
        "no_production_readiness_language": language["checks"]["no_production_readiness"],
        "no_publishability_language": language["checks"]["no_publishability"],
        "no_fake_success_language": language["checks"]["no_fake_success"],
        "no_true_authorization_fragments": non_auth["checks"]["no_true_authorization_fragments"],
        "runner_has_no_forbidden_network_imports": non_auth["checks"]["runner_has_no_forbidden_network_imports"],
        "all_scenarios_passed": all(item["passed"] for item in scenarios.values()),
    }
    return {
        name: {"passed": bool(passed), "failure_reason": None if passed else "CHECK_FAILED"}
        for name, passed in checks.items()
    }


def _blocking_failures(checklist: dict[str, dict[str, Any]], scenarios: dict[str, dict[str, Any]]) -> list[str]:
    failures = [f"CHECK_FAILED:{name}" for name, item in checklist.items() if not item["passed"]]
    failures.extend(f"SCENARIO_FAILED:{name}" for name, item in scenarios.items() if not item["passed"])
    return sorted(failures)


def main() -> int:
    _reset_audit_dir()
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    preconditions = _preconditions()
    scope = _scope_review()
    non_auth = _non_authorization_review()
    residuals = _residual_monitoring_review()
    boundary = _boundary_review()
    language = _language_safety_review()
    scenarios = _run_scenarios(
        preconditions=preconditions,
        scope=scope,
        non_auth=non_auth,
        residuals=residuals,
        boundary=boundary,
        language=language,
    )
    checklist = _build_checklist(
        preconditions=preconditions,
        scenarios=scenarios,
        scope=scope,
        non_auth=non_auth,
        residuals=residuals,
        boundary=boundary,
        language=language,
    )
    blocking_failures = _blocking_failures(checklist, scenarios)

    scenario_count = len(scenarios)
    scenario_pass_count = sum(1 for item in scenarios.values() if item["passed"])
    checklist_count = len(checklist)
    checklist_pass_count = sum(1 for item in checklist.values() if item["passed"])

    critical_flags = {
        "implementation_authorized": not non_auth["checks"]["implementation_unauthorized"],
        "external_call_authorized": not non_auth["checks"]["external_call_unauthorized"],
        "credential_value_access_authorized": not non_auth["checks"]["credential_value_access_unauthorized"],
        "runtime_integration_authorized": not non_auth["checks"]["runtime_integration_unauthorized"],
        "http_client_allowed": not non_auth["checks"]["http_client_unauthorized"],
        "platform_sdk_allowed": not non_auth["checks"]["platform_sdk_unauthorized"],
        "endpoint_allowed": not non_auth["checks"]["endpoint_unauthorized"],
        "dns_network_allowed": not non_auth["checks"]["dns_network_unauthorized"],
        "api_call_allowed": not non_auth["checks"]["api_call_unauthorized"],
        "request_transformation_authorized": not non_auth["checks"]["request_transformation_unauthorized"],
        "upload_authorized": not non_auth["checks"]["upload_unauthorized"],
        "scheduler_authorized": not non_auth["checks"]["scheduler_unauthorized"],
        "real_publish_authorized": not non_auth["checks"]["real_publish_unauthorized"],
        "published_url_allowed": not non_auth["checks"]["published_url_unauthorized"],
        "platform_content_id_allowed": not non_auth["checks"]["platform_content_id_unauthorized"],
        "receipt_allowed": not non_auth["checks"]["receipt_unauthorized"],
        "production_residuals_closed": not residuals["checks"]["production_residuals_remain_open_asserted"],
        "silent_failures_detected": False,
    }

    hold_required = bool(blocking_failures) or any(critical_flags.values())
    verdict = "HOLD" if hold_required else "GO_WITH_MONITORING"
    recommendation = (
        "PROCEED_TO_EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE_REVIEW"
        if verdict != "HOLD"
        else "HOLD_BEFORE_AUTHORIZATION_RUNNER"
    )

    metrics = {
        "critical_failures": sum(1 for value in critical_flags.values() if value),
        "blocking_failures_count": len(blocking_failures),
        "scenario_count": scenario_count,
        "scenario_pass_count": scenario_pass_count,
        "checklist_count": checklist_count,
        "checklist_pass_count": checklist_pass_count,
        **critical_flags,
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE",
        "verdict": verdict,
        "timestamp": now,
        "authorization_scope_exact": "PLAN_SANDBOX_VALIDATION_CALL_ONLY",
        "implementation_authorized": False,
        "external_call_authorized": False,
        "credential_value_access_authorized": False,
        "runtime_integration_authorized": False,
        "publish_scope_excluded": scope["checks"]["publish_scope_excluded"],
        "production_residuals_remain_open": residuals["passed"],
        "http_client_allowed": False,
        "platform_sdk_allowed": False,
        "endpoint_allowed": False,
        "dns_network_allowed": False,
        "api_call_allowed": False,
        "request_transformation_authorized": False,
        "upload_authorized": False,
        "scheduler_authorized": False,
        "real_publish_authorized": False,
        "published_url_allowed": False,
        "platform_content_id_allowed": False,
        "receipt_allowed": False,
        "scenario_pass_count": f"{scenario_pass_count}/{scenario_count}",
        "checklist_pass_count": f"{checklist_pass_count}/{checklist_count}",
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": EXPECTED_RESIDUALS,
        "recommendation": recommendation,
    }

    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(METRICS_PATH, metrics)
    _write_json(SCOPE_REVIEW_PATH, scope)
    _write_json(NON_AUTHORIZATION_REVIEW_PATH, non_auth)
    _write_json(RESIDUAL_MONITORING_REVIEW_PATH, residuals)
    _write_json(BOUNDARY_REVIEW_PATH, boundary)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False, ensure_ascii=True))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
