from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.policy.default_policy_by_stage import ACCOUNT_POLICY_STAGES
from src.core.policy.resolver import compose_policy, resolve_policy


def test_insufficient_data_returns_growth() -> None:
    stage = resolve_policy(
        {
            "videos_last_10_count": 0,
            "avg_3s_retention_last_10": 0.10,
            "followers": 999999,
            "avg_rpm_last_10": 99.0,
        },
        target_rpm=0.8,
    )
    assert stage == "GROWTH"


def test_low_retention_returns_recovery_when_enough_videos() -> None:
    stage = resolve_policy(
        {
            "videos_last_10_count": 10,
            "avg_3s_retention_last_10": 0.34,
            "followers": 20000,
            "avg_rpm_last_10": 1.5,
        },
        target_rpm=0.8,
    )
    assert stage == "RECOVERY"


def test_high_followers_and_high_rpm_returns_monetization() -> None:
    stage = resolve_policy(
        {
            "videos_last_10_count": 10,
            "avg_3s_retention_last_10": 0.50,
            "followers": 15000,
            "avg_rpm_last_10": 1.2,
        },
        target_rpm=0.8,
    )
    assert stage == "MONETIZATION"


def test_high_followers_and_low_rpm_returns_growth() -> None:
    stage = resolve_policy(
        {
            "videos_last_10_count": 10,
            "avg_3s_retention_last_10": 0.50,
            "followers": 15000,
            "avg_rpm_last_10": 0.6,
        },
        target_rpm=0.8,
    )
    assert stage == "GROWTH"


def test_default_path_returns_growth() -> None:
    stage = resolve_policy(
        {
            "videos_last_10_count": 10,
            "avg_3s_retention_last_10": 0.60,
            "followers": 9000,
            "avg_rpm_last_10": 2.0,
        },
        target_rpm=0.8,
    )
    assert stage == "GROWTH"


def test_compose_policy_returns_full_document_and_closed_enum() -> None:
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

    assert policy["stage"] in ACCOUNT_POLICY_STAGES
    assert isinstance(policy["targets"], dict)
    assert isinstance(policy["constraints"], dict)
    assert policy["metrics_window"]["videos_considered"] == 10
    assert policy["metrics_window"]["updated_at"] == "2026-03-04T18:00:00Z"
