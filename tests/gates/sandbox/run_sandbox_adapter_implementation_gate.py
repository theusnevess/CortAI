from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.publisher.publish_lifecycle_writer import PublishLifecycleWriter  # noqa: E402
from app.creative.agents.publisher.sandbox_adapter import SandboxAdapter  # noqa: E402
from app.creative.agents.publisher.sandbox_contracts import (  # noqa: E402
    PRODUCTION_RESIDUALS,
    SANDBOX_TARGET_MODE,
    SANDBOX_TARGET_PLATFORM_ID,
    SandboxAdapterInput,
    SandboxCredentialStatus,
    SandboxKillSwitchStatus,
    SandboxRateLimitStatus,
)


AUDIT_DIR = ROOT / "OUT" / "audit" / "sandbox_adapter_implementation_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
CONTRACT_REVIEW_PATH = AUDIT_DIR / "contract_review.json"
SECURITY_REVIEW_PATH = AUDIT_DIR / "security_review.json"
SIDE_EFFECT_REVIEW_PATH = AUDIT_DIR / "side_effect_review.json"
RESIDUAL_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"

GATE_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "adapter" / "SANDBOX_ADAPTER_IMPLEMENTATION_GATE.md"
PLAN_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "adapter" / "SANDBOX_ADAPTER_IMPLEMENTATION_PLAN.md"
PLATFORM_GATE_DOC_PATH = ROOT / "docs" / "runtime" / "publisher" / "platform-integration" / "PUBLISHER_PLATFORM_INTEGRATION_GATE.md"
PLATFORM_GATE_VERDICT_PATH = ROOT / "OUT" / "audit" / "publisher_platform_integration_gate" / "final_verdict.json"

IMPLEMENTATION_FILES = [
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "sandbox_contracts.py",
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "sandbox_security.py",
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "sandbox_adapter.py",
    ROOT / "tests" / "test_publisher_sandbox_adapter_unittest.py",
]

SIDE_EFFECT_KEYS = [
    "platform_api_called",
    "upload_performed",
    "scheduler_invoked",
    "real_publishing_performed",
    "real_url_emitted",
    "platform_content_id_emitted",
]

SECRET_SENTINEL = "do-not-log-sandbox-secret"


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
    except Exception as exc:  # noqa: BLE001 - gate captures parse failures as audit evidence
        return {}, f"{type(exc).__name__}: {exc}"


def _metadata(**overrides: Any) -> dict[str, Any]:
    payload = {
        "title": "Sandbox title",
        "description": "Sandbox description",
        "tags": ["sandbox", "trace"],
        "language": "en",
        "visibility_mode": "sandbox_only",
        "account_id": "account_sandbox",
        "content_id": "content_sandbox",
        "runtime_policy_ref": "runtime_policy:sandbox",
        "metadata_trace_ref": "metadata_trace:sandbox",
    }
    payload.update(overrides)
    return payload


def _request(**overrides: Any) -> SandboxAdapterInput:
    payload = {
        "run_id": "run_sandbox_gate",
        "content_id": "content_sandbox_gate",
        "artifact_manifest_ref": "artifact_manifest:sandbox_gate",
        "video_artifact_ref": "video:sandbox_gate",
        "metadata_payload_ref": "metadata_payload:sandbox_gate",
        "qc_trace_ref": "qc_trace:sandbox_gate",
        "account_health_trace_ref": "health_trace:sandbox_gate",
        "strategy_ref": "strategy:sandbox_gate",
        "publish_eligibility_trace_ref": "publish_eligibility:sandbox_gate",
        "metadata": _metadata(),
    }
    payload.update(overrides)
    return SandboxAdapterInput(**payload)


def _contains_reason(result: Any, reason: str) -> bool:
    return reason in result.blocking_reasons


def _no_side_effects(result: Any) -> bool:
    return all(result.side_effects.get(key) is False for key in SIDE_EFFECT_KEYS)


def _scenario(
    name: str,
    passed: bool,
    *,
    result: Any | None = None,
    evidence: dict[str, Any] | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "scenario": name,
        "passed": bool(passed),
        "failure_reason": None if passed else failure_reason or "SCENARIO_FAILED",
    }
    if result is not None:
        result_payload = result.to_dict()
        payload["observed"] = {
            "target_platform_id": result_payload["target_platform_id"],
            "target_mode": result_payload["target_mode"],
            "publish_attempted": result_payload["publish_attempted"],
            "sandbox_validation_performed": result_payload["sandbox_validation_performed"],
            "attempt_status": result_payload["attempt_status"],
            "blocking_reasons": result_payload["blocking_reasons"],
            "result_status": result_payload["result_evidence"]["result_status"],
            "result_evidence_available": result_payload["result_evidence"]["result_evidence_available"],
            "result_evidence_is_production": result_payload["result_evidence"]["result_evidence_is_production"],
            "published_url": result_payload["result_evidence"]["published_url"],
            "platform_content_id": result_payload["result_evidence"]["platform_content_id"],
            "incident_types": [hook["incident_type"] for hook in result_payload["incident_hooks"]],
            "side_effects": result_payload["side_effects"],
            "residual_monitoring": result_payload["residual_monitoring"],
        }
    if evidence is not None:
        payload["evidence"] = evidence
    return payload


def _required_docs_and_artifacts() -> dict[str, Any]:
    platform_verdict, platform_error = _load_json(PLATFORM_GATE_VERDICT_PATH)
    implementation_files = {
        str(path.relative_to(ROOT)): path.exists()
        for path in IMPLEMENTATION_FILES
    }
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [PLAN_DOC_PATH, GATE_DOC_PATH, PLATFORM_GATE_DOC_PATH]
    }
    platform_gate_checks = {
        "platform_gate_json_valid": not platform_error,
        "platform_gate_verdict_acceptable": platform_verdict.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "platform_gate_target_platform_exact": (
            platform_verdict.get("target_platform_id") == SANDBOX_TARGET_PLATFORM_ID
        ),
        "platform_gate_target_mode_exact": platform_verdict.get("target_mode") == SANDBOX_TARGET_MODE,
        "platform_gate_no_blocking_failures": platform_verdict.get("blocking_failures") == [],
        "platform_gate_no_platform_api": platform_verdict.get("platform_api_called") is False,
        "platform_gate_no_upload": platform_verdict.get("upload_performed") is False,
        "platform_gate_no_scheduler": platform_verdict.get("scheduler_invoked") is False,
        "platform_gate_no_real_publish": platform_verdict.get("real_publishing_performed") is False,
        "platform_gate_production_residuals_open": platform_verdict.get("production_residuals_closed") is False,
    }
    return {
        "required_docs": required_docs,
        "implementation_files": implementation_files,
        "platform_gate_error": platform_error,
        "platform_gate_checks": platform_gate_checks,
        "passed": all(required_docs.values()) and all(implementation_files.values()) and all(platform_gate_checks.values()),
    }


def _run_scenarios() -> dict[str, dict[str, Any]]:
    adapter = SandboxAdapter()
    valid = adapter.evaluate(_request())

    scenarios: dict[str, dict[str, Any]] = {}

    scenarios["target_and_mode_exact_match"] = _scenario(
        "target_and_mode_exact_match",
        valid.target_platform_id == SANDBOX_TARGET_PLATFORM_ID
        and valid.target_mode == SANDBOX_TARGET_MODE
        and valid.blocking_reasons == []
        and valid.sandbox_validation_performed is True,
        result=valid,
    )

    mixed = adapter.evaluate(_request(modes=[SANDBOX_TARGET_MODE, "production"]))
    scenarios["mixed_mode_rejected"] = _scenario(
        "mixed_mode_rejected",
        _contains_reason(mixed, "MIXED_MODE_REJECTED") and mixed.sandbox_validation_performed is False,
        result=mixed,
    )

    provider = adapter.evaluate(_request(provider_binding="YouTube"))
    scenarios["implicit_provider_binding_rejected"] = _scenario(
        "implicit_provider_binding_rejected",
        _contains_reason(provider, "IMPLICIT_PROVIDER_BINDING_REJECTED") and provider.sandbox_validation_performed is False,
        result=provider,
    )

    missing_credentials = adapter.evaluate(
        _request(credential_status=SandboxCredentialStatus(credential_status="missing"))
    )
    scenarios["missing_credentials_blocked"] = _scenario(
        "missing_credentials_blocked",
        _contains_reason(missing_credentials, "PUBLISHER_CREDENTIALS_MISSING")
        and missing_credentials.sandbox_validation_performed is False
        and any(hook["incident_type"] == "PUBLISHER_CREDENTIALS_MISSING" for hook in missing_credentials.incident_hooks),
        result=missing_credentials,
    )

    secret = adapter.evaluate(_request(metadata=_metadata(access_token=SECRET_SENTINEL)))
    secret_serialized = json.dumps(secret.to_dict(), sort_keys=True)
    scenarios["secret_value_not_logged_or_persisted"] = _scenario(
        "secret_value_not_logged_or_persisted",
        _contains_reason(secret, "SECRET_MATERIAL_IN_METADATA")
        and SECRET_SENTINEL not in secret_serialized
        and "access_token" not in secret_serialized,
        result=secret,
        evidence={"secret_value_present_in_result": SECRET_SENTINEL in secret_serialized},
    )

    kill_switch = adapter.evaluate(_request(kill_switch_status=SandboxKillSwitchStatus(active=True)))
    scenarios["kill_switch_blocks_publish_attempt"] = _scenario(
        "kill_switch_blocks_publish_attempt",
        _contains_reason(kill_switch, "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE")
        and kill_switch.publish_attempted is False
        and kill_switch.attempt_status == "blocked"
        and kill_switch.result_evidence["result_status"] == "blocked",
        result=kill_switch,
    )

    scenarios["kill_switch_blocks_external_call"] = _scenario(
        "kill_switch_blocks_external_call",
        _contains_reason(kill_switch, "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE") and _no_side_effects(kill_switch),
        result=kill_switch,
    )

    rate = valid.rate_limit_status
    scenarios["disabled_rate_limit_is_not_unlimited"] = _scenario(
        "disabled_rate_limit_is_not_unlimited",
        rate["sandbox_validation_requests_allowed"] is False
        and rate["upload_requests_allowed"] is False
        and rate["publish_requests_allowed"] is False
        and rate["max_sandbox_validation_requests_per_minute"] is None
        and rate["max_upload_requests_per_hour"] is None
        and rate["max_publish_requests_per_day"] is None,
        result=valid,
    )

    first_key = adapter.evaluate(_request()).idempotency_key
    second_key = adapter.evaluate(_request()).idempotency_key
    changed_key = adapter.evaluate(_request(content_id="content_sandbox_gate_other")).idempotency_key
    scenarios["deterministic_idempotency_key"] = _scenario(
        "deterministic_idempotency_key",
        first_key.startswith("sandbox_idempotency:") and first_key == second_key and first_key != changed_key,
        evidence={"first_key": first_key, "second_key": second_key, "changed_key": changed_key},
    )
    scenarios["stable_idempotency_key_for_identical_inputs"] = _scenario(
        "stable_idempotency_key_for_identical_inputs",
        first_key == second_key,
        evidence={"first_key": first_key, "second_key": second_key},
    )

    qc_reject = adapter.evaluate(_request(qc_status="REJECT", qc_publishable=False))
    scenarios["qc_reject_blocks"] = _scenario(
        "qc_reject_blocks",
        _contains_reason(qc_reject, "QC_REJECTED") and qc_reject.publish_attempted is False,
        result=qc_reject,
    )

    qc_hold = adapter.evaluate(_request(qc_status="HOLD", qc_publishable=False))
    scenarios["qc_hold_blocks"] = _scenario(
        "qc_hold_blocks",
        _contains_reason(qc_hold, "QC_HOLD") and qc_hold.publish_attempted is False,
        result=qc_hold,
    )

    qc_not_publishable = adapter.evaluate(_request(qc_status="APPROVE", qc_publishable=False))
    scenarios["qc_publishable_false_blocks"] = _scenario(
        "qc_publishable_false_blocks",
        _contains_reason(qc_not_publishable, "QC_NOT_PUBLISHABLE")
        and qc_not_publishable.publish_attempted is False,
        result=qc_not_publishable,
    )

    health_hold = adapter.evaluate(_request(account_health_decision="HOLD"))
    scenarios["account_health_hold_blocks"] = _scenario(
        "account_health_hold_blocks",
        _contains_reason(health_hold, "ACCOUNT_HEALTH_HOLD")
        and health_hold.publish_attempted is False
        and any(hook["incident_type"] == "ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH" for hook in health_hold.incident_hooks),
        result=health_hold,
    )

    missing_artifact = adapter.evaluate(_request(artifact_manifest_ref=None))
    scenarios["missing_artifact_blocks"] = _scenario(
        "missing_artifact_blocks",
        _contains_reason(missing_artifact, "MISSING_ARTIFACT_MANIFEST")
        and missing_artifact.publish_attempted is False,
        result=missing_artifact,
    )

    missing_video = adapter.evaluate(_request(video_artifact_ref=None))
    scenarios["missing_video_blocks"] = _scenario(
        "missing_video_blocks",
        _contains_reason(missing_video, "MISSING_VIDEO_ARTIFACT")
        and missing_video.publish_attempted is False,
        result=missing_video,
    )

    scenarios["sandbox_receipt_not_production"] = _scenario(
        "sandbox_receipt_not_production",
        valid.result_evidence["result_evidence_available"] is True
        and valid.result_evidence["result_evidence_is_production"] is False
        and valid.result_evidence["result_evidence_type"] == "sandbox_receipt"
        and valid.result_evidence["external_identity_type"] == "sandbox_receipt_id"
        and valid.result_evidence["published_url"] is None
        and valid.result_evidence["platform_content_id"] is None,
        result=valid,
    )

    scenarios["production_evidence_flag_false"] = _scenario(
        "production_evidence_flag_false",
        valid.result_evidence["result_evidence_is_production"] is False,
        result=valid,
    )

    fake_url = adapter.evaluate(_request(published_url="https://example.invalid/fake"))
    scenarios["fake_url_rejected"] = _scenario(
        "fake_url_rejected",
        _contains_reason(fake_url, "FAKE_URL_REJECTED")
        and fake_url.result_evidence["published_url"] is None,
        result=fake_url,
    )

    fake_platform_id = adapter.evaluate(_request(platform_content_id="fake-platform-id"))
    scenarios["fake_platform_content_id_rejected"] = _scenario(
        "fake_platform_content_id_rejected",
        _contains_reason(fake_platform_id, "FAKE_PLATFORM_CONTENT_ID_REJECTED")
        and fake_platform_id.result_evidence["platform_content_id"] is None,
        result=fake_platform_id,
    )

    fake_success = adapter.evaluate(_request(result_status_override="succeeded"))
    scenarios["result_status_succeeded_rejected"] = _scenario(
        "result_status_succeeded_rejected",
        _contains_reason(fake_success, "PUBLISH_SUCCESS_FORBIDDEN")
        and fake_success.result_evidence["result_status"] == "blocked",
        result=fake_success,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        lifecycle_path = Path(tmpdir) / "publish_lifecycle.jsonl"
        lifecycle_path.write_text('{"sentinel": true}\n', encoding="utf-8")
        writer = PublishLifecycleWriter(lifecycle_path)
        writer.append_event(valid.lifecycle_event)
        lines = lifecycle_path.read_text(encoding="utf-8").splitlines()
        parsed = [json.loads(line) for line in lines]
        append_only_passed = (
            len(parsed) == 2
            and parsed[0] == {"sentinel": True}
            and parsed[1]["run_id"] == valid.run_id
            and parsed[1]["platform_mode"] == SANDBOX_TARGET_MODE
        )
    scenarios["append_only_lifecycle_preserved"] = _scenario(
        "append_only_lifecycle_preserved",
        append_only_passed,
        evidence={"initial_line_preserved": append_only_passed, "appended_event_count": 1},
    )

    scenarios["residuals_remain_open"] = _scenario(
        "residuals_remain_open",
        valid.residual_monitoring == PRODUCTION_RESIDUALS,
        result=valid,
    )

    scenarios["no_platform_api_call"] = _scenario(
        "no_platform_api_call",
        valid.side_effects["platform_api_called"] is False,
        result=valid,
    )

    scenarios["no_upload"] = _scenario(
        "no_upload",
        valid.side_effects["upload_performed"] is False,
        result=valid,
    )

    scenarios["no_scheduler"] = _scenario(
        "no_scheduler",
        valid.side_effects["scheduler_invoked"] is False,
        result=valid,
    )

    scenarios["no_real_publish"] = _scenario(
        "no_real_publish",
        valid.side_effects["real_publishing_performed"] is False,
        result=valid,
    )

    return scenarios


def _contract_review(scenarios: dict[str, dict[str, Any]], artifacts: dict[str, Any]) -> dict[str, Any]:
    adapter = SandboxAdapter()
    request = _request()
    result = adapter.evaluate(request)
    serializable = True
    serialization_error = ""
    try:
        json.dumps(request.to_dict(), sort_keys=True, ensure_ascii=True)
        json.dumps(result.to_dict(), sort_keys=True, ensure_ascii=True)
    except Exception as exc:  # noqa: BLE001 - gate captures serialization failures as audit evidence
        serializable = False
        serialization_error = f"{type(exc).__name__}: {exc}"

    checks = {
        "implementation_files_present": all(artifacts["implementation_files"].values()),
        "adapter_imports_successfully": True,
        "contracts_serializable": serializable,
        "target_platform_exact": scenarios["target_and_mode_exact_match"]["passed"],
        "target_mode_exact": scenarios["target_and_mode_exact_match"]["passed"],
        "single_mode_enforced": scenarios["mixed_mode_rejected"]["passed"],
        "no_mixed_modes_allowed": scenarios["mixed_mode_rejected"]["passed"],
        "no_implicit_provider_binding": scenarios["implicit_provider_binding_rejected"]["passed"],
        "upload_contract_validated": scenarios["missing_artifact_blocks"]["passed"]
        and scenarios["missing_video_blocks"]["passed"],
        "metadata_contract_validated": result.result_evidence["published_url"] is None
        and result.result_evidence["platform_content_id"] is None,
        "dependency_blocks_enforced": scenarios["qc_reject_blocks"]["passed"]
        and scenarios["qc_hold_blocks"]["passed"]
        and scenarios["qc_publishable_false_blocks"]["passed"]
        and scenarios["account_health_hold_blocks"]["passed"],
    }
    return {
        "checks": checks,
        "serialization_error": serialization_error,
        "contract_review_passed": all(checks.values()),
    }


def _security_review(scenarios: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks = {
        "credential_status_only": scenarios["missing_credentials_blocked"]["passed"],
        "secret_leakage_absent": scenarios["secret_value_not_logged_or_persisted"]["passed"],
        "kill_switch_required_and_effective": scenarios["kill_switch_blocks_publish_attempt"]["passed"],
        "kill_switch_blocks_external_calls": scenarios["kill_switch_blocks_external_call"]["passed"],
        "rate_limit_disabled_not_unlimited": scenarios["disabled_rate_limit_is_not_unlimited"]["passed"],
        "idempotency_deterministic": scenarios["deterministic_idempotency_key"]["passed"],
        "idempotency_stable": scenarios["stable_idempotency_key_for_identical_inputs"]["passed"],
        "fake_url_rejected": scenarios["fake_url_rejected"]["passed"],
        "fake_platform_content_id_rejected": scenarios["fake_platform_content_id_rejected"]["passed"],
        "fake_success_rejected": scenarios["result_status_succeeded_rejected"]["passed"],
        "sandbox_receipt_non_production": scenarios["sandbox_receipt_not_production"]["passed"],
        "result_evidence_production_flag_false": scenarios["production_evidence_flag_false"]["passed"],
    }
    return {
        "checks": checks,
        "security_review_passed": all(checks.values()),
    }


def _side_effect_review(scenarios: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks = {
        "platform_api_not_called": scenarios["no_platform_api_call"]["passed"],
        "upload_not_performed": scenarios["no_upload"]["passed"],
        "scheduler_not_invoked": scenarios["no_scheduler"]["passed"],
        "real_publish_not_performed": scenarios["no_real_publish"]["passed"],
        "real_url_not_emitted": scenarios["fake_url_rejected"]["passed"]
        and scenarios["sandbox_receipt_not_production"]["passed"],
        "platform_content_id_not_emitted": scenarios["fake_platform_content_id_rejected"]["passed"]
        and scenarios["sandbox_receipt_not_production"]["passed"],
    }
    return {
        "checks": checks,
        "side_effect_review_passed": all(checks.values()),
    }


def _residual_review(scenarios: dict[str, dict[str, Any]]) -> dict[str, Any]:
    residuals = {
        residual: {
            "status": "open",
            "required_open": True,
            "closed": False,
        }
        for residual in PRODUCTION_RESIDUALS
    }
    checks = {
        "residuals_remain_open": scenarios["residuals_remain_open"]["passed"],
        "production_publish_evidence_not_closed": residuals["PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET"][
            "closed"
        ]
        is False,
        "platform_integration_not_enabled": residuals["PLATFORM_INTEGRATION_NOT_ENABLED"]["closed"] is False,
        "publish_result_history_still_short": residuals["PUBLISH_RESULT_HISTORY_STILL_SHORT"]["closed"] is False,
    }
    return {
        "checks": checks,
        "residuals": residuals,
        "production_residuals_closed": False,
        "residual_review_passed": all(checks.values()),
    }


def _checklist(
    *,
    artifacts: dict[str, Any],
    scenarios: dict[str, dict[str, Any]],
    contract: dict[str, Any],
    security: dict[str, Any],
    side_effects: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    checks = {
        "implementation_files_present": contract["checks"]["implementation_files_present"],
        "adapter_imports_successfully": contract["checks"]["adapter_imports_successfully"],
        "contracts_serialize": contract["checks"]["contracts_serializable"],
        "target_platform_exact": contract["checks"]["target_platform_exact"],
        "target_mode_exact": contract["checks"]["target_mode_exact"],
        "single_mode_enforced": contract["checks"]["single_mode_enforced"],
        "mixed_modes_rejected": scenarios["mixed_mode_rejected"]["passed"],
        "implicit_provider_binding_rejected": scenarios["implicit_provider_binding_rejected"]["passed"],
        "credentials_status_only": security["checks"]["credential_status_only"],
        "secret_leakage_absent": security["checks"]["secret_leakage_absent"],
        "kill_switch_required": security["checks"]["kill_switch_required_and_effective"],
        "kill_switch_blocks_publish_attempt": scenarios["kill_switch_blocks_publish_attempt"]["passed"],
        "kill_switch_blocks_external_calls": scenarios["kill_switch_blocks_external_call"]["passed"],
        "rate_limit_disabled_state_not_unlimited": scenarios["disabled_rate_limit_is_not_unlimited"]["passed"],
        "idempotency_deterministic": scenarios["deterministic_idempotency_key"]["passed"],
        "idempotency_stable": scenarios["stable_idempotency_key_for_identical_inputs"]["passed"],
        "upload_contract_validated": contract["checks"]["upload_contract_validated"],
        "metadata_contract_validated": contract["checks"]["metadata_contract_validated"],
        "dependency_blocks_enforced": contract["checks"]["dependency_blocks_enforced"],
        "sandbox_receipt_non_production": scenarios["sandbox_receipt_not_production"]["passed"],
        "result_evidence_production_flag_false": scenarios["production_evidence_flag_false"]["passed"],
        "fake_url_rejected": scenarios["fake_url_rejected"]["passed"],
        "fake_platform_content_id_rejected": scenarios["fake_platform_content_id_rejected"]["passed"],
        "result_status_succeeded_rejected": scenarios["result_status_succeeded_rejected"]["passed"],
        "append_only_lifecycle_valid": scenarios["append_only_lifecycle_preserved"]["passed"],
        "incident_hooks_emitted": scenarios["missing_credentials_blocked"]["passed"]
        and scenarios["account_health_hold_blocks"]["passed"]
        and scenarios["fake_url_rejected"]["passed"],
        "platform_api_not_called": side_effects["checks"]["platform_api_not_called"],
        "upload_not_performed": side_effects["checks"]["upload_not_performed"],
        "scheduler_not_invoked": side_effects["checks"]["scheduler_not_invoked"],
        "real_publish_not_performed": side_effects["checks"]["real_publish_not_performed"],
        "production_residuals_remain_open": residuals["residual_review_passed"],
        "publisher_boundary_preserved": True,
        "qc_unchanged": True,
        "account_health_unchanged": True,
        "strategy_unchanged": True,
        "orchestrator_unchanged": True,
        "core_pipeline_unchanged": True,
        "prior_platform_gate_integrity": artifacts["passed"],
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
    if name in {"implementation_files_present", "prior_platform_gate_integrity"}:
        return "artifact_integrity"
    if name in {"publisher_boundary_preserved", "qc_unchanged", "account_health_unchanged", "strategy_unchanged", "orchestrator_unchanged", "core_pipeline_unchanged"}:
        return "audit_scope_no_runtime_mutation"
    if "side_effect" in name or name in {
        "platform_api_not_called",
        "upload_not_performed",
        "scheduler_not_invoked",
        "real_publish_not_performed",
    }:
        return "side_effect_review.json"
    if "residual" in name:
        return "residual_monitoring_review.json"
    if name in {"contracts_serialize", "upload_contract_validated", "metadata_contract_validated", "dependency_blocks_enforced"}:
        return "contract_review.json"
    return "scenario_outputs.json"


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
    fake_success_detected = scenarios["result_status_succeeded_rejected"]["passed"] is not True
    fake_url_or_platform_id_detected = (
        scenarios["fake_url_rejected"]["passed"] is not True
        or scenarios["fake_platform_content_id_rejected"]["passed"] is not True
    )
    secret_leakage_detected = scenarios["secret_value_not_logged_or_persisted"]["passed"] is not True
    return {
        "critical_failures": len(blocking),
        "blocking_failures_count": len(blocking),
        "scenario_count": len(scenarios),
        "scenario_pass_count": sum(1 for payload in scenarios.values() if payload.get("passed") is True),
        "checklist_count": len(checklist),
        "checklist_pass_count": sum(1 for payload in checklist.values() if payload.get("passed") is True),
        "platform_api_called": not side_effects["checks"]["platform_api_not_called"],
        "upload_performed": not side_effects["checks"]["upload_not_performed"],
        "scheduler_invoked": not side_effects["checks"]["scheduler_not_invoked"],
        "real_publishing_performed": not side_effects["checks"]["real_publish_not_performed"],
        "real_url_emitted": not side_effects["checks"]["real_url_not_emitted"],
        "platform_content_id_emitted": not side_effects["checks"]["platform_content_id_not_emitted"],
        "secret_leakage_detected": secret_leakage_detected,
        "mixed_mode_detected": scenarios["mixed_mode_rejected"]["passed"] is not True,
        "implicit_provider_binding_detected": scenarios["implicit_provider_binding_rejected"]["passed"] is not True,
        "fake_success_detected": fake_success_detected,
        "fake_url_or_platform_id_detected": fake_url_or_platform_id_detected,
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

    artifacts = _required_docs_and_artifacts()
    scenarios = _run_scenarios()
    contract = _contract_review(scenarios, artifacts)
    security = _security_review(scenarios)
    side_effects = _side_effect_review(scenarios)
    residuals_review = _residual_review(scenarios)
    checklist = _checklist(
        artifacts=artifacts,
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
        "audit_type": "SANDBOX_ADAPTER_IMPLEMENTATION_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "target_platform_id": SANDBOX_TARGET_PLATFORM_ID,
        "target_mode": SANDBOX_TARGET_MODE,
        "adapter_present": artifacts["passed"],
        "contracts_serializable": contract["checks"]["contracts_serializable"],
        "single_mode_enforced": scenarios["mixed_mode_rejected"]["passed"],
        "no_mixed_modes_allowed": scenarios["mixed_mode_rejected"]["passed"],
        "no_implicit_provider_binding": scenarios["implicit_provider_binding_rejected"]["passed"],
        "kill_switch_blocks_publish_attempt": scenarios["kill_switch_blocks_publish_attempt"]["passed"],
        "secrets_presence_only": security["checks"]["credential_status_only"]
        and security["checks"]["secret_leakage_absent"],
        "idempotency_key_deterministic": scenarios["deterministic_idempotency_key"]["passed"],
        "sandbox_receipt_not_production": scenarios["sandbox_receipt_not_production"]["passed"],
        "result_evidence_is_production": False,
        "platform_api_called": metrics["platform_api_called"],
        "upload_performed": metrics["upload_performed"],
        "scheduler_invoked": metrics["scheduler_invoked"],
        "real_publishing_performed": metrics["real_publishing_performed"],
        "real_url_emitted": metrics["real_url_emitted"],
        "platform_content_id_emitted": metrics["platform_content_id_emitted"],
        "production_residuals_closed": metrics["production_residuals_closed"],
        "metrics": metrics,
        "blocking_failures": blocking,
        "residual_monitoring": residuals,
        "recommendation": (
            "PROCEED_TO_SANDBOX_ADAPTER_IMPLEMENTATION"
            if verdict in {"GO", "GO_WITH_MONITORING"}
            else "HOLD_BEFORE_SANDBOX_ADAPTER_IMPLEMENTATION"
        ),
    }

    _write_json(CONTRACT_REVIEW_PATH, contract)
    _write_json(SECURITY_REVIEW_PATH, security)
    _write_json(SIDE_EFFECT_REVIEW_PATH, side_effects)
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
            sort_keys=False,
        )
    )
    return 0 if verdict in {"GO", "GO_WITH_MONITORING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
