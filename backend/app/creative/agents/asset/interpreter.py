from __future__ import annotations

from dataclasses import dataclass
import re

from app.creative.contracts.creative_pack import (
    AssetBackgroundPlan,
    AssetDecisionContract,
    AssetPlan,
    AssetRuntimeConstraints,
    AssetSegmentPlan,
    ScriptPlan,
    TrendProfile,
    VisualQuery,
)


def _normalize(value: str) -> str:
    text = value.upper()
    text = re.sub(r"[^A-Z0-9\\s]", " ", text)
    text = re.sub(r"\\s+", " ", text).strip()
    return f" {text} "


def _topic_tokens(value: str) -> list[str]:
    normalized = _normalize(value).strip().split()
    ranked = [
        token.lower()
        for token in normalized
        if len(token) >= 4 and token not in {"WHAT", "WITH", "FROM", "THEY", "THIS", "THAT", "ROOM", "VOICE"}
    ]
    seen: set[str] = set()
    deduped: list[str] = []
    for token in ranked:
        if token in seen:
            continue
        seen.add(token)
        deduped.append(token)
    return deduped[:6]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


@dataclass
class AssetInterpreterService:
    def build_plan(
        self,
        *,
        niche: str,
        topic: str,
        script_plan: ScriptPlan,
        trend_profile: TrendProfile,
        deterministic_seed: str,
    ) -> AssetPlan:
        hook_type = self._hook_type(topic=topic, hook_text=script_plan.hook)
        visual_anchor = self._visual_anchor(topic=topic, hook_text=script_plan.hook, hook_type=hook_type)
        semantic_pattern = self._semantic_pattern(topic=topic, script_plan=script_plan)
        entity = self._entity(topic=topic, script_plan=script_plan)
        topic_tags = _topic_tokens(f"{topic} {script_plan.hook} {script_plan.setup} {script_plan.payoff}")
        hook_event = self._segment_event_profile(
            segment="hook",
            topic=topic,
            segment_text=script_plan.hook,
            visual_anchor=visual_anchor,
            semantic_pattern=semantic_pattern,
            entity=entity,
        )
        setup_event = self._segment_event_profile(
            segment="setup",
            topic=topic,
            segment_text=script_plan.setup,
            visual_anchor=visual_anchor,
            semantic_pattern=semantic_pattern,
            entity=entity,
        )
        payoff_event = self._segment_event_profile(
            segment="payoff",
            topic=topic,
            segment_text=script_plan.payoff,
            visual_anchor=visual_anchor,
            semantic_pattern=semantic_pattern,
            entity=entity,
        )
        visual_world = self._visual_world_profile(
            niche=niche,
            topic=topic,
            visual_anchor=visual_anchor,
            semantic_pattern=semantic_pattern,
            entity=entity,
            topic_tags=topic_tags,
            event_profiles={
                "hook": hook_event,
                "setup": setup_event,
                "payoff": payoff_event,
            },
        )
        case_visual_pack = self._case_visual_pack_profile(
            topic=topic,
            visual_anchor=visual_anchor,
            semantic_pattern=semantic_pattern,
            entity=entity,
            topic_tags=topic_tags,
            event_profiles={
                "hook": hook_event,
                "setup": setup_event,
                "payoff": payoff_event,
            },
        )
        hook_category = self._segment_category(
            segment="hook",
            visual_anchor=visual_anchor,
            semantic_pattern=semantic_pattern,
            entity=entity,
            topic=topic,
            segment_text=script_plan.hook,
        )
        setup_category = self._segment_category(
            segment="setup",
            visual_anchor=visual_anchor,
            semantic_pattern=semantic_pattern,
            entity=entity,
            topic=topic,
            segment_text=script_plan.setup,
        )
        payoff_category = self._segment_category(
            segment="payoff",
            visual_anchor=visual_anchor,
            semantic_pattern=semantic_pattern,
            entity=entity,
            topic=topic,
            segment_text=script_plan.payoff,
        )
        hook_query = self._visual_query(
            segment="hook",
            topic=topic,
            segment_text=script_plan.hook,
            category=hook_category,
            visual_anchor=visual_anchor,
            entity=entity,
            semantic_pattern=semantic_pattern,
            event_profile=hook_event,
            visual_world=visual_world,
            case_visual_pack=case_visual_pack,
        )
        setup_query = self._visual_query(
            segment="setup",
            topic=topic,
            segment_text=script_plan.setup,
            category=setup_category,
            visual_anchor=visual_anchor,
            entity=entity,
            semantic_pattern=semantic_pattern,
            event_profile=setup_event,
            visual_world=visual_world,
            case_visual_pack=case_visual_pack,
        )
        payoff_query = self._visual_query(
            segment="payoff",
            topic=topic,
            segment_text=script_plan.payoff,
            category=payoff_category,
            visual_anchor=visual_anchor,
            entity=entity,
            semantic_pattern=semantic_pattern,
            event_profile=payoff_event,
            visual_world=visual_world,
            case_visual_pack=case_visual_pack,
        )
        segments = {
            "hook": AssetSegmentPlan(
                background=AssetBackgroundPlan(
                    source=self._background_source(
                        segment="hook",
                        event_profile=hook_event,
                    ),
                ),
                category=hook_category,
                tags=self._segment_tags(
                    segment="hook",
                    niche=niche,
                    visual_anchor=visual_anchor,
                    semantic_pattern=semantic_pattern,
                    entity=entity,
                    trend_profile=trend_profile,
                    topic_tags=topic_tags,
                    event_profile=hook_event,
                    visual_world=visual_world,
                    case_visual_pack=case_visual_pack,
                ),
                effects=self._segment_effects(segment="hook", trend_profile=trend_profile),
                decision_contract=self._decision_contract(
                    segment="hook",
                    category=hook_category,
                    event_profile=hook_event,
                ),
                visual_query=hook_query,
            ),
            "setup": AssetSegmentPlan(
                background=AssetBackgroundPlan(
                    source=self._background_source(
                        segment="setup",
                        event_profile=setup_event,
                    ),
                ),
                category=setup_category,
                tags=self._segment_tags(
                    segment="setup",
                    niche=niche,
                    visual_anchor=visual_anchor,
                    semantic_pattern=semantic_pattern,
                    entity=entity,
                    trend_profile=trend_profile,
                    topic_tags=topic_tags,
                    event_profile=setup_event,
                    visual_world=visual_world,
                    case_visual_pack=case_visual_pack,
                ),
                effects=self._segment_effects(segment="setup", trend_profile=trend_profile),
                decision_contract=self._decision_contract(
                    segment="setup",
                    category=setup_category,
                    event_profile=setup_event,
                ),
                visual_query=setup_query,
            ),
            "payoff": AssetSegmentPlan(
                background=AssetBackgroundPlan(
                    source=self._background_source(
                        segment="payoff",
                        event_profile=payoff_event,
                    ),
                ),
                category=payoff_category,
                tags=self._segment_tags(
                    segment="payoff",
                    niche=niche,
                    visual_anchor=visual_anchor,
                    semantic_pattern=semantic_pattern,
                    entity=entity,
                    trend_profile=trend_profile,
                    topic_tags=topic_tags,
                    event_profile=payoff_event,
                    visual_world=visual_world,
                    case_visual_pack=case_visual_pack,
                ),
                effects=self._segment_effects(segment="payoff", trend_profile=trend_profile),
                decision_contract=self._decision_contract(
                    segment="payoff",
                    category=payoff_category,
                    event_profile=payoff_event,
                ),
                visual_query=payoff_query,
            ),
        }
        return AssetPlan(
            visual_style=trend_profile.visual_style or "phase1_baseline",
            motion_profile="subtle_push_in" if trend_profile.pacing == "fast_first_3s" else "phase1_baseline",
            visual_anchor=visual_anchor,
            semantic_pattern=semantic_pattern,
            entity=entity,
            case_visual_pack=case_visual_pack,
            segments=segments,
            runtime_constraints=AssetRuntimeConstraints(
                allow_safe_fallback=True,
                allow_comfyui_generation_fallback=True,
                allow_comfyui_edit=False,
                deterministic_seed=deterministic_seed,
            ),
        )

    def _hook_type(self, *, topic: str, hook_text: str) -> str:
        text = _normalize(f"{topic} {hook_text}")
        experiential = (
            " CAMERA ",
            " BLACKOUT ",
            " DOOR ",
            " WARNING ",
            " SIGNAL ",
            " VOICE ",
            " INTERCOM ",
            " ROOM ",
            " WING ",
            " CORRIDOR ",
            " MAP ",
            " BLUEPRINT ",
            " LOCKER ",
        )
        inferential = (
            " TRANSCRIPT ",
            " RECORD ",
            " FILE ",
            " ARCHIVE ",
            " LOG ",
            " STATEMENT ",
            " DATE ",
            " TIMESTAMP ",
            " EVIDENCE ",
        )
        if any(token in text for token in experiential):
            return "experiential"
        if any(token in text for token in inferential):
            return "inferential"
        return "experiential"

    def _visual_anchor(self, *, topic: str, hook_text: str, hook_type: str) -> str:
        text = _normalize(f"{topic} {hook_text}")
        if hook_type == "inferential":
            if any(token in text for token in (" TRANSCRIPT ", " AUDIO ")):
                return "document"
            if any(token in text for token in (" DATE ", " TIMESTAMP ", " ARCHIVE ", " RECORD ", " LOG ", " FILE ")):
                return "document"
            return "document"
        if any(token in text for token in (" DOOR ", " LOCKER ", " SEALED ", " ROOM ", " WING ")):
            if not any(token in text for token in (" INTERCOM ", " WARNING ", " SIGNAL ", " CAMERA ", " DISPLAY ")):
                return "door"
        if any(token in text for token in (" CAMERA ", " DISPLAY ", " SCREEN ", " SIGNAL ")):
            return "device"
        if any(token in text for token in (" INTERCOM ", " RECORDER ", " SPEAKER ", " RADIO ")):
            return "device"
        if any(token in text for token in (" STATION ", " TUNNEL ", " CORRIDOR ", " PLATFORM ", " STAIRWELL ")):
            return "corridor"
        if any(token in text for token in (" MAP ", " BLUEPRINT ", " CORRIDOR ")):
            return "document"
        return "room"

    def _semantic_pattern(self, *, topic: str, script_plan: ScriptPlan) -> str:
        text = _normalize(f"{topic} {script_plan.hook} {script_plan.setup} {script_plan.payoff}")
        patterns = (
            ("glitch", (" GLITCH ", " BLACKOUT ", " DESYNC ", " FAILED ")),
            ("sealed", (" SEALED ", " LOCKED ", " SHUTTERED ")),
            ("missing", (" MISSING ", " TORN ")),
            ("warning", (" WARNING ", " DO NOT PLAY ")),
            ("contradiction", (" CHANGED ", " ALTERED ", " DUPLICATE ", " YEARS AGO ")),
            ("voice_anomaly", (" VOICE ", " WHISPER ", " INTERCOM ")),
        )
        for label, tokens in patterns:
            if any(token in text for token in tokens):
                return label
        return "other"

    def _entity(self, *, topic: str, script_plan: ScriptPlan) -> str:
        text = _normalize(f"{topic} {script_plan.hook} {script_plan.setup} {script_plan.payoff}")
        entities = (
            ("camera", (" CAMERA ",)),
            ("door", (" DOOR ", " LOCKER ")),
            ("room", (" ROOM ", " WING ")),
            ("intercom", (" INTERCOM ", " SPEAKER ", " RADIO ")),
            ("recorder", (" RECORDER ",)),
            ("signal", (" SIGNAL ", " WARNING ", " DISPLAY ")),
            ("corridor", (" CORRIDOR ", " TUNNEL ", " PLATFORM ", " STAIRWELL ", " STATION ")),
            ("document", (" TRANSCRIPT ", " RECORD ", " FILE ", " ARCHIVE ", " LOG ")),
            ("device", (" DISPLAY ",)),
            ("map", (" MAP ", " BLUEPRINT ", " TIMETABLE ")),
        )
        for label, tokens in entities:
            if any(token in text for token in tokens):
                return label
        return "other"

    def _segment_category(
        self,
        *,
        segment: str,
        visual_anchor: str,
        semantic_pattern: str = "",
        entity: str = "",
        topic: str = "",
        segment_text: str = "",
    ) -> str:
        text = _normalize(topic)
        segment_norm = _normalize(segment_text)
        topic_norm = _normalize(f"{topic} {segment_text}")
        if segment == "hook":
            if visual_anchor == "device":
                if " WARNING " in segment_norm or semantic_pattern == "warning":
                    return "warning_display"
                if any(token in segment_norm for token in (" INTERCOM ", " RECORDER ", " VOICE ", " SPEAKER ", " RADIO ")) or entity in {"intercom", "recorder"} or semantic_pattern == "voice_anomaly":
                    return "intercom_recorder"
                if any(token in segment_norm for token in (" CAMERA ", " SIGNAL ", " SCREEN ", " DISPLAY ", " BLACKOUT ", " GLITCH ")) or entity in {"signal", "camera"} or semantic_pattern == "glitch":
                    return "monitor_screen"
            return visual_anchor
        if segment == "setup":
            if visual_anchor == "document":
                if any(token in text for token in (" ARCHIVE ", " EVIDENCE ", " STATION ", " SERVER ")):
                    return "archive"
                if any(token in topic_norm for token in (" TRANSCRIPT ", " WITNESS ", " STATEMENT ", " CASEFILE ", " RECORD ", " FILE ")):
                    return "archive"
                if any(token in text for token in (" MAP ", " BLUEPRINT ", " CORRIDOR ")):
                    return "map_blueprint"
                return "investigative_interior"
            if visual_anchor == "device":
                if entity in {"intercom", "signal", "camera"} or any(token in text for token in (" STATION ", " PLATFORM ", " TUNNEL ", " CORRIDOR ")):
                    return "institutional_space"
                return "investigative_interior"
            if visual_anchor == "door":
                if any(token in topic_norm for token in (" WHISPER ", " KNOCK ", " WALL ", " ROOM ", " WING ", " HOSPITAL ")):
                    return "horror_interior"
                return "sealed_access" if any(token in text for token in (" SEALED ", " LOCKED ", " EVIDENCE ")) else "horror_interior"
            if visual_anchor == "corridor":
                if any(token in topic_norm for token in (" PLATFORM ", " STATION ", " TUNNEL ", " BLUEPRINT ", " TIMETABLE ")):
                    return "corridor"
                return "institutional_space"
            if any(token in topic_norm for token in (" ELEVATOR ", " EXIT ", " PLATFORM ", " STATION ", " TUNNEL ")):
                return "institutional_space"
            return "investigative_interior"
        if segment == "payoff":
            if semantic_pattern in {"warning", "voice_anomaly", "glitch"} or any(token in segment_norm for token in (" WARNING ", " VOICE ", " INTERCOM ", " RECORDER ", " CAMERA ", " SIGNAL ", " GLITCH ")):
                if any(token in segment_norm for token in (" INTERCOM ", " RECORDER ", " VOICE ", " SPEAKER ", " RADIO ")) or entity in {"intercom", "recorder"}:
                    return "intercom_recorder"
                if any(token in segment_norm for token in (" WARNING ", " SIGNAL ", " CAMERA ", " DISPLAY ", " SCREEN ")) or entity in {"signal", "camera"} or semantic_pattern == "warning":
                    return "warning_display"
                return "monitor_screen"
            if visual_anchor == "document":
                if semantic_pattern in {"missing", "contradiction"} and entity in {"document", "map"}:
                    if any(token in topic_norm for token in (" DATE ", " TIMESTAMP ", " PAGE ", " LOG ", " RECORD ", " FORM ", " FILE ")):
                        return "document"
                    return "evidence_surface"
                if any(token in text for token in (" MAP ", " BLUEPRINT ")):
                    return "map_blueprint"
                return "document"
            if visual_anchor == "corridor":
                if any(token in topic_norm for token in (" MAP ", " BLUEPRINT ", " TIMETABLE ")):
                    return "map_blueprint"
                return "corridor"
            if visual_anchor in {"door", "room"}:
                if semantic_pattern == "sealed":
                    return "sealed_access"
                if any(token in topic_norm for token in (" WHISPER ", " KNOCK ", " WALL ", " INSIDE ")):
                    return "horror_interior"
                return "intercom_recorder"
            return visual_anchor
        return visual_anchor

    def _segment_tags(
        self,
        *,
        segment: str,
        niche: str,
        visual_anchor: str,
        semantic_pattern: str,
        entity: str,
        trend_profile: TrendProfile,
        topic_tags: list[str],
        event_profile: dict[str, str],
        visual_world: dict[str, str | list[str]],
        case_visual_pack: dict[str, str | list[str]],
    ) -> list[str]:
        tags = [niche or "default", visual_anchor, semantic_pattern, entity]
        if segment == "hook":
            tags.append("high_impact")
        if segment == "payoff":
            tags.append("reveal")
        if segment == "setup":
            tags.append("context")
        pacing = (trend_profile.pacing or "").strip().lower()
        if pacing:
            tags.append(pacing)
        event_slug = _slug(event_profile.get("event", ""))
        anomaly_slug = _slug(event_profile.get("anomaly_type", ""))
        visibility_slug = _slug(event_profile.get("visibility_requirement", ""))
        photo_slug = _slug(event_profile.get("photographability", ""))
        if event_slug:
            tags.append(f"event_{event_slug}")
        if anomaly_slug:
            tags.append(f"anomaly_{anomaly_slug}")
        if visibility_slug:
            tags.append(f"visibility_{visibility_slug}")
        if photo_slug:
            tags.append(f"photo_{photo_slug}")
        tags.extend(self._event_signal_tags(event_profile=event_profile))
        tags.extend(
            self._style_tags(
                segment=segment,
                niche=niche,
                visual_anchor=visual_anchor,
                semantic_pattern=semantic_pattern,
                entity=entity,
                event_profile=event_profile,
                topic_tags=topic_tags,
            )
        )
        tags.extend(self._visual_world_tags(visual_world=visual_world))
        tags.extend(self._case_pack_tags(case_visual_pack=case_visual_pack))
        tags.extend(topic_tags)
        return [tag for tag in tags if tag]

    def _segment_effects(self, *, segment: str, trend_profile: TrendProfile) -> list[str]:
        if segment == "hook":
            return ["subtle_push_in"] if trend_profile.pacing == "fast_first_3s" else ["steady_hold"]
        if segment == "payoff":
            return ["contrast_hold"]
        return ["steady_hold"]

    def _background_source(self, *, segment: str, event_profile: dict[str, str]) -> str:
        _ = (segment, event_profile)
        return "local"

    def _segment_event_profile(
        self,
        *,
        segment: str,
        topic: str,
        segment_text: str,
        visual_anchor: str,
        semantic_pattern: str,
        entity: str,
    ) -> dict[str, str]:
        local_text = _normalize(segment_text)
        text = _normalize(f"{topic} {segment_text}")
        topic_text = _normalize(topic)
        event = "ambient_context"
        anomaly_type = semantic_pattern or "other"
        visibility_requirement = "implicit" if segment == "setup" else "explicit"
        photographability = "real"

        document_context = any(token in text for token in (" PAGE ", " DOCUMENT ", " FILE ", " RECORD ", " LOG ", " TRANSCRIPT ", " TIMESTAMP ", " DATE ", " ARCHIVE ", " FORM "))
        device_activation_tokens = (" WARNING ", " ALERT ", " CODE ", " SIGNAL ", " DISPLAY ", " PANEL ", " ACTIVE ", " LIT ", " LIGHT ")
        if any(token in local_text for token in device_activation_tokens) or (
            segment == "hook" and any(token in text for token in device_activation_tokens)
        ):
            event = "active_warning_state"
            anomaly_type = "audio_triggered_device_state" if any(token in text for token in (" INTERCOM ", " VOICE ", " SPEAKER ", " RECORDER ")) else "active_warning_signal"
            visibility_requirement = "explicit"
        elif document_context and (
            any(token in local_text for token in (" CHANGED ", " ALTERED ", " TIMESTAMP ", " DATE ", " REVISED ", " NEXT YEAR ", " MIDNIGHT "))
            or (segment == "hook" and any(token in text for token in (" CHANGED ", " ALTERED ", " TIMESTAMP ", " DATE ", " REVISED ", " NEXT YEAR ", " MIDNIGHT ")))
        ):
            event = "data_inconsistency"
            anomaly_type = "temporal_contradiction"
            visibility_requirement = "explicit"
        elif any(token in local_text for token in (" REDACTED ", " MARGIN ", " NOTE ", " MARKED ", " CHANGED PAGE ", " TRANSCRIPT ")) or (
            segment == "hook" and any(token in text for token in (" REDACTED ", " MARGIN ", " NOTE ", " MARKED ", " CHANGED PAGE ", " TRANSCRIPT "))
        ):
            event = "document_anomaly"
            anomaly_type = "evidence_irregularity"
            visibility_requirement = "explicit"
        elif any(token in local_text for token in (" WHISPER ", " BREATHING ", " PRESENCE ", " ANSWERED BACK ", " SOMEONE INSIDE ", " ANSWERED ", " INSIDE THE ROOM ")) or (
            segment == "hook" and any(token in text for token in (" WHISPER ", " BREATHING ", " PRESENCE ", " ANSWERED BACK ", " SOMEONE INSIDE ", " ANSWERED ", " INSIDE THE ROOM "))
        ):
            event = "unauthorized_presence"
            anomaly_type = "presence_signal"
            visibility_requirement = "explicit" if segment == "payoff" else "implicit"
        elif any(token in local_text for token in (" SEALED ", " LOCKED ", " WARNING TAPE ", " BLOCKED ", " SECURITY TAPE ")) or (
            segment == "hook" and any(token in text for token in (" SEALED ", " LOCKED ", " WARNING TAPE ", " BLOCKED ", " SECURITY TAPE "))
        ):
            event = "containment_breach" if any(token in local_text for token in (" WHISPER ", " INSIDE ", " ANSWERED ", " OPENED ", " MOVED ", " BREATHING ")) else "sealed_containment"
            anomaly_type = "containment_breach" if event == "containment_breach" else "restricted_access"
            visibility_requirement = "explicit" if segment != "setup" else "implicit"
        elif any(token in local_text for token in (" MAP ", " BLUEPRINT ", " EXIT ", " ERASED ", " MISSING ROUTE ", " TIMETABLE ")) or (
            segment == "hook" and any(token in text for token in (" MAP ", " BLUEPRINT ", " EXIT ", " ERASED ", " MISSING ROUTE ", " TIMETABLE "))
        ):
            event = "route_erasure"
            anomaly_type = "navigation_contradiction"
            visibility_requirement = "explicit"
        elif semantic_pattern == "glitch":
            event = "impossible_state"
            anomaly_type = "signal_distortion"
            visibility_requirement = "explicit"

        if any(token in text for token in (" IMPOSSIBLE ", " NOT THERE ", " WRONG SHADOW ", " DISTORTED ", " WARPED ", " BLED THROUGH ", " MOVED BY ITSELF ")):
            photographability = "hard_to_capture"
            event = "impossible_state"
            anomaly_type = "visual_impossibility"
            visibility_requirement = "explicit"
        elif semantic_pattern == "glitch" and entity in {"camera", "signal"} and segment in {"hook", "payoff"}:
            photographability = "hard_to_capture"
        elif event in {"containment_breach", "unauthorized_presence"} and visual_anchor not in {"device", "document", "door"} and segment == "payoff":
            photographability = "hard_to_capture"

        if segment == "setup" and visibility_requirement == "explicit" and event not in {"data_inconsistency", "route_erasure"}:
            visibility_requirement = "implicit"

        if segment == "setup" and event == "ambient_context":
            if any(token in topic_text for token in (" ARCHIVE ", " RECORD ", " FILE ", " DOCUMENT ")):
                event = "archive_context"
                anomaly_type = anomaly_type if anomaly_type != "other" else "documentary_context"
            elif any(token in topic_text for token in (" HOSPITAL ", " WING ", " STATION ", " PLATFORM ", " CORRIDOR ", " TUNNEL ")):
                event = "institutional_context"
                anomaly_type = anomaly_type if anomaly_type != "other" else "environmental_context"

        return {
            "entity": entity or visual_anchor or "other",
            "event": event,
            "anomaly_type": anomaly_type,
            "visibility_requirement": visibility_requirement,
            "photographability": photographability,
        }

    def _decision_contract(
        self,
        *,
        segment: str,
        category: str,
        event_profile: dict[str, str],
    ) -> AssetDecisionContract:
        return AssetDecisionContract(
            entity=event_profile.get("entity", ""),
            event=event_profile.get("event", ""),
            anomaly_type=event_profile.get("anomaly_type", ""),
            visibility_requirement=event_profile.get("visibility_requirement", ""),
            photographability=event_profile.get("photographability", ""),
            justification=self._decision_justification(
                segment=segment,
                category=category,
                event_profile=event_profile,
            ),
        )

    def _decision_justification(
        self,
        *,
        segment: str,
        category: str,
        event_profile: dict[str, str],
    ) -> str:
        event = event_profile.get("event", "ambient_context")
        visibility = event_profile.get("visibility_requirement", "implicit")
        entity = event_profile.get("entity", "scene")
        photographability = event_profile.get("photographability", "real")
        role_phrase = {
            "hook": "hook needs",
            "setup": "setup needs",
            "payoff": "payoff needs",
        }.get(segment, "segment needs")
        visibility_phrase = "explicit" if visibility == "explicit" else "contextual"
        photo_phrase = "hard-to-capture evidence" if photographability == "hard_to_capture" else "real evidence"
        return f"{role_phrase} {category or entity} for {event} with {visibility_phrase} visibility and {photo_phrase}"

    def _visual_query(
        self,
        *,
        segment: str,
        topic: str,
        segment_text: str,
        category: str,
        visual_anchor: str,
        entity: str,
        semantic_pattern: str,
        event_profile: dict[str, str],
        visual_world: dict[str, str | list[str]],
        case_visual_pack: dict[str, str | list[str]],
    ) -> VisualQuery:
        subject = self._visual_query_subject(
            category=category,
            entity=entity,
            case_visual_pack=case_visual_pack,
        )
        state_or_event = self._visual_query_state_or_event(
            segment=segment,
            event_profile=event_profile,
            semantic_pattern=semantic_pattern,
        )
        environment = self._visual_query_environment(
            segment=segment,
            visual_anchor=visual_anchor,
            case_visual_pack=case_visual_pack,
            topic=topic,
        )
        lighting = self._visual_query_lighting(
            visual_world=visual_world,
            segment=segment,
        )
        framing = self._visual_query_framing(segment=segment, category=category)
        mood = self._visual_query_mood(visual_world=visual_world, semantic_pattern=semantic_pattern)
        real_query = " ".join(
            value
            for value in (
                framing,
                subject,
                state_or_event,
                environment,
                lighting,
                mood,
            )
            if value
        )
        return VisualQuery(
            subject=subject,
            state_or_event=state_or_event,
            environment=environment,
            lighting=lighting,
            framing=framing,
            mood=mood,
            search_query_real=real_query.strip(),
        )

    def _visual_query_subject(
        self,
        *,
        category: str,
        entity: str,
        case_visual_pack: dict[str, str | list[str]],
    ) -> str:
        primary_objects = [str(item).replace("_", " ") for item in case_visual_pack.get("primary_objects", [])]
        subject_map = {
            "warning_display": "institutional warning panel with active alert light",
            "intercom_recorder": "institutional intercom panel and wall speaker",
            "monitor_screen": "surveillance monitor with unstable signal",
            "document": "police case file page with marked timestamp",
            "evidence_surface": "evidence desk with case file under review",
            "archive": "records evidence surface with active case file",
            "map_blueprint": "station map or blueprint with missing route",
            "sealed_access": "restricted access door with broken seal",
            "door": "sealed institutional door with breach cue",
            "horror_interior": "restricted room threshold with intrusion evidence",
            "institutional_space": "institutional wall zone around alert system",
            "corridor": "transit corridor tied to the active case",
            "investigative_interior": "investigation room with case evidence",
        }
        if category in subject_map:
            return subject_map[category]
        if primary_objects:
            return " ".join(primary_objects[:2])
        return f"{entity or category} evidence".strip()

    def _visual_query_state_or_event(
        self,
        *,
        segment: str,
        event_profile: dict[str, str],
        semantic_pattern: str,
    ) -> str:
        event = event_profile.get("event", "")
        state_map = {
            "active_warning_state": "showing active warning state",
            "data_inconsistency": "showing a visible timestamp mismatch",
            "document_anomaly": "showing redaction or marked contradiction",
            "unauthorized_presence": "showing a presence cue or response from inside",
            "sealed_containment": "showing restricted access still under tension",
            "containment_breach": "showing a broken seal and breach evidence",
            "route_erasure": "showing a missing route or erased corridor mark",
            "impossible_state": "showing an impossible or distorted state",
            "archive_context": "under active evidence review",
            "institutional_context": "under anomaly pressure",
            "ambient_context": "with visible case tension",
        }
        base = state_map.get(event, semantic_pattern.replace("_", " "))
        if segment == "setup":
            return f"{base} with new evidence progression".strip()
        if segment == "payoff":
            return f"{base} as explicit proof".strip()
        return base.strip()

    def _visual_query_environment(
        self,
        *,
        segment: str,
        visual_anchor: str,
        case_visual_pack: dict[str, str | list[str]],
        topic: str,
    ) -> str:
        primary_envs = [str(item).replace("_", " ") for item in case_visual_pack.get("primary_environments", [])]
        if primary_envs:
            if segment == "hook":
                return primary_envs[0]
            return " ".join(primary_envs[:2])
        topic_text = _normalize(topic)
        if any(token in topic_text for token in (" STATION ", " PLATFORM ", " CORRIDOR ", " TUNNEL ")):
            return "dark transit corridor"
        if any(token in topic_text for token in (" ARCHIVE ", " FILE ", " RECORD ", " CASE ")):
            return "evidence desk in investigative archive room"
        if visual_anchor in {"door", "room"}:
            return "cold institutional threshold"
        return "grounded institutional setting"

    def _visual_query_lighting(self, *, visual_world: dict[str, str | list[str]], segment: str) -> str:
        lighting_style = str(visual_world.get("lighting_style", "")).replace("_", " ").strip()
        if lighting_style:
            return lighting_style
        if segment == "hook":
            return "high contrast practical lighting"
        if segment == "payoff":
            return "dim focused reveal lighting"
        return "dim tungsten practical light"

    def _visual_query_framing(self, *, segment: str, category: str) -> str:
        if segment == "hook":
            return "close up"
        if segment == "payoff":
            return "tight detail shot"
        if category in {"corridor", "institutional_space"}:
            return "medium shot"
        return "close mid shot"

    def _visual_query_mood(self, *, visual_world: dict[str, str | list[str]], semantic_pattern: str) -> str:
        mood = str(visual_world.get("mood", "")).replace("_", " ").strip()
        if mood:
            return mood
        if semantic_pattern in {"sealed", "voice_anomaly"}:
            return "cold ominous mood"
        if semantic_pattern in {"warning", "glitch"}:
            return "urgent institutional tension"
        return "investigative tense mood"

    def _event_signal_tags(self, *, event_profile: dict[str, str]) -> list[str]:
        event = event_profile.get("event", "")
        anomaly_type = event_profile.get("anomaly_type", "")
        mapping = {
            "active_warning_state": ["evidence_warning", "evidence_activation", "evidence_signal", "evidence_device_state"],
            "data_inconsistency": ["evidence_date", "evidence_timestamp", "evidence_changed", "evidence_document_anomaly"],
            "document_anomaly": ["evidence_redacted", "evidence_marked", "evidence_closeup", "evidence_document_anomaly"],
            "sealed_containment": ["evidence_sealed", "evidence_restricted", "evidence_security"],
            "containment_breach": ["evidence_breach", "evidence_sealed", "evidence_violation", "evidence_security"],
            "unauthorized_presence": ["evidence_presence", "evidence_whisper", "evidence_glow"],
            "route_erasure": ["evidence_map", "evidence_blueprint", "evidence_missing_route"],
            "archive_context": ["context_archive", "context_document"],
            "institutional_context": ["context_institutional", "context_corridor"],
            "impossible_state": ["evidence_distortion", "evidence_impossible", "evidence_glitch"],
        }
        tags = list(mapping.get(event, []))
        if anomaly_type == "temporal_contradiction":
            tags.extend(["evidence_temporal", "evidence_contradiction"])
        if anomaly_type == "audio_triggered_device_state":
            tags.extend(["evidence_audio", "evidence_intercom"])
        if anomaly_type == "presence_signal":
            tags.extend(["evidence_presence", "evidence_inside"])
        return tags

    def _case_visual_pack_profile(
        self,
        *,
        topic: str,
        visual_anchor: str,
        semantic_pattern: str,
        entity: str,
        topic_tags: list[str],
        event_profiles: dict[str, dict[str, str]],
    ) -> dict[str, str | list[str]]:
        topic_text = _normalize(topic)
        event_set = {profile.get("event", "") for profile in event_profiles.values()}

        if visual_anchor == "document" or event_set & {"data_inconsistency", "document_anomaly", "archive_context"}:
            payload = {
                "primary_case_family": "live_evidence_review",
                "primary_objects": ["marked_page", "redacted_file", "transcript", "evidence_surface", "case_form"],
                "primary_evidence_forms": ["altered_entry", "timestamp_inconsistency", "anomaly_marking", "active_inspection"],
                "primary_environments": ["evidence_desk", "review_surface", "case_handling_context"],
                "forbidden_proxy_families": ["generic_archive_ambience", "generic_shelves", "generic_manuscript_texture", "decorative_old_paper"],
                "required_event_states": ["alteration", "contradiction", "timestamp_anomaly", "marking", "active_inspection"],
            }
            return self._with_case_evidence_schema(payload=payload)

        if visual_anchor == "device" or entity in {"intercom", "signal", "camera", "recorder"} or event_set & {"active_warning_state"}:
            payload = {
                "primary_case_family": "institutional_alert_system",
                "primary_objects": ["intercom", "warning_panel", "wall_speaker", "alert_interface", "signal_device"],
                "primary_evidence_forms": ["active_signal", "warning_state", "device_activation", "panel_alert"],
                "primary_environments": ["station_corridor", "institutional_wall_zone", "control_panel_context"],
                "forbidden_proxy_families": ["car_dashboard", "generic_clock", "unrelated_meter", "consumer_dashboard"],
                "required_event_states": ["active_signal", "warning_state", "ongoing_alert", "state_change"],
            }
            return self._with_case_evidence_schema(payload=payload)

        if visual_anchor in {"door", "room"} or semantic_pattern in {"sealed", "voice_anomaly"} or event_set & {"containment_breach", "sealed_containment", "unauthorized_presence"}:
            payload = {
                "primary_case_family": "sealed_containment_incident",
                "primary_objects": ["sealed_door", "security_tape", "threshold_marker", "entry_panel", "containment_label"],
                "primary_evidence_forms": ["seal_violation", "breach_signal", "presence_cue", "lock_state_change"],
                "primary_environments": ["sealed_threshold", "restricted_corridor", "containment_entry_zone"],
                "forbidden_proxy_families": ["generic_tape_closeup", "neutral_hallway", "generic_room_context", "generic_warning_loop"],
                "required_event_states": ["containment_state", "breach_state", "presence_state", "security_violation"],
            }
            return self._with_case_evidence_schema(payload=payload)

        if visual_anchor == "corridor" or event_set & {"route_erasure"} or {"map", "blueprint", "route", "station"} & set(topic_tags):
            payload = {
                "primary_case_family": "route_anomaly_investigation",
                "primary_objects": ["map_surface", "blueprint_panel", "route_marker", "navigation_display"],
                "primary_evidence_forms": ["route_erasure", "path_contradiction", "missing_exit_signal"],
                "primary_environments": ["station_passage", "map_review_zone", "navigation_wall_context"],
                "forbidden_proxy_families": ["generic_corridor_ambience", "empty_walkway", "neutral_passage_context"],
                "required_event_states": ["route_change", "navigation_anomaly", "evidence_progression"],
            }
            return self._with_case_evidence_schema(payload=payload)

        fallback_family = "case_specific_event_world"
        if any(token in topic_text for token in (" ARCHIVE ", " FILE ", " DOCUMENT ", " CASE ")):
            fallback_family = "case_evidence_world"
        payload = {
            "primary_case_family": fallback_family,
            "primary_objects": [entity or visual_anchor or "case_object"],
            "primary_evidence_forms": ["event_evidence", "state_change"],
            "primary_environments": ["case_environment"],
            "forbidden_proxy_families": ["generic_context_proxy"],
            "required_event_states": ["event_progression"],
        }
        return self._with_case_evidence_schema(payload=payload)

    def _with_case_evidence_schema(self, *, payload: dict[str, str | list[str]]) -> dict[str, str | list[str]]:
        family = str(payload.get("primary_case_family", "")).strip()
        objects = [str(v).strip() for v in payload.get("primary_objects", []) if str(v).strip()]
        evidence_forms = [str(v).strip() for v in payload.get("primary_evidence_forms", []) if str(v).strip()]
        environments = [str(v).strip() for v in payload.get("primary_environments", []) if str(v).strip()]
        forbidden = [str(v).strip() for v in payload.get("forbidden_proxy_families", []) if str(v).strip()]
        required_states = [str(v).strip() for v in payload.get("required_event_states", []) if str(v).strip()]
        progression_steps = required_states[:]
        if family == "institutional_alert_system":
            progression_steps = ["signal", "source", "escalation"]
        elif family == "live_evidence_review":
            progression_steps = ["document", "anomaly_detail", "contradiction_proof"]
        elif family == "sealed_containment_incident":
            progression_steps = ["restriction", "anomaly_signal", "breach_evidence"]
        merged = dict(payload)
        merged.update(
            {
                "case_core_objects": objects,
                "case_evidence_forms": evidence_forms,
                "case_allowed_contexts": environments,
                "forbidden_symbolic_motifs": forbidden,
                "required_progression_steps": progression_steps,
            }
        )
        # Keep a stable canonical family key for audit consumers.
        merged["case_primary_family"] = family
        return merged

    def _case_pack_tags(self, *, case_visual_pack: dict[str, str | list[str]]) -> list[str]:
        tags: list[str] = []
        family = str(case_visual_pack.get("primary_case_family", "")).strip()
        if family:
            tags.append(f"case_family_{_slug(family)}")

        for key, prefix in (
            ("primary_objects", "case_object"),
            ("primary_evidence_forms", "case_evidence"),
            ("primary_environments", "case_environment"),
            ("forbidden_proxy_families", "case_forbid"),
            ("required_event_states", "case_state"),
            ("case_core_objects", "case_core"),
            ("case_evidence_forms", "case_form"),
            ("case_allowed_contexts", "case_context"),
            ("forbidden_symbolic_motifs", "case_motif_forbid"),
            ("required_progression_steps", "case_step"),
        ):
            for value in case_visual_pack.get(key, []):
                item = str(value).strip()
                if item:
                    tags.append(f"{prefix}_{_slug(item)}")
        return tags

    def _style_tags(
        self,
        *,
        segment: str,
        niche: str,
        visual_anchor: str,
        semantic_pattern: str,
        entity: str,
        event_profile: dict[str, str],
        topic_tags: list[str],
    ) -> list[str]:
        tags: list[str] = []
        lowered_niche = niche.strip().lower()
        topic_token_set = set(topic_tags)
        event = event_profile.get("event", "")

        if lowered_niche in {"true_crime", "crime", "facts"} or visual_anchor == "document":
            tags.append("style_documentary_dark")
        if lowered_niche == "horror" or semantic_pattern in {"sealed", "voice_anomaly"}:
            tags.append("style_horror_institutional")
        if visual_anchor in {"corridor", "door", "room"} or {"hospital", "station", "platform", "corridor", "wing"} & topic_token_set:
            tags.append("style_institutional_cold")
        if visual_anchor == "device" or entity in {"intercom", "signal", "camera"}:
            tags.append("style_device_tense")
        if {"archive", "record", "document", "casefile"} & topic_token_set or event in {"archive_context", "data_inconsistency", "document_anomaly"}:
            tags.append("style_archive_case")
        if segment == "setup":
            tags.append("style_bridge_frame")
        if segment == "payoff":
            tags.append("style_reveal_frame")
        return tags

    def _visual_world_profile(
        self,
        *,
        niche: str,
        topic: str,
        visual_anchor: str,
        semantic_pattern: str,
        entity: str,
        topic_tags: list[str],
        event_profiles: dict[str, dict[str, str]],
    ) -> dict[str, str | list[str]]:
        topic_token_set = set(topic_tags)
        lowered_niche = niche.strip().lower()
        event_set = {profile.get("event", "") for profile in event_profiles.values()}

        visual_family = "institutional_investigation"
        environment_type = "interior_institutional"
        lighting_style = "low_key_cold"
        color_palette = "desaturated_blue_gray"
        texture_profile = "documentary_grain"
        realism_level = "photorealistic"
        dominant_emotion = "mystery"
        secondary_emotion = "tension"
        tension_level = "medium"
        mood = "mysterious"
        preferred_families = ["investigative_ambient", "institutional_space"]
        preferred_moods = ["tense", "clinical", "ominous"]
        allowed_categories = [
            visual_anchor,
            "corridor",
            "archive",
            "document",
            "institutional_space",
            "intercom_recorder",
            "warning_display",
            "sealed_access",
            "horror_interior",
        ]
        forbidden_patterns = ["corporate_people", "bright_lifestyle", "sunny_exterior", "playful_stock"]

        if visual_anchor == "document" or {"archive", "document", "record", "casefile", "file"} & topic_token_set:
            visual_family = "documentary_caseworld"
            environment_type = "archive_evidence_interior"
            lighting_style = "low_key_documentary"
            color_palette = "desaturated_paper_steel"
            texture_profile = "paper_grain_evidence"
            dominant_emotion = "curiosity"
            secondary_emotion = "dread"
            mood = "investigative"
            preferred_families = ["documentary_evidence", "archive", "documentary_context"]
            preferred_moods = ["clinical", "tense"]
            allowed_categories = ["document", "archive", "evidence_surface", "investigative_interior", "institutional_space"]
            forbidden_patterns = ["corporate_people", "meeting_room", "lifestyle_office", "sunny_exterior"]
        elif visual_anchor == "device" or entity in {"intercom", "signal", "camera", "recorder"}:
            visual_family = "institutional_device_alert"
            environment_type = "device_institutional_interior"
            lighting_style = "contrast_device_glow"
            color_palette = "cold_gray_signal_red"
            texture_profile = "metal_panel_noise"
            dominant_emotion = "threat"
            secondary_emotion = "urgency"
            tension_level = "high"
            mood = "threatening"
            preferred_families = ["device_warning", "warning_display", "intercom_recorder", "institutional_space", "corridor"]
            preferred_moods = ["tense", "ominous"]
            allowed_categories = ["warning_display", "intercom_recorder", "monitor_screen", "institutional_space", "corridor"]
            forbidden_patterns = ["corporate_people", "sunny_walkway", "outdoor_daylight", "lifestyle_workspace"]
        elif visual_anchor in {"door", "room"} or semantic_pattern in {"sealed", "voice_anomaly"}:
            visual_family = "sealed_institutional_horror"
            environment_type = "contained_decay_interior"
            lighting_style = "low_key_ominous"
            color_palette = "dirty_green_steel"
            texture_profile = "decay_threshold"
            dominant_emotion = "fear"
            secondary_emotion = "claustrophobia"
            tension_level = "high"
            mood = "oppressive"
            realism_level = "stylized_realistic" if "impossible_state" in event_set else "photorealistic"
            preferred_families = ["institutional_horror", "sealed_access", "door", "corridor"]
            preferred_moods = ["ominous", "tense"]
            allowed_categories = ["sealed_access", "horror_interior", "door", "corridor", "institutional_space"]
            forbidden_patterns = ["corporate_people", "bright_lobby", "sunny_exterior", "clean_office"]
        elif visual_anchor == "corridor":
            visual_family = "institutional_passage_tension"
            environment_type = "narrow_passage_interior"
            lighting_style = "cold_falloff"
            color_palette = "gray_blue_shadow"
            texture_profile = "hard_surface_depth"
            dominant_emotion = "tension"
            secondary_emotion = "unease"
            tension_level = "high" if "route_erasure" in event_set else "medium"
            mood = "tense"
            preferred_families = ["corridor", "institutional_space", "institutional_horror", "archive"]
            preferred_moods = ["tense", "ominous", "clinical"]
            allowed_categories = ["corridor", "institutional_space", "map_blueprint", "sealed_access", "warning_display"]
            forbidden_patterns = ["corporate_people", "sunny_walkway", "bright_open_passage", "lifestyle_space"]

        if semantic_pattern == "contradiction" or "data_inconsistency" in event_set:
            dominant_emotion = "unease"
            secondary_emotion = "curiosity"
            mood = "mysterious"
        if semantic_pattern == "warning":
            dominant_emotion = "urgency"
            secondary_emotion = "threat"
            tension_level = "high"
            mood = "threatening"
        if semantic_pattern == "voice_anomaly":
            secondary_emotion = "dread"
            mood = "oppressive"
        if lowered_niche == "horror":
            lighting_style = "low_key_ominous"
            color_palette = "dirty_green_shadow"
            texture_profile = "decay_threshold"
            dominant_emotion = "fear"
            tension_level = "high"
            mood = "oppressive"

        return {
            "visual_family": visual_family,
            "environment_type": environment_type,
            "lighting_style": lighting_style,
            "color_palette": color_palette,
            "texture_profile": texture_profile,
            "realism_level": realism_level,
            "dominant_emotion": dominant_emotion,
            "secondary_emotion": secondary_emotion,
            "tension_level": tension_level,
            "mood": mood,
            "preferred_families": preferred_families,
            "preferred_moods": preferred_moods,
            "allowed_categories": allowed_categories,
            "forbidden_patterns": forbidden_patterns,
        }

    def _visual_world_tags(self, *, visual_world: dict[str, str | list[str]]) -> list[str]:
        tags: list[str] = []
        for key in (
            "visual_family",
            "environment_type",
            "lighting_style",
            "color_palette",
            "texture_profile",
            "realism_level",
            "dominant_emotion",
            "secondary_emotion",
            "tension_level",
            "mood",
        ):
            value = str(visual_world.get(key, "")).strip()
            if value:
                tags.append(f"{key}_{_slug(value)}")

        emotion_constraints = {
            "fear": ["constraint_shadow", "constraint_occlusion", "constraint_tight_framing"],
            "threat": ["constraint_high_contrast", "constraint_presence_cue", "constraint_signal_focus"],
            "urgency": ["constraint_signal_focus", "constraint_mid_close_framing", "constraint_contrast_shaping"],
            "mystery": ["constraint_partial_information", "constraint_ambiguous_depth", "constraint_subtle_occlusion"],
            "curiosity": ["constraint_evidence_focus", "constraint_detail_focus"],
            "unease": ["constraint_limited_depth", "constraint_directional_falloff"],
            "claustrophobia": ["constraint_tight_framing", "constraint_limited_depth", "constraint_enclosed_space"],
            "tension": ["constraint_mid_close_framing", "constraint_directional_falloff"],
            "dread": ["constraint_shadow", "constraint_enclosed_space", "constraint_ambiguous_depth"],
        }
        for emotion_key in ("dominant_emotion", "secondary_emotion"):
            value = str(visual_world.get(emotion_key, "")).strip()
            if not value:
                continue
            tags.extend(emotion_constraints.get(value, []))

        for category in visual_world.get("allowed_categories", []):
            if str(category).strip():
                tags.append(f"world_allow_{_slug(str(category))}")
        for family in visual_world.get("preferred_families", []):
            if str(family).strip():
                tags.append(f"world_family_{_slug(str(family))}")
        for mood in visual_world.get("preferred_moods", []):
            if str(mood).strip():
                tags.append(f"world_mood_{_slug(str(mood))}")
        for pattern in visual_world.get("forbidden_patterns", []):
            if str(pattern).strip():
                tags.append(f"world_forbid_{_slug(str(pattern))}")
        return tags
