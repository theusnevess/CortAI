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


class ExternalSandboxExecutionSimulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.envelope = ExternalSandboxValidationEnvelopeBuilder().build(self._envelope_input())
        self.simulator = ExternalSandboxExecutionSimulation()

    def _metadata(self, **overrides):
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

    def _envelope_input(self, **overrides) -> ExternalSandboxValidationEnvelopeInput:
        payload = {
            "run_id": "run_simulation",
            "content_id": "content_simulation",
            "artifact_manifest_ref": "artifact_manifest:simulation",
            "metadata_payload_ref": "metadata_payload:simulation",
            "qc_trace_ref": "qc_trace:simulation",
            "account_health_trace_ref": "health_trace:simulation",
            "strategy_ref": "strategy:simulation",
            "publish_eligibility_trace_ref": "publish_eligibility:simulation",
            "metadata": self._metadata(),
        }
        payload.update(overrides)
        return ExternalSandboxValidationEnvelopeInput(**payload)

    def _simulate(self):
        return self.simulator.simulate(ExternalSandboxExecutionSimulationInput(envelope=self.envelope))

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

    def test_simulation_result_is_offline_only(self) -> None:
        payload = self._simulate().to_dict()

        self.assertTrue(payload["simulation_only"])
        self.assertFalse(payload["external_call_authorized"])
        self.assertFalse(payload["http_client_allowed"])
        self.assertFalse(payload["platform_sdk_allowed"])
        self.assertFalse(payload["endpoint_allowed"])
        self.assertFalse(payload["network_access_allowed"])
        self.assertFalse(payload["upload_authorized"])
        self.assertFalse(payload["scheduler_authorized"])
        self.assertFalse(payload["real_publish_authorized"])
        self.assertFalse(payload["transformation_layer_authorized"])

    def test_all_required_misuse_attempts_are_present_and_blocked(self) -> None:
        payload = self._simulate().to_dict()
        attempts = payload["misuse_attempts"]
        expected_types = {spec["attempt_type"] for spec in MISUSE_ATTEMPT_SPECS}
        observed_types = {attempt["attempt_type"] for attempt in attempts}

        self.assertEqual(expected_types, observed_types)
        self.assertGreaterEqual(len(attempts), 30)
        self.assertEqual(payload["unblocked_attempts_count"], 0)
        self.assertEqual(payload["blocked_attempts_count"], len(attempts))
        self.assertTrue(all(attempt["blocked"] for attempt in attempts))

    def test_each_attempt_preserves_no_execution_flags(self) -> None:
        for attempt in self._simulate().misuse_attempts:
            with self.subTest(attempt=attempt["attempt_type"]):
                self.assertFalse(attempt["external_call_authorized"])
                self.assertFalse(attempt["upload_authorized"])
                self.assertFalse(attempt["scheduler_authorized"])
                self.assertFalse(attempt["real_publish_authorized"])
                self.assertFalse(attempt["result_evidence_is_production"])

    def test_simulation_passed_is_not_readiness_or_success(self) -> None:
        payload = self._simulate().to_dict()

        self.assertTrue(payload["simulation_passed"])
        self.assertEqual(payload["simulation_passed_meaning"], SIMULATION_PASSED_MEANING)
        self.assertIn("misuse_attempts_blocked_offline only", " ".join(payload["rationale"]))
        self.assertFalse(payload["real_publish_authorized"])
        self.assertFalse(payload["result_evidence_is_production"])

    def test_fake_receipt_and_identity_are_never_generated(self) -> None:
        payload = self._simulate().to_dict()

        self.assertFalse(payload["simulated_receipt_generated"])
        self.assertFalse(payload["production_receipt_generated"])
        self.assertIsNone(payload["published_url"])
        self.assertIsNone(payload["platform_content_id"])
        self.assertFalse(payload["result_evidence_is_production"])

    def test_target_and_mode_remain_sandbox_only(self) -> None:
        payload = self._simulate().to_dict()

        self.assertEqual(payload["target_platform_id"], TARGET_PLATFORM_ID)
        self.assertEqual(payload["target_mode"], TARGET_MODE)

    def test_incident_hooks_exist_without_sensitive_values(self) -> None:
        payload = self._simulate().to_dict()
        serialized_hooks = json.dumps(payload["incident_hooks"], sort_keys=True)

        self.assertGreaterEqual(len(payload["incident_hooks"]), 10)
        self.assertIn("EXTERNAL_SANDBOX_SIMULATION_REQUEST_TRANSFORMATION_ATTEMPT", serialized_hooks)
        self.assertIn("EXTERNAL_SANDBOX_SIMULATION_FAKE_RECEIPT_ATTEMPT", serialized_hooks)
        self.assertNotIn("secret-value", serialized_hooks)
        self.assertNotIn("https://", serialized_hooks)

    def test_residuals_remain_open(self) -> None:
        payload = self._simulate().to_dict()

        self.assertFalse(payload["production_residuals_closed"])
        self.assertEqual(payload["residual_monitoring"], PRODUCTION_RESIDUALS)

    def test_deterministic_replay(self) -> None:
        first = self.simulator.deterministic_audit_json(self._simulate())
        second = self.simulator.deterministic_audit_json(self._simulate())

        self.assertEqual(first, second)

    def test_result_is_json_serializable(self) -> None:
        json.dumps(self._simulate().to_dict(), sort_keys=True)

    def test_no_top_level_transport_artifacts(self) -> None:
        payload = self._simulate().to_dict()

        self.assertNotIn("request", payload)
        self.assertNotIn("transport_payload", payload)
        self.assertNotIn("method", payload)
        self.assertNotIn("headers", payload)
        self.assertNotIn("body", payload)

    def test_static_source_has_no_network_or_platform_client_imports(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_execution_simulation.py"
        source = source_path.read_text(encoding="utf-8")
        forbidden_import_pattern = re.compile(
            r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|urllib3|socket|googleapiclient|boto3)\b",
            re.MULTILINE,
        )

        self.assertIsNone(forbidden_import_pattern.search(source))

    def test_static_source_has_no_executable_helper_defs(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_execution_simulation.py"
        source = source_path.read_text(encoding="utf-8")
        forbidden_def_pattern = re.compile(
            r"^\s*def\s+(to_request|as_request|to_payload|as_payload|to_http|to_headers|to_body|send|execute|post|put|patch|upload|publish|schedule)\s*\(",
            re.MULTILINE,
        )

        self.assertIsNone(forbidden_def_pattern.search(source))

    def test_static_source_has_no_endpoint_constants(self) -> None:
        source_path = ROOT / "backend/app/creative/agents/publisher/external_sandbox_execution_simulation.py"
        source = source_path.read_text(encoding="utf-8")
        endpoint_constant_pattern = re.compile(
            r"^\s*[A-Z_]*(ENDPOINT|BASE_URL|UPLOAD_URL|PUBLISH_URL|CALLBACK_URL|WEBHOOK_URL)[A-Z_]*\s*=",
            re.MULTILINE,
        )

        self.assertIsNone(endpoint_constant_pattern.search(source))

    def test_simulation_does_not_mutate_envelope(self) -> None:
        before = self.envelope.to_dict()
        self._simulate()
        after = self.envelope.to_dict()

        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
