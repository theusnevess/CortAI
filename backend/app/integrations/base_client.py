from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter, sleep
from typing import Any, Callable

from app.integrations.models import ProviderCallResult


class ProviderIntegrationError(RuntimeError):
    """Erro base para a camada de provider externo."""


class ProviderTimeoutError(ProviderIntegrationError):
    """Timeout ou indisponibilidade transitória."""


class ProviderRateLimitError(ProviderIntegrationError):
    """Rate limit retornado pelo provider."""


class ProviderAuthFailedError(ProviderIntegrationError):
    """Credencial inválida ou expirada."""


class ProviderInvalidPayloadError(ProviderIntegrationError):
    """Payload externo inválido ou fora do contrato do adapter."""


class ProviderUnavailableError(ProviderIntegrationError):
    """5xx transitório do provider."""


Transport = Callable[[str, dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class RetryPolicy:
    """Política simples de retry para providers externos."""

    max_attempts: int = 3
    base_backoff_s: float = 0.05


class BasePlatformClient:
    """Cliente base com retry e taxonomia de erro externa."""

    def __init__(
        self,
        *,
        provider_name: str,
        transport: Transport,
        retry_policy: RetryPolicy | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.transport = transport
        self.retry_policy = retry_policy or RetryPolicy()
        self.sleep_fn = sleep_fn or sleep

    def execute(self, endpoint: str, payload: dict[str, Any]) -> ProviderCallResult:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            started = perf_counter()
            try:
                raw = self.transport(endpoint, payload)
                latency_ms = round((perf_counter() - started) * 1000, 3)
                status_code = int(raw.get("status_code", 200))
                if status_code == 429:
                    raise ProviderRateLimitError("PROVIDER_RATE_LIMIT")
                if status_code in {401, 403}:
                    raise ProviderAuthFailedError("PROVIDER_AUTH_FAILED")
                if 500 <= status_code <= 599:
                    raise ProviderUnavailableError("PROVIDER_UNAVAILABLE")
                if status_code >= 400:
                    raise ProviderInvalidPayloadError("PROVIDER_INVALID_PAYLOAD")
                return ProviderCallResult(
                    provider=self.provider_name,
                    endpoint=endpoint,
                    payload=raw,
                    latency_ms=latency_ms,
                    retry_count=attempt - 1,
                    external_id=str(raw.get("external_video_id") or raw.get("external_post_id") or ""),
                    request_id=str(raw.get("request_id") or ""),
                )
            except TimeoutError as exc:
                last_error = ProviderTimeoutError("PROVIDER_TIMEOUT")
            except (ProviderRateLimitError, ProviderUnavailableError) as exc:
                last_error = exc
            except (ProviderAuthFailedError, ProviderInvalidPayloadError):
                raise

            if attempt >= self.retry_policy.max_attempts:
                assert last_error is not None
                raise last_error
            self.sleep_fn(self.retry_policy.base_backoff_s * (2 ** (attempt - 1)))
        raise ProviderUnavailableError("PROVIDER_UNAVAILABLE")
