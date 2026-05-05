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
from app.creative.agents.publisher.publish_semantics import BOUNDARY_STATEMENT  # noqa: E402
from app.creative.agents.publisher.publish_trace import (  # noqa: E402
    PublishTraceBuilder,
    PublishTraceValidationError,
)


class PublisherTraceImplementationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = PublishTraceBuilder()

    def _eligible_bundle(self):
        return self.builder.build_trace_bundle(
            run_id="run_1",
            content_id="content_1",
            qc_status="APPROVE",
            qc_publishable=True,
            qc_trace_ref="qc_trace:1",
            account_health_decision="SAFE",
            health_trace_ref="health_trace:1",
            strategy_ref="strategy:1",
            artifact_manifest_ref="artifact_manifest:1",
            dry_run=True,
        )

    def test_trace_builders_create_complete_dry_run_bundle(self) -> None:
        bundle = self._eligible_bundle()
        payload = bundle.to_dict()

        self.assertTrue(payload["publish_eligibility_trace"]["eligible"])
        self.assertFalse(payload["publish_attempt_trace"]["attempted"])
        self.assertEqual(payload["publish_attempt_trace"]["skip_reason"], "DRY_RUN_MODE")
        self.assertEqual(payload["publish_result_trace"]["result_status"], "not_attempted")
        self.assertIsNone(payload["publish_result_trace"]["published_url"])
        self.assertEqual(payload["publish_lifecycle_event"]["boundary_statement"], BOUNDARY_STATEMENT)

    def test_account_health_hold_blocks_eligibility(self) -> None:
        trace = self.builder.build_eligibility_trace(
            run_id="run_hold",
            content_id="content_hold",
            qc_status="APPROVE",
            qc_publishable=True,
            qc_trace_ref="qc_trace:hold",
            account_health_decision="HOLD",
            health_trace_ref="health_trace:hold",
            strategy_ref="strategy:hold",
            artifact_manifest_ref="artifact_manifest:hold",
        )

        self.assertFalse(trace.eligible)
        self.assertIn("ACCOUNT_HEALTH_HOLD", trace.blocking_reasons)

    def test_qc_reject_hold_and_non_publishable_block_eligibility(self) -> None:
        cases = [
            ("REJECT", False, "QC_REJECTED"),
            ("HOLD", False, "QC_HOLD"),
            ("APPROVE", False, "QC_NOT_PUBLISHABLE"),
        ]
        for qc_status, publishable, reason in cases:
            with self.subTest(qc_status=qc_status):
                trace = self.builder.build_eligibility_trace(
                    run_id=f"run_{qc_status}",
                    content_id=f"content_{qc_status}",
                    qc_status=qc_status,
                    qc_publishable=publishable,
                    qc_trace_ref=f"qc_trace:{qc_status}",
                    account_health_decision="SAFE",
                    health_trace_ref=f"health_trace:{qc_status}",
                    strategy_ref=f"strategy:{qc_status}",
                    artifact_manifest_ref=f"artifact_manifest:{qc_status}",
                )
                self.assertFalse(trace.eligible)
                self.assertIn(reason, trace.blocking_reasons)

    def test_missing_qc_trace_and_artifact_manifest_block_eligibility(self) -> None:
        trace = self.builder.build_eligibility_trace(
            run_id="run_missing",
            content_id="content_missing",
            qc_status="APPROVE",
            qc_publishable=True,
            qc_trace_ref=None,
            account_health_decision="SAFE",
            health_trace_ref="health_trace:missing",
            strategy_ref="strategy:missing",
            artifact_manifest_ref=None,
        )

        self.assertFalse(trace.eligible)
        self.assertIn("MISSING_QC_TRACE", trace.blocking_reasons)
        self.assertIn("MISSING_ARTIFACT_MANIFEST", trace.blocking_reasons)

    def test_missing_evidence_never_becomes_success(self) -> None:
        bundle = self._eligible_bundle()

        with self.assertRaises(PublishTraceValidationError):
            self.builder.build_result_trace(
                attempt_trace=bundle.publish_attempt_trace,
                result_status="succeeded",
                result_evidence_available=False,
            )

    def test_fake_url_or_platform_id_without_evidence_is_rejected(self) -> None:
        bundle = self._eligible_bundle()

        with self.assertRaises(PublishTraceValidationError):
            self.builder.build_result_trace(
                attempt_trace=bundle.publish_attempt_trace,
                result_status="pending",
                published_url="https://example.invalid/fake",
                platform_content_id="fake-platform-id",
                result_evidence_available=False,
            )

    def test_validation_rejects_forged_success_bundle(self) -> None:
        payload = self._eligible_bundle().to_dict()
        payload["publish_result_trace"]["result_status"] = "succeeded"
        payload["publish_result_trace"]["result_evidence_available"] = False
        payload["publish_lifecycle_event"]["result"] = dict(payload["publish_result_trace"])

        valid, failures = self.builder.validate_trace_bundle(payload)

        self.assertFalse(valid)
        self.assertIn("fabricated_publish_success", failures)

    def test_validation_rejects_forged_url_bundle(self) -> None:
        payload = self._eligible_bundle().to_dict()
        payload["publish_result_trace"]["published_url"] = "https://example.invalid/fake"
        payload["publish_lifecycle_event"]["result"] = dict(payload["publish_result_trace"])

        valid, failures = self.builder.validate_trace_bundle(payload)

        self.assertFalse(valid)
        self.assertIn("fake_url_or_platform_id", failures)

    def test_incident_hooks_for_missing_inputs_and_failed_attempt(self) -> None:
        eligibility = self.builder.build_eligibility_trace(
            run_id="run_incident",
            content_id="content_incident",
            qc_status="APPROVE",
            qc_publishable=True,
            qc_trace_ref=None,
            account_health_decision="SAFE",
            health_trace_ref="health_trace:incident",
            strategy_ref="strategy:incident",
            artifact_manifest_ref=None,
        )
        attempt = self.builder.build_attempt_trace(
            eligibility_trace=eligibility,
            attempt_id="attempt:incident",
        )
        result = self.builder.build_result_trace(attempt_trace=attempt)

        hooks = self.builder.build_incident_hooks(
            eligibility_trace=eligibility,
            attempt_trace=attempt,
            result_trace=result,
        )

        incident_types = {hook.incident_type for hook in hooks}
        self.assertIn("MISSING_QC_TRACE", incident_types)
        self.assertIn("MISSING_ARTIFACT_MANIFEST", incident_types)

    def test_failed_attempt_emits_incident_hook(self) -> None:
        eligibility = self.builder.build_eligibility_trace(
            run_id="run_fail",
            content_id="content_fail",
            qc_status="APPROVE",
            qc_publishable=True,
            qc_trace_ref="qc_trace:fail",
            account_health_decision="SAFE",
            health_trace_ref="health_trace:fail",
            strategy_ref="strategy:fail",
            artifact_manifest_ref="artifact_manifest:fail",
            dry_run=False,
        )
        attempt = self.builder.build_attempt_trace(
            eligibility_trace=eligibility,
            attempt_id="attempt:fail",
            dry_run=False,
            simulate_failure=True,
        )
        result = self.builder.build_result_trace(attempt_trace=attempt)
        hooks = self.builder.build_incident_hooks(
            eligibility_trace=eligibility,
            attempt_trace=attempt,
            result_trace=result,
        )

        self.assertEqual(result.result_status, "failed")
        self.assertIn("PUBLISH_ATTEMPT_FAILED", {hook.incident_type for hook in hooks})

    def test_skip_and_failure_reason_normalization(self) -> None:
        eligibility = self.builder.build_eligibility_trace(
            run_id="run_norm",
            content_id="content_norm",
            qc_status="APPROVE",
            qc_publishable=True,
            qc_trace_ref="qc_trace:norm",
            account_health_decision="SAFE",
            health_trace_ref="health_trace:norm",
            strategy_ref="strategy:norm",
            artifact_manifest_ref="artifact_manifest:norm",
            dry_run=False,
        )
        attempt = self.builder.build_attempt_trace(
            eligibility_trace=eligibility,
            attempt_id="attempt:norm",
            dry_run=False,
            simulate_failure=True,
            failure_reason="unexpected",
        )

        self.assertEqual(attempt.failure_reason, "UNKNOWN_INTERNAL_FAILURE")

    def test_lifecycle_writer_is_append_only(self) -> None:
        bundle = self._eligible_bundle()
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "publish_lifecycle.jsonl"
            target.write_text('{"sentinel": true}\n', encoding="utf-8")
            writer = PublishLifecycleWriter(target)
            writer.append_event(bundle.publish_lifecycle_event)

            lines = target.read_text(encoding="utf-8").splitlines()
            self.assertEqual(json.loads(lines[0]), {"sentinel": True})
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[1])["boundary_statement"], BOUNDARY_STATEMENT)

    def test_lifecycle_writer_creates_parent_directory(self) -> None:
        bundle = self._eligible_bundle()
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "nested" / "publish_lifecycle.jsonl"
            writer = PublishLifecycleWriter(target)
            writer.append_event(bundle.publish_lifecycle_event)

            self.assertTrue(target.exists())
            self.assertEqual(len(writer.read_events()), 1)

    def test_deterministic_same_input_same_trace(self) -> None:
        first = self._eligible_bundle().to_dict()
        second = self._eligible_bundle().to_dict()

        self.assertEqual(first, second)

    def test_boundary_preserved_and_no_performance_prediction_fields(self) -> None:
        payload = self._eligible_bundle().to_dict()
        serialized = json.dumps(payload, sort_keys=True)

        self.assertEqual(payload["boundary_statement"], BOUNDARY_STATEMENT)
        self.assertNotIn("expected_performance", serialized)
        self.assertNotIn("forecast", serialized)
        self.assertNotIn("predicted", serialized)


if __name__ == "__main__":
    unittest.main()
