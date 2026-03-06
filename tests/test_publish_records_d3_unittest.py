from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.data.publish_records.invariants import (
    PublishRecordInvariantError,
    enforce_no_ambiguous_active_mapping,
)
from app.data.publish_records.repo import get_by_job, get_by_video
from app.data.publish_records.writer import write_publish_record
from app.data.schemas.publish_record import PublishRecordValidationError, validate_publish_record


def _base_record(**overrides):
    record = {
        "publish_id": "pub_001",
        "account_id": "acc_ca_001",
        "job_id": "job_001",
        "video_id": "vid_001",
        "platform": "tiktok",
        "publish_mode": "auto",
        "status": "posted",
        "published_at": "2026-03-04T18:00:00Z",
        "created_at": "2026-03-04T18:00:00Z",
        "metadata": {},
    }
    record.update(overrides)
    return record


class PublishRecordsD3Tests(unittest.TestCase):
    def test_schema_rejects_missing_required_and_invalid_status(self) -> None:
        with self.assertRaises(PublishRecordValidationError):
            validate_publish_record({"publish_id": "pub_only"})

        with self.assertRaises(PublishRecordValidationError):
            validate_publish_record(_base_record(status="unknown"))

    def test_writer_is_append_only_and_idempotent_by_publish_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "publish_records.jsonl"
            first = write_publish_record(_base_record(), path=path)
            second = write_publish_record(_base_record(), path=path)
            self.assertEqual(first["publish_id"], second["publish_id"])
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)

    def test_repo_lookup_by_job_and_video(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "publish_records.jsonl"
            write_publish_record(_base_record(publish_id="pub_001", video_id="vid_001"), path=path)
            write_publish_record(
                _base_record(
                    publish_id="pub_002",
                    job_id="job_002",
                    video_id="vid_002",
                    status="failed",
                ),
                path=path,
            )

            by_job = get_by_job("job_001", "acc_ca_001", "tiktok", path=path)
            by_video = get_by_video("vid_001", "acc_ca_001", "tiktok", path=path)
            missing = get_by_job("job_002", "acc_ca_001", "tiktok", path=path)

            self.assertIsNotNone(by_job)
            self.assertIsNotNone(by_video)
            self.assertEqual(by_job["publish_id"], "pub_001")
            self.assertEqual(by_video["publish_id"], "pub_001")
            self.assertIsNone(missing)

    def test_invariant_blocks_ambiguous_active_mapping(self) -> None:
        records = [
            _base_record(publish_id="pub_001", job_id="job_001", status="posted"),
            _base_record(
                publish_id="pub_002",
                job_id="job_001",
                video_id="vid_002",
                status="posted",
            ),
        ]
        with self.assertRaises(PublishRecordInvariantError):
            enforce_no_ambiguous_active_mapping(records)


if __name__ == "__main__":
    unittest.main()
