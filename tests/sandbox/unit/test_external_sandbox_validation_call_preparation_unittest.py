from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.publisher.external_sandbox_validation_call_preparation import (  # noqa: E402
    BOUNDARY_STATEMENT,
    PREPARATION_VERSION,
    TARGET_MODE,
    TARGET_PLATFORM_ID,
    SandboxValidationCallPreparationBuilder,
    SandboxValidationCallPreparationInput,
)


class SandboxValidationCallPreparationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = SandboxValidationCallPreparationBuilder()

    def _input(self, **overrides) -> SandboxValidationCallPreparationInput:
        payload = {
            "run_id": "run_preparation",
            "content_id": "content_preparation",
            "validation_envelope_ref": "validation_envelope:1",
            "publish_eligibility_trace_ref": "publish_eligibility:1",
            "qc_trace_ref": "qc_trace:1",
            "account_health_trace_ref": "health_trace:1",
            "artifact_manifest_ref": "artifact_manifest:1",
            "metadata_payload_ref": "metadata_payload:1",
            "credential_status": "present",
            "kill_switch_blocking": True,
            "rate_limit_state": "blocked",
        }
        payload.update(overrides)
        return SandboxValidationCallPreparationInput(**payload)

    def _build(self, **overrides):
        return self.builder.build(self._input(**overrides))

    def test_preparation_shape_is_serializable_and_inert(self) -> None:
        payload = self._build().to_dict()

        self.assertEqual(payload["preparation_version"], PREPARATION_VERSION)
        self.assertEqual(payload["target_platform_id"], TARGET_PLATFORM_ID)
        self.assertEqual(payload["target_mode"], TARGET_MODE)
        self.assertTrue(payload["preparation_complete"])
        self.assertTrue(payload["eligible_for_future_sandbox_validation_review"])
        self.assertFalse(payload["external_call_authorized"])
        self.assertFalse(payload["request_transformation_authorized"])
        self.assertFalse(payload["transport_payload_authorized"])
        self.assertFalse(payload["credential_value_access_authorized"])
        self.assertFalse(payload["runtime_integration_authorized"])
        self.assertEqual(payload["boundary_statement"], BOUNDARY_STATEMENT)
        json.dumps(payload, sort_keys=True)

    def test_future_eligibility_does_not_authorize_execution(self) -> None:
        payload = self._build().to_dict()

        self.assertTrue(payload["eligible_for_future_sandbox_validation_review"])
        self.assertFalse(payload["external_call_authorized"])
        self.assertFalse(payload["validation"]["external_call_authorized"])
        self.assertIn("future review only", " ".join(payload["validation"]["rationale"]))

    def test_target_platform_and_mode_are_fixed(self) -> None:
        payload = self._build(target_platform_id="BAD", target_mode="production").to_dict()

        self.assertEqual(payload["target_platform_id"], TARGET_PLATFORM_ID)
        self.assertEqual(payload["target_mode"], TARGET_MODE)
        self.assertIn("INVALID_TARGET_PLATFORM", payload["blocking_reasons"])
        self.assertIn("INVALID_TARGET_MODE", payload["blocking_reasons"])

    def test_secret_like_fields_are_detected_and_not_copied(self) -> None:
        payload = self._build(additional_context={"access_token": "secret-token-value"}).to_dict()
        serialized = json.dumps(payload, sort_keys=True)

        self.assertIn("SECRET_LIKE_FIELD_DETECTED", payload["blocking_reasons"])
        self.assertTrue(payload["validation"]["security_scan"]["secret_leakage_detected"])
        self.assertNotIn("secret-token-value", serialized)

    def test_forbidden_endpoint_url_and_transport_fields_block(self) -> None:
        cases = [
            ({"endpoint": "sandbox"}, "FORBIDDEN_FIELD_DETECTED"),
            ({"url": "https://example.invalid"}, "FORBIDDEN_FIELD_DETECTED"),
            ({"media_bytes": "abc123"}, "FORBIDDEN_FIELD_DETECTED"),
            ({"receipt": "fake"}, "FORBIDDEN_FIELD_DETECTED"),
            ({"platform_content_id": "fake"}, "FORBIDDEN_FIELD_DETECTED"),
            ({"payload": {"field": "value"}}, "TRANSPORT_PAYLOAD_DETECTED"),
        ]
        for context, reason in cases:
            with self.subTest(context=context):
                payload = self._build(additional_context=context).to_dict()
                self.assertIn(reason, payload["blocking_reasons"])
                self.assertFalse(payload["transport_payload_authorized"])

    def test_qc_and_account_health_blocks(self) -> None:
        cases = [
            ({"qc_status": "HOLD"}, "QC_HOLD"),
            ({"qc_status": "REJECT"}, "QC_REJECTED"),
            ({"qc_publishable": False}, "QC_NOT_PUBLISHABLE"),
            ({"account_health_decision": "HOLD"}, "ACCOUNT_HEALTH_HOLD"),
        ]
        for overrides, reason in cases:
            with self.subTest(reason=reason):
                payload = self._build(**overrides).to_dict()
                self.assertIn(reason, payload["blocking_reasons"])
                self.assertFalse(payload["external_call_authorized"])

    def test_missing_dependency_refs_block(self) -> None:
        payload = self._build(
            validation_envelope_ref=None,
            publish_eligibility_trace_ref=None,
            qc_trace_ref=None,
            account_health_trace_ref=None,
            artifact_manifest_ref=None,
            metadata_payload_ref=None,
        ).to_dict()

        for reason in [
            "MISSING_VALIDATION_ENVELOPE_REF",
            "MISSING_PUBLISH_ELIGIBILITY_TRACE",
            "MISSING_QC_TRACE",
            "MISSING_ACCOUNT_HEALTH_TRACE",
            "MISSING_ARTIFACT_MANIFEST",
            "MISSING_METADATA_PAYLOAD",
        ]:
            self.assertIn(reason, payload["blocking_reasons"])

    def test_credential_and_kill_switch_blocks_are_local_only(self) -> None:
        missing = self._build(credential_status="missing").to_dict()
        invalid = self._build(credential_status="bad-status").to_dict()
        kill_switch = self._build(kill_switch_blocking=False).to_dict()

        self.assertIn("PUBLISHER_CREDENTIALS_MISSING", missing["blocking_reasons"])
        self.assertIn("PUBLISHER_CREDENTIAL_VALIDATION_FAILED", invalid["blocking_reasons"])
        self.assertIn("KILL_SWITCH_NOT_BLOCKING", kill_switch["blocking_reasons"])
        self.assertFalse(missing["credential_status"]["credential_value_access_authorized"])

    def test_incident_hooks_do_not_include_secret_values(self) -> None:
        payload = self._build(additional_context={"api_key": "raw-api-key-value"}).to_dict()
        serialized_hooks = json.dumps(payload["incident_hooks"], sort_keys=True)

        self.assertIn("SANDBOX_VALIDATION_CALL_PREPARATION_SECRET_FIELD", {h["incident_type"] for h in payload["incident_hooks"]})
        self.assertNotIn("raw-api-key-value", serialized_hooks)

    def test_deterministic_replay(self) -> None:
        first = self.builder.deterministic_audit_json(self._build())
        second = self.builder.deterministic_audit_json(self._build())

        self.assertEqual(first, second)

    def test_static_source_has_no_network_or_platform_client_imports(self) -> None:
        module_paths = [
            ROOT / "backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation.py",
            ROOT / "backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation_security.py",
        ]
        forbidden_imports = [
            "import requests",
            "from requests",
            "import httpx",
            "from httpx",
            "import aiohttp",
            "from aiohttp",
            "import urllib.request",
            "import urllib3",
            "import socket",
            "googleapiclient",
            "boto3",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in module_paths)

        for token in forbidden_imports:
            with self.subTest(token=token):
                self.assertNotIn(token, combined)


if __name__ == "__main__":
    unittest.main()
