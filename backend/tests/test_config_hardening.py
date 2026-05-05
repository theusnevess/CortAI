from __future__ import annotations

from pathlib import Path

import pytest

from app.config.runtime import (
    RuntimeConfigError,
    cursor_signing_policy_from_env,
    redact_config_value,
    require_async_database_url,
    require_database_url,
    require_worker_broker_url,
    runtime_database_config,
    runtime_worker_config,
)


@pytest.fixture(autouse=True)
def cleanup_metrics():
    yield


def test_missing_database_url_fails_closed_without_value_disclosure():
    with pytest.raises(RuntimeConfigError) as exc_info:
        require_database_url(env={})

    message = str(exc_info.value)
    assert "DATABASE_URL" in message
    assert "postgresql://" not in message
    assert "password" not in message.lower()
    assert "secret" not in message.lower()


def test_runtime_config_repr_redacts_values():
    database_config = runtime_database_config(
        env={"DATABASE_URL": "postgresql://user:non-secret-test-password@localhost:5432/testdb"}
    )
    worker_config = runtime_worker_config(env={"REDIS_URL": "redis://localhost:6379/9"})

    assert database_config.database_url.startswith("postgresql://")
    assert "non-secret-test-password" not in repr(database_config)
    assert "<redacted>" in repr(database_config)
    assert "redis://localhost" not in repr(worker_config)
    assert redact_config_value(database_config.database_url) == "<redacted>"


def test_async_database_url_conversion_requires_explicit_config():
    assert (
        require_async_database_url(env={"DATABASE_URL": "postgresql://user:pass@example.invalid:5432/testdb"})
        == "postgresql+asyncpg://user:pass@example.invalid:5432/testdb"
    )


def test_missing_worker_broker_url_fails_closed_without_value_disclosure():
    with pytest.raises(RuntimeConfigError) as exc_info:
        require_worker_broker_url(env={})

    message = str(exc_info.value)
    assert "REDIS_URL" in message
    assert "redis://" not in message
    assert "localhost" not in message


def test_cursor_signing_requires_secret_when_enforcement_enabled():
    with pytest.raises(RuntimeConfigError) as exc_info:
        cursor_signing_policy_from_env(env={"CURSOR_SIGNATURE_ENFORCEMENT": "1"})

    assert "CURSOR_SIGNATURE_SECRET" in str(exc_info.value)
    assert "dev-secret" not in str(exc_info.value)


def test_cursor_signing_disabled_has_no_dev_secret_default():
    policy = cursor_signing_policy_from_env(env={})

    assert policy.enabled is False
    assert policy.secret == b""


def test_authorized_source_files_do_not_contain_credential_bearing_fallbacks():
    repo_root = Path(__file__).resolve().parents[2]
    source_files = [
        "backend/app/db/session.py",
        "backend/alembic/env.py",
        "backend/app/cognitive_runs.py",
        "backend/app/cognitive_metrics.py",
        "backend/app/observations.py",
        "backend/app/publish_receipts.py",
        "backend/app/agents/collector/observability.py",
        "backend/app/worker.py",
        "backend/app/tasks/collector_tasks.py",
        "backend/app/observability/event_query/query_service.py",
    ]
    forbidden_fragments = [
        "postgresql://cortai_admin",
        "cortai_secret_pass",
        "redis://localhost:6379/0",
        "dev-secret",
    ]

    for relative_path in source_files:
        text = (repo_root / relative_path).read_text(encoding="utf-8")
        for fragment in forbidden_fragments:
            assert fragment not in text, f"{fragment!r} found in {relative_path}"
