from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.models import ExecutionEnvelope
from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import RenderAdapter, RenderResponse
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.creative.contracts.creative_pack import (
    AssetBackgroundPlan,
    AssetDecisionContract,
    AssetPlan,
    AssetRuntimeConstraints,
    AssetSegmentPlan,
    VoicePlan,
)
from app.creative.contracts.edit_plan import EditPlan


class _CaptureRenderAdapter(RenderAdapter):
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.received_asset_plan: AssetPlan | None = None
        self.received_edit_plan: EditPlan | None = None

    def render_video(
        self,
        *,
        audio_path: str,
        script_text: str,
        asset_plan: AssetPlan,
        edit_plan: EditPlan | None,
        screen_blocks: list[str] | None,
        segment_durations: list[float] | None,
        render_job_id: str,
        template_id: str | None,
        aspect_ratio: str | None,
        attempt_count: int,
    ) -> RenderResponse:
        del audio_path, script_text, screen_blocks, segment_durations, template_id, aspect_ratio, attempt_count
        self.received_asset_plan = asset_plan
        self.received_edit_plan = edit_plan
        target = self.base_dir / "video" / f"{render_job_id}.mp4"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"video")
        return RenderResponse(video_path=str(target))


class AssetPlanRuntimeIntegrationTests(unittest.TestCase):
    def test_pipeline_passes_resolved_asset_plan_into_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            render = _CaptureRenderAdapter(base)
            service = ContentPipelineService(
                tts_adapter=StubTtsAdapter(base_dir=base),
                render_adapter=render,
                publish_adapter=StubPublishAdapter(),
                event_path=base / "events.jsonl",
            )
            local_hook = "assets/imports/pexels/warning_display/pexels_warning_display_panel_2.jpg"
            local_setup = "assets/imports/pexels/intercom_recorder/pexels_intercom_panel_wall_13.jpg"
            local_payoff = "assets/imports/pexels/intercom_recorder/pexels_intercom_panel_wall_1.jpg"
            asset_plan = AssetPlan(
                segments={
                    "hook": AssetSegmentPlan(
                        background=AssetBackgroundPlan(source="local", path=local_hook),
                        category="door",
                        decision_contract=AssetDecisionContract(
                            entity="door",
                            event="sealed_containment",
                            anomaly_type="restricted_access",
                            visibility_requirement="explicit",
                            photographability="real",
                            justification="hook needs door for sealed_containment with explicit visibility and real evidence",
                        ),
                    ),
                    "setup": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=local_setup), category="room"),
                    "payoff": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=local_payoff), category="device"),
                },
                runtime_constraints=AssetRuntimeConstraints(deterministic_seed="seed"),
            )

            output = service.execute(
                ExecutionEnvelope(
                    job_id="job",
                    account_id="acc",
                    creative_pack_id="cp",
                    publish_slot="2026-03-20T00:00:00Z",
                ),
                script_text="HOOK.\\n\\nSETUP.\\n\\nPAYOFF.",
                asset_plan=asset_plan,
                voice_plan=VoicePlan(provider="piper", voice_id="voice", style="baseline"),
            )

            self.assertIsNotNone(render.received_asset_plan)
            assert render.received_asset_plan is not None
            self.assertEqual(render.received_asset_plan.hook_asset.replace("\\", "/"), local_hook)
            self.assertEqual(render.received_asset_plan.setup_asset.replace("\\", "/"), local_setup)
            self.assertEqual(render.received_asset_plan.payoff_asset.replace("\\", "/"), local_payoff)
            self.assertTrue(output["result"]["visual_trace"]["rows"])
            self.assertEqual(
                render.received_asset_plan.segments["hook"].decision_contract.entity,
                "door",
            )
            self.assertIn(
                "visual_query",
                render.received_asset_plan.to_dict()["segments"]["hook"],
            )
            self.assertEqual(
                output["result"]["visual_trace"]["rows"][0]["event"],
                "sealed_containment",
            )
            self.assertIsNone(render.received_edit_plan)


if __name__ == "__main__":
    unittest.main()
