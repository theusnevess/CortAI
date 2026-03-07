from __future__ import annotations

from hashlib import sha256


def assign_variant(*, experiment_id: str, subject_key: str) -> str:
    material = f"{experiment_id}|{subject_key}".encode("utf-8")
    digest = sha256(material).hexdigest()
    return "A" if int(digest[-2:], 16) % 2 == 0 else "B"
