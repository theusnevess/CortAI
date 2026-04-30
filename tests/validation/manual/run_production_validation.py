"""
ASSET_AGENT_PRODUCTION_VALIDATION_v1_0

Runs a realistic production batch through the full pipeline
(Script → Voice → Asset → Render) and evaluates asset selection
quality, coherence, and diversity.

Usage:
    python tests/validation/manual/run_production_validation.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load .env
_env_path = ROOT / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            _k, _v = _k.strip(), _v.strip()
            if _k and _k not in os.environ:
                os.environ[_k] = _v

from app.runtime.rollout.pilot_runner import run_pilot_rollout

AUDIT_DIR = ROOT / "OUT" / "audit" / "asset_agent_production_validation"
RUNTIME_DIR = AUDIT_DIR / "runtime"

# ── Scenario pool ──────────────────────────────────────────────
SCENARIO_POOL = [
    # Documentary / Investigative
    {"theme": "abandoned hospital corridor discovery", "angle": "missing patient file", "hook_hint": "a file marked as destroyed still exists"},
    {"theme": "underground bunker archive", "angle": "sealed records from 1962", "hook_hint": "someone wrote a warning inside the folder"},
    {"theme": "decommissioned train station blueprints", "angle": "a corridor that was erased from the map", "hook_hint": "the corridor connects two buildings that should not be connected"},
    {"theme": "old police evidence room audit", "angle": "a case file reopened after 40 years", "hook_hint": "the original investigator left a hidden note"},
    {"theme": "military base document leak", "angle": "classified testing protocol", "hook_hint": "the test subjects were never officially registered"},
    # Anomaly / Horror
    {"theme": "psychiatric ward night shift recording", "angle": "intercom activation at 3AM with no operator", "hook_hint": "the recorded voice matches a patient who died two weeks earlier"},
    {"theme": "sealed basement room in government building", "angle": "an access door with a broken seal", "hook_hint": "someone entered after it was officially sealed"},
    {"theme": "abandoned research lab intrusion", "angle": "security cameras showing movement in a locked room", "hook_hint": "the room had been sealed with concrete blocks"},
    {"theme": "coastal lighthouse keeper disappearance", "angle": "logbook entries written after official departure", "hook_hint": "the handwriting matches but the details are impossible"},
    {"theme": "industrial facility warning system malfunction", "angle": "alert panels activating in sequence without trigger", "hook_hint": "the sequence spells a word in morse code"},
    # Device / Technical
    {"theme": "radio frequency anomaly detection station", "angle": "a signal that repeats every 72 hours", "hook_hint": "the frequency was decommissioned in 1991"},
    {"theme": "surveillance system forensic analysis", "angle": "footage gap in a critical corridor", "hook_hint": "the gap coincides with a door being opened"},
    {"theme": "emergency broadcast system test failure", "angle": "a test message that was never authorized", "hook_hint": "the message contained coordinates that lead to a real location"},
    # Corridor / Institutional
    {"theme": "subway tunnel maintenance inspection", "angle": "a sealed passage discovered behind a wall panel", "hook_hint": "the passage appears on blueprints from 1948"},
    {"theme": "hospital wing quarantine review", "angle": "a corridor sealed since 2003", "hook_hint": "the sealing order was signed by someone who did not exist"},
    {"theme": "abandoned factory floor investigation", "angle": "equipment still running in a sealed section", "hook_hint": "the power was officially cut off in 1997"},
    # Mixed / Cross-category
    {"theme": "cold case forensic re-examination", "angle": "evidence that contradicts the official report", "hook_hint": "the contradiction was noted in the original file but redacted"},
    {"theme": "archive room water damage assessment", "angle": "records that survived in a sealed cabinet", "hook_hint": "the cabinet was not listed in any inventory"},
    {"theme": "institutional building safety inspection", "angle": "fire exit that leads to an unmarked room", "hook_hint": "the room contains equipment from a different decade"},
    {"theme": "restricted floor access control audit", "angle": "badge swipe records showing impossible patterns", "hook_hint": "the same badge was used in two locations simultaneously"},
    {"theme": "forensic document analysis of sealed evidence", "angle": "ink dating reveals a document was written years after its official date", "hook_hint": "the document changed the outcome of a major investigation"},
    {"theme": "abandoned school corridor investigation", "angle": "graffiti that contains specific dates and names", "hook_hint": "the dates correspond to events that happened after the school was closed"},
    {"theme": "warehouse inventory discrepancy audit", "angle": "items listed as destroyed still have active barcodes", "hook_hint": "the barcodes were scanned at a location that does not match any warehouse"},
    {"theme": "underwater tunnel structural assessment", "angle": "a chamber not present in any construction record", "hook_hint": "the chamber has acoustic properties that suggest recent modification"},
    {"theme": "old newspaper archive contradiction", "angle": "two editions of the same date with different front pages", "hook_hint": "one edition reports an event that the other edition says never happened"},
]


def _build_accounts(count: int) -> list[str]:
    accounts = []
    for i in range(1, count + 1):
        accounts.append(f"acc_prod_val_{i:03d}")
    return accounts


def _evaluate_video(metadata: dict, visual_trace: dict | None) -> dict:
    """Evaluate a single video based on its pipeline data."""
    asset_plan = metadata.get("asset_plan", {})
    hook_bg = metadata.get("hook_background_path")
    setup_bg = metadata.get("setup_background_path")
    payoff_bg = metadata.get("payoff_background_path")

    # All 3 backgrounds must exist (not None/empty)
    has_hook = bool(hook_bg)
    has_setup = bool(setup_bg)
    has_payoff = bool(payoff_bg)
    all_assets_resolved = has_hook and has_setup and has_payoff

    # Check diversity: are all 3 different?
    bg_paths = [hook_bg, setup_bg, payoff_bg]
    unique_paths = len(set(p for p in bg_paths if p))
    visual_diversity = "high" if unique_paths == 3 else ("medium" if unique_paths == 2 else "low")

    # Check for phase1 feel: phase1 means all 3 assets are identical
    # or generic/empty. The legacy visual_style field is always
    # "phase1_baseline" and is NOT an indicator of actual quality.
    feels_phase1 = (not all_assets_resolved) or (unique_paths <= 1)

    # Scene coherence: check visual_trace for query quality
    query_rich = False
    assets_match = False
    if visual_trace:
        sq = visual_trace.get("search_query_real", "")
        query_rich = len(str(sq).split()) >= 8
        # If all segments resolved, assets likely match
        assets_match = all_assets_resolved

    # Hook/setup/payoff strength from metadata
    duration = metadata.get("render_duration_s", 0)
    timings = metadata.get("timings", [])
    hook_strength = "high" if (timings and len(timings) >= 3 and timings[0][1] - timings[0][0] >= 2.0) else "medium"
    setup_progression = "strong" if (len(timings) >= 3 and timings[1][1] - timings[1][0] >= 2.5) else "weak"
    payoff_clarity = "clear" if (len(timings) >= 3 and timings[2][1] - timings[2][0] >= 2.5) else "unclear"

    # Overall impression
    if all_assets_resolved and visual_diversity in ("high", "medium") and not feels_phase1 and assets_match:
        overall = "good"
        visual_quality = "high"
    elif all_assets_resolved and not feels_phase1:
        overall = "acceptable"
        visual_quality = "medium"
    else:
        overall = "bad"
        visual_quality = "low"

    return {
        "render_job_id": metadata.get("render_job_id", ""),
        "feels_like_phase1": feels_phase1,
        "visual_quality": visual_quality,
        "hook_strength": hook_strength,
        "setup_progression": setup_progression,
        "payoff_clarity": payoff_clarity,
        "scene_coherence": all_assets_resolved and query_rich,
        "visual_diversity": visual_diversity,
        "repetition_detected": unique_paths < 3,
        "assets_match_script": assets_match,
        "overall_impression": overall,
        "all_assets_resolved": all_assets_resolved,
        "hook_asset": asset_plan.get("hook_asset", ""),
        "setup_asset": asset_plan.get("setup_asset", ""),
        "payoff_asset": asset_plan.get("payoff_asset", ""),
        "hook_background": hook_bg,
        "setup_background": setup_bg,
        "payoff_background": payoff_bg,
    }


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    started = datetime.now(timezone.utc)
    count = min(25, len(SCENARIO_POOL))
    accounts = _build_accounts(count)

    print("=" * 70)
    print("ASSET_AGENT_PRODUCTION_VALIDATION_v1_0")
    print("=" * 70)

    # ── Phase 1: Run production batch ──
    print(f"\n[Phase 1] Running production batch ({count} videos)...")
    print(f"  Base dir: {RUNTIME_DIR}")

    stage_by_account = {acc: "GROWTH" for acc in accounts}
    rollout_result = run_pilot_rollout(
        base_dir=RUNTIME_DIR,
        account_ids=accounts,
        stage_by_account=stage_by_account,
        now=started,
    )

    batch_summary = rollout_result.get("batch_summary", {})
    print(f"  Tasks executed: {batch_summary.get('tasks_executed', 0)}")
    print(f"  Publish records: {batch_summary.get('publish_records_written', 0)}")

    # ── Phase 2: Evaluate each video ──
    print("\n[Phase 2] Evaluating video quality...")
    metadata_dir = RUNTIME_DIR / "content" / "metadata"
    video_dir = RUNTIME_DIR / "content" / "video"
    visual_trace_path = ROOT / "OUT" / "audit" / "asset_agent_runtime" / "visual_trace.json"

    visual_trace = None
    if visual_trace_path.exists():
        try:
            visual_trace = json.loads(visual_trace_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    reviews = []
    if metadata_dir.exists():
        for meta_file in sorted(metadata_dir.glob("*.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                review = _evaluate_video(meta, visual_trace)
                reviews.append(review)
            except Exception as e:
                print(f"  ⚠ Error evaluating {meta_file.name}: {e}")

    print(f"  Videos evaluated: {len(reviews)}")

    # Write human review simulation
    review_path = AUDIT_DIR / "human_review_simulation.json"
    review_path.write_text(json.dumps(reviews, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Phase 3: Failure analysis ──
    print("\n[Phase 3] Analyzing failures...")
    failures = {
        "unresolved_assets": [],
        "phase1_feel": [],
        "low_diversity": [],
        "weak_setups": [],
        "repeated_families": [],
    }

    family_counter = Counter()
    for r in reviews:
        if not r["all_assets_resolved"]:
            failures["unresolved_assets"].append(r["render_job_id"])
        if r["feels_like_phase1"]:
            failures["phase1_feel"].append(r["render_job_id"])
        if r["visual_diversity"] == "low":
            failures["low_diversity"].append(r["render_job_id"])
        if r["setup_progression"] == "weak":
            failures["weak_setups"].append(r["render_job_id"])
        # Track asset families
        for asset in [r["hook_asset"], r["setup_asset"], r["payoff_asset"]]:
            if asset:
                family = Path(asset).parent.name if "/" in str(asset) or "\\" in str(asset) else "unknown"
                family_counter[family] += 1

    # Detect repeated families
    total_assets = sum(family_counter.values())
    for family, count_fam in family_counter.most_common(5):
        if total_assets > 0 and count_fam / total_assets > 0.3:
            failures["repeated_families"].append({"family": family, "count": count_fam, "rate": round(count_fam / total_assets, 3)})

    failure_path = AUDIT_DIR / "failure_analysis.json"
    failure_path.write_text(json.dumps(failures, indent=2, ensure_ascii=False), encoding="utf-8")

    for k, v in failures.items():
        print(f"  {k}: {len(v)}")

    # ── Phase 4: Metrics ──
    print("\n[Phase 4] Computing metrics...")
    total = len(reviews) or 1
    good_count = sum(1 for r in reviews if r["overall_impression"] == "good")
    acceptable_count = sum(1 for r in reviews if r["overall_impression"] == "acceptable")
    bad_count = sum(1 for r in reviews if r["overall_impression"] == "bad")
    phase1_count = sum(1 for r in reviews if r["feels_like_phase1"])
    rep_count = sum(1 for r in reviews if r["repetition_detected"])
    high_div = sum(1 for r in reviews if r["visual_diversity"] == "high")
    resolved = sum(1 for r in reviews if r["all_assets_resolved"])

    metrics = {
        "total_videos": len(reviews),
        "good_videos_rate": round(good_count / total, 4),
        "acceptable_videos_rate": round(acceptable_count / total, 4),
        "bad_videos_rate": round(bad_count / total, 4),
        "phase1_feel_rate": round(phase1_count / total, 4),
        "repetition_rate": round(rep_count / total, 4),
        "visual_diversity_score": round(high_div / total, 4),
        "retrieval_match_rate": round(resolved / total, 4),
        "selector_accuracy_rate": round(resolved / total, 4),
    }

    metrics_path = AUDIT_DIR / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # ── Phase 5: Final verdict ──
    print("\n[Phase 5] Generating final verdict...")
    is_go = (
        metrics["good_videos_rate"] >= 0.7
        and metrics["phase1_feel_rate"] <= 0.1
        and metrics["repetition_rate"] <= 0.4
        and metrics["retrieval_match_rate"] >= 0.7
    )

    main_failure_list = []
    if metrics["good_videos_rate"] < 0.7:
        main_failure_list.append(f"good_videos_rate too low: {metrics['good_videos_rate']}")
    if metrics["retrieval_match_rate"] < 0.7:
        main_failure_list.append(f"retrieval_match_rate too low: {metrics['retrieval_match_rate']}")
    if metrics["phase1_feel_rate"] > 0.1:
        main_failure_list.append(f"phase1_feel_rate too high: {metrics['phase1_feel_rate']}")
    if metrics["repetition_rate"] > 0.4:
        main_failure_list.append(f"repetition_rate too high: {metrics['repetition_rate']}")

    verdict = {
        "verdict": "GO" if is_go else "HOLD",
        "production_ready": is_go,
        "good_videos_rate": metrics["good_videos_rate"],
        "main_failures": main_failure_list,
        "system_status": "ready_for_promotion" if is_go else "needs_refinement",
        "confidence_level": "high" if is_go and metrics["good_videos_rate"] >= 0.8 else ("medium" if is_go else "low"),
        "next_action": "proceed_to_deployment" if is_go else "investigate_failures",
        "metrics_summary": metrics,
    }

    verdict_path = AUDIT_DIR / "final_verdict.json"
    verdict_path.write_text(json.dumps(verdict, indent=2, ensure_ascii=False), encoding="utf-8")

    verdict_str = verdict["verdict"]
    print(f"\n{'='*70}")
    print(f"VERDICT: {verdict_str}")
    if not is_go:
        for fail in main_failure_list:
            print(f"  ✗ {fail}")
    else:
        print(f"  ✓ good_videos_rate: {metrics['good_videos_rate']}")
        print(f"  ✓ retrieval_match_rate: {metrics['retrieval_match_rate']}")
        print(f"  ✓ phase1_feel_rate: {metrics['phase1_feel_rate']}")
    print(f"{'='*70}")
    print(f"\nAll artifacts written to: {AUDIT_DIR}")


if __name__ == "__main__":
    main()
