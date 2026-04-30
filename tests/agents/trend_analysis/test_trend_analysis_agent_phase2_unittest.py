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

from app.creative.agents.trend_analysis.collectors import TikTokCreativeCenterCollector
from app.creative.agents.trend_analysis.models import TrendAnalysisInput, TrendCollectorResult, TrendSourceRecord
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.contracts.creative_pack import TrendEvidenceReference


class TrendAnalysisAgentPhase2Tests(unittest.TestCase):
    def test_creative_center_collector_parses_public_trend_discovery_html(self) -> None:
        html_text = """
        <html><body>
        <div>Hashtags</div><div>Songs</div><div>Creators</div>
        <div>Trend Discovery</div>
        <div>Hashtags</div><div>Songs</div><div>Creators</div><div>TikTok Videos</div>
        <div>1</div><div>6</div><div>#</div><div>aprilfools</div><div>52K</div><div>Posts</div><div>See analytics</div>
        <div>2</div><div>10</div><div>#</div><div>april</div><div>21K</div><div>Posts</div><div>See analytics</div>
        <div>3</div><div>40</div><div>#</div><div>aprilfoolsday</div><div>9K</div><div>Posts</div><div>See analytics</div>
        <div>4</div><div>#</div><div>nasa</div><div>Education</div><div>10K</div><div>Posts</div><div>See analytics</div>
        <div>5</div><div>#</div><div>firstofthemonth</div><div>6K</div><div>Posts</div><div>See analytics</div>
        <div>1</div><div>Classic classical gymnopedie solo piano(1034554)</div><div>Lyrebirds music</div><div>Approved for business use</div><div>See analytics</div>
        <div>2</div><div>2</div><div>Gucci</div><div>MAF Teeski</div><div>See analytics</div>
        <div>3</div><div>Snowfall (Slowed)</div><div>dunsky &amp; 777Muzic</div><div>Approved for business use</div><div>See analytics</div>
        <div>4</div><div>2</div><div>silence</div><div>moartea regelui.</div><div>See analytics</div>
        <div>5</div><div>A Dream</div><div>Flatsound</div><div>See analytics</div>
        </body></html>
        """

        class _FakeResponse:
            status_code = 200
            text = html_text

        class _FakeClient:
            def get(self, url):  # noqa: ANN001
                _ = url
                return _FakeResponse()

            def close(self) -> None:
                return None

        collector = TikTokCreativeCenterCollector(http_client_factory=lambda **_: _FakeClient())
        result = collector.collect(TrendAnalysisInput(niche="horror", region="US", force_refresh=True))

        self.assertFalse(result.used_stub)
        self.assertIsNotNone(result.source_record)
        self.assertEqual(result.trace["status"], "COLLECTED")
        self.assertEqual(result.trace["hashtags_count"], 5)
        self.assertEqual(result.trace["songs_count"], 5)
        self.assertEqual(result.source_record.source, "creative_center")
        self.assertEqual(result.source_record.source_metadata["hashtags"][0], "aprilfools")
        self.assertEqual(result.source_record.source_metadata["songs"][0]["title"], "Classic classical gymnopedie solo piano(1034554)")
        self.assertEqual(result.source_record.evidence[0].evidence_type, "creative_center_hashtag")

    def test_repo_seed_manual_curation_files_are_canonical_and_approved(self) -> None:
        service = TrendAnalysisAgentService()
        expected = {
            "horror": ("manual_curation", "APPROVE"),
            "true_crime": ("manual_curation", "APPROVE"),
            "facts": ("manual_curation", "APPROVE"),
            "history": ("manual_curation", "APPROVE"),
            "conspiracy": ("manual_curation", "APPROVE"),
        }

        for niche, (source, status) in expected.items():
            with self.subTest(niche=niche):
                result = service.load(TrendAnalysisInput(niche=niche, current_time="2026-04-03T12:00:00Z"))
                self.assertFalse(result.fallback.used)
                self.assertEqual(result.trend_profile.niche, niche)
                self.assertEqual(result.trend_profile.trend_source, source)
                self.assertEqual(result.validation_summary["status"], status)
                self.assertGreaterEqual(result.trend_profile.sample_size, 6)
                self.assertGreaterEqual(len(result.trend_profile.evidence), 2)
                self.assertEqual(result.collector_trace["assembly_mode"], "source_assembly")

    def test_loads_manual_curated_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            (trends_dir / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "dominant_hooks": ["question", "shock_statement"],
                        "avg_duration": "35-60",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror"))

            self.assertFalse(result.fallback.used)
            self.assertEqual(result.trend_profile.niche, "horror")
            self.assertEqual(result.trend_profile.pacing, "fast_first_3s")
            self.assertEqual(result.trend_profile.visual_style, "dark_backgrounds")
            self.assertEqual(result.trend_profile.trend_source, "manual_file_legacy")
            self.assertTrue(result.trend_profile.updated_at)
            self.assertTrue(result.trend_profile.valid_until)
            self.assertIn("overall_confidence", result.validation_summary)
            self.assertIn("resolved_path", result.collector_trace)
            self.assertEqual(result.validation_summary["status"], "HOLD")

    def test_falls_back_when_profile_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = TrendAnalysisAgentService(trends_dir=Path(tmp_dir))

            result = service.load(TrendAnalysisInput(niche="history"))

            self.assertTrue(result.fallback.used)
            self.assertEqual(result.fallback.reason, "TREND_PROFILE_FALLBACK")
            self.assertEqual(result.trend_profile.niche, "default")
            self.assertEqual(result.trend_profile.trend_source, "safe_default")

    def test_loads_from_canonical_current_directory_and_persists_history_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_root = Path(tmp_dir)
            current_dir = trends_root / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            (current_dir / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "dominant_hooks": ["story_opening"],
                        "avg_duration": "35-60",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                        "trend_source": "manual_curation",
                        "sample_size": 12,
                        "evidence": [
                            {
                                "evidence_type": "manual_top_video",
                                "source": "manual_curation",
                                "reference_id": "vid_001",
                                "reference_url": "https://example.com/vid_001",
                                "captured_at": "2026-04-01T00:00:00Z",
                                "metadata": {"rank": 1},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_root)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-03T00:00:00Z"))

            self.assertFalse(result.fallback.used)
            self.assertEqual(result.collector_trace["storage_mode"], "canonical_v2")
            self.assertEqual(result.trend_profile.trend_source, "manual_curation")
            self.assertEqual(result.validation_summary["status"], "APPROVE")
            history_files = list((trends_root / "history" / "horror").glob("*.json"))
            self.assertEqual(len(history_files), 1)

    def test_assembles_hybrid_profile_from_explicit_source_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_root = Path(tmp_dir)
            (trends_root / "manual_curation").mkdir(parents=True, exist_ok=True)
            (trends_root / "cache" / "creative_center").mkdir(parents=True, exist_ok=True)
            (trends_root / "manual_curation" / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "collected_at": "2026-04-02T00:00:00Z",
                        "sample_size": 6,
                        "dominant_hooks": ["ominous_question", "story_opening"],
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                        "evidence": [
                            {
                                "evidence_type": "manual_top_video",
                                "source": "manual_curation",
                                "reference_id": "manual_001",
                                "reference_url": "https://example.com/manual_001",
                                "captured_at": "2026-04-02T00:00:00Z",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (trends_root / "cache" / "creative_center" / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "collected_at": "2026-04-03T00:00:00Z",
                        "sample_size": 20,
                        "dominant_hooks": ["story_opening", "shock_statement"],
                        "avg_duration": "35-60",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                        "evidence": [
                            {
                                "evidence_type": "creative_center_hashtag",
                                "source": "creative_center",
                                "reference_id": "#horrortok",
                                "reference_url": "https://ads.tiktok.com/business/creativecenter",
                                "captured_at": "2026-04-03T00:00:00Z",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_root)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-03T12:00:00Z"))

            self.assertFalse(result.fallback.used)
            self.assertEqual(result.trend_profile.trend_source, "hybrid")
            self.assertEqual(result.collector_trace["assembly_mode"], "source_assembly")
            self.assertEqual(result.collector_trace["source_mix"], ["creative_center", "manual_curation"])
            self.assertEqual(result.trend_profile.dominant_hooks[0], "story_opening")
            self.assertGreaterEqual(result.trend_profile.sample_size, 26)
            self.assertTrue((trends_root / "current" / "horror.json").exists())
            self.assertEqual(result.validation_summary["status"], "APPROVE")

    def test_force_refresh_reports_explicit_creative_center_failure_trace(self) -> None:
        class _FailingCollector:
            def collect(self, data):  # noqa: ANN001
                _ = data
                return TrendCollectorResult(
                    source_record=None,
                    used_stub=False,
                    trace={"status": "COLLECTION_FAILED", "source": "creative_center"},
                )

        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_root = Path(tmp_dir)
            (trends_root / "manual_curation").mkdir(parents=True, exist_ok=True)
            (trends_root / "manual_curation" / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "collected_at": "2026-04-02T00:00:00Z",
                        "sample_size": 4,
                        "dominant_hooks": ["story_opening"],
                        "avg_duration": "35-60",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                        "evidence": [{"evidence_type": "manual_top_video", "source": "manual_curation", "reference_id": "m1"}],
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_root, creative_center_collector=_FailingCollector())

            result = service.load(
                TrendAnalysisInput(
                    niche="horror",
                    force_refresh=True,
                    current_time="2026-04-03T12:00:00Z",
                )
            )

            self.assertFalse(result.fallback.used)
            self.assertIsNotNone(result.collector_trace["creative_center_refresh"])
            self.assertEqual(
                result.collector_trace["creative_center_refresh"]["trace"]["status"],
                "COLLECTION_FAILED",
            )

    def test_force_refresh_persists_real_creative_center_collection_to_cache(self) -> None:
        class _RealishCollector:
            def collect(self, data):  # noqa: ANN001
                return TrendCollectorResult(
                    source_record=TrendSourceRecord(
                        source="creative_center",
                        niche=data.niche,
                        region=data.region,
                        collected_at="2026-04-03T00:00:00Z",
                        sample_size=2,
                        dominant_hooks=[],
                        avg_duration="",
                        pacing="",
                        visual_style="",
                        text_style="",
                        evidence=[
                            TrendEvidenceReference(
                                evidence_type="creative_center_hashtag",
                                source="creative_center",
                                reference_id="#horror",
                                captured_at="2026-04-03T00:00:00Z",
                            ),
                            TrendEvidenceReference(
                                evidence_type="creative_center_song",
                                source="creative_center",
                                reference_id="song:Gucci",
                                captured_at="2026-04-03T00:00:00Z",
                            ),
                        ],
                        source_metadata={"hashtags": ["horror"], "songs": [{"title": "Gucci", "artist": "MAF Teeski"}]},
                    ),
                    used_stub=False,
                    trace={"status": "COLLECTED", "source": "creative_center"},
                )

        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_root = Path(tmp_dir)
            (trends_root / "manual_curation").mkdir(parents=True, exist_ok=True)
            (trends_root / "manual_curation" / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "source": "manual_curation",
                        "collected_at": "2026-04-03T00:00:00Z",
                        "sample_size": 6,
                        "dominant_hooks": ["story_opening"],
                        "avg_duration": "8-12s",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                        "evidence": [{"evidence_type": "manual_top_video", "source": "manual_curation", "reference_id": "m1"}],
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_root, creative_center_collector=_RealishCollector())

            result = service.load(
                TrendAnalysisInput(
                    niche="horror",
                    force_refresh=True,
                    current_time="2026-04-03T12:00:00Z",
                )
            )

            self.assertFalse(result.fallback.used)
            self.assertEqual(result.collector_trace["creative_center_refresh"]["trace"]["status"], "COLLECTED")
            self.assertTrue((trends_root / "cache" / "creative_center" / "horror.json").exists())
            self.assertIn("creative_center", result.collector_trace["source_mix"])

    def test_rejected_primary_profile_falls_back_to_validated_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_root = Path(tmp_dir)
            (trends_root / "current").mkdir(parents=True, exist_ok=True)
            (trends_root / "cache" / "validated").mkdir(parents=True, exist_ok=True)
            (trends_root / "current" / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "trend_source": "manual_curation",
                        "updated_at": "2026-03-01T00:00:00Z",
                        "valid_until": "2026-03-10T00:00:00Z",
                        "dominant_hooks": ["story_opening"],
                        "avg_duration": "35-60",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                        "sample_size": 12,
                        "evidence": [
                            {"evidence_type": "manual_top_video", "source": "manual_curation", "reference_id": "bad_1"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (trends_root / "cache" / "validated" / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "trend_source": "creative_center",
                        "updated_at": "2026-04-02T00:00:00Z",
                        "valid_until": "2026-04-08T00:00:00Z",
                        "dominant_hooks": ["shock_statement"],
                        "avg_duration": "35-60",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                        "sample_size": 18,
                        "evidence": [
                            {"evidence_type": "creative_center_hashtag", "source": "creative_center", "reference_id": "#horror"}
                        ],
                        "confidence_scores": {"overall": 0.82, "dominant_hooks": 0.82, "avg_duration": 0.82, "pacing": 0.82, "visual_style": 0.82},
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_root)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-03T00:00:00Z"))

            self.assertTrue(result.fallback.used)
            self.assertEqual(result.fallback.reason, "TREND_CACHE_FALLBACK")
            self.assertEqual(result.trend_profile.trend_source, "creative_center")
            self.assertEqual(result.validation_summary["status"], "APPROVE")
            self.assertEqual(result.collector_trace["fallback_path"], "validated_cache")

    def test_rejected_primary_and_missing_cache_fall_back_to_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_root = Path(tmp_dir)
            (trends_root / "current").mkdir(parents=True, exist_ok=True)
            (trends_root / "history" / "horror").mkdir(parents=True, exist_ok=True)
            (trends_root / "current" / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "trend_source": "manual_curation",
                        "updated_at": "2026-03-01T00:00:00Z",
                        "valid_until": "2026-03-10T00:00:00Z",
                        "dominant_hooks": ["story_opening"],
                        "avg_duration": "35-60",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                        "sample_size": 12,
                        "evidence": [
                            {"evidence_type": "manual_top_video", "source": "manual_curation", "reference_id": "bad_1"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (trends_root / "history" / "horror" / "20260402T000000Z.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "trend_source": "manual_curation",
                        "updated_at": "2026-04-01T00:00:00Z",
                        "valid_until": "2026-04-10T00:00:00Z",
                        "dominant_hooks": ["ominous_question"],
                        "avg_duration": "35-60",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                        "sample_size": 8,
                        "evidence": [
                            {"evidence_type": "manual_top_video", "source": "manual_curation", "reference_id": "hist_1"}
                        ],
                        "confidence_scores": {"overall": 0.71, "dominant_hooks": 0.71, "avg_duration": 0.71, "pacing": 0.71, "visual_style": 0.71},
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_root)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-03T00:00:00Z"))

            self.assertTrue(result.fallback.used)
            self.assertEqual(result.fallback.reason, "TREND_HISTORY_FALLBACK")
            self.assertEqual(result.trend_profile.dominant_hooks[0], "ominous_question")
            self.assertEqual(result.validation_summary["status"], "APPROVE")
            self.assertEqual(result.collector_trace["fallback_path"], "history")


if __name__ == "__main__":
    unittest.main()
