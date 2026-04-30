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

from app.runtime.asset_selector import AssetSelector


class AssetEventRepresentationSelectorTests(unittest.TestCase):
    def test_event_evidence_beats_generic_same_entity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            payload = [
                {
                    "path": "assets/generic_doc.jpg",
                    "category": "document",
                    "subtype": "archive_page",
                    "family": "document",
                    "framing": "closeup",
                    "tags": ["document", "archive", "evidence"],
                    "mood": "clinical",
                    "semantic_pattern_fit": ["contradiction"],
                    "entity_fit": ["document"],
                    "hook_strength_score": 0.83,
                    "payoff_strength_score": 0.84,
                    "setup_specificity_score": 0.72,
                    "realism_score": 0.96,
                    "source_type": "unsplash",
                    "usage_count": 0,
                    "freshness_score": 1.0,
                    "resolution": [1080, 1920],
                    "strength": 0.84,
                    "genericity": 0.12,
                },
                {
                    "path": "assets/event_doc.jpg",
                    "category": "document",
                    "subtype": "casefile_redacted",
                    "family": "document",
                    "framing": "detail",
                    "tags": ["document", "archive", "evidence", "redacted", "anomaly", "date"],
                    "mood": "clinical",
                    "semantic_pattern_fit": ["contradiction", "missing"],
                    "entity_fit": ["document"],
                    "hook_strength_score": 0.84,
                    "payoff_strength_score": 0.9,
                    "setup_specificity_score": 0.78,
                    "realism_score": 0.94,
                    "source_type": "unsplash",
                    "usage_count": 0,
                    "freshness_score": 1.0,
                    "resolution": [1080, 1920],
                    "strength": 0.86,
                    "genericity": 0.08,
                },
            ]
            catalog.write_text(json.dumps(payload), encoding="utf-8")
            selector = AssetSelector(catalog_path=catalog)

            selected = selector.select(
                category="document",
                tags=[
                    "document",
                    "event_data_inconsistency",
                    "anomaly_temporal_contradiction",
                    "evidence_date",
                    "evidence_document_anomaly",
                ],
                seed="seed-1",
                query_text="archive page changed date after midnight",
                segment_role="payoff",
            )

            self.assertEqual(selected, "assets/event_doc.jpg")

    def test_setup_rejects_archive_context_without_visible_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            payload = [
                {
                    "path": "assets/generic_corridor.jpg",
                    "category": "corridor",
                    "subtype": "hallway",
                    "family": "corridor",
                    "framing": "wide",
                    "tags": ["corridor", "institutional"],
                    "mood": "neutral",
                    "semantic_pattern_fit": ["other"],
                    "entity_fit": ["corridor"],
                    "hook_strength_score": 0.7,
                    "payoff_strength_score": 0.7,
                    "setup_specificity_score": 0.7,
                    "realism_score": 0.95,
                    "source_type": "pexels",
                    "usage_count": 0,
                    "freshness_score": 1.0,
                    "resolution": [1080, 1920],
                    "strength": 0.82,
                    "genericity": 0.15,
                },
                {
                    "path": "assets/archive_room.jpg",
                    "category": "archive",
                    "subtype": "storage_rows",
                    "family": "archive",
                    "framing": "medium",
                    "tags": ["archive", "records", "files", "document"],
                    "mood": "clinical",
                    "semantic_pattern_fit": ["contradiction", "missing"],
                    "entity_fit": ["archive", "document"],
                    "hook_strength_score": 0.76,
                    "payoff_strength_score": 0.8,
                    "setup_specificity_score": 0.8,
                    "realism_score": 0.96,
                    "source_type": "pexels",
                    "usage_count": 0,
                    "freshness_score": 1.0,
                    "resolution": [1080, 1920],
                    "strength": 0.84,
                    "genericity": 0.08,
                },
            ]
            catalog.write_text(json.dumps(payload), encoding="utf-8")
            selector = AssetSelector(catalog_path=catalog)

            selected = selector.select(
                category="archive",
                tags=[
                    "archive",
                    "event_archive_context",
                    "context_archive",
                    "context_document",
                ],
                seed="seed-2",
                query_text="archive anomaly records changed after midnight",
                segment_role="setup",
            )

            self.assertIsNone(selected)

    def test_visual_world_cannot_rescue_documentary_context_without_visible_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            payload = [
                {
                    "path": "assets/corporate_people.jpg",
                    "category": "investigative_interior",
                    "subtype": "office_group",
                    "family": "investigative_ambient",
                    "framing": "medium",
                    "tags": ["people", "office", "group", "workspace", "corporate"],
                    "mood": "neutral",
                    "semantic_pattern_fit": ["other"],
                    "entity_fit": ["room"],
                    "hook_strength_score": 0.68,
                    "payoff_strength_score": 0.68,
                    "setup_specificity_score": 0.62,
                    "realism_score": 0.95,
                    "source_type": "unsplash",
                    "usage_count": 0,
                    "freshness_score": 1.0,
                    "resolution": [1080, 1920],
                    "strength": 0.8,
                    "genericity": 0.12,
                },
                {
                    "path": "assets/archive_storage.jpg",
                    "category": "archive",
                    "subtype": "records_storage",
                    "family": "archive",
                    "framing": "medium",
                    "tags": ["archive", "records", "files", "document", "institutional"],
                    "mood": "clinical",
                    "semantic_pattern_fit": ["contradiction"],
                    "entity_fit": ["document", "archive"],
                    "hook_strength_score": 0.76,
                    "payoff_strength_score": 0.8,
                    "setup_specificity_score": 0.81,
                    "realism_score": 0.96,
                    "source_type": "pexels",
                    "usage_count": 0,
                    "freshness_score": 1.0,
                    "resolution": [1080, 1920],
                    "strength": 0.85,
                    "genericity": 0.08,
                },
            ]
            catalog.write_text(json.dumps(payload), encoding="utf-8")
            selector = AssetSelector(catalog_path=catalog)

            selected = selector.select(
                category="archive",
                tags=[
                    "archive",
                    "context_archive",
                    "visual_family_documentary_caseworld",
                    "environment_type_archive_evidence_interior",
                    "lighting_style_low_key_documentary",
                    "dominant_emotion_curiosity",
                    "secondary_emotion_dread",
                    "mood_investigative",
                    "world_allow_archive",
                    "world_allow_document",
                    "world_forbid_corporate_people",
                ],
                seed="seed-world",
                query_text="archive page changed after midnight investigative records room",
                segment_role="setup",
            )

            self.assertIsNone(selected)

    def test_setup_rejects_legacy_corridor_without_event_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            payload = [
                {
                    "path": "assets/legacy_walkway.jpg",
                    "category": "institutional_space",
                    "subtype": "public_walkway",
                    "family": "investigative_ambient",
                    "framing": "wide",
                    "tags": ["institutional", "walkway", "public_space"],
                    "mood": "tense",
                    "semantic_pattern_fit": ["other"],
                    "entity_fit": ["corridor"],
                    "hook_strength_score": 0.7,
                    "payoff_strength_score": 0.7,
                    "setup_specificity_score": 0.7,
                    "realism_score": 0.95,
                    "source_type": "local_curated",
                    "usage_count": 0,
                    "freshness_score": 0.9,
                    "resolution": [1080, 1920],
                    "strength": 0.8,
                    "genericity": 0.12,
                },
                {
                    "path": "assets/station_notice.jpg",
                    "category": "institutional_space",
                    "subtype": "station_notice",
                    "family": "investigative_ambient",
                    "framing": "wide",
                    "tags": ["institutional", "station", "platform", "notice", "corridor", "warning"],
                    "mood": "tense",
                    "semantic_pattern_fit": ["warning"],
                    "entity_fit": ["corridor", "device"],
                    "hook_strength_score": 0.76,
                    "payoff_strength_score": 0.76,
                    "setup_specificity_score": 0.82,
                    "realism_score": 0.95,
                    "source_type": "pexels",
                    "usage_count": 0,
                    "freshness_score": 0.9,
                    "resolution": [1080, 1920],
                    "strength": 0.84,
                    "genericity": 0.08,
                },
            ]
            catalog.write_text(json.dumps(payload), encoding="utf-8")
            selector = AssetSelector(catalog_path=catalog)

            selected = selector.select(
                category="institutional_space",
                tags=[
                    "context",
                    "event_active_warning_state",
                    "evidence_warning",
                    "evidence_intercom",
                    "style_device_tense",
                ],
                seed="seed-legacy",
                query_text="station intercom warning empty platform hall",
                segment_role="setup",
            )

            self.assertEqual(selected, "assets/station_notice.jpg")

    def test_setup_allows_legacy_family_if_it_carries_event_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            payload = [
                {
                    "path": "assets/platform_warning.jpg",
                    "category": "corridor",
                    "subtype": "institutional_platform",
                    "family": "corridor",
                    "framing": "medium",
                    "tags": ["corridor", "platform", "warning", "institutional"],
                    "mood": "tense",
                    "semantic_pattern_fit": ["warning"],
                    "entity_fit": ["corridor"],
                    "hook_strength_score": 0.78,
                    "payoff_strength_score": 0.78,
                    "setup_specificity_score": 0.79,
                    "realism_score": 0.94,
                    "source_type": "pexels",
                    "usage_count": 0,
                    "freshness_score": 0.9,
                    "resolution": [1080, 1920],
                    "strength": 0.82,
                    "genericity": 0.1,
                }
            ]
            catalog.write_text(json.dumps(payload), encoding="utf-8")
            selector = AssetSelector(catalog_path=catalog)

            selected = selector.select(
                category="corridor",
                tags=[
                    "context",
                    "event_active_warning_state",
                    "evidence_warning",
                    "style_institutional_cold",
                ],
                seed="seed-legacy-allow",
                query_text="platform warning corridor",
                segment_role="setup",
            )

            self.assertEqual(selected, "assets/platform_warning.jpg")

    def test_documentary_setup_prefers_case_linked_evidence_over_archive_ambience(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            payload = [
                {
                    "path": "assets/archive_storage.jpg",
                    "category": "archive",
                    "subtype": "storage_rows",
                    "family": "archive",
                    "framing": "medium",
                    "tags": ["archive", "storage", "records", "files"],
                    "mood": "clinical",
                    "semantic_pattern_fit": ["contradiction"],
                    "entity_fit": ["archive", "document"],
                    "hook_strength_score": 0.74,
                    "payoff_strength_score": 0.76,
                    "setup_specificity_score": 0.8,
                    "realism_score": 0.96,
                    "source_type": "local_curated",
                    "usage_count": 0,
                    "freshness_score": 0.8,
                    "resolution": [1080, 1920],
                    "strength": 0.82,
                    "genericity": 0.08,
                },
                {
                    "path": "assets/casefile_surface.jpg",
                    "category": "evidence_surface",
                    "subtype": "casefile_anomaly",
                    "family": "documentary_evidence",
                    "framing": "detail",
                    "tags": ["evidence", "surface", "document", "anomaly", "case_file", "page"],
                    "mood": "tense",
                    "semantic_pattern_fit": ["contradiction", "missing"],
                    "entity_fit": ["document"],
                    "hook_strength_score": 0.8,
                    "payoff_strength_score": 0.84,
                    "setup_specificity_score": 0.82,
                    "realism_score": 0.95,
                    "source_type": "unsplash",
                    "usage_count": 0,
                    "freshness_score": 0.8,
                    "resolution": [1080, 1920],
                    "strength": 0.85,
                    "genericity": 0.05,
                },
            ]
            catalog.write_text(json.dumps(payload), encoding="utf-8")
            selector = AssetSelector(catalog_path=catalog)

            selected = selector.select(
                category="archive",
                tags=[
                    "context",
                    "event_data_inconsistency",
                    "evidence_document_anomaly",
                    "style_archive_case",
                    "visual_family_documentary_caseworld",
                ],
                seed="seed-doc-break",
                query_text="archive page changed date casefile anomaly",
                segment_role="setup",
            )

            self.assertEqual(selected, "assets/casefile_surface.jpg")

    def test_documentary_setup_rejects_generic_archive_ambience_without_case_linkage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            payload = [
                {
                    "path": "assets/archive_shelves.jpg",
                    "category": "archive",
                    "subtype": "shelves",
                    "family": "documentary_context",
                    "framing": "wide",
                    "tags": ["archive", "shelves", "records"],
                    "mood": "tense",
                    "semantic_pattern_fit": ["other"],
                    "entity_fit": ["archive"],
                    "hook_strength_score": 0.7,
                    "payoff_strength_score": 0.7,
                    "setup_specificity_score": 0.76,
                    "realism_score": 0.95,
                    "source_type": "local_curated",
                    "usage_count": 0,
                    "freshness_score": 0.8,
                    "resolution": [1080, 1920],
                    "strength": 0.8,
                    "genericity": 0.08,
                }
            ]
            catalog.write_text(json.dumps(payload), encoding="utf-8")
            selector = AssetSelector(catalog_path=catalog)

            selected = selector.select(
                category="archive",
                tags=[
                    "context",
                    "event_document_anomaly",
                    "evidence_document_anomaly",
                    "style_archive_case",
                    "visual_family_documentary_caseworld",
                ],
                seed="seed-doc-reject",
                query_text="missing witness transcript altered page",
                segment_role="setup",
            )

            self.assertIsNone(selected)

    def test_setup_rejects_context_only_asset_without_visible_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            payload = [
                {
                    "path": "assets/empty_corridor.jpg",
                    "category": "corridor",
                    "subtype": "hallway",
                    "family": "corridor",
                    "framing": "wide",
                    "tags": ["corridor", "institutional"],
                    "mood": "neutral",
                    "semantic_pattern_fit": ["other"],
                    "entity_fit": ["corridor"],
                    "hook_strength_score": 0.72,
                    "payoff_strength_score": 0.72,
                    "setup_specificity_score": 0.78,
                    "realism_score": 0.96,
                    "source_type": "pexels",
                    "usage_count": 0,
                    "freshness_score": 1.0,
                    "resolution": [1080, 1920],
                    "strength": 0.84,
                    "genericity": 0.1,
                }
            ]
            catalog.write_text(json.dumps(payload), encoding="utf-8")
            selector = AssetSelector(catalog_path=catalog)

            selected = selector.select(
                category="corridor",
                tags=[
                    "event_unauthorized_presence",
                    "evidence_presence",
                    "anomaly_presence_signal",
                ],
                seed="seed-context-reject",
                query_text="someone whispered behind the sealed corridor door",
                segment_role="setup",
            )

            self.assertIsNone(selected)

    def test_setup_rejects_phase1_legacy_even_if_category_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            payload = [
                {
                    "path": "assets/legacy_archive.jpg",
                    "category": "archive",
                    "subtype": "storage_rows",
                    "family": "archive",
                    "framing": "medium",
                    "tags": ["archive", "records", "files", "document", "anomaly"],
                    "mood": "clinical",
                    "semantic_pattern_fit": ["contradiction"],
                    "entity_fit": ["archive", "document"],
                    "hook_strength_score": 0.74,
                    "payoff_strength_score": 0.78,
                    "setup_specificity_score": 0.82,
                    "realism_score": 0.95,
                    "source_type": "local_curated",
                    "usage_count": 0,
                    "freshness_score": 0.75,
                    "resolution": [1080, 1920],
                    "strength": 0.83,
                    "genericity": 0.08,
                    "phase1_legacy": True,
                },
                {
                    "path": "assets/new_casefile.jpg",
                    "category": "document",
                    "subtype": "casefile_anomaly",
                    "family": "documentary_evidence",
                    "framing": "detail",
                    "tags": ["document", "case_file", "evidence", "anomaly", "changed"],
                    "mood": "tense",
                    "semantic_pattern_fit": ["contradiction"],
                    "entity_fit": ["document"],
                    "hook_strength_score": 0.78,
                    "payoff_strength_score": 0.88,
                    "setup_specificity_score": 0.8,
                    "realism_score": 0.96,
                    "source_type": "unsplash",
                    "usage_count": 0,
                    "freshness_score": 1.0,
                    "resolution": [1080, 1920],
                    "strength": 0.88,
                    "genericity": 0.05,
                },
            ]
            catalog.write_text(json.dumps(payload), encoding="utf-8")
            selector = AssetSelector(catalog_path=catalog)

            selected = selector.select(
                category="archive",
                tags=[
                    "event_document_anomaly",
                    "evidence_document_anomaly",
                    "visual_family_documentary_caseworld",
                    "world_family_documentary_evidence",
                ],
                seed="seed-legacy-doc",
                query_text="archive casefile page changed overnight",
                segment_role="setup",
            )

            self.assertEqual(selected, "assets/new_casefile.jpg")

    def test_payoff_rejects_document_without_visible_anomaly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            payload = [
                {
                    "path": "assets/plain_document.jpg",
                    "category": "document",
                    "subtype": "typed_page",
                    "family": "document",
                    "framing": "detail",
                    "tags": ["document", "page", "record"],
                    "mood": "clinical",
                    "semantic_pattern_fit": ["contradiction"],
                    "entity_fit": ["document"],
                    "hook_strength_score": 0.72,
                    "payoff_strength_score": 0.82,
                    "setup_specificity_score": 0.68,
                    "realism_score": 0.96,
                    "source_type": "unsplash",
                    "usage_count": 0,
                    "freshness_score": 1.0,
                    "resolution": [1080, 1920],
                    "strength": 0.82,
                    "genericity": 0.08,
                }
            ]
            catalog.write_text(json.dumps(payload), encoding="utf-8")
            selector = AssetSelector(catalog_path=catalog)

            selected = selector.select(
                category="document",
                tags=[
                    "event_data_inconsistency",
                    "evidence_document_anomaly",
                    "evidence_timestamp",
                ],
                seed="seed-payoff-reject",
                query_text="the casefile timestamp changed to next year",
                segment_role="payoff",
            )

            self.assertIsNone(selected)


if __name__ == "__main__":
    unittest.main()
