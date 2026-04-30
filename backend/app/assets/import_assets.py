from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from app.assets.pexels_ingestor import PexelsIngestor
from app.assets.unsplash_ingestor import UnsplashIngestor
from app.assets.pixabay_ingestor import PixabayIngestor


ROOT = Path(__file__).resolve().parents[3]
ASSETS_DIR = ROOT / "assets" / "curated"
CATALOG_PATH = Path(__file__).resolve().parent / "catalog.json"
SUMMARY_PATH = ROOT / "OUT" / "audit" / "asset_agent_rebuild" / "import_workflow_summary.json"


@dataclass(frozen=True)
class AssetRecipe:
    name: str
    category: str
    subtype: str
    source: str
    family: str = ""
    framing: str = "medium"
    crop: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)
    flip: bool = False
    brightness: float = 1.0
    contrast: float = 1.0
    color: float = 1.0
    blur: float = 0.0
    overlays: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    mood: str = "neutral"
    semantic_pattern_fit: tuple[str, ...] = ()
    entity_fit: tuple[str, ...] = ()
    hook_strength_score: float = 0.5
    payoff_strength_score: float = 0.5
    setup_specificity_score: float = 0.5
    realism_score: float = 0.7
    source_type: str = "local_curated"


def default_recipes() -> list[AssetRecipe]:
    return [
        AssetRecipe("corridor_platform_warning_01", "corridor", "institutional_platform", "assets/backgrounds/horror/horror_02.jpg", brightness=0.95, contrast=1.08, tags=("corridor", "platform", "warning", "institutional"), mood="tense", semantic_pattern_fit=("warning", "sealed"), entity_fit=("corridor", "station"), hook_strength_score=0.86, payoff_strength_score=0.72, realism_score=0.88),
        AssetRecipe("corridor_dark_passage_01", "corridor", "dark_passage", "assets/backgrounds/horror/horror_03.jpg", contrast=1.06, color=0.82, tags=("corridor", "dark", "passage", "sealed"), mood="ominous", semantic_pattern_fit=("sealed", "missing"), entity_fit=("corridor", "tunnel"), hook_strength_score=0.82, payoff_strength_score=0.82, realism_score=0.84),
        AssetRecipe("corridor_decay_stairs_01", "corridor", "decay_stairs", "assets/backgrounds/horror/horror_04.jpg", contrast=1.04, tags=("corridor", "warning", "decay", "entryway"), mood="ominous", semantic_pattern_fit=("warning", "voice_anomaly"), entity_fit=("corridor", "station"), hook_strength_score=0.88, payoff_strength_score=0.78, realism_score=0.86),
        AssetRecipe("corridor_night_hall_01", "corridor", "night_hall", "assets/environments/corridor_01.jpg", brightness=0.9, contrast=1.04, tags=("corridor", "hallway", "dark", "institutional"), mood="tense", semantic_pattern_fit=("sealed", "warning"), entity_fit=("corridor",), hook_strength_score=0.74, payoff_strength_score=0.7, realism_score=0.8),
        AssetRecipe("corridor_interior_reveal_01", "corridor", "interior_reveal", "assets/environments/corridor_02.jpg", contrast=1.06, tags=("corridor", "interior", "reveal"), mood="tense", semantic_pattern_fit=("reveal", "voice_anomaly"), entity_fit=("corridor",), hook_strength_score=0.7, payoff_strength_score=0.75, realism_score=0.78),

        AssetRecipe("room_forensics_lab_01", "room", "forensics_lab", "assets/backgrounds/facts/facts_02.jpg", crop=(0.1, 0.05, 0.92, 0.95), contrast=1.02, tags=("lab", "forensics", "investigation", "room"), mood="clinical", semantic_pattern_fit=("other", "contradiction"), entity_fit=("room", "evidence_surface"), hook_strength_score=0.68, payoff_strength_score=0.7, realism_score=0.92),
        AssetRecipe("room_archive_interior_01", "room", "archive_interior", "assets/backgrounds/conspiracy/conspiracy_01.jpg", tags=("archive", "interior", "investigation", "room"), mood="tense", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("room", "archive"), hook_strength_score=0.64, payoff_strength_score=0.68, realism_score=0.84),
        AssetRecipe("room_investigative_interior_02", "room", "old_interior", "assets/environments/room_02.jpg", contrast=1.02, tags=("room", "investigation", "institutional_space"), mood="tense", semantic_pattern_fit=("warning", "contradiction"), entity_fit=("room", "archive"), hook_strength_score=0.62, payoff_strength_score=0.66, realism_score=0.82),

        AssetRecipe("door_sealed_entry_01", "door", "sealed_entry", "assets/objects/door_01.jpg", contrast=1.06, tags=("door", "sealed", "entry"), mood="ominous", semantic_pattern_fit=("sealed",), entity_fit=("door", "sealed_access"), hook_strength_score=0.88, payoff_strength_score=0.8, realism_score=0.9),
        AssetRecipe("door_locked_entry_02", "door", "locked_entry", "assets/objects/door_02.jpg", contrast=1.04, tags=("door", "locked", "entry"), mood="tense", semantic_pattern_fit=("sealed", "warning"), entity_fit=("door", "sealed_access"), hook_strength_score=0.82, payoff_strength_score=0.76, realism_score=0.88),

        AssetRecipe("archive_shelves_01", "archive", "shelves", "assets/backgrounds/conspiracy/conspiracy_02.jpg", family="documentary_context", framing="wide", tags=("archive", "shelves", "records"), mood="tense", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("archive", "document"), hook_strength_score=0.46, payoff_strength_score=0.5, setup_specificity_score=0.42, realism_score=0.74),
        AssetRecipe("archive_shelves_02", "archive", "shelves_close", "assets/objects/document_01.jpg", family="documentary_context", framing="closeup", crop=(0.08, 0.0, 0.85, 1.0), tags=("archive", "records", "document"), mood="neutral", semantic_pattern_fit=("contradiction",), entity_fit=("archive", "document"), hook_strength_score=0.4, payoff_strength_score=0.46, setup_specificity_score=0.24, realism_score=0.68),
        AssetRecipe("archive_storage_real_01", "archive", "storage_rows", "assets/imports/wikimedia_archive_storage.jpg", crop=(0.03, 0.0, 0.97, 1.0), contrast=1.04, color=0.94, tags=("archive", "storage", "records", "files"), mood="clinical", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("archive", "document"), hook_strength_score=0.76, payoff_strength_score=0.8, realism_score=0.97),
        AssetRecipe("archive_storage_real_02", "archive", "records_shelves", "assets/imports/wikimedia_records_shelves.jpg", crop=(0.18, 0.0, 0.9, 1.0), contrast=1.03, color=0.96, tags=("archive", "records", "shelves", "files"), mood="clinical", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("archive", "document"), hook_strength_score=0.74, payoff_strength_score=0.78, realism_score=0.95),

        AssetRecipe("document_transcript_01", "document", "transcript", "assets/objects/document_02.jpg", family="documentary_evidence", framing="detail", tags=("document", "transcript", "record"), mood="neutral", semantic_pattern_fit=("missing", "contradiction"), entity_fit=("document", "transcript"), hook_strength_score=0.58, payoff_strength_score=0.68, setup_specificity_score=0.36, realism_score=0.78),
        AssetRecipe("document_timestamp_01", "document", "timestamp_record", "assets/objects/document_03.jpg", family="documentary_evidence", framing="detail", tags=("document", "timestamp", "date", "record"), mood="neutral", semantic_pattern_fit=("contradiction",), entity_fit=("document", "record"), hook_strength_score=0.5, payoff_strength_score=0.58, setup_specificity_score=0.28, realism_score=0.66),
        AssetRecipe("document_archive_closeup_01", "document", "archive_closeup", "assets/objects/document_01.jpg", family="documentary_evidence", framing="closeup", tags=("document", "archive", "evidence"), mood="neutral", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("document", "evidence_surface"), hook_strength_score=0.62, payoff_strength_score=0.72, setup_specificity_score=0.4, realism_score=0.8),
        AssetRecipe("document_casefile_timestamp_01", "document", "casefile_timestamp", "assets/imports/wikimedia_casefile_page4.jpg", family="documentary_evidence", framing="closeup", crop=(0.04, 0.0, 0.96, 0.98), contrast=1.06, brightness=1.02, color=0.94, tags=("document", "timestamp", "date", "record", "case_file"), mood="neutral", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("document", "record"), hook_strength_score=0.96, payoff_strength_score=0.88, setup_specificity_score=0.78, realism_score=0.99),
        AssetRecipe("document_casefile_form_01", "document", "casefile_form", "assets/imports/wikimedia_casefile_page13.jpg", family="documentary_evidence", framing="closeup", crop=(0.03, 0.0, 0.97, 0.98), contrast=1.04, brightness=1.02, color=0.96, tags=("document", "record", "form", "case_file"), mood="neutral", semantic_pattern_fit=("contradiction",), entity_fit=("document", "record"), hook_strength_score=0.92, payoff_strength_score=0.86, setup_specificity_score=0.76, realism_score=0.99),
        AssetRecipe("document_casefile_redacted_02", "document", "casefile_redacted", "assets/imports/wikimedia_casefile_page4.jpg", family="documentary_evidence", framing="detail", crop=(0.1, 0.08, 0.9, 0.88), contrast=1.08, brightness=1.04, color=0.92, overlays=("redaction_bar", "highlight_box"), tags=("document", "record", "redacted", "anomaly", "case_file", "timestamp", "date", "page"), mood="tense", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("document", "record"), hook_strength_score=0.84, payoff_strength_score=0.96, setup_specificity_score=0.72, realism_score=0.96),
        AssetRecipe("document_margin_anomaly_03", "document", "margin_anomaly", "assets/imports/wikimedia_casefile_page13.jpg", family="documentary_evidence", framing="detail", crop=(0.08, 0.06, 0.9, 0.92), contrast=1.08, brightness=1.03, color=0.94, overlays=("anomaly_circle", "highlight_box"), tags=("document", "form", "anomaly", "record", "case_file", "page", "changed"), mood="tense", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("document", "record"), hook_strength_score=0.8, payoff_strength_score=0.94, setup_specificity_score=0.7, realism_score=0.96),

        AssetRecipe("warning_display_01", "warning_display", "intercom_warning", "assets/backgrounds/horror/horror_04.jpg", family="device_warning", framing="closeup", overlays=("warning_panel", "signal_wave"), tags=("warning", "display", "intercom"), mood="tense", semantic_pattern_fit=("warning", "voice_anomaly"), entity_fit=("warning_display", "intercom"), hook_strength_score=0.48, payoff_strength_score=0.46, setup_specificity_score=0.25, realism_score=0.42),
        AssetRecipe("warning_display_02", "warning_display", "monitor_alert", "assets/backgrounds/horror/horror_03.jpg", family="device_warning", framing="closeup", overlays=("warning_panel",), tags=("warning", "display", "monitor"), mood="tense", semantic_pattern_fit=("warning", "glitch"), entity_fit=("warning_display", "monitor_screen"), hook_strength_score=0.44, payoff_strength_score=0.42, setup_specificity_score=0.22, realism_score=0.4),
        AssetRecipe("warning_display_real_01", "warning_display", "intercom_panel_alert", "assets/imports/wikimedia_intercom.jpg", family="device_warning", framing="closeup", crop=(0.02, 0.0, 0.92, 1.0), overlays=("warning_led",), contrast=1.06, brightness=0.98, color=0.94, tags=("warning", "display", "intercom", "device"), mood="tense", semantic_pattern_fit=("warning", "voice_anomaly"), entity_fit=("warning_display", "intercom"), hook_strength_score=0.95, payoff_strength_score=0.82, setup_specificity_score=0.74, realism_score=0.96),

        AssetRecipe("monitor_screen_01", "monitor_screen", "alert_monitor", "assets/backgrounds/facts/facts_02.jpg", family="device_warning", framing="closeup", overlays=("monitor_panel", "warning_symbol"), tags=("monitor", "screen", "alert"), mood="clinical", semantic_pattern_fit=("warning", "glitch"), entity_fit=("monitor_screen", "device"), hook_strength_score=0.58, payoff_strength_score=0.56, setup_specificity_score=0.32, realism_score=0.48),
        AssetRecipe("monitor_screen_02", "monitor_screen", "signal_monitor", "assets/backgrounds/horror/horror_02.jpg", family="device_warning", framing="closeup", overlays=("monitor_panel", "signal_wave"), tags=("monitor", "screen", "signal"), mood="tense", semantic_pattern_fit=("warning", "voice_anomaly"), entity_fit=("monitor_screen", "device"), hook_strength_score=0.56, payoff_strength_score=0.56, setup_specificity_score=0.3, realism_score=0.46),

        AssetRecipe("intercom_recorder_01", "intercom_recorder", "wall_intercom", "assets/backgrounds/horror/horror_04.jpg", family="device_warning", framing="closeup", overlays=("intercom_panel", "signal_wave"), tags=("intercom", "recorder", "device"), mood="tense", semantic_pattern_fit=("voice_anomaly", "warning"), entity_fit=("intercom", "recorder"), hook_strength_score=0.48, payoff_strength_score=0.5, setup_specificity_score=0.22, realism_score=0.4),
        AssetRecipe("intercom_recorder_02", "intercom_recorder", "corridor_intercom", "assets/backgrounds/horror/horror_03.jpg", family="device_warning", framing="medium", overlays=("intercom_panel",), tags=("intercom", "speaker", "device"), mood="ominous", semantic_pattern_fit=("voice_anomaly",), entity_fit=("intercom", "device"), hook_strength_score=0.46, payoff_strength_score=0.48, setup_specificity_score=0.24, realism_score=0.38),
        AssetRecipe("intercom_recorder_real_01", "intercom_recorder", "flat_intercom", "assets/imports/wikimedia_intercom.jpg", family="device_warning", framing="closeup", crop=(0.02, 0.0, 0.92, 1.0), contrast=1.08, brightness=1.0, color=0.92, tags=("intercom", "recorder", "device", "warning"), mood="tense", semantic_pattern_fit=("voice_anomaly", "warning"), entity_fit=("intercom", "device"), hook_strength_score=0.93, payoff_strength_score=0.94, setup_specificity_score=0.7, realism_score=0.98),
        AssetRecipe("intercom_recorder_real_02", "intercom_recorder", "flat_intercom_close", "assets/imports/wikimedia_intercom.jpg", family="device_warning", framing="detail", crop=(0.12, 0.08, 0.9, 0.98), contrast=1.09, brightness=1.01, color=0.92, tags=("intercom", "speaker", "device", "warning"), mood="tense", semantic_pattern_fit=("voice_anomaly", "warning"), entity_fit=("intercom", "device"), hook_strength_score=0.9, payoff_strength_score=0.96, setup_specificity_score=0.68, realism_score=0.98),

        AssetRecipe("sealed_access_01", "sealed_access", "warning_tape_door", "assets/objects/door_01.jpg", family="institutional_horror", framing="medium", overlays=("seal_strips",), tags=("sealed", "access", "door"), mood="tense", semantic_pattern_fit=("sealed",), entity_fit=("sealed_access", "door"), hook_strength_score=0.9, payoff_strength_score=0.82, setup_specificity_score=0.74, realism_score=0.86),
        AssetRecipe("sealed_access_02", "sealed_access", "blocked_corridor", "assets/backgrounds/horror/horror_02.jpg", family="institutional_horror", framing="wide", overlays=("seal_strips",), tags=("sealed", "access", "corridor"), mood="tense", semantic_pattern_fit=("sealed", "missing"), entity_fit=("sealed_access", "corridor"), hook_strength_score=0.74, payoff_strength_score=0.78, setup_specificity_score=0.62, realism_score=0.74),
        AssetRecipe("sealed_access_security_lock_03", "sealed_access", "security_lock", "assets/objects/door_02.jpg", family="institutional_horror", framing="detail", crop=(0.18, 0.05, 0.88, 0.92), contrast=1.08, brightness=0.98, overlays=("seal_strips", "security_lock"), tags=("sealed", "access", "door", "security", "lock"), mood="ominous", semantic_pattern_fit=("sealed", "warning"), entity_fit=("sealed_access", "door"), hook_strength_score=0.82, payoff_strength_score=0.95, setup_specificity_score=0.66, realism_score=0.88),
        AssetRecipe("sealed_access_window_glow_04", "sealed_access", "window_glow", "assets/objects/door_01.jpg", family="institutional_horror", framing="closeup", crop=(0.08, 0.0, 0.92, 1.0), contrast=1.1, brightness=0.94, overlays=("door_window_glow", "seal_strips"), tags=("sealed", "access", "door", "window", "warning"), mood="ominous", semantic_pattern_fit=("sealed", "voice_anomaly"), entity_fit=("sealed_access", "door"), hook_strength_score=0.84, payoff_strength_score=0.92, setup_specificity_score=0.68, realism_score=0.84),

        AssetRecipe("map_blueprint_01", "map_blueprint", "missing_corridor_map", "assets/objects/document_03.jpg", overlays=("blueprint_grid", "missing_block"), tags=("map", "blueprint", "corridor"), mood="neutral", semantic_pattern_fit=("missing", "contradiction"), entity_fit=("map", "blueprint"), hook_strength_score=0.86, payoff_strength_score=0.88, realism_score=0.8),
        AssetRecipe("map_blueprint_02", "map_blueprint", "sealed_wing_blueprint", "assets/objects/document_01.jpg", overlays=("blueprint_grid", "seal_stamp"), tags=("map", "blueprint", "sealed"), mood="neutral", semantic_pattern_fit=("sealed", "contradiction"), entity_fit=("map", "blueprint"), hook_strength_score=0.84, payoff_strength_score=0.82, realism_score=0.78),

        AssetRecipe("evidence_surface_01", "evidence_surface", "desk_evidence", "assets/backgrounds/facts/facts_02.jpg", family="documentary_evidence", framing="closeup", crop=(0.18, 0.42, 0.88, 0.98), overlays=("evidence_marker",), tags=("evidence", "surface", "desk"), mood="clinical", semantic_pattern_fit=("missing", "contradiction"), entity_fit=("evidence_surface", "document"), hook_strength_score=0.62, payoff_strength_score=0.76, setup_specificity_score=0.44, realism_score=0.84),
        AssetRecipe("evidence_surface_02", "evidence_surface", "recording_surface", "assets/objects/document_02.jpg", family="documentary_evidence", framing="detail", crop=(0.18, 0.18, 0.88, 0.92), overlays=("evidence_marker",), tags=("evidence", "surface", "recording"), mood="neutral", semantic_pattern_fit=("voice_anomaly", "missing"), entity_fit=("evidence_surface", "recorder"), hook_strength_score=0.74, payoff_strength_score=0.86, setup_specificity_score=0.52, realism_score=0.88),
        AssetRecipe("evidence_surface_casefile_anomaly_03", "evidence_surface", "casefile_anomaly", "assets/imports/wikimedia_casefile_page4.jpg", family="documentary_evidence", framing="detail", crop=(0.18, 0.18, 0.86, 0.82), contrast=1.08, brightness=1.04, overlays=("evidence_marker", "highlight_box", "anomaly_circle"), tags=("evidence", "surface", "document", "anomaly"), mood="tense", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("evidence_surface", "document"), hook_strength_score=0.78, payoff_strength_score=0.94, setup_specificity_score=0.68, realism_score=0.95),

        AssetRecipe("investigative_interior_01", "investigative_interior", "lab_context", "assets/backgrounds/facts/facts_02.jpg", family="investigative_ambient", framing="wide", tags=("investigation", "interior", "lab"), mood="clinical", semantic_pattern_fit=("contradiction", "warning"), entity_fit=("investigative_interior", "room"), hook_strength_score=0.52, payoff_strength_score=0.56, setup_specificity_score=0.46, realism_score=0.82),
        AssetRecipe("investigative_interior_02", "investigative_interior", "archive_context", "assets/environments/room_02.jpg", family="investigative_ambient", framing="wide", tags=("investigation", "interior", "archive"), mood="tense", semantic_pattern_fit=("missing", "contradiction"), entity_fit=("investigative_interior", "room"), hook_strength_score=0.5, payoff_strength_score=0.54, setup_specificity_score=0.42, realism_score=0.74),
        AssetRecipe("investigative_interior_03", "investigative_interior", "records_archive", "assets/imports/wikimedia_records_shelves.jpg", family="investigative_ambient", framing="wide", crop=(0.12, 0.0, 0.88, 1.0), contrast=1.04, color=0.95, tags=("investigation", "interior", "archive", "records"), mood="clinical", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("investigative_interior", "archive"), hook_strength_score=0.72, payoff_strength_score=0.76, setup_specificity_score=0.9, realism_score=0.97),
        AssetRecipe("investigative_interior_records_desk_04", "investigative_interior", "records_desk", "assets/imports/wikimedia_archive_storage.jpg", family="investigative_ambient", framing="medium", crop=(0.1, 0.18, 0.9, 0.98), contrast=1.06, color=0.95, tags=("investigation", "interior", "records", "archive", "desk"), mood="clinical", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("investigative_interior", "archive"), hook_strength_score=0.74, payoff_strength_score=0.78, setup_specificity_score=0.94, realism_score=0.97),

        AssetRecipe("horror_interior_01", "horror_interior", "sealed_room", "assets/environments/room_01.jpg", family="institutional_horror", framing="wide", tags=("horror", "interior", "sealed"), mood="ominous", semantic_pattern_fit=("sealed", "voice_anomaly"), entity_fit=("horror_interior", "room"), hook_strength_score=0.54, payoff_strength_score=0.62, setup_specificity_score=0.62, realism_score=0.74),
        AssetRecipe("horror_interior_02", "horror_interior", "dark_corridor", "assets/backgrounds/horror/horror_03.jpg", family="institutional_horror", framing="medium", tags=("horror", "interior", "corridor"), mood="ominous", semantic_pattern_fit=("voice_anomaly", "missing"), entity_fit=("horror_interior", "corridor"), hook_strength_score=0.7, payoff_strength_score=0.78, setup_specificity_score=0.72, realism_score=0.8),
        AssetRecipe("horror_interior_threshold_03", "horror_interior", "threshold_room", "assets/environments/room_01.jpg", family="institutional_horror", framing="medium", crop=(0.04, 0.08, 0.94, 0.98), contrast=1.08, brightness=0.94, overlays=("door_window_glow",), tags=("horror", "interior", "sealed", "threshold", "whisper", "room"), mood="ominous", semantic_pattern_fit=("sealed", "voice_anomaly"), entity_fit=("horror_interior", "room"), hook_strength_score=0.76, payoff_strength_score=0.84, setup_specificity_score=0.96, realism_score=0.82),
        AssetRecipe("horror_interior_hospital_wing_04", "horror_interior", "hospital_wing", "assets/environments/room_02.jpg", family="institutional_horror", framing="wide", crop=(0.0, 0.02, 0.94, 0.98), contrast=1.07, brightness=0.92, overlays=("directional_marker",), tags=("horror", "interior", "hospital", "wing", "institutional", "sealed"), mood="ominous", semantic_pattern_fit=("sealed", "voice_anomaly"), entity_fit=("horror_interior", "room"), hook_strength_score=0.74, payoff_strength_score=0.82, setup_specificity_score=0.94, realism_score=0.8),

        AssetRecipe("institutional_space_01", "institutional_space", "public_walkway", "assets/backgrounds/horror/horror_02.jpg", family="investigative_ambient", framing="wide", tags=("institutional", "walkway", "public_space"), mood="tense", semantic_pattern_fit=("warning",), entity_fit=("institutional_space", "station"), hook_strength_score=0.46, payoff_strength_score=0.42, setup_specificity_score=0.28, realism_score=0.78),
        AssetRecipe("institutional_space_02", "institutional_space", "forensics_floor", "assets/backgrounds/facts/facts_02.jpg", family="investigative_ambient", framing="wide", crop=(0.0, 0.0, 1.0, 0.84), tags=("institutional", "lab", "public_space"), mood="clinical", semantic_pattern_fit=("contradiction",), entity_fit=("institutional_space", "room"), hook_strength_score=0.42, payoff_strength_score=0.4, setup_specificity_score=0.24, realism_score=0.8),
        AssetRecipe("institutional_space_03", "institutional_space", "station_walkway", "assets/backgrounds/horror/horror_02.jpg", family="investigative_ambient", framing="wide", crop=(0.04, 0.0, 0.96, 1.0), contrast=1.04, color=0.9, tags=("institutional", "station", "platform", "warning", "corridor"), mood="tense", semantic_pattern_fit=("warning", "voice_anomaly"), entity_fit=("institutional_space", "station"), hook_strength_score=0.68, payoff_strength_score=0.66, setup_specificity_score=0.74, realism_score=0.88),
        AssetRecipe("institutional_space_station_notice_04", "institutional_space", "station_notice", "assets/backgrounds/horror/horror_02.jpg", family="investigative_ambient", framing="wide", crop=(0.02, 0.08, 0.98, 0.98), contrast=1.06, color=0.92, overlays=("directional_marker",), tags=("institutional", "station", "platform", "notice", "corridor", "warning"), mood="tense", semantic_pattern_fit=("warning", "voice_anomaly"), entity_fit=("institutional_space", "station"), hook_strength_score=0.76, payoff_strength_score=0.74, setup_specificity_score=0.98, realism_score=0.88),
        AssetRecipe("institutional_space_archive_hall_05", "institutional_space", "archive_hall", "assets/imports/wikimedia_archive_storage.jpg", family="investigative_ambient", framing="wide", crop=(0.0, 0.0, 0.9, 1.0), contrast=1.04, color=0.94, tags=("institutional", "archive", "records", "hall"), mood="clinical", semantic_pattern_fit=("contradiction", "missing"), entity_fit=("institutional_space", "archive"), hook_strength_score=0.68, payoff_strength_score=0.72, setup_specificity_score=0.94, realism_score=0.97)
    ]


def load_image(source: str) -> Image.Image:
    path = ROOT / source
    with Image.open(path) as image:
        return image.convert("RGB")


def cover_crop(image: Image.Image, target: tuple[int, int] = (1080, 1920)) -> Image.Image:
    target_w, target_h = target
    source_w, source_h = image.size
    scale = max(target_w / source_w, target_h / source_h)
    resized = image.resize((int(source_w * scale), int(source_h * scale)))
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def crop_percent(image: Image.Image, crop: tuple[float, float, float, float]) -> Image.Image:
    width, height = image.size
    left = int(width * crop[0])
    top = int(height * crop[1])
    right = int(width * crop[2])
    bottom = int(height * crop[3])
    return image.crop((left, top, right, bottom))


def apply_overlay(image: Image.Image, overlay: str) -> Image.Image:
    result = image.copy().convert("RGBA")
    draw = ImageDraw.Draw(result, "RGBA")
    width, height = result.size
    if overlay == "warning_panel":
        draw.rounded_rectangle((int(width * 0.22), int(height * 0.18), int(width * 0.78), int(height * 0.68)), radius=18, fill=(34, 42, 52, 180), outline=(222, 228, 232, 220), width=6)
        draw.rectangle((int(width * 0.3), int(height * 0.3), int(width * 0.7), int(height * 0.42)), fill=(244, 104, 44, 220))
        draw.polygon([(int(width * 0.34), int(height * 0.23)), (int(width * 0.38), int(height * 0.29)), (int(width * 0.30), int(height * 0.29))], fill=(248, 210, 60, 230))
    elif overlay == "signal_wave":
        points = []
        for idx in range(10):
            x = int(width * 0.1 + idx * width * 0.08)
            y = int(height * (0.22 + (0.02 if idx % 2 == 0 else -0.01)))
            points.append((x, y))
        draw.line(points, fill=(126, 246, 238, 210), width=5)
    elif overlay == "monitor_panel":
        draw.rounded_rectangle((int(width * 0.16), int(height * 0.22), int(width * 0.84), int(height * 0.78)), radius=24, fill=(20, 26, 34, 150), outline=(196, 206, 214, 220), width=6)
        draw.rectangle((int(width * 0.26), int(height * 0.3), int(width * 0.74), int(height * 0.46)), fill=(76, 226, 206, 180))
    elif overlay == "warning_symbol":
        draw.polygon([(int(width * 0.48), int(height * 0.34)), (int(width * 0.54), int(height * 0.46)), (int(width * 0.42), int(height * 0.46))], fill=(248, 214, 72, 230))
    elif overlay == "intercom_panel":
        draw.rounded_rectangle((int(width * 0.22), int(height * 0.18), int(width * 0.78), int(height * 0.82)), radius=18, fill=(42, 48, 58, 165), outline=(176, 188, 198, 220), width=6)
        for row in range(4):
            y = int(height * 0.42) + row * 50
            draw.line((int(width * 0.34), y, int(width * 0.66), y), fill=(16, 18, 22, 220), width=8)
    elif overlay == "seal_strips":
        draw.line((int(width * 0.12), int(height * 0.28), int(width * 0.88), int(height * 0.7)), fill=(224, 198, 84, 190), width=24)
        draw.line((int(width * 0.12), int(height * 0.7), int(width * 0.88), int(height * 0.28)), fill=(224, 198, 84, 190), width=24)
    elif overlay == "blueprint_grid":
        for x in range(0, width, 120):
            draw.line((x, 0, x, height), fill=(64, 124, 188, 72), width=2)
        for y in range(0, height, 120):
            draw.line((0, y, width, y), fill=(64, 124, 188, 72), width=2)
    elif overlay == "missing_block":
        draw.rectangle((int(width * 0.28), int(height * 0.36), int(width * 0.78), int(height * 0.48)), fill=(14, 18, 24, 220))
    elif overlay == "seal_stamp":
        draw.rectangle((int(width * 0.08), int(height * 0.08), int(width * 0.34), int(height * 0.16)), outline=(196, 42, 38, 220), width=6)
    elif overlay == "evidence_marker":
        draw.rectangle((int(width * 0.06), int(height * 0.8), int(width * 0.26), int(height * 0.94)), fill=(224, 198, 82, 220), outline=(42, 28, 18, 220), width=4)
    elif overlay == "warning_led":
        draw.ellipse((int(width * 0.68), int(height * 0.08), int(width * 0.82), int(height * 0.17)), fill=(232, 96, 44, 210), outline=(248, 214, 136, 220), width=4)
        draw.rectangle((int(width * 0.1), int(height * 0.83), int(width * 0.9), int(height * 0.92)), fill=(26, 28, 32, 180))
        draw.rectangle((int(width * 0.12), int(height * 0.85), int(width * 0.54), int(height * 0.9)), fill=(236, 118, 56, 210))
    elif overlay == "redaction_bar":
        draw.rectangle((int(width * 0.18), int(height * 0.34), int(width * 0.82), int(height * 0.4)), fill=(18, 18, 20, 220))
        draw.rectangle((int(width * 0.22), int(height * 0.58), int(width * 0.76), int(height * 0.63)), fill=(18, 18, 20, 220))
    elif overlay == "highlight_box":
        draw.rounded_rectangle((int(width * 0.22), int(height * 0.2), int(width * 0.82), int(height * 0.34)), radius=14, outline=(246, 192, 68, 220), width=8)
    elif overlay == "anomaly_circle":
        draw.ellipse((int(width * 0.48), int(height * 0.42), int(width * 0.76), int(height * 0.65)), outline=(212, 72, 56, 220), width=10)
    elif overlay == "security_lock":
        draw.rounded_rectangle((int(width * 0.4), int(height * 0.28), int(width * 0.66), int(height * 0.56)), radius=12, outline=(228, 196, 92, 220), width=8)
        draw.arc((int(width * 0.44), int(height * 0.16), int(width * 0.62), int(height * 0.34)), start=180, end=360, fill=(228, 196, 92, 220), width=10)
    elif overlay == "door_window_glow":
        draw.rectangle((int(width * 0.58), int(height * 0.18), int(width * 0.82), int(height * 0.42)), fill=(140, 182, 176, 120))
    elif overlay == "directional_marker":
        draw.rectangle((int(width * 0.08), int(height * 0.18), int(width * 0.34), int(height * 0.28)), fill=(28, 34, 40, 180))
        draw.polygon([(int(width * 0.3), int(height * 0.23)), (int(width * 0.22), int(height * 0.18)), (int(width * 0.22), int(height * 0.28))], fill=(236, 194, 88, 220))
    return result.convert("RGB")


def process_recipe(recipe: AssetRecipe) -> tuple[Path, dict[str, Any]]:
    image = load_image(recipe.source)
    if min(image.size) < 700:
        raise ValueError(f"Asset source too small for production curation: {recipe.source} -> {image.size}")
    image = crop_percent(image, recipe.crop)
    if recipe.flip:
        image = image.transpose(Image.FLIP_LEFT_RIGHT)
    image = cover_crop(image)
    for overlay in recipe.overlays:
        image = apply_overlay(image, overlay)
    image = ImageEnhance.Brightness(image).enhance(recipe.brightness)
    image = ImageEnhance.Contrast(image).enhance(recipe.contrast)
    image = ImageEnhance.Color(image).enhance(recipe.color)
    if recipe.blur > 0:
        image = image.filter(ImageFilter.GaussianBlur(radius=recipe.blur))
    target_dir = ASSETS_DIR / recipe.category
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{recipe.name}.jpg"
    image.save(target, format="JPEG", quality=92)
    entry = {
        "path": str(target.relative_to(ROOT)).replace("\\", "/"),
        "category": recipe.category,
        "subtype": recipe.subtype,
        "family": recipe.family or recipe.category,
        "framing": recipe.framing,
        "tags": list(recipe.tags),
        "mood": recipe.mood,
        "semantic_pattern_fit": list(recipe.semantic_pattern_fit),
        "entity_fit": list(recipe.entity_fit),
        "hook_strength_score": recipe.hook_strength_score,
        "payoff_strength_score": recipe.payoff_strength_score,
        "setup_specificity_score": recipe.setup_specificity_score,
        "realism_score": recipe.realism_score,
        "source_type": recipe.source_type,
        "resolution": [1080, 1920],
        "strength": round((recipe.hook_strength_score + recipe.payoff_strength_score + recipe.realism_score) / 3.0, 3),
        "genericity": round(max(0.05, 1.0 - ((recipe.hook_strength_score + recipe.payoff_strength_score) / 2.0)), 3),
    }
    return target, entry


def build_default_library() -> dict[str, Any]:
    recipes = default_recipes()
    generated: list[dict[str, Any]] = []
    for recipe in recipes:
        target, entry = process_recipe(recipe)
        generated.append({"recipe": recipe.name, "path": str(target), "catalog_entry": entry})
    catalog_entries = [item["catalog_entry"] for item in generated]
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(json.dumps(catalog_entries, indent=2), encoding="utf-8")

    category_counts: dict[str, int] = {}
    for entry in catalog_entries:
        category_counts[entry["category"]] = category_counts.get(entry["category"], 0) + 1

    summary = {
        "generated_count": len(generated),
        "categories": category_counts,
        "catalog_path": str(CATALOG_PATH),
        "asset_root": str(ASSETS_DIR),
        "recipes": [{"name": item["recipe"], "path": item["path"]} for item in generated],
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def import_from_url(*, url: str, target_name: str) -> Path:
    target = ASSETS_DIR / "imports" / target_name
    target.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        target.write_bytes(response.content)
    return target


def ingest_from_source(
    *,
    source: str,
    query: str,
    category: str,
    subtype: str,
    tags: list[str],
    limit: int,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    normalized = source.strip().lower()
    if normalized == "pexels":
        ingestor = PexelsIngestor()
    elif normalized == "unsplash":
        ingestor = UnsplashIngestor()
    elif normalized == "pixabay":
        ingestor = PixabayIngestor()
    else:
        raise ValueError(f"unsupported source: {source}")
    return ingestor.ingest_query(
        query=query,
        category=category,
        subtype=subtype,
        tags=tags,
        limit=limit,
        metadata=metadata or {},
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-default-library", action="store_true")
    parser.add_argument("--import-url", type=str, default="")
    parser.add_argument("--target-name", type=str, default="")
    parser.add_argument("--source", type=str, default="")
    parser.add_argument("--query", type=str, default="")
    parser.add_argument("--category", type=str, default="")
    parser.add_argument("--subtype", type=str, default="")
    parser.add_argument("--tags", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    if args.import_url:
        if not args.target_name:
            raise SystemExit("--target-name is required with --import-url")
        path = import_from_url(url=args.import_url, target_name=args.target_name)
        print(json.dumps({"imported": str(path)}, indent=2))
        return

    if args.source:
        if not args.query or not args.category or not args.subtype:
            raise SystemExit("--source requires --query, --category and --subtype")
        rows = ingest_from_source(
            source=args.source,
            query=args.query,
            category=args.category,
            subtype=args.subtype,
            tags=list(args.tags),
            limit=max(1, args.limit),
        )
        print(json.dumps({"source": args.source, "query": args.query, "imported": rows}, indent=2))
        return

    summary = build_default_library()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
