from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass

from app.observability.event_query.errors import TraceRequestInvalidError
from app.observability.event_query.models import (
    EventQueryFilters,
    EventRecord,
    PipelineTrace,
    TraceRequest,
    TraceSummary,
)
from app.observability.event_query.query_service import EventQueryService


_OPERATIONAL_FAMILIES = {"LOCK", "IDEMPOTENCY", "GUARD", "METRICS", "PUB", "SC", "ATTR", "REG", "PIPE"}
_ERROR_SEVERITIES = {"ERROR", "CRITICAL"}
_SUCCESS_EVENT_TYPES = {
    "SC/generated",
    "ATTR/written",
    "SL/patch_written",
    "SL/strategy_patch_written",
    "PIPE/D10_FINISHED",
}


@dataclass(frozen=True)
class TraceBuilder:
    """Monta trilha de pipeline de forma deterministica para debug forense."""

    query_service: EventQueryService

    def build_trace(self, request: TraceRequest, *, limit: int = 500) -> PipelineTrace:
        """Constroi timeline e resumo final a partir dos eventos filtrados."""
        self._validate_request(request)
        start_ts = request.start_ts or "1970-01-01T00:00:00Z"
        end_ts = request.end_ts or "2100-01-01T00:00:00Z"

        query_result = self.query_service.get_events(
            EventQueryFilters(
                start_ts=start_ts,
                end_ts=end_ts,
                account_id=request.account_id,
                window_id=request.window_id,
                job_id=request.job_id,
                publish_id=request.publish_id,
            ),
            limit=limit,
        )

        timeline = sorted(query_result.items, key=lambda ev: (ev.ts, ev.event_id or ""))
        summary = self._build_summary(timeline)
        stats = self._build_stats(timeline)
        trace_id = self._build_trace_id(request, start_ts=start_ts, end_ts=end_ts)

        return PipelineTrace(
            trace_id=trace_id,
            account_id=request.account_id,
            job_id=request.job_id,
            publish_id=request.publish_id,
            window_id=request.window_id,
            time_range={"start_ts": start_ts, "end_ts": end_ts},
            timeline=timeline,
            summary=summary,
            stats=stats,
        )

    def _validate_request(self, request: TraceRequest) -> None:
        if not (request.job_id or request.publish_id or request.window_id):
            raise TraceRequestInvalidError()

    def _build_trace_id(self, request: TraceRequest, *, start_ts: str, end_ts: str) -> str:
        seed = "|".join(
            [
                request.account_id or "",
                request.job_id or "",
                request.publish_id or "",
                request.window_id or "",
                start_ts,
                end_ts,
            ]
        )
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]

    def _build_summary(self, timeline: list[EventRecord]) -> TraceSummary:
        if not timeline:
            return TraceSummary(final_status="UNKNOWN", last_event_id=None)

        dominant_family = self._dominant_family(timeline)
        dominant_reason_code = None
        first_failure_event_id = None

        root_cause = self._root_cause_candidate(timeline)
        if root_cause is not None:
            dominant_reason_code = _reason_code(root_cause)

        final_status = "UNKNOWN"
        for event in timeline:
            family = _family(event.event_type)
            action = (event.action_taken or "").upper()
            severity = (event.severity or "").upper()
            if action == "BLOCK" or family in {"LOCK", "GUARD", "CONSISTENCY"} and action == "BLOCK":
                final_status = "BLOCKED"
                first_failure_event_id = event.event_id or None
                break
            if severity in _ERROR_SEVERITIES and action != "OBSERVE":
                final_status = "FAILED"
                first_failure_event_id = event.event_id or None
                break

        if final_status == "UNKNOWN":
            success_found = any(event.event_type in _SUCCESS_EVENT_TYPES for event in timeline)
            if success_found:
                final_status = "OK"

        return TraceSummary(
            final_status=final_status,
            dominant_family=dominant_family,
            dominant_reason_code=dominant_reason_code,
            first_failure_event_id=first_failure_event_id,
            last_event_id=timeline[-1].event_id or None,
        )

    def _root_cause_candidate(self, timeline: list[EventRecord]) -> EventRecord | None:
        for event in timeline:
            reason = _reason_code(event)
            if reason and _family(event.event_type) in _OPERATIONAL_FAMILIES:
                return event
        for event in timeline:
            severity = (event.severity or "").upper()
            if severity in _ERROR_SEVERITIES:
                return event
        return None

    def _dominant_family(self, timeline: list[EventRecord]) -> str | None:
        families = [_family(event.event_type) for event in timeline if _family(event.event_type)]
        if not families:
            return None
        counts = Counter(families)
        return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def _build_stats(self, timeline: list[EventRecord]) -> dict[str, dict[str, int]]:
        by_family: Counter[str] = Counter()
        by_severity: Counter[str] = Counter()
        by_action: Counter[str] = Counter()

        for event in timeline:
            family = _family(event.event_type)
            if family:
                by_family[family] += 1
            if event.severity:
                by_severity[event.severity.upper()] += 1
            if event.action_taken:
                by_action[event.action_taken.upper()] += 1

        return {
            "family": dict(sorted(by_family.items())),
            "severity": dict(sorted(by_severity.items())),
            "action": dict(sorted(by_action.items())),
        }


def _family(event_type: str | None) -> str:
    if not event_type:
        return ""
    return event_type.split("/", 1)[0].upper()


def _reason_code(event: EventRecord) -> str | None:
    if not isinstance(event.details, dict):
        return None
    value = event.details.get("reason_code")
    if isinstance(value, str) and value.strip():
        return value
    return None
