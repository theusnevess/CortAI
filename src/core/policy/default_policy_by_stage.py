from __future__ import annotations

DEFAULT_POLICY_BY_STAGE_V1 = {
    "GROWTH": {
        "targets": {
            "target_duration_s": [25, 35],
            "target_follow_rate": 0.03,
            "target_3s_retention": 0.45,
            "target_completion": 0.35,
        },
        "constraints": {
            "series_mode": "prefer",
            "forbid_complex_openings": True,
        },
    },
    "MONETIZATION": {
        "targets": {
            "target_duration_s": [60, 75],
            "target_follow_rate": 0.02,
            "target_3s_retention": 0.40,
            "target_completion": 0.45,
        },
        "constraints": {
            "series_mode": "optional",
            "forbid_complex_openings": False,
        },
    },
    "RECOVERY": {
        "targets": {
            "target_duration_s": [25, 45],
            "target_follow_rate": 0.025,
            "target_3s_retention": 0.45,
            "target_completion": 0.35,
        },
        "constraints": {
            "series_mode": "prefer",
            "forbid_complex_openings": True,
        },
    },
}

ACCOUNT_POLICY_STAGES = ("GROWTH", "MONETIZATION", "RECOVERY")
