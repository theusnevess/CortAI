from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.contracts.creative_pack import (
    AssetBackgroundPlan,
    AssetDecisionContract,
    AssetPlan,
    AssetRuntimeConstraints,
    AssetSegmentPlan,
)
from app.runtime.asset_router import AssetRouter
from app.runtime.asset_selector import AssetSelector


class _ComfyUiStub:
    def __init__(self, *, root: Path) -> None:
        self.root = root

    def generate_image(self, *, prompt: str, render_job_id: str, segment_name: str, seed: str = ""):
        _ = (prompt, seed)
        target = self.root / f"{render_job_id}_{segment_name}_generated.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"img")
        metadata = self.root / f"{render_job_id}_{segment_name}_generated.json"
        metadata.write_text("{}", encoding="utf-8")
        return type(
            "ComfyUiResult",
            (),
            {
                "image_path": str(target),
                "metadata_path": str(metadata),
                "source_type": "comfyui",
                "model": "test-model",
                "operation": "generate",
            },
        )()

    def edit_image(self, *, prompt: str, input_image_path: str, render_job_id: str, segment_name: str):
        _ = (prompt, input_image_path)
        target = self.root / f"{render_job_id}_{segment_name}_edited.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"img")
        metadata = self.root / f"{render_job_id}_{segment_name}_edited.json"
        metadata.write_text("{}", encoding="utf-8")
        return type(
            "ComfyUiResult",
            (),
            {
                "image_path": str(target),
                "metadata_path": str(metadata),
                "source_type": "comfyui",
                "model": "test-model",
                "operation": "edit",
            },
        )()


class AssetRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures = {}
        AssetSelector._global_failed_sequences_prevented = {}

    def test_prefers_local_path_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            external_path = Path(tmp_dir) / "assets" / "imports" / "pexels" / "warning_display" / "panel.jpg"
            external_path.parent.mkdir(parents=True, exist_ok=True)
            external_path.write_bytes(b"img")
            catalog = Path(tmp_dir) / "catalog.json"
            catalog.write_text(
                '[{"path":"%s","source_type":"pexels","category":"warning_display","subtype":"panel","family":"warning_display","framing":"medium","tags":["warning","signal"],"mood":"tense","semantic_pattern_fit":[],"entity_fit":[],"hook_strength_score":0.8,"payoff_strength_score":0.8,"setup_specificity_score":0.7,"realism_score":0.95,"usage_count":0,"freshness_score":1.0,"resolution":[1080,1920],"strength":0.8,"genericity":0.1}]'
                % str(external_path).replace("\\", "/"),
                encoding="utf-8",
            )
            router = AssetRouter(selector=AssetSelector(catalog_path=catalog))
            plan = AssetPlan(
                segments={
                    "hook": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(external_path)), category="warning_display"),
                    "setup": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(external_path)), category="warning_display"),
                    "payoff": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(external_path)), category="warning_display"),
                },
                runtime_constraints=AssetRuntimeConstraints(deterministic_seed="seed"),
            )

            resolved, trace = router.resolve_plan(asset_plan=plan, render_job_id="rj_1")

            self.assertEqual(resolved.hook_asset, str(external_path))
            self.assertEqual(trace["rows"][0]["source"], "pexels")

    def test_visual_trace_persists_explicit_decision_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            external_path = Path(tmp_dir) / "assets" / "imports" / "unsplash" / "document" / "doc.jpg"
            external_path.parent.mkdir(parents=True, exist_ok=True)
            external_path.write_bytes(b"img")
            catalog = Path(tmp_dir) / "catalog.json"
            catalog.write_text(
                '[{"path":"%s","source_type":"unsplash","category":"document","subtype":"casefile","family":"documentary_evidence","framing":"detail","tags":["document","anomaly"],"mood":"tense","semantic_pattern_fit":[],"entity_fit":[],"hook_strength_score":0.8,"payoff_strength_score":0.9,"setup_specificity_score":0.75,"realism_score":0.95,"usage_count":0,"freshness_score":1.0,"resolution":[1080,1920],"strength":0.85,"genericity":0.08}]'
                % str(external_path).replace("\\", "/"),
                encoding="utf-8",
            )
            router = AssetRouter(selector=AssetSelector(catalog_path=catalog))
            plan = AssetPlan(
                segments={
                    "hook": AssetSegmentPlan(
                        background=AssetBackgroundPlan(source="local", path=str(external_path)),
                        category="document",
                        decision_contract=AssetDecisionContract(
                            entity="document",
                            event="data_inconsistency",
                            anomaly_type="temporal_contradiction",
                            visibility_requirement="explicit",
                            photographability="real",
                            justification="hook needs document for data_inconsistency with explicit visibility and real evidence",
                        ),
                    ),
                    "setup": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(external_path)), category="document"),
                    "payoff": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(external_path)), category="document"),
                },
                runtime_constraints=AssetRuntimeConstraints(deterministic_seed="seed"),
            )

            _, trace = router.resolve_plan(asset_plan=plan, render_job_id="rj_contract")

            row = trace["rows"][0]
            self.assertEqual(row["entity"], "document")
            self.assertEqual(row["event"], "data_inconsistency")
            self.assertEqual(row["anomaly_type"], "temporal_contradiction")
            self.assertEqual(row["visibility_requirement"], "explicit")
            self.assertEqual(row["photographability"], "real")
            self.assertIn("real evidence", row["justification"])

    def test_fails_explicitly_when_no_external_asset_and_no_safe_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            catalog.write_text("[]", encoding="utf-8")
            router = AssetRouter(selector=AssetSelector(catalog_path=catalog))
            plan = AssetPlan(
                segments={
                    "hook": AssetSegmentPlan(background=AssetBackgroundPlan(source="local"), category="door"),
                    "setup": AssetSegmentPlan(background=AssetBackgroundPlan(source="local"), category="room"),
                    "payoff": AssetSegmentPlan(background=AssetBackgroundPlan(source="local"), category="device"),
                },
                runtime_constraints=AssetRuntimeConstraints(
                    deterministic_seed="seed",
                    allow_safe_fallback=False,
                ),
            )
            with self.assertRaisesRegex(RuntimeError, "ASSET_RUNTIME_NO_EXTERNAL_ASSET"):
                router.resolve_plan(asset_plan=plan, render_job_id="rj_fail_external_only")

    def test_uses_comfyui_generation_when_no_external_asset_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            catalog.write_text("[]", encoding="utf-8")
            router = AssetRouter(
                selector=AssetSelector(catalog_path=catalog),
                comfyui_service=_ComfyUiStub(root=Path(tmp_dir) / "comfyui"),
            )
            plan = AssetPlan(
                visual_anchor="warning_display",
                semantic_pattern="active_signal",
                entity="panel",
                segments={
                    "hook": AssetSegmentPlan(background=AssetBackgroundPlan(source="local"), category="warning_display"),
                    "setup": AssetSegmentPlan(background=AssetBackgroundPlan(source="local"), category="warning_display"),
                    "payoff": AssetSegmentPlan(background=AssetBackgroundPlan(source="local"), category="warning_display"),
                },
                runtime_constraints=AssetRuntimeConstraints(
                    deterministic_seed="seed",
                    allow_safe_fallback=False,
                    allow_comfyui_generation_fallback=True,
                ),
            )

            resolved, trace = router.resolve_plan(asset_plan=plan, render_job_id="rj_comfyui")

            self.assertIn("comfyui", resolved.hook_asset)
            self.assertEqual(trace["rows"][0]["source"], "comfyui")

    def test_uses_comfyui_edit_when_requested_by_segment_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            external_path = Path(tmp_dir) / "assets" / "imports" / "pexels" / "warning_display" / "panel.jpg"
            external_path.parent.mkdir(parents=True, exist_ok=True)
            external_path.write_bytes(b"img")
            catalog = Path(tmp_dir) / "catalog.json"
            catalog.write_text(
                '[{"path":"%s","source_type":"pexels","category":"warning_display","subtype":"panel","family":"warning_display","framing":"medium","tags":["warning","signal"],"mood":"tense","semantic_pattern_fit":[],"entity_fit":[],"hook_strength_score":0.8,"payoff_strength_score":0.8,"setup_specificity_score":0.7,"realism_score":0.95,"usage_count":0,"freshness_score":1.0,"resolution":[1080,1920],"strength":0.8,"genericity":0.1}]'
                % str(external_path).replace("\\", "/"),
                encoding="utf-8",
            )
            router = AssetRouter(
                selector=AssetSelector(catalog_path=catalog),
                comfyui_service=_ComfyUiStub(root=Path(tmp_dir) / "comfyui"),
            )
            plan = AssetPlan(
                segments={
                    "hook": AssetSegmentPlan(
                        background=AssetBackgroundPlan(source="local", path=str(external_path)),
                        category="warning_display",
                        effects=["comfyui_edit"],
                    ),
                    "setup": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(external_path)), category="warning_display"),
                    "payoff": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(external_path)), category="warning_display"),
                },
                runtime_constraints=AssetRuntimeConstraints(
                    deterministic_seed="seed",
                    allow_comfyui_edit=True,
                ),
            )

            resolved, trace = router.resolve_plan(asset_plan=plan, render_job_id="rj_comfyui_edit")

            self.assertIn("edited", resolved.hook_asset)
            self.assertEqual(trace["rows"][0]["source"], "comfyui")

    def test_fails_when_only_local_curated_candidates_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog = Path(tmp_dir) / "catalog.json"
            catalog.write_text(
                '[{"path":"assets/curated/legacy.jpg","source_type":"local_curated","category":"door","subtype":"sealed_door","family":"door","framing":"medium","tags":["door","sealed"],"mood":"tense","semantic_pattern_fit":[],"entity_fit":[],"hook_strength_score":0.9,"payoff_strength_score":0.9,"setup_specificity_score":0.8,"realism_score":0.9,"usage_count":0,"freshness_score":0.9,"resolution":[1080,1920],"strength":0.9,"genericity":0.1}]',
                encoding="utf-8",
            )
            router = AssetRouter(selector=AssetSelector(catalog_path=catalog))
            plan = AssetPlan(
                segments={
                    "hook": AssetSegmentPlan(background=AssetBackgroundPlan(source="local"), category="door"),
                    "setup": AssetSegmentPlan(background=AssetBackgroundPlan(source="local"), category="door"),
                    "payoff": AssetSegmentPlan(background=AssetBackgroundPlan(source="local"), category="door"),
                },
                runtime_constraints=AssetRuntimeConstraints(
                    deterministic_seed="seed",
                    allow_safe_fallback=False,
                ),
            )

            with self.assertRaisesRegex(RuntimeError, "ASSET_RUNTIME_NO_EXTERNAL_ASSET"):
                router.resolve_plan(asset_plan=plan, render_job_id="rj_external_only")

    def test_fails_when_repeated_signature_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            hook_path = Path(tmp_dir) / "assets" / "imports" / "pexels" / "document" / "hook.jpg"
            setup_path = Path(tmp_dir) / "assets" / "imports" / "unsplash" / "archive" / "setup.jpg"
            payoff_path = Path(tmp_dir) / "assets" / "imports" / "pixabay" / "document" / "payoff.jpg"
            for item in (hook_path, setup_path, payoff_path):
                item.parent.mkdir(parents=True, exist_ok=True)
                item.write_bytes(b"img")
            catalog = Path(tmp_dir) / "catalog.json"
            catalog.write_text(
                (
                    '[{"path":"%s","source_type":"pexels","category":"document","subtype":"casefile","family":"doc_family","framing":"closeup","tags":["document","anomaly","event_data_inconsistency"],"mood":"tense","semantic_pattern_fit":[],"entity_fit":[],"hook_strength_score":0.9,"payoff_strength_score":0.8,"setup_specificity_score":0.7,"realism_score":0.95,"usage_count":0,"freshness_score":1.0,"resolution":[1080,1920],"strength":0.9,"genericity":0.05},'
                    '{"path":"%s","source_type":"unsplash","category":"archive","subtype":"records_room","family":"archive_family","framing":"medium","tags":["archive","context","event_archive_context"],"mood":"neutral","semantic_pattern_fit":[],"entity_fit":[],"hook_strength_score":0.5,"payoff_strength_score":0.5,"setup_specificity_score":0.7,"realism_score":0.95,"usage_count":0,"freshness_score":1.0,"resolution":[1080,1920],"strength":0.8,"genericity":0.1},'
                    '{"path":"%s","source_type":"pixabay","category":"document","subtype":"proof","family":"doc_family","framing":"detail","tags":["document","proof","event_document_anomaly"],"mood":"tense","semantic_pattern_fit":[],"entity_fit":[],"hook_strength_score":0.7,"payoff_strength_score":0.95,"setup_specificity_score":0.75,"realism_score":0.95,"usage_count":0,"freshness_score":1.0,"resolution":[1080,1920],"strength":0.9,"genericity":0.05}]'
                )
                % (
                    str(hook_path).replace("\\", "/"),
                    str(setup_path).replace("\\", "/"),
                    str(payoff_path).replace("\\", "/"),
                ),
                encoding="utf-8",
            )
            router = AssetRouter(selector=AssetSelector(catalog_path=catalog))
            plan = AssetPlan(
                visual_anchor="document",
                semantic_pattern="anomaly",
                entity="document",
                segments={
                    "hook": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(hook_path)), category="document", tags=["case_family_live_evidence_review", "case_object_casefile", "case_evidence_date_mismatch"]),
                    "setup": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(setup_path)), category="archive", tags=["case_environment_evidence_desk", "case_state_contradiction"]),
                    "payoff": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(payoff_path)), category="document", tags=["case_evidence_contradiction_proof", "case_state_timestamp_anomaly"]),
                },
                runtime_constraints=AssetRuntimeConstraints(deterministic_seed="seed"),
            )

            router.resolve_plan(asset_plan=plan, render_job_id="rj_sig_1")
            with self.assertRaisesRegex(RuntimeError, "ASSET_RUNTIME_REPEATED_SIGNATURE|ASSET_RUNTIME_REPEATED_PROGRESSION_PATTERN|ASSET_RUNTIME_FAMILY_MONOCULTURE_FAILURE"):
                router.resolve_plan(asset_plan=plan, render_job_id="rj_sig_2")


if __name__ == "__main__":
    unittest.main()
