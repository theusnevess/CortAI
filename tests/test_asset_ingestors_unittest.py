from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.assets.pexels_ingestor import PexelsIngestor
from app.assets.unsplash_ingestor import UnsplashIngestor
from app.assets.pixabay_ingestor import PixabayIngestor


def _image_bytes() -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
        path = Path(handle.name)
    try:
        image = Image.new("RGB", (1600, 2400), color=(128, 128, 128))
        image.save(path, format="JPEG")
        return path.read_bytes()
    finally:
        path.unlink(missing_ok=True)


class AssetIngestorTests(unittest.TestCase):
    def test_pexels_ingest_query_registers_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            imports_root = Path(tmp_dir) / "imports"
            with patch.object(PexelsIngestor, "search", return_value=[{"src": {"original": "https://images.example/test.jpg"}}]), patch(
                "app.assets.pexels_ingestor.download_bytes",
                return_value=_image_bytes(),
            ), patch(
                "app.assets.ingestion_common.upsert_catalog_entries",
                return_value=[],
            ):
                ingestor = PexelsIngestor(api_key="test-key", imports_root=imports_root)
                rows = ingestor.ingest_query(
                    query="abandoned corridor",
                    category="corridor",
                    subtype="institutional",
                    tags=["corridor", "institutional"],
                    limit=1,
                )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_type"], "pexels")
        self.assertEqual(rows[0]["category"], "corridor")

    def test_unsplash_requires_key_for_search(self) -> None:
        ingestor = UnsplashIngestor(access_key="")
        with self.assertRaisesRegex(RuntimeError, "UNSPLASH_ACCESS_KEY"):
            ingestor.search(query="archive shelves")

    def test_pixabay_ingest_query_registers_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            imports_root = Path(tmp_dir) / "imports"
            with patch.object(PixabayIngestor, "search", return_value=[{"largeImageURL": "https://images.example/test.jpg"}]), patch(
                "app.assets.pixabay_ingestor.download_bytes",
                return_value=_image_bytes(),
            ), patch(
                "app.assets.ingestion_common.upsert_catalog_entries",
                return_value=[],
            ):
                ingestor = PixabayIngestor(api_key="test-key", imports_root=imports_root)
                rows = ingestor.ingest_query(
                    query="intercom panel",
                    category="warning_display",
                    subtype="panel",
                    tags=["warning", "device"],
                    limit=1,
                )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_type"], "pixabay")
        self.assertEqual(rows[0]["category"], "warning_display")


if __name__ == "__main__":
    unittest.main()
