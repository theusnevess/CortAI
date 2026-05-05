"""
RETRIEVAL_COVERAGE_EXPANSION_v1_0 — Directed Catalog Ingestion.

Reads failed queries from the validation batch, clusters them,
ingests targeted assets from Pexels/Unsplash/Pixabay, and re-runs
the validation batch for before/after comparison.

Usage:
    # Load .env first, then run:
    python backend/app/assets/run_directed_ingestion.py
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.assets.catalog_registry import load_catalog, CATALOG_PATH

OUTPUT_DIR = ROOT / "OUT" / "audit" / "retrieval_coverage_expansion"
SELECTION_BATCH_PATH = ROOT / "OUT" / "audit" / "visual_query_product_validation" / "selection_batch.json"

# ── Ingestion query templates per cluster ──
# Each cluster maps to provider-friendly search queries + metadata

CLUSTER_INGESTION_PLAN: dict[str, dict] = {
    "document": {
        "subtype": "case_file",
        "family": "documentary_evidence",
        "mood": "mysterious",
        "framing": "close",
        "queries": [
            "police case file folder desk",
            "classified document close up desk",
            "old paper file evidence desk lamp",
            "court document stamp close up",
            "official report paper desk dark",
        ],
        "tags": ["evidence_document", "case_file", "desk_surface", "documentary_context"],
        "semantic_pattern_fit": ["contradiction", "sealed", "glitch"],
        "entity_fit": ["document", "file", "case", "paper", "report"],
    },
    "archive": {
        "subtype": "archive_records",
        "family": "documentary_evidence",
        "mood": "mysterious",
        "framing": "medium",
        "queries": [
            "archive filing cabinet records dark",
            "old storage shelf files dusty",
            "records room shelves dim light",
            "vintage filing system drawer open",
        ],
        "tags": ["archive_room", "records_surface", "evidence_storage", "documentary_context"],
        "semantic_pattern_fit": ["contradiction", "sealed"],
        "entity_fit": ["archive", "records", "cabinet", "storage"],
    },
    "corridor": {
        "subtype": "transit_corridor",
        "family": "investigative_ambient",
        "mood": "threatening",
        "framing": "medium",
        "queries": [
            "dark industrial corridor dim light",
            "underground tunnel passage concrete",
            "hospital corridor empty dark",
            "subway tunnel dark moody",
            "institutional hallway fluorescent abandoned",
        ],
        "tags": ["corridor_passage", "transit_route", "institutional_space", "ambient_tension"],
        "semantic_pattern_fit": ["sealed", "glitch", "contradiction"],
        "entity_fit": ["corridor", "tunnel", "hallway", "passage"],
    },
    "door": {
        "subtype": "sealed_door",
        "family": "barrier_signal",
        "mood": "ominous",
        "framing": "close",
        "queries": [
            "locked metal door dark hallway",
            "industrial heavy door closed dark",
            "restricted area sealed door warning",
            "old wooden door dark corridor",
        ],
        "tags": ["sealed_access", "locked_door", "barrier_signal", "containment"],
        "semantic_pattern_fit": ["sealed", "breach"],
        "entity_fit": ["door", "threshold", "access", "barrier"],
    },
    "sealed_access": {
        "subtype": "restricted_access",
        "family": "barrier_signal",
        "mood": "ominous",
        "framing": "close",
        "queries": [
            "restricted area door caution tape",
            "sealed entrance warning sign dark",
            "security door access control dark",
            "industrial gate closed restricted",
        ],
        "tags": ["restricted_access", "sealed_threshold", "warning_barrier", "containment"],
        "semantic_pattern_fit": ["sealed", "breach"],
        "entity_fit": ["door", "gate", "access", "barrier", "seal"],
    },
    "institutional_space": {
        "subtype": "wall_zone",
        "family": "investigative_ambient",
        "mood": "threatening",
        "framing": "medium",
        "queries": [
            "institutional wall corridor dark fluorescent",
            "hospital hallway wall empty dark",
            "concrete wall industrial interior",
            "government building hallway dim",
        ],
        "tags": ["institutional_wall", "ambient_space", "interior_zone", "investigation_context"],
        "semantic_pattern_fit": ["sealed", "glitch"],
        "entity_fit": ["wall", "corridor", "institution", "interior"],
    },
    "investigative_interior": {
        "subtype": "investigation_room",
        "family": "investigative_ambient",
        "mood": "tense",
        "framing": "medium",
        "queries": [
            "investigation room evidence table dark",
            "detective office desk files dark",
            "interrogation room table lamp",
            "evidence room shelves dark moody",
        ],
        "tags": ["investigation_room", "evidence_desk", "case_environment", "procedural_interior"],
        "semantic_pattern_fit": ["contradiction", "sealed"],
        "entity_fit": ["room", "desk", "evidence", "interior", "office"],
    },
    "horror_interior": {
        "subtype": "restricted_room",
        "family": "horror_ambient",
        "mood": "oppressive",
        "framing": "medium",
        "queries": [
            "dark abandoned room interior",
            "creepy empty room dark shadows",
            "old hospital room dark abandoned",
        ],
        "tags": ["restricted_room", "horror_interior", "abandoned_space", "containment_breach"],
        "semantic_pattern_fit": ["breach", "sealed"],
        "entity_fit": ["room", "interior", "space", "threshold"],
    },
    "map_blueprint": {
        "subtype": "station_blueprint",
        "family": "documentary_evidence",
        "mood": "mysterious",
        "framing": "close",
        "queries": [
            "old architectural blueprint close up",
            "vintage floor plan document",
            "technical drawing blueprint dark desk",
        ],
        "tags": ["blueprint", "map_document", "architectural_plan", "station_layout"],
        "semantic_pattern_fit": ["contradiction", "sealed"],
        "entity_fit": ["blueprint", "map", "plan", "corridor", "station"],
    },
}


@dataclass
class IngestionResult:
    provider: str
    query: str
    category: str
    success_count: int = 0
    error: str = ""
    entries: list[dict] = field(default_factory=list)


def load_env_file(env_path: Path) -> None:
    """Load .env file into os.environ (simple parser, no override)."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def build_failure_clusters(selection_batch: list[dict]) -> list[dict]:
    clusters: dict[str, dict] = {}
    for case in selection_batch:
        for seg_name in ("hook", "setup", "payoff"):
            seg = case["segments"][seg_name]
            if seg["selected_path"]:
                continue
            cat = seg["category"]
            if cat not in clusters:
                clusters[cat] = {"category": cat, "failed_count": 0, "sample_queries": [], "niches": set()}
            clusters[cat]["failed_count"] += 1
            clusters[cat]["niches"].add(case["niche"])
            if len(clusters[cat]["sample_queries"]) < 3:
                clusters[cat]["sample_queries"].append(seg["search_query_real"][:120])

    result = []
    for cat in sorted(clusters, key=lambda k: -clusters[k]["failed_count"]):
        c = clusters[cat]
        priority = "P0" if c["failed_count"] >= 10 else ("P1" if c["failed_count"] >= 5 else ("P2" if c["failed_count"] >= 3 else "P3"))
        result.append({
            "category": cat,
            "failed_count": c["failed_count"],
            "priority": priority,
            "niches": sorted(c["niches"]),
            "sample_queries": c["sample_queries"],
            "has_ingestion_plan": cat in CLUSTER_INGESTION_PLAN,
        })
    return result


def run_ingestion_for_cluster(category: str, plan: dict, limit_per_query: int = 5) -> list[IngestionResult]:
    results = []

    providers = []
    # Priority order: Pexels → Unsplash → Pixabay
    pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
    pixabay_key = os.getenv("PIXABAY_API_KEY", "").strip()

    if pexels_key:
        from app.assets.pexels_ingestor import PexelsIngestor
        providers.append(("pexels", PexelsIngestor(api_key=pexels_key)))
    if unsplash_key:
        from app.assets.unsplash_ingestor import UnsplashIngestor
        providers.append(("unsplash", UnsplashIngestor(access_key=unsplash_key)))
    if pixabay_key:
        from app.assets.pixabay_ingestor import PixabayIngestor
        providers.append(("pixabay", PixabayIngestor(api_key=pixabay_key)))

    if not providers:
        print("  ⚠ No API keys available — skipping ingestion")
        return results

    metadata = {
        "family": plan.get("family", category),
        "mood": plan.get("mood", "neutral"),
        "framing": plan.get("framing", "medium"),
        "semantic_pattern_fit": plan.get("semantic_pattern_fit", []),
        "entity_fit": plan.get("entity_fit", []),
        "hook_strength_score": 0.80,
        "payoff_strength_score": 0.82,
        "realism_score": 0.95,
        "setup_specificity_score": 0.78,
        "genericity": 0.10,
        "strength": 0.90,
        "freshness_score": 1.0,
    }

    for query in plan["queries"]:
        ingested = False
        for provider_name, ingestor in providers:
            if ingested:
                break
            result = IngestionResult(provider=provider_name, query=query, category=category)
            try:
                entries = ingestor.ingest_query(
                    query=query,
                    category=category,
                    subtype=plan.get("subtype", category),
                    tags=plan.get("tags", []),
                    limit=limit_per_query,
                    metadata=metadata,
                )
                result.success_count = len(entries)
                result.entries = entries
                if entries:
                    ingested = True
                    print(f"    ✓ [{provider_name}] '{query}' → {len(entries)} assets")
                else:
                    print(f"    · [{provider_name}] '{query}' → 0 results")
            except Exception as exc:
                result.error = str(exc)
                print(f"    ✗ [{provider_name}] '{query}' → ERROR: {exc}")
            results.append(result)

    return results


def main() -> None:
    # Load .env
    load_env_file(ROOT / ".env")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("RETRIEVAL_COVERAGE_EXPANSION_v1_0")
    print("=" * 70)

    # ── PHASE 1: Failure Cluster Analysis ──
    print("\n[Phase 1] Building failure clusters...")
    selection_batch = json.loads(SELECTION_BATCH_PATH.read_text(encoding="utf-8"))
    clusters = build_failure_clusters(selection_batch)

    clusters_path = OUTPUT_DIR / "failure_clusters.json"
    clusters_path.write_text(json.dumps(clusters, indent=2, ensure_ascii=False), encoding="utf-8")

    total_failed = sum(c["failed_count"] for c in clusters)
    print(f"  Total failed segments: {total_failed}")
    print(f"  Clusters found: {len(clusters)}")
    for c in clusters:
        marker = "✓" if c["has_ingestion_plan"] else "✗"
        print(f"  [{marker}] {c['category']}: {c['failed_count']}x ({c['priority']})")

    # ── PHASE 2+3: Catalog snapshot before + Directed Ingestion ──
    print("\n[Phase 2] Saving catalog snapshot (before)...")
    catalog_before = load_catalog()
    catalog_before_path = OUTPUT_DIR / "catalog_before.json"
    catalog_before_path.write_text(
        json.dumps({"total_entries": len(catalog_before), "timestamp": datetime.now(timezone.utc).isoformat()},
                   indent=2), encoding="utf-8")
    print(f"  Catalog size before: {len(catalog_before)} entries")

    print("\n[Phase 3] Running directed ingestion...")
    all_results: list[IngestionResult] = []
    for cluster in clusters:
        cat = cluster["category"]
        plan = CLUSTER_INGESTION_PLAN.get(cat)
        if not plan:
            print(f"\n  Skipping {cat} — no ingestion plan defined")
            continue
        print(f"\n  Ingesting for [{cat}] ({cluster['failed_count']}x failed)...")
        cluster_results = run_ingestion_for_cluster(cat, plan, limit_per_query=5)
        all_results.extend(cluster_results)

    # ── PHASE 4: Catalog Update Audit ──
    print("\n[Phase 4] Generating catalog audit...")
    catalog_after = load_catalog()
    new_count = len(catalog_after) - len(catalog_before)

    # Provider summary
    provider_summary: dict[str, dict] = {}
    category_summary: dict[str, int] = {}
    for r in all_results:
        if r.provider not in provider_summary:
            provider_summary[r.provider] = {"success": 0, "failed": 0, "total_assets": 0, "errors": []}
        if r.success_count > 0:
            provider_summary[r.provider]["success"] += 1
            provider_summary[r.provider]["total_assets"] += r.success_count
        elif r.error:
            provider_summary[r.provider]["failed"] += 1
            provider_summary[r.provider]["errors"].append(f"{r.query}: {r.error[:80]}")

        if r.success_count > 0:
            category_summary[r.category] = category_summary.get(r.category, 0) + r.success_count

    ingestion_results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "catalog_size_before": len(catalog_before),
        "catalog_size_after": len(catalog_after),
        "total_new_assets": new_count,
        "provider_summary": provider_summary,
        "category_summary": category_summary,
        "total_queries_attempted": len(all_results),
        "total_queries_succeeded": sum(1 for r in all_results if r.success_count > 0),
        "detailed_results": [
            {"provider": r.provider, "query": r.query, "category": r.category,
             "success_count": r.success_count, "error": r.error}
            for r in all_results
        ],
    }

    (OUTPUT_DIR / "ingestion_results.json").write_text(
        json.dumps(ingestion_results, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUTPUT_DIR / "catalog_after.json").write_text(
        json.dumps({"total_entries": len(catalog_after), "timestamp": datetime.now(timezone.utc).isoformat()},
                   indent=2), encoding="utf-8")

    print(f"\n  Catalog growth: {len(catalog_before)} → {len(catalog_after)} (+{new_count})")
    for prov, summary in provider_summary.items():
        print(f"  [{prov}] {summary['total_assets']} assets ingested, {summary['success']} queries succeeded, {summary['failed']} failed")
    for cat, count in sorted(category_summary.items(), key=lambda x: -x[1]):
        print(f"  [{cat}] +{count} new assets")

    print(f"\n{'='*70}")
    print("INGESTION COMPLETE")
    print(f"{'='*70}")
    print(f"  New assets: {new_count}")
    print(f"  Run 'python tests/validation/manual/run_batch_validation.py' to re-validate")


if __name__ == "__main__":
    main()
