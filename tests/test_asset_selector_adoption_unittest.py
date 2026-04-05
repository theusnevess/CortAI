from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.runtime.asset_selector import AssetSelector


class AssetSelectorAdoptionTests(unittest.TestCase):
    def test_new_real_asset_can_beat_legacy_when_semantically_equivalent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog_path = Path(tmp_dir) / "catalog.json"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "path": "assets/curated/corridor/legacy.jpg",
                            "source_type": "local_curated",
                            "category": "corridor",
                            "subtype": "dark_passage",
                            "tags": ["corridor", "sealed", "door"],
                            "semantic_pattern_fit": ["sealed"],
                            "entity_fit": ["corridor"],
                            "hook_strength_score": 0.82,
                            "payoff_strength_score": 0.82,
                            "setup_specificity_score": 0.55,
                            "realism_score": 0.84,
                            "usage_count": 5,
                            "freshness_score": 0.5,
                            "framing": "medium",
                            "family": "corridor",
                            "mood": "ominous",
                            "resolution": [1080, 1920],
                            "strength": 0.82,
                            "genericity": 0.18,
                            "phase1_legacy": True,
                        },
                        {
                            "path": "assets/imports/unsplash/corridor/new_hospital_corridor.jpg",
                            "source_type": "unsplash",
                            "category": "corridor",
                            "subtype": "hospital",
                            "tags": ["hospital", "corridor", "night", "sealed", "warning", "door"],
                            "semantic_pattern_fit": [],
                            "entity_fit": [],
                            "hook_strength_score": 0.78,
                            "payoff_strength_score": 0.8,
                            "setup_specificity_score": 0.75,
                            "realism_score": 0.96,
                            "usage_count": 0,
                            "freshness_score": 1.0,
                            "framing": "medium",
                            "family": "corridor",
                            "mood": "neutral",
                            "resolution": [1080, 1920],
                            "strength": 0.88,
                            "genericity": 0.12,
                        },
                    ],
                    indent=2,
                ),
                encoding="utf-8",
            )
            selector = AssetSelector(catalog_path=catalog_path)
            selected = selector.select(
                category="corridor",
                tags=["hospital", "corridor", "sealed", "event_sealed_containment", "evidence_sealed"],
                seed="seed-1",
                query_text="sealed hospital corridor warning at night",
                minimum_score=0.0,
                segment_role="setup",
            )

        self.assertEqual(selected, "assets/imports/unsplash/corridor/new_hospital_corridor.jpg")

    def test_local_curated_is_ineligible_for_all_segment_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog_path = Path(tmp_dir) / "catalog.json"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "path": "assets/curated/warning_display/legacy_warning.jpg",
                            "source_type": "local_curated",
                            "category": "warning_display",
                            "subtype": "panel",
                            "tags": ["warning", "signal", "panel"],
                            "semantic_pattern_fit": ["warning"],
                            "entity_fit": ["device"],
                            "hook_strength_score": 0.9,
                            "payoff_strength_score": 0.9,
                            "setup_specificity_score": 0.8,
                            "realism_score": 0.9,
                            "usage_count": 0,
                            "freshness_score": 0.9,
                            "framing": "closeup",
                            "family": "warning_display",
                            "mood": "tense",
                            "resolution": [1080, 1920],
                            "strength": 0.9,
                            "genericity": 0.05,
                        },
                        {
                            "path": "assets/imports/pexels/warning_display/panel.jpg",
                            "source_type": "pexels",
                            "category": "warning_display",
                            "subtype": "panel",
                            "tags": ["warning", "signal", "panel"],
                            "semantic_pattern_fit": ["warning"],
                            "entity_fit": ["device"],
                            "hook_strength_score": 0.85,
                            "payoff_strength_score": 0.85,
                            "setup_specificity_score": 0.78,
                            "realism_score": 0.95,
                            "usage_count": 0,
                            "freshness_score": 1.0,
                            "framing": "closeup",
                            "family": "warning_display",
                            "mood": "tense",
                            "resolution": [1080, 1920],
                            "strength": 0.88,
                            "genericity": 0.08,
                        },
                    ],
                    indent=2,
                ),
                encoding="utf-8",
            )
            selector = AssetSelector(catalog_path=catalog_path)

            for role in ("hook", "setup", "payoff"):
                selected = selector.select(
                    category="warning_display",
                    tags=["warning", "signal", "event_active_warning_state"],
                    seed=f"seed-{role}",
                    query_text="station warning panel activated",
                    minimum_score=0.0,
                    segment_role=role,
                )
                self.assertEqual(selected, "assets/imports/pexels/warning_display/panel.jpg")

    def test_case_pack_proxy_is_hard_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog_path = Path(tmp_dir) / "catalog.json"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "path": "assets/imports/unsplash/warning_display/car_dashboard_warning.jpg",
                            "source_type": "unsplash",
                            "category": "warning_display",
                            "subtype": "car_dashboard",
                            "tags": ["warning", "signal", "dashboard"],
                            "semantic_pattern_fit": ["warning"],
                            "entity_fit": ["signal"],
                            "hook_strength_score": 0.9,
                            "payoff_strength_score": 0.9,
                            "setup_specificity_score": 0.85,
                            "realism_score": 0.95,
                            "usage_count": 0,
                            "freshness_score": 1.0,
                            "framing": "closeup",
                            "family": "dashboard_signal",
                            "mood": "tense",
                            "resolution": [1080, 1920],
                            "strength": 0.9,
                            "genericity": 0.05,
                        },
                        {
                            "path": "assets/imports/pexels/intercom_recorder/station_intercom_panel.jpg",
                            "source_type": "pexels",
                            "category": "intercom_recorder",
                            "subtype": "wall_speaker_panel",
                            "tags": ["intercom", "warning", "panel", "active", "signal"],
                            "semantic_pattern_fit": ["warning"],
                            "entity_fit": ["intercom", "signal"],
                            "hook_strength_score": 0.85,
                            "payoff_strength_score": 0.88,
                            "setup_specificity_score": 0.82,
                            "realism_score": 0.96,
                            "usage_count": 0,
                            "freshness_score": 1.0,
                            "framing": "closeup",
                            "family": "warning_display",
                            "mood": "tense",
                            "resolution": [1080, 1920],
                            "strength": 0.9,
                            "genericity": 0.08,
                        },
                    ],
                    indent=2,
                ),
                encoding="utf-8",
            )
            selector = AssetSelector(catalog_path=catalog_path)
            selected = selector.select(
                category="warning_display",
                tags=[
                    "event_active_warning_state",
                    "case_family_institutional_alert_system",
                    "case_object_intercom",
                    "case_evidence_active_signal",
                    "case_environment_station_corridor",
                    "case_forbid_car_dashboard",
                    "case_motif_forbid_generic_clock",
                    "case_state_warning_state",
                    "case_step_signal",
                ],
                seed="seed-case-proxy",
                query_text="station intercom warning panel active signal",
                minimum_score=0.0,
                segment_role="setup",
            )
            self.assertEqual(
                selected,
                "assets/imports/pexels/intercom_recorder/station_intercom_panel.jpg",
            )


if __name__ == "__main__":
    unittest.main()
