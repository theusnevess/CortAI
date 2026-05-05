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

from app.creative.agents.publisher.external_sandbox_external_call_boundary import (  # noqa: E402
    BOUNDARY_RESIDUALS,
    BOUNDARY_STATE,
    BOUNDARY_TYPE,
    BOUNDARY_VERSION,
    GUARD_STATE,
    TARGET_MODE,
    TARGET_PLATFORM_ID,
    ExternalSandboxExternalCallBoundaryBuilder,
    ExternalSandboxExternalCallBoundaryInput,
)


class ExternalSandboxExternalCallBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = ExternalSandboxExternalCallBoundaryBuilder()

    def _input(self, **overrides) -> ExternalSandboxExternalCallBoundaryInput:
        payload = {
            "run_id": "run_boundary",
            "content_id": "content_boundary",
        }
        payload.update(overrides)
        return ExternalSandboxExternalCallBoundaryInput(**payload)

    def _build(self, **overrides):
        return self.builder.build(self._input(**overrides))

    def test_boundary_marker_contract_is_inert(self) -> None:
        payload = self._build().to_dict()

        self.assertEqual(payload["boundary_version"], BOUNDARY_VERSION)
        self.assertEqual(payload["boundary_type"], BOUNDARY_TYPE)
        self.assertEqual(payload["boundary_state"], BOUNDARY_STATE)
        self.assertEqual(payload["target_platform_id"], TARGET_PLATFORM_ID)
        self.assertEqual(payload["target_mode"], TARGET_MODE)
        self.assertEqual(payload["execution_capability"], "none")
        self.assertEqual(payload["transport_capability"], "none")
        self.assertEqual(payload["client_capability"], "none")
        self.assertEqual(payload["endpoint_capability"], "none")
        self.assertTrue(payload["non_transportable"])
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["pre_execution_only"])

    def test_no_external_or_transport_capability_is_authorized(self) -> None:
        payload = self._build().to_dict()

        for key in [
            "external_call_implemented",
            "external_call_authorized",
            "http_client_present",
            "http_client_allowed",
            "platform_sdk_present",
            "platform_sdk_allowed",
            "endpoint_present",
            "endpoint_allowed",
            "dns_network_present",
            "dns_network_allowed",
            "api_call_present",
            "api_call_allowed",
            "request_transformation_present",
            "request_transformation_authorized",
            "upload_present",
            "upload_authorized",
            "scheduler_present",
            "scheduler_authorized",
            "publish_present",
            "real_publish_authorized",
            "url_present",
            "url_emission_authorized",
            "platform_content_id_present",
            "platform_content_id_authorized",
            "receipt_present",
            "receipt_authorized",
            "credential_value_access_present",
            "credential_value_access_authorized",
            "authorization_header_present",
            "authorization_header_authorized",
            "fake_success_detected",
            "production_residuals_closed",
        ]:
            with self.subTest(key=key):
                self.assertFalse(payload[key])

    def test_guard_contract_is_blocking_only(self) -> None:
        guard = self._build().to_dict()["guard_contract"]

        self.assertEqual(guard["guard_state"], GUARD_STATE)
        self.assertTrue(guard["kill_switch_required"])
        self.assertTrue(guard["rate_limit_required"])
        self.assertTrue(guard["disabled_rate_limits_mean_not_authorized"])
        self.assertFalse(guard["external_call_authorized"])
        self.assertFalse(guard["guard_pass_means_external_success"])

    def test_each_requested_external_surface_is_rejected(self) -> None:
        cases = [
            ("external_call_requested", "EXTERNAL_CALL_SURFACE_REJECTED"),
            ("http_client_requested", "HTTP_CLIENT_SURFACE_REJECTED"),
            ("platform_sdk_requested", "PLATFORM_SDK_SURFACE_REJECTED"),
            ("endpoint_requested", "ENDPOINT_SURFACE_REJECTED"),
            ("dns_network_requested", "DNS_NETWORK_SURFACE_REJECTED"),
            ("api_call_requested", "API_CALL_SURFACE_REJECTED"),
            ("request_transformation_requested", "REQUEST_TRANSFORMATION_SURFACE_REJECTED"),
            ("upload_requested", "UPLOAD_SURFACE_REJECTED"),
            ("scheduler_requested", "SCHEDULER_SURFACE_REJECTED"),
            ("publish_requested", "PUBLISH_SURFACE_REJECTED"),
            ("url_requested", "URL_EMISSION_REJECTED"),
            ("platform_content_id_requested", "PLATFORM_CONTENT_ID_REJECTED"),
            ("receipt_requested", "RECEIPT_REJECTED"),
            ("credential_value_access_requested", "CREDENTIAL_VALUE_ACCESS_REJECTED"),
            ("authorization_header_requested", "AUTHORIZATION_HEADER_REJECTED"),
            ("success_claimed", "FAKE_SUCCESS_REJECTED"),
        ]

        for field_name, reason in cases:
            with self.subTest(field_name=field_name):
                payload = self._build(**{field_name: True}).to_dict()
                self.assertIn(reason, payload["blocking_reasons"])
                self.assertFalse(payload["external_call_authorized"])
                self.assertFalse(payload["real_publish_authorized"])

    def test_invalid_target_and_mode_block_without_mixed_execution(self) -> None:
        payload = self._build(target_platform_id="REAL_PROVIDER", target_mode="production").to_dict()

        self.assertIn("INVALID_TARGET_PLATFORM", payload["blocking_reasons"])
        self.assertIn("INVALID_TARGET_MODE", payload["blocking_reasons"])
        self.assertEqual(payload["target_platform_id"], TARGET_PLATFORM_ID)
        self.assertEqual(payload["target_mode"], TARGET_MODE)

    def test_credentials_are_status_only_and_values_are_rejected(self) -> None:
        payload = self._build(
            credential_status="present",
            credential_payload={"access_token": "never-log-this"},
        ).to_dict()
        serialized = json.dumps(payload, sort_keys=True)

        self.assertIn("CREDENTIAL_VALUE_ACCESS_REJECTED", payload["blocking_reasons"])
        self.assertFalse(payload["credential_value_access_present"])
        self.assertFalse(payload["credential_value_access_authorized"])
        self.assertNotIn("never-log-this", serialized)

    def test_missing_or_invalid_credentials_block(self) -> None:
        missing = self._build(credential_status="missing").to_dict()
        invalid = self._build(credential_status="invalid_shape").to_dict()

        self.assertIn("PUBLISHER_CREDENTIALS_MISSING", missing["blocking_reasons"])
        self.assertIn("PUBLISHER_CREDENTIAL_VALIDATION_FAILED", invalid["blocking_reasons"])

    def test_kill_switch_and_rate_limit_unsafe_states_block(self) -> None:
        active = self._build(kill_switch_status={"active": True}).to_dict()
        weak_kill = self._build(kill_switch_status={"blocks_external_calls": False}).to_dict()
        allowed_rate = self._build(rate_limit_status={"sandbox_validation_requests_allowed": True}).to_dict()

        self.assertIn("PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE", active["blocking_reasons"])
        self.assertIn("KILL_SWITCH_DOES_NOT_BLOCK_EXTERNAL_CALLS", weak_kill["blocking_reasons"])
        self.assertIn("RATE_LIMIT_REQUESTS_NOT_AUTHORIZED", allowed_rate["blocking_reasons"])

    def test_incident_hooks_do_not_include_sensitive_or_platform_identity_values(self) -> None:
        payload = self._build(
            credential_payload={"client_secret": "secret-value"},
            url_requested=True,
            platform_content_id_requested=True,
            receipt_requested=True,
        ).to_dict()
        hooks = json.dumps(payload["incident_hooks"], sort_keys=True)

        self.assertIn("EXTERNAL_SANDBOX_URL_ATTEMPT", hooks)
        self.assertIn("EXTERNAL_SANDBOX_PLATFORM_CONTENT_ID_ATTEMPT", hooks)
        self.assertIn("EXTERNAL_SANDBOX_RECEIPT_ATTEMPT", hooks)
        self.assertNotIn("secret-value", hooks)
        self.assertNotIn("https://", hooks)

    def test_residuals_remain_open(self) -> None:
        payload = self._build().to_dict()

        self.assertEqual(payload["residual_monitoring"], BOUNDARY_RESIDUALS)
        self.assertIn("PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET", payload["residual_monitoring"])
        self.assertIn("EXTERNAL_CALL_NOT_IMPLEMENTED", payload["residual_monitoring"])

    def test_boundary_validity_does_not_create_readiness_or_success(self) -> None:
        payload = self._build().to_dict()

        self.assertEqual(payload["blocking_reasons"], [])
        self.assertIn("external execution remains absent", " ".join(payload["rationale"]))
        self.assertFalse(payload["external_call_authorized"])
        self.assertFalse(payload["fake_success_detected"])
        self.assertFalse(payload["production_residuals_closed"])

    def test_deterministic_audit_serialization_replay(self) -> None:
        first = self.builder.deterministic_audit_json(self._build())
        second = self.builder.deterministic_audit_json(self._build())

        self.assertEqual(first, second)

    def test_contracts_are_json_serializable(self) -> None:
        json.dumps(self._input().to_dict(), sort_keys=True)
        json.dumps(self._build().to_dict(), sort_keys=True)

    def test_static_source_has_no_network_or_platform_client_imports(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_external_call_boundary.py"
        source = source_path.read_text(encoding="utf-8")
        forbidden_import_pattern = re.compile(
            r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|urllib3|socket|googleapiclient|boto3)\b",
            re.MULTILINE,
        )

        self.assertIsNone(forbidden_import_pattern.search(source))

    def test_static_source_has_no_executable_helper_defs(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_external_call_boundary.py"
        source = source_path.read_text(encoding="utf-8")
        forbidden_def_pattern = re.compile(
            r"^\s*def\s+(to_request|as_request|to_payload|as_payload|to_http|to_headers|to_body|send|execute|post|put|patch|upload|publish|schedule)\s*\(",
            re.MULTILINE,
        )

        self.assertIsNone(forbidden_def_pattern.search(source))

    def test_static_source_has_no_endpoint_or_url_constants(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_external_call_boundary.py"
        source = source_path.read_text(encoding="utf-8")
        endpoint_constant_pattern = re.compile(
            r"^\s*[A-Z_]*(ENDPOINT|BASE_URL|UPLOAD_URL|PUBLISH_URL|CALLBACK_URL|WEBHOOK_URL|API_URL)[A-Z_]*\s*=",
            re.MULTILINE,
        )

        self.assertIsNone(endpoint_constant_pattern.search(source))


if __name__ == "__main__":
    unittest.main()
