from __future__ import annotations

import unittest

from src.core.policy.default_policy_by_stage import ACCOUNT_POLICY_STAGES
from src.core.policy.resolver import compose_policy, resolve_policy


class AccountPolicyResolutionTests(unittest.TestCase):
    def test_insufficient_data_returns_growth(self) -> None:
        stage = resolve_policy(
            {
                "videos_last_10_count": 0,
                "avg_3s_retention_last_10": 0.10,
                "followers": 999999,
                "avg_rpm_last_10": 99.0,
            },
            target_rpm=0.8,
        )
        self.assertEqual(stage, "GROWTH")

    def test_low_retention_returns_recovery_when_enough_videos(self) -> None:
        stage = resolve_policy(
            {
                "videos_last_10_count": 10,
                "avg_3s_retention_last_10": 0.34,
                "followers": 20000,
                "avg_rpm_last_10": 1.5,
            },
            target_rpm=0.8,
        )
        self.assertEqual(stage, "RECOVERY")

    def test_high_followers_and_high_rpm_returns_monetization(self) -> None:
        stage = resolve_policy(
            {
                "videos_last_10_count": 10,
                "avg_3s_retention_last_10": 0.50,
                "followers": 15000,
                "avg_rpm_last_10": 1.2,
            },
            target_rpm=0.8,
        )
        self.assertEqual(stage, "MONETIZATION")

    def test_high_followers_and_low_rpm_returns_growth(self) -> None:
        stage = resolve_policy(
            {
                "videos_last_10_count": 10,
                "avg_3s_retention_last_10": 0.50,
                "followers": 15000,
                "avg_rpm_last_10": 0.6,
            },
            target_rpm=0.8,
        )
        self.assertEqual(stage, "GROWTH")

    def test_default_path_returns_growth(self) -> None:
        stage = resolve_policy(
            {
                "videos_last_10_count": 10,
                "avg_3s_retention_last_10": 0.60,
                "followers": 9000,
                "avg_rpm_last_10": 2.0,
            },
            target_rpm=0.8,
        )
        self.assertEqual(stage, "GROWTH")

    def test_compose_policy_returns_full_document_and_closed_enum(self) -> None:
        policy = compose_policy(
            "acc_ca_001",
            {
                "videos_last_10_count": 10,
                "avg_3s_retention_last_10": 0.50,
                "followers": 15000,
                "avg_rpm_last_10": 1.2,
            },
            target_rpm=0.8,
            updated_at="2026-03-04T18:00:00Z",
        )

        self.assertIn(policy["stage"], ACCOUNT_POLICY_STAGES)
        self.assertIsInstance(policy["targets"], dict)
        self.assertIsInstance(policy["constraints"], dict)
        self.assertEqual(policy["metrics_window"]["videos_considered"], 10)
        self.assertEqual(policy["metrics_window"]["updated_at"], "2026-03-04T18:00:00Z")


if __name__ == "__main__":
    unittest.main()
