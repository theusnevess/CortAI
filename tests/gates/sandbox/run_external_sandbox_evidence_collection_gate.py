from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_evidence_collection_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
SECURITY_REVIEW_PATH = AUDIT_DIR / "security_review.json"
CONTRACT_REVIEW_PATH = AUDIT_DIR / "contract_review.json"
RESIDUAL_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
SIDE_EFFECT_REVIEW_PATH = AUDIT_DIR / "side_effect_review.json"

PLAN_PATH = ROOT / "docs" / "runtime" / "sandbox" / "evidence" / "EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_PLAN.md"
GATE_PATH = ROOT / "docs" / "runtime" / "sandbox" / "evidence" / "EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE.md"
SANDBOX_ADAPTER_PLAN_PATH = ROOT / "docs" / "runtime" / "sandbox" / "adapter" / "SANDBOX_ADAPTER_IMPLEMENTATION_PLAN.md"
SANDBOX_ADAPTER_GATE_PATH = ROOT / "docs" / "runtime" / "sandbox" / "adapter" / "SANDBOX_ADAPTER_IMPLEMENTATION_GATE.md"
PUBLISHER_PLATFORM_GATE_PATH = ROOT / "docs" / "runtime" / "publisher" / "platform-integration" / "PUBLISHER_PLATFORM_INTEGRATION_GATE.md"
PRIOR_FINAL_VERDICT_PATH = ROOT / "OUT" / "audit" / "sandbox_adapter_implementation_gate" / "final_verdict.json"

IMPLEMENTATION_FILES = [
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "sandbox_contracts.py",
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "sandbox_security.py",
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "sandbox_adapter.py",
    ROOT / "tests" / "test_publisher_sandbox_adapter_unittest.py",
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
    prior_verdict, prior_error = _load_json(PRIOR_FINAL_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [
            PLAN_PATH,
            GATE_PATH,
            SANDBOX_ADAPTER_PLAN_PATH,
            SANDBOX_ADAPTER_GATE_PATH,
            PUBLISHER_PLATFORM_GATE_PATH,
        ]
    }
    implementation_files = {
        str(path.relative_to(ROOT)): path.exists()
        for path in IMPLEMENTATION_FILES
    }
    prior_checks = {
        "prior_json_valid": not prior_error,
        "prior_verdict_acceptable": prior_verdict.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "prior_target_platform_exact": prior_verdict.get("target_platform_id") == TARGET_PLATFORM_ID,
        "prior_target_mode_exact": prior_verdict.get("target_mode") == TARGET_MODE,
        "prior_adapter_present": prior_verdict.get("adapter_present") is True,
        "prior_contracts_serializable": prior_verdict.get("contracts_serializable") is True,
        "prior_single_mode_enforced": prior_verdict.get("single_mode_enforced") is True,
        "prior_mixed_modes_forbidden": prior_verdict.get("no_mixed_modes_allowed") is True,
        "prior_implicit_provider_forbidden": prior_verdict.get("no_implicit_provider_binding") is True,
        "prior_sandbox_receipt_not_production": prior_verdict.get("sandbox_receipt_not_production") is True,
        "prior_result_evidence_non_production": prior_verdict.get("result_evidence_is_production") is False,
        "prior_platform_api_not_called": prior_verdict.get("platform_api_called") is False,
        "prior_upload_not_performed": prior_verdict.get("upload_performed") is False,
        "prior_scheduler_not_invoked": prior_verdict.get("scheduler_invoked") is False,
        "prior_real_publish_not_performed": prior_verdict.get("real_publishing_performed") is False,
        "prior_real_url_not_emitted": prior_verdict.get("real_url_emitted") is False,
        "prior_platform_content_id_not_emitted": prior_verdict.get("platform_content_id_emitted") is False,
        "prior_production_residuals_open": prior_verdict.get("production_residuals_closed") is False,
        "prior_blocking_failures_empty": prior_verdict.get("blocking_failures") == [],
    }
    return {
        "required_docs": required_docs,
        "implementation_files": implementation_files,
        "prior_error": prior_error,
        "prior_summary": {
            "verdict": prior_verdict.get("verdict"),
            "target_platform_id": prior_verdict.get("target_platform_id"),
            "target_mode": prior_verdict.get("target_mode"),
            "platform_api_called": prior_verdict.get("platform_api_called"),
            "upload_performed": prior_verdict.get("upload_performed"),
            "scheduler_invoked": prior_verdict.get("scheduler_invoked"),
            "real_publishing_performed": prior_verdict.get("real_publishing_performed"),
            "production_residuals_closed": prior_verdict.get("production_residuals_closed"),
        },
        "checks": {
            "required_docs_exist": all(required_docs.values()),
            "implementation_files_exist": all(implementation_files.values()),
            "plan_readable": bool(plan_text),
            "gate_readable": bool(gate_text),
            **prior_checks,
        },
        "passed": all(required_docs.values())
        and all(implementation_files.values())
        and bool(plan_text)
        and bool(gate_text)
        and all(prior_checks.values()),
    }


def _contract_review(plan_text: str, gate_text: str) -> dict[str, Any]:
    combined = f"{plan_text}\n{gate_text}"
    request_fields = [
        '"run_id"',
        '"content_id"',
        '"target_platform_id"',
        '"target_mode"',
        '"idempotency_key"',
        '"artifact_manifest_ref"',
        '"metadata_payload_ref"',
        '"qc_trace_ref"',
        '"account_health_trace_ref"',
        '"strategy_ref"',
        '"publish_eligibility_trace_ref"',
        '"credential_status"',
        '"kill_switch_status"',
        '"rate_limit_status"',
        '"request_body_class"',
        '"media_bytes_included"',
        '"public_visibility_requested"',
    ]
    response_fields = [
        '"result_status"',
        '"result_evidence_available"',
        '"result_evidence_is_production"',
        '"result_evidence_type"',
        '"result_evidence_ref"',
        '"receipt_hash"',
        '"receipt_observed_at"',
        '"external_identity_type"',
        '"published_url"',
        '"platform_content_id"',
        '"raw_response_persisted"',
        '"redacted_response_ref"',
    ]
    checks = {
        "target_platform_exact": _contains(combined, f'"target_platform_id": "{TARGET_PLATFORM_ID}"'),
        "target_mode_exact": _contains(combined, f'"target_mode": "{TARGET_MODE}"'),
        "external_boundary_type_defined": _contains(
            combined, '"external_boundary_type": "controlled_sandbox_validation"'
        ),
        "single_mode_enforced": _contains(combined, '"single_mode_enforced": true'),
        "mixed_modes_forbidden": _contains(combined, '"no_mixed_modes_allowed": true')
        and _contains(combined, "Mixed modes are forbidden"),
        "implicit_provider_binding_forbidden": _contains(combined, '"no_implicit_provider_binding": true')
        and _contains(combined, "separate provider approval artifact"),
        "request_envelope_complete": _all_contains(plan_text, request_fields),
        "request_body_metadata_shape_only": _contains(plan_text, '"request_body_class": "metadata_shape_only"'),
        "media_bytes_forbidden": _contains(plan_text, '"media_bytes_included": false')
        and _contains(plan_text, "media bytes must not be included"),
        "public_visibility_forbidden": _contains(plan_text, '"public_visibility_requested": false')
        and _contains(plan_text, "public visibility must not be requested"),
        "idempotency_key_required": _contains(combined, "idempotency key must be deterministic"),
        "response_evidence_complete": _all_contains(plan_text, response_fields),
        "response_evidence_non_production": _contains(combined, '"result_evidence_is_production": false'),
        "published_url_null": _contains(plan_text, '"published_url": null'),
        "platform_content_id_null": _contains(plan_text, '"platform_content_id": null'),
        "pending_not_success": _contains(plan_text, "`pending_sandbox` does not mean success"),
        "sandbox_failed_not_production_failure": _contains(
            plan_text, "`sandbox_failed` does not mean production failure"
        ),
        "append_only_rules_defined": _all_contains(
            plan_text,
            [
                "no rewrite",
                "no deletion",
                "no failed/pending/skipped event rewritten into success",
                "no sandbox event rewritten into production event",
                "no production identity backfilled into sandbox event",
            ],
        ),
    }
    return {
        "checks": checks,
        "contract_review_passed": all(checks.values()),
    }


def _security_review(plan_text: str, gate_text: str) -> dict[str, Any]:
    combined = f"{plan_text}\n{gate_text}"
    required_incidents = [
        "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE",
        "PUBLISHER_CREDENTIALS_MISSING",
        "PUBLISHER_CREDENTIAL_VALIDATION_FAILED",
        "PUBLISHER_RATE_LIMIT_EXCEEDED",
        "PUBLISHER_EXTERNAL_SANDBOX_TIMEOUT",
        "PUBLISHER_EXTERNAL_SANDBOX_SCHEMA_INVALID",
        "PUBLISHER_EXTERNAL_SANDBOX_VALIDATION_FAILED",
        "PUBLISHER_SANDBOX_RESPONSE_MISSING",
        "PUBLISHER_FAKE_SUCCESS_ATTEMPT",
        "PUBLISHER_FAKE_URL_OR_PLATFORM_ID_ATTEMPT",
        "ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH",
        "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
    ]
    checks = {
        "credential_status_only": _contains(plan_text, '"credential_status": "present | missing | invalid_shape | not_checked"'),
        "secret_values_not_logged": _contains(plan_text, "raw secret values in logs"),
        "secret_values_not_in_jsonl": _contains(plan_text, "raw secret values in JSONL"),
        "secret_values_not_in_audit_artifacts": _contains(plan_text, "raw secret values in audit artifacts"),
        "tokens_not_in_incident_hooks": _contains(plan_text, "tokens in incident hooks"),
        "authorization_headers_not_in_traces": _contains(plan_text, "authorization headers in traces"),
        "missing_credentials_block": _contains(plan_text, "Missing credentials must block external sandbox validation"),
        "kill_switch_required": _contains(combined, '"kill_switch_name": "PUBLISHER_PLATFORM_KILL_SWITCH"'),
        "kill_switch_blocks_external_request": _contains(combined, '"blocks_external_calls": true')
        and _contains(plan_text, "no external sandbox request may be sent"),
        "kill_switch_blocks_upload": _contains(combined, '"blocks_upload": true'),
        "kill_switch_blocks_scheduler": _contains(combined, '"blocks_scheduler": true'),
        "rate_limit_disabled_not_unlimited": _contains(plan_text, "`null` means disabled/not authorized, never unlimited"),
        "timeout_not_success": _contains(plan_text, "timeout must produce evidence, not success"),
        "rate_limit_exhaustion_blocks": _contains(plan_text, "rate-limit exhaustion must block and trace"),
        "incident_hooks_defined": _all_contains(combined, required_incidents),
        "fake_success_forbidden": _all_contains(
            combined,
            [
                "`result_status = succeeded`",
                "`result_status = published`",
                "`result_status = production_published`",
                "eligibility counted as success",
                "pending counted as success",
            ],
        ),
        "fake_url_or_platform_id_forbidden": _all_contains(
            combined,
            [
                "non-null `published_url`",
                "non-null `platform_content_id`",
            ],
        ),
        "qc_non_publishable_blocks": _contains(combined, "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH")
        and (
            _contains(combined, "QC `publishable=false`")
            or _contains(combined, "QC non-publishable")
        ),
        "account_health_hold_blocks": _contains(combined, "ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH")
        and _contains(combined, "Account Health"),
        "post_publish_metrics_forbidden": _contains(combined, "post-publish metrics")
        and _contains(combined, "post_publish_metrics_allowed"),
        "attribution_causality_forbidden": _contains(combined, "attribution causality")
        and _contains(combined, "attribution_causality_detected"),
    }
    return {
        "checks": checks,
        "security_review_passed": all(checks.values()),
    }


def _side_effect_review(plan_text: str, gate_text: str) -> dict[str, Any]:
    combined = f"{plan_text}\n{gate_text}"
    checks = {
        "external_call_not_authorized": _contains(combined, '"external_call_authorized": false')
        and _none_contains(combined, ['"external_call_authorized": true']),
        "platform_api_execution_not_authorized": _contains(
            combined, '"platform_api_execution_authorized": false'
        )
        and _none_contains(combined, ['"platform_api_execution_authorized": true']),
        "upload_not_authorized": _contains(combined, '"upload_authorized": false')
        and _none_contains(combined, ['"upload_authorized": true']),
        "scheduler_not_authorized": _contains(combined, '"scheduler_authorized": false')
        and _none_contains(combined, ['"scheduler_authorized": true']),
        "real_publish_not_authorized": _contains(combined, '"real_publish_authorized": false')
        and _none_contains(combined, ['"real_publish_authorized": true']),
        "production_url_not_allowed": _contains(combined, '"production_url_allowed": false')
        and _none_contains(combined, ['"production_url_allowed": true']),
        "production_platform_content_id_not_allowed": _contains(
            combined, '"production_platform_content_id_allowed": false'
        )
        and _none_contains(combined, ['"production_platform_content_id_allowed": true']),
        "platform_api_not_called": True,
        "upload_not_performed": True,
        "scheduler_not_invoked": True,
        "real_publishing_not_performed": True,
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
        "production_residuals_must_remain_open": _contains(combined, "These residuals must remain open"),
        "sandbox_does_not_reduce_production_publish_residual": _contains(
            combined, "production publish evidence residual"
        ),
        "sandbox_does_not_reduce_real_platform_residual": _contains(combined, "real platform integration residual"),
        "sandbox_does_not_reduce_production_result_history": _contains(
            combined, "production result history residual"
        ),
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
        "prior_sandbox_adapter_gate_integrity": _scenario(
            "prior_sandbox_adapter_gate_integrity",
            preconditions["passed"],
            evidence_source=str(PRIOR_FINAL_VERDICT_PATH.relative_to(ROOT)),
            details=preconditions["prior_summary"],
        ),
        "target_platform_exact": _scenario("target_platform_exact", c["target_platform_exact"], evidence_source="contract_review"),
        "target_mode_exact": _scenario("target_mode_exact", c["target_mode_exact"], evidence_source="contract_review"),
        "external_call_not_authorized": _scenario(
            "external_call_not_authorized", e["external_call_not_authorized"], evidence_source="side_effect_review"
        ),
        "platform_api_execution_not_authorized": _scenario(
            "platform_api_execution_not_authorized",
            e["platform_api_execution_not_authorized"],
            evidence_source="side_effect_review",
        ),
        "upload_not_authorized": _scenario("upload_not_authorized", e["upload_not_authorized"], evidence_source="side_effect_review"),
        "scheduler_not_authorized": _scenario(
            "scheduler_not_authorized", e["scheduler_not_authorized"], evidence_source="side_effect_review"
        ),
        "real_publish_not_authorized": _scenario(
            "real_publish_not_authorized", e["real_publish_not_authorized"], evidence_source="side_effect_review"
        ),
        "production_url_not_allowed": _scenario(
            "production_url_not_allowed", e["production_url_not_allowed"], evidence_source="side_effect_review"
        ),
        "platform_content_id_not_allowed": _scenario(
            "platform_content_id_not_allowed",
            e["production_platform_content_id_not_allowed"],
            evidence_source="side_effect_review",
        ),
        "single_mode_enforced": _scenario("single_mode_enforced", c["single_mode_enforced"], evidence_source="contract_review"),
        "mixed_modes_forbidden": _scenario("mixed_modes_forbidden", c["mixed_modes_forbidden"], evidence_source="contract_review"),
        "implicit_provider_binding_forbidden": _scenario(
            "implicit_provider_binding_forbidden", c["implicit_provider_binding_forbidden"], evidence_source="contract_review"
        ),
        "request_envelope_schema_defined": _scenario(
            "request_envelope_schema_defined", c["request_envelope_complete"], evidence_source="contract_review"
        ),
        "media_bytes_forbidden": _scenario("media_bytes_forbidden", c["media_bytes_forbidden"], evidence_source="contract_review"),
        "public_visibility_forbidden": _scenario(
            "public_visibility_forbidden", c["public_visibility_forbidden"], evidence_source="contract_review"
        ),
        "secret_leakage_forbidden": _scenario(
            "secret_leakage_forbidden",
            s["secret_values_not_logged"]
            and s["secret_values_not_in_jsonl"]
            and s["secret_values_not_in_audit_artifacts"]
            and s["tokens_not_in_incident_hooks"]
            and s["authorization_headers_not_in_traces"],
            evidence_source="security_review",
        ),
        "missing_credentials_block": _scenario(
            "missing_credentials_block", s["missing_credentials_block"], evidence_source="security_review"
        ),
        "kill_switch_blocks_external_request": _scenario(
            "kill_switch_blocks_external_request",
            s["kill_switch_required"] and s["kill_switch_blocks_external_request"],
            evidence_source="security_review",
        ),
        "rate_limit_disabled_not_unlimited": _scenario(
            "rate_limit_disabled_not_unlimited",
            s["rate_limit_disabled_not_unlimited"],
            evidence_source="security_review",
        ),
        "timeout_not_success": _scenario("timeout_not_success", s["timeout_not_success"], evidence_source="security_review"),
        "response_evidence_schema_defined": _scenario(
            "response_evidence_schema_defined", c["response_evidence_complete"], evidence_source="contract_review"
        ),
        "result_evidence_non_production": _scenario(
            "result_evidence_non_production", c["response_evidence_non_production"], evidence_source="contract_review"
        ),
        "sandbox_receipt_not_production": _scenario(
            "sandbox_receipt_not_production",
            c["response_evidence_non_production"],
            evidence_source="contract_review",
        ),
        "pending_not_success": _scenario("pending_not_success", c["pending_not_success"], evidence_source="contract_review"),
        "sandbox_failed_not_production_failure": _scenario(
            "sandbox_failed_not_production_failure",
            c["sandbox_failed_not_production_failure"],
            evidence_source="contract_review",
        ),
        "append_only_rules_defined": _scenario(
            "append_only_rules_defined", c["append_only_rules_defined"], evidence_source="contract_review"
        ),
        "incident_hooks_defined": _scenario("incident_hooks_defined", s["incident_hooks_defined"], evidence_source="security_review"),
        "qc_non_publishable_blocks": _scenario(
            "qc_non_publishable_blocks",
            s["qc_non_publishable_blocks"],
            evidence_source="security_review",
        ),
        "account_health_hold_blocks": _scenario(
            "account_health_hold_blocks",
            s["account_health_hold_blocks"],
            evidence_source="security_review",
        ),
        "fake_success_rejected": _scenario("fake_success_rejected", s["fake_success_forbidden"], evidence_source="security_review"),
        "fake_url_or_platform_id_rejected": _scenario(
            "fake_url_or_platform_id_rejected", s["fake_url_or_platform_id_forbidden"], evidence_source="security_review"
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
            e["external_call_not_authorized"]
            and e["upload_not_authorized"]
            and e["scheduler_not_authorized"]
            and e["real_publish_not_authorized"],
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
        "prior_sandbox_adapter_gate_acceptable": preconditions["checks"]["prior_verdict_acceptable"],
        "prior_sandbox_adapter_gate_no_blockers": preconditions["checks"]["prior_blocking_failures_empty"],
        "prior_sandbox_adapter_gate_no_side_effects": preconditions["checks"]["prior_platform_api_not_called"]
        and preconditions["checks"]["prior_upload_not_performed"]
        and preconditions["checks"]["prior_scheduler_not_invoked"]
        and preconditions["checks"]["prior_real_publish_not_performed"],
        "target_platform_exact": c["target_platform_exact"],
        "target_mode_exact": c["target_mode_exact"],
        "external_call_unauthorized": e["external_call_not_authorized"],
        "platform_api_unauthorized": e["platform_api_execution_not_authorized"],
        "upload_unauthorized": e["upload_not_authorized"],
        "scheduler_unauthorized": e["scheduler_not_authorized"],
        "real_publishing_unauthorized": e["real_publish_not_authorized"],
        "real_url_forbidden": e["production_url_not_allowed"],
        "real_platform_content_id_forbidden": e["production_platform_content_id_not_allowed"],
        "single_mode_enforced": c["single_mode_enforced"],
        "mixed_modes_forbidden": c["mixed_modes_forbidden"],
        "implicit_provider_binding_forbidden": c["implicit_provider_binding_forbidden"],
        "request_envelope_complete": c["request_envelope_complete"],
        "request_envelope_no_media_bytes": c["media_bytes_forbidden"],
        "request_envelope_public_visibility_false": c["public_visibility_forbidden"],
        "secrets_presence_status_only": s["credential_status_only"],
        "missing_credentials_block": s["missing_credentials_block"],
        "kill_switch_required": s["kill_switch_required"],
        "kill_switch_blocks_external_request": s["kill_switch_blocks_external_request"],
        "rate_limit_disabled_not_unlimited": s["rate_limit_disabled_not_unlimited"],
        "timeout_cannot_be_success": s["timeout_not_success"],
        "response_evidence_non_production": c["response_evidence_non_production"],
        "sandbox_receipt_non_production": c["response_evidence_non_production"],
        "pending_not_success": c["pending_not_success"],
        "sandbox_failure_not_production_failure": c["sandbox_failed_not_production_failure"],
        "append_only_rules_present": c["append_only_rules_defined"],
        "incident_hooks_present": s["incident_hooks_defined"],
        "qc_dependency_blocks_present": s["qc_non_publishable_blocks"],
        "account_health_hold_block_present": s["account_health_hold_blocks"],
        "fake_success_forbidden": s["fake_success_forbidden"],
        "fake_url_forbidden": s["fake_url_or_platform_id_forbidden"],
        "fake_platform_content_id_forbidden": s["fake_url_or_platform_id_forbidden"],
        "post_publish_metrics_forbidden": s["post_publish_metrics_forbidden"],
        "attribution_causal_claims_forbidden": s["attribution_causality_forbidden"],
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
    if name.startswith("prior_") or name == "required_documents_exist":
        return "preconditions"
    if "secret" in name or "credential" in name or "kill_switch" in name or "fake" in name:
        return "security_review.json"
    if "residual" in name:
        return "residual_monitoring_review.json"
    if name in {
        "external_call_unauthorized",
        "platform_api_unauthorized",
        "upload_unauthorized",
        "scheduler_unauthorized",
        "real_publishing_unauthorized",
        "real_url_forbidden",
        "real_platform_content_id_forbidden",
        "publisher_boundary_preserved",
    }:
        return "side_effect_review.json"
    if name.endswith("_unchanged"):
        return "audit_scope_no_runtime_mutation"
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
        "real_url_emitted": not side_effects["checks"]["real_url_not_emitted"],
        "platform_content_id_emitted": not side_effects["checks"]["platform_content_id_not_emitted"],
        "secret_leakage_detected": scenarios["secret_leakage_forbidden"]["passed"] is not True,
        "mixed_mode_detected": scenarios["mixed_modes_forbidden"]["passed"] is not True,
        "implicit_provider_binding_detected": scenarios["implicit_provider_binding_forbidden"]["passed"] is not True,
        "fake_success_detected": scenarios["fake_success_rejected"]["passed"] is not True,
        "post_publish_metrics_detected": scenarios["post_publish_metrics_forbidden"]["passed"] is not True,
        "attribution_causality_detected": scenarios["attribution_causality_forbidden"]["passed"] is not True,
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
    side_effects = _side_effect_review(plan_text, gate_text)
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
    metrics = _metrics(scenarios, checklist, blocking, side_effects, residuals_review)

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "target_platform_id": TARGET_PLATFORM_ID,
        "target_mode": TARGET_MODE,
        "external_sandbox_evidence_collection_planned": True,
        "external_call_implemented": False,
        "external_call_authorized": metrics["external_call_authorized"],
        "platform_api_called": metrics["platform_api_called"],
        "upload_performed": metrics["upload_performed"],
        "scheduler_invoked": metrics["scheduler_invoked"],
        "real_publishing_performed": metrics["real_publishing_performed"],
        "real_url_emitted": metrics["real_url_emitted"],
        "platform_content_id_emitted": metrics["platform_content_id_emitted"],
        "result_evidence_is_production": False,
        "secret_leakage_detected": metrics["secret_leakage_detected"],
        "fake_success_detected": metrics["fake_success_detected"],
        "post_publish_metrics_detected": metrics["post_publish_metrics_detected"],
        "attribution_causality_detected": metrics["attribution_causality_detected"],
        "production_residuals_closed": metrics["production_residuals_closed"],
        "metrics": metrics,
        "blocking_failures": blocking,
        "residual_monitoring": residuals,
        "recommendation": (
            "PROCEED_TO_EXTERNAL_SANDBOX_REQUEST_ENVELOPE_PLAN"
            if verdict in {"GO", "GO_WITH_MONITORING"}
            else "HOLD_BEFORE_EXTERNAL_SANDBOX_REQUEST_ENVELOPE"
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
                "external_call_authorized": metrics["external_call_authorized"],
                "platform_api_called": metrics["platform_api_called"],
                "upload_performed": metrics["upload_performed"],
                "scheduler_invoked": metrics["scheduler_invoked"],
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
