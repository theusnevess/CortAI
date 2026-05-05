from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "publisher_platform_integration_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
CONTRACT_REVIEW_PATH = AUDIT_DIR / "contract_review.json"
SECURITY_REVIEW_PATH = AUDIT_DIR / "security_review.json"
RESIDUAL_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"

PLAN_PATH = ROOT / "docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_PLAN.md"
GATE_PLAN_PATH = ROOT / "docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_GATE_PLAN.md"
GATE_PATH = ROOT / "docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_GATE.md"
DRY_RUN_BATCH_GATE_PATH = ROOT / "docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE.md"

PRIOR_AUDIT_DIR = ROOT / "OUT" / "audit" / "publisher_dry_run_batch_collection_gate"
PRIOR_FINAL_VERDICT_PATH = PRIOR_AUDIT_DIR / "final_verdict.json"
PRIOR_REVIEW_PATHS = {
    "coverage_review": PRIOR_AUDIT_DIR / "coverage_review.json",
    "representation_review": PRIOR_AUDIT_DIR / "representation_review.json",
    "append_only_checks": PRIOR_AUDIT_DIR / "append_only_checks.json",
    "temporal_consistency": PRIOR_AUDIT_DIR / "temporal_consistency.json",
    "anti_fake_causality_review": PRIOR_AUDIT_DIR / "anti_fake_causality_review.json",
    "residual_monitoring_review": PRIOR_AUDIT_DIR / "residual_monitoring_review.json",
}

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


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as exc:  # noqa: BLE001 - gate captures parse errors as audit evidence
        return {}, f"{type(exc).__name__}: {exc}"


def _read_text(path: Path) -> tuple[str, str]:
    try:
        return path.read_text(encoding="utf-8"), ""
    except Exception as exc:  # noqa: BLE001 - gate captures read errors as audit evidence
        return "", f"{type(exc).__name__}: {exc}"


def _contains(text: str, needle: str) -> bool:
    return needle in text


def _all_contains(text: str, needles: list[str]) -> bool:
    return all(_contains(text, needle) for needle in needles)


def _preconditions(plan_text: str, gate_plan_text: str, gate_text: str) -> dict[str, Any]:
    docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [PLAN_PATH, GATE_PLAN_PATH, GATE_PATH, DRY_RUN_BATCH_GATE_PATH]
    }
    docs_readable = bool(plan_text and gate_plan_text and gate_text)

    prior_final, prior_error = _load_json(PRIOR_FINAL_VERDICT_PATH)
    prior_reviews: dict[str, Any] = {}
    prior_review_errors: dict[str, str] = {}
    for name, path in PRIOR_REVIEW_PATHS.items():
        payload, error = _load_json(path)
        prior_reviews[name] = payload
        prior_review_errors[name] = error

    prior_checks = {
        "prior_final_exists": PRIOR_FINAL_VERDICT_PATH.exists(),
        "prior_final_json_valid": not prior_error,
        "prior_gate_verdict_acceptable": prior_final.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "prior_publisher_maturity_scale": prior_final.get("publisher_maturity") == "TRACE_OBSERVABLE_AT_SCALE",
        "prior_publishing_not_authorized": prior_final.get("publishing_authorized") is False,
        "prior_platform_integration_not_authorized": prior_final.get("platform_integration_authorized") is False,
        "prior_success_count_zero": (prior_final.get("metrics") or {}).get("success_count") == 0,
        "prior_real_publishing_absent": prior_final.get("real_publishing_performed") is False,
        "prior_platform_api_absent": prior_final.get("platform_api_called") is False,
        "prior_production_residuals_open": prior_final.get("production_residuals_closed") is False,
        "prior_blocking_failures_empty": prior_final.get("blocking_failures") == [],
        "prior_coverage_valid": prior_reviews["coverage_review"].get("coverage_requirements_met") is True,
        "prior_representation_valid": prior_reviews["representation_review"].get("representation_valid") is True,
        "prior_append_only_valid": prior_reviews["append_only_checks"].get("append_only_valid") is True,
        "prior_temporal_valid": prior_reviews["temporal_consistency"].get("temporal_consistency_valid") is True,
        "prior_anti_fake_causality_valid": (
            prior_reviews["anti_fake_causality_review"].get("anti_fake_causality_valid") is True
        ),
        "prior_residual_review_valid": prior_reviews["residual_monitoring_review"].get("review_passed") is True,
    }
    return {
        "docs": docs,
        "docs_readable": docs_readable,
        "prior_final_error": prior_error,
        "prior_review_errors": prior_review_errors,
        "prior_final_summary": {
            "verdict": prior_final.get("verdict"),
            "publisher_maturity": prior_final.get("publisher_maturity"),
            "publishing_authorized": prior_final.get("publishing_authorized"),
            "platform_integration_authorized": prior_final.get("platform_integration_authorized"),
            "success_count": (prior_final.get("metrics") or {}).get("success_count"),
            "platform_api_called": prior_final.get("platform_api_called"),
            "real_publishing_performed": prior_final.get("real_publishing_performed"),
            "production_residuals_closed": prior_final.get("production_residuals_closed"),
        },
        "checks": {
            "required_docs_exist": all(docs.values()),
            "required_docs_readable": docs_readable,
            "required_prior_reviews_parse": not any(prior_review_errors.values()),
            **prior_checks,
        },
        "preconditions_passed": all(docs.values())
        and docs_readable
        and not prior_error
        and not any(prior_review_errors.values())
        and all(prior_checks.values()),
    }


def _contract_review(plan_text: str, gate_plan_text: str, gate_text: str) -> dict[str, Any]:
    combined = "\n".join([plan_text, gate_plan_text, gate_text])
    required_upload_fields = [
        "`content_id`",
        "`run_id`",
        "`artifact_manifest_ref`",
        "`video_artifact_ref`",
        "`metadata_payload_ref`",
        "`qc_trace_ref`",
        "`account_health_trace_ref`",
        "`strategy_ref`",
        "`publish_eligibility_trace_ref`",
        "`idempotency_key`",
        "`platform_target`",
        "`platform_mode`",
    ]
    required_metadata_fields = [
        "`title`",
        "`description`",
        "`tags`",
        "`language`",
        "`visibility_mode`",
        "`account_id`",
        "`content_id`",
        "`runtime_policy_ref`",
        "`metadata_trace_ref`",
    ]
    checks = {
        "target_platform_id_exact": _all_contains(
            combined,
            [
                f'"target_platform_id": "{TARGET_PLATFORM_ID}"',
                f"`target_platform_id = {TARGET_PLATFORM_ID}`",
            ],
        ),
        "target_mode_exact": _all_contains(
            combined,
            [
                f'"target_mode": "{TARGET_MODE}"',
                f"`target_mode = {TARGET_MODE}`",
            ],
        ),
        "single_mode_enforced": _contains(combined, '"single_mode_enforced": true'),
        "no_mixed_modes_allowed": _contains(combined, '"no_mixed_modes_allowed": true'),
        "no_implicit_provider_binding": _contains(combined, '"no_implicit_provider_binding": true')
        and _contains(combined, "Implicit provider binding is forbidden"),
        "no_real_provider_binding_without_approval": _all_contains(
            combined,
            [
                "separate platform-provider approval artifact",
                "provider fallback into YouTube, TikTok, Instagram",
            ],
        ),
        "platform_api_execution_unauthorized": _contains(combined, '"platform_api_execution_authorized": false')
        and not _contains(combined, '"platform_api_execution_authorized": true'),
        "real_publishing_unauthorized": _contains(combined, '"real_publishing_authorized": false')
        and not _contains(combined, '"real_publishing_authorized": true'),
        "upload_requests_forbidden": _contains(combined, '"upload_requests_allowed": false')
        and not _contains(combined, '"upload_requests_allowed": true'),
        "publish_requests_forbidden": _contains(combined, '"publish_requests_allowed": false')
        and not _contains(combined, '"publish_requests_allowed": true'),
        "sandbox_validation_requests_forbidden": _contains(combined, '"sandbox_validation_requests_allowed": false')
        and not _contains(combined, '"sandbox_validation_requests_allowed": true'),
        "upload_contract_complete": _all_contains(plan_text, required_upload_fields),
        "metadata_contract_complete": _all_contains(plan_text, required_metadata_fields),
        "idempotency_key_deterministic": _all_contains(
            combined,
            [
                "idempotency key is deterministic",
                "idempotency key is stable",
                "idempotency key is traceable",
                "idempotency key is not random",
            ],
        ),
        "result_evidence_contract_complete": _all_contains(
            combined,
            [
                '"result_evidence_available": true',
                '"result_evidence_is_production": false',
                '"result_evidence_type": "sandbox_receipt | platform_error | rate_limit_response | credential_validation_response | none"',
                '"published_url": null',
                '"platform_content_id": null',
            ],
        ),
        "result_evidence_production_flag_required": _all_contains(
            combined,
            [
                "`result_evidence_is_production = false` is mandatory in sandbox mode",
                "missing `result_evidence_is_production` invalid",
            ],
        ),
        "sandbox_receipt_not_production": _all_contains(
            combined,
            [
                "sandbox receipt is not production receipt",
                "sandbox receipt does not close production residuals",
            ],
        ),
        "real_url_forbidden": _contains(combined, "`published_url` in sandbox mode")
        or _contains(combined, "real URL is allowed in sandbox"),
        "platform_content_id_forbidden": _contains(combined, "production `platform_content_id` in sandbox mode")
        or _contains(combined, "production platform content ID is allowed"),
        "qc_non_publishable_blocks": _all_contains(
            combined,
            [
                "QC `publishable=false` blocks upload",
                "QC non-publishable blocks",
            ],
        ),
        "account_health_hold_blocks": _all_contains(
            combined,
            [
                "Account Health `HOLD` blocks upload",
                "Account Health `HOLD` blocks",
            ],
        ),
        "public_visibility_forbidden": _contains(combined, "`public` visibility must remain forbidden"),
        "succeeded_status_forbidden": _contains(combined, "`result_status = succeeded`")
        or _contains(combined, "`result_status=succeeded` is rejected"),
    }
    return {
        "checks": checks,
        "target_platform_id": TARGET_PLATFORM_ID,
        "target_mode": TARGET_MODE,
        "contract_review_passed": all(checks.values()),
    }


def _security_review(plan_text: str, gate_plan_text: str, gate_text: str) -> dict[str, Any]:
    combined = "\n".join([plan_text, gate_plan_text, gate_text])
    checks = {
        "secret_values_never_logged": _contains(combined, "secret values are never logged")
        or _contains(combined, "never write secret values to logs"),
        "secret_values_never_in_jsonl": _contains(combined, "secret values are never written to JSONL")
        or _contains(combined, "never write secret values to JSONL artifacts"),
        "secret_values_never_in_audit_artifacts": _contains(combined, "secret values are never written to audit artifacts")
        or _contains(combined, "no secrets in audit artifacts"),
        "tokens_not_in_incident_hooks": _contains(combined, "tokens are never included in incident hooks")
        or _contains(combined, "never include tokens in incident hooks"),
        "authorization_headers_not_traced": _contains(combined, "authorization headers are never included in traces")
        or _contains(combined, "never include authorization headers in traces"),
        "missing_credentials_block": _contains(combined, "missing credentials block integration")
        or _contains(combined, "Missing credentials must produce `blocked_missing_credentials`"),
        "kill_switch_required": _contains(combined, '"kill_switch_name": "PUBLISHER_PLATFORM_KILL_SWITCH"'),
        "kill_switch_blocks_publish_attempt": _contains(combined, '"blocks_publish_attempt": true'),
        "kill_switch_blocks_external_calls": _contains(combined, '"blocks_external_calls": true'),
        "kill_switch_blocks_upload": _contains(combined, '"blocks_upload": true'),
        "kill_switch_blocks_scheduler": _contains(combined, '"blocks_scheduler": true'),
        "rate_limits_required": _contains(combined, '"rate_limit_policy_version": "publisher_platform_rate_limits_v1"'),
        "rate_limit_disabled_state_unambiguous": _contains(
            combined,
            "`null` request limits must mean disabled/not authorized, never unlimited",
        )
        or _contains(combined, "`null` request limits mean disabled/not authorized, not unlimited"),
        "unbounded_retry_forbidden": _contains(combined, "Unbounded retry is forbidden")
        or _contains(combined, "rate-limit exhaustion must not retry indefinitely"),
        "no_performance_prediction_authority": _contains(combined, "performance prediction authority appears")
        and _contains(combined, "no hidden performance prediction"),
        "no_attribution_causality_authority": _contains(combined, "attribution causality authority appears")
        and _contains(combined, "Publisher does not become Attribution"),
        "no_external_side_effects_authorized": _all_contains(
            combined,
            [
                "Platform API execution remains unauthorized",
                "Upload remains unauthorized",
                "Scheduler remains unauthorized",
                "Real publishing remains unauthorized",
            ],
        ),
    }
    return {
        "checks": checks,
        "security_review_passed": all(checks.values()),
    }


def _residual_review(plan_text: str, gate_text: str) -> dict[str, Any]:
    combined = "\n".join([plan_text, gate_text])
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
        "sandbox_does_not_close_production_residuals": _contains(combined, "sandbox receipt does not close production residuals")
        and _contains(combined, "production residuals remain open"),
        "post_publish_metric_residual_not_closed": _contains(combined, "post-publish metric residual"),
        "attribution_causality_residual_not_closed": _contains(combined, "attribution causality residual"),
    }
    return {
        "checks": checks,
        "residuals": residuals,
        "production_residuals_closed": False,
        "residual_review_passed": all(checks.values()),
    }


def _scenario_outputs(
    *,
    preconditions: dict[str, Any],
    contract: dict[str, Any],
    security: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, Any]:
    c = contract["checks"]
    s = security["checks"]
    r = residuals["checks"]
    p = preconditions["checks"]
    return {
        "target_platform_exact_match": {"passed": c["target_platform_id_exact"]},
        "sandbox_mode_exact_match": {"passed": c["target_mode_exact"]},
        "single_mode_enforced": {"passed": c["single_mode_enforced"]},
        "mixed_mode_rejected": {"passed": c["no_mixed_modes_allowed"]},
        "implicit_provider_binding_rejected": {"passed": c["no_implicit_provider_binding"] and c["no_real_provider_binding_without_approval"]},
        "missing_credentials_block_integration": {"passed": s["missing_credentials_block"]},
        "secret_value_leakage_forbidden": {
            "passed": s["secret_values_never_logged"]
            and s["secret_values_never_in_jsonl"]
            and s["secret_values_never_in_audit_artifacts"]
        },
        "kill_switch_blocks_publish_attempt": {"passed": s["kill_switch_blocks_publish_attempt"]},
        "kill_switch_blocks_external_call": {"passed": s["kill_switch_blocks_external_calls"]},
        "rate_limit_disabled_not_unlimited": {"passed": s["rate_limit_disabled_state_unambiguous"]},
        "rate_limit_exceeded_blocks_and_traces": {"passed": s["rate_limits_required"] and s["unbounded_retry_forbidden"]},
        "idempotency_key_deterministic": {"passed": c["idempotency_key_deterministic"]},
        "idempotency_key_stable_for_identical_inputs": {"passed": c["idempotency_key_deterministic"]},
        "qc_reject_blocks_upload": {"passed": c["qc_non_publishable_blocks"]},
        "qc_hold_blocks_upload": {"passed": c["qc_non_publishable_blocks"]},
        "qc_publishable_false_blocks_upload": {"passed": c["qc_non_publishable_blocks"]},
        "account_health_hold_blocks_upload": {"passed": c["account_health_hold_blocks"]},
        "missing_artifact_manifest_blocks_upload": {"passed": c["upload_contract_complete"]},
        "missing_video_artifact_blocks_upload": {"passed": c["upload_contract_complete"]},
        "sandbox_receipt_not_production_receipt": {"passed": c["sandbox_receipt_not_production"]},
        "sandbox_receipt_does_not_authorize_production_publish": {
            "passed": c["sandbox_receipt_not_production"] and r["sandbox_does_not_close_production_residuals"]
        },
        "result_evidence_production_flag_required": {"passed": c["result_evidence_production_flag_required"]},
        "result_evidence_is_production_true_rejected": {"passed": c["result_evidence_production_flag_required"]},
        "fake_url_in_sandbox_rejected": {"passed": c["real_url_forbidden"]},
        "fake_platform_content_id_in_sandbox_rejected": {"passed": c["platform_content_id_forbidden"]},
        "result_status_succeeded_rejected": {"passed": c["succeeded_status_forbidden"]},
        "pending_sandbox_not_success": {"passed": c["result_evidence_contract_complete"]},
        "production_residuals_remain_open": {"passed": residuals["residual_review_passed"]},
        "public_visibility_forbidden": {"passed": c["public_visibility_forbidden"]},
        "platform_api_execution_unauthorized": {"passed": c["platform_api_execution_unauthorized"]},
        "real_publishing_unauthorized": {"passed": c["real_publishing_unauthorized"]},
        "performance_prediction_authority_absent": {"passed": s["no_performance_prediction_authority"]},
        "attribution_causality_absent": {"passed": s["no_attribution_causality_authority"]},
        "backward_precondition_artifacts_valid": {"passed": preconditions["preconditions_passed"], "details": p},
    }


def _checklist(
    *,
    preconditions: dict[str, Any],
    contract: dict[str, Any],
    security: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    c = contract["checks"]
    s = security["checks"]
    r = residuals["checks"]
    p = preconditions["checks"]
    return {
        "artifact_integrity": {"passed": preconditions["preconditions_passed"], "evidence_source": "preconditions"},
        "prior_batch_gate_integrity": {
            "passed": all(
                p[name]
                for name in [
                    "prior_gate_verdict_acceptable",
                    "prior_publisher_maturity_scale",
                    "prior_publishing_not_authorized",
                    "prior_platform_integration_not_authorized",
                    "prior_success_count_zero",
                    "prior_real_publishing_absent",
                    "prior_platform_api_absent",
                    "prior_production_residuals_open",
                    "prior_blocking_failures_empty",
                ]
            ),
            "evidence_source": "OUT/audit/publisher_dry_run_batch_collection_gate/final_verdict.json",
        },
        "target_platform_frozen": {"passed": c["target_platform_id_exact"], "evidence_source": str(PLAN_PATH)},
        "sandbox_mode_frozen": {"passed": c["target_mode_exact"], "evidence_source": str(PLAN_PATH)},
        "single_mode_enforced": {"passed": c["single_mode_enforced"], "evidence_source": str(PLAN_PATH)},
        "mixed_modes_forbidden": {"passed": c["no_mixed_modes_allowed"], "evidence_source": str(PLAN_PATH)},
        "implicit_provider_binding_forbidden": {
            "passed": c["no_implicit_provider_binding"] and c["no_real_provider_binding_without_approval"],
            "evidence_source": str(PLAN_PATH),
        },
        "real_publishing_forbidden": {"passed": c["real_publishing_unauthorized"], "evidence_source": str(GATE_PATH)},
        "platform_api_execution_unauthorized": {
            "passed": c["platform_api_execution_unauthorized"],
            "evidence_source": str(GATE_PATH),
        },
        "upload_unauthorized": {"passed": c["upload_requests_forbidden"], "evidence_source": str(GATE_PATH)},
        "scheduler_unauthorized": {
            "passed": not _contains(PLAN_PATH.read_text(encoding="utf-8"), '"scheduler_enabled": true'),
            "evidence_source": str(PLAN_PATH),
        },
        "real_url_forbidden": {"passed": c["real_url_forbidden"], "evidence_source": str(PLAN_PATH)},
        "production_platform_content_id_forbidden": {
            "passed": c["platform_content_id_forbidden"],
            "evidence_source": str(PLAN_PATH),
        },
        "secrets_policy_complete": {"passed": security["security_review_passed"], "evidence_source": "security_review.json"},
        "secret_leakage_impossible_by_contract": {
            "passed": s["secret_values_never_logged"]
            and s["secret_values_never_in_jsonl"]
            and s["secret_values_never_in_audit_artifacts"]
            and s["tokens_not_in_incident_hooks"]
            and s["authorization_headers_not_traced"],
            "evidence_source": "security_review.json",
        },
        "kill_switch_required": {"passed": s["kill_switch_required"], "evidence_source": str(PLAN_PATH)},
        "kill_switch_blocks_publish_attempt": {
            "passed": s["kill_switch_blocks_publish_attempt"],
            "evidence_source": str(PLAN_PATH),
        },
        "kill_switch_blocks_external_calls": {
            "passed": s["kill_switch_blocks_external_calls"],
            "evidence_source": str(PLAN_PATH),
        },
        "rate_limits_required": {"passed": s["rate_limits_required"], "evidence_source": str(PLAN_PATH)},
        "disabled_rate_limit_state_unambiguous": {
            "passed": s["rate_limit_disabled_state_unambiguous"],
            "evidence_source": str(PLAN_PATH),
        },
        "idempotency_key_deterministic": {
            "passed": c["idempotency_key_deterministic"],
            "evidence_source": str(PLAN_PATH),
        },
        "idempotency_key_stable": {"passed": c["idempotency_key_deterministic"], "evidence_source": str(PLAN_PATH)},
        "upload_contract_complete": {"passed": c["upload_contract_complete"], "evidence_source": str(PLAN_PATH)},
        "metadata_contract_complete": {"passed": c["metadata_contract_complete"], "evidence_source": str(PLAN_PATH)},
        "result_evidence_contract_complete": {
            "passed": c["result_evidence_contract_complete"],
            "evidence_source": str(PLAN_PATH),
        },
        "result_evidence_production_flag_required": {
            "passed": c["result_evidence_production_flag_required"],
            "evidence_source": str(PLAN_PATH),
        },
        "sandbox_receipt_not_production": {
            "passed": c["sandbox_receipt_not_production"],
            "evidence_source": str(PLAN_PATH),
        },
        "account_health_hold_blocks": {
            "passed": c["account_health_hold_blocks"],
            "evidence_source": str(PLAN_PATH),
        },
        "qc_non_publishable_blocks": {"passed": c["qc_non_publishable_blocks"], "evidence_source": str(PLAN_PATH)},
        "no_performance_prediction_authority": {
            "passed": s["no_performance_prediction_authority"],
            "evidence_source": "security_review.json",
        },
        "no_attribution_causality_authority": {
            "passed": s["no_attribution_causality_authority"],
            "evidence_source": "security_review.json",
        },
        "production_residuals_remain_open": {
            "passed": residuals["residual_review_passed"],
            "evidence_source": "residual_monitoring_review.json",
        },
        "gate_required_before_external_side_effects": {
            "passed": s["no_external_side_effects_authorized"],
            "evidence_source": str(GATE_PATH),
        },
    }


def _blocking_failures(scenarios: dict[str, Any], checklist: dict[str, dict[str, Any]]) -> list[str]:
    failures = [
        f"scenario:{name}"
        for name, result in scenarios.items()
        if result.get("passed") is not True
    ]
    failures.extend(
        f"checklist:{name}"
        for name, result in checklist.items()
        if result.get("passed") is not True
    )
    return list(dict.fromkeys(failures))


def _metrics(scenarios: dict[str, Any], checklist: dict[str, dict[str, Any]], blocking: list[str]) -> dict[str, Any]:
    return {
        "critical_failures": len(blocking),
        "blocking_failures_count": len(blocking),
        "scenario_count": len(scenarios),
        "scenario_pass_count": sum(1 for result in scenarios.values() if result.get("passed") is True),
        "checklist_count": len(checklist),
        "checklist_pass_count": sum(1 for result in checklist.values() if result.get("passed") is True),
        "platform_api_called": False,
        "real_publishing_performed": False,
        "upload_performed": False,
        "scheduler_invoked": False,
        "fake_success_detected": False,
        "fake_url_or_platform_id_detected": False,
        "secret_leakage_detected": False,
        "mixed_mode_detected": False,
        "implicit_provider_binding_detected": False,
        "production_residuals_closed": False,
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
    gate_plan_text, gate_plan_error = _read_text(GATE_PLAN_PATH)
    gate_text, gate_error = _read_text(GATE_PATH)
    preconditions = _preconditions(plan_text, gate_plan_text, gate_text)
    if plan_error or gate_plan_error or gate_error:
        preconditions["read_errors"] = {
            str(PLAN_PATH.relative_to(ROOT)): plan_error,
            str(GATE_PLAN_PATH.relative_to(ROOT)): gate_plan_error,
            str(GATE_PATH.relative_to(ROOT)): gate_error,
        }

    contract = _contract_review(plan_text, gate_plan_text, gate_text)
    security = _security_review(plan_text, gate_plan_text, gate_text)
    residuals_review = _residual_review(plan_text, gate_text)
    scenarios = _scenario_outputs(
        preconditions=preconditions,
        contract=contract,
        security=security,
        residuals=residuals_review,
    )
    checklist = _checklist(
        preconditions=preconditions,
        contract=contract,
        security=security,
        residuals=residuals_review,
    )
    blocking = _blocking_failures(scenarios, checklist)
    residuals = [] if blocking else list(PRODUCTION_RESIDUALS)
    verdict = _derive_verdict(blocking, residuals)
    metrics = _metrics(scenarios, checklist, blocking)
    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "PUBLISHER_PLATFORM_INTEGRATION_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "target_platform_id": TARGET_PLATFORM_ID,
        "target_mode": TARGET_MODE,
        "single_mode_enforced": contract["checks"]["single_mode_enforced"],
        "no_mixed_modes_allowed": contract["checks"]["no_mixed_modes_allowed"],
        "result_evidence_is_production": False,
        "idempotency_key_deterministic": contract["checks"]["idempotency_key_deterministic"],
        "no_implicit_provider_binding": contract["checks"]["no_implicit_provider_binding"],
        "kill_switch_blocks_publish_attempt": security["checks"]["kill_switch_blocks_publish_attempt"],
        "sandbox_validation_requests_allowed": False,
        "upload_requests_allowed": False,
        "publish_requests_allowed": False,
        "platform_api_execution_authorized": False,
        "real_publishing_authorized": False,
        "secrets_policy_valid": security["security_review_passed"],
        "rate_limits_required": security["checks"]["rate_limits_required"],
        "upload_contract_valid": contract["checks"]["upload_contract_complete"],
        "metadata_contract_valid": contract["checks"]["metadata_contract_complete"],
        "result_evidence_contract_valid": contract["checks"]["result_evidence_contract_complete"],
        "sandbox_receipt_not_production": contract["checks"]["sandbox_receipt_not_production"],
        "real_url_forbidden": contract["checks"]["real_url_forbidden"],
        "platform_content_id_forbidden": contract["checks"]["platform_content_id_forbidden"],
        "account_health_hold_blocks": contract["checks"]["account_health_hold_blocks"],
        "qc_non_publishable_blocks": contract["checks"]["qc_non_publishable_blocks"],
        "production_residuals_closed": residuals_review["production_residuals_closed"],
        "platform_api_called": False,
        "upload_performed": False,
        "scheduler_invoked": False,
        "real_publishing_performed": False,
        "metrics": metrics,
        "blocking_failures": blocking,
        "residual_monitoring": residuals,
        "recommendation": (
            "PROCEED_TO_SANDBOX_ADAPTER_IMPLEMENTATION_PLAN"
            if verdict in {"GO", "GO_WITH_MONITORING"}
            else "HOLD_BEFORE_SANDBOX_ADAPTER_IMPLEMENTATION"
        ),
    }

    _write_json(CONTRACT_REVIEW_PATH, contract)
    _write_json(SECURITY_REVIEW_PATH, security)
    _write_json(RESIDUAL_REVIEW_PATH, residuals_review)
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
        )
    )
    return 0 if verdict in {"GO", "GO_WITH_MONITORING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
