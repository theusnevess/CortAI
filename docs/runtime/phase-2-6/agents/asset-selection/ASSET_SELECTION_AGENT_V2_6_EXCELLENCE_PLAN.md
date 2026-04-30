# Asset Selection Agent v2.6 Excellence Plan

## 1. Purpose

This document defines the formal Phase 2.6 excellence plan for the Asset Selection Agent.

The Asset Selection Agent is the third Wave 2 output agent. It consumes Script, Strategy, Trend, and local asset catalog context, then produces an `AssetPlan` for downstream visual composition.

This is not an implementation artifact.

This plan defines how Asset Selection must evolve from a functional local asset selector into an audit-grade, visually truthful, semantically aligned, fallback-honest, confidence-aware visual selection subsystem.

## 2. Governance Context

The system remains under:

```json
{
  "system_version": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "governance_model": "SUBSYSTEM_BASELINE_WITH_MONITORING",
  "change_policy": "FROZEN_UNLESS_GOVERNANCE_REOPEN",
  "no_core_modification": true,
  "no_subsystem_mutation_without_reopen": true,
  "new_work_must_be_isolated_subsystems": true
}
```

Asset Selection v2.6 work must preserve:

- frozen core pipeline
- Strategy ownership over creative control
- Script ownership over narrative text
- Voice ownership over voice planning
- Trend ownership over trend context
- QC ownership over final product-quality validation
- Experiment ownership
- Publisher out of scope
- no hidden enforcement
- no new external asset providers
- no uncontrolled scraping
- no fake visual evidence
- no fake image understanding
- no fake confidence
- no publishability decisions
- no downstream behavior changes without explicit governance

## 3. Current State

The Asset Selection subsystem is runtime-real and already participates in the creative pipeline.

Current capabilities include:

- `AssetSelectionInput` exists and carries niche, topic, Script, Strategy, and Trend surfaces.
- `AssetSelectionResult` returns `AssetPlan` and fallback state.
- `AssetSelectionAgentService` selects from local runtime assets.
- `AssetInterpreterService` produces segment-level visual plans.
- `AssetSelector` ranks local catalog entries deterministically.
- Hook/setup/payoff segments are represented.
- Local fallback exists when assets are unavailable.
- Strategy variation policy can influence category/tags.
- Payoff evidence can bias payoff category.
- Hook visual alignment exists as a bounded behavior.
- Selected asset categories are tested against realized catalog metadata.

Current limitations for Phase 2.6:

- visual context intake is not yet audit-grade.
- selected asset rationale is spread across selection logic.
- visual truthfulness is implicit, not explicitly scored or traced.
- semantic alignment to hook/setup/payoff is not fully explainable.
- local catalog provenance and eligibility are not consolidated.
- fallback visual state can be explicit but not yet deeply classified.
- confidence is not calibrated as trust in visual selection.
- `AssetPlan` selection is not reconstructible from a consolidated trace.

## 4. Objective

Asset Selection v2.6 must make visual selection more:

- context-governed
- catalog-governed
- visually truthful
- script-aligned
- trend-aware without becoming Trend
- strategy-aware without becoming Strategy
- fallback-honest
- confidence-calibrated
- traceable end-to-end
- ready for v3 with monitoring

The goal is to improve reliability, explainability, and visual-semantic honesty.

The goal is not to make Asset Selection a vision model, scraper, Strategy layer, QC judge, publisher, or performance predictor.

## 5. Scope

In scope:

- Asset context intake governance.
- local catalog/source governance.
- field-level selection rationale for hook/setup/payoff assets.
- visual semantic alignment analysis.
- visual truthfulness and mismatch risk analysis.
- fallback and safe-default honesty.
- duplicate/repetition/diversity analysis.
- confidence calibration for trust in visual selection.
- consolidated `asset_trace`.
- Asset Selection v2.6 excellence gate.

Out of scope:

- core pipeline changes.
- Strategy behavior changes.
- Script behavior changes.
- Voice behavior changes.
- Trend behavior changes.
- QC publishability decisions.
- Publisher work.
- external provider expansion.
- uncontrolled scraping.
- image generation.
- image embedding/ML scoring unless separately authorized.
- replacing local catalog selection.
- changing downstream editor behavior.
- predicting performance.

## 6. Boundary Rules

Asset Selection may:

- consume Script as narrative source.
- consume Strategy as bounded creative direction.
- consume Trend as advisory visual context.
- inspect local catalog metadata already available.
- select local assets for hook/setup/payoff.
- explain why a selected asset is appropriate.
- expose fallback, uncertainty, mismatch, and confidence.
- surface constraints for downstream interpretation only when already represented in `AssetPlan`.

Asset Selection must not:

- rewrite Script.
- decide Strategy.
- decide QC outcome.
- decide publishability.
- execute rendering.
- add providers.
- scrape or fetch uncontrolled external assets.
- claim visual facts not present in metadata.
- claim image content understanding without evidence.
- hide fallback.
- treat pretty but semantically wrong assets as strong selection.
- predict performance.

## 7. Required Workstream Order

Asset Selection v2.6 must be implemented in bounded workstreams:

1. Asset Context Governance
2. Catalog And Source Governance
3. Segment Visual Intent Mapping
4. Visual Semantic Alignment
5. Visual Truthfulness And Mismatch Risk
6. Fallback And Safe Default Honesty
7. Diversity And Repetition Guard
8. Confidence Calibration
9. Trace And Auditability Hardening
10. Asset Selection Excellence Gate

Do not implement all workstreams at once.

Each workstream must pass focused validation before the next workstream begins.

## 8. Workstream 1: Asset Context Governance

### Goal

Make Asset Selection context intake explicit, bounded, and auditable.

### Required Behavior

The Asset Selection Agent must identify which context was available, used, ignored, missing, or degraded.

Expected context classes:

- script_context
- strategy_context
- trend_context
- topic_context
- niche_context
- local_catalog_context
- experiment_context, if present

### Required Output

Additive structure:

```json
{
  "asset_context_governance": {
    "available_context": [],
    "used_context": [],
    "ignored_context": [],
    "missing_context": [],
    "degraded_context": [],
    "context_priority": [],
    "policy_respected": true,
    "boundary_statement": "Asset Selection uses context for visual selection only; Strategy remains the control layer.",
    "rationale": []
  }
}
```

### Constraints

- Strategy remains creative control.
- Script remains narrative source.
- Trend remains advisory context.
- Missing optional context must not be fabricated.
- Context governance must not alter selection behavior in this workstream.

### Validation

Focused tests must prove context classification is explicit, serializable, deterministic, and backward-compatible.

## 9. Workstream 2: Catalog And Source Governance

### Goal

Make local asset catalog eligibility, source type, and selection source governance explicit.

### Required Behavior

The Asset Selection Agent must expose:

- catalog availability.
- asset source class.
- runtime eligibility.
- local vs fallback source.
- selected entry metadata used.
- rejected or ineligible candidates when available.
- catalog coverage limitations.

### Required Output

Additive structure:

```json
{
  "catalog_governance": {
    "catalog_available": true,
    "source_policy": "local_catalog_only_v2_6",
    "allowed_source_classes": ["local", "curated_local", "safe_default"],
    "forbidden_source_classes": ["unbounded_external", "unknown", "scraped_unverified"],
    "selected_sources": {},
    "ineligible_sources": [],
    "source_policy_respected": true,
    "rationale": []
  }
}
```

### Constraints

- Do not add external providers.
- Do not scrape.
- Do not generate assets.
- Do not alter `AssetSelector` ranking unless a later workstream explicitly requires a trace-only wrapper.

### Validation

Focused tests must prove local catalog source governance is visible and fallback source is not treated as high-quality evidence.

## 10. Workstream 3: Segment Visual Intent Mapping

### Goal

Map Script hook/setup/payoff roles to intended visual roles before evaluating asset fit.

### Required Behavior

For each segment, explain:

- segment narrative role.
- intended visual role.
- requested category.
- requested tags.
- visual query text if available.
- expected visual evidence family.
- whether segment intent is sufficiently specified.

### Required Output

Additive structure:

```json
{
  "segment_visual_intent": {
    "hook": {
      "narrative_role": "attention_capture",
      "visual_role": "first_frame_anchor",
      "intent_complete": true,
      "requested_category": "...",
      "requested_tags": [],
      "rationale": []
    }
  }
}
```

### Constraints

- Do not change Script.
- Do not change selected assets in this workstream.
- Do not invent visual evidence.

### Validation

Focused tests must prove hook/setup/payoff visual intent is explicit and deterministic.

## 11. Workstream 4: Visual Semantic Alignment

### Goal

Evaluate whether selected assets align with segment visual intent and Script meaning.

### Required Behavior

For each segment, compute deterministic alignment from available metadata:

- category match.
- tag overlap.
- query/token overlap.
- segment role fit.
- selected category vs realized catalog category.
- mismatch indicators.

### Required Output

Additive structure:

```json
{
  "visual_alignment": {
    "overall_alignment_level": "low | medium | high",
    "segments": {
      "hook": {
        "alignment_score": 0.0,
        "alignment_level": "low | medium | high",
        "category_match": true,
        "tag_overlap_count": 0,
        "mismatch_indicators": [],
        "rationale": []
      }
    }
  }
}
```

### Constraints

- Use metadata and existing fields only.
- Do not use image ML.
- Do not claim object recognition unless metadata supports it.
- Do not alter selection behavior yet.

### Validation

Focused tests must cover strong alignment, partial alignment, mismatch, missing metadata, and deterministic replay.

## 12. Workstream 5: Visual Truthfulness And Mismatch Risk

### Goal

Make visually misleading selections explicit.

### Required Behavior

Detect risk that an asset is:

- pretty but semantically weak.
- generic local fallback.
- wrong category for payoff evidence.
- mismatched to hook claim.
- unsupported by catalog metadata.
- too abstract for a concrete script claim.

### Required Output

Additive structure:

```json
{
  "visual_truthfulness": {
    "truthfulness_level": "low | medium | high",
    "mismatch_risk_level": "low | medium | high",
    "unsupported_visual_claims": [],
    "generic_visual_risk": false,
    "fallback_visual_risk": false,
    "rationale": []
  }
}
```

### Constraints

- Do not become QC.
- Do not decide publishability.
- Do not claim visual fact without metadata evidence.
- Do not fail closed yet.

### Validation

Focused tests must prove visual mismatch is visible and not hidden behind fallback or generic assets.

## 13. Workstream 6: Fallback And Safe Default Honesty

### Goal

Make visual fallback explicit, scoped, and lower trust.

### Required Behavior

Expose:

- fallback used or not.
- fallback mode.
- fallback reason.
- per-segment fallback.
- safe default usage.
- missing catalog coverage.
- whether selected asset is fallback-safe rather than semantically strong.

### Required Output

Additive structure:

```json
{
  "asset_fallback_honesty": {
    "fallback_used": false,
    "fallback_mode": "NONE",
    "fallback_reason": "",
    "segment_fallbacks": {},
    "safe_default_used": false,
    "fallback_not_strong_evidence": true,
    "rationale": []
  }
}
```

### Constraints

- Do not hide fallback.
- Do not treat fallback as strong visual evidence.
- Do not alter fallback selection behavior unless explicitly scoped later.

### Validation

Focused tests must prove fallback is visible and penalizable by later confidence.

## 14. Workstream 7: Diversity And Repetition Guard

### Goal

Make visual repetition and low-diversity risk visible.

### Required Behavior

Detect:

- same asset reused across segments.
- same category repeated without rationale.
- generic category overuse.
- weak hook/setup/payoff visual progression.
- deterministic batch signature constraints where available.

### Required Output

Additive structure:

```json
{
  "asset_diversity": {
    "repetition_risk_level": "low | medium | high",
    "same_asset_reused": false,
    "category_repetition": [],
    "progression_level": "low | medium | high",
    "rationale": []
  }
}
```

### Constraints

- Do not introduce randomness.
- Do not mutate batch/global selector state beyond existing runtime behavior.
- Do not alter selection in this workstream.

### Validation

Focused tests must cover repeated asset, repeated category, healthy progression, and deterministic replay.

## 15. Workstream 8: Confidence Calibration

### Goal

Add evidence-backed confidence that measures trust in the visual selection, not predicted content performance.

### Required Behavior

Confidence must consider:

- context completeness.
- catalog/source governance.
- visual intent completeness.
- semantic alignment.
- truthfulness/mismatch risk.
- fallback presence.
- diversity/repetition risk.
- selected asset metadata coverage.

### Required Output

Additive structure:

```json
{
  "confidence": 0.0,
  "confidence_level": "low | medium | high",
  "confidence_components": {
    "context_completeness": 0.0,
    "catalog_governance": 0.0,
    "semantic_alignment": 0.0,
    "visual_truthfulness": 0.0,
    "fallback_penalty": 0.0,
    "diversity_penalty": 0.0
  },
  "confidence_rationale": {
    "confidence_meaning": "trust_in_visual_selection",
    "penalties": [],
    "boundary_statement": "Asset confidence is not performance prediction."
  }
}
```

### Constraints

- Confidence must not be constant.
- Confidence must not be high under fallback/generic/mismatch conditions.
- Confidence must not predict performance.
- Confidence must not decide QC outcome.

### Validation

Focused tests must cover high-confidence aligned local selection, low-confidence fallback, mismatch penalty, diversity penalty, deterministic replay, and backward compatibility.

## 16. Workstream 9: Trace And Auditability Hardening

### Goal

Consolidate all Asset Selection v2.6 artifacts into a reconstructible `asset_trace`.

### Required Behavior

`asset_trace` must include:

- `asset_context_governance`
- `catalog_governance`
- `segment_visual_intent`
- `visual_alignment`
- `visual_truthfulness`
- `asset_fallback_honesty`
- `asset_diversity`
- `confidence_calibration`
- `final_asset_plan_rationale`
- `missing_or_degraded_inputs`
- `audit_summary`

### Required Output

Additive structure:

```json
{
  "asset_trace": {
    "asset_context_governance": {},
    "catalog_governance": {},
    "segment_visual_intent": {},
    "visual_alignment": {},
    "visual_truthfulness": {},
    "asset_fallback_honesty": {},
    "asset_diversity": {},
    "confidence_calibration": {},
    "final_asset_plan_rationale": {},
    "missing_or_degraded_inputs": [],
    "audit_summary": {
      "reconstructible": true,
      "required_sections_present": true,
      "silent_failure_indicators": []
    }
  }
}
```

### Constraints

- Do not recalculate selection.
- Do not alter confidence.
- Do not alter fallback.
- Do not alter selected assets.

### Validation

Focused tests must prove `asset_trace` reconstructs why each selected asset was emitted and exposes all missing/degraded inputs.

## 17. Workstream 10: Asset Selection Excellence Gate

### Goal

Create and execute the official Asset Selection Agent v2.6 Excellence Gate.

### Required Artifacts

- `docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_GATE.md`
- `tests/gates/agents/asset_selection/run_asset_selection_agent_v2_6_excellence_gate.py`
- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/final_verdict.json`

### Required Gate Dimensions

The gate must validate:

- runtime real
- context governed
- catalog/source governed
- segment visual intent explicit
- semantic alignment explicit
- visual truthfulness explicit
- fallback honest
- diversity/repetition guarded
- confidence calibrated
- traceability complete
- deterministic replay
- boundary preserved
- Strategy/core/orchestrator unchanged
- no fake visual evidence
- no silent failures

### Verdict

Expected likely outcome:

`GO_WITH_MONITORING`

Only if all critical checks pass and residuals are non-structural.

## 18. Required Test Philosophy

Every workstream must include focused tests proving:

- additive output fields exist.
- deterministic behavior.
- serialization.
- fallback honesty.
- no hidden Strategy/QC behavior.
- no core pipeline changes.
- no selected asset mutation unless explicitly allowed.
- backward compatibility.

Regression tests should include:

- `tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py`
- `tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py`
- `tests/agents/strategy/test_strategy_agent_phase2_unittest.py`
- `tests/agents/script/test_script_agent_phase2_unittest.py`
- `tests/agents/voice/test_voice_agent_service_phase2_5_unittest.py`

Add additional tests per workstream.

## 19. Residual Monitoring Candidates

Acceptable non-structural residuals may include:

- `ASSET_RUNTIME_CATALOG_COVERAGE_STILL_EXPANDING`
- `ASSET_VISUAL_METADATA_DEPTH_STILL_LIMITED`
- `ASSET_LONGITUDINAL_SELECTION_HISTORY_STILL_SHORT`
- `ASSET_EXTERNAL_PROVIDER_COVERAGE_NOT_IN_SCOPE`

Structural blockers must not be reclassified as residual monitoring.

## 20. Final Principle

Asset Selection must choose visuals that are explainable, semantically honest, and bounded by available evidence.

It must not make a visually attractive mismatch look like a correct decision.
