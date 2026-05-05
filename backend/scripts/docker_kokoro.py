import json
import shutil
import sys
from pathlib import Path
import subprocess

ROOT = Path("/workspace")
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.kokoro_adapter import KokoroAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.creative.contracts.creative_pack import AssetPlan

AUDIT_DIR = ROOT / "OUT" / "audit" / "asset_agent_production_validation"

metadata_dir = AUDIT_DIR / "runtime" / "content" / "metadata"

def _reconstruct_asset_plan(meta: dict) -> AssetPlan:
    ap = meta.get("asset_plan", {})
    return AssetPlan(
        hook_asset=ap.get("hook_asset", ""),
        setup_asset=ap.get("setup_asset", ""),
        payoff_asset=ap.get("payoff_asset", ""),
        visual_style=ap.get("visual_style", "phase1_baseline"),
        motion_profile=ap.get("motion_profile", "phase1_baseline"),
    )

def main():
    movies = list(metadata_dir.glob("*.json"))
    movies.sort()

    print("Initialize Kokoro in Docker...")
    kokoro = KokoroAdapter()
    if not kokoro.available():
        print("ERROR: Kokoro model not found or failed to load!")
        sys.exit(1)

    adapter = StubRenderAdapter(base_dir=AUDIT_DIR / "runtime" / "content")

    # Monkeypatch Docker calls
    original_which = shutil.which
    def fake_which(cmd):
        if cmd == "docker": return "/usr/bin/docker"
        return original_which(cmd)
    shutil.which = fake_which

    original_run = subprocess.run
    def fake_run(cmd, **kwargs):
        if "docker" in str(cmd[0]):
            ffmpeg_idx = cmd.index("ffmpeg") if "ffmpeg" in cmd else cmd.index("ffprobe")
            cmd = cmd[ffmpeg_idx:]
        return original_run(cmd, **kwargs)
    subprocess.run = fake_run

    processed = 0
    for meta_file in movies:
        if processed >= 3:
            break

        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        hook_bg = meta.get("hook_background_path")
        setup_bg = meta.get("setup_background_path")
        payoff_bg = meta.get("payoff_background_path")

        has_all = bool(hook_bg) and bool(setup_bg) and bool(payoff_bg)
        uniq = len(set(p for p in [hook_bg, setup_bg, payoff_bg] if p))

        if has_all and uniq == 3:
            job_id = meta.get("render_job_id")
            print(f"\n[{processed+1}/3] Processing Kokoro Voice & Render for: {job_id}")

            text_path = meta.get("text_path")
            if text_path:
                text_path = text_path.replace("C:\\Users\\Mathe\\Documents\\LUMA Cognitive Systems\\CortAI\\CortAI 1.0", "/workspace").replace("\\", "/")
            if text_path and Path(text_path).exists():
                script_text = Path(text_path).read_text(encoding="utf-8")
            else:
                print(f"  Missing text: {text_path}")
                continue

            print("  Generating voice...")
            try:
                pause_profile = [650] * max(0, len(script_text.split("\n\n")) - 1)

                tts_result = kokoro.generate_audio(
                    script_text=script_text,
                    voice_profile="af_heart",
                    language="en-us",
                    render_job_id=f"{job_id}_kokoro",
                    overall_rate=1.0,
                    inter_segment_pause_ms=pause_profile
                )
                kokoro_audio_path = tts_result.audio_path
                print(f"  Voice Generated: {kokoro_audio_path}")
            except Exception as e:
                print(f"  Failed Kokoro: {e}")
                continue

            print("  Rendering Docker...")
            asset_plan = _reconstruct_asset_plan(meta)
            blocks = meta.get("blocks", [])
            if not blocks:
                blocks = None

            try:
                response = adapter.render_video(
                    audio_path=kokoro_audio_path,
                    script_text=script_text,
                    asset_plan=asset_plan,
                    screen_blocks=blocks,
                    segment_durations=tts_result.segment_durations,
                    render_job_id=f"{job_id}_kokoro",
                    template_id=meta.get("template_id"),
                    aspect_ratio=meta.get("aspect_ratio"),
                    attempt_count=1,
                )
                print(f"  Success Render: {response.video_path}")
                processed += 1
            except Exception as e:
                print(f"  Failed Render: {e}")

if __name__ == "__main__":
    main()
