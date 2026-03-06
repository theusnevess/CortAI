from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MinioPath:
    """Representa um caminho logico no formato bucket/chave."""

    bucket: str
    key: str


def parse_minio_path(minio_path: str) -> MinioPath:
    """Converte um caminho logico MinIO no formato bucket/chave."""
    if not minio_path or "/" not in minio_path:
        raise ValueError(f"Invalid minio_path format: {minio_path!r}")

    bucket, key = minio_path.split("/", 1)
    bucket = bucket.strip()
    key = key.strip()

    if not bucket or not key:
        raise ValueError(f"Invalid minio_path format: {minio_path!r}")

    return MinioPath(bucket=bucket, key=key)
