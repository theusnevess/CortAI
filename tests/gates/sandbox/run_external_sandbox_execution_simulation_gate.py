from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.publisher.external_sandbox_execution_simulation import (  # noqa: E402
    MISUSE_ATTEMPT_SPECS,
    SIMULATION_PASSED_MEANING,
    ExternalSandboxExecutionSimulation,
    ExternalSandboxExecutionSimulationInput,
)
from app.creative.agents.publisher.external_sandbox_validation_envelope import (  # noqa: E402
    TARGET_MODE,
    TARGET_PLATFORM_ID,
    ExternalSandboxValidationEnvelopeBuilder,
    ExternalSandboxValidationEnvelopeInput,
)
from app.creative.agents.publisher.sandbox_contracts import PRODUCTION_RESIDUALS  # noqa: E402


AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_execution_simulation_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
MISUSE_REVIEW_PATH = AUDIT_DIR / "misuse_attempt_review.json"
ANTI_FAKE_SUCCESS_REVIEW_PATH = AUDIT_DIR / "anti_fake_success_review.json"
STATIC_SCAN_REVIEW_PATH = AUDIT_DIR / "static_scan_review.json"
SIDE_EFFECT_REVIEW_PATH = AUDIT_DIR / "side_effect_review.json"
DETERMINISM_REVIEW_PATH = AUDIT_DIR / "determinism_review.json"
RESIDUAL_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"

PLAN_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "simulation" / "EXTERNAL_SANDBOX_EXECUTION_SIMULATION_PLAN.md"
GATE_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "simulation" / "EXTERNAL_SANDBOX_EXECUTION_SIMULATION_GATE.md"
ENVELOPE_GATE_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_request_envelope_implementation_gate" / "final_verdict.json"
)
ENVELOPE_REVIEW_PATH = ROOT / "docs" / "runtime" / "sandbox" / "envelope" / "EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE_REVIEW.md"

IMPLEMENTATION_FILES = [
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "external_sandbox_execution_simulation.py",
    ROOT / "tests" / "test_external_sandbox_execution_simulation_unittest.py",
]
SOURCE_FILES = IMPLEMENTATION_FILES[:1]

FORBIDDEN_IMPORT_PATTERN = re.compile(
    r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|urllib3|socket|googleapiclient|boto3)\b",
    re.MULTILINE,
)
EXECUTABLE_DEF_PATTERN = re.compile(
    r"^\s*def\s+(to_request|as_request|to_payload|as_payload|to_http|to_headers|to_body|send|execute|post|put|patch|upload|publish|schedule)\s*\(",
    re.MULTILINE,
)
ENDPOINT_CONSTANT_PATTERN = re.compile(
    r"^\s*[A-Z_]*(ENDPOINT|BASE_URL|UPLOAD_URL|PUBLISH_URL|CALLBACK_URL|WEBHOOK_URL)[A-Z_]*\s*=",
    re.MULTILINE,
)


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=True), encoding="utf-8")


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as exc:  # noqa: BLE001 - gate captures read failures as audit evidence
        return {}, f"{type(exc).__name__}: {exc}"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _metadata(**overrides: Any) -> dict[str, Any]:
    payload = {
        "title": "Sandbox title",
        "description": "Sandbox description",
        "tags": ["sandbox", "simulation"],
        "language": "en",
        "visibility_mode": "sandbox_only",
        "account_id": "account_sandbox",
        "runtime_policy_ref": "runtime_policy:sandbox",
        "metadata_trace_ref": "metadata_trace:sandbox",
    }
    payload.update(overrides)
    return payload


def _envelope_input(**overrides: Any) -> ExternalSandboxValidationEnvelopeInput:
    payload = {
        "run_id": "run_simulation_gate",
        "content_id": "content_simulation_gate",
        "artifact_manifest_ref": "artifact_manifest:simulation_gate",
        "metadata_payload_ref": "metadata_payload:simulation_gate",
        "qc_trace_ref": "qc_trace:simulation_gate",
        "account_health_trace_ref": "health_trace:simulation_gate",
        "strategy_ref": "strategy:simulation_gate",
        "publish_eligibility_trace_ref": "publish_eligibility:simulation_gate",
        "metadata": _metadata(),
    }
    payload.update(overrides)
    return ExternalSandboxValidationEnvelopeInput(**payload)


def _simulation_result():
    envelope = ExternalSandboxValidationEnvelopeBuilder().build(_envelope_input())
    return ExternalSandboxExecutionSimulation().simulate(
        ExternalSandboxExecutionSimulationInput(envelope=envelope, envelope_ref="envelope:simulation_gate")
    )


def _scenario(name: str, passed: bool, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "scenario": name,
        "passed": bool(passed),
        "failure_reason": None if passed else "SCENARIO_FAILED",
        "evidence": evidence or {},
    }


def _preconditions() -> dict[str, Any]:
    envelope_gate, envelope_gate_error = _load_json(ENVELOPE_GATE_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [PLAN_DOC_PATH, GATE_DOC_PATH, ENVELOPE_REVIEW_PATH]
    }
    required_prior_artifacts = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [ENVELOPE_GATE_VERDICT_PATH]
    }
    implementation_files = {
        str(path.relative_to(ROOT)): path.exists()
        for path in IMPLEMENTATION_FILES
    }
    checks = {
        "required_docs_present": all(required_docs.values()),
        "required_prior_artifacts_present": all(required_prior_artifacts.values()),
        "implementation_files_present": all(implementation_files.values()),
        "envelope_gate_json_valid": not envelope_gate_error,
        "envelope_gate_verdict_acceptable": envelope_gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "envelope_gate_transport_nullified": envelope_gate.get("transport_capability") == "none"
        and envelope_gate.get("execution_capability") == "none"
        and envelope_gate.get("non_transportable") is True,
        "envelope_gate_no_external_call": envelope_gate.get("external_call_authorized") is False,
        "envelope_gate_no_platform_api": envelope_gate.get("platform_api_called") is False,
        "envelope_gate_no_upload": envelope_gate.get("upload_performed") is False,
        "envelope_gate_no_scheduler": envelope_gate.get("scheduler_invoked") is False,
        "envelope_gate_no_real_publish": envelope_gate.get("real_publishing_performed") is False,
        "envelope_gate_production_residuals_open": envelope_gate.get("production_residuals_closed") is False,
    }
    return {
        "required_docs": required_docs,
        "required_prior_artifacts": required_prior_artifacts,
        "implementation_files": implementation_files,
        "envelope_gate_error": envelope_gate_error,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _static_scan_review() -> dict[str, Any]:
    source_text = "\n".join(_read(path) for path in SOURCE_FILES)
    forbidden_imports = sorted(set(FORBIDDEN_IMPORT_PATTERN.findall(source_text)))
    executable_defs = sorted(set(EXECUTABLE_DEF_PATTERN.findall(source_text)))
    endpoint_constants = sorted(set(match.group(0).strip() for match in ENDPOINT_CONSTANT_PATTERN.finditer(source_text)))
    raw_network_literals = sorted(
        token
        for token in ["requests.", "httpx.", "aiohttp.", "urllib.request.", "urllib3.", "socket.", ".getaddrinfo("]
        if token in source_text
    )
    forbidden_symbols = sorted(
        token
        for token in ["upload_authorized=True", "scheduler_authorized=True", "real_publish_authorized=True"]
        if token in source_text.replace(" ", "")
    )
    checks = {
        "no_http_client_imports": not forbidden_imports,
        "no_sdk_imports": not forbidden_imports,
        "no_endpoint_constants": not endpoint_constants,
        "no_dns_or_network_access": not raw_network_literals,
        "no_upload_scheduler_publish_symbols": not executable_defs and not forbidden_symbols,
        "no_transformation_layer_helpers": not executable_defs,
    }
    return {
        "forbidden_imports": forbidden_imports,
        "executable_defs": executable_defs,
        "endpoint_constants": endpoint_constants,
        "raw_network_literals": raw_network_literals,
        "forbidden_symbols": forbidden_symbols,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _misuse_attempt_review(result: Any) -> dict[str, Any]:
    attempts = result.to_dict()["misuse_attempts"]
    hooks = result.to_dict()["incident_hooks"]
    expected_types = {spec["attempt_type"] for spec in MISUSE_ATTEMPT_SPECS}
    observed_types = {attempt["attempt_type"] for attempt in attempts}
    unblocked_attempts = [attempt for attempt in attempts if attempt["blocked"] is not True]
    checks = {
        "all_required_attempts_present": expected_types <= observed_types,
        "no_extra_missing_attempts": expected_types == observed_types,
        "all_attempts_blocked": not unblocked_attempts,
        "unblocked_attempts_count_zero": result.unblocked_attempts_count == 0,
        "blocked_attempts_count_matches": result.blocked_attempts_count == len(attempts),
        "all_attempts_no_external_call": all(attempt["external_call_authorized"] is False for attempt in attempts),
        "all_attempts_no_upload": all(attempt["upload_authorized"] is False for attempt in attempts),
        "all_attempts_no_scheduler": all(attempt["scheduler_authorized"] is False for attempt in attempts),
        "all_attempts_no_real_publish": all(attempt["real_publish_authorized"] is False for attempt in attempts),
        "all_attempts_not_production_evidence": all(
            attempt["result_evidence_is_production"] is False for attempt in attempts
        ),
        "incident_hooks_present": bool(hooks),
    }
    return {
        "expected_attempt_types": sorted(expected_types),
        "observed_attempt_types": sorted(observed_types),
        "missing_attempt_types": sorted(expected_types - observed_types),
        "unblocked_attempts": unblocked_attempts,
        "incident_hooks_present": bool(hooks),
        "incident_hook_count": len(hooks),
        "checks": checks,
        "passed": all(checks.values()),
    }


def _anti_fake_success_review(result: Any) -> dict[str, Any]:
    payload = result.to_dict()
    checks = {
        "simulation_passed_meaning_bounded": payload["simulation_passed_meaning"] == SIMULATION_PASSED_MEANING,
        "simulation_passed_not_readiness": payload["simulation_passed"] is True
        and payload["external_call_authorized"] is False,
        "simulation_passed_not_success": payload["simulation_passed"] is True
        and payload["real_publish_authorized"] is False,
        "simulation_passed_not_platform_validation": payload["simulation_passed"] is True
        and payload["result_evidence_is_production"] is False,
        "no_simulated_receipt": payload["simulated_receipt_generated"] is False,
        "no_production_receipt": payload["production_receipt_generated"] is False,
        "no_url": payload["published_url"] is None,
        "no_platform_content_id": payload["platform_content_id"] is None,
        "production_residuals_not_closed": payload["production_residuals_closed"] is False,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _side_effect_review(result: Any) -> dict[str, Any]:
    payload = result.to_dict()
    checks = {
        "simulation_only": payload["simulation_only"] is True,
        "external_call_authorized_false": payload["external_call_authorized"] is False,
        "http_client_allowed_false": payload["http_client_allowed"] is False,
        "platform_sdk_allowed_false": payload["platform_sdk_allowed"] is False,
        "endpoint_allowed_false": payload["endpoint_allowed"] is False,
        "network_access_allowed_false": payload["network_access_allowed"] is False,
        "upload_authorized_false": payload["upload_authorized"] is False,
        "scheduler_authorized_false": payload["scheduler_authorized"] is False,
        "real_publish_authorized_false": payload["real_publish_authorized"] is False,
        "transformation_layer_authorized_false": payload["transformation_layer_authorized"] is False,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _determinism_review() -> dict[str, Any]:
    simulator = ExternalSandboxExecutionSimulation()
    first = _simulation_result()
    second = _simulation_result()
    first_json = simulator.deterministic_audit_json(first)
    second_json = simulator.deterministic_audit_json(second)
    checks = {
        "same_input_same_output": first.to_dict() == second.to_dict(),
        "same_input_same_serialization": first_json == second_json,
        "json_serialization_valid": isinstance(json.loads(first_json), dict),
        "stable_attempt_order": [a["attempt_id"] for a in first.misuse_attempts]
        == [a["attempt_id"] for a in second.misuse_attempts],
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_review(result: Any) -> dict[str, Any]:
    residuals = list(result.residual_monitoring)
    checks = {
        "production_publish_evidence_residual_open": "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET" in residuals,
        "platform_integration_residual_open": "PLATFORM_INTEGRATION_NOT_ENABLED" in residuals,
        "publish_result_history_residual_open": "PUBLISH_RESULT_HISTORY_STILL_SHORT" in residuals,
        "production_residuals_closed_false": result.production_residuals_closed is False,
        "residuals_exact": residuals == PRODUCTION_RESIDUALS,
    }
    return {
        "residual_monitoring": residuals,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _run_scenarios(result: Any, static_scan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payload = result.to_dict()
    attempts = {attempt["attempt_type"]: attempt for attempt in payload["misuse_attempts"]}

    def blocked(attempt_type: str) -> bool:
        attempt = attempts.get(attempt_type)
        return bool(attempt and attempt["blocked"] is True)

    scenarios = {
        "clean_envelope_simulation_remains_offline": _scenario(
            "clean_envelope_simulation_remains_offline",
            payload["simulation_only"] is True and payload["external_call_authorized"] is False,
        ),
        "envelope_to_request_transformation_attempt_blocked": _scenario(
            "envelope_to_request_transformation_attempt_blocked", blocked("transform_envelope_into_request")
        ),
        "requests_post_misuse_modeled_and_blocked_without_importing_requests": _scenario(
            "requests_post_misuse_modeled_and_blocked_without_importing_requests",
            blocked("http_client_post_shape") and static_scan["checks"]["no_http_client_imports"],
        ),
        "envelope_valid_readiness_misuse_blocked": _scenario(
            "envelope_valid_readiness_misuse_blocked", blocked("envelope_valid_as_readiness")
        ),
        "future_eligibility_misuse_blocked": _scenario(
            "future_eligibility_misuse_blocked", blocked("future_eligibility_as_permission")
        ),
        "endpoint_injection_blocked": _scenario("endpoint_injection_blocked", blocked("endpoint_injection")),
        "headers_injection_blocked": _scenario("headers_injection_blocked", blocked("headers_injection")),
        "body_injection_blocked": _scenario("body_injection_blocked", blocked("body_injection")),
        "method_injection_blocked": _scenario("method_injection_blocked", blocked("method_injection")),
        "url_injection_blocked": _scenario("url_injection_blocked", blocked("url_injection")),
        "published_url_injection_blocked": _scenario(
            "published_url_injection_blocked", blocked("published_url_injection")
        ),
        "platform_content_id_injection_blocked": _scenario(
            "platform_content_id_injection_blocked", blocked("platform_content_id_injection")
        ),
        "production_receipt_injection_blocked": _scenario(
            "production_receipt_injection_blocked", blocked("production_receipt_injection")
        ),
        "sandbox_receipt_resembling_production_blocked": _scenario(
            "sandbox_receipt_resembling_production_blocked", blocked("sandbox_receipt_resembles_production")
        ),
        "media_bytes_injection_blocked": _scenario(
            "media_bytes_injection_blocked", blocked("media_bytes_injection")
        ),
        "upload_url_injection_blocked": _scenario("upload_url_injection_blocked", blocked("upload_url_injection")),
        "scheduler_job_injection_blocked": _scenario(
            "scheduler_job_injection_blocked", blocked("scheduler_job_injection")
        ),
        "post_publish_metrics_injection_blocked": _scenario(
            "post_publish_metrics_injection_blocked", blocked("post_publish_metrics_injection")
        ),
        "performance_prediction_injection_blocked": _scenario(
            "performance_prediction_injection_blocked", blocked("expected_performance_claim")
        ),
        "attribution_causal_claim_injection_blocked": _scenario(
            "attribution_causal_claim_injection_blocked", blocked("attribution_causal_claim")
        ),
        "residual_closure_attempt_blocked": _scenario(
            "residual_closure_attempt_blocked", blocked("residual_closure_attempt")
        ),
        "simulation_pass_not_success": _scenario(
            "simulation_pass_not_success",
            blocked("simulation_pass_as_publish_success") and payload["real_publish_authorized"] is False,
        ),
        "simulation_pass_not_platform_validation": _scenario(
            "simulation_pass_not_platform_validation",
            blocked("simulation_pass_as_platform_validation") and payload["result_evidence_is_production"] is False,
        ),
        "simulation_pass_not_readiness": _scenario(
            "simulation_pass_not_readiness",
            payload["simulation_passed_meaning"] == SIMULATION_PASSED_MEANING
            and payload["external_call_authorized"] is False,
        ),
        "qc_non_publishable_bypass_blocked": _scenario(
            "qc_non_publishable_bypass_blocked", blocked("qc_non_publishable_bypass")
        ),
        "account_health_hold_bypass_blocked": _scenario(
            "account_health_hold_bypass_blocked", blocked("account_health_hold_bypass")
        ),
        "kill_switch_bypass_blocked": _scenario("kill_switch_bypass_blocked", blocked("kill_switch_bypass")),
        "disabled_rate_limit_bypass_blocked": _scenario(
            "disabled_rate_limit_bypass_blocked", blocked("rate_limit_bypass")
        ),
        "implicit_provider_binding_blocked": _scenario(
            "implicit_provider_binding_blocked", blocked("implicit_provider_binding")
        ),
        "mixed_mode_blocked": _scenario("mixed_mode_blocked", blocked("mixed_mode")),
        "secret_like_field_blocked_and_redacted": _scenario(
            "secret_like_field_blocked_and_redacted", blocked("secret_like_field")
        ),
        "deterministic_replay": _scenario("deterministic_replay", _determinism_review()["passed"]),
        "no_http_client_import": _scenario("no_http_client_import", static_scan["checks"]["no_http_client_imports"]),
        "no_sdk_import": _scenario("no_sdk_import", static_scan["checks"]["no_sdk_imports"]),
        "no_endpoint_constants": _scenario("no_endpoint_constants", static_scan["checks"]["no_endpoint_constants"]),
        "no_dns_network_access": _scenario("no_dns_network_access", static_scan["checks"]["no_dns_or_network_access"]),
        "no_upload_scheduler_publish_symbols": _scenario(
            "no_upload_scheduler_publish_symbols", static_scan["checks"]["no_upload_scheduler_publish_symbols"]
        ),
        "production_residuals_remain_open": _scenario(
            "production_residuals_remain_open", payload["production_residuals_closed"] is False
        ),
    }
    return scenarios


def _build_checklist(
    *,
    preconditions: dict[str, Any],
    scenarios: dict[str, dict[str, Any]],
    misuse: dict[str, Any],
    anti_fake_success: dict[str, Any],
    static_scan: dict[str, Any],
    side_effects: dict[str, Any],
    determinism: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    checks = {
        "preconditions_present": preconditions["passed"],
        "simulation_implementation_present": all(path.exists() for path in IMPLEMENTATION_FILES),
        "simulation_only_result_shape": side_effects["checks"]["simulation_only"],
        "all_misuse_attempts_present": misuse["checks"]["all_required_attempts_present"],
        "all_misuse_attempts_blocked": misuse["checks"]["all_attempts_blocked"],
        "no_transformation_layer": side_effects["checks"]["transformation_layer_authorized_false"],
        "no_http_client": static_scan["checks"]["no_http_client_imports"],
        "no_sdk_client": static_scan["checks"]["no_sdk_imports"],
        "no_endpoint": static_scan["checks"]["no_endpoint_constants"],
        "no_dns_network_access": static_scan["checks"]["no_dns_or_network_access"],
        "no_upload": side_effects["checks"]["upload_authorized_false"],
        "no_scheduler": side_effects["checks"]["scheduler_authorized_false"],
        "no_real_publish": side_effects["checks"]["real_publish_authorized_false"],
        "no_url": anti_fake_success["checks"]["no_url"],
        "no_platform_content_id": anti_fake_success["checks"]["no_platform_content_id"],
        "no_production_receipt": anti_fake_success["checks"]["no_production_receipt"],
        "no_simulated_receipt_resembling_production": anti_fake_success["checks"]["no_simulated_receipt"],
        "simulation_passed_meaning_bounded": anti_fake_success["checks"]["simulation_passed_meaning_bounded"],
        "readiness_misuse_blocked": "envelope_valid_as_readiness" in misuse["observed_attempt_types"],
        "fake_success_blocked": anti_fake_success["checks"]["simulation_passed_not_success"],
        "residual_closure_attempt_blocked": "residual_closure_attempt" in misuse["observed_attempt_types"],
        "qc_bypass_blocked": "qc_non_publishable_bypass" in misuse["observed_attempt_types"],
        "account_health_hold_bypass_blocked": "account_health_hold_bypass" in misuse["observed_attempt_types"],
        "kill_switch_bypass_blocked": "kill_switch_bypass" in misuse["observed_attempt_types"],
        "rate_limit_bypass_blocked": "rate_limit_bypass" in misuse["observed_attempt_types"],
        "no_secret_leakage": "secret_like_field" in misuse["observed_attempt_types"],
        "incident_hooks_present": misuse["incident_hooks_present"],
        "deterministic_replay": determinism["passed"],
        "production_residuals_remain_open": residuals["passed"],
        "all_scenarios_passed": all(item["passed"] for item in scenarios.values()),
    }
    return {
        name: {
            "passed": bool(passed),
            "failure_reason": None if passed else "CHECK_FAILED",
        }
        for name, passed in checks.items()
    }


def _blocking_failures(checklist: dict[str, dict[str, Any]], scenarios: dict[str, dict[str, Any]]) -> list[str]:
    failures = [f"CHECK_FAILED:{name}" for name, item in checklist.items() if not item["passed"]]
    failures.extend(f"SCENARIO_FAILED:{name}" for name, item in scenarios.items() if not item["passed"])
    return sorted(failures)


def main() -> int:
    _reset_audit_dir()
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    result = _simulation_result()
    preconditions = _preconditions()
    static_scan = _static_scan_review()
    misuse = _misuse_attempt_review(result)
    anti_fake_success = _anti_fake_success_review(result)
    side_effects = _side_effect_review(result)
    determinism = _determinism_review()
    residuals = _residual_review(result)
    scenarios = _run_scenarios(result, static_scan)
    checklist = _build_checklist(
        preconditions=preconditions,
        scenarios=scenarios,
        misuse=misuse,
        anti_fake_success=anti_fake_success,
        static_scan=static_scan,
        side_effects=side_effects,
        determinism=determinism,
        residuals=residuals,
    )
    blocking_failures = _blocking_failures(checklist, scenarios)

    scenario_count = len(scenarios)
    scenario_pass_count = sum(1 for item in scenarios.values() if item["passed"])
    checklist_count = len(checklist)
    checklist_pass_count = sum(1 for item in checklist.values() if item["passed"])

    critical_flags = {
        "external_call_authorized": not side_effects["checks"]["external_call_authorized_false"],
        "http_client_detected": not static_scan["checks"]["no_http_client_imports"],
        "platform_sdk_detected": not static_scan["checks"]["no_sdk_imports"],
        "endpoint_detected": not static_scan["checks"]["no_endpoint_constants"],
        "dns_or_network_detected": not static_scan["checks"]["no_dns_or_network_access"],
        "upload_authorized": not side_effects["checks"]["upload_authorized_false"],
        "scheduler_authorized": not side_effects["checks"]["scheduler_authorized_false"],
        "real_publish_authorized": not side_effects["checks"]["real_publish_authorized_false"],
        "transformation_layer_detected": not side_effects["checks"]["transformation_layer_authorized_false"],
        "fake_success_detected": not anti_fake_success["checks"]["simulation_passed_not_success"],
        "fake_receipt_detected": not anti_fake_success["checks"]["no_production_receipt"],
        "real_url_emitted": not anti_fake_success["checks"]["no_url"],
        "platform_content_id_emitted": not anti_fake_success["checks"]["no_platform_content_id"],
        "production_residuals_closed": not residuals["checks"]["production_residuals_closed_false"],
    }

    hold_required = bool(blocking_failures) or any(critical_flags.values())
    verdict = "HOLD" if hold_required else "GO_WITH_MONITORING"
    recommendation = (
        "PROCEED_TO_EXTERNAL_SANDBOX_EXECUTION_SIMULATION_REVIEW"
        if verdict != "HOLD"
        else "HOLD_BEFORE_NEXT_STEP"
    )

    metrics = {
        "critical_failures": sum(1 for value in critical_flags.values() if value),
        "blocking_failures_count": len(blocking_failures),
        "scenario_count": scenario_count,
        "scenario_pass_count": scenario_pass_count,
        "checklist_count": checklist_count,
        "checklist_pass_count": checklist_pass_count,
        "simulation_only": result.simulation_only,
        "all_misuse_attempts_blocked": misuse["checks"]["all_attempts_blocked"],
        "unblocked_attempts_count": result.unblocked_attempts_count,
        **critical_flags,
        "silent_failures_detected": False,
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_EXECUTION_SIMULATION_GATE",
        "verdict": verdict,
        "timestamp": now,
        "simulation_only": result.simulation_only,
        "simulation_implemented": all(path.exists() for path in IMPLEMENTATION_FILES),
        "all_misuse_attempts_blocked": misuse["checks"]["all_attempts_blocked"],
        "unblocked_attempts_count": result.unblocked_attempts_count,
        "simulation_passed_meaning": result.simulation_passed_meaning,
        "external_call_authorized": result.external_call_authorized,
        "http_client_allowed": result.http_client_allowed,
        "platform_sdk_allowed": result.platform_sdk_allowed,
        "endpoint_allowed": result.endpoint_allowed,
        "network_access_allowed": result.network_access_allowed,
        "upload_authorized": result.upload_authorized,
        "scheduler_authorized": result.scheduler_authorized,
        "real_publish_authorized": result.real_publish_authorized,
        "transformation_layer_authorized": result.transformation_layer_authorized,
        "simulated_receipt_generated": result.simulated_receipt_generated,
        "production_receipt_generated": result.production_receipt_generated,
        "real_url_emitted": result.published_url is not None,
        "platform_content_id_emitted": result.platform_content_id is not None,
        "result_evidence_is_production": result.result_evidence_is_production,
        "production_residuals_closed": result.production_residuals_closed,
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": list(PRODUCTION_RESIDUALS),
        "recommendation": recommendation,
    }

    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(METRICS_PATH, metrics)
    _write_json(MISUSE_REVIEW_PATH, misuse)
    _write_json(ANTI_FAKE_SUCCESS_REVIEW_PATH, anti_fake_success)
    _write_json(STATIC_SCAN_REVIEW_PATH, static_scan)
    _write_json(SIDE_EFFECT_REVIEW_PATH, side_effects)
    _write_json(DETERMINISM_REVIEW_PATH, determinism)
    _write_json(RESIDUAL_REVIEW_PATH, residuals)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False, ensure_ascii=True))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
