from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.analysis.consistency.service import DataConsistencyCheckerService
from app.content.creative_pack.store_jsonl import append_pack
from app.data.publish_records.store_jsonl import read_all_records as read_publish_records
from app.metrics.store_jsonl import read_all_records as read_metrics
from app.runtime.rollout.pilot_runner import run_pilot_rollout


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _build_accounts() -> list[str]:
    accounts: list[str] = []
    for idx in range(1, 7):
        accounts.append(f"acc_truecrime_batch_{idx:03d}")
    for idx in range(1, 7):
        accounts.append(f"acc_history_batch_{idx:03d}")
    for idx in range(1, 7):
        accounts.append(f"acc_mystery_batch_{idx:03d}")
    return accounts


def _load_existing_accounts(base_dir: Path) -> list[str]:
    publish_records_path = base_dir / "data" / "publish_records" / "publish_records.jsonl"
    rows = read_publish_records(publish_records_path)
    return sorted({str(row.get("account_id") or "") for row in rows if row.get("account_id")})


def _seed_creative_packs(*, base_dir: Path, account_ids: list[str], now: datetime) -> list[dict[str, str]]:
    creative_packs_path = base_dir / "content" / "creative_packs" / "creative_packs.jsonl"
    rows: list[dict[str, str]] = []
    for account_id in account_ids:
        creative_pack_id = f"cp_{account_id}_{now.strftime('%Y%m%d')}"
        row = {
            "creative_pack_id": creative_pack_id,
            "account_id": account_id,
            "created_at": now.isoformat().replace("+00:00", "Z"),
            "source": "local_d23_18_batch",
        }
        append_pack(row, creative_packs_path)
        rows.append(row)
    return rows


def _ffprobe_validate(video_path: Path) -> dict[str, object]:
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        cmd = [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(video_path),
        ]
    else:
        docker = shutil.which("docker")
        if not docker:
            raise RuntimeError(f"FFPROBE_UNAVAILABLE:{video_path}")
        relative = video_path.resolve().relative_to(ROOT.resolve())
        container_path = str(PurePosixPath("/workspace").joinpath(*relative.parts))
        cmd = [
            docker,
            "run",
            "--rm",
            "--entrypoint",
            "ffprobe",
            "-v",
            f"{ROOT.resolve().as_posix()}:/workspace",
            "-w",
            "/workspace",
            "cortai10-api",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            container_path,
        ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    streams = payload.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if video_stream is None:
        raise RuntimeError(f"VIDEO_STREAM_MISSING:{video_path}")
    if audio_stream is None:
        raise RuntimeError(f"AUDIO_STREAM_MISSING:{video_path}")
    width = int(video_stream.get("width") or 0)
    height = int(video_stream.get("height") or 0)
    if (width, height) != (1080, 1920):
        raise RuntimeError(f"VIDEO_DIMENSIONS_INVALID:{video_path}:{width}x{height}")
    return {
        "codec_video": video_stream.get("codec_name"),
        "codec_audio": audio_stream.get("codec_name"),
        "width": width,
        "height": height,
        "duration": float(payload.get("format", {}).get("duration") or 0.0),
    }


def _validate_batch(*, base_dir: Path, batch_id: str, started_at: datetime, account_ids: list[str], creative_packs: list[dict[str, str]], rollout_result: dict[str, object]) -> dict[str, object]:
    audit_dir = base_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    publish_records_path = base_dir / "data" / "publish_records" / "publish_records.jsonl"
    metrics_path = base_dir / "metrics" / "video_metrics.jsonl"
    metadata_dir = base_dir / "content" / "metadata"
    video_dir = base_dir / "content" / "video"
    audio_dir = base_dir / "content" / "audio"

    publish_records = read_publish_records(publish_records_path)
    metrics_rows = read_metrics(metrics_path)
    videos = sorted(video_dir.glob("*.mp4"))
    audios = sorted(audio_dir.glob("*.wav"))
    metadatas = sorted(metadata_dir.glob("*.json"))

    if len(videos) != 18:
        raise RuntimeError(f"VIDEO_COUNT_INVALID:{len(videos)}")
    if len(audios) != 18:
        raise RuntimeError(f"AUDIO_COUNT_INVALID:{len(audios)}")
    if len(metadatas) != 18:
        raise RuntimeError(f"METADATA_COUNT_INVALID:{len(metadatas)}")
    if len(publish_records) != 18:
        raise RuntimeError(f"PUBLISH_RECORD_COUNT_INVALID:{len(publish_records)}")
    if len(metrics_rows) != 18:
        raise RuntimeError(f"METRICS_COUNT_INVALID:{len(metrics_rows)}")

    publish_ids = [str(row["publish_id"]) for row in publish_records]
    if len(set(publish_ids)) != 18:
        raise RuntimeError("PUBLISH_RECORD_DUPLICATE_IDS")

    artifact_rows: list[dict[str, object]] = []
    for metadata_path in metadatas:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        video_path = Path(metadata["audio_path"]).with_suffix(".mp4")
        video_path = Path(metadata["audio_path"].replace("\\audio\\", "\\video\\").replace(".wav", ".mp4"))
        if not video_path.exists():
            video_path = video_dir / f"{metadata['render_job_id']}.mp4"
        audio_path = Path(metadata["audio_path"])
        if not audio_path.exists():
            raise RuntimeError(f"AUDIO_ARTIFACT_MISSING:{audio_path}")
        if not video_path.exists():
            raise RuntimeError(f"VIDEO_ARTIFACT_MISSING:{video_path}")
        probe = _ffprobe_validate(video_path)
        if float(metadata.get("render_duration_s") or 0.0) < 8.0:
            raise RuntimeError(f"RENDER_DURATION_INVALID:{metadata['render_job_id']}")
        artifact_rows.append(
            {
                "render_job_id": metadata["render_job_id"],
                "video_path": str(video_path),
                "audio_path": str(audio_path),
                "metadata_path": str(metadata_path),
                "probe": probe,
            }
        )

    consistency = DataConsistencyCheckerService(
        publish_records_path=publish_records_path,
        video_metrics_path=metrics_path,
        creative_packs_path=base_dir / "content" / "creative_packs" / "creative_packs.jsonl",
        safety_events_path=base_dir / "events" / "events.jsonl",
        analysis_dir=base_dir / "analysis",
    ).generate_consistency_report()
    if consistency.status != "OK":
        raise RuntimeError(f"CONSISTENCY_NOT_OK:{consistency.status}")

    report = {
        "batch_id": batch_id,
        "entrypoint": "app.runtime.rollout.pilot_runner.run_pilot_rollout",
        "base_dir": str(base_dir),
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "accounts": account_ids,
        "creative_packs_seeded": creative_packs,
        "rollout_result": rollout_result,
        "counts": {
            "videos": len(videos),
            "audios": len(audios),
            "metadatas": len(metadatas),
            "publish_records": len(publish_records),
            "metrics": len(metrics_rows),
        },
        "artifacts": artifact_rows,
        "consistency_status": consistency.status,
        "consistency_json": str(base_dir / "analysis" / "consistency_check.json"),
        "consistency_md": str(base_dir / "analysis" / "consistency_check.md"),
        "verdict": "PASS",
    }
    report_path = audit_dir / "batch_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", type=Path, default=None)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    started_at = _utc_now()
    if args.base_dir is None:
        batch_id = f"local_d23_18_{started_at.strftime('%Y%m%d_%H%M%S')}"
        base_dir = ROOT / "OUT" / "batches" / batch_id
    else:
        base_dir = args.base_dir.resolve()
        batch_id = base_dir.name

    if args.validate_only:
        account_ids = _load_existing_accounts(base_dir)
        creative_packs_path = base_dir / "content" / "creative_packs" / "creative_packs.jsonl"
        creative_packs = []
        if creative_packs_path.exists():
            with creative_packs_path.open("r", encoding="utf-8") as handle:
                creative_packs = [json.loads(line) for line in handle if line.strip()]
        rollout_result = {"mode": "validate_only", "base_dir": str(base_dir)}
    else:
        account_ids = _build_accounts()
        stage_by_account = {account_id: "GROWTH" for account_id in account_ids}
        creative_packs = _seed_creative_packs(base_dir=base_dir, account_ids=account_ids, now=started_at)
        rollout_result = run_pilot_rollout(
            base_dir=base_dir,
            account_ids=account_ids,
            stage_by_account=stage_by_account,
            now=started_at,
        )

    report = _validate_batch(
        base_dir=base_dir,
        batch_id=batch_id,
        started_at=started_at,
        account_ids=account_ids,
        creative_packs=creative_packs,
        rollout_result=rollout_result,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
