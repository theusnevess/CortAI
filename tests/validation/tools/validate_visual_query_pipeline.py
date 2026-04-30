"""
Asset Agent VisualQuery Pipeline Validation Script.

Validates that the interpreter generates rich, specific visual queries
that flow correctly through the pipeline to the selector.

Outputs:
  - OUT/audit/visual_query_validation/scenario_results.json
  - OUT/audit/visual_query_validation/final_verdict.json
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.asset.interpreter import AssetInterpreterService
from app.creative.contracts.creative_pack import ScriptPlan, TrendProfile

OUTPUT_DIR = ROOT / "OUT" / "audit" / "visual_query_validation"

GENERIC_TOKENS = {"document", "archive", "corridor", "room", "scene", "image", "background", "photo"}

REQUIRED_QUERY_COMPONENTS = {"subject", "lighting", "mood", "framing"}

SCENARIOS = [
    {
        "name": "sealed_room_whisper",
        "niche": "horror",
        "topic": "sealed room whisper phone rang inside",
        "script": ScriptPlan(
            hook="THE SEALED ROOM STARTED WHISPERING AFTER MIDNIGHT.",
            setup="Security tape on the door was still intact. Phone rang inside the shuttered room.",
            payoff="Something answered from inside the room.",
        ),
        "trend": TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
    },
    {
        "name": "archive_timestamp_contradiction",
        "niche": "facts",
        "topic": "archive page changed date",
        "script": ScriptPlan(
            hook="ARCHIVES KEPT CHANGING — ARCHIVE PAGE CHANGED DATE.",
            setup="The entry was revised every night at midnight.",
            payoff="The timestamp pointed to a city that never stood.",
        ),
        "trend": TrendProfile(niche="facts", pacing="baseline", visual_style="archive_dark"),
    },
    {
        "name": "station_intercom_warning",
        "niche": "true_crime",
        "topic": "station intercom warning",
        "script": ScriptPlan(
            hook="POLICE REOPENED STATION INTERCOM WARNING LOGS.",
            setup="The recorder captured a voice from sealed evidence.",
            payoff="A voice from sealed evidence answered back.",
        ),
        "trend": TrendProfile(niche="true_crime", pacing="baseline", visual_style="investigation_dark"),
    },
    {
        "name": "camera_blackout_glitch",
        "niche": "true_crime",
        "topic": "camera blackout signal desync",
        "script": ScriptPlan(
            hook="CAMERA SEVEN WENT TO BLACKOUT AT 03:04 AM.",
            setup="The signal desynced across all monitors.",
            payoff="A shadow moved through the distorted feed.",
        ),
        "trend": TrendProfile(niche="true_crime", pacing="fast_first_3s", visual_style="investigation_dark"),
    },
    {
        "name": "blueprint_missing_corridor",
        "niche": "conspiracy",
        "topic": "station blueprint missing corridor",
        "script": ScriptPlan(
            hook="THE STATION BLUEPRINT HAD A CORRIDOR THAT DOESN'T EXIST.",
            setup="Workers found a sealed tunnel behind the platform wall.",
            payoff="The map showed an exit that was erased 40 years ago.",
        ),
        "trend": TrendProfile(niche="conspiracy", pacing="baseline", visual_style="archive_dark"),
    },
]


def _tokenize(text: str) -> set[str]:
    return {
        token.strip().lower()
        for token in re.sub(r"[^a-z0-9]+", " ", text.lower()).split()
        if len(token.strip()) >= 4
    }


def _is_generic(search_query_real: str) -> bool:
    tokens = _tokenize(search_query_real)
    if not tokens:
        return True
    return tokens <= GENERIC_TOKENS


def _has_required_components(visual_query_dict: dict) -> tuple[bool, list[str]]:
    missing = []
    for key in REQUIRED_QUERY_COMPONENTS:
        value = visual_query_dict.get(key, "").strip()
        if not value:
            missing.append(key)
    return len(missing) == 0, missing


def _segments_are_differentiated(segments: dict) -> tuple[bool, str]:
    queries = {}
    for seg_name in ("hook", "setup", "payoff"):
        seg = segments.get(seg_name)
        if seg is None:
            return False, f"missing segment {seg_name}"
        queries[seg_name] = seg.visual_query.search_query_real

    hook_tokens = _tokenize(queries["hook"])
    setup_tokens = _tokenize(queries["setup"])
    payoff_tokens = _tokenize(queries["payoff"])

    if hook_tokens == setup_tokens == payoff_tokens:
        return False, "all 3 segments have identical query tokens"

    hook_setup_overlap = len(hook_tokens & setup_tokens) / max(len(hook_tokens | setup_tokens), 1)
    if hook_setup_overlap > 0.85:
        return False, f"hook/setup overlap too high: {hook_setup_overlap:.2f}"

    return True, "queries are differentiated"


def validate_scenario(scenario: dict, service: AssetInterpreterService) -> dict:
    plan = service.build_plan(
        niche=scenario["niche"],
        topic=scenario["topic"],
        script_plan=scenario["script"],
        trend_profile=scenario["trend"],
        deterministic_seed=f"validation-{scenario['name']}",
    )

    results = {
        "scenario": scenario["name"],
        "visual_anchor": plan.visual_anchor,
        "semantic_pattern": plan.semantic_pattern,
        "entity": plan.entity,
        "segments": {},
        "checks": {},
    }

    all_rich = True
    all_complete = True
    for seg_name in ("hook", "setup", "payoff"):
        seg = plan.segments[seg_name]
        vq = seg.visual_query
        vq_dict = vq.to_dict()

        is_generic = _is_generic(vq.search_query_real)
        has_components, missing = _has_required_components(vq_dict)
        tokens = sorted(_tokenize(vq.search_query_real))

        if is_generic:
            all_rich = False
        if not has_components:
            all_complete = False

        results["segments"][seg_name] = {
            "category": seg.category,
            "search_query_real": vq.search_query_real,
            "query_tokens": tokens,
            "is_generic": is_generic,
            "has_all_components": has_components,
            "missing_components": missing,
            "visual_query": vq_dict,
        }

    differentiated, diff_reason = _segments_are_differentiated(plan.segments)

    results["checks"] = {
        "all_queries_rich": all_rich,
        "all_queries_complete": all_complete,
        "segments_differentiated": differentiated,
        "differentiation_reason": diff_reason,
        "scenario_pass": all_rich and all_complete and differentiated,
    }

    return results


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    service = AssetInterpreterService()

    scenario_results = []
    for scenario in SCENARIOS:
        result = validate_scenario(scenario, service)
        scenario_results.append(result)

    passed = sum(1 for r in scenario_results if r["checks"]["scenario_pass"])
    failed = len(scenario_results) - passed

    verdict = {
        "total_scenarios": len(scenario_results),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(scenario_results), 2),
        "pipeline_status": "HEALTHY" if failed == 0 else "DEGRADED" if failed <= 1 else "BROKEN",
        "summary": [],
    }

    print("=" * 70)
    print("VISUAL QUERY PIPELINE VALIDATION")
    print("=" * 70)

    for result in scenario_results:
        name = result["scenario"]
        checks = result["checks"]
        status = "PASS" if checks["scenario_pass"] else "FAIL"
        print(f"\n{'='*50}")
        print(f"[{status}] {name}")
        print(f"  visual_anchor: {result['visual_anchor']}")
        print(f"  semantic_pattern: {result['semantic_pattern']}")
        print(f"  entity: {result['entity']}")

        for seg_name in ("hook", "setup", "payoff"):
            seg = result["segments"][seg_name]
            generic_marker = " [GENERIC!]" if seg["is_generic"] else ""
            incomplete_marker = f" [MISSING: {', '.join(seg['missing_components'])}]" if seg["missing_components"] else ""
            print(f"\n  {seg_name}:")
            print(f"    category: {seg['category']}")
            print(f"    search_query_real: {seg['search_query_real']}{generic_marker}{incomplete_marker}")
            print(f"    tokens: {seg['query_tokens']}")

        print(f"\n  differentiated: {checks['segments_differentiated']} ({checks['differentiation_reason']})")

        verdict["summary"].append({
            "scenario": name,
            "status": status,
            "all_rich": checks["all_queries_rich"],
            "all_complete": checks["all_queries_complete"],
            "differentiated": checks["segments_differentiated"],
        })

    print(f"\n{'='*70}")
    print(f"VERDICT: {verdict['pipeline_status']} ({passed}/{len(scenario_results)} passed)")
    print("=" * 70)

    results_path = OUTPUT_DIR / "scenario_results.json"
    verdict_path = OUTPUT_DIR / "final_verdict.json"

    results_path.write_text(json.dumps(scenario_results, indent=2, ensure_ascii=False), encoding="utf-8")
    verdict_path.write_text(json.dumps(verdict, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nResults written to: {results_path}")
    print(f"Verdict written to: {verdict_path}")


if __name__ == "__main__":
    main()
