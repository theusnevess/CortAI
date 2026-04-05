from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.runtime.asset_selector import AssetSelector


class AssetSelectorSignaturePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures = {}
        AssetSelector._global_failed_sequences_prevented = {}
        self.selector = AssetSelector()
        self.batch_key = "global_solution_batch"

    def test_family_repeat_relaxes_after_diversity_is_proven(self) -> None:
        prior = [
            {
                "hook_family": "documentary_evidence",
                "setup_family": "sealed_access",
                "payoff_family": "documentary_evidence",
                "progression_type": "document_evidence>barrier_signal>document_evidence",
                "evidence_pattern": "h:document,mark|s:seal,breach|p:document,proof,timestamp",
                "dominant_family": "documentary_evidence",
            },
            {
                "hook_family": "warning_display",
                "setup_family": "intercom_recorder",
                "payoff_family": "warning_display",
                "progression_type": "device_signal>device_signal>device_signal",
                "evidence_pattern": "h:signal,warning|s:source,warning|p:signal,proof,warning",
                "dominant_family": "warning_display",
            },
            {
                "hook_family": "sealed_access",
                "setup_family": "horror_ambient",
                "payoff_family": "sealed_access",
                "progression_type": "barrier_signal>room_context>barrier_signal",
                "evidence_pattern": "h:seal,restriction|s:presence,tension|p:breach,proof,seal",
                "dominant_family": "sealed_access",
            },
            {
                "hook_family": "monitor_screen",
                "setup_family": "barrier_signal",
                "payoff_family": "monitor_screen",
                "progression_type": "device_signal>barrier_signal>device_signal",
                "evidence_pattern": "h:monitor,signal|s:breach,panel|p:distortion,proof,signal",
                "dominant_family": "monitor_screen",
            },
            {
                "hook_family": "documentary_evidence",
                "setup_family": "intercom_recorder",
                "payoff_family": "warning_display",
                "progression_type": "document_evidence>device_signal>device_signal",
                "evidence_pattern": "h:file,mark|s:source,warning|p:panel,proof,warning",
                "dominant_family": "mixed",
            },
            {
                "hook_family": "warning_display",
                "setup_family": "sealed_access",
                "payoff_family": "documentary_evidence",
                "progression_type": "device_signal>barrier_signal>document_evidence",
                "evidence_pattern": "h:warning|s:breach,seal|p:document,proof,timestamp",
                "dominant_family": "mixed",
            },
            {
                "hook_family": "intercom_recorder",
                "setup_family": "sealed_access",
                "payoff_family": "warning_display",
                "progression_type": "device_signal>barrier_signal>device_signal_alt",
                "evidence_pattern": "h:audio,warning|s:breach,security|p:alert,proof,signal",
                "dominant_family": "mixed",
            },
            {
                "hook_family": "documentary_evidence",
                "setup_family": "investigative_ambient",
                "payoff_family": "horror_ambient",
                "progression_type": "document_evidence>room_context>room_context",
                "evidence_pattern": "h:file,route|s:room,tension|p:breach,room,seal",
                "dominant_family": "mixed",
            },
        ]
        AssetSelector._global_video_signatures[self.batch_key] = prior

        candidate = {
            "hook_family": "documentary_evidence",
            "setup_family": "intercom_recorder",
            "payoff_family": "documentary_evidence",
            "progression_type": "document_evidence>device_signal>document_evidence_alt",
            "evidence_pattern": "h:file,mark|s:audio,newstate,warning|p:document,proof,timestamp,violation",
            "dominant_family": "documentary_evidence",
        }

        violation = self.selector._signature_policy_violation(signature=candidate, batch_key=self.batch_key)
        self.assertIsNone(violation)

    def test_family_repeat_stays_blocked_when_phase1_like(self) -> None:
        AssetSelector._global_video_signatures[self.batch_key] = [
            {
                "hook_family": "documentary_evidence",
                "setup_family": "sealed_access",
                "payoff_family": "documentary_evidence",
                "progression_type": "document_evidence>barrier_signal>document_evidence",
                "evidence_pattern": "h:document,mark|s:seal,breach|p:document,proof,timestamp",
                "dominant_family": "documentary_evidence",
            }
        ] * 8

        candidate = {
            "hook_family": "documentary_evidence",
            "setup_family": "barrier_signal",
            "payoff_family": "documentary_evidence",
            "progression_type": "document_evidence>barrier_signal>document_evidence",
            "evidence_pattern": "h:document,mark|s:seal,breach|p:document,proof,timestamp",
            "dominant_family": "documentary_evidence",
        }

        violation = self.selector._signature_policy_violation(signature=candidate, batch_key=self.batch_key)
        self.assertIn(
            violation,
            {
                "ASSET_RUNTIME_REPEATED_SIGNATURE",
                "ASSET_RUNTIME_REPEATED_PROGRESSION_PATTERN",
                "ASSET_RUNTIME_FAMILY_MONOCULTURE_FAILURE",
            },
        )

    def test_progression_repeat_relaxes_when_evidence_pattern_differs(self) -> None:
        AssetSelector._global_video_signatures[self.batch_key] = [
            {
                "hook_family": "investigative_ambient",
                "setup_family": "documentary_evidence",
                "payoff_family": "warning_display",
                "progression_type": "room_context>document_evidence>device_signal",
                "evidence_pattern": "h:active,anomaly,evidence,sealed|s:anomaly,evidence,missing,route,sealed|p:active,anomaly,evidence,sealed,signal,warning",
                "dominant_family": "mixed",
            }
        ]

        candidate = {
            "hook_family": "archive",
            "setup_family": "documentary_evidence",
            "payoff_family": "warning_display",
            "progression_type": "room_context>document_evidence>device_signal",
            "evidence_pattern": "h:document,mark,stamp|s:anomaly,casefile,newstate|p:active,proof,signal,warning",
            "dominant_family": "mixed",
        }

        violation = self.selector._signature_policy_violation(signature=candidate, batch_key=self.batch_key)
        self.assertIsNone(violation)

    def test_progression_repeat_stays_blocked_when_evidence_pattern_matches(self) -> None:
        AssetSelector._global_video_signatures[self.batch_key] = [
            {
                "hook_family": "warning_display",
                "setup_family": "barrier_signal",
                "payoff_family": "archive",
                "progression_type": "device_signal>barrier_signal>archive_context",
                "evidence_pattern": "h:active,anomaly,evidence,sealed,signal,warning|s:anomaly,breach,evidence,presence,sealed,security,signal,warning|p:active,anomaly,evidence,sealed,timestamp",
                "dominant_family": "mixed",
            }
        ]

        candidate = {
            "hook_family": "warning_display",
            "setup_family": "barrier_signal",
            "payoff_family": "archive",
            "progression_type": "device_signal>barrier_signal>archive_context",
            "evidence_pattern": "h:active,anomaly,evidence,sealed,signal,warning|s:anomaly,breach,evidence,presence,sealed,security,signal,warning|p:active,anomaly,evidence,sealed,timestamp",
            "dominant_family": "mixed",
        }

        violation = self.selector._signature_policy_violation(signature=candidate, batch_key=self.batch_key)
        self.assertIn(
            violation,
            {
                "ASSET_RUNTIME_REPEATED_SIGNATURE",
                "ASSET_RUNTIME_REPEATED_PROGRESSION_PATTERN",
            },
        )


if __name__ == "__main__":
    unittest.main()
