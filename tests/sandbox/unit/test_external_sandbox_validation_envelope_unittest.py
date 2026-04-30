from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.publisher.external_sandbox_envelope_security import (  # noqa: E402
    EXECUTABLE_HELPER_NAMES,
    HTTP_LIKE_FIELD_NAMES,
    executable_helper_names_on,
)
from app.creative.agents.publisher.external_sandbox_validation_envelope import (  # noqa: E402
    BOUNDARY_STATEMENT,
    ENVELOPE_TYPE,
    IDEMPOTENCY_NAMESPACE,
    TARGET_MODE,
    TARGET_PLATFORM_ID,
    ExternalSandboxValidationEnvelope,
    ExternalSandboxValidationEnvelopeBuilder,
    ExternalSandboxValidationEnvelopeInput,
)
from app.creative.agents.publisher.sandbox_contracts import PRODUCTION_RESIDUALS  # noqa: E402


class ExternalSandboxValidationEnvelopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = ExternalSandboxValidationEnvelopeBuilder()

    def _metadata(self, **overrides):
        payload = {
            "title": "Sandbox title",
            "description": "Sandbox description that must not be copied into transport.",
            "tags": ["sandbox", "validation"],
            "language": "en",
            "visibility_mode": "sandbox_only",
            "account_id": "account_sandbox",
            "runtime_policy_ref": "runtime_policy:sandbox",
            "metadata_trace_ref": "metadata_trace:sandbox",
        }
        payload.update(overrides)
        return payload

    def _input(self, **overrides) -> ExternalSandboxValidationEnvelopeInput:
        payload = {
            "run_id": "run_external_sandbox",
            "content_id": "content_external_sandbox",
            "artifact_manifest_ref": "artifact_manifest:external_sandbox",
            "metadata_payload_ref": "metadata_payload:external_sandbox",
            "qc_trace_ref": "qc_trace:external_sandbox",
            "account_health_trace_ref": "health_trace:external_sandbox",
            "strategy_ref": "strategy:external_sandbox",
            "publish_eligibility_trace_ref": "publish_eligibility:external_sandbox",
            "metadata": self._metadata(),
        }
        payload.update(overrides)
        return ExternalSandboxValidationEnvelopeInput(**payload)

    def _build(self, **overrides):
        return self.builder.build(self._input(**overrides))

    def _collect_keys(self, value):
        keys: set[str] = set()
        if isinstance(value, dict):
            for key, child in value.items():
                keys.add(str(key).lower())
                keys.update(self._collect_keys(child))
        elif isinstance(value, list):
            for child in value:
                keys.update(self._collect_keys(child))
        return keys

    def test_envelope_shape_contains_inert_markers(self) -> None:
        payload = self._build().to_dict()

        self.assertEqual(payload["envelope_type"], ENVELOPE_TYPE)
        self.assertEqual(payload["target_platform_id"], TARGET_PLATFORM_ID)
        self.assertEqual(payload["target_mode"], TARGET_MODE)
        self.assertEqual(payload["execution_capability"], "none")
        self.assertEqual(payload["transport_capability"], "none")
        self.assertTrue(payload["non_transportable"])
        self.assertFalse(payload["external_call_authorized"])
        self.assertFalse(payload["platform_api_execution_authorized"])
        self.assertFalse(payload["upload_authorized"])
        self.assertFalse(payload["scheduler_authorized"])
        self.assertFalse(payload["real_publish_authorized"])
        self.assertFalse(payload["media_bytes_included"])
        self.assertTrue(payload["production_identity_absent"])
        self.assertEqual(payload["boundary_statement"], BOUNDARY_STATEMENT)

    def test_output_has_no_exact_http_like_fields(self) -> None:
        keys = self._collect_keys(self._build().to_dict())

        self.assertFalse(HTTP_LIKE_FIELD_NAMES & keys)

    def test_no_executable_helpers_are_exposed(self) -> None:
        envelope = self._build()

        self.assertEqual(executable_helper_names_on(self.builder), [])
        self.assertEqual(executable_helper_names_on(envelope), [])
        self.assertFalse(EXECUTABLE_HELPER_NAMES & set(dir(ExternalSandboxValidationEnvelope)))

    def test_validation_envelope_naming_is_primary(self) -> None:
        self.assertIn("ValidationEnvelope", ExternalSandboxValidationEnvelope.__name__)
        self.assertIn("ValidationEnvelope", ExternalSandboxValidationEnvelopeBuilder.__name__)

    def test_static_source_has_no_network_or_platform_client_imports(self) -> None:
        module_paths = [
            ROOT / "backend/app/creative/agents/publisher/external_sandbox_validation_envelope.py",
            ROOT / "backend/app/creative/agents/publisher/external_sandbox_envelope_security.py",
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

    def test_metadata_projection_is_bounded_and_not_full_copy(self) -> None:
        payload = self._build().to_dict()
        projection = payload["metadata_projection"]
        serialized = json.dumps(payload, sort_keys=True)

        self.assertTrue(projection["title_present"])
        self.assertTrue(projection["description_present"])
        self.assertTrue(projection["tags_present"])
        self.assertEqual(projection["visibility_mode"], "sandbox_only")
        self.assertNotIn("Sandbox description that must not be copied", serialized)

    def test_credential_projection_status_only(self) -> None:
        payload = self._build(credential_status="missing").to_dict()
        serialized = json.dumps(payload, sort_keys=True)

        self.assertEqual(payload["credential_status"]["credential_status"], "missing")
        self.assertFalse(payload["credential_status"]["secret_values_logged"])
        self.assertFalse(payload["credential_status"]["secret_values_persisted"])
        self.assertIn("PUBLISHER_CREDENTIALS_MISSING", payload["blocking_reasons"])
        self.assertNotIn("access-token-value", serialized)

    def test_secret_like_fields_block_and_values_are_not_copied(self) -> None:
        envelope = self._build(metadata=self._metadata(access_token="access-token-value"))
        payload = envelope.to_dict()
        serialized = json.dumps(payload, sort_keys=True)

        self.assertIn("SECRET_LEAKAGE_ATTEMPT", payload["blocking_reasons"])
        self.assertTrue(payload["validation_result"]["secret_leakage_detected"])
        self.assertIn(
            "EXTERNAL_SANDBOX_ENVELOPE_SECRET_LEAKAGE_ATTEMPT",
            {hook["incident_type"] for hook in payload["incident_hooks"]},
        )
        self.assertNotIn("access-token-value", serialized)

    def test_forbidden_publish_identity_fields_block_and_values_are_not_copied(self) -> None:
        envelope = self._build(
            metadata=self._metadata(
                published_url="https://example.invalid/fake",
                platform_content_id="fake-platform-id",
            )
        )
        payload = envelope.to_dict()
        serialized = json.dumps(payload, sort_keys=True)

        self.assertIn("FORBIDDEN_FIELD_DETECTED", payload["blocking_reasons"])
        self.assertTrue(payload["validation_result"]["forbidden_field_detected"])
        self.assertTrue(payload["production_identity_absent"])
        self.assertNotIn("https://example.invalid/fake", serialized)
        self.assertNotIn("fake-platform-id", serialized)

    def test_transport_shaped_input_blocks(self) -> None:
        payload = self._build(metadata=self._metadata(payload={"field": "value"})).to_dict()

        self.assertIn("TRANSPORT_PAYLOAD_SHAPE_DETECTED", payload["blocking_reasons"])
        self.assertTrue(payload["validation_result"]["transport_payload_detected"])
        self.assertIn(
            "EXTERNAL_SANDBOX_ENVELOPE_TRANSPORT_PAYLOAD_SHAPE",
            {hook["incident_type"] for hook in payload["incident_hooks"]},
        )

    def test_http_like_fields_block(self) -> None:
        payload = self._build(metadata=self._metadata(headers={"x": "y"})).to_dict()

        self.assertIn("HTTP_LIKE_FIELD_DETECTED", payload["blocking_reasons"])
        self.assertTrue(payload["validation_result"]["http_like_field_detected"])

    def test_mixed_mode_and_provider_binding_block(self) -> None:
        payload = self._build(modes=[TARGET_MODE, "production"], provider_binding="YouTube").to_dict()

        self.assertIn("MIXED_MODE_REJECTED", payload["blocking_reasons"])
        self.assertIn("IMPLICIT_PROVIDER_BINDING_REJECTED", payload["blocking_reasons"])

    def test_kill_switch_active_and_missing_block(self) -> None:
        active = self._build(kill_switch_status={"active": True}).to_dict()
        missing = self._build(kill_switch_status={"missing": True}).to_dict()

        self.assertIn("PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE", active["blocking_reasons"])
        self.assertIn("PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE", missing["blocking_reasons"])
        self.assertFalse(active["external_call_authorized"])
        self.assertFalse(missing["external_call_authorized"])

    def test_rate_limit_disabled_is_not_unlimited_and_authorized_requests_block(self) -> None:
        normal = self._build().to_dict()
        authorized = self._build(
            rate_limit_status={"sandbox_validation_requests_allowed": True}
        ).to_dict()
        ambiguous = self._build(
            rate_limit_status={"max_sandbox_validation_requests_per_minute": 1}
        ).to_dict()

        self.assertFalse(normal["rate_limit_status"]["sandbox_validation_requests_allowed"])
        self.assertFalse(normal["rate_limit_status"]["upload_requests_allowed"])
        self.assertFalse(normal["rate_limit_status"]["publish_requests_allowed"])
        self.assertIsNone(normal["rate_limit_status"]["max_sandbox_validation_requests_per_minute"])
        self.assertIn("RATE_LIMIT_REQUESTS_NOT_AUTHORIZED", authorized["blocking_reasons"])
        self.assertIn("RATE_LIMIT_DISABLED_STATE_AMBIGUOUS", ambiguous["blocking_reasons"])

    def test_qc_and_account_health_blocks(self) -> None:
        cases = [
            ({"qc_status": "REJECT"}, "QC_REJECTED"),
            ({"qc_status": "HOLD"}, "QC_HOLD"),
            ({"qc_publishable": False}, "QC_NOT_PUBLISHABLE"),
            ({"account_health_decision": "HOLD"}, "ACCOUNT_HEALTH_HOLD"),
        ]
        for overrides, reason in cases:
            with self.subTest(reason=reason):
                payload = self._build(**overrides).to_dict()
                self.assertIn(reason, payload["blocking_reasons"])
                self.assertFalse(payload["real_publish_authorized"])

    def test_missing_dependency_refs_block(self) -> None:
        payload = self._build(
            artifact_manifest_ref=None,
            metadata_payload_ref=None,
            qc_trace_ref=None,
            account_health_trace_ref=None,
            strategy_ref=None,
            publish_eligibility_trace_ref=None,
        ).to_dict()

        for reason in [
            "MISSING_ARTIFACT_MANIFEST",
            "MISSING_METADATA_PAYLOAD",
            "MISSING_QC_TRACE",
            "MISSING_ACCOUNT_HEALTH_TRACE",
            "MISSING_STRATEGY_CONTEXT",
            "MISSING_PUBLISH_ELIGIBILITY_TRACE",
        ]:
            self.assertIn(reason, payload["blocking_reasons"])

    def test_invalid_metadata_visibility_blocks(self) -> None:
        payload = self._build(metadata=self._metadata(visibility_mode="public")).to_dict()

        self.assertIn("PUBLIC_VISIBILITY_FORBIDDEN", payload["blocking_reasons"])
        self.assertEqual(payload["metadata_projection"]["visibility_mode"], "invalid_or_missing")
        self.assertFalse(payload["public_visibility_requested"])

    def test_idempotency_key_is_sandbox_namespaced_and_deterministic(self) -> None:
        first = self._build().idempotency_key
        second = self._build().idempotency_key
        changed = self._build(content_id="content_other").idempotency_key

        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)
        self.assertTrue(first.startswith(IDEMPOTENCY_NAMESPACE))

    def test_valid_envelope_does_not_authorize_external_execution_or_success(self) -> None:
        payload = self._build().to_dict()

        self.assertTrue(payload["validation_result"]["envelope_valid"])
        self.assertFalse(payload["validation_result"]["eligible_for_future_external_sandbox_validation"])
        self.assertFalse(payload["validation_result"]["external_call_authorized"])
        self.assertFalse(payload["validation_result"]["platform_api_execution_authorized"])
        self.assertFalse(payload["validation_result"]["upload_authorized"])
        self.assertFalse(payload["validation_result"]["scheduler_authorized"])
        self.assertFalse(payload["validation_result"]["real_publish_authorized"])

    def test_incident_hooks_do_not_include_secret_values(self) -> None:
        payload = self._build(metadata=self._metadata(client_secret="secret-value")).to_dict()
        hooks = json.dumps(payload["incident_hooks"], sort_keys=True)

        self.assertNotIn("secret-value", hooks)

    def test_deterministic_audit_serialization_replay(self) -> None:
        first = self.builder.deterministic_audit_json(self._build())
        second = self.builder.deterministic_audit_json(self._build())

        self.assertEqual(first, second)

    def test_residuals_remain_open(self) -> None:
        payload = self._build().to_dict()

        self.assertEqual(payload["residual_monitoring"], PRODUCTION_RESIDUALS)

    def test_contracts_are_json_serializable(self) -> None:
        json.dumps(self._input().to_dict(), sort_keys=True)
        json.dumps(self._build().to_dict(), sort_keys=True)


if __name__ == "__main__":
    unittest.main()
