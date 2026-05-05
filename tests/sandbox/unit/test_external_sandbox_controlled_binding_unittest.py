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

from app.creative.agents.publisher.external_sandbox_controlled_binding import (  # noqa: E402
    PROVIDER_BINDING_STATUS,
    PROVIDER_IDENTITY_CLASS,
    ExternalSandboxControlledBindingBuilder,
    ExternalSandboxControlledBindingInput,
)
from app.creative.agents.publisher.external_sandbox_validation_envelope import (  # noqa: E402
    TARGET_MODE,
    TARGET_PLATFORM_ID,
)
from app.creative.agents.publisher.sandbox_contracts import PRODUCTION_RESIDUALS  # noqa: E402


class ExternalSandboxControlledBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = ExternalSandboxControlledBindingBuilder()

    def _input(self, **overrides) -> ExternalSandboxControlledBindingInput:
        payload = {
            "run_id": "run_binding",
            "content_id": "content_binding",
            "qc_trace_ref": "qc_trace:binding",
            "account_health_trace_ref": "account_health_trace:binding",
        }
        payload.update(overrides)
        return ExternalSandboxControlledBindingInput(**payload)

    def _build(self, **overrides):
        return self.builder.build(self._input(**overrides))

    def test_binding_contract_is_inactive_and_pre_execution(self) -> None:
        payload = self._build().to_dict()

        self.assertFalse(payload["binding_active"])
        self.assertEqual(payload["execution_authority"], "none")
        self.assertEqual(payload["transport_authority"], "none")
        self.assertEqual(payload["provider_binding_status"], PROVIDER_BINDING_STATUS)
        self.assertEqual(payload["provider_identity_class"], PROVIDER_IDENTITY_CLASS)
        self.assertEqual(payload["target_platform_id"], TARGET_PLATFORM_ID)
        self.assertEqual(payload["target_mode"], TARGET_MODE)

    def test_no_external_capability_is_authorized(self) -> None:
        payload = self._build().to_dict()

        for key in [
            "external_call_authorized",
            "http_client_allowed",
            "platform_sdk_allowed",
            "endpoint_allowed",
            "network_access_allowed",
            "api_call_allowed",
            "upload_authorized",
            "scheduler_authorized",
            "real_publish_authorized",
            "url_authorized",
            "platform_content_id_authorized",
            "receipt_authorized",
            "credential_value_accessed",
            "transformation_layer_authorized",
        ]:
            with self.subTest(key=key):
                self.assertFalse(payload[key])

    def test_contract_has_no_defined_client_or_identity_surface(self) -> None:
        payload = self._build().to_dict()

        for key in [
            "endpoint_defined",
            "http_client_defined",
            "platform_sdk_defined",
            "network_access_defined",
            "api_call_defined",
            "upload_defined",
            "scheduler_defined",
            "publish_defined",
            "receipt_defined",
            "production_identity_defined",
        ]:
            with self.subTest(key=key):
                self.assertFalse(payload[key])

    def test_missing_and_invalid_credentials_block_without_secret_access(self) -> None:
        missing = self._build(credential_status="missing").to_dict()
        invalid = self._build(credential_status="invalid_shape").to_dict()

        self.assertIn("PUBLISHER_CREDENTIALS_MISSING", missing["blocking_reasons"])
        self.assertIn("PUBLISHER_CREDENTIAL_VALIDATION_FAILED", invalid["blocking_reasons"])
        self.assertFalse(missing["credential_status"]["secret_values_accessed"])
        self.assertFalse(invalid["credential_status"]["secret_values_accessed"])

    def test_credential_value_payload_is_rejected_and_not_copied(self) -> None:
        payload = self._build(credential_payload={"access_token": "do-not-log"}).to_dict()
        serialized = json.dumps(payload, sort_keys=True)

        self.assertIn("CREDENTIAL_VALUE_ACCESS_REJECTED", payload["blocking_reasons"])
        self.assertFalse(payload["credential_value_accessed"])
        self.assertNotIn("do-not-log", serialized)

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
                self.assertFalse(payload["binding_active"])

    def test_missing_qc_and_account_health_trace_blocks(self) -> None:
        payload = self._build(qc_trace_ref=None, account_health_trace_ref=None).to_dict()

        self.assertIn("MISSING_QC_TRACE", payload["blocking_reasons"])
        self.assertIn("MISSING_ACCOUNT_HEALTH_TRACE", payload["blocking_reasons"])

    def test_kill_switch_unsafe_states_block(self) -> None:
        active = self._build(kill_switch_status={"active": True}).to_dict()
        missing = self._build(kill_switch_status={"missing": True}).to_dict()
        weak = self._build(kill_switch_status={"blocks_external_calls": False}).to_dict()

        self.assertIn("PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE", active["blocking_reasons"])
        self.assertIn("PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE", missing["blocking_reasons"])
        self.assertIn("KILL_SWITCH_DOES_NOT_BLOCK_EXTERNAL_CALLS", weak["blocking_reasons"])

    def test_rate_limit_unsafe_states_block(self) -> None:
        allowed = self._build(rate_limit_status={"sandbox_validation_requests_allowed": True}).to_dict()
        ambiguous = self._build(rate_limit_status={"max_sandbox_validation_requests_per_minute": 1}).to_dict()

        self.assertIn("RATE_LIMIT_REQUESTS_NOT_AUTHORIZED", allowed["blocking_reasons"])
        self.assertIn("RATE_LIMIT_DISABLED_STATE_AMBIGUOUS", ambiguous["blocking_reasons"])

    def test_implicit_provider_and_non_abstract_identity_block(self) -> None:
        payload = self._build(provider_binding="YouTube", provider_identity_class="real_provider").to_dict()

        self.assertIn("IMPLICIT_PROVIDER_BINDING_REJECTED", payload["blocking_reasons"])
        self.assertIn("PROVIDER_IDENTITY_CLASS_NOT_ABSTRACT", payload["blocking_reasons"])

    def test_residuals_remain_open(self) -> None:
        payload = self._build().to_dict()

        self.assertEqual(payload["residual_monitoring"], PRODUCTION_RESIDUALS)

    def test_deterministic_replay(self) -> None:
        first = self.builder.deterministic_audit_json(self._build())
        second = self.builder.deterministic_audit_json(self._build())

        self.assertEqual(first, second)

    def test_contract_is_json_serializable(self) -> None:
        json.dumps(self._input().to_dict(), sort_keys=True)
        json.dumps(self._build().to_dict(), sort_keys=True)

    def test_static_source_has_no_network_or_platform_client_imports(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_controlled_binding.py"
        source = source_path.read_text(encoding="utf-8")
        forbidden_import_pattern = re.compile(
            r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|urllib3|socket|googleapiclient|boto3)\b",
            re.MULTILINE,
        )

        self.assertIsNone(forbidden_import_pattern.search(source))

    def test_static_source_has_no_executable_helper_defs(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_controlled_binding.py"
        source = source_path.read_text(encoding="utf-8")
        forbidden_def_pattern = re.compile(
            r"^\s*def\s+(to_request|as_request|to_payload|as_payload|to_http|to_headers|to_body|send|execute|post|put|patch|upload|publish|schedule)\s*\(",
            re.MULTILINE,
        )

        self.assertIsNone(forbidden_def_pattern.search(source))

    def test_static_source_has_no_endpoint_constants(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_controlled_binding.py"
        source = source_path.read_text(encoding="utf-8")
        endpoint_constant_pattern = re.compile(
            r"^\s*[A-Z_]*(ENDPOINT|BASE_URL|UPLOAD_URL|PUBLISH_URL|CALLBACK_URL|WEBHOOK_URL)[A-Z_]*\s*=",
            re.MULTILINE,
        )

        self.assertIsNone(endpoint_constant_pattern.search(source))


if __name__ == "__main__":
    unittest.main()
