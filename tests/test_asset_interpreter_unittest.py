from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.asset.interpreter import AssetInterpreterService
from app.creative.contracts.creative_pack import ScriptPlan, TrendProfile


class AssetInterpreterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AssetInterpreterService()

    def test_build_plan_derives_anchor_entity_and_segments(self) -> None:
        plan = self.service.build_plan(
            niche="true_crime",
            topic="sealed locker recorder",
            script_plan=ScriptPlan(
                hook="WHAT'S ON THE SEALED LOCKER RECORDER?",
                setup="Evidence locker sealed 14 years ago.",
                payoff="Voice of Detective James at 3:04 AM.",
            ),
            trend_profile=TrendProfile(niche="true_crime", pacing="baseline", visual_style="investigation_dark"),
            deterministic_seed="seed-1",
        )

        self.assertEqual(plan.visual_anchor, "door")
        self.assertEqual(plan.entity, "door")
        self.assertEqual(plan.runtime_constraints.deterministic_seed, "seed-1")
        self.assertIn("hook", plan.segments)
        self.assertIn("setup", plan.segments)
        self.assertIn("payoff", plan.segments)
        self.assertTrue(plan.segments["hook"].tags)
        self.assertEqual(plan.segments["hook"].decision_contract.entity, "door")
        self.assertTrue(plan.segments["hook"].decision_contract.justification)

    def test_documentary_hook_maps_to_document_anchor(self) -> None:
        plan = self.service.build_plan(
            niche="facts",
            topic="archive page changed date",
            script_plan=ScriptPlan(
                hook="ARCHIVES KEPT CHANGING ARCHIVE PAGE CHANGED DATE",
                setup="The entry was revised every night.",
                payoff="The timestamp pointed to a city that never stood.",
            ),
            trend_profile=TrendProfile(niche="facts", pacing="baseline", visual_style="archive_dark"),
            deterministic_seed="seed-2",
        )

        self.assertEqual(plan.visual_anchor, "document")
        self.assertEqual(plan.segments["hook"].category, "document")
        self.assertIn("event_data_inconsistency", plan.segments["hook"].tags)
        self.assertIn("anomaly_temporal_contradiction", plan.segments["hook"].tags)
        self.assertIn("evidence_date", plan.segments["hook"].tags)

    def test_intercom_warning_prefers_generated_device_and_corridor_context(self) -> None:
        plan = self.service.build_plan(
            niche="true_crime",
            topic="station intercom warning",
            script_plan=ScriptPlan(
                hook="POLICE REOPENED STATION INTERCOM WARNING LOGS.",
                setup="The recorder captured a voice from sealed evidence.",
                payoff="A voice from sealed evidence answered back.",
            ),
            trend_profile=TrendProfile(niche="true_crime", pacing="baseline", visual_style="investigation_dark"),
            deterministic_seed="seed-3",
        )

        self.assertEqual(plan.visual_anchor, "device")
        self.assertEqual(plan.entity, "intercom")
        self.assertEqual(plan.segments["hook"].background.source, "local")
        self.assertEqual(plan.segments["hook"].category, "warning_display")
        self.assertEqual(plan.segments["setup"].category, "institutional_space")
        self.assertEqual(plan.segments["payoff"].category, "intercom_recorder")
        self.assertIn("event_active_warning_state", plan.segments["hook"].tags)
        self.assertIn("evidence_intercom", plan.segments["hook"].tags)

    def test_sealed_room_whisper_marks_breach_event_and_presence_signals(self) -> None:
        plan = self.service.build_plan(
            niche="horror",
            topic="sealed room whisper",
            script_plan=ScriptPlan(
                hook="THE SEALED ROOM STARTED WHISPERING AFTER MIDNIGHT.",
                setup="Security tape on the door was still intact.",
                payoff="Something answered from inside the room.",
                generation_mode="test",
            ),
            trend_profile=TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
            deterministic_seed="seed-4",
        )

        self.assertTrue(
            "event_containment_breach" in plan.segments["hook"].tags
            or "event_unauthorized_presence" in plan.segments["hook"].tags
        )
        self.assertIn("evidence_sealed", plan.segments["setup"].tags)
        self.assertIn("event_unauthorized_presence", plan.segments["payoff"].tags)
        self.assertIn("evidence_presence", plan.segments["payoff"].tags)

    def test_visual_world_profile_is_shared_across_segments(self) -> None:
        plan = self.service.build_plan(
            niche="true_crime",
            topic="station intercom warning",
            script_plan=ScriptPlan(
                hook="THE STATION INTERCOM PLAYED A WARNING AFTER MIDNIGHT.",
                setup="A cold hallway led toward the dead speaker panel.",
                payoff="The intercom display lit up with a sealed code.",
            ),
            trend_profile=TrendProfile(niche="true_crime", pacing="baseline", visual_style="investigation_dark"),
            deterministic_seed="seed-world",
        )

        shared_expected = {
            "visual_family_institutional_device_alert",
            "environment_type_device_institutional_interior",
            "lighting_style_contrast_device_glow",
            "dominant_emotion_threat",
            "secondary_emotion_urgency",
            "mood_threatening",
            "world_forbid_corporate_people",
        }
        for segment_name in ("hook", "setup", "payoff"):
            segment_tags = set(plan.segments[segment_name].tags)
            self.assertTrue(shared_expected <= segment_tags)

    def test_segment_decision_contract_is_explicit_and_serializable(self) -> None:
        plan = self.service.build_plan(
            niche="facts",
            topic="archive page changed date",
            script_plan=ScriptPlan(
                hook="ARCHIVE PAGE CHANGED DATE",
                setup="The file stayed in the records room until midnight.",
                payoff="The timestamp changed again on the same page.",
            ),
            trend_profile=TrendProfile(niche="facts", pacing="baseline", visual_style="archive_dark"),
            deterministic_seed="seed-contract",
        )

        setup_contract = plan.segments["setup"].decision_contract
        self.assertEqual(setup_contract.entity, plan.entity)
        self.assertTrue(setup_contract.event)
        self.assertTrue(setup_contract.anomaly_type)
        self.assertTrue(setup_contract.visibility_requirement)
        self.assertTrue(setup_contract.photographability)
        self.assertIn("setup needs", setup_contract.justification)

        payload = plan.to_dict()
        self.assertIn("decision_contract", payload["segments"]["setup"])
        self.assertEqual(
            payload["segments"]["setup"]["decision_contract"]["entity"],
            setup_contract.entity,
        )
        self.assertIn("visual_query", payload["segments"]["setup"])

    def test_segment_visual_query_is_scene_based_and_serializable(self) -> None:
        plan = self.service.build_plan(
            niche="true_crime",
            topic="station intercom warning",
            script_plan=ScriptPlan(
                hook="STATION INTERCOM WARNING STARTED AT 03:04.",
                setup="Wall speaker stayed active with alert signal.",
                payoff="The warning panel kept escalating with a red code.",
            ),
            trend_profile=TrendProfile(niche="true_crime", pacing="baseline", visual_style="investigation_dark"),
            deterministic_seed="seed-visual-query",
        )

        hook_query = plan.segments["hook"].visual_query
        self.assertTrue(hook_query.subject)
        self.assertTrue(hook_query.state_or_event)
        self.assertTrue(hook_query.environment)
        self.assertTrue(hook_query.lighting)
        self.assertTrue(hook_query.framing)
        self.assertTrue(hook_query.mood)
        self.assertTrue(
            any(token in hook_query.search_query_real.lower() for token in ("warning", "panel", "intercom"))
        )

        payload = plan.to_dict()
        serialized_query = payload["segments"]["hook"]["visual_query"]
        self.assertEqual(serialized_query["subject"], hook_query.subject)
        self.assertEqual(serialized_query["search_query_real"], hook_query.search_query_real)

    def test_case_visual_pack_is_generated_and_encoded_in_tags(self) -> None:
        plan = self.service.build_plan(
            niche="true_crime",
            topic="station intercom warning",
            script_plan=ScriptPlan(
                hook="STATION INTERCOM WARNING STARTED AT 03:04.",
                setup="Wall speaker stayed active with alert signal.",
                payoff="The warning panel kept escalating with a red code.",
            ),
            trend_profile=TrendProfile(niche="true_crime", pacing="baseline", visual_style="investigation_dark"),
            deterministic_seed="seed-case-pack",
        )

        self.assertTrue(plan.case_visual_pack)
        self.assertEqual(
            plan.case_visual_pack.get("primary_case_family"),
            "institutional_alert_system",
        )
        tags = set(plan.segments["setup"].tags)
        self.assertIn("case_family_institutional_alert_system", tags)
        self.assertIn("case_state_warning_state", tags)
        payload = plan.to_dict()
        self.assertIn("case_visual_pack", payload)
        self.assertEqual(
            payload["case_visual_pack"]["primary_case_family"],
            "institutional_alert_system",
        )
        self.assertIn("case_core_objects", payload["case_visual_pack"])
        self.assertIn("forbidden_symbolic_motifs", payload["case_visual_pack"])
        self.assertIn("required_progression_steps", payload["case_visual_pack"])


if __name__ == "__main__":
    unittest.main()
