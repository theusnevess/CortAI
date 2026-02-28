from __future__ import annotations

import pytest

from app.agents.collector.utils import MinioPath, parse_minio_path


def test_parse_minio_path_returns_bucket_and_key():
    result = parse_minio_path("videos-raw/path/to/file.wav")

    assert result == MinioPath(bucket="videos-raw", key="path/to/file.wav")


@pytest.mark.parametrize("value", ["", "videos-raw", "/file.wav", "videos-raw/"])
def test_parse_minio_path_rejects_invalid_values(value: str):
    with pytest.raises(ValueError):
        parse_minio_path(value)
