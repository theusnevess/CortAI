from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from app.observability.event_query.cursor_signing import SigningPolicy


REDACTED_CONFIG_VALUE = "<redacted>"


class RuntimeConfigError(RuntimeError):
    """Fail-closed configuration error that never includes secret values."""

    def __init__(self, env_name: str, *, reason: str = "required") -> None:
        self.env_name = env_name
        self.reason = reason
        super().__init__(f"Required runtime configuration is missing: {env_name}")

    def __repr__(self) -> str:
        return f"RuntimeConfigError(env_name={self.env_name!r}, reason={self.reason!r})"


@dataclass(frozen=True)
class RuntimeDatabaseConfig:
    database_url: str

    def __repr__(self) -> str:
        return f"RuntimeDatabaseConfig(database_url={REDACTED_CONFIG_VALUE!r})"


@dataclass(frozen=True)
class RuntimeWorkerConfig:
    broker_url: str

    def __repr__(self) -> str:
        return f"RuntimeWorkerConfig(broker_url={REDACTED_CONFIG_VALUE!r})"


def _env_value(env_name: str, env: Mapping[str, str] | None) -> str | None:
    source = os.environ if env is None else env
    value = source.get(env_name)
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def require_env_var(env_name: str, *, env: Mapping[str, str] | None = None) -> str:
    value = _env_value(env_name, env)
    if value is None:
        raise RuntimeConfigError(env_name)
    return value


def env_flag_enabled(
    env_name: str,
    *,
    default: bool = False,
    env: Mapping[str, str] | None = None,
) -> bool:
    value = _env_value(env_name, env)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def redact_config_value(value: object) -> str:
    return REDACTED_CONFIG_VALUE if value is not None else ""


def require_database_url(*, env: Mapping[str, str] | None = None) -> str:
    return require_env_var("DATABASE_URL", env=env)


def require_async_database_url(*, env: Mapping[str, str] | None = None) -> str:
    database_url = require_database_url(env=env)
    return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)


def require_worker_broker_url(*, env: Mapping[str, str] | None = None) -> str:
    return require_env_var("REDIS_URL", env=env)


def runtime_database_config(*, env: Mapping[str, str] | None = None) -> RuntimeDatabaseConfig:
    return RuntimeDatabaseConfig(database_url=require_database_url(env=env))


def runtime_worker_config(*, env: Mapping[str, str] | None = None) -> RuntimeWorkerConfig:
    return RuntimeWorkerConfig(broker_url=require_worker_broker_url(env=env))


def cursor_signing_policy_from_env(
    *,
    env: Mapping[str, str] | None = None,
) -> SigningPolicy:
    enforcement = env_flag_enabled("CURSOR_SIGNATURE_ENFORCEMENT", env=env)
    if not enforcement:
        return SigningPolicy(enabled=False, secret=b"")
    secret = require_env_var("CURSOR_SIGNATURE_SECRET", env=env)
    return SigningPolicy(enabled=True, secret=secret.encode("utf-8"))
