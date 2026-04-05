from __future__ import annotations

import sys
import tempfile
import unittest
import wave
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.perceptual_correction import analyze_frame, balance_sequence, correct_frame
from app.content.pipeline.render import StubRenderAdapter
from app.creative.contracts.creative_pack import AssetBackgroundPlan, AssetPlan, AssetRuntimeConstraints, AssetSegmentPlan


class PerceptualCorrectionTests(unittest.TestCase):
    def test_correct_frame_lifts_dark_luminance(self) -> None:
        dark = Image.new("RGB", (256, 256), (12, 12, 12))
        before = analyze_frame(dark)
        after_image = correct_frame(dark)
        after = analyze_frame(after_image)
        self.assertGreater(after.mean_luminance, before.mean_luminance)
        self.assertGreaterEqual(after.shadow_floor, before.shadow_floor)

    def test_balance_sequence_reduces_extreme_luminance_gap(self) -> None:
        images = [
            Image.new("RGB", (128, 128), (18, 18, 18)),
            Image.new("RGB", (128, 128), (45, 45, 45)),
            Image.new("RGB", (128, 128), (80, 80, 80)),
        ]
        balanced = balance_sequence(images)
        means = [analyze_frame(image).mean_luminance for image in balanced]
        self.assertLess(max(means) - min(means), 45.0)

    def test_render_metadata_uses_corrected_luminance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir) / "out"
            assets_dir = Path(tmp_dir) / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            hook = assets_dir / "hook.jpg"
            setup = assets_dir / "setup.jpg"
            payoff = assets_dir / "payoff.jpg"
            Image.new("RGB", (256, 256), (16, 16, 16)).save(hook)
            Image.new("RGB", (256, 256), (24, 24, 24)).save(setup)
            Image.new("RGB", (256, 256), (10, 10, 10)).save(payoff)
            audio = assets_dir / "audio.wav"
            self._write_wav(audio, duration_s=1.2)

            adapter = StubRenderAdapter(base_dir=base_dir)
            plan = AssetPlan(
                hook_asset=str(hook),
                setup_asset=str(setup),
                payoff_asset=str(payoff),
                visual_style="dark_backgrounds",
                motion_profile="subtle_push_in",
                visual_anchor="door",
                semantic_pattern="sealed",
                entity="room",
                segments={
                    "hook": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(hook)), category="door"),
                    "setup": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(setup)), category="room"),
                    "payoff": AssetSegmentPlan(background=AssetBackgroundPlan(source="local", path=str(payoff)), category="device"),
                },
                runtime_constraints=AssetRuntimeConstraints(),
            )
            adapter.render_video(
                audio_path=str(audio),
                script_text="A TEST HOOK. A TEST SETUP. A TEST PAYOFF.",
                asset_plan=plan,
                screen_blocks=["A TEST HOOK", "A TEST SETUP", "A TEST PAYOFF"],
                segment_durations=[1.0, 1.0, 1.0],
                render_job_id="render_test",
                template_id=None,
                aspect_ratio=None,
                attempt_count=1,
            )

            metadata_path = base_dir / "metadata" / "render_test.json"
            self.assertTrue(metadata_path.exists())
            metadata = __import__("json").loads(metadata_path.read_text(encoding="utf-8"))
            self.assertGreater(metadata["hook_background_mean_luma"], 16.0)
            self.assertGreater(metadata["setup_background_mean_luma"], 24.0)
            self.assertGreater(metadata["payoff_background_mean_luma"], 10.0)

    def _write_wav(self, path: Path, *, duration_s: float) -> None:
        sample_rate = 22050
        frames = int(sample_rate * duration_s)
        with wave.open(str(path), "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(sample_rate)
            writer.writeframes(b"\x00\x00" * frames)


if __name__ == "__main__":
    unittest.main()
