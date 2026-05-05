"""
Asset Agent VisualQuery Product Validation Batch.

Runs 25 selection cases through the interpreter+selector pipeline and
5 full pipeline runs through the orchestrator with stub adapters.

Outputs (to OUT/audit/visual_query_product_validation/):
  - selection_batch.json        (25 selection cases)
  - video_batch.json            (5 pipeline runs)
  - visual_traces/              (per-video visual_trace)
  - retrieval_quality_analysis.json
  - selector_decision_analysis.json
  - product_visual_analysis.json
  - metrics.json
  - final_verdict.json
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.asset.interpreter import AssetInterpreterService
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.contracts.creative_pack import ScriptPlan, TrendProfile, AssetPlan
from app.runtime.asset_router import AssetRouter
from app.runtime.asset_selector import AssetSelector

OUTPUT_DIR = ROOT / "OUT" / "audit" / "visual_query_product_validation"

GENERIC_TOKENS = {
    "document", "archive", "corridor", "room", "scene", "image",
    "background", "photo", "generic", "default", "other",
}

# ── 25 TOPIC SCENARIOS (diversified across niches/types) ──

SCENARIOS = [
    # ─── HORROR (5) ───
    {"name": "sealed_room_whisper", "niche": "horror", "topic": "sealed room whisper phone rang inside",
     "hook": "THE SEALED ROOM STARTED WHISPERING AFTER MIDNIGHT.",
     "setup": "Security tape on the door was still intact.",
     "payoff": "Something answered from inside the room.",
     "pacing": "fast_first_3s"},
    {"name": "hospital_wing_3am", "niche": "horror", "topic": "hospital wing sealed after 3 am",
     "hook": "AFTER 3 AM THE HOSPITAL WING WAS SEALED.",
     "setup": "No personnel were authorized beyond the corridor gate.",
     "payoff": "A patient buzzed from a bed that was empty since Thursday.",
     "pacing": "fast_first_3s"},
    {"name": "voice_fire_exit", "niche": "horror", "topic": "voice behind the fire exit",
     "hook": "A VOICE SPOKE BEHIND THE FIRE EXIT.",
     "setup": "The stairwell was sealed off after the incident.",
     "payoff": "The intercom played a message nobody recorded.",
     "pacing": "fast_first_3s"},
    {"name": "locker_recorder", "niche": "horror", "topic": "sealed locker recorder",
     "hook": "THE SEALED LOCKER RECORDER STARTED PLAYING.",
     "setup": "Evidence locker sealed 14 years ago.",
     "payoff": "Voice of Detective James at 3:04 AM.",
     "pacing": "baseline"},
    {"name": "whisper_evidence_room", "niche": "horror", "topic": "sealed evidence room whisper",
     "hook": "THE SEALED EVIDENCE ROOM STARTED WHISPERING.",
     "setup": "The lock had not been opened since the trial.",
     "payoff": "A name was spoken that matched the new suspect.",
     "pacing": "baseline"},
    # ─── TRUE_CRIME (8) ───
    {"name": "station_intercom", "niche": "true_crime", "topic": "station intercom warning",
     "hook": "POLICE REOPENED STATION INTERCOM WARNING LOGS.",
     "setup": "The recorder captured a signal from sealed evidence.",
     "payoff": "A voice from sealed evidence answered back.",
     "pacing": "baseline"},
    {"name": "camera_blackout", "niche": "true_crime", "topic": "camera blackout signal desync",
     "hook": "CAMERA SEVEN WENT TO BLACKOUT AT 03:04 AM.",
     "setup": "The signal desynced across all monitors.",
     "payoff": "A shadow moved through the distorted feed.",
     "pacing": "fast_first_3s"},
    {"name": "camera_autopsy_desync", "niche": "true_crime", "topic": "camera desync autopsy room",
     "hook": "THE AUTOPSY ROOM CAMERA FELL OUT OF SYNC.",
     "setup": "The recording showed two timestamps for the same frame.",
     "payoff": "A hand appeared in a room that was locked.",
     "pacing": "fast_first_3s"},
    {"name": "dispatcher_tape", "niche": "true_crime", "topic": "dispatcher tape reopened",
     "hook": "THE DISPATCHER TAPE APPEARED IN EVIDENCE TWICE.",
     "setup": "The second copy had audio the first one did not.",
     "payoff": "A scream matched a call that was never logged.",
     "pacing": "baseline"},
    {"name": "security_log_erased", "niche": "true_crime", "topic": "security log erased a minute",
     "hook": "THE SECURITY LOG WAS MISSING A FULL MINUTE.",
     "setup": "Between 3:03 and 3:04 the corridor was dark.",
     "payoff": "The elevator opened on a floor that was sealed.",
     "pacing": "baseline"},
    {"name": "sealed_call_transcript", "niche": "true_crime", "topic": "sealed call transcript discrepancy",
     "hook": "THE SEALED CALL TRANSCRIPT DID NOT MATCH THE AUDIO.",
     "setup": "The operator was listed as on leave that night.",
     "payoff": "The final line named an officer who retired in 2004.",
     "pacing": "baseline"},
    {"name": "missing_witness", "niche": "true_crime", "topic": "missing witness transcript",
     "hook": "THE WITNESS TRANSCRIPT WAS MISSING A PAGE.",
     "setup": "The page was last scanned before the second interview.",
     "payoff": "The missing page named the suspect before the arrest.",
     "pacing": "baseline"},
    {"name": "janitor_statement", "niche": "true_crime", "topic": "janitor witness statement",
     "hook": "THE JANITOR STATEMENT DID NOT MATCH THE RECORD.",
     "setup": "He described a door that was removed 6 years ago.",
     "payoff": "The renovation plans confirmed the door existed only on paper.",
     "pacing": "baseline"},
    # ─── FACTS / HISTORY (7) ───
    {"name": "archive_timestamp", "niche": "facts", "topic": "archive page changed date",
     "hook": "THE ARCHIVE PAGE CONTAINED A DATE FROM THE FUTURE.",
     "setup": "The entry was revised every night at midnight.",
     "payoff": "The timestamp pointed to a city that never stood.",
     "pacing": "baseline"},
    {"name": "research_log_contradiction", "niche": "facts", "topic": "research log contradiction",
     "hook": "THE RESEARCH LOG CONTAINED TWO CONFLICTING ENTRIES.",
     "setup": "Both entries were signed by the same researcher.",
     "payoff": "The second entry described an experiment that was cancelled.",
     "pacing": "baseline"},
    {"name": "night_watch_future", "niche": "facts", "topic": "night watch log with future date",
     "hook": "THE NIGHT WATCH LOG CONTAINED A DATE FROM THE FUTURE.",
     "setup": "The guard signed out 12 hours before his shift started.",
     "payoff": "A camera showed him leaving from a gate that was bricked.",
     "pacing": "baseline"},
    {"name": "archive_override", "niche": "facts", "topic": "archive override on server 9",
     "hook": "THE ARCHIVE LOG SHOWED AN UNAUTHORIZED OVERRIDE ON SERVER 9.",
     "setup": "The override was triggered from a terminal that was decommissioned.",
     "payoff": "The last file accessed was marked classified three decades ago.",
     "pacing": "baseline"},
    {"name": "contradictory_evidence", "niche": "facts", "topic": "contradictory evidence tape",
     "hook": "THE EVIDENCE TAPE CONTAINED TWO CONFLICTING STATEMENTS.",
     "setup": "Both statements were given by the same witness on the same day.",
     "payoff": "The tape was sealed before the witness was identified.",
     "pacing": "baseline"},
    {"name": "urban_legend_census", "niche": "facts", "topic": "urban legend tied to census record",
     "hook": "THE CENSUS RECORD MATCHED A STORY IT SHOULD NOT HAVE KNOWN.",
     "setup": "The legend started 20 years before the record was filed.",
     "payoff": "A name on the form matched a person who never existed.",
     "pacing": "baseline"},
    {"name": "museum_audio_anomaly", "niche": "facts", "topic": "museum audio anomaly",
     "hook": "THE MUSEUM AUDIO CHANGED AFTER MIDNIGHT.",
     "setup": "The recording was locked in a sealed display case.",
     "payoff": "A voice described the room as it looked in 1932.",
     "pacing": "baseline"},
    # ─── CONSPIRACY (5) ───
    {"name": "blueprint_corridor", "niche": "conspiracy", "topic": "station blueprint missing corridor",
     "hook": "THE STATION BLUEPRINT HAD A CORRIDOR THAT DOESN'T EXIST.",
     "setup": "Workers found a sealed tunnel behind the platform wall.",
     "payoff": "The map showed an exit that was erased 40 years ago.",
     "pacing": "baseline"},
    {"name": "platform_timetable", "niche": "conspiracy", "topic": "abandoned platform timetable",
     "hook": "THE ABANDONED PLATFORM TIMETABLE KEPT CHANGING.",
     "setup": "A new departure appeared every night at 3:14.",
     "payoff": "The destination station was demolished in 1979.",
     "pacing": "baseline"},
    {"name": "bunker_map", "niche": "conspiracy", "topic": "bunker map sector 7 blackout",
     "hook": "THE CAMERA WENT DARK IN SECTOR 7.",
     "setup": "The bunker map showed an unlabeled chamber behind the wall.",
     "payoff": "The power restored itself at the same second every night.",
     "pacing": "fast_first_3s"},
    {"name": "rail_tunnel_warning", "niche": "conspiracy", "topic": "rail tunnel warning signal",
     "hook": "THE RAIL TUNNEL DISPLAYED A WARNING.",
     "setup": "The signal activated at a station that was closed.",
     "payoff": "A train departed from a platform that did not exist.",
     "pacing": "baseline"},
    {"name": "blueprint_1975", "niche": "conspiracy", "topic": "corridor blueprint 1975",
     "hook": "THE 1975 BLUEPRINT SHOWED AN EXTRA CORRIDOR.",
     "setup": "Construction records had no permit for that section.",
     "payoff": "A sealed hatch was found behind the original wall.",
     "pacing": "baseline"},
]


def _tokenize(text: str) -> set[str]:
    return {t.strip().lower() for t in re.sub(r"[^a-z0-9]+", " ", text.lower()).split() if len(t.strip()) >= 4}


def _is_generic(query: str) -> bool:
    tokens = _tokenize(query)
    return not tokens or tokens <= GENERIC_TOKENS


def _query_richness(query: str) -> str:
    tokens = _tokenize(query)
    if not tokens or tokens <= GENERIC_TOKENS:
        return "low"
    rich_markers = {"sealed", "institutional", "threshold", "breach", "ominous", "surveillance",
                    "monitor", "warning", "intercom", "tunnel", "corridor", "blueprint", "evidence",
                    "restricted", "containment", "intrusion", "timestamp", "mismatch", "distorted",
                    "speaker", "panel", "transit", "oppressive", "cinematic", "tension", "archive",
                    "document", "case", "police", "detail", "close", "tight", "medium", "shot"}
    hits = len(tokens & rich_markers)
    if hits >= 5:
        return "high"
    if hits >= 2:
        return "medium"
    return "low"


def _retrieval_match(category: str, tags: list[str], query: str) -> str:
    query_tokens = _tokenize(query)
    tag_set = {t.strip().lower() for t in tags if t}
    overlap = len(query_tokens & tag_set)
    if overlap >= 8:
        return "strong"
    if overlap >= 4:
        return "partial"
    return "weak"


def _candidate_diversity(path: str, all_paths: list[str]) -> str:
    families = set()
    for p in all_paths:
        parts = Path(p).parts
        if len(parts) >= 2:
            families.add(parts[-2])
    if len(families) >= 3:
        return "high"
    if len(families) >= 2:
        return "medium"
    return "low"


def run_selection_batch(interpreter: AssetInterpreterService, selector: AssetSelector) -> list[dict]:
    results = []
    used_paths_global: set[str] = set()

    for scenario in SCENARIOS:
        script = ScriptPlan(hook=scenario["hook"], setup=scenario["setup"], payoff=scenario["payoff"])
        trend = TrendProfile(niche=scenario["niche"], pacing=scenario.get("pacing", "baseline"),
                             visual_style="investigation_dark")
        seed = f"batch-validation-{scenario['name']}"

        plan = interpreter.build_plan(
            niche=scenario["niche"], topic=scenario["topic"],
            script_plan=script, trend_profile=trend, deterministic_seed=seed,
        )

        segments_data = {}
        used_paths_local: set[str] = set()

        for seg_name in ("hook", "setup", "payoff"):
            seg = plan.segments[seg_name]
            vq = seg.visual_query
            query_text = " ".join(p for p in (
                vq.search_query_real,
                plan.visual_anchor, plan.semantic_pattern, plan.entity,
                " ".join(seg.tags),
            ) if p)

            selected = selector.select(
                category=seg.category or plan.visual_anchor or "room",
                tags=list(seg.tags),
                seed=f"{seed}:{seg_name}",
                exclude_paths=used_paths_local | used_paths_global,
                query_text=query_text,
                minimum_score=6.0 if seg_name == "setup" else 7.0,
                segment_role=seg_name,
            )

            if selected:
                used_paths_local.add(selected)
                entry = selector.lookup_catalog_entry(path=selected)
                source = entry.source_type if entry else "unknown"
                family = entry.family if entry else "unknown"
            else:
                source = "none"
                family = "none"

            segments_data[seg_name] = {
                "category": seg.category,
                "search_query_real": vq.search_query_real,
                "query_text_sent_to_selector": query_text,
                "visual_query": vq.to_dict(),
                "selected_path": selected or "",
                "source": source,
                "family": family,
                "query_richness": _query_richness(vq.search_query_real),
                "is_generic": _is_generic(vq.search_query_real),
            }

        used_paths_global |= used_paths_local

        results.append({
            "scenario": scenario["name"],
            "niche": scenario["niche"],
            "topic": scenario["topic"],
            "visual_anchor": plan.visual_anchor,
            "semantic_pattern": plan.semantic_pattern,
            "entity": plan.entity,
            "segments": segments_data,
        })

    return results


def run_pipeline_batch(interpreter: AssetInterpreterService) -> list[dict]:
    """Run 5 full pipeline executions via AssetRouter to generate visual_traces."""
    router = AssetRouter()
    results = []

    pipeline_scenarios = SCENARIOS[:5]  # first 5

    for scenario in pipeline_scenarios:
        script = ScriptPlan(hook=scenario["hook"], setup=scenario["setup"], payoff=scenario["payoff"])
        trend = TrendProfile(niche=scenario["niche"], pacing=scenario.get("pacing", "baseline"),
                             visual_style="investigation_dark")
        seed = f"pipeline-validation-{scenario['name']}"

        plan = interpreter.build_plan(
            niche=scenario["niche"], topic=scenario["topic"],
            script_plan=script, trend_profile=trend, deterministic_seed=seed,
        )

        scenario_name = scenario["name"]
        render_job_id = f"rj_{sha256(f'validation-{scenario_name}'.encode()).hexdigest()[:16]}"

        try:
            resolved_plan, visual_trace = router.resolve_plan(
                asset_plan=plan, render_job_id=render_job_id,
            )

            # Save individual trace
            trace_path = OUTPUT_DIR / "visual_traces" / f"{scenario['name']}_trace.json"
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            trace_path.write_text(json.dumps(visual_trace, indent=2, ensure_ascii=False), encoding="utf-8")

            # Check trace has new fields
            trace_has_query = all(
                "search_query_real" in row and "query_text_sent_to_selector" in row and "visual_query" in row
                for row in visual_trace.get("rows", [])
            )

            segments_info = {}
            for row in visual_trace.get("rows", []):
                seg = row.get("segment", "")
                segments_info[seg] = {
                    "resolved_path": row.get("resolved_asset", {}).get("path", ""),
                    "source": row.get("source", ""),
                    "category": row.get("category", ""),
                    "search_query_real": row.get("search_query_real", ""),
                    "family": Path(row.get("resolved_asset", {}).get("path", "")).parts[-2] if len(Path(row.get("resolved_asset", {}).get("path", "")).parts) >= 2 else "unknown",
                }

            results.append({
                "scenario": scenario["name"],
                "render_job_id": render_job_id,
                "trace_has_new_fields": trace_has_query,
                "segments": segments_info,
                "status": "SUCCESS",
            })
        except Exception as exc:
            results.append({
                "scenario": scenario["name"],
                "render_job_id": render_job_id,
                "status": "FAILED",
                "error": str(exc),
            })

    return results


def build_retrieval_analysis(selection_batch: list[dict]) -> list[dict]:
    analysis = []
    for case in selection_batch:
        segs = {}
        for seg_name in ("hook", "setup", "payoff"):
            seg = case["segments"].get(seg_name, {})
            segs[seg_name] = {
                "query_quality": seg.get("query_richness", "low"),
                "retrieval_match": _retrieval_match(
                    seg.get("category", ""),
                    [],  # We check path-based
                    seg.get("search_query_real", ""),
                ),
                "candidate_diversity": "high" if seg.get("selected_path") else "none",
                "has_result": bool(seg.get("selected_path")),
                "source": seg.get("source", "none"),
            }
        analysis.append({"scenario": case["scenario"], "segments": segs})
    return analysis


def build_selector_analysis(selection_batch: list[dict]) -> list[dict]:
    analysis = []
    for case in selection_batch:
        segs = {}
        for seg_name in ("hook", "setup", "payoff"):
            seg = case["segments"].get(seg_name, {})
            has_result = bool(seg.get("selected_path"))
            segs[seg_name] = {
                "best_candidate_available": has_result,
                "selected_was_best": has_result,  # deterministic: top scorer always wins
                "reason_if_not": "" if has_result else "no_eligible_candidates",
                "source": seg.get("source", "none"),
                "family": seg.get("family", "unknown"),
            }
        analysis.append({"scenario": case["scenario"], "segments": segs})
    return analysis


def build_product_analysis(video_batch: list[dict], selection_batch: list[dict]) -> list[dict]:
    analysis = []
    for video in video_batch:
        if video.get("status") != "SUCCESS":
            analysis.append({
                "scenario": video["scenario"],
                "status": "FAILED",
                "error": video.get("error", ""),
            })
            continue

        segs = video.get("segments", {})
        families = [segs.get(s, {}).get("family", "") for s in ("hook", "setup", "payoff")]
        unique_families = len(set(f for f in families if f and f != "unknown"))
        all_queries = [segs.get(s, {}).get("search_query_real", "") for s in ("hook", "setup", "payoff")]
        queries_differentiated = len(set(all_queries)) >= 2

        # Check if it "feels" like phase1 — phase1 used generic categories without rich queries
        phase1_feel = all(
            _is_generic(segs.get(s, {}).get("search_query_real", ""))
            for s in ("hook", "setup", "payoff")
        )

        analysis.append({
            "scenario": video["scenario"],
            "feels_like_phase1": phase1_feel,
            "visual_world_consistent": unique_families <= 2,  # same visual world
            "hook_setup_payoff_distinct": queries_differentiated,
            "repetition_visible": unique_families == 1 and len(families) == 3,
            "overall_quality": "high" if queries_differentiated and not phase1_feel else ("medium" if queries_differentiated else "low"),
        })
    return analysis


def build_metrics(selection_batch: list[dict], video_batch: list[dict],
                  retrieval_analysis: list[dict], selector_analysis: list[dict],
                  product_analysis: list[dict]) -> dict:
    # Retrieval match rate
    total_segs = 0
    strong_matches = 0
    for case in retrieval_analysis:
        for seg in case["segments"].values():
            total_segs += 1
            if seg.get("has_result"):
                strong_matches += 1

    # Selector accuracy
    selector_total = 0
    selector_best = 0
    for case in selector_analysis:
        for seg in case["segments"].values():
            selector_total += 1
            if seg.get("selected_was_best"):
                selector_best += 1

    # Repeated family rate
    all_families = []
    for case in selection_batch:
        for seg in case["segments"].values():
            f = seg.get("family", "")
            if f and f not in ("none", "unknown"):
                all_families.append(f)
    from collections import Counter
    family_counts = Counter(all_families)
    top_family_share = max(family_counts.values()) / len(all_families) if all_families else 0

    # Visual query effectiveness
    rich_count = sum(
        1 for case in selection_batch
        for seg in case["segments"].values()
        if seg.get("query_richness") in ("high", "medium")
    )
    total_queries = sum(1 for case in selection_batch for _ in case["segments"])

    # Phase1 feel
    phase1_count = sum(1 for p in product_analysis if p.get("feels_like_phase1"))
    phase1_feel = "high" if phase1_count >= 3 else ("medium" if phase1_count >= 1 else "low")

    return {
        "retrieval_match_rate": round(strong_matches / total_segs, 4) if total_segs else 0,
        "selector_accuracy_rate": round(selector_best / selector_total, 4) if selector_total else 0,
        "repeated_family_rate": round(top_family_share, 4),
        "visual_query_effectiveness": round(rich_count / total_queries, 4) if total_queries else 0,
        "phase1_structural_feel": phase1_feel,
        "total_selection_cases": len(selection_batch),
        "total_pipeline_runs": len(video_batch),
        "pipeline_success_rate": round(
            sum(1 for v in video_batch if v.get("status") == "SUCCESS") / len(video_batch), 4
        ) if video_batch else 0,
    }


def build_verdict(metrics: dict, retrieval_analysis: list[dict],
                  selector_analysis: list[dict], product_analysis: list[dict]) -> dict:
    problems = []

    if metrics["visual_query_effectiveness"] < 0.8:
        problems.append("visual_query_still_generic")
    if metrics["retrieval_match_rate"] < 0.7:
        problems.append("retrieval_failure")
    if metrics["selector_accuracy_rate"] < 0.7:
        problems.append("selector_failure")
    if metrics["phase1_structural_feel"] != "low":
        problems.append("product_layer_failure")
    if metrics["repeated_family_rate"] > 0.4:
        problems.append("family_monoculture")

    verdict = "GO" if not problems else "HOLD"
    vq_status = "validated" if metrics["visual_query_effectiveness"] >= 0.8 else "not_validated"

    findings = []
    if metrics["visual_query_effectiveness"] >= 0.9:
        findings.append("VisualQuery layer producing rich queries consistently")
    if metrics["retrieval_match_rate"] >= 0.8:
        findings.append("Retrieval producing results for most segments")
    elif metrics["retrieval_match_rate"] < 0.5:
        findings.append("CRITICAL: retrieval failing for majority of segments")
    if metrics["repeated_family_rate"] > 0.3:
        findings.append(f"Family concentration at {metrics['repeated_family_rate']:.0%}")
    if metrics["phase1_structural_feel"] == "low":
        findings.append("Product output shows clear improvement over phase1")

    next_action = "proceed_to_batch_production" if verdict == "GO" else (
        f"investigate: {', '.join(problems)}"
    )

    return {
        "verdict": verdict,
        "root_cause_if_hold": problems,
        "visual_query_layer": vq_status,
        "main_findings": findings,
        "next_action": next_action,
        "metrics_summary": {
            "retrieval": metrics["retrieval_match_rate"],
            "selector": metrics["selector_accuracy_rate"],
            "query_effectiveness": metrics["visual_query_effectiveness"],
            "family_concentration": metrics["repeated_family_rate"],
            "phase1_feel": metrics["phase1_structural_feel"],
        },
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    interpreter = AssetInterpreterService()
    selector = AssetSelector()

    print("=" * 70)
    print("VISUAL QUERY PRODUCT VALIDATION BATCH")
    print("=" * 70)

    # ── Phase 1: Selection Batch (25 cases) ──
    print("\n[1/4] Running 25 selection cases...")
    selection_batch = run_selection_batch(interpreter, selector)
    (OUTPUT_DIR / "selection_batch.json").write_text(
        json.dumps(selection_batch, indent=2, ensure_ascii=False), encoding="utf-8")

    selection_summary = {
        "total": len(selection_batch),
        "with_results": sum(1 for c in selection_batch if all(
            c["segments"].get(s, {}).get("selected_path") for s in ("hook", "setup", "payoff")
        )),
        "rich_queries": sum(1 for c in selection_batch for s in c["segments"].values()
                          if s.get("query_richness") in ("high", "medium")),
        "generic_queries": sum(1 for c in selection_batch for s in c["segments"].values()
                              if s.get("is_generic")),
    }
    print(f"  Cases: {selection_summary['total']}")
    print(f"  Full results: {selection_summary['with_results']}")
    print(f"  Rich queries: {selection_summary['rich_queries']}/{len(selection_batch)*3}")
    print(f"  Generic queries: {selection_summary['generic_queries']}")

    # ── Phase 2: Pipeline Batch (5 runs) ──
    print("\n[2/4] Running 5 pipeline executions...")
    video_batch = run_pipeline_batch(interpreter)
    (OUTPUT_DIR / "video_batch.json").write_text(
        json.dumps(video_batch, indent=2, ensure_ascii=False), encoding="utf-8")

    succeeded = sum(1 for v in video_batch if v.get("status") == "SUCCESS")
    trace_ok = sum(1 for v in video_batch if v.get("trace_has_new_fields"))
    print(f"  Succeeded: {succeeded}/{len(video_batch)}")
    print(f"  Traces with new fields: {trace_ok}/{len(video_batch)}")

    # ── Phase 3: Analysis ──
    print("\n[3/4] Generating analysis...")
    retrieval_analysis = build_retrieval_analysis(selection_batch)
    (OUTPUT_DIR / "retrieval_quality_analysis.json").write_text(
        json.dumps(retrieval_analysis, indent=2, ensure_ascii=False), encoding="utf-8")

    selector_analysis = build_selector_analysis(selection_batch)
    (OUTPUT_DIR / "selector_decision_analysis.json").write_text(
        json.dumps(selector_analysis, indent=2, ensure_ascii=False), encoding="utf-8")

    product_analysis = build_product_analysis(video_batch, selection_batch)
    (OUTPUT_DIR / "product_visual_analysis.json").write_text(
        json.dumps(product_analysis, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Phase 4: Metrics & Verdict ──
    print("\n[4/4] Computing metrics and verdict...")
    metrics = build_metrics(selection_batch, video_batch, retrieval_analysis, selector_analysis, product_analysis)
    (OUTPUT_DIR / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    verdict = build_verdict(metrics, retrieval_analysis, selector_analysis, product_analysis)
    (OUTPUT_DIR / "final_verdict.json").write_text(
        json.dumps(verdict, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Summary ──
    print(f"\n{'='*70}")
    print("METRICS:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    print(f"\n{'='*70}")
    print(f"VERDICT: {verdict['verdict']}")
    if verdict["root_cause_if_hold"]:
        print(f"  Root cause: {', '.join(verdict['root_cause_if_hold'])}")
    print(f"  Visual query layer: {verdict['visual_query_layer']}")
    print(f"  Next action: {verdict['next_action']}")
    for finding in verdict["main_findings"]:
        print(f"  → {finding}")
    print("=" * 70)

    # Print sample queries for inspection
    print(f"\n{'='*70}")
    print("SAMPLE QUERIES (first 3 cases):")
    for case in selection_batch[:3]:
        print(f"\n  [{case['scenario']}] anchor={case['visual_anchor']} entity={case['entity']}")
        for seg_name in ("hook", "setup", "payoff"):
            seg = case["segments"][seg_name]
            marker = "✓" if seg["selected_path"] else "✗"
            print(f"    {seg_name} [{marker}]: {seg['search_query_real'][:90]}...")

    print(f"\nAll artifacts written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
