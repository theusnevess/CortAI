from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import html
import re
from typing import Callable, Any

import httpx

from app.creative.agents.trend_analysis.models import TrendAnalysisInput, TrendCollectorResult, TrendSourceRecord
from app.creative.contracts.creative_pack import TrendEvidenceReference


SAFE_PRE_CROSSING_EXTERNAL_CALL_AUTHORIZED = False
SAFE_PRE_CROSSING_REQUEST_TRANSFORMATION_AUTHORIZED = False
SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED = False


def _ensure_external_collection_authorized() -> None:
    if not SAFE_PRE_CROSSING_EXTERNAL_CALL_AUTHORIZED:
        raise RuntimeError("CORTAI_EXTERNAL_BOUNDARY_BLOCKED_SAFE_PRE_CROSSING")
    if not SAFE_PRE_CROSSING_REQUEST_TRANSFORMATION_AUTHORIZED:
        raise RuntimeError("CORTAI_REQUEST_TRANSFORMATION_BLOCKED_SAFE_PRE_CROSSING")
    if not SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED:
        raise RuntimeError("CORTAI_TRANSPORT_PAYLOAD_BLOCKED_SAFE_PRE_CROSSING")


@dataclass
class TikTokCreativeCenterCollector:
    collector_version: str = "creative-center-public-v1"
    base_url: str = "https://ads.tiktok.com/business/creativecenter/pc/en"
    max_hashtags: int = 5
    max_songs: int = 5
    timeout_s: float = 20.0
    http_client_factory: Callable[..., Any] = field(default=httpx.Client)

    def collect(self, data: TrendAnalysisInput) -> TrendCollectorResult:
        _ensure_external_collection_authorized()
        current_time = self._now_iso()
        client = self.http_client_factory(
            timeout=self.timeout_s,
            follow_redirects=True,
            headers={"user-agent": "Mozilla/5.0 (compatible; CortAITrendCollector/2.0)"},
        )
        return TrendCollectorResult(
            source_record=self._collect_source_record(client=client, data=data, current_time=current_time),
            used_stub=False,
            trace=self._last_trace,
        )

    def _collect_source_record(
        self,
        *,
        client: Any,
        data: TrendAnalysisInput,
        current_time: str,
    ) -> TrendSourceRecord | None:
        self._last_trace = {
            "source": "creative_center",
            "collector_version": self.collector_version,
            "status": "COLLECTION_STARTED",
            "niche": data.niche,
            "region_requested": data.region,
            "base_url": self.base_url,
        }
        try:
            response = client.get(self.base_url)
            if int(getattr(response, "status_code", 0) or 0) != 200:
                self._last_trace["status"] = f"HTTP_ERROR_{getattr(response, 'status_code', 'UNKNOWN')}"
                return None
            lines = self._visible_lines(str(getattr(response, "text", "") or ""))
            hashtags, songs = self._extract_trend_discovery(lines)
            evidence = self._build_evidence(
                hashtags=hashtags,
                songs=songs,
                current_time=current_time,
                region=data.region,
            )
            self._last_trace["status"] = "COLLECTED"
            self._last_trace["hashtags_count"] = len(hashtags)
            self._last_trace["songs_count"] = len(songs)
            self._last_trace["region_effective"] = "unfiltered_public_surface"
            self._last_trace["region_filter_applied"] = False
            if not evidence:
                self._last_trace["status"] = "COLLECTED_NO_PARSEABLE_EVIDENCE"
                return None
            return TrendSourceRecord(
                source="creative_center",
                niche=(data.niche or "").strip().lower() or "default",
                region=str(data.region or "US"),
                collected_at=current_time,
                sample_size=len(evidence),
                dominant_hooks=[],
                avg_duration="",
                pacing="",
                visual_style="",
                text_style="",
                evidence=evidence,
                source_metadata={
                    "base_url": self.base_url,
                    "requested_region": data.region,
                    "region_effective": "unfiltered_public_surface",
                    "region_filter_applied": False,
                    "hashtags": hashtags,
                    "songs": songs,
                    "record_version": self.collector_version,
                },
            )
        except Exception as exc:  # noqa: BLE001
            self._last_trace["status"] = "COLLECTION_FAILED"
            self._last_trace["error"] = str(exc)
            return None
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

    def _build_evidence(
        self,
        *,
        hashtags: list[str],
        songs: list[dict[str, str]],
        current_time: str,
        region: str,
    ) -> list[TrendEvidenceReference]:
        evidence: list[TrendEvidenceReference] = []
        for index, tag in enumerate(hashtags, start=1):
            evidence.append(
                TrendEvidenceReference(
                    evidence_type="creative_center_hashtag",
                    source="creative_center",
                    reference_id=f"hashtag:{tag}",
                    reference_url=self.base_url,
                    captured_at=current_time,
                    region=region or "US",
                    metadata={"rank": index, "tag": tag},
                )
            )
        for index, song in enumerate(songs, start=1):
            evidence.append(
                TrendEvidenceReference(
                    evidence_type="creative_center_song",
                    source="creative_center",
                    reference_id=f"song:{song['title']}",
                    reference_url=self.base_url,
                    captured_at=current_time,
                    region=region or "US",
                    metadata={"rank": index, "title": song["title"], "artist": song["artist"]},
                )
            )
        return evidence

    def _extract_trend_discovery(self, lines: list[str]) -> tuple[list[str], list[dict[str, str]]]:
        hashtag_markers = [index for index, line in enumerate(lines) if line == "Hashtags"]
        songs_markers = [index for index, line in enumerate(lines) if line == "Songs"]
        creators_markers = [index for index, line in enumerate(lines) if line == "Creators"]
        if len(hashtag_markers) < 2 or len(songs_markers) < 2 or len(creators_markers) < 2:
            return [], []
        start = creators_markers[1] + 1
        hashtags: list[str] = []
        songs: list[dict[str, str]] = []
        index = start
        while index < len(lines) and len(hashtags) < self.max_hashtags:
            if lines[index] == "#" and index + 1 < len(lines):
                tag = lines[index + 1].strip().lstrip("#").strip()
                if tag:
                    hashtags.append(tag)
            index += 1
        while index < len(lines) and len(songs) < self.max_songs:
            line = lines[index]
            if line == "Connect via TikTok One":
                break
            if line.isdigit():
                probe = index + 1
                while probe < len(lines) and lines[probe].isdigit():
                    probe += 1
                if probe + 1 < len(lines):
                    title = lines[probe].strip()
                    artist = lines[probe + 1].strip()
                    if self._is_song_title(title=title) and self._is_song_artist(artist=artist):
                        songs.append({"title": title, "artist": artist})
                        while probe < len(lines) and lines[probe] != "See analytics":
                            probe += 1
                        index = probe
            index += 1
        return hashtags[: self.max_hashtags], songs[: self.max_songs]

    def _visible_lines(self, html_text: str) -> list[str]:
        plain = html.unescape(re.sub(r"<[^>]+>", "\n", html_text))
        lines = [re.sub(r"\s+", " ", line).strip() for line in plain.splitlines()]
        return [line for line in lines if line]

    def _is_song_title(self, *, title: str) -> bool:
        invalid = {"See analytics", "Posts", "Hashtags", "Songs", "Creators", "TikTok Videos", "No related creator"}
        return bool(title) and not title.startswith("#") and title not in invalid

    def _is_song_artist(self, artist: str) -> bool:
        invalid = {"See analytics", "Posts", "Approved for business use", "Connect via TikTok One"}
        return bool(artist) and artist not in invalid and not artist.isdigit()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
