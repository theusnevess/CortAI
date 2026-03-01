from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = ROOT / "schemas" / "events"
EXAMPLES_DIR = ROOT / "examples" / "events"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_schema(name: str) -> dict:
    return _load_json(SCHEMAS_DIR / name)


def _load_example(name: str) -> dict:
    return _load_json(EXAMPLES_DIR / name)


def _payload_schema_name(example_name: str) -> str:
    return example_name


@pytest.mark.parametrize(
    "example_name",
    [
        "decision.created.v1.json",
        "webhook.delivery_attempted.v1.json",
        "webhook.delivery_failed.v1.json",
        "maestro.job_started.v1.json",
        "maestro.job_finished.v1.json",
    ],
)
def test_event_examples_validate_against_envelope_and_payload_schema(example_name: str) -> None:
    envelope = _load_example(example_name)
    envelope_schema = _load_schema("event_envelope.v1.schema.json")
    payload_schema = _load_schema(_payload_schema_name(example_name).replace(".json", ".schema.json"))

    jsonschema.validate(instance=envelope, schema=envelope_schema)
    jsonschema.validate(instance=envelope["payload"], schema=payload_schema)


def test_event_envelope_requires_event_id() -> None:
    envelope = _load_example("decision.created.v1.json")
    envelope.pop("event_id")
    envelope_schema = _load_schema("event_envelope.v1.schema.json")

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=envelope, schema=envelope_schema)


def test_maestro_job_finished_requires_status() -> None:
    envelope = _load_example("maestro.job_finished.v1.json")
    envelope["payload"].pop("status")
    payload_schema = _load_schema("maestro.job_finished.v1.schema.json")

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=envelope["payload"], schema=payload_schema)
