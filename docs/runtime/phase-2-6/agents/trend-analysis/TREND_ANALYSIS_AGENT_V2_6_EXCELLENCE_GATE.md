# TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_GATE

## 1. Purpose

`TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_GATE` is the formal validation gate for the Trend Analysis Agent after the Phase 2.6 excellence-hardening workstreams.

This gate validates Trend Analysis v2.6 as implemented. It must not mutate runtime behavior to make validation pass.

The gate determines whether Trend Analysis is:

- runtime-real
- source-governed
- evidence-backed
- provenance-aware
- freshness-disciplined
- confidence-calibrated
- shift-analysis meaningful
- downstream-utility clear
- traceable end-to-end
- fallback-honest
- deterministic under controlled inputs
- boundary-preserving
- free of silent failures

This gate is not a feature and is not a runtime behavior change. It is an audit artifact that can produce `GO`, `GO_WITH_MONITORING`, or `HOLD`.

## 2. Scope

In scope:

- Trend Analysis runtime service execution
- source governance policy
- evidence lineage and provenance
- freshness and validity state
- confidence calibration as trust in trend context
- retrospective shift analysis
- downstream utility clarification
- consolidated `trend_trace`
- fallback honesty
- deterministic replay
- Strategy and Asset boundary preservation
- backward-compatible `TrendAnalysisResult`

Out of scope:

- modifying Trend runtime logic to pass the gate
- modifying Strategy
- modifying Asset
- modifying Learning
- modifying Account Health
- modifying QC or Experiment
- modifying the orchestrator or core pipeline
- adding new external collection
- adding scraping
- using Trend as a decision authority
- converting failures into residual monitoring

Governance constraints:

```json
{
  "system_version": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "governance_model": "SUBSYSTEM_BASELINE_WITH_MONITORING",
  "change_policy": "FROZEN_UNLESS_GOVERNANCE_REOPEN",
  "no_core_modification": true,
  "no_strategy_mutation": true,
  "no_asset_mutation": true,
  "no_runtime_mutation_for_gate": true
}
```

## 3. Preconditions

The gate may run only after these Trend Analysis 2.6 workstreams exist:

- Source Governance Hardening
- Evidence Lineage And Provenance Hardening
- Freshness And Validity Hardening
- Confidence Calibration Hardening
- Shift Analysis Hardening
- Downstream Utility Clarification
- Trace And Auditability Hardening

Required code surfaces:

- `backend/app/creative/agents/trend_analysis/models.py`
- `backend/app/creative/agents/trend_analysis/service.py`
- `backend/app/creative/agents/trend_analysis/source_governance.py`
- `backend/app/creative/agents/trend_analysis/provenance.py`
- `backend/app/creative/agents/trend_analysis/freshness.py`
- `backend/app/creative/agents/trend_analysis/confidence_calibration.py`
- `backend/app/creative/agents/trend_analysis/shift_analysis.py`
- `backend/app/creative/agents/trend_analysis/downstream_utility.py`
- `backend/app/creative/agents/trend_analysis/trace_auditability.py`

Required validation command:

`python tests/gates/agents/trend_analysis/run_trend_analysis_agent_v2_6_excellence_gate.py`

Required output artifact:

`OUT/audit/trend_analysis_agent_v2_6_excellence_gate/final_verdict.json`

## 4. Evaluation Dimensions

The gate evaluates the following dimensions.

`runtime_real`

Means Trend Analysis executes through the real `TrendAnalysisAgentService`, not a stub.

Validated by controlled scenarios calling the public service and returning full `TrendAnalysisResult` objects.

Failure if Trend Analysis is mocked, cannot execute, or only emits fallback under valid governed input.

`source_governed`

Means allowed, rejected, ignored, selected, and fallback source policy decisions are explicit.

Validated by `collector_trace.source_governance`, source policy version, accepted source classes, rejected source handling, selected source class, source mix, and fallback-required semantics.

Failure if source policy is missing, unsupported source classes are accepted, or `safe_default` is treated as strong evidence.

`evidence_backed`

Means emitted Trend context is supported by evidence references and field-level provenance where available.

Validated by `TrendProfile.evidence`, `collector_trace.provenance`, `field_provenance`, `evidence_references`, and source mix.

Failure if emitted fields have fake source support, rejected sources support strong provenance, or fallback fields are inflated.

`freshness_disciplined`

Means freshness and validity semantics are explicit.

Validated by `collector_trace.freshness`, `collector_trace.validity`, per-source statuses, missing timestamp visibility, stale and expired source handling, cache usage mode, and validity status.

Failure if stale, expired, or missing timestamp evidence is hidden or treated as fresh.

`confidence_calibrated`

Means calibrated confidence measures trust in the emitted trend context, not trend strength or expected performance.

Validated by `collector_trace.confidence_calibration`, confidence variation across scenarios, penalties, rationale, and low confidence under fallback or degraded evidence.

Failure if confidence is constant, high under fallback, high under expired/missing evidence, or lacks rationale.

`shift_analysis_meaningful`

Means shift analysis is retrospective, field-level, severity-aware, and non-predictive.

Validated by `collector_trace.shift_analysis`, baseline availability, field changes, weak variations, meaningful shifts, severity, operational significance, and legacy shift fields.

Failure if shift analysis forecasts, fabricates baseline, hides changed fields, or treats weak variation as strong shift.

`downstream_utility_clear`

Means Trend explains how fields may be interpreted by downstream consumers without commanding behavior.

Validated by `collector_trace.downstream_utility`, field relevance, interpretation modes, advisory authority cap, consumer summary, and boundary statement.

Failure if Trend creates Strategy decisions, Asset decisions, constraints, publishability logic, or authority above advisory.

`traceability_complete`

Means Trend output can be reconstructed from artifacts.

Validated by `collector_trace.trend_trace` sections: source governance, provenance, freshness, validity, confidence calibration, shift analysis, downstream utility, fallback, final trend profile rationale, missing or degraded inputs, and audit summary.

Failure if critical trace sections are missing, contradictory, or silently marked reconstructible.

`fallback_honest`

Means fallback and `safe_default` are explicit, low-confidence, and not presented as strong evidence.

Validated by fallback scenarios, fallback trace, safe_default source governance, provenance fallback fields, confidence penalties, and `trend_trace.fallback`.

Failure if fallback is hidden or inflated into strong trend intelligence.

`boundary_preserved`

Means Trend remains a bounded context provider and does not become Strategy, Asset, Learning, QC, or Publisher.

Validated by result shape, downstream utility authority cap, absence of Strategy/Profile decisions in Trend output, and no new constraints.

Failure if Trend emits hidden enforcement, strategy decisions, publishability decisions, or core ownership.

`determinism_where_required`

Means controlled identical input produces identical `TrendProfile`, confidence calibration, shift analysis, downstream utility, and `trend_trace`.

Validated by deterministic replay.

Failure if stable outputs drift without input change.

`silent_failures_detected`

Means missing critical sections, fake confidence, hidden fallback, fake evidence, boundary violations, and non-determinism are detected.

Validated by checklist aggregation and blocking failure derivation.

Failure if critical defects exist while the verdict passes.

## 5. Controlled Scenario Battery

The runner executes controlled inputs through the real Trend Analysis service.

Required scenarios:

- `fresh_governed_profile`: fresh current-store profile, governed source, evidence references, high trust context
- `hybrid_source_mix`: manual curation plus approved external reference source records, source mix visible
- `stale_profile`: stale source timestamp, stale state visible, confidence reduced or capped
- `expired_profile`: expired source timestamp, expired state visible, validity degraded or invalid
- `missing_timestamp_profile`: source timestamp missing, missing timestamp visible
- `safe_default_fallback`: missing profile, explicit fallback, `safe_default` not strong evidence
- `strong_shift`: baseline differs materially from current source assembly, strong shift visible
- `weak_shift`: list reorder only, weak variation without strong shift
- `determinism_replay`: same input produces stable output
- `backward_compatibility`: required public fields remain present

Controlled inputs are allowed. Stubbing Trend Analysis itself is not allowed.

## 6. Checklist

The runner validates a checklist across these blocks:

- runtime execution
- source governance
- provenance and evidence lineage
- freshness and validity
- confidence calibration
- shift analysis
- downstream utility
- trace completeness
- fallback honesty
- boundary preservation
- deterministic replay
- backward compatibility
- silent failure detection
- global consistency

Checklist release rule:

```json
{
  "critical_failures": 0,
  "soft_failures": "explicit_and_bounded",
  "fake_confidence": false,
  "silent_failures": false,
  "boundary_violations": false,
  "verdict": "ONLY_THEN_PROCEED"
}
```

Any failed checklist block becomes a blocking failure.

## 7. Verdict Semantics

`GO`

Allowed only when all critical dimensions pass and no meaningful residual monitoring remains.

`GO_WITH_MONITORING`

Allowed when all critical dimensions pass and remaining issues are explicit, bounded, non-structural, or related to short runtime history, producer coverage, or long-horizon trend source diversity.

`HOLD`

Required when any critical failure exists, including trace incompleteness, fake confidence, hidden fallback, source governance failure, provenance inflation, unsafe freshness handling, non-deterministic replay, boundary violation, or silent failure.

The expected likely outcome is `GO_WITH_MONITORING`, but the runner must derive the verdict from evidence.

## 8. Failure Conditions

The gate must return `HOLD` if any of the following occur:

- Trend Analysis cannot execute through the real service
- source governance is missing
- unsupported source classes are accepted
- `safe_default` is treated as strong evidence
- provenance is fake, missing, or inflated
- rejected sources support strong fields
- stale, expired, or missing timestamp inputs are hidden
- calibrated confidence is constant or fake
- fallback receives high confidence
- shift analysis forecasts or hides changed fields
- downstream utility creates hidden authority
- `trend_trace` is incomplete for governed non-fallback outputs
- fallback is hidden
- deterministic replay fails
- Trend crosses into Strategy, Asset, QC, Learning, Publisher, or core ownership
- silent failure indicators are present without being classified as blockers

## 9. Output Artifacts

The runner writes:

- `OUT/audit/trend_analysis_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/trend_analysis_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/trend_analysis_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/trend_analysis_agent_v2_6_excellence_gate/metrics.json`

Minimum final verdict shape:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "agent": "trend_analysis",
  "audit_type": "TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_GATE",
  "verdict": "GO_WITH_MONITORING",
  "runtime_real": true,
  "source_governed": true,
  "evidence_backed": true,
  "freshness_disciplined": true,
  "confidence_calibrated": true,
  "shift_analysis_meaningful": true,
  "downstream_utility_clear": true,
  "traceability_complete": true,
  "fallback_honest": true,
  "boundary_preserved": true,
  "determinism_where_required": true,
  "silent_failures_detected": false,
  "scenario_results": {},
  "checklist_results": {},
  "metrics": {},
  "blocking_failures": [],
  "residual_monitoring": []
}
```

## 10. Final Criteria

Trend Analysis v2.6 may pass only if the gate proves:

- runtime execution is real
- source governance is explicit
- provenance is evidence-backed and honest
- freshness and validity are disciplined
- confidence is calibrated and non-constant
- shift analysis is retrospective and meaningful
- downstream utility is explanatory and non-authoritative
- `trend_trace` reconstructs governed non-fallback output formation
- fallback remains explicit and low-authority
- deterministic replay holds
- Trend remains within its boundary

Final rule:

> Trend Analysis is ready for v3 only when it can explain why a `TrendProfile` was emitted without pretending weak, stale, fallback, or bounded evidence is stronger than it is.
