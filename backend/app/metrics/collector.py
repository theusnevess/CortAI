from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable

from app.data.publish_records.store_jsonl import read_all_records as read_publish_records
from app.metrics.models import VideoMetricsRecord
from app.metrics.provider_adapter import (
    MetricsProviderClient,
    MetricsProviderRateLimit,
    MetricsProviderTimeout,
    MetricsProviderUnavailable,
    StubMetricsProviderAdapter,
)
from app.metrics.repo import save_if_absent
from app.metrics.store_jsonl import DEFAULT_METRICS_PATH
from app.observability.event_append.service import append_event, build_event_record


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _to_iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _bucket_hour(ts: datetime) -> str:
    return ts.replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def _metrics_id(*, publish_id: str, bucket: str) -> str:
    material = f"{publish_id}|{bucket}".encode("utf-8")
    return f"vmc_{sha256(material).hexdigest()[:16]}"


EventEmitter = Callable[[str, dict[str, Any]], None]


@dataclass
class MetricsCollectorService:
    provider: MetricsProviderClient = StubMetricsProviderAdapter()
    metrics_path: Path = DEFAULT_METRICS_PATH
    publish_records_path: Path = Path("OUT/data/publish_records/publish_records.jsonl")
    event_path: Path = Path("OUT/events/events.jsonl")
    max_attempts: int = 3

    def collect_for_publish(self, *, publish_id: str, collected_at: str | None = None) -> dict[str, Any]:
        now = _parse_iso(collected_at) if collected_at else _now()
        publish = self._find_publish(publish_id)
        if publish is None:
            raise ValueError("PUBLISH_RECORD_NOT_FOUND")

        account_id = str(publish.get("account_id") or "")
        video_id = str(publish.get("video_id") or "")
        provider_name = str(publish.get("platform") or "")
        bucket = _bucket_hour(now)
        self._emit("METRICS/collection_started", {"publish_id": publish_id, "account_id": account_id, "video_id": video_id, "bucket": bucket})

        try:
            payload, attempts = self._retry_fetch(publish_id=publish_id, video_id=video_id, account_id=account_id)
        except MetricsProviderRateLimit as exc:
            self._emit("METRICS/api_rate_limited", {"publish_id": publish_id, "account_id": account_id, "video_id": video_id, "error": str(exc)})
            self._emit("METRICS/collection_failed", {"publish_id": publish_id, "account_id": account_id, "video_id": video_id, "error": str(exc)})
            raise
        except (MetricsProviderTimeout, MetricsProviderUnavailable) as exc:
            self._emit("METRICS/collection_failed", {"publish_id": publish_id, "account_id": account_id, "video_id": video_id, "error": str(exc)})
            raise

        published_at = _parse_iso(str(publish.get("published_at") or publish.get("created_at") or _to_iso(now)))
        age_hours = round(max((now - published_at).total_seconds() / 3600.0, 0.0), 2)
        record = VideoMetricsRecord(
            metrics_id=_metrics_id(publish_id=publish_id, bucket=bucket),
            publish_id=publish_id,
            account_id=account_id,
            video_id=video_id,
            views=int(payload.get("views") or 0),
            likes=int(payload.get("likes") or 0),
            comments=int(payload.get("comments") or 0),
            shares=int(payload.get("shares") or 0),
            watch_time_total=float(payload.get("watch_time_total") or 0.0),
            avg_watch_time=float(payload.get("avg_watch_time") or 0.0),
            completion_rate=float(payload.get("completion_rate") or 0.0),
            view_3s_rate=float(payload.get("view_3s_rate") or 0.0),
            view_5s_rate=float(payload.get("view_5s_rate") or 0.0),
            collected_at=_to_iso(now),
            collected_at_bucket=bucket,
            age_hours=age_hours,
            provider=provider_name,
        )
        action = save_if_absent(record.to_dict(), path=self.metrics_path)
        self._emit(
            "METRICS/collection_completed",
            {
                "publish_id": publish_id,
                "account_id": account_id,
                "video_id": video_id,
                "bucket": bucket,
                "action": action,
                "attempts": attempts,
            },
        )
        return {"status": action, "record": record.to_dict()}

    def _retry_fetch(self, *, publish_id: str, video_id: str, account_id: str) -> tuple[dict[str, Any], int]:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return (
                    self.provider.fetch_video_metrics(
                        publish_id=publish_id,
                        video_id=video_id,
                        account_id=account_id,
                    ),
                    attempt,
                )
            except (MetricsProviderTimeout, MetricsProviderRateLimit, MetricsProviderUnavailable) as exc:
                last_exc = exc
                if attempt >= self.max_attempts:
                    raise
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("UNREACHABLE_METRICS_RETRY")

    def _find_publish(self, publish_id: str) -> dict[str, Any] | None:
        for row in read_publish_records(self.publish_records_path):
            if row.get("publish_id") == publish_id:
                return row
        return None

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        event = build_event_record(event_type, payload, writer_id="metrics_collector")
        append_event(event, path=self.event_path)
