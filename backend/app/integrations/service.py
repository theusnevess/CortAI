from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.data.publish_records.writer import write_publish_record
from app.data.video_metrics.writer import write_video_metrics
from app.integrations.models import IntegrationSyncResult
from app.observability.event_append.service import append_event, build_event_record


EventSink = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class ProviderIntegrationDeps:
    """Dependências de integração externa do D22."""

    client: Any
    adapter: Any
    event_sink: EventSink | None = None
    publish_record_writer: Callable[..., dict[str, Any]] = write_publish_record
    video_metrics_writer: Callable[..., dict[str, Any]] = write_video_metrics


class ExternalPlatformIntegrationService:
    """Orquestra provider, adapter e persistência interna normalizada."""

    def __init__(self, deps: ProviderIntegrationDeps) -> None:
        self.deps = deps

    def ingest_video_metrics(
        self,
        *,
        account_id: str,
        external_video_id: str,
        captured_window_id: str,
    ) -> IntegrationSyncResult:
        raw = self.deps.client.fetch_video_metrics(
            external_video_id=external_video_id,
            captured_window_id=captured_window_id,
        )
        normalized = self.deps.adapter.normalize_video_metrics(
            raw_payload=raw,
            account_id=account_id,
            captured_window_id=captured_window_id,
        )
        persisted = self.deps.video_metrics_writer(normalized.record)
        self._emit_provider_event(
            entity="video_metrics",
            account_id=account_id,
            external_id=external_video_id,
            raw=raw,
            result="WRITTEN",
        )
        return IntegrationSyncResult(
            status="WRITTEN",
            provider=str(raw.get("provider") or "tiktok"),
            entity="video_metrics",
            record=persisted,
            retry_count=int(raw.get("retry_count", 0) or 0),
            latency_ms=float(raw.get("latency_ms", 0.0) or 0.0),
        )

    def ingest_publish_record(
        self,
        *,
        account_id: str,
        external_post_id: str,
    ) -> IntegrationSyncResult:
        raw = self.deps.client.fetch_publish_record(external_post_id=external_post_id)
        normalized = self.deps.adapter.normalize_publish_record(
            raw_payload=raw,
            account_id=account_id,
        )
        persisted = self.deps.publish_record_writer(normalized.record)
        self._emit_provider_event(
            entity="publish_record",
            account_id=account_id,
            external_id=external_post_id,
            raw=raw,
            result="WRITTEN",
        )
        return IntegrationSyncResult(
            status="WRITTEN",
            provider=str(raw.get("provider") or "tiktok"),
            entity="publish_record",
            record=persisted,
            retry_count=int(raw.get("retry_count", 0) or 0),
            latency_ms=float(raw.get("latency_ms", 0.0) or 0.0),
        )

    def _emit_provider_event(
        self,
        *,
        entity: str,
        account_id: str,
        external_id: str,
        raw: dict[str, Any],
        result: str,
    ) -> None:
        payload = {
            "event_id": str(raw.get("request_id") or f"{entity}:{external_id}"),
            "timestamp": _event_ts(raw),
            "account_id": account_id,
            "event_type": "INTEGRATION/provider_call",
            "severity": "INFO",
            "action_taken": "OBSERVE",
            "provider": str(raw.get("provider") or "tiktok"),
            "endpoint": str(raw.get("endpoint") or entity),
            "request_id": raw.get("request_id"),
            "external_id": external_id,
            "latency_ms": raw.get("latency_ms"),
            "retry_count": raw.get("retry_count"),
            "result": result,
        }
        event = build_event_record("INTEGRATION/provider_call", payload, writer_id="integration_service")
        sink = self.deps.event_sink
        if sink is not None:
            sink(event)
            return
        append_event(event)


def _event_ts(raw: dict[str, Any]) -> str:
    payload = raw.get("payload")
    if isinstance(payload, dict):
        captured_at = payload.get("captured_at") or payload.get("published_at")
        if isinstance(captured_at, str) and captured_at:
            return captured_at
    return "2026-03-06T00:00:00Z"
