from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.publisher.external_sandbox_external_call_boundary import BOUNDARY_RESIDUALS  # noqa: E402
from app.creative.agents.publisher.external_sandbox_pre_execution_guard import (  # noqa: E402
    BLOCKED_FALSE_MEANING,
    GUARD_STATE,
    GUARD_TYPE,
    TARGET_MODE,
    TARGET_PLATFORM_ID,
    ExternalSandboxPreExecutionGuard,
    ExternalSandboxPreExecutionGuardInput,
)


class ExternalSandboxPreExecutionGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = ExternalSandboxPreExecutionGuard()

    def _input(self, **overrides) -> ExternalSandboxPreExecutionGuardInput:
        payload = {
            "run_id": "run_pre_execution_guard",
            "content_id": "content_pre_execution_guard",
            "boundary_ref": "boundary:pre_execution",
            "controlled_binding_ref": "controlled_binding:pre_execution",
            "validation_envelope_ref": "validation_envelope:pre_execution",
            "publish_eligibility_trace_ref": "publish_eligibility:pre_execution",
            "qc_trace_ref": "qc_trace:pre_execution",
            "account_health_trace_ref": "account_health_trace:pre_execution",
            "dependency_status": {
                "qc_status": "APPROVE",
                "qc_publishable": True,
                "account_health_decision": "SAFE",
                "credential_status": "present",
                "kill_switch_active": False,
                "kill_switch_missing": False,
                "rate_limit_requests_allowed": False,
            },
        }
        payload.update(overrides)
        return ExternalSandboxPreExecutionGuardInput(**payload)

    def _evaluate(self, **overrides):
        return self.guard.evaluate(self._input(**overrides))

    def test_no_crossing_attempt_does_not_authorize_execution(self) -> None:
        payload = self._evaluate().to_dict()

        self.assertEqual(payload["guard_type"], GUARD_TYPE)
        self.assertEqual(payload["guard_state"], GUARD_STATE)
        self.assertFalse(payload["crossing_attempt_detected"])
        self.assertFalse(payload["blocked"])
        self.assertEqual(payload["blocked_meaning"], BLOCKED_FALSE_MEANING)
        self.assertTrue(payload["blocked_false_does_not_authorize"])
        self.assertTrue(payload["guard_pass_does_not_mean_success"])
        self.assertFalse(payload["external_call_authorized"])
        self.assertFalse(payload["publish_authorized"])
        self.assertFalse(payload["production_residuals_closed"])

    def test_all_authorization_fields_are_false(self) -> None:
        payload = self._evaluate().to_dict()
        authorization_fields = [
            "external_call_authorized",
            "http_client_authorized",
            "platform_sdk_authorized",
            "endpoint_authorized",
            "dns_network_authorized",
            "api_call_authorized",
            "request_transformation_authorized",
            "upload_authorized",
            "scheduler_authorized",
            "publish_authorized",
            "url_authorized",
            "platform_content_id_authorized",
            "receipt_authorized",
            "credential_value_access_authorized",
            "authorization_header_authorized",
        ]

        for field in authorization_fields:
            with self.subTest(field=field):
                self.assertFalse(payload[field])
                self.assertFalse(payload["pre_execution_guard_trace"]["authorization_summary"][field])

    def test_each_crossing_attempt_is_blocked(self) -> None:
        cases = [
            ("external_call", "EXTERNAL_CALL_ATTEMPT_BLOCKED"),
            ("http_client", "HTTP_CLIENT_ATTEMPT_BLOCKED"),
            ("platform_sdk", "PLATFORM_SDK_ATTEMPT_BLOCKED"),
            ("endpoint", "ENDPOINT_ATTEMPT_BLOCKED"),
            ("dns_network", "DNS_NETWORK_ATTEMPT_BLOCKED"),
            ("api_call", "API_CALL_ATTEMPT_BLOCKED"),
            ("request_transformation", "REQUEST_TRANSFORMATION_ATTEMPT_BLOCKED"),
            ("upload", "UPLOAD_ATTEMPT_BLOCKED"),
            ("scheduler", "SCHEDULER_ATTEMPT_BLOCKED"),
            ("publish", "PUBLISH_ATTEMPT_BLOCKED"),
            ("url", "URL_EMISSION_ATTEMPT_BLOCKED"),
            ("platform_content_id", "PLATFORM_CONTENT_ID_ATTEMPT_BLOCKED"),
            ("receipt", "RECEIPT_ATTEMPT_BLOCKED"),
            ("credential_value_access", "CREDENTIAL_VALUE_ACCESS_ATTEMPT_BLOCKED"),
            ("authorization_header", "AUTHORIZATION_HEADER_ATTEMPT_BLOCKED"),
            ("fake_success", "FAKE_SUCCESS_ATTEMPT_BLOCKED"),
        ]

        for capability, reason in cases:
            with self.subTest(capability=capability):
                payload = self._evaluate(attempted_capabilities={capability: True}).to_dict()
                self.assertTrue(payload["crossing_attempt_detected"])
                self.assertTrue(payload["blocked"])
                self.assertIn(reason, payload["blocked_capabilities"])
                self.assertFalse(payload["external_call_authorized"])
                self.assertFalse(payload["publish_authorized"])

    def test_dependency_blocks_are_explicit(self) -> None:
        payload = self._evaluate(
            boundary_ref=None,
            controlled_binding_ref=None,
            validation_envelope_ref=None,
            publish_eligibility_trace_ref=None,
            qc_trace_ref=None,
            account_health_trace_ref=None,
        ).to_dict()

        for reason in [
            "MISSING_BOUNDARY_REF",
            "MISSING_CONTROLLED_BINDING_REF",
            "MISSING_VALIDATION_ENVELOPE_REF",
            "MISSING_PUBLISH_ELIGIBILITY_TRACE",
            "MISSING_QC_TRACE",
            "MISSING_ACCOUNT_HEALTH_TRACE",
        ]:
            self.assertIn(reason, payload["dependency_blocks"])
        self.assertTrue(payload["blocked"])
        self.assertFalse(payload["external_call_authorized"])

    def test_qc_and_account_health_blocks(self) -> None:
        cases = [
            ({"qc_status": "HOLD"}, "QC_HOLD"),
            ({"qc_status": "REJECT"}, "QC_REJECTED"),
            ({"qc_publishable": False}, "QC_NOT_PUBLISHABLE"),
            ({"account_health_decision": "HOLD"}, "ACCOUNT_HEALTH_HOLD"),
        ]
        for status_overrides, reason in cases:
            with self.subTest(reason=reason):
                status = dict(self._input().dependency_status)
                status.update(status_overrides)
                payload = self._evaluate(dependency_status=status).to_dict()
                self.assertIn(reason, payload["dependency_blocks"])
                self.assertTrue(payload["blocked"])
                self.assertFalse(payload["publish_authorized"])

    def test_credentials_kill_switch_and_rate_limit_blocks(self) -> None:
        cases = [
            ({"credential_status": "missing"}, "PUBLISHER_CREDENTIALS_MISSING"),
            ({"credential_status": "invalid_shape"}, "PUBLISHER_CREDENTIAL_VALIDATION_FAILED"),
            ({"kill_switch_active": True}, "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE"),
            ({"kill_switch_missing": True}, "PUBLISHER_PLATFORM_KILL_SWITCH_MISSING"),
            ({"kill_switch_blocks_external_calls": False}, "KILL_SWITCH_DOES_NOT_BLOCK_EXTERNAL_CALLS"),
            ({"rate_limit_requests_allowed": True}, "RATE_LIMIT_REQUESTS_NOT_AUTHORIZED"),
        ]
        for status_overrides, reason in cases:
            with self.subTest(reason=reason):
                status = dict(self._input().dependency_status)
                status.update(status_overrides)
                payload = self._evaluate(dependency_status=status).to_dict()
                self.assertIn(reason, payload["dependency_blocks"])
                self.assertTrue(payload["blocked"])
                self.assertFalse(payload["external_call_authorized"])

    def test_invalid_target_and_mode_block(self) -> None:
        payload = self._evaluate(target_platform_id="REAL_PROVIDER", target_mode="production").to_dict()

        self.assertIn("INVALID_TARGET_PLATFORM", payload["dependency_blocks"])
        self.assertIn("INVALID_TARGET_MODE", payload["dependency_blocks"])
        self.assertEqual(payload["target_platform_id"], TARGET_PLATFORM_ID)
        self.assertEqual(payload["target_mode"], TARGET_MODE)

    def test_incident_hooks_do_not_include_sensitive_values(self) -> None:
        payload = self._evaluate(
            attempted_capabilities={
                "url": True,
                "platform_content_id": True,
                "receipt": True,
                "credential_value_access": True,
            }
        ).to_dict()
        hooks = json.dumps(payload["incident_hooks"], sort_keys=True)

        self.assertIn("EXTERNAL_SANDBOX_PRE_EXECUTION_URL_ATTEMPT", hooks)
        self.assertIn("EXTERNAL_SANDBOX_PRE_EXECUTION_PLATFORM_CONTENT_ID_ATTEMPT", hooks)
        self.assertIn("EXTERNAL_SANDBOX_PRE_EXECUTION_RECEIPT_ATTEMPT", hooks)
        self.assertNotIn("https://", hooks)
        self.assertNotIn("secret", hooks.lower())

    def test_trace_is_reconstructible_and_authorization_false(self) -> None:
        payload = self._evaluate(attempted_capabilities={"external_call": True}).to_dict()
        trace = payload["pre_execution_guard_trace"]

        self.assertEqual(trace["boundary_ref"], "boundary:pre_execution")
        self.assertTrue(trace["crossing_attempt_detected"])
        self.assertIn("EXTERNAL_CALL_ATTEMPT_BLOCKED", trace["blocked_capabilities"])
        self.assertFalse(trace["authorization_summary"]["external_call_authorized"])
        self.assertEqual(trace["residual_monitoring"], BOUNDARY_RESIDUALS)

    def test_residuals_remain_open(self) -> None:
        payload = self._evaluate().to_dict()

        self.assertEqual(payload["residual_monitoring"], BOUNDARY_RESIDUALS)
        self.assertFalse(payload["production_residuals_closed"])
        self.assertIn("EXTERNAL_CALL_NOT_IMPLEMENTED", payload["residual_monitoring"])

    def test_deterministic_replay(self) -> None:
        first = self.guard.deterministic_audit_json(self._evaluate())
        second = self.guard.deterministic_audit_json(self._evaluate())
        changed = self.guard.deterministic_audit_json(self._evaluate(content_id="changed"))

        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)

    def test_contracts_are_json_serializable(self) -> None:
        json.dumps(self._input().to_dict(), sort_keys=True)
        json.dumps(self._evaluate().to_dict(), sort_keys=True)

    def test_static_source_has_no_network_or_platform_client_imports(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_pre_execution_guard.py"
        source = source_path.read_text(encoding="utf-8")
        forbidden_import_pattern = re.compile(
            r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|urllib3|socket|dns|googleapiclient|boto3)\b",
            re.MULTILINE,
        )

        self.assertIsNone(forbidden_import_pattern.search(source))

    def test_static_source_has_no_executable_helper_defs(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_pre_execution_guard.py"
        source = source_path.read_text(encoding="utf-8")
        forbidden_def_pattern = re.compile(
            r"^\s*def\s+(to_request|as_request|to_payload|as_payload|to_http|to_headers|to_body|send|execute|post|put|patch|call_api|upload|publish|schedule)\s*\(",
            re.MULTILINE,
        )

        self.assertIsNone(forbidden_def_pattern.search(source))

    def test_static_source_has_no_endpoint_or_url_constants(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_pre_execution_guard.py"
        source = source_path.read_text(encoding="utf-8")
        endpoint_constant_pattern = re.compile(
            r"^\s*[A-Z_]*(ENDPOINT|BASE_URL|UPLOAD_URL|PUBLISH_URL|CALLBACK_URL|WEBHOOK_URL|API_URL)[A-Z_]*\s*=",
            re.MULTILINE,
        )

        self.assertIsNone(endpoint_constant_pattern.search(source))


if __name__ == "__main__":
    unittest.main()
