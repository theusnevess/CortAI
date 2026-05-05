from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

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


class PublisherSandboxAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = SandboxAdapter()

    def _metadata(self, **overrides):
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

    def _input(self, **overrides) -> SandboxAdapterInput:
        payload = {
            "run_id": "run_sandbox",
            "content_id": "content_sandbox",
            "artifact_manifest_ref": "artifact_manifest:sandbox",
            "video_artifact_ref": "video:sandbox",
            "metadata_payload_ref": "metadata_payload:sandbox",
            "qc_trace_ref": "qc_trace:sandbox",
            "account_health_trace_ref": "health_trace:sandbox",
            "strategy_ref": "strategy:sandbox",
            "publish_eligibility_trace_ref": "publish_eligibility:sandbox",
            "metadata": self._metadata(),
        }
        payload.update(overrides)
        return SandboxAdapterInput(**payload)

    def test_target_and_mode_exact_match_validates_sandbox_only(self) -> None:
        result = self.adapter.evaluate(self._input())
        payload = result.to_dict()

        self.assertEqual(payload["target_platform_id"], SANDBOX_TARGET_PLATFORM_ID)
        self.assertEqual(payload["target_mode"], SANDBOX_TARGET_MODE)
        self.assertEqual(payload["blocking_reasons"], [])
        self.assertTrue(payload["sandbox_validation_performed"])

    def test_mixed_mode_rejected(self) -> None:
        result = self.adapter.evaluate(self._input(modes=[SANDBOX_TARGET_MODE, "production"]))

        self.assertIn("MIXED_MODE_REJECTED", result.blocking_reasons)
        self.assertFalse(result.sandbox_validation_performed)

    def test_implicit_provider_binding_rejected(self) -> None:
        result = self.adapter.evaluate(self._input(provider_binding="YouTube"))

        self.assertIn("IMPLICIT_PROVIDER_BINDING_REJECTED", result.blocking_reasons)

    def test_missing_credentials_blocked_without_secret_value(self) -> None:
        result = self.adapter.evaluate(
            self._input(credential_status=SandboxCredentialStatus(credential_status="missing"))
        )
        payload = result.to_dict()
        serialized = json.dumps(payload, sort_keys=True)

        self.assertIn("PUBLISHER_CREDENTIALS_MISSING", payload["blocking_reasons"])
        self.assertIn("PUBLISHER_CREDENTIALS_MISSING", {hook["incident_type"] for hook in payload["incident_hooks"]})
        self.assertNotIn("access_token", serialized)
        self.assertNotIn("client_secret", serialized)

    def test_secret_material_in_metadata_blocks(self) -> None:
        result = self.adapter.evaluate(self._input(metadata=self._metadata(access_token="do-not-log")))

        self.assertIn("SECRET_MATERIAL_IN_METADATA", result.blocking_reasons)

    def test_kill_switch_blocks_publish_attempt_and_external_call(self) -> None:
        result = self.adapter.evaluate(
            self._input(kill_switch_status=SandboxKillSwitchStatus(active=True))
        )
        payload = result.to_dict()

        self.assertIn("PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE", payload["blocking_reasons"])
        self.assertFalse(payload["publish_attempted"])
        self.assertEqual(payload["attempt_status"], "blocked")
        self.assertFalse(payload["side_effects"]["platform_api_called"])
        self.assertFalse(payload["side_effects"]["upload_performed"])
        self.assertFalse(payload["side_effects"]["scheduler_invoked"])

    def test_disabled_rate_limit_is_not_unlimited(self) -> None:
        result = self.adapter.evaluate(self._input())
        rate = result.rate_limit_status

        self.assertFalse(rate["sandbox_validation_requests_allowed"])
        self.assertFalse(rate["upload_requests_allowed"])
        self.assertFalse(rate["publish_requests_allowed"])
        self.assertIsNone(rate["max_sandbox_validation_requests_per_minute"])
        self.assertIsNone(rate["max_upload_requests_per_hour"])
        self.assertIsNone(rate["max_publish_requests_per_day"])

    def test_rate_limit_authorization_is_blocked(self) -> None:
        result = self.adapter.evaluate(
            self._input(
                rate_limit_status=SandboxRateLimitStatus(sandbox_validation_requests_allowed=True)
            )
        )

        self.assertIn("RATE_LIMIT_REQUESTS_NOT_AUTHORIZED", result.blocking_reasons)

    def test_rate_limit_exceeded_blocks_and_traces(self) -> None:
        result = self.adapter.evaluate(
            self._input(rate_limit_status=SandboxRateLimitStatus(rate_limit_exceeded=True))
        )

        self.assertIn("PUBLISHER_RATE_LIMIT_EXCEEDED", result.blocking_reasons)
        self.assertIn("PUBLISHER_RATE_LIMIT_EXCEEDED", {hook["incident_type"] for hook in result.incident_hooks})

    def test_deterministic_and_stable_idempotency_key(self) -> None:
        first = self.adapter.evaluate(self._input()).idempotency_key
        second = self.adapter.evaluate(self._input()).idempotency_key
        changed = self.adapter.evaluate(self._input(content_id="content_other")).idempotency_key

        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)
        self.assertTrue(first.startswith("sandbox_idempotency:"))

    def test_qc_reject_hold_and_non_publishable_block(self) -> None:
        cases = [
            {"qc_status": "REJECT", "qc_publishable": False, "reason": "QC_REJECTED"},
            {"qc_status": "HOLD", "qc_publishable": False, "reason": "QC_HOLD"},
            {"qc_status": "APPROVE", "qc_publishable": False, "reason": "QC_NOT_PUBLISHABLE"},
        ]
        for case in cases:
            with self.subTest(case=case):
                result = self.adapter.evaluate(
                    self._input(qc_status=case["qc_status"], qc_publishable=case["qc_publishable"])
                )
                self.assertIn(case["reason"], result.blocking_reasons)
                self.assertFalse(result.publish_attempted)

    def test_account_health_hold_blocks(self) -> None:
        result = self.adapter.evaluate(self._input(account_health_decision="HOLD"))

        self.assertIn("ACCOUNT_HEALTH_HOLD", result.blocking_reasons)
        self.assertIn("ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH", {hook["incident_type"] for hook in result.incident_hooks})

    def test_missing_artifact_and_video_block(self) -> None:
        result = self.adapter.evaluate(self._input(artifact_manifest_ref=None, video_artifact_ref=None))

        self.assertIn("MISSING_ARTIFACT_MANIFEST", result.blocking_reasons)
        self.assertIn("MISSING_VIDEO_ARTIFACT", result.blocking_reasons)

    def test_missing_metadata_and_invalid_visibility_block(self) -> None:
        metadata = self._metadata(visibility_mode="public")
        metadata.pop("metadata_trace_ref")
        result = self.adapter.evaluate(self._input(metadata=metadata))

        self.assertIn("PUBLIC_VISIBILITY_FORBIDDEN", result.blocking_reasons)
        self.assertIn("MISSING_METADATA_FIELD:metadata_trace_ref", result.blocking_reasons)

    def test_sandbox_receipt_is_not_production(self) -> None:
        evidence = self.adapter.evaluate(self._input()).result_evidence

        self.assertEqual(evidence["result_status"], "sandbox_validated")
        self.assertTrue(evidence["result_evidence_available"])
        self.assertFalse(evidence["result_evidence_is_production"])
        self.assertEqual(evidence["external_identity_type"], "sandbox_receipt_id")
        self.assertIsNone(evidence["published_url"])
        self.assertIsNone(evidence["platform_content_id"])

    def test_fake_url_and_platform_content_id_rejected(self) -> None:
        result = self.adapter.evaluate(
            self._input(
                published_url="https://example.invalid/fake",
                platform_content_id="fake-platform-id",
            )
        )

        self.assertIn("FAKE_URL_REJECTED", result.blocking_reasons)
        self.assertIn("FAKE_PLATFORM_CONTENT_ID_REJECTED", result.blocking_reasons)
        self.assertIsNone(result.result_evidence["published_url"])
        self.assertIsNone(result.result_evidence["platform_content_id"])

    def test_result_status_succeeded_rejected(self) -> None:
        result = self.adapter.evaluate(self._input(result_status_override="succeeded"))

        self.assertIn("PUBLISH_SUCCESS_FORBIDDEN", result.blocking_reasons)

    def test_production_evidence_flag_true_rejected(self) -> None:
        result = self.adapter.evaluate(self._input(result_evidence_is_production_override=True))

        self.assertIn("PRODUCTION_EVIDENCE_FORBIDDEN", result.blocking_reasons)
        self.assertFalse(result.result_evidence["result_evidence_is_production"])

    def test_append_only_lifecycle_preserved(self) -> None:
        result = self.adapter.evaluate(self._input())
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "publish_lifecycle.jsonl"
            target.write_text('{"sentinel": true}\n', encoding="utf-8")
            writer = PublishLifecycleWriter(target)
            writer.append_event(result.lifecycle_event)

            lines = target.read_text(encoding="utf-8").splitlines()
            self.assertEqual(json.loads(lines[0]), {"sentinel": True})
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[1])["platform_mode"], SANDBOX_TARGET_MODE)

    def test_residuals_remain_open(self) -> None:
        result = self.adapter.evaluate(self._input())

        self.assertEqual(result.residual_monitoring, PRODUCTION_RESIDUALS)

    def test_no_side_effect_flags_are_ever_set(self) -> None:
        result = self.adapter.evaluate(self._input())

        self.assertEqual(
            result.side_effects,
            {
                "platform_api_called": False,
                "upload_performed": False,
                "scheduler_invoked": False,
                "real_publishing_performed": False,
                "real_url_emitted": False,
                "platform_content_id_emitted": False,
            },
        )

    def test_contracts_are_serializable(self) -> None:
        result = self.adapter.evaluate(self._input())

        json.dumps(self._input().to_dict(), sort_keys=True)
        json.dumps(result.to_dict(), sort_keys=True)

    def test_boundary_and_no_prediction_or_attribution_fields(self) -> None:
        payload = self.adapter.evaluate(self._input()).to_dict()
        serialized = json.dumps(payload, sort_keys=True).lower()

        self.assertIn("publisher is explicit publish authority", serialized)
        self.assertNotIn("expected_performance", serialized)
        self.assertNotIn("forecast", serialized)
        self.assertNotIn("predicted", serialized)
        self.assertNotIn("causal_claim", serialized)


if __name__ == "__main__":
    unittest.main()
