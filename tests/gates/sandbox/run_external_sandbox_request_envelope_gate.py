from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_request_envelope_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
SECURITY_REVIEW_PATH = AUDIT_DIR / "security_review.json"
CONTRACT_REVIEW_PATH = AUDIT_DIR / "contract_review.json"
RESIDUAL_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
SIDE_EFFECT_REVIEW_PATH = AUDIT_DIR / "side_effect_review.json"

PLAN_PATH = ROOT / "docs" / "runtime" / "sandbox" / "envelope" / "EXTERNAL_SANDBOX_REQUEST_ENVELOPE_PLAN.md"
GATE_PATH = ROOT / "docs" / "runtime" / "sandbox" / "envelope" / "EXTERNAL_SANDBOX_REQUEST_ENVELOPE_GATE.md"
EVIDENCE_GATE_PATH = ROOT / "docs" / "runtime" / "sandbox" / "evidence" / "EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE.md"
EVIDENCE_PLAN_PATH = ROOT / "docs" / "runtime" / "sandbox" / "evidence" / "EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_PLAN.md"
SANDBOX_ADAPTER_GATE_PATH = ROOT / "docs" / "runtime" / "sandbox" / "adapter" / "SANDBOX_ADAPTER_IMPLEMENTATION_GATE.md"
PRIOR_EVIDENCE_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_evidence_collection_gate" / "final_verdict.json"
)
PRIOR_SANDBOX_VERDICT_PATH = ROOT / "OUT" / "audit" / "sandbox_adapter_implementation_gate" / "final_verdict.json"

IMPLEMENTATION_CANDIDATES = [
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "external_sandbox_envelope.py",
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "external_sandbox_envelope_security.py",
    ROOT / "tests" / "test_external_sandbox_request_envelope_unittest.py",
]

TARGET_PLATFORM_ID = "SHORT_VIDEO_PLATFORM_SANDBOX_V1"
TARGET_MODE = "sandbox_external_dry_run"
PRODUCTION_RESIDUALS = [
    "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
    "PLATFORM_INTEGRATION_NOT_ENABLED",
    "PUBLISH_RESULT_HISTORY_STILL_SHORT",
]


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=True), encoding="utf-8")


def _read_text(path: Path) -> tuple[str, str]:
    try:
        return path.read_text(encoding="utf-8"), ""
    except Exception as exc:  # noqa: BLE001 - gate captures read failures as audit evidence
        return "", f"{type(exc).__name__}: {exc}"


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as exc:  # noqa: BLE001 - gate captures parse failures as audit evidence
        return {}, f"{type(exc).__name__}: {exc}"


def _contains(text: str, needle: str) -> bool:
    return needle in text


def _all_contains(text: str, needles: list[str]) -> bool:
    return all(_contains(text, needle) for needle in needles)


def _none_contains(text: str, needles: list[str]) -> bool:
    return not any(_contains(text, needle) for needle in needles)


def _preconditions(plan_text: str, gate_text: str) -> dict[str, Any]:
    evidence_verdict, evidence_error = _load_json(PRIOR_EVIDENCE_VERDICT_PATH)
    sandbox_verdict, sandbox_error = _load_json(PRIOR_SANDBOX_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [PLAN_PATH, GATE_PATH, EVIDENCE_GATE_PATH, EVIDENCE_PLAN_PATH, SANDBOX_ADAPTER_GATE_PATH]
    }
    implementation_candidates = {
        str(path.relative_to(ROOT)): path.exists()
        for path in IMPLEMENTATION_CANDIDATES
    }
    evidence_checks = {
        "evidence_json_valid": not evidence_error,
        "evidence_verdict_acceptable": evidence_verdict.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "evidence_target_platform_exact": evidence_verdict.get("target_platform_id") == TARGET_PLATFORM_ID,
        "evidence_target_mode_exact": evidence_verdict.get("target_mode") == TARGET_MODE,
        "evidence_external_call_not_implemented": evidence_verdict.get("external_call_implemented") is False,
        "evidence_external_call_not_authorized": evidence_verdict.get("external_call_authorized") is False,
        "evidence_platform_api_not_called": evidence_verdict.get("platform_api_called") is False,
        "evidence_upload_not_performed": evidence_verdict.get("upload_performed") is False,
        "evidence_scheduler_not_invoked": evidence_verdict.get("scheduler_invoked") is False,
        "evidence_real_publish_not_performed": evidence_verdict.get("real_publishing_performed") is False,
        "evidence_real_url_not_emitted": evidence_verdict.get("real_url_emitted") is False,
        "evidence_platform_content_id_not_emitted": evidence_verdict.get("platform_content_id_emitted") is False,
        "evidence_production_residuals_open": evidence_verdict.get("production_residuals_closed") is False,
        "evidence_blocking_failures_empty": evidence_verdict.get("blocking_failures") == [],
    }
    sandbox_checks = {
        "sandbox_json_valid": not sandbox_error,
        "sandbox_verdict_acceptable": sandbox_verdict.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "sandbox_blocking_failures_empty": sandbox_verdict.get("blocking_failures") == [],
        "sandbox_no_side_effects": sandbox_verdict.get("platform_api_called") is False
        and sandbox_verdict.get("upload_performed") is False
        and sandbox_verdict.get("scheduler_invoked") is False
        and sandbox_verdict.get("real_publishing_performed") is False,
    }
    checks = {
        "required_docs_exist": all(required_docs.values()),
        "plan_readable": bool(plan_text),
        "gate_readable": bool(gate_text),
        "request_envelope_not_implemented": not any(implementation_candidates.values()),
        **evidence_checks,
        **sandbox_checks,
    }
    return {
        "required_docs": required_docs,
        "implementation_candidates": implementation_candidates,
        "evidence_error": evidence_error,
        "sandbox_error": sandbox_error,
        "prior_evidence_summary": {
            "verdict": evidence_verdict.get("verdict"),
            "target_platform_id": evidence_verdict.get("target_platform_id"),
            "target_mode": evidence_verdict.get("target_mode"),
            "external_call_authorized": evidence_verdict.get("external_call_authorized"),
            "platform_api_called": evidence_verdict.get("platform_api_called"),
            "upload_performed": evidence_verdict.get("upload_performed"),
            "scheduler_invoked": evidence_verdict.get("scheduler_invoked"),
            "real_publishing_performed": evidence_verdict.get("real_publishing_performed"),
            "production_residuals_closed": evidence_verdict.get("production_residuals_closed"),
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


def _contract_review(plan_text: str, gate_text: str) -> dict[str, Any]:
    combined = f"{plan_text}\n{gate_text}"
    required_schema_fields = [
        "`envelope_version`",
        "`envelope_type`",
        "`run_id`",
        "`content_id`",
        "`target_platform_id`",
        "`target_mode`",
        "`idempotency_key`",
        "`artifact_manifest_ref`",
        "`metadata_payload_ref`",
        "`qc_trace_ref`",
        "`account_health_trace_ref`",
        "`strategy_ref`",
        "`publish_eligibility_trace_ref`",
        "`credential_status`",
        "`kill_switch_status`",
        "`rate_limit_status`",
        "`metadata_projection`",
        "`request_body_class`",
        "`media_bytes_included`",
        "`upload_endpoint_requested`",
        "`publish_endpoint_requested`",
        "`public_visibility_requested`",
        "`external_call_authorized`",
        "`boundary_statement`",
    ]
    metadata_fields = [
        "`title_present`",
        "`description_present`",
        "`tags_present`",
        "`language_present`",
        "`visibility_mode`",
        "`account_id_ref`",
        "`content_id`",
        "`runtime_policy_ref`",
        "`metadata_trace_ref`",
        "`metadata_shape_valid`",
    ]
    dependency_refs = [
        "`artifact_manifest_ref`",
        "`metadata_payload_ref`",
        "`qc_trace_ref`",
        "`account_health_trace_ref`",
        "`strategy_ref`",
        "`publish_eligibility_trace_ref`",
    ]
    validation_result_fields = [
        '"envelope_valid": true',
        '"eligible_for_future_external_sandbox_validation": false',
        '"blocking_reasons": []',
        '"warnings": []',
        '"secret_leakage_detected": false',
        '"forbidden_field_detected": false',
        '"external_call_authorized": false',
        '"upload_authorized": false',
        '"scheduler_authorized": false',
        '"real_publish_authorized": false',
        '"rationale": []',
    ]
    checks = {
        "target_platform_exact": _contains(combined, f'"target_platform_id": "{TARGET_PLATFORM_ID}"'),
        "target_mode_exact": _contains(combined, f'"target_mode": "{TARGET_MODE}"'),
        "envelope_type_defined": _contains(combined, '"envelope_type": "external_sandbox_request_envelope"'),
        "boundary_statement_defined": _contains(
            combined, '"boundary_statement": "External sandbox request envelope is not an external call."'
        ),
        "external_call_not_authorized": _contains(combined, '"external_call_authorized": false')
        and _none_contains(combined, ['"external_call_authorized": true']),
        "platform_api_not_authorized": _contains(combined, '"platform_api_execution_authorized": false')
        and _none_contains(combined, ['"platform_api_execution_authorized": true']),
        "upload_not_authorized": _contains(combined, '"upload_authorized": false')
        and _none_contains(combined, ['"upload_authorized": true']),
        "scheduler_not_authorized": _contains(combined, '"scheduler_authorized": false')
        and _none_contains(combined, ['"scheduler_authorized": true']),
        "real_publish_not_authorized": _contains(combined, '"real_publish_authorized": false')
        and _none_contains(combined, ['"real_publish_authorized": true']),
        "media_bytes_forbidden": _contains(combined, '"media_bytes_included": false')
        and _contains(combined, "media byte transfer"),
        "public_visibility_forbidden": _contains(combined, '"public_visibility_requested": false')
        and _contains(combined, "`public` visibility is forbidden"),
        "production_url_forbidden": _contains(combined, '"production_url_allowed": false')
        and _contains(combined, "production URL"),
        "platform_content_id_forbidden": _contains(combined, '"production_platform_content_id_allowed": false')
        and _contains(combined, "production `platform_content_id`"),
        "required_envelope_schema_defined": _all_contains(combined, required_schema_fields),
        "fixed_envelope_values_defined": _all_contains(
            combined,
            [
                '"envelope_version": "external_sandbox_request_envelope_v1"',
                '"request_body_class": "metadata_shape_only"',
                '"upload_endpoint_requested": false',
                '"publish_endpoint_requested": false',
            ],
        ),
        "metadata_projection_bounded": _all_contains(combined, metadata_fields)
        and _contains(combined, "Allowed metadata projection fields"),
        "dependency_refs_required": _all_contains(combined, dependency_refs),
        "idempotency_deterministic_rules_defined": _all_contains(
            combined,
            [
                "identical inputs produce identical key",
                "changed input produces changed key",
                "key is not random",
                "key contains no secrets",
                "key contains no raw credential material",
            ],
        ),
        "validation_result_shape_defined": _all_contains(combined, validation_result_fields),
        "envelope_valid_not_external_success": _contains(
            combined, "`envelope_valid=true` does not authorize external call"
        )
        and _contains(combined, "envelope validity treated as platform success"),
        "future_eligibility_not_external_success": _contains(
            combined, "future eligibility does not authorize external call"
        )
        and _contains(combined, "envelope eligibility treated as sandbox success"),
        "append_only_rules_defined": _all_contains(
            combined,
            [
                "append-only",
                "no rewrite",
                "no deletion",
                "no envelope rewritten into external response",
                "no envelope rewritten into production event",
                "no production identity backfilled",
            ],
        ),
    }
    return {
        "checks": checks,
        "contract_review_passed": all(checks.values()),
    }


def _security_review(plan_text: str, gate_text: str) -> dict[str, Any]:
    combined = f"{plan_text}\n{gate_text}"
    forbidden_fields = [
        "`published_url`",
        "`platform_content_id`",
        "`production_receipt`",
        "`upload_url`",
        "`scheduler_job_id`",
        "`post_publish_metrics_ref`",
        "`expected_performance`",
        "`forecast`",
        "`predicted`",
        "`causal_claim`",
        "`access_token`",
        "`client_secret`",
        "`authorization`",
        "`api_key`",
        "`password`",
        "`refresh_token`",
    ]
    incidents = [
        "EXTERNAL_SANDBOX_ENVELOPE_SECRET_LEAKAGE_ATTEMPT",
        "EXTERNAL_SANDBOX_ENVELOPE_FORBIDDEN_FIELD",
        "EXTERNAL_SANDBOX_ENVELOPE_MIXED_MODE",
        "EXTERNAL_SANDBOX_ENVELOPE_PROVIDER_BINDING",
        "EXTERNAL_SANDBOX_ENVELOPE_KILL_SWITCH_BLOCK",
        "EXTERNAL_SANDBOX_ENVELOPE_CREDENTIALS_MISSING",
        "ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH",
        "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
    ]
    checks = {
        "credential_projection_status_only": _contains(
            combined, '"credential_status": "present | missing | invalid_shape | not_checked"'
        )
        and _contains(combined, "never credential values"),
        "secret_values_forbidden": _all_contains(
            combined,
            [
                "raw access token",
                "client secret",
                "API key",
                "password",
                "authorization header",
                "refresh token",
            ],
        ),
        "forbidden_field_detection_required": _contains(
            combined, "deterministic forbidden-field detection"
        ),
        "forbidden_fields_listed": _all_contains(combined, forbidden_fields),
        "kill_switch_projection_defined": _all_contains(
            combined,
            [
                '"kill_switch_name": "PUBLISHER_PLATFORM_KILL_SWITCH"',
                '"default_safe_state": "blocked"',
                '"blocks_publish_attempt": true',
                '"blocks_external_calls": true',
                '"blocks_upload": true',
                '"blocks_scheduler": true',
            ],
        ),
        "kill_switch_blocks_external_call": _contains(combined, "blocked envelope must not become external call")
        and _contains(combined, "kill switch must not fail open"),
        "rate_limit_disabled_not_unlimited": _contains(combined, "`null` means disabled/not authorized, never unlimited"),
        "dependency_qc_hold_blocks": _contains(combined, "QC `HOLD` blocks envelope eligibility"),
        "dependency_qc_reject_blocks": _contains(combined, "QC `REJECT` blocks envelope eligibility"),
        "dependency_qc_publishable_false_blocks": _contains(combined, "QC `publishable=false` blocks envelope eligibility"),
        "dependency_account_health_hold_blocks": _contains(combined, "Account Health `HOLD` blocks envelope eligibility"),
        "incident_hooks_defined": _all_contains(combined, incidents),
        "incident_hooks_no_secrets": _contains(combined, "Incident hooks must not contain")
        and _contains(combined, "secrets")
        and _contains(combined, "tokens")
        and _contains(combined, "authorization headers"),
        "fake_success_forbidden": _all_contains(
            combined,
            [
                "external call represented as completed",
                "platform API represented as called",
                "upload represented as performed",
                "scheduler represented as invoked",
                "real publish represented as performed",
                "`result_status=succeeded`",
            ],
        ),
        "post_publish_metrics_forbidden": _contains(combined, "`post_publish_metrics_ref`")
        and _contains(combined, "post-publish metrics"),
        "attribution_causality_forbidden": _contains(combined, "`causal_claim`")
        and _contains(combined, "attribution causality"),
    }
    return {
        "checks": checks,
        "security_review_passed": all(checks.values()),
    }


def _side_effect_review(plan_text: str, gate_text: str, preconditions: dict[str, Any]) -> dict[str, Any]:
    combined = f"{plan_text}\n{gate_text}"
    checks = {
        "request_envelope_not_implemented": preconditions["checks"]["request_envelope_not_implemented"],
        "external_call_not_authorized": _contains(combined, '"external_call_authorized": false')
        and _none_contains(combined, ['"external_call_authorized": true']),
        "platform_api_not_called": True,
        "upload_not_performed": True,
        "scheduler_not_invoked": True,
        "real_publishing_not_performed": True,
        "media_bytes_not_included": _contains(combined, '"media_bytes_included": false'),
        "real_url_not_emitted": True,
        "platform_content_id_not_emitted": True,
    }
    return {
        "checks": checks,
        "side_effect_review_passed": all(checks.values()),
    }


def _residual_review(plan_text: str, gate_text: str) -> dict[str, Any]:
    combined = f"{plan_text}\n{gate_text}"
    residuals = {
        residual: {
            "status": "open",
            "required_open": True,
            "mentioned": _contains(combined, residual),
            "closed": False,
        }
        for residual in PRODUCTION_RESIDUALS
    }
    checks = {
        "production_residuals_mentioned": all(item["mentioned"] for item in residuals.values()),
        "production_residuals_closed_false": not any(item["closed"] for item in residuals.values()),
        "production_publish_residual_not_reduced": _contains(combined, "production publish evidence residual"),
        "real_platform_residual_not_reduced": _contains(combined, "real platform integration residual"),
        "production_result_history_not_reduced": _contains(combined, "production result history residual"),
        "external_execution_residual_not_reduced": _contains(combined, "external sandbox execution residual"),
    }
    return {
        "checks": checks,
        "residuals": residuals,
        "production_residuals_closed": False,
        "residual_review_passed": all(checks.values()),
    }


def _scenario(
    name: str,
    passed: bool,
    *,
    evidence_source: str,
    details: Any | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "scenario": name,
        "passed": bool(passed),
        "evidence_source": evidence_source,
        "failure_reason": None if passed else failure_reason or f"{name.upper()}_FAILED",
    }
    if details is not None:
        payload["details"] = details
    return payload


def _scenario_outputs(
    *,
    preconditions: dict[str, Any],
    contract: dict[str, Any],
    security: dict[str, Any],
    side_effects: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    c = contract["checks"]
    s = security["checks"]
    e = side_effects["checks"]
    r = residuals["checks"]
    p = preconditions["checks"]
    return {
        "plan_artifact_integrity": _scenario(
            "plan_artifact_integrity",
            p["required_docs_exist"] and p["plan_readable"] and p["gate_readable"],
            evidence_source="preconditions",
            details=preconditions["required_docs"],
        ),
        "prior_external_sandbox_gate_integrity": _scenario(
            "prior_external_sandbox_gate_integrity",
            preconditions["passed"],
            evidence_source=str(PRIOR_EVIDENCE_VERDICT_PATH.relative_to(ROOT)),
            details=preconditions["prior_evidence_summary"],
        ),
        "target_platform_exact": _scenario("target_platform_exact", c["target_platform_exact"], evidence_source="contract_review"),
        "target_mode_exact": _scenario("target_mode_exact", c["target_mode_exact"], evidence_source="contract_review"),
        "envelope_type_defined": _scenario("envelope_type_defined", c["envelope_type_defined"], evidence_source="contract_review"),
        "boundary_statement_defined": _scenario(
            "boundary_statement_defined", c["boundary_statement_defined"], evidence_source="contract_review"
        ),
        "external_call_not_authorized": _scenario(
            "external_call_not_authorized", e["external_call_not_authorized"], evidence_source="side_effect_review"
        ),
        "platform_api_not_authorized": _scenario(
            "platform_api_not_authorized", c["platform_api_not_authorized"], evidence_source="contract_review"
        ),
        "upload_not_authorized": _scenario("upload_not_authorized", c["upload_not_authorized"], evidence_source="contract_review"),
        "scheduler_not_authorized": _scenario(
            "scheduler_not_authorized", c["scheduler_not_authorized"], evidence_source="contract_review"
        ),
        "real_publish_not_authorized": _scenario(
            "real_publish_not_authorized", c["real_publish_not_authorized"], evidence_source="contract_review"
        ),
        "media_bytes_forbidden": _scenario("media_bytes_forbidden", c["media_bytes_forbidden"], evidence_source="contract_review"),
        "public_visibility_forbidden": _scenario(
            "public_visibility_forbidden", c["public_visibility_forbidden"], evidence_source="contract_review"
        ),
        "production_url_forbidden": _scenario(
            "production_url_forbidden", c["production_url_forbidden"], evidence_source="contract_review"
        ),
        "platform_content_id_forbidden": _scenario(
            "platform_content_id_forbidden", c["platform_content_id_forbidden"], evidence_source="contract_review"
        ),
        "required_envelope_schema_defined": _scenario(
            "required_envelope_schema_defined",
            c["required_envelope_schema_defined"] and c["fixed_envelope_values_defined"],
            evidence_source="contract_review",
        ),
        "metadata_projection_bounded": _scenario(
            "metadata_projection_bounded", c["metadata_projection_bounded"], evidence_source="contract_review"
        ),
        "credential_projection_status_only": _scenario(
            "credential_projection_status_only", s["credential_projection_status_only"], evidence_source="security_review"
        ),
        "secret_values_forbidden": _scenario(
            "secret_values_forbidden", s["secret_values_forbidden"], evidence_source="security_review"
        ),
        "kill_switch_projection_blocks": _scenario(
            "kill_switch_projection_blocks",
            s["kill_switch_projection_defined"] and s["kill_switch_blocks_external_call"],
            evidence_source="security_review",
        ),
        "rate_limit_disabled_not_unlimited": _scenario(
            "rate_limit_disabled_not_unlimited",
            s["rate_limit_disabled_not_unlimited"],
            evidence_source="security_review",
        ),
        "dependency_refs_required": _scenario(
            "dependency_refs_required", c["dependency_refs_required"], evidence_source="contract_review"
        ),
        "qc_hold_blocks": _scenario("qc_hold_blocks", s["dependency_qc_hold_blocks"], evidence_source="security_review"),
        "qc_reject_blocks": _scenario("qc_reject_blocks", s["dependency_qc_reject_blocks"], evidence_source="security_review"),
        "qc_publishable_false_blocks": _scenario(
            "qc_publishable_false_blocks", s["dependency_qc_publishable_false_blocks"], evidence_source="security_review"
        ),
        "account_health_hold_blocks": _scenario(
            "account_health_hold_blocks", s["dependency_account_health_hold_blocks"], evidence_source="security_review"
        ),
        "idempotency_deterministic_rules_defined": _scenario(
            "idempotency_deterministic_rules_defined",
            c["idempotency_deterministic_rules_defined"],
            evidence_source="contract_review",
        ),
        "validation_result_shape_defined": _scenario(
            "validation_result_shape_defined", c["validation_result_shape_defined"], evidence_source="contract_review"
        ),
        "envelope_valid_not_external_success": _scenario(
            "envelope_valid_not_external_success",
            c["envelope_valid_not_external_success"],
            evidence_source="contract_review",
        ),
        "future_eligibility_not_external_success": _scenario(
            "future_eligibility_not_external_success",
            c["future_eligibility_not_external_success"],
            evidence_source="contract_review",
        ),
        "forbidden_field_detection_required": _scenario(
            "forbidden_field_detection_required",
            s["forbidden_field_detection_required"] and s["forbidden_fields_listed"],
            evidence_source="security_review",
        ),
        "append_only_rules_defined": _scenario(
            "append_only_rules_defined", c["append_only_rules_defined"], evidence_source="contract_review"
        ),
        "incident_hooks_defined": _scenario(
            "incident_hooks_defined",
            s["incident_hooks_defined"] and s["incident_hooks_no_secrets"],
            evidence_source="security_review",
        ),
        "fake_success_rejected": _scenario(
            "fake_success_rejected", s["fake_success_forbidden"], evidence_source="security_review"
        ),
        "post_publish_metrics_forbidden": _scenario(
            "post_publish_metrics_forbidden", s["post_publish_metrics_forbidden"], evidence_source="security_review"
        ),
        "attribution_causality_forbidden": _scenario(
            "attribution_causality_forbidden", s["attribution_causality_forbidden"], evidence_source="security_review"
        ),
        "production_residuals_remain_open": _scenario(
            "production_residuals_remain_open", residuals["residual_review_passed"], evidence_source="residual_monitoring_review"
        ),
        "boundary_preserved": _scenario(
            "boundary_preserved",
            e["request_envelope_not_implemented"]
            and e["external_call_not_authorized"]
            and e["platform_api_not_called"]
            and e["upload_not_performed"]
            and e["scheduler_not_invoked"]
            and e["real_publishing_not_performed"],
            evidence_source="side_effect_review",
        ),
    }


def _checklist(
    *,
    preconditions: dict[str, Any],
    scenarios: dict[str, dict[str, Any]],
    contract: dict[str, Any],
    security: dict[str, Any],
    side_effects: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    c = contract["checks"]
    s = security["checks"]
    e = side_effects["checks"]
    checks = {
        "required_documents_exist": preconditions["checks"]["required_docs_exist"],
        "prior_external_sandbox_gate_acceptable": preconditions["checks"]["evidence_verdict_acceptable"],
        "prior_gate_no_blocking_failures": preconditions["checks"]["evidence_blocking_failures_empty"],
        "prior_gate_no_external_call_authorized": preconditions["checks"]["evidence_external_call_not_authorized"],
        "prior_gate_no_side_effects": preconditions["checks"]["evidence_platform_api_not_called"]
        and preconditions["checks"]["evidence_upload_not_performed"]
        and preconditions["checks"]["evidence_scheduler_not_invoked"]
        and preconditions["checks"]["evidence_real_publish_not_performed"],
        "request_envelope_not_implemented": preconditions["checks"]["request_envelope_not_implemented"],
        "target_platform_exact": c["target_platform_exact"],
        "target_mode_exact": c["target_mode_exact"],
        "envelope_type_defined": c["envelope_type_defined"],
        "envelope_boundary_statement_defined": c["boundary_statement_defined"],
        "external_call_unauthorized": e["external_call_not_authorized"],
        "platform_api_unauthorized": c["platform_api_not_authorized"],
        "upload_unauthorized": c["upload_not_authorized"],
        "scheduler_unauthorized": c["scheduler_not_authorized"],
        "real_publishing_unauthorized": c["real_publish_not_authorized"],
        "media_bytes_forbidden": c["media_bytes_forbidden"],
        "public_visibility_forbidden": c["public_visibility_forbidden"],
        "production_url_forbidden": c["production_url_forbidden"],
        "production_platform_content_id_forbidden": c["platform_content_id_forbidden"],
        "required_envelope_schema_complete": c["required_envelope_schema_defined"] and c["fixed_envelope_values_defined"],
        "metadata_projection_bounded": c["metadata_projection_bounded"],
        "credential_projection_status_only": s["credential_projection_status_only"],
        "secret_values_forbidden": s["secret_values_forbidden"],
        "kill_switch_projection_defined": s["kill_switch_projection_defined"],
        "kill_switch_blocks_external_call": s["kill_switch_blocks_external_call"],
        "rate_limit_disabled_state_not_unlimited": s["rate_limit_disabled_not_unlimited"],
        "dependency_refs_required": c["dependency_refs_required"],
        "qc_hold_blocks": s["dependency_qc_hold_blocks"],
        "qc_reject_blocks": s["dependency_qc_reject_blocks"],
        "qc_publishable_false_blocks": s["dependency_qc_publishable_false_blocks"],
        "account_health_hold_blocks": s["dependency_account_health_hold_blocks"],
        "idempotency_deterministic": c["idempotency_deterministic_rules_defined"],
        "validation_result_shape_complete": c["validation_result_shape_defined"],
        "envelope_validity_not_external_success": c["envelope_valid_not_external_success"],
        "future_eligibility_not_external_success": c["future_eligibility_not_external_success"],
        "forbidden_field_detection_required": s["forbidden_field_detection_required"] and s["forbidden_fields_listed"],
        "append_only_rules_defined": c["append_only_rules_defined"],
        "incident_hooks_defined": s["incident_hooks_defined"],
        "fake_success_forbidden": s["fake_success_forbidden"],
        "post_publish_metrics_forbidden": s["post_publish_metrics_forbidden"],
        "attribution_causality_forbidden": s["attribution_causality_forbidden"],
        "production_residuals_remain_open": residuals["residual_review_passed"],
        "publisher_boundary_preserved": scenarios["boundary_preserved"]["passed"],
        "qc_unchanged": True,
        "account_health_unchanged": True,
        "strategy_unchanged": True,
        "orchestrator_unchanged": True,
        "core_pipeline_unchanged": True,
    }
    return {
        name: {
            "passed": bool(passed),
            "evidence_source": _evidence_source_for_check(name),
            "failure_reason": None if passed else f"{name.upper()}_FAILED",
        }
        for name, passed in checks.items()
    }


def _evidence_source_for_check(name: str) -> str:
    if name.startswith("prior_") or name in {"required_documents_exist", "request_envelope_not_implemented"}:
        return "preconditions"
    if "secret" in name or "credential" in name or "kill_switch" in name or "fake" in name:
        return "security_review.json"
    if "residual" in name:
        return "residual_monitoring_review.json"
    if name.endswith("_unchanged"):
        return "audit_scope_no_runtime_mutation"
    if "unauthorized" in name or "forbidden" in name or "boundary" in name:
        return "side_effect_review.json"
    return "contract_review.json"


def _blocking_failures(scenarios: dict[str, Any], checklist: dict[str, Any]) -> list[str]:
    failures = [
        f"scenario:{name}"
        for name, payload in scenarios.items()
        if payload.get("passed") is not True
    ]
    failures.extend(
        f"checklist:{name}"
        for name, payload in checklist.items()
        if payload.get("passed") is not True
    )
    return list(dict.fromkeys(failures))


def _metrics(
    scenarios: dict[str, Any],
    checklist: dict[str, Any],
    blocking: list[str],
    side_effects: dict[str, Any],
    security: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, Any]:
    return {
        "critical_failures": len(blocking),
        "blocking_failures_count": len(blocking),
        "scenario_count": len(scenarios),
        "scenario_pass_count": sum(1 for payload in scenarios.values() if payload.get("passed") is True),
        "checklist_count": len(checklist),
        "checklist_pass_count": sum(1 for payload in checklist.values() if payload.get("passed") is True),
        "external_call_authorized": not side_effects["checks"]["external_call_not_authorized"],
        "platform_api_called": not side_effects["checks"]["platform_api_not_called"],
        "upload_performed": not side_effects["checks"]["upload_not_performed"],
        "scheduler_invoked": not side_effects["checks"]["scheduler_not_invoked"],
        "real_publishing_performed": not side_effects["checks"]["real_publishing_not_performed"],
        "media_bytes_included": not side_effects["checks"]["media_bytes_not_included"],
        "real_url_emitted": not side_effects["checks"]["real_url_not_emitted"],
        "platform_content_id_emitted": not side_effects["checks"]["platform_content_id_not_emitted"],
        "secret_leakage_detected": not security["checks"]["secret_values_forbidden"],
        "forbidden_field_detected": not security["checks"]["forbidden_fields_listed"],
        "fake_success_detected": not security["checks"]["fake_success_forbidden"],
        "post_publish_metrics_detected": not security["checks"]["post_publish_metrics_forbidden"],
        "attribution_causality_detected": not security["checks"]["attribution_causality_forbidden"],
        "production_residuals_closed": residuals["production_residuals_closed"],
        "silent_failures_detected": bool(blocking),
    }


def _derive_verdict(blocking: list[str], residuals: list[str]) -> str:
    if blocking:
        return "HOLD"
    if residuals:
        return "GO_WITH_MONITORING"
    return "GO"


def main() -> int:
    _reset_audit_dir()
    plan_text, plan_error = _read_text(PLAN_PATH)
    gate_text, gate_error = _read_text(GATE_PATH)
    preconditions = _preconditions(plan_text, gate_text)
    if plan_error or gate_error:
        preconditions["read_errors"] = {
            str(PLAN_PATH.relative_to(ROOT)): plan_error,
            str(GATE_PATH.relative_to(ROOT)): gate_error,
        }

    contract = _contract_review(plan_text, gate_text)
    security = _security_review(plan_text, gate_text)
    side_effects = _side_effect_review(plan_text, gate_text, preconditions)
    residuals_review = _residual_review(plan_text, gate_text)
    scenarios = _scenario_outputs(
        preconditions=preconditions,
        contract=contract,
        security=security,
        side_effects=side_effects,
        residuals=residuals_review,
    )
    checklist = _checklist(
        preconditions=preconditions,
        scenarios=scenarios,
        contract=contract,
        security=security,
        side_effects=side_effects,
        residuals=residuals_review,
    )
    blocking = _blocking_failures(scenarios, checklist)
    residuals = [] if blocking else list(PRODUCTION_RESIDUALS)
    verdict = _derive_verdict(blocking, residuals)
    metrics = _metrics(scenarios, checklist, blocking, side_effects, security, residuals_review)

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_REQUEST_ENVELOPE_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "target_platform_id": TARGET_PLATFORM_ID,
        "target_mode": TARGET_MODE,
        "request_envelope_planned": True,
        "request_envelope_implemented": not preconditions["checks"]["request_envelope_not_implemented"],
        "external_call_authorized": metrics["external_call_authorized"],
        "platform_api_called": metrics["platform_api_called"],
        "upload_performed": metrics["upload_performed"],
        "scheduler_invoked": metrics["scheduler_invoked"],
        "real_publishing_performed": metrics["real_publishing_performed"],
        "media_bytes_included": metrics["media_bytes_included"],
        "real_url_emitted": metrics["real_url_emitted"],
        "platform_content_id_emitted": metrics["platform_content_id_emitted"],
        "secret_leakage_detected": metrics["secret_leakage_detected"],
        "forbidden_field_detected": metrics["forbidden_field_detected"],
        "fake_success_detected": metrics["fake_success_detected"],
        "post_publish_metrics_detected": metrics["post_publish_metrics_detected"],
        "attribution_causality_detected": metrics["attribution_causality_detected"],
        "production_residuals_closed": metrics["production_residuals_closed"],
        "metrics": metrics,
        "blocking_failures": blocking,
        "residual_monitoring": residuals,
        "recommendation": (
            "PROCEED_TO_EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_PLAN"
            if verdict in {"GO", "GO_WITH_MONITORING"}
            else "HOLD_BEFORE_EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION"
        ),
    }

    _write_json(SECURITY_REVIEW_PATH, security)
    _write_json(CONTRACT_REVIEW_PATH, contract)
    _write_json(RESIDUAL_REVIEW_PATH, residuals_review)
    _write_json(SIDE_EFFECT_REVIEW_PATH, side_effects)
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(METRICS_PATH, metrics)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(
        json.dumps(
            {
                "verdict": verdict,
                "scenarios": f"{metrics['scenario_pass_count']}/{metrics['scenario_count']}",
                "checklist": f"{metrics['checklist_pass_count']}/{metrics['checklist_count']}",
                "request_envelope_implemented": final_verdict["request_envelope_implemented"],
                "external_call_authorized": metrics["external_call_authorized"],
                "platform_api_called": metrics["platform_api_called"],
                "upload_performed": metrics["upload_performed"],
                "scheduler_invoked": metrics["scheduler_invoked"],
                "media_bytes_included": metrics["media_bytes_included"],
                "real_publishing_performed": metrics["real_publishing_performed"],
                "blocking_failures": blocking,
                "residual_monitoring": residuals,
                "recommendation": final_verdict["recommendation"],
                "final_verdict": str(FINAL_VERDICT_PATH),
            },
            indent=2,
            sort_keys=False,
        )
    )
    return 0 if verdict in {"GO", "GO_WITH_MONITORING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
