# Phase 2.6 Release Record

Consolidated record for Phase 2.6 plans, gates, agent excellence workstreams and release decisions.

## Consolidation Notice

This file consolidates documentation that was previously split across multiple legacy files. The source contents are preserved below for auditability.

## Source Files

- `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/master-gates/CORTAI_ABSOLUTE_MASTER_GATE_PRE_WAVE_2.md`
- `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md`
- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_FINAL_MASTER_GATE.md`
- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH.md`
- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_1_MASTER_GATE.md`
- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_2_MASTER_GATE.md`
- `docs/runtime/phase-2-6/master/PHASE_2_6_WAVE_2_OUTPUT_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/reports/PHASE_2_6_WAVES_1_AND_2_REPORT.md`
- `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/video-qc/VIDEO_QC_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/video-qc/VIDEO_QC_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_PLAN.md`

## Consolidated Contents

---

## Source: `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE.md`

# ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE

## 1. Purpose

`ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE` is the formal validation gate for the Account Health Agent after the Phase 2.6 excellence-hardening workstreams.

The gate validates Account Health v2.6 as implemented. It must not mutate runtime behavior to make validation pass.

The gate exists to determine whether Account Health is:

- runtime-real
- telemetry-enriched
- risk-component explicit
- confidence-calibrated
- temporally aware
- safe under degraded input
- complete in constraint rationale
- traceable end-to-end
- deterministic under controlled input
- boundary-preserving
- `HOLD` authority preserving
- fallback-honest
- free of silent failures

This gate is not a feature and is not a runtime behavior change. It is an audit artifact that can produce `GO`, `GO_WITH_MONITORING`, or `HOLD`.

## 2. Scope

In scope:

- Account Health runtime service execution
- telemetry enrichment
- risk component scoring
- confidence calibration
- temporal health analysis
- degraded input and fail-safer behavior
- constraint rationale
- `health_trace`
- `decision_trace` backward compatibility
- `SAFE` / `CAUTION` / `HOLD` preservation
- `HOLD` authority preservation
- fallback honesty
- deterministic replay

Out of scope:

- modifying Account Health runtime logic to pass the gate
- modifying Strategy
- modifying Learning
- modifying QC
- modifying Experiment
- modifying Script, Voice, Asset, Editor, or Publisher
- modifying the orchestrator or core pipeline
- introducing new Account Health authority
- weakening checks to obtain a passing verdict

Governance constraints:

```json
{
  "system_version": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "governance_model": "SUBSYSTEM_BASELINE_WITH_MONITORING",
  "change_policy": "FROZEN_UNLESS_GOVERNANCE_REOPEN",
  "no_core_modification": true,
  "no_strategy_mutation": true,
  "no_runtime_mutation_for_gate": true
}
```

## 3. Preconditions

The gate may run only after these Account Health 2.6 workstreams exist:

- Telemetry Enrichment
- Risk Component Scoring
- Confidence Calibration
- Temporal Health Analysis
- Degraded Input And Fail-Closed Behavior
- Constraint Rationale Hardening
- Trace And Auditability Hardening

Required code surfaces:

- `backend/app/creative/agents/account_health/models.py`
- `backend/app/creative/agents/account_health/service.py`
- `backend/app/creative/agents/account_health/telemetry_enrichment.py`
- `backend/app/creative/agents/account_health/risk_components.py`
- `backend/app/creative/agents/account_health/confidence_calibrator.py`
- `backend/app/creative/agents/account_health/temporal_health.py`
- `backend/app/creative/agents/account_health/degraded_input_policy.py`
- `backend/app/creative/agents/account_health/constraint_rationale.py`
- `backend/app/creative/agents/account_health/health_trace.py`

Required validation command:

`python tests/gates/agents/account_health/run_account_health_agent_v2_6_excellence_gate.py`

Required output artifact:

`OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json`

## 4. Evaluation Dimensions

The gate evaluates the following dimensions.

`runtime_real`

Means Account Health executes through the real `AccountHealthAgentService`, not a stub.

Validated by controlled scenarios calling the public service and returning full `AccountHealthResult` objects.

Failure if Account Health is mocked, cannot execute, or returns only fallback under valid input.

`telemetry_enriched`

Means telemetry lineage, freshness, source status distribution, available signals, missing signals, and degraded input mode are visible.

Validated by `telemetry_summary` and `health_trace.telemetry_lineage`.

Failure if telemetry is absent from artifacts or missing/stale/degraded inputs are hidden.

`risk_components_explicit`

Means all required risk components are present and explainable.

Validated by `risk_score`, `risk_components`, and the five required components: `publish_frequency_risk`, `performance_drop_risk`, `repetition_risk`, `low_quality_streak_risk`, `fallback_contamination_risk`.

Failure if any component lacks `score`, `level`, `reason_code`, `evidence_status`, or `rationale`.

`confidence_calibrated`

Means confidence measures trust in the Account Health decision, not account health itself.

Validated by confidence variation across scenarios, confidence components, confidence rationale, and low confidence under missing or degraded telemetry.

Failure if confidence is constant, high under weak evidence, or lacks rationale.

`temporal_health_real`

Means Account Health classifies observed posture movement without forecasting.

Validated by controlled `degrading`, `recovering`, `volatile`, and `insufficient_evidence` scenarios.

Failure if temporal classification is missing, fake, non-deterministic, or treats insufficient evidence as stable.

`degraded_input_safe`

Means missing, stale, degraded, and contradictory inputs do not silently become fully trusted `SAFE`.

Validated by degraded input scenarios, `degraded_input_decision`, and `decision_trace.degraded_input_policy`.

Failure if degraded input is hidden, `SAFE` remains fully trusted under severe missing/degraded telemetry, or missing input becomes automatic `HOLD`.

`constraints_rationale_complete`

Means every emitted `recommended_constraint` has exactly one rationale.

Validated by `constraint_rationale`, interpretation mode, severity, source, evidence summary, downstream interpretation, and rationale text.

Failure if a constraint is orphaned, duplicated, or lacks evidence linkage.

`traceability_complete`

Means Account Health can be reconstructed from artifacts.

Validated by `health_trace` sections: telemetry lineage, risk assessment, confidence calibration, temporal health, degraded input policy, constraint rationale, final decision rationale, downgraded or missing inputs, and audit summary.

Failure if any required section is missing or contradictory.

`hold_authority_preserved`

Means `HOLD` remains a hard upstream stop and is never downgraded.

Validated by high-risk and severe degraded scenarios returning `HOLD`, `block_generation`, blocking constraint rationale, and visible `hold_authority_invoked`.

Failure if `HOLD` is downgraded or blocking semantics disappear.

`boundary_preserved`

Means Account Health remains an upstream posture governor and does not become Strategy, QC, Learning, or a rollout engine.

Validated by static artifact shape and absence of Strategy mutation, publishability decision, QC replacement, Learning policy ownership, or hidden enforcement.

Failure if Account Health creates downstream strategy decisions or replaces another subsystem's authority.

`determinism_where_required`

Means controlled identical input produces identical decision, risk score, confidence, temporal health, constraint rationale, and health trace.

Validated by deterministic replay.

Failure if outputs change without input change.

`fallback_honest`

Means fallback or degraded default behavior is explicit.

Validated by cold-start fallback and fallback trace fields.

Failure if fallback is hidden or represented as evidence-backed posture.

`silent_failures_detected`

Means missing critical sections, orphan constraints, fake confidence, hidden degraded input, boundary violations, and non-determinism are detected.

Validated by checklist aggregation and blocking failure derivation.

Failure if critical defects exist while the verdict passes.

## 5. Controlled Scenario Battery

The runner executes controlled inputs through the real Account Health service.

Required scenarios:

- `clean_safe`: rich `REAL` telemetry, low risk, final decision `SAFE`, no degraded adjustment
- `moderate_risk_caution`: moderate risk evidence, final decision `CAUTION`, constraints with rationale
- `high_risk_hold`: high-risk threshold evidence, final decision `HOLD`, blocking rationale visible
- `missing_telemetry_safe_not_trusted`: mostly absent telemetry, no hidden missing evidence, low confidence or explicit degraded trace
- `moderate_degraded_safe_to_caution`: base `SAFE`, moderate degraded input, final decision `CAUTION`, adjustment visible
- `severe_degraded_high_risk_to_hold`: severe degradation plus fallback contamination/high risk, final decision `HOLD`, adjustment visible
- `temporal_degrading`: temporal classification `degrading`
- `temporal_recovering`: temporal classification `recovering`
- `temporal_volatile`: temporal classification `volatile`
- `insufficient_temporal_evidence`: temporal classification `insufficient_evidence`
- `determinism_replay`: same input produces stable output
- `backward_compatibility`: required public result fields remain present

Controlled inputs are allowed. Stubbing Account Health itself is not allowed.

## 6. Checklist

The runner validates a checklist across these blocks:

- telemetry enrichment
- risk components
- confidence calibration
- temporal health
- degraded input policy
- constraints rationale
- trace completeness
- authority preservation
- determinism
- fallback honesty
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

Allowed when all critical dimensions pass and remaining issues are explicit, bounded, non-structural, or related to short runtime history or telemetry producer coverage.

`HOLD`

Required when any critical failure exists, including trace incompleteness, fake confidence, hidden degraded input, orphan constraint, broken `HOLD`, non-deterministic replay, boundary violation, or silent failure.

The expected likely outcome is `GO_WITH_MONITORING`, but the runner must derive the verdict from evidence.

## 8. Failure Conditions

The gate must return `HOLD` if any of the following occur:

- Account Health cannot execute through the real service
- telemetry lineage is missing
- risk components are incomplete
- confidence is constant or fake
- missing/degraded telemetry is hidden
- insufficient temporal evidence is treated as stable
- degraded input adjustment is not traceable
- severe degraded high-risk input fails to hold
- `HOLD` is downgraded
- any `recommended_constraint` lacks exactly one rationale
- `health_trace` is incomplete
- `decision_trace` backward compatibility breaks
- fallback is hidden
- deterministic replay fails
- Account Health crosses into Strategy, QC, Learning, or core ownership
- silent failure indicators are present

## 9. Output Artifacts

The runner writes:

- `OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/account_health_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/account_health_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/account_health_agent_v2_6_excellence_gate/metrics.json`

Minimum final verdict shape:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "agent": "account_health",
  "audit_type": "ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE",
  "verdict": "GO_WITH_MONITORING",
  "runtime_real": true,
  "telemetry_enriched": true,
  "risk_components_explicit": true,
  "confidence_calibrated": true,
  "temporal_health_real": true,
  "degraded_input_safe": true,
  "constraints_rationale_complete": true,
  "traceability_complete": true,
  "hold_authority_preserved": true,
  "boundary_preserved": true,
  "determinism_where_required": true,
  "fallback_honest": true,
  "silent_failures_detected": false,
  "scenario_results": {},
  "checklist_results": {},
  "metrics": {},
  "blocking_failures": [],
  "residual_monitoring": []
}
```

## 10. Final Criteria

Account Health v2.6 may pass only if the gate proves:

- runtime execution is real
- telemetry is enriched and lineage-aware
- risk components are explicit and explainable
- confidence is calibrated and non-constant
- temporal health is real and bounded
- degraded input is explicit and safe
- constraints are fully rationalized
- `health_trace` reconstructs the decision
- `decision_trace` remains backward-compatible
- `HOLD` authority is preserved
- fallback is honest
- determinism holds
- Account Health remains within its boundary

Final rule:

> Account Health is ready for v3 only when it can explain why execution should proceed, proceed cautiously, or stop without becoming the system's strategic brain.


---

## Source: `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md`

# ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN

## 1. Executive Summary

`Account Health Agent v2.6` is the second Wave 1 excellence artifact in the Phase 2.6 hardening program, following the Learning Agent v2.6 gate result:

`OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`

Current Learning status:

```json
{
  "agent": "learning",
  "phase": "2.6",
  "verdict": "GO_WITH_MONITORING",
  "release_state": "READY_FOR_V3_WITH_MONITORING"
}
```

Account Health enters Phase 2.6 because it is the upstream runtime posture governor. It decides whether the account and runtime context should proceed normally, proceed with constraints, or stop before downstream creative execution.

Account Health is not:
- a strategy engine
- a learning engine
- a QC agent
- a content quality judge
- a publishability judge
- a full risk platform
- the system's strategic brain

Account Health owns the bounded `SAFE` / `CAUTION` / `HOLD` posture surface and the upstream ability to constrain or stop execution before Strategy, Script, Voice, Asset, Editor, Render, and QC consume downstream context.

Phase 2.6 must strengthen Account Health because weak health posture contaminates every downstream decision. A false `SAFE` can allow the runtime to optimize under unsafe or degraded context. An excessive `HOLD` can suppress useful execution. A shallow `CAUTION` can produce constraints without enough evidence or rationale.

Target Account Health state after Phase 2.6:
- evidence-backed
- telemetry-rich
- temporally aware
- confidence-aware
- safer under degraded input
- stronger as an upstream runtime governor
- ready for v3 with monitoring

Canonical principle:

> Account Health must become better at deciding when the system should proceed, proceed cautiously, or stop - without becoming the system's brain.

## 2. Current State Of Account Health

Account Health v2 is already a real governed subsystem.

Current proven capabilities:
- it is runtime-real
- it runs upstream of Strategy
- it returns `SAFE`, `CAUTION`, or `HOLD`
- `HOLD` can block execution early
- `SAFE` and `CAUTION` allow execution to continue
- `recommended_constraints` can propagate downstream
- `decision_trace` is exposed
- `input_summary` is exposed
- fallback is explicit
- controlled validation is deterministic
- baseline status is `ACTIVE_WITH_MONITORING`

Authoritative baseline references:
- `docs/runtime/baselines/account-health/ACCOUNT_HEALTH_AGENT_SYSTEM_BIBLE_PHASE1.md`
- `docs/runtime/baselines/account-health/ACCOUNT_HEALTH_AGENT_BASELINE_OPERATION_RULES_v1_0.md`
- `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`
- `OUT/audit/account_health_agent_v2_standalone_governance_decision/final_verdict.json`
- `OUT/audit/account_health_agent_v2_baseline_promotion_verdict.json`

Current governed classification:

```json
{
  "agent": "account_health",
  "runtime_real": true,
  "authority": "upstream_safe_caution_hold",
  "hold_authority": "operational",
  "recommended_constraints": "propagated",
  "traceability": "present",
  "baseline_status": "ACTIVE_WITH_MONITORING",
  "phase_2_6_target": "telemetry_rich_confidence_aware_temporally_credible"
}
```

Current residues:
- standalone runtime history is still short
- telemetry richness is still limited
- thresholds are still comparatively simple
- confidence is not yet mature enough
- temporal trend of account health can be stronger
- degraded-input behavior can be stricter and more explicit
- `recommended_constraints` can become more evidence-backed
- `decision_trace` can become more reconstructible

These residues are not evidence that Account Health is broken. They are evidence that the subsystem is stable enough to harden, but not yet excellence-grade for v3 expansion.

## 3. Correct Boundary Of Account Health In Phase 2.6

Account Health 2.6 must preserve the current governance model:

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

### 3.1 Account Health Owns

Account Health may own:
- account and runtime posture evaluation
- `SAFE` / `CAUTION` / `HOLD`
- health constraints
- early blocking authority
- health decision trace
- health telemetry interpretation
- degraded-input safety behavior
- health-specific confidence reporting
- health-specific threshold explainability
- health-specific temporal posture classification

### 3.2 Account Health Does Not Own

Account Health must not own:
- Strategy policy
- Learning policy
- content quality scoring
- publishability
- experiment assignment
- trend interpretation
- Script decisions
- Voice decisions
- Asset decisions
- Editor decisions
- final QC
- winner selection
- rollout optimization
- external publishing automation

Boundary rule:

> Account Health may constrain Strategy, but it must not become Strategy.

Corollary:

> Account Health should make downstream execution safer, not strategically autonomous.

## 4. Why Account Health Must Be Hardened Before v3

v3 will increase autonomy, complexity, and operational pressure. The runtime should not expand while its first upstream posture gate remains only moderately telemetry-rich.

Account Health is high leverage because it decides whether downstream agents should execute under the current account/runtime conditions.

Hardening Account Health before v3 is necessary because:
- v3 may increase execution frequency, scenario diversity, and cross-agent coupling
- downstream agents may optimize under unsafe context if Account Health returns a false `SAFE`
- weak telemetry can hide degrading account conditions
- shallow threshold explanations make `CAUTION` and `HOLD` harder to audit
- over-aggressive `HOLD` can suppress valid execution
- under-aggressive `HOLD` can allow repeated downstream waste
- degraded input can silently become `SAFE` if not handled with discipline
- Strategy depends on Account Health constraints without owning Health's evidence
- v3 requires stronger account posture awareness before any expansion of runtime autonomy

The v3 risk is not only that Account Health misses a severe state. The larger risk is that it emits plausible but under-evidenced posture signals that downstream agents treat as stable operating truth.

## 5. Current Deficits To Fix

Phase 2.6 must address the following Account Health deficits.

### 5.1 Telemetry Richness

Current telemetry is useful but not yet mature enough for v3-grade posture governance.

Deficit:
- Account Health can still operate from limited or narrow input surfaces

Required fix:
- richer real telemetry summaries should be available when producers exist, including publish history, QC/reject history, failure history, fallback contamination, and repetition or format risk where available

### 5.2 Temporal Awareness

Current Account Health posture is not yet strongly temporal.

Deficit:
- recent degradation, recovery, volatility, and stale posture evidence are not sufficiently explicit

Required fix:
- Account Health should classify posture trend as `stable`, `degrading`, `recovering`, or `volatile` without forecasting

### 5.3 Confidence Calibration

Current confidence semantics are not mature enough for stronger downstream trust.

Deficit:
- Health posture can be emitted without enough explicit confidence basis around freshness, source count, consistency, and telemetry richness

Required fix:
- confidence should be evidence-backed and conservative under sparse, stale, or contradictory telemetry

### 5.4 Threshold Explainability

Current threshold logic is deterministic but still comparatively simple.

Deficit:
- threshold decisions can be correct but insufficiently explanatory for v3-grade audit

Required fix:
- threshold evaluations should explain which component triggered posture movement and why the final status was proportionate

### 5.5 Degraded Input Behavior

Current degraded-input behavior should become more fail-closed.

Deficit:
- missing telemetry must not silently become a fully justified `SAFE`

Required fix:
- degraded input should be explicit, should lower confidence, and may produce `CAUTION` unless safe evidence exists

### 5.6 Recommended Constraints Rationale

Current `recommended_constraints` can propagate but should become more evidence-backed.

Deficit:
- constraints may not always carry enough reason and evidence context

Required fix:
- every recommended constraint should have a rationale, source, proportionality statement, and relationship to the risk component that produced it

### 5.7 Decision Trace Reconstructability

Current traces exist, but Phase 2.6 requires stronger reconstruction.

Deficit:
- an auditor should be able to reconstruct the Health decision from telemetry lineage, risk components, threshold trace, confidence trace, and final rationale

Required fix:
- Account Health must expose a coherent `health_trace` without turning trace into a second hidden reasoning engine

### 5.8 Monitoring Residues

Account Health still carries monitoring-class residues.

Deficit:
- standalone runtime history is still short and telemetry richness remains bounded

Required fix:
- Phase 2.6 must reduce these residues where real evidence exists and preserve them honestly where long-horizon runtime evidence remains limited

## 6. Phase 2.6 Objectives For Account Health

Account Health 2.6 objectives:
- improve real telemetry use
- improve telemetry lineage
- improve confidence calibration
- improve temporal posture analysis
- improve threshold explainability
- improve degraded-input behavior
- improve recommended constraints rationale
- preserve deterministic behavior
- preserve `HOLD` authority
- preserve the `SAFE` / `CAUTION` / `HOLD` public contract
- preserve Strategy ownership
- preserve Learning ownership
- preserve QC ownership
- preserve Experiment ownership
- prepare Account Health for v3 with monitoring

Account Health 2.6 must not optimize for sophistication. It must optimize for safer, clearer, more evidence-backed posture governance.

Target state:

```json
{
  "account_health_v2_6": {
    "telemetry_enriched": true,
    "risk_components_explicit": true,
    "confidence_calibrated": true,
    "temporal_health_real": true,
    "degraded_input_safe": true,
    "constraints_rationale_complete": true,
    "traceability_complete": true,
    "hold_authority_preserved": true,
    "boundary_preserved": true
  }
}
```

## 7. Workstreams Of Account Health 2.6

Account Health 2.6 must be implemented in bounded workstreams. These workstreams are ordered to avoid overbuilding the agent before its evidence surface is mature.

### 7.1 Telemetry Enrichment

Objective:
- strengthen the input assembly available to Account Health without opening the core pipeline or inventing external telemetry

Scope:
- better input assembly
- publish history
- metrics trends
- QC/reject history if available
- fallback/failed-run history
- repetition or format risk if available

Rules:
- only real available evidence may be used
- missing producers must remain explicit
- no placeholder telemetry may be represented as real evidence
- telemetry enrichment must remain Account Health-specific

Expected result:
- Account Health receives a richer, auditable telemetry surface and can distinguish strong posture evidence from thin posture evidence.

### 7.2 Risk Component Scoring

Objective:
- decompose Account Health risk into bounded, explainable components

Required components:
- `publish_frequency_risk`
- `performance_drop_risk`
- `repetition_risk`
- `low_quality_streak_risk`
- `fallback_contamination_risk`

Rules:
- component scores must be deterministic
- component scores must be explainable
- component scores must not become opaque risk modeling
- aggregate risk must remain bounded by the `SAFE` / `CAUTION` / `HOLD` contract

Expected result:
- Account Health can explain which risk dimension produced `SAFE`, `CAUTION`, or `HOLD`.

### 7.3 Confidence Calibration

Objective:
- make Account Health confidence evidence-backed and conservative

Confidence should consider:
- telemetry richness
- telemetry freshness
- telemetry source count
- source consistency
- missing input rate
- stale input rate
- contradiction between sources
- fallback contamination

Rules:
- confidence must be low when telemetry is sparse, stale, contradictory, or degraded
- confidence must not become a vanity score
- confidence must not hide uncertainty
- `SAFE` with low confidence must be treated as a governance concern, not as healthy proof

Expected result:
- Account Health can distinguish a high-confidence `SAFE` from a low-confidence pass-through state.

### 7.4 Temporal Health Analysis

Objective:
- classify account posture trend over bounded windows without forecasting

Allowed temporal classifications:
- `stable`
- `degrading`
- `recovering`
- `volatile`

Rules:
- Account Health must not predict future outcomes
- Account Health must not become a time-series forecasting system
- temporal classification must be based on recent posture evidence and bounded history
- temporal volatility must lower confidence or strengthen caution when justified

Expected result:
- Account Health can explain whether the current posture is stable, worsening, recovering, or unstable.

### 7.5 Degraded Input And Fail-Closed Behavior

Objective:
- ensure missing, stale, or degraded telemetry never silently becomes a fully justified `SAFE`

Required behavior:
- missing telemetry must be explicit
- fallback must be explicit
- degraded input may return `CAUTION` unless safe evidence exists
- severe degraded input should prevent strong confidence
- fail-closed behavior must remain proportional and deterministic

Rules:
- do not overblock without evidence
- do not treat absence of evidence as proof of safety
- do not hide degraded producers behind default values

Expected result:
- Account Health becomes safer under incomplete input while preserving execution when evidence supports it.

### 7.6 Constraint Rationale Hardening

Objective:
- make every recommended constraint evidence-backed and proportional

Every recommended constraint should include:
- constraint key
- reason code
- linked risk component
- evidence reference or source summary
- proportionality rationale
- expected downstream interpretation

Rules:
- constraints must not become hidden Strategy directives
- constraints must not decide final creative profile
- constraints must remain advisory or constraining within Account Health authority
- Strategy remains the control layer that interprets constraints

Expected result:
- downstream consumers can see why a constraint exists and how strongly it should matter.

### 7.7 Trace And Auditability Hardening

Objective:
- make Account Health decisions reconstructible from artifacts

Trace should include:
- input lineage
- telemetry summary
- risk component trace
- threshold trace
- confidence trace
- temporal health trace
- degraded-input trace
- constraint rationale trace
- final decision rationale

Rules:
- no fake lineage
- no ornamental trace fields
- no hidden enforcement
- no removal of uncertainty
- trace must remain deterministic and serializable

Expected result:
- an auditor can reconstruct why Account Health returned `SAFE`, `CAUTION`, or `HOLD`.

## 8. Proposed Contract Evolution

Account Health 2.6 may evolve contracts only in additive, backward-compatible ways.

The public decision surface must remain:
- `SAFE`
- `CAUTION`
- `HOLD`
- `recommended_constraints`
- explicit fallback

### 8.1 Proposed `AccountHealthResult` Additions

Possible additive fields:

```json
{
  "confidence": 0.0,
  "risk_score": 0.0,
  "risk_components": {
    "publish_frequency_risk": {},
    "performance_drop_risk": {},
    "repetition_risk": {},
    "low_quality_streak_risk": {},
    "fallback_contamination_risk": {}
  },
  "telemetry_summary": {},
  "temporal_health": {
    "classification": "stable",
    "rationale": ""
  },
  "constraint_rationale": [],
  "degraded_input_mode": false,
  "health_trace": {}
}
```

### 8.2 Proposed `AccountHealthInput` Additions

Possible additive fields:

```json
{
  "telemetry_sources": [],
  "metric_window_summary": {},
  "qc_history_summary": {},
  "failure_history_summary": {},
  "format_repetition_summary": {},
  "telemetry_freshness": {}
}
```

### 8.3 Contract Rules

Contract evolution must follow these rules:
- no fake fields
- no required fields without a real producer
- no breaking current callers
- keep `SAFE` / `CAUTION` / `HOLD` stable
- keep `recommended_constraints` compatible
- keep fallback semantics explicit
- keep orchestrator `HOLD` enforcement unchanged
- keep Strategy as consumer of constraints, not executor of Health-owned strategy
- keep additive fields serializable in runtime artifacts

If a proposed field has no real evidence producer, it must not be required for the runtime path.

## 9. Validation Strategy For Account Health 2.6

Account Health 2.6 must be validated with unit tests, controlled batteries, integration validation, and a dedicated excellence gate.

Required validation scenarios:
- `SAFE` with strong clean telemetry
- `CAUTION` with moderate risk
- `HOLD` with high risk
- missing telemetry does not silently return fully justified `SAFE`
- stale telemetry reduces confidence
- contradictory telemetry lowers confidence
- degraded input path is explicit
- constraints are proportional to risk
- temporal `degrading` path
- temporal `recovering` path
- temporal `volatile` path
- deterministic same-input same-output behavior
- `HOLD` still blocks orchestrator before downstream generation
- Strategy receives constraints but retains ownership
- fallback remains explicit and honest
- no hidden enforcement is introduced

Validation layers:
- unit validation for risk components and confidence
- controlled scenario battery for `SAFE` / `CAUTION` / `HOLD`
- integration validation with orchestrator `HOLD`
- Strategy propagation validation
- trace completeness validation
- degraded-input validation
- determinism validation
- governance boundary validation

Acceptance rules:
- no fake confidence
- no silent fallback
- no `SAFE` from missing evidence without rationale
- no `HOLD` without evidence-backed reason
- no Strategy ownership transfer
- no QC ownership transfer
- no Learning ownership transfer
- no core pipeline mutation

## 10. Account Health Excellence Gate

At the end of Account Health 2.6, the subsystem must be evaluated by a dedicated gate.

Required documentation:

`docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE.md`

Required runner:

`tests/gates/agents/account_health/run_account_health_agent_v2_6_excellence_gate.py`

Required final artifact:

`OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json`

Minimum verdict schema:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "agent": "account_health",
  "audit_type": "ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "runtime_real": true,
  "telemetry_enriched": true,
  "risk_components_explicit": true,
  "confidence_calibrated": true,
  "temporal_health_real": true,
  "degraded_input_safe": true,
  "constraints_rationale_complete": true,
  "traceability_complete": true,
  "hold_authority_preserved": true,
  "boundary_preserved": true,
  "determinism_where_required": true,
  "fallback_honest": true,
  "silent_failures_detected": false,
  "blocking_failures": [],
  "residual_monitoring": []
}
```

Gate dimensions:
- `runtime_real`
- `telemetry_enriched`
- `risk_components_explicit`
- `confidence_calibrated`
- `temporal_health_real`
- `degraded_input_safe`
- `constraints_rationale_complete`
- `traceability_complete`
- `hold_authority_preserved`
- `boundary_preserved`
- `determinism_where_required`
- `fallback_honest`
- `silent_failures_detected`

Verdict semantics:
- `GO`: all critical dimensions pass and no meaningful residual risk remains
- `GO_WITH_MONITORING`: all critical dimensions pass and residuals are explicit, bounded, and non-structural
- `HOLD`: any critical dimension fails, boundary is violated, fallback is hidden, confidence is fake, or `HOLD` authority is broken

The gate must prove that Account Health is ready for v3 with monitoring. It must not merely confirm that existing tests pass.

## 11. What Account Health 2.6 Must Not Do

Account Health 2.6 must not:
- become Strategy
- become Learning
- become QC
- decide publishability
- decide final content quality
- decide experiment variants
- own rollout policy
- become a full platform risk engine
- create Publisher behavior
- integrate external expansion surfaces
- hide degraded input
- return `SAFE` from missing evidence without rationale
- use fake confidence
- create hidden enforcement
- overblock without evidence
- inject opaque scoring into downstream agents
- mutate the core pipeline
- replace downstream agent ownership
- convert constraints into mandatory Strategy directives

Forbidden failure modes:
- false `SAFE` due to missing telemetry
- false `HOLD` due to over-aggressive static thresholds
- `CAUTION` with vague or non-actionable constraints
- confidence without rationale
- telemetry without lineage
- trace without threshold reconstruction
- boundary drift into Strategy, Learning, QC, or Experiment

## 12. Exit Criteria

Account Health 2.6 is complete only when:
- telemetry is enriched with real available sources
- risk components are explicit
- confidence is calibrated
- temporal health classification is real
- degraded input is handled safely
- constraints have rationale
- trace reconstructs the decision
- `HOLD` still blocks early
- `SAFE` is justified by evidence
- `CAUTION` is proportionate to risk
- `HOLD` is evidence-backed
- fallback remains explicit
- determinism is preserved
- Strategy receives constraints without losing ownership
- Learning ownership remains preserved
- QC ownership remains preserved
- Experiment ownership remains preserved
- boundary is preserved
- the Account Health Excellence Gate passes

Final readiness target:

```json
{
  "account_health_agent_v2_6": {
    "telemetry_enriched": true,
    "risk_components_explicit": true,
    "confidence_calibrated": true,
    "temporal_health_real": true,
    "degraded_input_safe": true,
    "constraints_rationale_complete": true,
    "traceability_complete": true,
    "hold_authority_preserved": true,
    "boundary_preserved": true,
    "gate_verdict": "GO_OR_GO_WITH_MONITORING"
  }
}
```

The subsystem must not advance to the next Wave 1 agent until its gate result proves that remaining residues are explicit, bounded, and non-structural.

## 13. Final Position

Account Health 2.6 exists to make the runtime safer, more evidence-backed, and more honest about when execution should proceed, slow down, or stop.

It must strengthen upstream governance without becoming the system's strategic brain.


---

## Source: `docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_GATE.md`

# ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_GATE

## 1. Purpose

`ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_GATE` is the formal validation gate for the Asset Selection Agent after the Phase 2.6 excellence-hardening workstreams.

This gate validates Asset Selection Agent v2.6 as implemented. It must not mutate runtime behavior to make validation pass.

The gate determines whether Asset Selection is:

- runtime-real
- context-governed
- catalog/source-governed
- segment visual-intent aware
- metadata-alignment aware
- visual-truthfulness and mismatch-risk aware
- fallback and safe-default honest
- diversity and repetition guarded
- confidence-calibrated
- traceable end-to-end
- deterministic under controlled inputs
- boundary-preserving
- free of silent failures

This gate is not a feature and is not a runtime behavior change. It is an audit artifact that can produce `GO`, `GO_WITH_MONITORING`, or `HOLD`.

## 2. Scope

In scope:

- Asset Selection runtime service execution
- context governance
- local catalog and source governance
- hook/setup/payoff visual intent mapping
- metadata-only visual semantic alignment
- visual truthfulness and mismatch risk
- fallback and safe-default honesty
- diversity and repetition guard
- confidence calibration as trust in asset selection
- consolidated `asset_trace`
- deterministic replay
- backward-compatible `AssetSelectionResult`
- Strategy, Script, Voice, Trend, QC, orchestrator, and core boundary preservation

Out of scope:

- modifying Asset Selection runtime logic to pass the gate
- changing selected assets, ranking, or fallback behavior
- changing catalog contents
- adding external providers or image scraping
- using ML/image inspection
- modifying Strategy, Script, Voice, Trend, QC, orchestrator, or core pipeline
- adding publishability logic
- predicting performance
- converting Asset Selection into Strategy, QC, Publisher, or a visual intelligence authority

## 3. Preconditions

The gate may run only after these Asset Selection v2.6 workstreams exist:

- Asset Context Governance
- Catalog And Source Governance
- Segment Visual Intent Mapping
- Visual Semantic Alignment
- Visual Truthfulness And Mismatch Risk
- Fallback And Safe Default Honesty
- Diversity And Repetition Guard
- Confidence Calibration
- Trace And Auditability Hardening

Required code surfaces:

- `backend/app/creative/agents/asset_selection/models.py`
- `backend/app/creative/agents/asset_selection/service.py`
- `backend/app/creative/agents/asset_selection/context_governance.py`
- `backend/app/creative/agents/asset_selection/catalog_source_governance.py`
- `backend/app/creative/agents/asset_selection/segment_visual_intent.py`
- `backend/app/creative/agents/asset_selection/visual_semantic_alignment.py`
- `backend/app/creative/agents/asset_selection/visual_truthfulness.py`
- `backend/app/creative/agents/asset_selection/fallback_honesty.py`
- `backend/app/creative/agents/asset_selection/diversity_guard.py`
- `backend/app/creative/agents/asset_selection/confidence_calibration.py`
- `backend/app/creative/agents/asset_selection/trace_auditability.py`

Required validation command:

`python tests/gates/agents/asset_selection/run_asset_selection_agent_v2_6_excellence_gate.py`

Required output artifact:

`OUT/audit/asset_selection_agent_v2_6_excellence_gate/final_verdict.json`

## 4. Evaluation Dimensions

`runtime_real`

Means Asset Selection executes through `AssetSelectionAgentService`, not a stubbed result object.

Failure if the service cannot execute, valid local catalog inputs unexpectedly fall into fallback, or only synthetic result objects are inspected.

`context_governed`

Means upstream context is classified as available, used, ignored, missing, or degraded.

Failure if missing/degraded context is hidden or upstream context silently becomes Strategy authority.

`catalog_source_governed`

Means selected assets are checked against `local_catalog_only_v2_6`, eligible local catalog sources are explicit, and ineligible sources remain visible.

Failure if unsupported, legacy, or unregistered sources are accepted as strong governed evidence.

`segment_visual_intent_explicit`

Means hook/setup/payoff visual intent, narrative role, requested category, tags, completeness, and rationale are visible.

Failure if segment intent is missing, fake, or used to change ranking in the gate.

`visual_alignment_explicit`

Means category match, tag/query overlap, metadata availability, mismatch status, and metadata-only boundaries are visible.

Failure if mismatches are hidden, image inspection is claimed without evidence, or alignment mutates selection.

`visual_truthfulness_explicit`

Means generic assets, unsupported visual claims, fallback visual weakness, and mismatch risk are visible.

Failure if visually weak or unsupported assets are represented as strong truthfulness.

`fallback_safe_default_honest`

Means global and segment fallback are explicit and `safe_default` is treated as weak visual evidence.

Failure if fallback is hidden or safe default can produce high-confidence strong semantic evidence.

`diversity_repetition_guarded`

Means repeated asset paths, repeated categories, and weak hook/setup/payoff visual progression are visible.

Failure if repetition or weak progression is hidden, or if randomness is added to solve repetition.

`confidence_calibrated`

Means confidence measures trust in asset selection, varies by evidence state, and is not performance prediction.

Failure if confidence is constant, high under fallback/safe default, high under high mismatch, lacks rationale, or predicts performance.

`traceability_complete`

Means `asset_trace` reconstructs why the `AssetPlan` was emitted and what evidence was unavailable.

Failure if required trace sections are missing, reconstructibility is faked, mismatch is not exposed, fallback is hidden, or confidence lacks rationale.

`selection_ranking_fallback_preserved`

Means the gate validates audit layers without changing selected assets, ranking policy, or fallback behavior.

Failure if the gate or workstream changes asset choice, ranking semantics, or fallback selection to pass.

`boundary_preserved`

Means Asset Selection remains a visual selection and audit agent and does not become Strategy, Script, Voice, Trend, QC, Publisher, or core.

Failure if Asset Selection emits publishability decisions, Strategy commands, QC decisions, provider execution, external collection, or hidden enforcement.

`determinism_where_required`

Means controlled identical input produces stable asset selection, analyses, confidence, and trace.

Failure if stable output drifts without input changes.

`silent_failures_detected`

Means missing trace sections, fake confidence, hidden fallback, hidden mismatch, hidden safe default, boundary violations, and non-determinism are detected as blockers.

Failure if critical defects exist while the verdict passes.

## 5. Controlled Scenario Battery

The runner executes controlled scenarios through `AssetSelectionAgentService` and component probes using the same v2.6 evaluators where direct mismatch/repetition evidence is required.

Required scenarios:

- `strong_catalog_match`
- `missing_script_context`
- `empty_segment_context`
- `safe_default_fallback`
- `metadata_mismatch_probe`
- `repetition_probe`
- `confidence_cap_probe`
- `determinism_replay`
- `backward_compatibility`

Controlled component probes are allowed only to validate audit logic that cannot be reliably forced through the service without changing selector behavior. The service itself must not be stubbed.

## 6. Checklist

The runner validates:

- runtime execution
- context governance
- catalog/source governance
- segment visual intent
- metadata-only visual alignment
- visual truthfulness and mismatch risk
- fallback and safe-default honesty
- diversity and repetition guard
- confidence calibration
- trace completeness
- selection/ranking/fallback preservation
- boundary preservation
- deterministic replay
- backward compatibility
- critical Asset, Strategy, Script, Voice, Trend, orchestrator, and selector tests
- silent failure detection

Any failed critical checklist item becomes a blocking failure.

## 7. Verdict Semantics

`GO`

Allowed only when all critical dimensions pass and no meaningful residual monitoring remains.

`GO_WITH_MONITORING`

Allowed when all critical checks pass and remaining residuals are explicit, bounded, non-structural, and related to catalog coverage, visual history, or lack of pixel-level validation at the selection layer.

`HOLD`

Required if any critical failure, blocking failure, fake confidence, silent failure, boundary violation, non-determinism, incomplete trace, hidden fallback, hidden mismatch, safe-default inflation, selection mutation, ranking mutation, or core/downstream mutation is detected.

Expected likely verdict is `GO_WITH_MONITORING`. The runner must derive it from evidence and must not hardcode it.

## 8. Failure Conditions

Critical failures include:

- Asset Selection service cannot execute
- local catalog path unexpectedly falls back under valid input
- selected sources are not governed
- ineligible or unsupported sources are accepted as strong evidence
- visual intent is missing for emitted segments
- visual mismatch is hidden
- visual truthfulness risk is hidden
- fallback or safe default is hidden
- safe default produces high confidence
- confidence is constant or fake
- confidence predicts performance
- repeated assets/categories are hidden
- `asset_trace` is incomplete
- `asset_trace.audit_summary.reconstructible` is false for normal service output
- selected assets, ranking, or fallback behavior are mutated by the gate
- boundary violation
- non-deterministic replay
- failed critical test battery

## 9. Output Artifacts

The runner must write:

- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/metrics.json`

## 10. Final Criteria

The Asset Selection Agent v2.6 gate may recommend proceeding only when:

- Asset Selection runs through real `AssetSelectionAgentService`
- all v2.6 additive fields exist and serialize
- context governance is explicit
- catalog/source governance is explicit
- segment visual intent is explicit
- visual alignment is metadata-only and exposes mismatch
- visual truthfulness exposes weak/generic/unsupported visual evidence
- fallback and safe default remain explicit and weak
- diversity/repetition risk is visible
- confidence means trust in asset selection
- `asset_trace` reconstructs the emitted `AssetPlan`
- deterministic replay holds
- selected assets, ranking, and fallback behavior remain unchanged
- Asset Selection remains within its boundary

Final recommendation values:

- `PROCEED_TO_VIDEO_QC_AGENT_V2_6_PLAN`
- `HOLD_BEFORE_VIDEO_QC`


---

## Source: `docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_PLAN.md`

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


---

## Source: `docs/runtime/phase-2-6/master-gates/CORTAI_ABSOLUTE_MASTER_GATE_PRE_WAVE_2.md`

# CORTAI_ABSOLUTE_MASTER_GATE_PRE_WAVE_2

## 1. Purpose

`CORTAI_ABSOLUTE_MASTER_GATE_PRE_WAVE_2` is the final structural-risk gate before Phase 2.6 Wave 2.

This gate does not attempt to prove that the system is perfect. It proves whether the system is safe, governed, traceable, deterministic where required, and free of hidden structural failures before new Wave 2 work starts.

This is an audit artifact. It must not implement features, mutate runtime behavior, fix code to pass, modify agents, modify Strategy, modify Asset, modify QC, modify Experiment, modify the orchestrator, or change the core pipeline.

The gate exists to detect structural hidden risk, not to create readiness.

## 2. Scope

In scope:

- system governance and frozen-core integrity
- all Phase 2.6 Wave 1 agents: Learning, Account Health, Trend Analysis
- non-Wave-1 cognitive surfaces already active in the runtime: Strategy, Asset, Experiment, QC, Script, Voice, Editor, Novelty, Attribution
- creative orchestrator compatibility
- runtime and content pipeline smoke/integration health
- contract import and serialization integrity
- deterministic replay for controlled stable surfaces
- fallback honesty
- confidence honesty
- telemetry/evidence/provenance integrity
- degraded input visibility
- HOLD authority
- boundary preservation
- full trace and auditability
- residual monitoring classification
- consistency with canonical master gates and registry artifacts

Out of scope:

- starting Wave 2
- changing runtime behavior
- modifying any agent to pass the gate
- modifying Strategy or Asset behavior
- modifying the orchestrator or core pipeline
- converting failures into monitoring residues
- proving subjective perfection

## 3. Preconditions

Required canonical artifacts include:

- `OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/trend_analysis_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/phase_2_6_wave_1_master_gate/final_verdict.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/final_verdict.json`
- `OUT/audit/system_governance_registry.json`
- `OUT/audit/cortai_runtime_v2_5_all_agents_extreme_checklist/final_verdict.json`
- `OUT/audit/cortai_runtime_v2_5_max_integrity_gate/final_verdict.json`
- `OUT/audit/cortai_runtime_v2_5_final_audit/final_audit_report.json`
- `docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md`
- `docs/runtime/architecture/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md`

Required command:

`python tests/gates/phase_2_6/run_cortai_absolute_master_gate.py`

## 4. Absolute Checklist Blocks

### Block A - Governance And Kernel Neutrality

Validates that the core remains frozen, the governance model remains active, kernel/runtime surfaces remain neutral, and no artifact implies unauthorized mutation.

Fails if core governance is missing, false, contradictory, or if an agent appears to own decisions outside its boundary.

### Block B - Artifact Integrity

Validates required documents, runners, final verdicts, and JSON artifacts.

Fails if any mandatory artifact is absent or invalid.

### Block C - Contract Integrity Across Agents

Validates importability and serializability of representative contracts and runtime outputs for all major cognitive agents and integration surfaces.

Fails on broken imports, non-serializable representative outputs, missing required additive fields, or obvious backward compatibility breaks.

### Block D - Runtime Reality

Validates that controlled checks use real services or canonical runtime artifacts, not stubs standing in for agent behavior.

Fails if critical agents only pass through mock-like evidence or if fallback is emitted with valid controlled input without rationale.

### Block E - Telemetry And Evidence Integrity

Validates Learning evidence, Account Health telemetry, Trend source governance/provenance, and explicit fallback/degraded data handling.

Fails on fake evidence, hidden fallback, hidden missing data, or missing provenance.

### Block F - Confidence Honesty

Validates confidence is non-constant, low under fallback/missing/degraded input, and high only with sufficient evidence.

Fails on fake confidence, constant confidence, confidence without rationale, or high confidence under poor evidence.

### Block G - Temporal And Freshness Discipline

Validates Account Health temporal posture and Trend freshness/validity semantics.

Fails if stale data is treated as fresh, insufficient evidence is treated as stable, or expired/missing timestamp evidence is hidden.

### Block H - Degraded Input And Fail-Safety

Validates degraded input policy, HOLD preservation, SAFE-to-CAUTION/HOLD proportional behavior, and visible degradation traces.

Fails on HOLD downgrade, severe degraded SAFE, hidden degradation, or automatic overblocking without evidence.

### Block I - Risk Components

Validates Account Health risk components and evidence status.

Fails if any required risk component is missing, lacks score/evidence/rationale, or treats missing evidence as healthy.

### Block J - Trend Analysis Complete Check

Validates Trend source governance, provenance, freshness, confidence calibration, shift analysis, downstream utility, and `trend_trace` reconstructibility.

Fails on fake trend strength, invalid source acceptance, fallback inflation, predictive shift analysis, hidden authority, or incomplete trace.

### Block K - Trace And Auditability

Validates that Learning `learning_trace`, Account Health `health_trace`, and Trend `trend_trace` reconstruct their outputs.

Fails on missing sections, contradictory traces, `reconstructible = false`, or absent rationale.

### Block L - HOLD Authority

Validates that `HOLD` blocks downstream generation where applicable, is never downgraded, and remains visible in trace.

Fails if HOLD is ignored, downgraded, or lacks rationale.

### Block M - Determinism And Replay

Validates stable replay for controlled Learning, Account Health, Trend, and combined upstream scenarios.

Fails on unexplained drift.

### Block N - Boundary Preservation

Validates that Learning, Account Health, Trend, QC, Asset, Strategy, Experiment, and other agents retain their architectural ownership.

Fails on hidden Strategy ownership, hidden publishability authority, hidden QC authority, or core mutation.

### Block O - Full Test Battery

Runs a broad pre-Wave-2 test battery covering Wave 1 agents, Strategy, Asset, Experiment, Attribution, QC, Script, Voice, Editor, orchestrator, and content pipeline.

Fails on any critical test failure or unclassified timeout.

### Block P - Cross-Agent Consistency

Validates upstream relationships: Health outranks Learning/Trend, Trend remains context-only, Learning pressure remains bounded, Strategy remains control layer, and Asset consumes context without becoming authority.

Fails on authority conflict or contradictory traces.

### Block Q - Silent Failure Detection

Validates absence of hidden fallback, fake confidence, fake telemetry, fake provenance, orphan constraints, silent HOLD downgrade, inflated Trend fallback, and learning contamination dominance.

Fails if any silent structural failure indicator appears.

### Block R - Backward Compatibility

Validates old fields and contracts remain present while new Phase 2.6 fields are additive.

Fails on silent schema breakage.

### Block S - Residual Monitoring Classification

Collects residuals from canonical gates and permits only explicit, bounded, non-structural residues.

Fails if a structural blocker is classified as monitoring.

### Block T - Master Consistency

Compares the absolute gate with Wave 1, partial master, runtime master state, all-agents extreme checklist, max integrity gate, final audit, and governance registry.

Fails on contradiction, recent HOLD, governance drift, or missing canonical state.

### Block U - Final Release Decision

Derives final verdict from all previous blocks.

Fails if any hard-stop condition is violated.

## 5. Hard Stop Conditions

The gate must return `HOLD` if any of the following occur:

- `critical_failures > 0`
- silent failure detected
- fake confidence detected
- fake telemetry or fake provenance detected
- boundary violation detected
- non-determinism detected
- trace incomplete
- hidden fallback
- hidden degraded input
- orphan constraint
- HOLD downgrade
- invalid source accepted as strong Trend evidence
- fallback represented as strong evidence
- Strategy/core/orchestrator mutation implied by audit evidence
- critical test failure
- structural residual misclassified as monitoring

## 6. Verdict Semantics

`HOLD`:

Required when any hard-stop condition or critical block failure is detected.

`GO_WITH_MONITORING`:

Allowed when no structural hidden risk is detected and all remaining residues are explicit, bounded, non-structural, and operationally monitorable.

`GO`:

Allowed only when all blocks pass and no meaningful monitoring residues remain.

This gate expects `GO_WITH_MONITORING` as the likely healthy outcome. It must not hardcode that outcome.

## 7. Required Artifacts

The runner writes:

- `OUT/audit/cortai_absolute_master_gate/final_verdict.json`
- `OUT/audit/cortai_absolute_master_gate/checklist_results.json`
- `OUT/audit/cortai_absolute_master_gate/scenario_outputs.json`
- `OUT/audit/cortai_absolute_master_gate/metrics.json`
- `OUT/audit/cortai_absolute_master_gate/cross_agent_consistency.json`
- `OUT/audit/cortai_absolute_master_gate/contract_integrity.json`

## 8. Final Decision Rule

Proceed to Wave 2 only if:

- all critical blocks pass
- all child gates are `GO` or `GO_WITH_MONITORING`
- no fake confidence exists
- no silent failure exists
- no boundary violation exists
- no non-determinism exists
- no trace is incomplete
- no fallback is hidden
- HOLD authority is preserved
- residuals are explicit, bounded, and non-structural

Final recommendations:

- `PROCEED_TO_PHASE_2_6_WAVE_2_PLAN`
- `HOLD_BEFORE_WAVE_2`

## 9. Final Principle

The Absolute Master Gate does not prove perfection.

It proves whether the system is safe, governed, reconstructible, and free of hidden structural risk before Wave 2.


---

## Source: `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_GATE.md`

# LEARNING_AGENT_V2_6_EXCELLENCE_GATE

## 1. Purpose Of The Gate

`LEARNING_AGENT_V2_6_EXCELLENCE_GATE` is the formal validation gate for the Learning Agent after the Phase 2.6 excellence-hardening workstreams.

The gate exists to prove that Learning is no longer only functional. It must be:

- runtime-real
- evidence-backed
- confidence-calibrated
- temporally credible
- contamination-aware
- bounded in its pressure on Strategy
- traceable end-to-end
- deterministic under controlled input
- compliant with CORTAI runtime governance

The gate does not exist to confirm success by assumption. It exists to prove that success is real and to block progression if Learning creates false confidence, hidden pressure, untraceable policy, or boundary drift.

## 2. Scope

This gate validates the Learning Agent as a governed Phase 2.6 subsystem.

In scope:

- Learning runtime execution
- QC evidence integration
- confidence calibration
- temporal weighting
- contamination and noise protection
- strategy pressure clarification
- trace and auditability hardening
- Learning to Strategy boundary behavior
- fallback honesty
- deterministic replay

Out of scope:

- re-opening the core pipeline
- changing Strategy ownership
- changing Health authority
- changing QC authority
- adding new external integrations
- adding publisher behavior
- changing thresholds to force a pass

Governance constraints:

```json
{
  "system_version": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "governance_model": "SUBSYSTEM_BASELINE_WITH_MONITORING",
  "change_policy": "FROZEN_UNLESS_GOVERNANCE_REOPEN",
  "no_core_modification": true,
  "no_subsystem_mutation_without_reopen": true
}
```

## 3. Preconditions

The gate may run only after these Learning 2.6 workstreams exist:

- QC Evidence Integration Hardening
- Confidence Calibration
- Temporal Weighting
- Contamination And Noise Protection
- Strategy Pressure Clarification
- Trace And Auditability Hardening

Required code surfaces:

- `backend/app/creative/agents/learning/service.py`
- `backend/app/learning/qc_evidence_analyzer.py`
- `backend/app/learning/confidence_calibrator.py`
- `backend/app/learning/temporal_weighting.py`
- `backend/app/learning/contamination_guard.py`
- `backend/app/learning/trace_builder.py`
- `backend/app/creative/contracts/creative_pack.py`

Required validation command:

`python tests/gates/agents/learning/run_learning_agent_v2_6_excellence_gate.py`

Required output artifact:

`OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`

## 4. Evaluation Dimensions

### 4.1 runtime_real

Means:

Learning executes through the real `LearningAgentService`, not a stub or fake fixture.

Validated by:

- executing Learning with controlled runtime artifacts
- verifying `fallback.used == false` for valid scenarios
- verifying persisted Learning output where applicable

Failure if:

- Learning is mocked
- Learning only returns fallback for valid evidence
- no runtime output can be produced

### 4.2 evidence_backed

Means:

Learning output is derived from visible evidence lineage.

Validated by:

- `learning_trace.lineage_summary` exists
- evidence counts are positive in non-fallback scenarios
- clean, contaminated, weak, insufficient, and noisy counts are explicit

Failure if:

- policy exists without evidence lineage
- evidence counts are missing
- lineage references are fabricated

### 4.3 qc_evidence_integration_hardened

Means:

QC-derived outcomes are converted into structured Learning evidence.

Validated by:

- `qc_analysis` exists
- approve/hold/reject rates exist
- QC patterns or QC confidence summary exist
- clean sample counts are explicit

Failure if:

- QC is ignored
- QC analysis is empty under available QC evidence
- fallback-contaminated QC is treated as clean

### 4.4 confidence_calibrated

Means:

Learning confidence is evidence-backed, conservative, and explainable.

Validated by:

- `confidence_calibration.final_confidence` exists
- confidence components exist
- penalties are visible when sample, contamination, controlled validation, temporal volatility, or bootstrap bias require them
- weak evidence does not produce high confidence

Failure if:

- confidence is constant or fake
- confidence lacks rationale
- contaminated or volatile evidence produces unjustified high confidence

### 4.5 temporal_weighting_real

Means:

Learning distinguishes recent, mid-term, long-term, durable, volatile, stale, and spike-like patterns.

Validated by:

- `temporal_analysis` exists
- controlled durable scenario produces `durable_pattern`
- controlled volatile scenario produces `volatile`
- temporal rationale is present

Failure if:

- temporal fields are missing
- recency alone creates strong policy
- volatile evidence is not downgraded

### 4.6 contamination_handling_strong

Means:

Learning identifies contaminated, noisy, weak, and insufficient evidence and prevents it from dominating policy pressure.

Validated by:

- `contamination_analysis` exists
- `downgraded_evidence` is visible in contaminated scenarios
- contaminated scenarios reduce confidence or cap pressure
- partial degradation is visible rather than hidden

Failure if:

- fallback evidence is treated as clean
- contaminated evidence creates strong pressure
- downgraded evidence is invisible

### 4.7 strategy_pressure_bounded

Means:

Learning pressure into Strategy is explicit, evidence-backed, and non-authoritative.

Validated by:

- `strategy_pressure.pressure_mode` exists
- strong pressure is allowed only under strong, clean, durable evidence
- contaminated/noisy/insufficient scenarios are capped
- `bounded`, `strategy_override_allowed`, and `higher_authority_constraints_apply` are true

Failure if:

- Learning pressure has hidden enforcement semantics
- strong pressure appears under unsafe evidence
- Learning overrides Strategy

### 4.8 traceability_complete

Means:

An auditor can reconstruct the Learning output from artifacts alone.

Validated by the presence of:

- `lineage_summary`
- `qc_analysis`
- `confidence_calibration`
- `temporal_analysis`
- `contamination_analysis`
- `strategy_pressure`
- `policy_safety_summary`
- `downgraded_evidence`
- `pattern_rationale`

Failure if:

- any required trace section is missing
- critical trace sections are empty under available evidence
- rationale hides uncertainty

### 4.9 policy_safety_explicit

Means:

Learning explicitly reports whether the output is safe to use as policy pressure.

Validated by:

- `policy_safety_summary.policy_safe`
- `reason_codes`
- `confidence_level`
- `pressure_mode`
- `blocking_issues`
- `warnings`

Failure if:

- policy safety must be inferred manually
- unsafe evidence lacks reason codes
- blocking issues are hidden

### 4.10 determinism_where_required

Means:

The same controlled input produces the same Learning output.

Validated by:

- deterministic replay of the strong durable scenario
- identical Learning and Strategy outputs under unchanged input

Failure if:

- replay changes trace, confidence, policy, pressure, or Strategy response without input change

### 4.11 fallback_honest

Means:

Fallback states are explicit and do not masquerade as evidence-backed policy.

Validated by:

- missing evidence scenario returns explicit fallback
- fallback trace marks low confidence and no meaningful pressure

Failure if:

- fallback is hidden
- fallback produces strong pressure
- fallback output appears clean/evidence-backed

### 4.12 boundary_preserved

Means:

Learning remains a bounded evidence interpreter and policy pressure generator.

Validated by:

- Strategy remains control layer
- HOLD Health state prevents Learning from applying changes
- Learning pressure metadata keeps higher authority constraints visible

Failure if:

- Learning overrides Strategy
- Learning bypasses Health, Trend, Novelty, Experiment, or QC
- Learning becomes a de facto strategy owner

### 4.13 silent_failures_detected

Means:

The gate detects missing fields, invalid traces, non-determinism, invalid pressure, fake confidence, and hidden fallback.

Validated by:

- required-field checks
- scenario checks
- failure aggregation

Failure if:

- critical sections are absent and verdict still passes
- invalid pressure semantics do not produce HOLD

## 5. Validation Methodology

The runner uses controlled but real service execution.

Scenario classes:

- strong durable clean evidence
- contaminated evidence
- volatile temporal evidence
- missing evidence fallback
- deterministic replay
- Strategy boundary under HOLD

The runner also executes the canonical Learning 2.6 test suites. These tests are not a replacement for the gate; they are supporting evidence.

## 6. Required Evidence

The final artifact must include:

- scenario summaries
- unit/integration test summary
- Learning output excerpts
- Strategy boundary check
- dimension-by-dimension results
- blocking failures
- residual monitoring items

Required trace evidence:

- lineage summary
- downgraded evidence
- confidence penalties
- temporal rationale
- contamination rationale
- strategy pressure rationale
- final safety classification

## 7. Verdict Semantics

### GO

Allowed only when:

- all dimensions pass
- no meaningful residual risk remains
- longitudinal runtime evidence is mature enough to remove monitoring

### GO_WITH_MONITORING

Allowed when:

- all critical dimensions pass
- no blocking failures exist
- residuals are explicit and monitorable

Typical acceptable residuals:

- controlled validation remains dominant over long-horizon production evidence
- production history is still short
- v3 readiness requires continued monitoring under real variability

### HOLD

Required if any critical failure exists, including:

- fake confidence
- missing trace sections
- boundary violation
- non-determinism
- hidden fallback
- invalid pressure semantics
- contaminated evidence producing strong pressure
- silent failure

## 8. Failure Conditions

The gate must fail with `HOLD` if:

- Learning cannot run
- Learning output lacks evidence lineage
- confidence lacks rationale
- confidence is high under weak/contaminated/noisy evidence
- temporal analysis is missing
- contaminated evidence is not downgraded
- strategy pressure is unbounded
- strong pressure appears in unsafe scenarios
- policy safety is absent
- replay is non-deterministic
- fallback is hidden
- Strategy boundary is violated
- any required trace section is missing

## 9. Output Artifact Format

The runner writes:

`OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`

Minimum artifact shape:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "agent": "learning",
  "audit_type": "LEARNING_AGENT_V2_6_EXCELLENCE_GATE",
  "verdict": "GO_WITH_MONITORING",
  "runtime_real": true,
  "evidence_backed": true,
  "qc_evidence_integration_hardened": true,
  "confidence_calibrated": true,
  "temporal_weighting_real": true,
  "contamination_handling_strong": true,
  "strategy_pressure_bounded": true,
  "traceability_complete": true,
  "policy_safety_explicit": true,
  "determinism_where_required": true,
  "fallback_honest": true,
  "boundary_preserved": true,
  "silent_failures_detected": false,
  "blocking_failures": [],
  "residual_monitoring": []
}
```

## 10. Final Criteria

Learning Agent v2.6 passes this gate only if the audit proves:

- Learning is real runtime behavior
- Learning output is evidence-backed
- confidence is calibrated and explainable
- time affects interpretation without creating prediction behavior
- contamination/noise is visible and downgraded
- Strategy pressure is explicit and bounded
- policy safety is explicit
- traces reconstruct the reasoning chain
- deterministic replay holds
- fallback honesty holds
- Strategy remains the control layer

Final rule:

> Learning is ready to support v3 only when it can explain what it learned, why it trusts it, what it downgraded, and how bounded its pressure remains.

## 11. Maximum Excellence Checklist Overlay

The runner must also emit a checklist overlay with the following strict release rule:

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

The checklist overlay must cover 15 blocks:

1. Runtime Real
2. Evidence Backed Lineage
3. QC Evidence Integration
4. Confidence Calibration
5. Temporal Weighting
6. Contamination And Noise Protection
7. Strategy Pressure Boundary
8. Pattern Detection Utility
9. Complete Trace
10. Downgraded Evidence
11. Policy Safety
12. Determinism
13. Boundary Preservation
14. Silent Failure Detection
15. Global Consistency

The final artifact must include:

- `critical_failures`
- `soft_failures`
- `fake_confidence`
- `boundary_violations`
- `checklist_results.global_rule`
- `checklist_results.blocks`
- `checklist_results.failed_blocks`
- `checklist_results.final_release_criteria`

If any checklist block fails, the gate verdict must become `HOLD`.

If all checklist blocks pass but longitudinal production evidence still requires monitoring, the gate verdict remains `GO_WITH_MONITORING` and the checklist release status may be `READY_FOR_V3_WITH_MONITORING`.


---

## Source: `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md`

# LEARNING_AGENT_V2_6_EXCELLENCE_PLAN

## 1. Executive Summary

`Learning Agent v2.6` is the first execution artifact of Wave 1 in the Phase 2.6 Excellence Hardening program.

Phase 2.6 is defined in:

`docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md`

The Learning Agent enters Wave 1 because it is one of the primary upstream converters of historical evidence into future policy pressure. If Learning remains shallow, v3 will scale shallow evidence. If Learning is poorly calibrated, Strategy will receive weak or misleading policy pressure. If Learning oversteps its boundary, the runtime risks invisible strategic drift.

Current Learning state:
- runtime-real
- causally active
- bounded
- deterministic under controlled inputs
- able to ingest evidence and emit `learning_insights`, `learning_policy`, and `pattern_findings_summary`
- able to separate clean and contaminated evidence
- able to influence Strategy through a governed path

Target Learning state after Phase 2.6:
- evidence-backed
- confidence-aware
- temporally stronger
- causally sharper
- excellence-gated
- production-credible
- still bounded in authority

The objective of Learning 2.6 is not to transform Learning into Strategy, nor into an autonomous policy owner.

The objective is to make Learning a stronger, more trustworthy evidence and policy-pressure subsystem while preserving the control boundary:

> Learning may influence Strategy strongly, but Strategy remains the control layer.

## 2. Current State Of The Learning Agent

The Learning Agent has already crossed the line from passive heuristic summarization into a minimally causal, bounded optimization layer.

Current proven capabilities:
- it is runtime-real
- it consumes historical evidence
- it emits `LearningInsights`
- it emits `LearningPolicy`
- it emits `PatternFindingSummary`
- it separates clean evidence from fallback-contaminated evidence
- it consumes QC-derived evidence in the v2 path
- it influences Strategy causally
- it preserves deterministic behavior under controlled inputs
- it persists auditable output into runtime artifacts
- it operates inside its boundary rather than directly mutating downstream agents

Current governed classification:

```json
{
  "learning_agent": "runtime_real_and_causally_active",
  "authority": "bounded_policy_pressure",
  "primary_consumer": "Strategy",
  "current_maturity": "partially_mature",
  "phase_2_6_target": "evidence_backed_confidence_aware_temporally_stronger"
}
```

Known deficits remain:
- confidence is still insufficiently mature and not yet production-rich
- temporal weighting can be stronger
- pattern extraction can become more specific and more useful
- QC integration can become more productive
- bounded enforcement over Strategy can be clearer
- bootstrap bias still needs stronger containment
- traces can explain policy formation more directly
- longitudinal runtime maturity remains short

These deficits are not structural blockers. They are exactly the kind of maturity residues Phase 2.6 exists to reduce.

## 3. Correct Boundary Of Learning In Phase 2.6

Learning 2.6 must preserve the existing runtime governance model:

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

### 3.1 Learning Owns

Learning may own:
- interpretation of historical performance evidence
- interpretation of QC-derived quality evidence
- formation of learning insights
- formation of bounded learning policy
- separation of clean and contaminated evidence
- temporal weighting of evidence
- confidence reporting
- pattern detection
- evidence lineage
- bounded policy pressure into Strategy
- traceability of why a policy was formed

### 3.2 Learning Does Not Own

Learning must not own:
- Strategy decisions
- experiment selection
- trend interpretation
- publishability authority
- final product quality authority
- direct mutation of Script, Voice, Asset, Editor, or QC outputs
- core pipeline mutation
- rollout policy
- winner selection outside its boundary
- autonomous policy enforcement

Boundary rule:

> Learning may influence Strategy strongly, but Strategy remains the control layer.

Corollary:

> Learning should make Strategy better informed, not less authoritative.

## 4. Why Learning Must Be Hardened Before v3

v3 should not be built on weak feedback conversion.

Learning is one of the runtime's main mechanisms for converting historical outcomes into future pressure. If that mechanism is shallow, noisy, or poorly calibrated, the next platform layer will amplify the wrong signals.

Hardening Learning before v3 is necessary because:
- Learning translates feedback into reusable future pressure
- weak Learning causes Strategy to operate with shallow policy evidence
- poorly calibrated Learning can create invisible strategic drift
- thin confidence can make policy pressure decorative instead of actionable
- excessive confidence can make policy pressure dangerous
- bootstrap bias can turn early small-sample artifacts into false direction
- contaminated evidence can poison downstream policy if not isolated
- temporal blindness can overvalue stale or noisy history

A v3 runtime will likely add more scale, more variety, and more external pressure. Learning must become more mature before that happens.

## 5. Current Deficits To Fix

Phase 2.6 must address the following Learning deficits.

### 5.1 Confidence Maturity

Current confidence exists, but it is not yet mature enough to carry stronger production meaning across wider variability.

Deficit:
- confidence can be present without being sufficiently calibrated to evidence quality, sample size, recency, and consistency

Required fix:
- confidence must become evidence-backed, explainable, and bounded

### 5.2 Temporal Memory And Weighting

Current evidence aggregation can be improved across short and long windows.

Deficit:
- recent signal and long-horizon signal are not always clearly separated in policy meaning

Required fix:
- temporal weighting must distinguish fresh signals, durable patterns, and stale evidence

### 5.3 Pattern Specificity

Current pattern findings are useful but can become more specific.

Deficit:
- some patterns are still too broad to produce strong bounded action

Required fix:
- pattern detection must produce more actionable findings without inflating ontology or ownership

### 5.4 Policy Usefulness

Learning policy can influence Strategy, but policy pressure can still become weak or decorative under thin evidence.

Deficit:
- not all policy outputs are equally actionable

Required fix:
- policy pressure must express strength, evidence basis, and enforcement limits

### 5.5 Bootstrap Bias

The runtime still carries short-history residues.

Deficit:
- early evidence can appear more meaningful than it is

Required fix:
- bootstrap bias must be explicitly detected, downgraded, or quarantined in confidence and policy strength

### 5.6 QC Integration Productivity

QC evidence is available, but its use can become richer.

Deficit:
- QC outcomes can be used more productively to identify quality-driving patterns

Required fix:
- QC-derived evidence should clarify what worked, what failed, and which dimensions drove policy pressure

### 5.7 Trace Explainability

Current traces are auditable but can become more explanatory.

Deficit:
- traces should more directly answer why a specific policy was formed

Required fix:
- Learning traces must expose evidence lineage, confidence reasoning, contamination impact, and temporal reasoning

### 5.8 Longitudinal Maturity

Learning requires more real runtime history.

Deficit:
- controlled validation remains stronger than long-horizon production evidence

Required fix:
- Learning 2.6 must explicitly distinguish controlled proof from production maturity

## 6. Phase 2.6 Objectives For Learning

Learning 2.6 objectives:
- make Learning more reliable
- make Learning more explainable
- make Learning more useful to Strategy
- make Learning more resistant to noise
- make Learning more temporally mature
- make Learning more precise under contamination
- make Learning confidence more evidence-backed
- make Learning traces more reconstructible
- preserve Learning as bounded policy pressure
- reduce monitoring residues tied to Learning maturity

Learning 2.6 does not aim to:
- create a new strategic brain
- make Learning autonomous
- make Learning own Strategy
- make Learning own experiments
- make Learning own rollout policy
- make Learning directly mutate generation agents
- give Learning authority beyond evidence interpretation and bounded policy pressure

Target state:

```json
{
  "learning_v2_6": {
    "runtime_real": true,
    "evidence_backed": true,
    "confidence_aware": true,
    "temporally_stronger": true,
    "causally_sharper": true,
    "strategy_pressure_bounded": true,
    "boundary_preserved": true
  }
}
```

## 7. Workstreams Of Learning 2.6

### 7.1 QC Evidence Integration Hardening

Objective:
- make QC-derived evidence more useful to Learning policy formation

Must improve:
- ingestion of QC status and score summaries
- interpretation of product signals
- separation between strong and weak QC signals
- ability to identify which quality dimensions matter
- distinction between valid output, publishable output, and strategically useful output

Required evidence:
- examples where QC APPROVE, HOLD, and REJECT lead to different Learning interpretations
- examples where hook, payoff, asset, voice, or edit quality affect policy formation
- trace explaining how QC evidence shaped policy

Prohibited behavior:
- treating QC as a vanity score source
- deriving strong policy from weak or ambiguous QC evidence
- bypassing QC authority

### 7.2 Pattern Detection Hardening

Objective:
- make pattern findings more useful, specific, and bounded

Must improve:
- pattern specificity
- actionability
- repeated success and failure detection
- differentiation between one-off outcomes and durable signals
- mapping from pattern to bounded policy implication

Required evidence:
- winner cluster patterns
- loser cluster patterns
- mixed cluster patterns
- no-pattern / insufficient-evidence cases

Prohibited behavior:
- large ornamental pattern ontology
- fake pattern confidence
- treating correlation as direct causation without trace limits

### 7.3 Confidence Calibration

Objective:
- make confidence meaningful, not decorative

Confidence should consider:
- evidence count
- sample size
- recency
- consistency
- contamination rate
- QC quality strength
- agreement between short and long windows
- whether evidence came from controlled validation or real runtime history

Must improve:
- confidence per insight
- confidence per policy bias
- confidence summary
- explicit low-confidence behavior
- policy strength constrained by confidence

Required evidence:
- high-confidence scenario
- low-confidence scenario
- conflicting-evidence scenario
- contaminated-evidence scenario
- short-history bootstrap scenario

Prohibited behavior:
- confidence inflation
- confidence without evidence lineage
- policy strength exceeding confidence basis

### 7.4 Temporal Weighting

Objective:
- improve recency and long-window reasoning

Must improve:
- separation between recent evidence and long-horizon evidence
- recency weighting
- stale evidence handling
- short-window volatility protection
- long-window durability recognition

Required evidence:
- recent winner cluster against weak long history
- recent loser cluster against strong long history
- stale evidence downgrade
- short-history insufficient-evidence case

Prohibited behavior:
- overreacting to a tiny recent sample
- ignoring durable historical quality
- treating stale evidence as current truth

### 7.5 Contamination And Noise Protection

Objective:
- prevent fallback contamination, bootstrap bias, and noisy evidence from forming strong policy

Must improve:
- contamination flags
- clean vs contaminated evidence separation
- fallback contamination rate use
- noise resistance
- bootstrap bias handling
- low-sample policy restraint

Required evidence:
- contaminated high-score case does not dominate policy confidence
- clean evidence can dominate when sufficiently consistent
- missing evidence leads to conservative confidence
- fallback-heavy history produces explicit warning or reduced policy strength

Prohibited behavior:
- masking fallback as clean evidence
- forming strong policy from contaminated clusters
- treating missing evidence as neutral success

### 7.6 Strategy Pressure Clarification

Objective:
- make Learning-to-Strategy influence clearer, stronger when justified, and explicitly bounded

Must improve:
- how policy reaches Strategy
- policy strength semantics
- bounded enforcement rules
- Strategy trace of Learning influence
- conflict behavior when Health, Trend, Novelty, Experiment, and Learning disagree

Required evidence:
- Learning changes Strategy when confidence is sufficient
- Learning is downgraded when confidence is weak
- Health still outranks Learning
- Strategy remains final control layer

Prohibited behavior:
- hidden enforcement
- direct Strategy override
- Learning bypassing Health or QC
- Learning becoming a parallel control layer

### 7.7 Trace And Auditability Hardening

Objective:
- make Learning decisions reconstructible from artifacts

Must improve:
- evidence lineage
- policy rationale
- confidence rationale
- temporal window trace
- contamination impact trace
- Strategy pressure explanation

Required evidence:
- trace answers what evidence was used
- trace answers why policy was formed
- trace answers why confidence has its value
- trace answers what was ignored or downgraded
- trace answers how contamination affected the result

Prohibited behavior:
- black-box policy formation
- unexplained confidence
- missing evidence lineage

## 8. Proposed Contract Evolution

Learning 2.6 may evolve contracts only where the added fields provide clear causal or audit value.

Contract evolution must be compatible with the governed runtime and must not create ornamental schema growth.

### 8.1 LearningInsights Potential Extensions

Potential additions:
- `insight_confidence`
- `evidence_references`
- `sample_size_summary`
- `recency_window_summary`
- `contamination_flags`
- `rationale`

Purpose:
- make insight formation more evidence-backed and traceable

### 8.2 LearningPolicy Potential Extensions

Potential additions:
- `policy_strength`
- `enforcement_strength`
- `confidence_by_bias`
- `evidence_count_by_bias`
- `recency_weight_by_bias`
- `contamination_impact`
- `policy_rationale`
- `strategy_pressure_mode`

Purpose:
- make Learning pressure more useful to Strategy while preserving bounded authority

### 8.3 PatternFindingSummary Potential Extensions

Potential additions:
- `pattern_id`
- `pattern_family`
- `evidence_count`
- `recent_evidence_count`
- `quality_delta_summary`
- `contamination_state`
- `confidence`
- `recommended_bounded_action`

Purpose:
- make patterns more actionable without turning Learning into Strategy

### 8.4 Contract Discipline Rules

Any contract evolution must satisfy:
- backward compatibility where practical
- deterministic serialization
- no required field without clear runtime producer
- no field that implies ownership outside Learning
- no fake confidence
- no unbounded enforcement semantics
- traceable producer and consumer behavior

A contract change is invalid if it adds fields that are not consumed, not audited, or not causally useful.

## 9. Validation Strategy For Learning 2.6

Learning 2.6 must be validated through layered proof.

Required validation layers:
- unit tests
- controlled scenario battery
- Strategy integration tests
- QC-derived evidence scenarios
- contamination scenarios
- temporal weighting scenarios
- confidence calibration scenarios
- deterministic replay checks
- audit trace checks
- governance boundary checks

### 9.1 Unit Validation

Must prove:
- evidence parsing remains valid
- clean and contaminated evidence are separated
- confidence is computed deterministically
- temporal windows are interpreted consistently
- policy strength does not exceed evidence basis

### 9.2 Controlled Scenario Battery

Must include:
- winner cluster
- loser cluster
- mixed cluster
- contaminated cluster
- short-history bootstrap cluster
- stale-evidence cluster
- conflicting recent vs long-horizon evidence

### 9.3 Strategy Integration Validation

Must prove:
- Strategy changes when Learning confidence and policy strength justify it
- Strategy does not change materially when Learning confidence is too weak
- Strategy trace records Learning influence
- Health constraints remain above Learning pressure
- Learning does not override Strategy ownership

### 9.4 Evidence Contamination Scenarios

Must prove:
- fallback-heavy history cannot form high-confidence policy by itself
- contaminated evidence is visible in trace
- contaminated high-score runs are not treated as clean wins

### 9.5 Temporal Weighting Scenarios

Must prove:
- recent signal and long-history signal are both represented
- short-window volatility is contained
- stale evidence is downgraded
- durable signal can persist when supported

### 9.6 Determinism Checks

Must prove:
- same evidence input yields same Learning output
- same Learning output yields same Strategy response
- replay does not create policy drift

### 9.7 Audit Trace Checks

Must prove:
- every policy can be reconstructed from evidence
- every confidence value has a rationale
- every downgraded evidence class is visible
- every bounded enforcement path is explicit

Invalid improvements:
- fake confidence
- boundary violation
- ornamental policy
- excessive policy dominance
- reduced determinism where determinism is required
- hidden enforcement
- contamination masking

## 10. Learning Excellence Gate

At the end of Learning 2.6, a dedicated gate must be generated:

`OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`

The gate must prove at minimum:
- `runtime_real = true`
- `evidence_backed = true`
- `confidence_calibrated = true`
- `temporal_weighting_real = true`
- `contamination_handling_strong = true`
- `strategy_pressure_bounded = true`
- `determinism_where_required = true`
- `fallback_honest = true`
- `boundary_preserved = true`
- `silent_failures_detected = false`

Suggested final verdict schema:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "agent": "learning",
  "audit_type": "LEARNING_AGENT_V2_6_EXCELLENCE_GATE",
  "verdict": "GO_WITH_MONITORING",
  "runtime_real": true,
  "evidence_backed": true,
  "confidence_calibrated": true,
  "temporal_weighting_real": true,
  "pattern_detection_actionable": true,
  "qc_evidence_integration_hardened": true,
  "contamination_handling_strong": true,
  "bootstrap_bias_protected": true,
  "strategy_pressure_bounded": true,
  "strategy_causal_response": true,
  "determinism_where_required": true,
  "fallback_honest": true,
  "boundary_preserved": true,
  "silent_failures_detected": false,
  "blocking_failures": [],
  "residual_monitoring": []
}
```

A `GO` verdict is allowed only if no meaningful Learning-specific residue remains.

A `GO_WITH_MONITORING` verdict is acceptable if the remaining residues are explicit, bounded, and tied to evidence horizon rather than implementation weakness.

A `HOLD` verdict is required if Learning violates boundary, inflates confidence, loses determinism, or becomes ornamental.

## 11. What Learning 2.6 Must Not Do

Learning 2.6 must not:
- become the owner of Strategy
- become a rollout system
- become a winner selector
- become a trend engine
- own experiment selection
- own publishability
- mutate the core pipeline
- directly mutate downstream generation outputs
- inflate policy beyond evidence
- use fake confidence
- mask noise as learning
- create hidden enforcement
- produce strong pressure from weak sample size
- treat contaminated evidence as clean
- treat controlled validation as full production maturity
- become a parallel control layer

Learning 2.6 must remain an evidence interpreter and bounded policy-pressure subsystem.

## 12. Exit Criteria

Learning 2.6 is complete only when:
- confidence is evidence-backed and traceable
- policy pressure is more useful and clearly bounded
- temporal weighting is proven in controlled scenarios
- QC evidence integration is more productive
- pattern detection is more specific and actionable
- contamination and noise protection are stronger
- bootstrap bias is explicitly contained
- Strategy integration is strengthened without ownership drift
- deterministic replay remains valid
- audit traces explain policy formation
- the Learning excellence gate passes
- major Learning-specific monitoring residues are reduced
- behavior under variability is more credible

Minimum accepted closure state:

```json
{
  "learning_agent_v2_6": {
    "runtime_real": true,
    "evidence_backed": true,
    "confidence_aware": true,
    "temporally_credible": true,
    "strategy_useful": true,
    "boundary_preserved": true,
    "excellence_gate_passed": true
  }
}
```

## 13. Final Position

Learning 2.6 exists to convert the current Learning Agent from a valid bounded evidence interpreter into a more mature, confidence-aware, temporally credible, strategically useful subsystem.

It must make Strategy better informed without becoming Strategy.

It must increase confidence without faking certainty.

It must strengthen policy pressure without hiding enforcement.

It must improve future behavior without violating governance.

Final principle:

> Learning 2.6 hardens the runtime's ability to learn from evidence while preserving the system's authority boundaries.


---

## Source: `docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md`

# PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN

## 1. Executive Summary

Phase 2.6 exists because `CORTAI_RUNTIME_V2_5` has reached a stable and governed operating state, but stability is not the same thing as excellence readiness for v3.

Current consolidated runtime posture:

```json
{
  "runtime": "stable_and_governed",
  "verdict": "GO_WITH_MONITORING"
}
```

Target posture after Phase 2.6:

```json
{
  "runtime": "excellence_ready_for_v3",
  "agents": "hardened",
  "monitoring_residuals": "minimized",
  "behavior_under_variability": "proven"
}
```

Phase 2.5 proved that the system can run as a governed multiagent runtime:
- the core pipeline is frozen and validated
- governed subsystems are active with monitoring
- the real manual batch reached `10/10` successful runs
- experiment assignment and result recording are active
- script generation is using a real provider path
- the all-agents extreme checklist produced `GO_WITH_MONITORING`
- audit artifacts are semantically aligned

That is sufficient for operational continuity.

It is not sufficient to justify a broad v3 expansion without additional hardening.

The correct next move is not to add external expansion surfaces. The correct next move is to strengthen the agents that already exist, reduce monitoring-class residues, improve evidence quality, prove behavior under variability, and tighten confidence without violating subsystem boundaries.

Phase 2.6 is therefore not a feature phase.

Phase 2.6 is:
- architectural excellence
- hardening
- reduction of monitoring residues
- causal strengthening of existing agents
- robustness under variability
- disciplined preparation for v3

Canonical principle:

> Phase 2.6 = hardening and excellence of existing agents, aiming at v3 readiness.

The system must not enter v3 until the Phase 2.6 gates prove that the current runtime is not merely functional, but mature enough to support the next platform layer without increasing hidden fragility.

## 2. Current State Of The Runtime

The current runtime is already operational, auditable, reproducible, and governed.

Current confirmed state:
- `system_version = CORTAI_RUNTIME_V2_5`
- `core_pipeline.status = FROZEN_AND_VALIDATED`
- `governance_model = SUBSYSTEM_BASELINE_WITH_MONITORING`
- `change_policy = FROZEN_UNLESS_GOVERNANCE_REOPEN`
- governed subsystems are active with monitoring
- the real manual batch reached `10/10` successful runs
- `valid_video_count = 10`
- `publishable_count = 10`
- `fallback_usage_count = 0`
- `experiment_assignment_count = 10`
- `experiment_result_recording_count = 10`
- `script_generation_real_provider_active = true`
- `script_fallback_count = 0`
- all-agents extreme checklist verdict is `GO_WITH_MONITORING`
- max integrity gate verdict is `GO_WITH_MONITORING`
- final audit artifacts are semantically aligned

The system has proven:
- real multiagent execution
- real render output
- real experiment loop activation
- fallback honesty
- no fake assignment
- no fake attribution
- no silent failure pattern in the current gate
- preserved governance boundaries
- purpose alignment

This means the runtime is healthy.

It does not mean every agent is excellence-grade under sustained variability.

The current residues are monitoring-class, not structural blockers. They still matter because v3 will increase system pressure. A stable runtime can absorb ordinary operation. An excellence-ready runtime must absorb variability, noisy evidence, edge cases, longer horizons, and causal conflict without drift.

## 3. Why Phase 2.6 Is Necessary

Going directly to v3 would be premature.

The current system is stable, but several residues still point to maturity risk:
- runtime history is still short in some subsystems
- controlled validation still dominates some evidence surfaces
- real production variety is still under monitoring
- attribution manual flow still requires real post-publish `window_metrics`
- trend monitoring still needs stronger evidence horizons
- QC still requires monitored alignment against real product quality
- experiment runtime history still needs longitudinal variety
- account health telemetry remains comparatively thin

These are not reasons to stop operation.

They are reasons to harden before expanding.

Phase 2.6 is necessary to prove:
- stronger longitudinal robustness
- more credible statistical maturity
- better behavior under real variability
- tighter confidence reporting
- stronger evidence provenance
- better conflict handling between agents
- fewer monitoring residues
- higher product quality under diverse inputs

The system should not begin v3 while still relying too heavily on short-horizon evidence or controlled validation dominance.

## 4. Phase 2.6 Boundary

Phase 2.6 must operate under the existing governance model:

```json
{
  "system_version": "CORTAI_RUNTIME_V2_5",
  "governance_model": "SUBSYSTEM_BASELINE_WITH_MONITORING",
  "change_policy": "FROZEN_UNLESS_GOVERNANCE_REOPEN",
  "no_core_modification": true,
  "no_subsystem_mutation_without_reopen": true,
  "new_work_must_be_isolated_subsystems": true
}
```

### 4.1 Allowed Work

Phase 2.6 may:
- harden existing agents
- improve traces
- improve evidence quality
- improve confidence reporting
- improve validation gates
- improve behavior under edge cases
- reduce monitorable residues
- strengthen existing loops
- improve controlled battery coverage
- improve runtime observability
- improve deterministic replay where required
- strengthen bounded downstream effects

### 4.2 Prohibited Work

Phase 2.6 must not:
- reopen the core pipeline
- mutate frozen governed subsystems without formal governance reopen
- create a real Publisher Agent
- create a new strategic brain
- turn bounded agents into mini-platforms
- inflate complexity without causal gain
- mix internal excellence with external expansion
- introduce external rollout autonomy
- introduce fake confidence
- optimize artifacts by hiding residuals

Phase 2.6 is not:
- a feature phase
- an external integration phase
- a new core phase
- a publisher phase
- a broad expansion phase

Phase 2.6 is a deep maturation phase.

## 5. Agents In Scope

All existing runtime agents remain in scope, but not with equal priority.

The hardening order must reflect architectural risk, causal leverage, and current monitoring residues.

### Wave 1 - Critical Structural Excellence

1. `Account Health`
2. `Learning`
3. `Trend Analysis`

Reason:
- these agents define upstream conditions, evidence interpretation, and strategic signal quality
- weak upstream signals contaminate downstream behavior
- v3 must not build on thin telemetry, weak confidence, or low-quality trend evidence

### Wave 2 - Perceptual And Output Quality Excellence

4. `Script`
5. `Voice`
6. `Asset`
7. `QC`

Reason:
- these agents materially determine product quality
- they expose whether the runtime can produce strong content under varied inputs
- QC must become more sensitive to quality edge cases without becoming unstable or over-adaptive

### Wave 3 - Precision Refinement

8. `Strategy`
9. `Novelty`
10. `Editor`
11. `Experiment Capability`
12. `Content Performance Attribution`

Reason:
- these systems are already causally active and governed
- they need precision, maturity, and stronger longitudinal confidence
- they should not be expanded before upstream and perceptual foundations are hardened

## 6. Per-Agent Goals

### 6.1 Account Health

Current state:
- runtime-real
- SAFE / CAUTION / HOLD path operational
- downstream constraints propagate
- fallback explicit
- deterministic under controlled inputs

Primary deficit:
- telemetry richness and temporal context are still limited

Phase 2.6 objective:
- make Account Health more credible as an upstream governance gate without turning it into a full risk engine

Must improve:
- real telemetry use
- decision trace quality
- threshold explainability
- simple temporal awareness
- standalone health gate evidence
- detection of risky account patterns before downstream waste

Must not inflate:
- platform-scale risk modeling
- autonomous policy rewriting
- cross-agent ownership
- hidden throttling logic

Expected Phase 2.6 result:
- Account Health becomes a stronger bounded safety and posture gate with better evidence and traceability.

### 6.2 Learning

Current state:
- consumes performance and QC-derived signals
- forms bounded policy hints
- separates clean and contaminated evidence
- influences Strategy
- deterministic under controlled inputs

Primary deficit:
- confidence and temporal weighting still need stronger runtime evidence

Phase 2.6 objective:
- improve Learning as a bounded evidence interpreter, not as a strategy owner

Must improve:
- integration with QC evidence
- useful pattern extraction
- confidence calibration
- temporal weighting
- contaminated evidence handling
- bounded enforcement over Strategy
- separation of short-term noise from durable learning

Must not inflate:
- direct ownership of Strategy decisions
- autonomous policy dominance
- winner-selection logic beyond its boundary
- fake confidence from thin evidence

Expected Phase 2.6 result:
- Learning emits more trustworthy, evidence-backed, bounded policy pressure with clear confidence.

### 6.3 Trend Analysis

Current state:
- runtime-real
- uses canonical trend profile paths
- fallback governed
- provenance present
- influences Strategy and Asset

Primary deficit:
- evidence quality, source governance, and shift analysis need maturity

Phase 2.6 objective:
- make Trend Analysis more credible as a governed trend evidence layer without unsustainable scraping expansion

Must improve:
- evidence quality
- provenance detail
- freshness validation
- confidence calibration
- shift analysis
- source governance
- manual curation discipline
- stale evidence behavior

Must not inflate:
- uncontrolled scraping
- fake regionalization
- unsupported live trend claims
- broad external automation beyond sustainability

Expected Phase 2.6 result:
- Trend Analysis becomes a stronger evidence-backed signal provider with safer confidence and clearer source lineage.

### 6.4 Script

Current state:
- real provider path active
- fallback no longer dominant in the latest batch
- hook / setup / payoff structure operational
- experiment context can reach script generation

Primary deficit:
- script quality can still become conservative under some contexts

Phase 2.6 objective:
- raise narrative strength while preserving deterministic structure and safety

Must improve:
- stronger hooks
- less conservative setup
- more memorable payoff
- pre-QC script validation
- controlled diversity
- semantic specificity
- stronger experiment-context utilization

Must not inflate:
- freeform uncontrolled generation
- excessive prompt complexity
- style novelty at the expense of clarity
- untraceable script rewrites

Expected Phase 2.6 result:
- Script consistently produces sharper, more specific, more memorable narratives without losing structure.

### 6.5 Voice

Current state:
- voice plan operational
- provider selection coherent
- delivery profile and segment plans exist
- fallback explicit

Primary deficit:
- adaptive delivery and monotony control need stronger quality evidence

Phase 2.6 objective:
- improve audio delivery quality and alignment with Script and Strategy

Must improve:
- adaptive voice selection
- delivery variation
- monotony reduction
- audio validation
- segment-level timing alignment
- stronger response to script intensity
- stronger response to strategy mode

Must not inflate:
- unnecessary voice-agent autonomy
- broad provider abstraction without runtime need
- hidden fallback substitution

Expected Phase 2.6 result:
- Voice becomes more expressive, better aligned, and less monotonous while staying traceable.

### 6.6 Asset

Current state:
- assets selected by segment
- trend and strategy response proven
- diversity guard improved
- latest batch reached `10/10` without fallback

Primary deficit:
- visual quality scoring and fallback quality can mature further

Phase 2.6 objective:
- make Asset more robust under varied topics without visual monoculture or poor proxy choices

Must improve:
- asset quality scoring
- diversity guard behavior
- visual evidence specificity
- fallback visual quality
- topic-to-visual alignment
- avoidance of repeated families where inappropriate
- stronger rejection of weak proxy assets

Must not inflate:
- custom generation dependency where retrieval is sufficient
- ungoverned asset generation
- broad visual ontology expansion without validation

Expected Phase 2.6 result:
- Asset produces more specific, varied, high-quality visual plans under real topic diversity.

### 6.7 QC

Current state:
- APPROVE / HOLD / REJECT operational
- false approve rate controlled in validation
- final authority preserved
- deterministic under controlled inputs

Primary deficit:
- sensitivity to edge cases and score-quality alignment need continued monitoring

Phase 2.6 objective:
- strengthen QC as product authority without making it prematurely hyperadaptive

Must improve:
- edge-case sensitivity
- alignment between score and real quality
- confidence reporting
- product signal clarity
- detection of weak-but-technically-valid videos
- traceability of HOLD and REJECT reasons

Must not inflate:
- self-modifying thresholds
- overfitted scoring
- opaque quality judgments
- bypass paths for publishability

Expected Phase 2.6 result:
- QC becomes more credible as final product authority under varied real outputs.

### 6.8 Strategy

Current state:
- reacts to Health, Trend, Learning, and Novelty
- downstream effects on Script, Voice, Asset, and Editor are proven
- decision trace exists
- deterministic under controlled inputs

Primary deficit:
- conflict handling and confidence expression can be stronger

Phase 2.6 objective:
- refine Strategy without reinventing it

Must improve:
- confidence reporting
- decision trace specificity
- conflict handling between signals
- variation policy responsiveness
- less excessive conservatism where safe
- clearer downstream intent

Must not inflate:
- new strategic brain
- ownership over Learning or Experiment
- autonomous policy governance
- unbounded adaptation

Expected Phase 2.6 result:
- Strategy becomes more precise, less conservatively flat, and more transparent under signal conflict.

### 6.9 Novelty

Current state:
- saturation pressure profile exists
- structural and visual repetition controls are active
- diversity effects are proven
- quality does not collapse in controlled gates

Primary deficit:
- confidence and memory behavior need maturity under longer windows

Phase 2.6 objective:
- improve repetition control without expanding Novelty beyond its scope

Must improve:
- confidence reporting
- memory window behavior
- decay logic if justified by evidence
- pattern explainability
- topic repetition awareness
- visual repetition pressure

Must not inflate:
- trend ownership
- strategy ownership
- creative taste authority
- overblocking based on thin history

Expected Phase 2.6 result:
- Novelty becomes a more precise saturation governor with better confidence and less blunt repetition pressure.

### 6.10 Editor

Current state:
- edit plan operational
- captions, motion, transitions, and color plans are coherent
- Strategy -> Editor effect is proven
- no slideshow regression in current gates

Primary deficit:
- fine pre-validation and consistency checks can mature

Phase 2.6 objective:
- refine Editor quality without treating it as the primary bottleneck unless evidence changes

Must improve:
- pre-validation
- consistency checks
- caption timing edge cases
- motion-to-script alignment
- transition consistency
- render-plan traceability

Must not inflate:
- independent creative ownership
- large new editor autonomy
- style complexity without product gain

Expected Phase 2.6 result:
- Editor becomes more reliable and internally consistent under diverse scripts and assets.

### 6.11 Experiment Capability

Current state:
- eligibility explicit
- assignment real
- result recording real
- deterministic replay and idempotency repaired
- latest batch reached `10/10` assignment and result recording

Primary deficit:
- runtime history remains short

Phase 2.6 objective:
- mature Experiment Capability through longitudinal evidence and variety, not scope expansion

Must improve:
- runtime variety evidence
- envelope confidence
- replay robustness
- result integrity across longer horizons
- monitoring of eligibility decisions
- clarity of fallback and non-eligibility cases

Must not inflate:
- winner-selection ownership
- autonomous experimentation policy
- learning ownership
- attribution ownership

Expected Phase 2.6 result:
- Experiment Capability becomes more mature and production-credible without exceeding its assignment/result boundary.

### 6.12 Content Performance Attribution

Current state:
- canonical contract hardened
- WRITTEN vs SKIPPED honest
- experiment linkage safe
- unsafe inference blocked
- bounded downstream effect proven
- manual batch remains NOT_RUN without real `window_metrics`

Primary deficit:
- operational maturity requires real post-publish metrics history

Phase 2.6 objective:
- strengthen attribution evidence and linkage without invading Experiment or Learning ownership

Must improve:
- evidence robustness
- linkage reliability
- operational maturity
- post-publish window handling
- bounded downstream effect clarity
- skip reason discipline

Must not inflate:
- fake attribution
- inferred experiment linkage
- ownership of experiment results
- direct Strategy mutation

Expected Phase 2.6 result:
- Attribution becomes more operationally credible under real metrics without weakening evidence honesty.

## 7. Phase Waves

### 7.1 Wave 1 - Structural Hardening

Agents:
- Account Health
- Learning
- Trend Analysis

Objective:
- strengthen upstream evidence, confidence, and governance posture before improving downstream expression

Risk reduced:
- thin upstream signal quality
- weak evidence provenance
- overreaction to noisy history
- downstream behavior driven by shallow inputs

Exit criteria:
- Account Health has richer telemetry and clearer traces
- Learning separates durable patterns from noise with better confidence
- Trend Analysis has stronger provenance, freshness, and source governance
- no agent violates its boundary
- dedicated gates or equivalent validation pass

### 7.2 Wave 2 - Output Excellence

Agents:
- Script
- Voice
- Asset
- QC

Objective:
- improve product quality and validation sensitivity under diverse real inputs

Risk reduced:
- technically valid but weak videos
- conservative scripts
- monotonous delivery
- weak visual specificity
- QC blind spots

Exit criteria:
- script hooks and payoffs are stronger in controlled and real batch contexts
- voice delivery aligns more tightly with script and strategy
- asset selection demonstrates quality and diversity under topic variety
- QC improves edge sensitivity without false inflation
- real batch quality improves without fallback contamination

### 7.3 Wave 3 - Precision Refinement

Agents:
- Strategy
- Novelty
- Editor
- Experiment Capability
- Content Performance Attribution

Objective:
- refine precision, confidence, and maturity of already-active loops

Risk reduced:
- unclear signal conflict resolution
- blunt novelty pressure
- editor inconsistency
- short experiment history
- attribution immaturity without real metrics windows

Exit criteria:
- Strategy handles signal conflict transparently
- Novelty pressure is more precise and evidence-backed
- Editor pre-validation catches consistency issues earlier
- Experiment Capability has longer runtime variety evidence
- Attribution remains honest while becoming more operationally useful
- the final Phase 2.6 master gate passes

## 8. Excellence Criteria

Phase 2.6 must not use vanity scores as its primary certification mechanism.

The official excellence criteria are qualitative, auditable, and evidence-backed.

An agent or subsystem is Phase 2.6-ready only if it is:
- runtime-real
- causally strong
- evidence-backed
- traceable
- deterministic where required
- bounded in authority
- excellence-gated
- production-credible
- robust under variability
- free of silent failure patterns
- honest under fallback
- compatible with governance boundaries

A claim is not accepted merely because a test passes.

A claim is accepted when:
- the behavior is observable in runtime or controlled gates
- the evidence is recorded in artifacts
- the trace explains the decision path
- fallback and uncertainty are explicit
- the behavior does not require fake confidence
- the change does not expand ownership silently

## 9. Validation Strategy

Each Phase 2.6 workstream must use validation appropriate to its agent boundary.

Required validation layers:
- unit validation
- controlled scenario battery
- integration validation
- excellence gate
- governance check
- longitudinal monitoring when required

Minimum validation expectations:
- no agent is considered hardened without a dedicated gate or equivalent validation artifact
- no improvement is accepted if it introduces fake confidence
- no improvement is accepted if it creates ornamental complexity
- no improvement is accepted if it hides fallback
- no improvement is accepted if it weakens determinism where determinism is required
- no improvement is accepted if it invades another agent's ownership

Validation outputs should be written under `OUT/audit/` with explicit verdicts, residuals, and artifact references.

Preferred gate format:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "agent_hardened": true,
  "runtime_real": true,
  "causality_proven": true,
  "evidence_backed": true,
  "fallback_honest": true,
  "boundary_preserved": true,
  "deterministic_where_required": true,
  "blocking_failures": [],
  "residual_monitoring": []
}
```

## 10. Global Phase 2.6 Gate

At the end of Phase 2.6, the system must produce a consolidated master gate:

`OUT/audit/phase_2_6_excellence_master_gate/final_verdict.json`

This gate must answer whether the runtime is ready to support v3.

Required dimensions:
- agent quality
- causal strength
- robustness under variability
- reduction of monitoring residues
- behavior in real batch execution
- governance preservation
- fallback honesty
- determinism and replay
- absence of silent failures
- absence of boundary violations
- product quality stability
- attribution evidence discipline
- experiment maturity

Minimum final schema:

```json
{
  "system": "CORTAI_RUNTIME_V2_6",
  "audit_type": "PHASE_2_6_EXCELLENCE_MASTER_GATE",
  "verdict": "GO_WITH_MONITORING",
  "runtime_ready_for_v3": true,
  "agents_hardened": true,
  "monitoring_residuals_minimized": true,
  "behavior_under_variability_proven": true,
  "governance_preserved": true,
  "silent_failures_detected": false,
  "boundary_violations_detected": false,
  "blocking_failures": [],
  "residual_monitoring": []
}
```

A `GO` verdict is only appropriate if residues are materially eliminated.

A `GO_WITH_MONITORING` verdict is acceptable if remaining residues are explicit, bounded, and not blockers for v3.

A `HOLD` verdict is required if any boundary violation, fake confidence, fake artifact, silent failure, or structural quality regression is detected.

## 11. What Phase 2.6 Must Not Do

Phase 2.6 must not:
- create a real Publisher Agent
- reopen the core pipeline
- create a new rollout system
- create a new strategic brain
- convert bounded agents into platforms
- use vanity scoring as proof of excellence
- introduce excessive autonomy
- expand externally before internal excellence is proven
- hide monitoring residues
- treat controlled validation as production maturity
- create fake assignment, fake result, or fake attribution
- weaken QC authority
- weaken Account Health authority
- bypass governance to move faster

Publisher work is explicitly out of scope.

External expansion is explicitly out of scope.

New core architecture is explicitly out of scope.

## 12. Exit Criteria Of Phase 2.6

Phase 2.6 is complete only when:
- Wave 1 structural agents are hardened
- Wave 2 output-quality agents are hardened
- Wave 3 refinement agents are hardened or explicitly monitored with non-blocking residues
- major monitoring residues are reduced
- behavior under variability is proven
- product quality improves under real diverse batches
- experiment loop maturity improves through longer evidence
- attribution remains honest and becomes operationally stronger when real metrics exist
- all relevant excellence gates pass
- governance remains intact
- no core reopening occurred without formal governance
- no subsystem boundary was violated
- no silent failure pattern exists
- no fake confidence was introduced
- the global Phase 2.6 master gate returns `GO` or `GO_WITH_MONITORING`

The correct final transition target is:

```json
{
  "runtime": "excellence_ready_for_v3",
  "agents": "hardened",
  "monitoring_residuals": "minimized",
  "behavior_under_variability": "proven"
}
```

## 13. Final Position

Phase 2.6 is the final excellence and hardening phase before v3.

Its purpose is not to expand the system.

Its purpose is to make the existing runtime strong, reliable, mature, evidence-backed, and governable enough for v3 to be built on a genuinely solid foundation.

The system has already proven stability.

Phase 2.6 must prove excellence.


---

## Source: `docs/runtime/phase-2-6/master-gates/PHASE_2_6_FINAL_MASTER_GATE.md`

# PHASE_2_6_FINAL_MASTER_GATE

## 1. Purpose

`PHASE_2_6_FINAL_MASTER_GATE` is the final consolidated audit gate for Phase 2.6.

The gate validates whether Phase 2.6 as a whole is ready for v3 with monitoring after:

- Wave 1 Master Gate
- Wave 2 Master Gate
- Absolute Master Gate pre-Wave 2
- global governance validation
- full pipeline compatibility checks

This is an audit artifact. It must not implement features, mutate runtime behavior, fix code to pass, modify Strategy, modify any agent, modify Publisher, modify the orchestrator, or modify the core pipeline.

The gate exists to prove v3 readiness with monitoring, not to create readiness.

## 2. Scope

In scope:

- Learning Agent v2.6
- Account Health Agent v2.6
- Trend Analysis Agent v2.6
- Script Agent v2.6
- Voice Agent v2.6
- Asset Selection Agent v2.6
- Video QC Agent v2.6
- Strategy compatibility
- Creative Orchestrator compatibility
- core pipeline compatibility
- governed subsystem registry consistency
- fallback honesty
- boundary preservation
- determinism where required
- trace and auditability
- residual monitoring classification
- final readiness for v3 with monitoring

Out of scope:

- Wave 3 implementation
- Publisher changes
- Strategy redesign
- core pipeline modification
- new provider integration
- asset ranking changes
- QC threshold changes
- new publishability authority
- performance prediction
- converting residuals into blockers or blockers into residuals

## 3. Preconditions

Required master gates:

- `OUT/audit/phase_2_6_wave_1_master_gate/final_verdict.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/final_verdict.json`
- `OUT/audit/cortai_absolute_master_gate/final_verdict.json`

Required child gates:

- `OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/trend_analysis_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json`

Required governance references:

- `OUT/audit/system_governance_registry.json`
- `docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md`
- `docs/runtime/architecture/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md`

Required command:

`python tests/gates/phase_2_6/run_phase_2_6_final_master_gate.py`

## 4. Blocks A-P

### Block A - Artifact Integrity

Validates that all required docs, runners, child gates, master gates, governance artifacts, and JSON payloads exist and parse.

Fails on missing mandatory artifact or invalid JSON.

### Block B - Governance Consistency

Validates:

- core pipeline is `FROZEN_AND_VALIDATED`
- change policy is `FROZEN_UNLESS_GOVERNANCE_REOPEN`
- no core modification rule is true
- no subsystem mutation without reopen rule is true
- new work must be isolated subsystems

Fails on any governance contradiction.

### Block C - Wave 1 Master Gate Integrity

Validates Wave 1 master verdict, readiness, blocks, metrics, residuals, and recommendation.

Fails on `HOLD`, blocking failures, critical failures, fake confidence, silent failures, boundary violations, non-determinism, or incomplete traces.

### Block D - Wave 2 Master Gate Integrity

Validates Wave 2 master verdict, readiness, blocks, metrics, residuals, and recommendation.

Fails on `HOLD`, blocking failures, critical failures, fake confidence, silent failures, boundary violations, non-determinism, incomplete traces, or output pipeline regression.

### Block E - Absolute Master Gate Pre-Wave 2 Integrity

Validates that the pre-Wave 2 absolute master gate had no hard-stop violations and authorized Wave 2 planning.

Fails on any prior hard-stop flag.

### Block F - Child Agent Gate Integrity

Validates all seven Phase 2.6 child gates:

- Learning
- Account Health
- Trend Analysis
- Script
- Voice
- Asset Selection
- Video QC

Fails if any child gate is `HOLD`, has blockers, critical failures, silent failures, boundary violations, fake confidence, hidden fallback, or missing readiness.

### Block G - Pipeline And Core Integrity

Validates pipeline/core artifacts and full certification references remain compatible with the Phase 2.6 final state.

Fails on core/pipeline contradiction, missing core artifact, or publishability authority drift.

### Block H - Contract And Serialization Integrity

Validates Wave 1 and Wave 2 contract surfaces are still represented by their master gates and test batteries.

Fails on missing required additive trace fields, serialization failure evidence, or obvious contract drift.

### Block I - Full Test Battery

Runs a unified relevant test battery covering:

- Wave 1 agents
- Wave 2 agents
- Strategy
- Creative Orchestrator
- TTS Router and Kokoro surfaces
- Editor surfaces
- Experiment and Attribution integration
- content pipeline smoke/unit tests

Fails on any test failure, missing test file, or timeout.

### Block J - Cross-Wave Consistency

Validates Wave 1 upstream governance and Wave 2 output-quality governance do not contradict each other.

Fails if upstream agents override output agents, output agents override Strategy, or QC authority is bypassed.

### Block K - Determinism And Replay Evidence

Validates determinism evidence from Wave 1 and Wave 2 master gates.

Fails if either wave reports non-determinism.

### Block L - Fallback Honesty

Validates fallback honesty across Learning, Account Health, Trend, Script, Voice, Asset Selection, and Video QC.

Fails if fallback is hidden, inflated into success, or treated as strong evidence without support.

### Block M - Boundary Preservation

Validates all boundaries:

- Learning does not become Strategy
- Account Health does not become Strategy/QC/Learning
- Trend does not become Strategy/Asset/QC/Publisher
- Script does not become Strategy/Voice/Asset/QC
- Voice does not become TTS Router/QC/Strategy
- Asset Selection does not become QC/Strategy/Publisher
- Video QC does not repair, publish, rewrite, rerender, replace assets, resynthesize voice, or predict performance
- Strategy remains control layer
- Publisher remains out of scope

Fails on any ownership drift.

### Block N - Trace And Auditability Completeness

Validates:

- Learning trace reconstructs policy
- Account Health `health_trace` reconstructs SAFE/CAUTION/HOLD
- Trend `trend_trace` reconstructs TrendProfile emission
- Script `script_trace` reconstructs ScriptPlan emission
- Voice `voice_trace` reconstructs VoicePlan emission
- Asset `asset_trace` reconstructs AssetPlan emission
- Video QC `qc_trace` reconstructs APPROVE/HOLD/REJECT

Fails on incomplete or contradictory audit traces.

### Block O - Residual Monitoring Classification

Collects residuals from child and master gates.

Only non-structural residuals may remain monitorable:

- runtime history still short
- longitudinal evidence still short
- producer/provider/catalog coverage still expanding
- product signal calibration still maturing
- media probe/environment coverage limitations
- layer attribution evidence still limited
- validation history still short
- controlled validation does not replace long-horizon runtime monitoring

Fails if a structural blocker is classified as monitoring.

### Block P - Final V3 Readiness Decision

Derives the final Phase 2.6 verdict.

Fails if any prior block fails.

## 5. Critical Failure Definitions

Critical failures include:

- missing mandatory final/master/child artifact
- invalid JSON artifact
- any child or master gate `HOLD`
- any blocking failure
- any critical failure
- failed test battery
- fake confidence
- hidden fallback
- silent failure
- boundary violation
- non-determinism
- trace incompleteness
- governance contradiction
- core/pipeline regression
- publishability authority drift
- QC threshold or decision drift
- performance prediction introduced
- structural blocker classified as residual

## 6. Verdict Semantics

`HOLD`:

Required if any critical block fails, any child/master gate is `HOLD`, any blocking failure exists, fake confidence is detected, silent failure is detected, boundary is violated, fallback is hidden, trace is incomplete, or the test battery fails.

`GO_WITH_MONITORING`:

Allowed when all critical checks pass and remaining residuals are explicit, bounded, non-structural, and monitorable.

`GO`:

Allowed only when all blocks pass and no meaningful residual monitoring remains.

Expected likely verdict is `GO_WITH_MONITORING`. The runner must derive it from evidence and must not hardcode it.

## 7. Required Artifacts

The runner writes:

- `OUT/audit/phase_2_6_final_master_gate/final_verdict.json`
- `OUT/audit/phase_2_6_final_master_gate/checklist_results.json`
- `OUT/audit/phase_2_6_final_master_gate/scenario_outputs.json`
- `OUT/audit/phase_2_6_final_master_gate/metrics.json`
- `OUT/audit/phase_2_6_final_master_gate/master_consistency.json`

The final verdict must include:

- Wave 1 readiness summary
- Wave 2 readiness summary
- child agent readiness summary
- blocks A-P
- test execution record
- metrics
- blocking failures
- residual monitoring
- final v3 recommendation

## 8. Final Decision Rule

Phase 2.6 may be declared ready for v3 with monitoring only when:

- Wave 1 Master Gate is `GO` or `GO_WITH_MONITORING`
- Wave 2 Master Gate is `GO` or `GO_WITH_MONITORING`
- Absolute Master Gate pre-Wave 2 is `GO` or `GO_WITH_MONITORING`
- all child gates are `GO` or `GO_WITH_MONITORING`
- all blocks A-P pass
- critical tests pass
- no fake confidence is detected
- no silent failure is detected
- no boundary violation is detected
- no non-determinism is detected
- no trace incompleteness is detected
- all residuals are explicit, bounded, and non-structural

Final recommendation values:

- `READY_FOR_V3_WITH_MONITORING`
- `READY_FOR_V3`
- `HOLD_BEFORE_V3`


---

## Source: `docs/runtime/phase-2-6/master-gates/PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH.md`

# PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH

## 1. Purpose

`PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH` is the partial master gate for Phase 2.6 after the Learning Agent and Account Health Agent excellence hardening workstreams.

The gate validates whether the already-hardened Wave 1 subsystems can be considered ready for v3 with monitoring before any Trend Analysis v2.6 work starts.

This gate does not implement features, mutate runtime behavior, fix code to pass, modify Strategy, modify the orchestrator, or change the core pipeline. It audits, executes controlled validation, consolidates artifacts, and emits a verdict.

## 2. Scope

In scope:

- Learning Agent v2.6 gate integrity
- Account Health Agent v2.6 gate integrity
- Account Health to Strategy integration
- Learning to Strategy integration
- governed orchestrator behavior through existing tests
- contract import and serialization
- governance artifact consistency
- deterministic replay
- fallback honesty
- boundary preservation
- trace completeness
- silent failure detection
- consistency with previous master/runtime artifacts

Out of scope:

- starting Trend Analysis v2.6
- changing Strategy
- changing Learning
- changing Account Health
- changing QC
- changing Experiment
- changing the orchestrator
- changing the core pipeline
- converting failures into residual monitoring

## 3. Preconditions

Required subsystem gates:

- `OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json`

Required planning and governance references:

- `docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md`
- `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md`
- `OUT/audit/system_governance_registry.json`

Required global audit references:

- `OUT/audit/cortai_runtime_v2_5_all_agents_extreme_checklist/final_verdict.json`
- `OUT/audit/cortai_runtime_v2_5_max_integrity_gate/final_verdict.json`
- `OUT/audit/cortai_runtime_v2_5_final_audit/final_audit_report.json`

Required command:

`python tests/gates/phase_2_6/run_phase_2_6_partial_master_gate_learning_account_health.py`

## 4. Blocks A-P

### Block A - Repository And Artifact Integrity

Validates that required documents, runners, and JSON artifacts exist and parse.

Fails if a mandatory document, runner, artifact, or valid JSON payload is missing.

### Block B - Governance Consistency

Validates frozen governance posture, no core modification policy, no subsystem mutation without governance reopen, and isolated subsystem work.

Fails if governance policy is absent, false, contradictory, or indicates unauthorized core/Strategy/QC/Learning/Experiment mutation.

### Block C - Learning v2.6 Gate Integrity

Validates the Learning Agent v2.6 excellence gate verdict and critical dimensions.

Fails on `HOLD`, fake confidence, silent failure, trace incompleteness, boundary violation, contamination mishandling, unbounded Strategy pressure, or missing policy safety.

### Block D - Account Health v2.6 Gate Integrity

Validates the Account Health Agent v2.6 excellence gate verdict and critical dimensions.

Fails on `HOLD`, missing telemetry enrichment, incomplete risk components, fake confidence, hidden degraded input, missing constraint rationale, broken `HOLD`, boundary violation, or silent failure.

### Block E - Learning Runtime Contract Integrity

Imports and validates Learning contracts and runtime output shape.

Required surfaces include `LearningAgentResult`, `LearningInsights`, `LearningPolicy`, `PatternFindingSummary`, `LearningStrategyPressure`, `LearningStrategyPressureTarget`, `learning_trace`, `policy_trace`, and `confidence_summary`.

Fails if contracts cannot import, serialize, or expose required backward-compatible fields.

### Block F - Account Health Runtime Contract Integrity

Imports and validates Account Health contracts and runtime output shape.

Required surfaces include `AccountHealthInput`, `AccountHealthResult`, `AccountHealthDecision`, `telemetry_summary`, `risk_score`, `risk_components`, `confidence`, `confidence_level`, `temporal_health`, `degraded_input_decision`, `constraint_rationale`, `health_trace`, and backward-compatible `decision_trace`.

Fails if contracts cannot import, serialize, or expose required fields.

### Block G - Unit Test Battery

Runs the Learning, Account Health, Strategy, orchestrator, Experiment, Attribution, and pipeline test battery.

Fails if a critical test fails, times out without explicit classification, or is skipped silently.

### Block H - Controlled Cross-Agent Scenarios

Runs controlled scenarios through real Learning, Account Health, and Strategy services.

Scenarios cover `SAFE`, `CAUTION`, `HOLD`, degraded Account Health, contaminated Learning, and mixed confidence/authority cases.

Fails if Learning overrides Health, Health becomes Strategy, Strategy ownership disappears, constraints vanish, or traces contradict outcomes.

### Block I - Determinism And Replay

Replays Learning, Account Health, and cross-agent scenarios.

Fails if stable fields drift without input changes.

### Block J - Fallback Honesty

Validates explicit Learning fallback/contamination handling and Account Health fallback/degraded input visibility.

Fails if fallback is hidden, treated as clean evidence, or produces inflated confidence.

### Block K - Boundary Preservation

Validates that Learning does not become Strategy/QC/Experiment/core and Account Health does not become Strategy/QC/Learning/Experiment/core.

Fails on ownership drift or hidden enforcement.

### Block L - Security And Logical Vulnerability Surface

Checks for fake confidence, fake telemetry, fake lineage, fake rationale, hidden degraded input, orphan constraints, silent `HOLD` downgrade, silent `SAFE` upgrade, contamination dominance, unsupported overblocking, and missing evidence treated as success.

Fails on any critical logical vulnerability.

### Block M - Trace And Auditability Completeness

Validates Learning trace reconstruction and Account Health `health_trace` reconstruction.

Fails if trace is incomplete, contradictory, or missing critical audit sections.

### Block N - Master Artifact Consistency

Compares Learning gate, Account Health gate, global audit artifacts, governance registry, and master state.

Fails if a recent artifact contradicts readiness, contains `HOLD`, or treats blockers as residual monitoring.

### Block O - Residual Monitoring Classification

Classifies known residuals as monitorable only when they are non-structural and explicit.

Fails if structural blockers are classified as residuals.

### Block P - Final Release Decision

Derives final verdict from all previous blocks.

Fails if any critical block fails, silent failure is detected, non-determinism appears, boundary is violated, trace is incomplete, or `HOLD` authority is broken.

## 5. Critical Failure Definitions

Critical failures include:

- missing mandatory artifact or invalid JSON artifact
- `HOLD` verdict in Learning or Account Health gate
- critical failures greater than zero in a subsystem gate
- non-empty blocking failures in a subsystem gate
- fake or constant confidence
- silent failure detected
- boundary violation
- trace incompleteness
- missing constraint rationale
- hidden fallback or hidden degraded input
- non-deterministic replay
- `HOLD` downgrade
- Learning pressure overriding Health or Strategy
- Account Health becoming Strategy
- Strategy/core/orchestrator mutation during this gate
- failed critical test battery

## 6. Verdict Semantics

`HOLD`:

Required if any blocking failure, critical failure, fake confidence, silent failure, boundary violation, trace incompleteness, critical test failure, non-determinism, or broken `HOLD` authority is detected.

`GO_WITH_MONITORING`:

Allowed when all critical blocks pass and remaining residues are explicit, bounded, and related to runtime maturity, longitudinal history, producer coverage, or already-known operational monitoring.

`GO`:

Allowed only when all blocks pass and no meaningful residual monitoring remains.

The expected likely result before Trend Analysis is `GO_WITH_MONITORING`. The runner must derive it from evidence and must not hardcode it.

## 7. Required Artifacts

The runner must write:

- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/final_verdict.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/checklist_results.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/scenario_outputs.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/metrics.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/cross_agent_consistency.json`

The final verdict must include:

- Learning Agent v2.6 readiness summary
- Account Health Agent v2.6 readiness summary
- block results A-P
- tests executed
- metrics
- blocking failures
- residual monitoring
- recommendation to proceed or hold before Trend Analysis

## 8. Final Decision Rule

The partial master gate may recommend proceeding to Trend Analysis v2.6 only when:

- Learning Agent v2.6 gate is `GO` or `GO_WITH_MONITORING`
- Account Health Agent v2.6 gate is `GO` or `GO_WITH_MONITORING`
- all blocks A-P pass
- all critical tests pass
- no fake confidence is detected
- no silent failure is detected
- no boundary violation is detected
- no non-determinism is detected
- no missing critical trace exists
- all residuals are explicit, bounded, and non-structural

Final recommendation values:

- `PROCEED_TO_TREND_ANALYSIS_AGENT_V2_6_PLAN`
- `HOLD_BEFORE_PROCEEDING`


---

## Source: `docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_1_MASTER_GATE.md`

# PHASE_2_6_WAVE_1_MASTER_GATE

## 1. Purpose

`PHASE_2_6_WAVE_1_MASTER_GATE` is the official consolidated gate for Phase 2.6 Wave 1.

The gate validates whether the Wave 1 agents that have completed their own excellence gates can be considered ready for v3 with monitoring before any Wave 2 work starts.

This is an audit artifact. It must not implement features, mutate runtime behavior, fix code to pass, modify Strategy, modify Asset, modify the orchestrator, or change the core pipeline.

The gate exists to prove readiness, not to create readiness.

## 2. Scope

In scope:

- Learning Agent v2.6
- Account Health Agent v2.6
- Trend Analysis Agent v2.6
- Strategy integration surfaces
- creative orchestrator compatibility
- governance consistency
- contract import and serialization
- deterministic replay
- fallback honesty
- boundary preservation
- trace completeness
- silent failure detection
- residual monitoring classification
- consistency with canonical Phase 2.6 artifacts

Out of scope:

- starting Wave 2
- changing Learning
- changing Account Health
- changing Trend Analysis
- changing Strategy
- changing Asset
- changing QC
- changing Experiment
- changing the orchestrator
- changing the core pipeline
- converting blockers into residual monitoring

## 3. Preconditions

Required child gates:

- `OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/trend_analysis_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/final_verdict.json`

Required planning and governance references:

- `docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md`
- `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md`
- `OUT/audit/system_governance_registry.json`

Required command:

`python tests/gates/phase_2_6/run_phase_2_6_wave_1_master_gate.py`

## 4. Blocks A-P

### Block A - Artifact Integrity

Validates that required documents, runners, final verdict artifacts, and JSON artifacts exist and parse.

Fails if any mandatory artifact is missing or invalid.

### Block B - Governance Consistency

Validates the frozen governance posture, `FROZEN_UNLESS_GOVERNANCE_REOPEN`, no core modification posture, and no unauthorized Strategy/orchestrator mutation implied by artifacts.

Fails if governance policy is absent, false, contradictory, or suggests unauthorized ownership drift.

### Block C - Learning Gate Integrity

Validates Learning v2.6 child gate readiness.

Required checks include non-HOLD verdict, no blockers, evidence-backed output, calibrated confidence, temporal weighting, contamination handling, bounded Strategy pressure, traceability, fallback honesty, boundary preservation, and no silent failures.

### Block D - Account Health Gate Integrity

Validates Account Health v2.6 child gate readiness.

Required checks include no blockers, telemetry enrichment, risk components, calibrated confidence, temporal health, degraded input safety, constraint rationale completeness, traceability, HOLD authority preservation, fallback honesty, boundary preservation, and no silent failures.

### Block E - Trend Analysis Gate Integrity

Validates Trend Analysis v2.6 child gate readiness.

Required checks include source governance, evidence backing, freshness discipline, calibrated context confidence, meaningful shift analysis, downstream utility clarity, traceability, fallback honesty, boundary preservation, determinism, and no silent failures.

### Block F - Contract Integrity

Imports and serializes representative outputs/contracts for Learning, Account Health, Trend Analysis, and Strategy integration surfaces.

Fails if imports break, serialization fails, or required additive fields disappear.

### Block G - Test Battery

Runs the Wave 1 relevant unit/integration test battery through `pytest`.

Fails on test failure, unclassified timeout, or hidden execution error.

### Block H - Cross-Agent Upstream Scenarios

Executes controlled scenarios through real services to prove:

- Health `HOLD` outranks Learning and Trend
- Health `CAUTION` constrains without becoming Strategy
- Learning strong pressure remains bounded
- Trend high-confidence context informs downstream only as context
- Trend fallback/low-confidence context does not become strong Strategy authority
- contaminated Learning evidence remains weak even when Trend is strong
- stale/expired Trend context remains visible
- upstream traces are not contradictory

### Block I - Determinism And Replay

Validates stable replay for Learning, Account Health, Trend Analysis, and a combined upstream scenario.

Fails on unexplained drift.

### Block J - Fallback Honesty

Validates explicit fallback/contamination/degradation visibility for all Wave 1 agents.

Fails if fallback is hidden or represented as strong evidence.

### Block K - Boundary Preservation

Validates that:

- Learning does not become Strategy, QC, Experiment, or Publisher
- Account Health does not become Strategy, QC, Learning, or Experiment
- Trend does not become Strategy, Asset, QC, Publisher, or a hidden authority
- Strategy remains the control layer
- QC remains final product quality authority

### Block L - Security And Logical Vulnerability Surface

Fails on fake confidence, fake telemetry, fake provenance, hidden degraded input, hidden fallback, orphan constraints, silent `HOLD` downgrade, inflated Trend fallback, Learning contamination dominance, non-determinism, or silent failure indicators.

### Block M - Trace And Auditability

Validates:

- Learning trace reconstructs policy
- Account Health `health_trace` reconstructs `SAFE` / `CAUTION` / `HOLD`
- Trend `trend_trace` reconstructs `TrendProfile` emission
- audit summaries are honest

### Block N - Residual Monitoring Classification

Collects residuals from child gates and classifies only non-structural residues as monitoring.

Acceptable categories include short runtime history, producer coverage still expanding, longitudinal source diversity still expanding, and production maturity monitoring.

Fails if structural blockers are classified as residual monitoring.

### Block O - Master Consistency

Compares the Wave 1 master state with the partial Learning + Account Health master gate, governance registry, runtime master state, and available global gates.

Fails on contradiction, recent `HOLD`, or missing canonical state.

### Block P - Final Release Decision

Derives the final verdict from all blocks.

Fails if any critical block fails.

## 5. Critical Failure Definitions

Critical failures include:

- missing mandatory artifact
- invalid JSON artifact
- child gate verdict `HOLD`
- child gate blocking failures
- child gate critical failures
- fake confidence
- silent failure detected
- boundary violation
- trace incompleteness
- hidden fallback
- hidden degraded input
- non-deterministic replay
- `HOLD` downgrade
- Strategy ownership loss
- core/orchestrator mutation implied by audit evidence
- critical unit/integration test failure
- structural blocker classified as residual monitoring

## 6. Verdict Semantics

`HOLD`:

Required when any critical block fails, any child gate is `HOLD`, any blocking failures exist, fake confidence is detected, silent failure is detected, boundary is violated, trace is incomplete, fallback is hidden, or non-determinism is detected.

`GO_WITH_MONITORING`:

Allowed when all critical blocks pass and remaining residuals are explicit, bounded, non-structural, and related to runtime maturity, producer coverage, or longitudinal evidence maturity.

`GO`:

Allowed only when all blocks pass and no meaningful residual monitoring remains.

Expected likely verdict is `GO_WITH_MONITORING`. The runner must derive it from evidence and must not hardcode it.

## 7. Required Artifacts

The runner writes:

- `OUT/audit/phase_2_6_wave_1_master_gate/final_verdict.json`
- `OUT/audit/phase_2_6_wave_1_master_gate/checklist_results.json`
- `OUT/audit/phase_2_6_wave_1_master_gate/scenario_outputs.json`
- `OUT/audit/phase_2_6_wave_1_master_gate/metrics.json`
- `OUT/audit/phase_2_6_wave_1_master_gate/cross_agent_consistency.json`

The final verdict must include:

- child gate readiness summaries
- block results A-P
- test execution records
- metrics
- blocking failures
- residual monitoring
- recommendation to proceed or hold before Wave 2

## 8. Final Decision Rule

The Wave 1 Master Gate may recommend proceeding to Wave 2 only when:

- Learning Agent v2.6 is `GO` or `GO_WITH_MONITORING`
- Account Health Agent v2.6 is `GO` or `GO_WITH_MONITORING`
- Trend Analysis Agent v2.6 is `GO` or `GO_WITH_MONITORING`
- all blocks A-P pass
- critical tests pass
- no fake confidence is detected
- no silent failure is detected
- no boundary violation is detected
- no non-determinism is detected
- all required traces are reconstructible
- all residuals are bounded and non-structural

Final recommendation values:

- `PROCEED_TO_PHASE_2_6_WAVE_2_PLAN`
- `HOLD_BEFORE_WAVE_2`


---

## Source: `docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_2_MASTER_GATE.md`

# PHASE_2_6_WAVE_2_MASTER_GATE

## 1. Purpose

`PHASE_2_6_WAVE_2_MASTER_GATE` is the official consolidated gate for Phase 2.6 Wave 2.

The gate validates whether the output-quality agents that completed their own excellence gates can be considered ready for v3 with monitoring as an integrated Wave 2 surface.

This is an audit artifact. It must not implement features, mutate runtime behavior, fix code to pass, modify Strategy, modify Script, Voice, Asset Selection, Video QC, Publisher, the orchestrator, or the core pipeline.

The gate exists to prove readiness, not to create readiness.

## 2. Scope

In scope:

- Script Agent v2.6
- Voice Agent v2.6
- Asset Selection Agent v2.6
- Video QC Agent v2.6
- output-quality contract compatibility
- Strategy and orchestrator compatibility
- content pipeline compatibility
- deterministic replay
- fallback honesty
- boundary preservation
- trace completeness
- silent failure detection
- residual monitoring classification
- consistency with child excellence gates

Out of scope:

- changing Script, Voice, Asset Selection, Video QC, Strategy, Publisher, orchestrator, or core pipeline
- changing provider order
- changing asset ranking
- changing QC thresholds
- changing publishability logic
- adding repair, regeneration, rerender, publishing, or performance prediction
- converting blockers into residual monitoring

## 3. Preconditions

Required child gates:

- `OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json`

Required planning and governance references:

- `docs/runtime/phase-2-6/master/PHASE_2_6_WAVE_2_OUTPUT_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/video-qc/VIDEO_QC_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md`
- `OUT/audit/system_governance_registry.json`

Required command:

`python tests/gates/phase_2_6/run_phase_2_6_wave_2_master_gate.py`

## 4. Blocks A-P

### Block A - Artifact Integrity

Validates required docs, child gate artifacts, runners, and JSON payloads.

Fails if any mandatory artifact is missing or invalid.

### Block B - Governance Consistency

Validates frozen governance posture, core immutability, isolated subsystem work, and no unauthorized Strategy/orchestrator/core mutation implied by artifacts.

Fails on governance contradiction or ownership drift.

### Block C - Script Gate Integrity

Validates Script v2.6 child gate readiness, including context governance, quality rubric, hook/setup/payoff analysis, fallback honesty, calibrated confidence, traceability, boundary preservation, determinism, and no silent failures.

### Block D - Voice Gate Integrity

Validates Voice v2.6 child gate readiness, including contract governance, delivery semantics, timing, monotony/contrast, provider fallback honesty, audio validation linkage, calibrated confidence, traceability, TTS Router boundary, determinism, and no silent failures.

### Block E - Asset Gate Integrity

Validates Asset Selection v2.6 child gate readiness, including context governance, catalog/source governance, visual intent, semantic alignment, truthfulness, fallback honesty, diversity, confidence, traceability, selection/ranking/fallback preservation, boundary preservation, determinism, and no silent failures.

### Block F - Video QC Gate Integrity

Validates Video QC v2.6 child gate readiness, including input governance, evidence scoring, confidence honesty, decision semantics, severity, reconstructible `qc_trace`, `APPROVE/HOLD/REJECT` preservation, publishability preservation, boundary preservation, determinism, and no silent failures.

### Block G - Contract Integrity

Imports and serializes representative outputs/contracts for Script, Voice, Asset Selection, Video QC, and Strategy integration surfaces.

Fails if imports break, serialization fails, or required additive fields disappear.

### Block H - Output Pipeline Integration

Executes controlled real-service scenarios proving Script output can feed Voice and Asset surfaces, and QC can evaluate final artifact surfaces without repairing, publishing, rewriting, rerendering, or predicting performance.

### Block I - Orchestrator Compatibility

Runs orchestrator compatibility tests and validates that existing QC governance remains the final output publishability path.

### Block J - Determinism And Replay

Replays controlled Script, Voice, Asset, Video QC, and combined output scenarios.

Fails on stable-field drift without input change.

### Block K - Fallback Honesty

Validates Script fallback, Voice fallback/trace absence, Asset safe-default fallback, and Video QC missing/fallback evidence remain explicit and not represented as success.

### Block L - Boundary Preservation

Validates:

- Script does not become Strategy, Voice, Asset, QC, or Publisher
- Voice does not become TTS Router, Strategy, QC, or Publisher
- Asset Selection does not become Strategy, QC, Publisher, or visual truth authority beyond metadata
- Video QC does not repair, publish, rewrite, rerender, replace assets, resynthesize voice, or predict performance
- Strategy remains the control layer
- Publisher remains out of scope

### Block M - Trace And Auditability

Validates:

- `script_trace` reconstructs `ScriptPlan`
- `voice_trace` reconstructs `VoicePlan`
- `asset_trace` reconstructs `AssetPlan`
- `qc_trace` reconstructs `APPROVE/HOLD/REJECT`
- audit summaries are honest

### Block N - Security And Logical Vulnerability Surface

Fails on fake confidence, fake evidence, hidden fallback, hidden degraded input, hidden safe default, silent publishability authority, hidden QC override, non-determinism, performance prediction, or silent failure indicators.

### Block O - Residual Monitoring Classification

Collects residuals from the four child gates and classifies only non-structural residues as monitoring.

Acceptable categories include runtime history still short, provider execution history still short, catalog coverage expanding, product signal calibration maturing, media probe coverage environment-dependent, and layer attribution evidence still limited.

Fails if structural blockers are classified as residual monitoring.

### Block P - Final Release Decision

Derives the final verdict from all blocks.

Fails if any critical block fails.

## 5. Critical Failure Definitions

Critical failures include:

- missing mandatory child gate artifact
- child gate verdict `HOLD`
- child gate blocking failures
- child gate critical failures
- failed critical test battery
- fake confidence
- silent failure detected
- boundary violation
- trace incompleteness
- hidden fallback
- non-deterministic replay
- publishability inconsistency
- output-quality agent overriding Strategy
- Video QC changing status/publishability semantics
- Publisher behavior introduced
- core/orchestrator mutation implied by audit evidence
- performance prediction introduced
- structural blocker classified as residual monitoring

## 6. Verdict Semantics

`HOLD`:

Required when any critical block fails, any child gate is `HOLD`, any blocking failure exists, fake confidence is detected, silent failure is detected, boundary is violated, trace is incomplete, fallback is hidden, publishability is inconsistent, or non-determinism is detected.

`GO_WITH_MONITORING`:

Allowed when all critical blocks pass and remaining residuals are explicit, bounded, non-structural, and related to runtime maturity, provider/catalog/media-probe coverage, or longitudinal evidence maturity.

`GO`:

Allowed only when all blocks pass and no meaningful residual monitoring remains.

Expected likely verdict is `GO_WITH_MONITORING`. The runner must derive it from evidence and must not hardcode it.

## 7. Required Artifacts

The runner writes:

- `OUT/audit/phase_2_6_wave_2_master_gate/final_verdict.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/checklist_results.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/scenario_outputs.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/metrics.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/cross_agent_consistency.json`

The final verdict must include child gate readiness summaries, block results A-P, test execution records, metrics, blocking failures, residual monitoring, and recommendation to proceed or hold.

## 8. Final Decision Rule

The Wave 2 Master Gate may recommend proceeding only when:

- Script Agent v2.6 is `GO` or `GO_WITH_MONITORING`
- Voice Agent v2.6 is `GO` or `GO_WITH_MONITORING`
- Asset Selection Agent v2.6 is `GO` or `GO_WITH_MONITORING`
- Video QC Agent v2.6 is `GO` or `GO_WITH_MONITORING`
- all blocks A-P pass
- critical tests pass
- no fake confidence is detected
- no silent failure is detected
- no boundary violation is detected
- no non-determinism is detected
- all required traces are reconstructible
- all residuals are bounded and non-structural

Final recommendation values:

- `PROCEED_TO_PHASE_2_6_FINAL_MASTER_GATE`
- `HOLD_BEFORE_PHASE_2_6_FINAL_MASTER_GATE`


---

## Source: `docs/runtime/phase-2-6/master/PHASE_2_6_WAVE_2_OUTPUT_EXCELLENCE_PLAN.md`

# PHASE_2_6_WAVE_2_OUTPUT_EXCELLENCE_PLAN

## 1. Purpose

`PHASE_2_6_WAVE_2_OUTPUT_EXCELLENCE_PLAN` is the formal excellence plan for Phase 2.6 Wave 2.

Wave 2 focuses on the output-quality agents:

- Script Agent
- Voice Agent
- Asset Selection Agent
- Video QC Agent

Wave 1 hardened the upstream evidence and governance layer:

- Learning Agent v2.6
- Account Health Agent v2.6
- Trend Analysis Agent v2.6

The Absolute Master Gate before Wave 2 returned:

```json
{
  "absolute_master_gate_pre_wave_2": "GO_WITH_MONITORING",
  "critical_failures": 0,
  "blocking_failures": [],
  "silent_failures": false,
  "fake_confidence": false,
  "boundary_violations": false,
  "non_determinism": false,
  "trace_incomplete": false,
  "recommendation": "PROCEED_TO_PHASE_2_6_WAVE_2_PLAN"
}
```

This authorizes planning for Wave 2.

It does not authorize broad runtime redesign.

Wave 2 exists to make the final produced content stronger, more traceable, more robust under variation, and more honestly validated without weakening the frozen runtime governance model.

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

Wave 2 must preserve:

- frozen core pipeline
- Creative Orchestrator ownership
- Strategy ownership
- Account Health `SAFE / CAUTION / HOLD` authority
- Learning bounded pressure
- Trend advisory context boundary
- QC final product-quality authority
- Experiment ownership
- Asset ownership over visual selection only
- Voice ownership over delivery plan only
- Script ownership over narrative text only
- no Publisher work
- no hidden publish enforcement
- no external expansion
- no provider expansion unless explicitly justified by a later gated plan
- no fake confidence
- no hidden fallback
- no silent schema break

## 3. Scope

In scope:

- narrative quality hardening
- voice delivery quality hardening
- visual decision and asset trace hardening
- QC product-signal hardening
- output trace consolidation
- fallback honesty
- product-quality scenario batteries
- deterministic replay where required
- contract-preserving additive fields
- dedicated excellence gates per agent
- Wave 2 master gate before Wave 3

Out of scope:

- modifying the core pipeline
- changing Strategy behavior
- changing Account Health behavior
- changing Learning behavior
- changing Trend behavior
- changing Experiment ownership
- implementing Publisher
- changing publish manifest semantics
- adding uncontrolled external data or provider dependencies
- broad prompt/provider expansion
- making QC silently enforce publish policy outside existing governance
- turning output agents into a hidden strategic brain

## 4. Wave 2 Objective

Wave 2 must move the output layer from:

- technically functional
- integrated
- traceable enough for operation
- quality-monitored
- `GO_WITH_MONITORING`

into:

- product-quality stronger
- narrative-specific
- voice-aligned
- visually justified
- QC-auditable
- fallback-honest
- contract-stable
- deterministic where required
- ready for v3 with monitoring

The goal is not aesthetic perfection.

The goal is to remove hidden output fragility before v3.

## 5. Operating Policy

Wave 2 must follow the same discipline as Wave 1.

Policy:

```json
{
  "phase_2_6_wave_2_policy": {
    "current_focus": "OUTPUT_AGENTS_ONLY",
    "do_not_implement_all_at_once": true,
    "advance_only_after_validation": true,
    "no_core_pipeline_modification": true,
    "no_strategy_modification": true,
    "no_publisher_work": true,
    "no_hidden_enforcement": true
  }
}
```

The correct order is:

1. Script Agent v2.6 Excellence Plan
2. Script Agent v2.6 bounded workstreams and gate
3. Voice Agent v2.6 Excellence Plan
4. Voice Agent v2.6 bounded workstreams and gate
5. Asset Selection Agent v2.6 Excellence Plan
6. Asset Selection Agent v2.6 bounded workstreams and gate
7. Video QC Agent v2.6 Excellence Plan
8. Video QC Agent v2.6 bounded workstreams and gate
9. Phase 2.6 Wave 2 Master Gate

No agent should start implementation without its own formal plan.

No downstream workstream should begin until the current workstream has been validated.

## 6. Agent Boundaries

### 6.1 Script Agent Boundary

Script owns:

- hook text
- setup text
- payoff text
- narration structure
- narrative specificity
- text-level style and clarity
- script generation trace

Script must not own:

- Strategy decisions
- Account Health posture
- Trend source authority
- Learning policy
- Voice provider selection
- Asset selection
- QC publishability
- Experiment assignment
- core pipeline execution

### 6.2 Voice Agent Boundary

Voice owns:

- `VoicePlan`
- voice provider request
- voice identity
- delivery profile
- segment-level delivery semantics
- provider and fallback trace
- voice-plan interpretation

Voice must not own:

- script text
- strategy
- asset selection
- QC decision
- publishability
- direct runtime publish policy
- provider expansion without gated justification

### 6.3 Asset Selection Boundary

Asset owns:

- visual interpretation
- `AssetPlan`
- segment-level visual decisions
- asset category/tag/source requests
- local catalog selection
- visual trace
- fallback visual selection

Asset must not own:

- script text
- voice delivery
- strategy
- QC decision
- publisher behavior
- uncontrolled external collection
- runtime HTTP fetching
- ungoverned image generation

### 6.4 Video QC Boundary

QC owns:

- final rendered artifact evaluation
- technical validity checks
- product-quality signals
- QC reason codes
- QC trace
- `APPROVE / HOLD / REJECT` if introduced through additive bounded contract
- publishability assessment as a product-quality decision, not as hidden runtime publish enforcement

QC must not own:

- script rewriting
- voice resynthesis
- asset replacement
- Strategy
- Account Health
- Learning
- Trend
- Experiment
- Publisher implementation
- core pipeline mutation
- hidden publish cancellation outside governance

Important boundary rule:

If true publish-manifest enforcement requires changing pipeline order or publish semantics, that requires explicit governance reopen. Wave 2 may expose stronger QC decisions and traces, but must not smuggle publisher behavior through QC.

## 7. Agent Sequence And Rationale

### 7.1 Script First

Script is first because it defines the content spine:

- weak hook limits retention
- weak setup weakens pacing
- weak payoff weakens memorability
- voice and asset quality depend on script intent
- QC product signals need clear script structure to evaluate

Script must become sharper before Voice and Asset can align properly.

### 7.2 Voice Second

Voice is second because it materializes script intent:

- monotone delivery weakens good scripts
- poor pacing weakens retention
- weak contrast between hook/setup/payoff reduces product impact
- voice trace must be strong before QC can audit audio delivery

Voice should harden after Script structure is clearer.

### 7.3 Asset Third

Asset is third because visual selection depends on Script and Trend:

- hook visuals must materialize the anomaly
- setup visuals must create escalation, not filler
- payoff visuals must support the reveal
- current asset gap is largely trace and decision-contract maturity

Asset must be hardened before QC can judge final audiovisual cohesion meaningfully.

### 7.4 QC Fourth

QC is fourth because it validates the combined output:

- Script, Voice, and Asset must expose stronger traces first
- QC should not invent signals that upstream agents cannot explain
- QC needs product-layer evidence, not only technical proxies
- QC must remain authority without becoming a repair engine

QC is the final Wave 2 agent before the Wave 2 Master Gate.

## 8. Script Agent v2.6 Plan

### 8.1 Current State

Script is already operational:

- real provider path active
- structured `hook / setup / payoff` output
- fallback chain explicit
- context from Strategy, Trend, Learning, and Experiment reaches script generation
- prior excellence gate proved material improvement

Known risk:

- output may remain conservative under some contexts
- hooks can be technically valid but not sufficiently sharp
- setup can be functional rather than escalating
- payoff can be coherent but not memorable enough
- script-quality trace is not yet audit-grade enough for v3

### 8.2 Objective

Make Script more specific, varied, memorable, and auditable without weakening structure or provider fallback safety.

Script confidence must describe trust in script construction, not expected video performance.

### 8.3 Workstreams

1. `script_context_governance`
   - validate what context Script consumes
   - distinguish Strategy, Trend, Learning, Experiment, and Account Health constraints
   - prevent unsupported context from becoming narrative claims
   - expose context use trace

2. `script_quality_rubric`
   - define deterministic rubric for hook, setup, payoff, specificity, clarity, novelty, and coherence
   - do not use fake scoring
   - expose rubric rationale
   - use as audit layer first, not as hidden rewrite logic

3. `hook_strength_hardening`
   - improve anomaly-first hooks
   - reduce generic openers
   - preserve niche and topic coherence
   - expose hook reason codes

4. `setup_progression_hardening`
   - make setup escalate the initial anomaly
   - reduce filler/context-only setup
   - preserve concise runtime format
   - expose setup function in trace

5. `payoff_memorability_hardening`
   - strengthen final reveal specificity
   - reduce generic explanation endings
   - connect payoff to hook anomaly
   - expose payoff rationale

6. `script_diversity_and_anti_cliche`
   - detect repeated structures
   - identify clichÃ© patterns
   - avoid overfitting to a single hook family
   - preserve deterministic behavior

7. `script_fallback_and_provider_honesty`
   - ensure fallback mode is always visible
   - avoid high quality/confidence claims under emergency fallback
   - preserve provider trace
   - do not add provider expansion

8. `script_trace_and_auditability`
   - consolidate context use, rubric, hook/setup/payoff rationale, provider path, fallback, and warnings
   - create reconstructible `script_trace`

9. `script_agent_v2_6_excellence_gate`
   - run controlled script scenarios
   - run provider/fallback scenarios
   - run anti-clichÃ© battery
   - run orchestrator integration
   - write final verdict artifact

### 8.4 Required Output By End Of Script v2.6

Script result or trace should expose additive fields such as:

- `script_trace`
- `context_usage_summary`
- `script_quality_rubric`
- `hook_rationale`
- `setup_rationale`
- `payoff_rationale`
- `fallback_honesty`
- `provider_trace`

Do not remove existing script fields.

### 8.5 Script Exit Criteria

Script is v2.6-complete only when:

- hook/setup/payoff rationale is explicit
- context use is traceable
- fallback is visible
- emergency fallback does not claim excellence
- script quality rubric is deterministic
- anti-clichÃ© behavior is measurable
- controlled output battery passes
- orchestrator integration remains stable
- Strategy unchanged
- core pipeline unchanged
- dedicated Script v2.6 gate passes

## 9. Voice Agent v2.6 Plan

### 9.1 Current State

Voice is operational:

- `VoicePlan` exists
- voice interpreter exists
- TTS router exists
- Kokoro is current local baseline
- Piper remains hard fallback
- provider trace exists
- fallback is explicit

Known risk:

- delivery can still be monotone
- segment-level contrast can be weak
- timing alignment may not fully follow hook/setup/payoff intensity
- provider execution trace can be strengthened
- quality validation remains proxy-based

### 9.2 Objective

Make Voice more expressive, segment-aware, auditable, and aligned with Script and Strategy without adding uncontrolled provider expansion.

Voice confidence must measure trust in voice-plan execution and delivery fit, not expected video performance.

### 9.3 Workstreams

1. `voice_plan_contract_hardening`
   - verify `VoicePlan` fields are complete and backward-compatible
   - expose requested vs executed voice parameters
   - ensure provider trace is complete

2. `delivery_profile_semantics`
   - define segment-level delivery intent
   - distinguish hook urgency, setup tension, payoff reveal
   - preserve deterministic mapping
   - avoid freeform delivery drift

3. `segment_timing_and_pause_hardening`
   - audit pause placement
   - align timing with script segments
   - expose timing rationale
   - avoid hidden audio mutation

4. `monotony_and_contrast_analysis`
   - add deterministic proxies for monotony and contrast
   - identify weak contrast under long narration
   - keep proxy honest and bounded

5. `provider_and_fallback_honesty`
   - distinguish requested provider, executed provider, and fallback provider
   - preserve Kokoro baseline and Piper fallback
   - do not add provider expansion in this workstream

6. `voice_audio_validation`
   - verify output audio existence, duration, format, and basic integrity
   - keep technical validation separate from perceptual claims
   - expose validation summary

7. `voice_trace_and_auditability`
   - consolidate provider, delivery profile, segment timing, monotony/contrast, fallback, and validation
   - create reconstructible `voice_trace`

8. `voice_agent_v2_6_excellence_gate`
   - run textual battery
   - run provider/fallback battery
   - run audio validation battery
   - run orchestrator/pipeline integration
   - write final verdict artifact

### 9.4 Required Output By End Of Voice v2.6

Voice result or trace should expose additive fields such as:

- `voice_trace`
- `requested_provider`
- `executed_provider`
- `fallback_path`
- `delivery_profile_summary`
- `segment_timing_summary`
- `monotony_proxy_summary`
- `audio_validation_summary`

Do not remove existing `VoicePlan` fields.

### 9.5 Voice Exit Criteria

Voice is v2.6-complete only when:

- requested vs executed provider is explicit
- fallback path is explicit
- segment-level delivery semantics are traceable
- monotony/contrast proxies are deterministic
- audio validation is explicit
- no provider expansion occurred
- script and strategy alignment is visible
- orchestrator/pipeline integration remains stable
- dedicated Voice v2.6 gate passes

## 10. Asset Selection Agent v2.6 Plan

### 10.1 Current State

Asset Selection is operational and sophisticated:

- segment-level asset planning exists
- local catalog selection exists
- visual trace exists
- deterministic selection exists under stable catalog state
- event-aware scoring exists
- visual-world and atmosphere scoring exist
- offline ingestion infrastructure exists

Known risk:

- formal decision contract is incomplete in persisted runtime outputs
- segment-level entity/anomaly/photographability/justification are not fully materialized
- setup can remain visually weak or phase-1-like
- visual-world enforcement is still mostly soft
- runner-up/candidate explanation is not audit-grade
- fallback visual quality is not sufficiently explained

### 10.2 Objective

Make Asset Selection explainable, visually specific, traceable, and robust under topic variety without adding runtime external fetching or ungoverned generation.

Asset confidence must describe trust in visual selection fit, not expected performance.

### 10.3 Workstreams

1. `asset_decision_contract_hardening`
   - materialize segment-level decision fields
   - include entity, event, anomaly, visibility, photographability, and justification
   - preserve `AssetPlan` backward compatibility
   - expose decision contract in trace

2. `asset_provenance_and_source_trace`
   - distinguish local catalog, curated source, imported source, generated source, and fallback
   - expose asset source class
   - do not add runtime external fetching
   - do not claim source quality without evidence

3. `asset_candidate_scoring_explainability`
   - expose winning candidate rationale
   - expose relevant score components
   - optionally expose bounded runner-up summary
   - avoid opaque ranking claims

4. `setup_specificity_hardening`
   - reduce filler setup visuals
   - strengthen event/context escalation
   - preserve deterministic selector behavior
   - do not broaden ontology without evidence

5. `visual_world_consistency_hardening`
   - make video-level visual-world rationale explicit
   - detect world breaks
   - expose style/coherence trace
   - avoid hidden hard enforcement unless explicitly tested

6. `family_diversity_and_repetition_control`
   - identify family-level repetition, not only file-level repetition
   - preserve legitimate continuity
   - avoid over-penalizing coherent visual worlds

7. `asset_fallback_quality_honesty`
   - make fallback visual selection explicit
   - distinguish safe fallback from high-quality match
   - prevent fallback from inflating visual confidence

8. `asset_trace_and_auditability`
   - consolidate segment decisions, source/provenance, scoring, world consistency, diversity, fallback, and unresolved gaps
   - create reconstructible `asset_trace`

9. `asset_selection_agent_v2_6_excellence_gate`
   - run controlled segment batteries
   - run setup/payoff specificity scenarios
   - run family repetition scenarios
   - run fallback scenarios
   - run orchestrator/pipeline integration
   - write final verdict artifact

### 10.4 Required Output By End Of Asset v2.6

Asset result or trace should expose additive fields such as:

- `asset_trace`
- `segment_decision_contract`
- `source_provenance_summary`
- `candidate_scoring_summary`
- `visual_world_summary`
- `family_diversity_summary`
- `fallback_visual_summary`
- `unresolved_visual_warnings`

Do not remove existing `AssetPlan`, `visual_trace`, or runtime path fields.

### 10.5 Asset Exit Criteria

Asset is v2.6-complete only when:

- every segment has explicit decision rationale
- source/provenance is visible
- fallback is not treated as strong visual evidence
- setup specificity improves in controlled scenarios
- visual-world consistency is traceable
- family repetition is detectable
- candidate selection is explainable
- no runtime external fetching is added
- orchestrator/pipeline integration remains stable
- dedicated Asset v2.6 gate passes

## 11. Video QC Agent v2.6 Plan

### 11.1 Current State

QC is operational as a technical validator:

- evaluates rendered artifacts
- returns `APPROVE / REJECT`
- catches missing files, invalid metadata, subtitles, darkness proxy, resolution, and audio stream issues
- is integrated after pipeline completion
- emits QC events

Known risk:

- QC is not yet a full product-quality judge
- `HOLD` is not currently present in the core QC model
- product signal trace is shallow
- publish manifest is created before QC, so QC is not currently a hard publish gate in pipeline order
- `VideoQcInput` and `VideoQcDecision` are partially unused contract surfaces
- confidence and severity are not explicit

### 11.2 Objective

Make QC more product-aware, traceable, and explicit without secretly modifying publish behavior or core pipeline order.

QC should become a stronger final product-quality authority while preserving governance.

### 11.3 Governance Constraint For QC

QC may improve:

- decision trace
- reason codes
- severity
- product-signal scoring
- confidence
- technical validation clarity
- layer-specific audit
- optional additive `HOLD` state only if bounded and backward-compatible

QC must not:

- silently cancel publish manifests
- rewrite pipeline status
- implement Publisher
- rerender content
- repair Script/Voice/Asset/Editor outputs
- change core pipeline order
- create hidden enforcement

If true publish-order enforcement is required, it must be handled by a separate governance reopen or later publisher/pipeline gate, not hidden inside QC Wave 2.

### 11.4 Workstreams

1. `qc_contract_and_status_governance`
   - audit current `VideoQcInput`, `VideoQcDecision`, and `VideoQcResult`
   - define whether `HOLD` can be added additively
   - preserve backward compatibility
   - document status semantics

2. `qc_technical_validation_hardening`
   - strengthen existing technical checks
   - expose severity per reason code
   - distinguish artifact invalidity from product weakness
   - preserve deterministic behavior

3. `qc_product_signal_layer`
   - add bounded product signals for hook readability, caption quality, payoff visibility, audiovisual cohesion, and runtime completeness
   - avoid ML or opaque scoring
   - do not claim human-level taste

4. `qc_confidence_and_severity`
   - calibrate confidence as trust in QC decision
   - confidence must drop when evidence is partial or environment-dependent
   - expose severity and rationale

5. `qc_layer_attribution`
   - link QC findings to Script, Voice, Asset, Editor, or Render layer when evidence supports it
   - do not mutate upstream outputs
   - do not assign blame without evidence

6. `qc_hold_semantics_if_allowed`
   - define `HOLD` for borderline or ambiguous output issues if backward-compatible
   - avoid overblocking
   - preserve `REJECT` for hard technical failures
   - preserve `APPROVE` for clean outputs

7. `qc_trace_and_auditability`
   - consolidate artifacts, reason codes, severity, confidence, layer attribution, product signals, and fallback/environment notes
   - create reconstructible `qc_trace`

8. `qc_agent_v2_6_excellence_gate`
   - run approve/hold/reject controlled scenarios if HOLD is introduced
   - run technical failure scenarios
   - run product-signal edge cases
   - run orchestrator/pipeline integration
   - verify no hidden publisher behavior
   - write final verdict artifact

### 11.5 Required Output By End Of QC v2.6

QC result or trace should expose additive fields such as:

- `qc_trace`
- `qc_version`
- `severity_summary`
- `confidence`
- `confidence_level`
- `product_signal_summary`
- `layer_attribution`
- `environment_probe_summary`
- `publish_boundary_statement`

Existing `VideoQcResult.status`, `reasons`, `checked_at`, and `details` must remain backward-compatible.

### 11.6 QC Exit Criteria

QC is v2.6-complete only when:

- technical checks remain deterministic
- product signals are explicit and bounded
- confidence is honest
- severity is visible
- layer attribution is evidence-backed
- fallback/environment degradation is visible
- `APPROVE / HOLD / REJECT` semantics are explicit if HOLD is introduced
- no hidden publish enforcement is added
- orchestrator/pipeline integration remains stable
- dedicated QC v2.6 gate passes

## 12. Wave 2 Cross-Agent Requirements

Wave 2 must prove not only per-agent improvement, but output-layer consistency.

Required cross-agent checks:

- Script intent reaches Voice
- Script intent reaches Asset
- Strategy constraints still influence Script/Voice/Asset through existing channels
- Trend remains context-only
- Learning pressure remains bounded
- Account Health `HOLD` still blocks before output generation
- QC evaluates rendered output, not planned output only
- QC does not mutate Script/Voice/Asset
- Asset fallback does not hide visual weakness
- Voice fallback does not hide delivery weakness
- Script fallback does not claim excellence
- final execution traces are not contradictory

## 13. Common Trace Requirements

By the end of Wave 2, every output agent should expose reconstructible trace data:

- `script_trace`
- `voice_trace`
- `asset_trace`
- `qc_trace`

Each trace must include:

- inputs consumed
- evidence used
- fallback state
- confidence or trust signal where applicable
- decision rationale
- degraded/missing input notes
- boundary statement
- deterministic reason codes
- audit summary

Trace must not fabricate evidence.

Trace must not claim reconstructibility when required sections are missing.

## 14. Common Confidence Rules

Any confidence added in Wave 2 must follow these rules:

- confidence measures trust in the agent output or decision, not expected video performance
- confidence must not be constant
- confidence must decrease under fallback, missing evidence, degraded inputs, or weak trace
- confidence must include rationale
- confidence must not create hidden enforcement
- confidence must not override Strategy, Account Health, Learning, Trend, Experiment, or QC boundaries

No fake confidence is allowed.

## 15. Common Fallback Rules

Fallback must remain:

- explicit
- traceable
- non-inflated
- lower-authority than clean evidence
- visible in agent result or trace

Forbidden fallback behaviors:

- hidden fallback
- fallback represented as clean execution
- fallback with high confidence without rationale
- fallback silently changing downstream semantics
- fallback used to hide provider, asset, script, voice, or QC weakness

## 16. Common Determinism Rules

Determinism is required where the same controlled input and same local state are expected to produce stable output.

Determinism must be validated for:

- script audit scoring
- voice delivery mapping
- asset selection under fixed catalog and seed
- QC decision under fixed artifacts
- trace reconstruction
- fallback decisions

Allowed non-determinism:

- external provider raw generations, if provider path is explicitly marked and output is not treated as deterministic
- timestamps, if explicitly ignored in replay comparison
- catalog state changes that are explicitly caused by usage-count updates

Any non-determinism must be documented.

## 17. Workstream Advancement Rules

Each workstream may proceed only if:

- the previous workstream has focused tests
- no runtime/core mutation occurred
- no boundary violation occurred
- no existing public contract was broken
- fallback remains honest
- trace is additive
- validation output is documented

Hard stop:

```json
{
  "critical_failures": 0,
  "blocking_failures": [],
  "silent_failures_detected": false,
  "fake_confidence_detected": false,
  "boundary_violations_detected": false,
  "core_pipeline_modified": false
}
```

If violated, Wave 2 must pause.

## 18. Wave 2 Master Gate

After all four agents complete their own gates, create:

- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_2_MASTER_GATE.md`
- `tests/run_phase_2_6_wave_2_output_master_gate.py`
- `OUT/audit/phase_2_6_wave_2_output_master_gate/final_verdict.json`

The Wave 2 Master Gate must validate:

- Script v2.6 gate integrity
- Voice v2.6 gate integrity
- Asset v2.6 gate integrity
- QC v2.6 gate integrity
- cross-agent output consistency
- orchestrator compatibility
- content pipeline compatibility
- fallback honesty
- trace completeness
- confidence honesty
- product-quality scenario battery
- deterministic replay
- boundary preservation
- no hidden publish enforcement
- no core pipeline mutation

Minimum verdict schema:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "audit_type": "PHASE_2_6_WAVE_2_OUTPUT_MASTER_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "script_agent_v2_6": {
    "ready_for_v3_with_monitoring": true,
    "blocking_failures": []
  },
  "voice_agent_v2_6": {
    "ready_for_v3_with_monitoring": true,
    "blocking_failures": []
  },
  "asset_selection_agent_v2_6": {
    "ready_for_v3_with_monitoring": true,
    "blocking_failures": []
  },
  "video_qc_agent_v2_6": {
    "ready_for_v3_with_monitoring": true,
    "blocking_failures": []
  },
  "output_quality_improved": true,
  "fallback_honest": true,
  "traceability_complete": true,
  "boundary_preserved": true,
  "core_pipeline_unchanged": true,
  "hidden_publish_enforcement_detected": false,
  "silent_failures_detected": false,
  "blocking_failures": [],
  "residual_monitoring": []
}
```

## 19. Wave 2 Failure Conditions

Wave 2 must return `HOLD` if any of the following occurs:

- Script outputs generic/clichÃ© text while claiming high confidence
- Voice fallback is hidden
- Voice provider trace is incomplete
- Asset source/provenance is hidden
- Asset fallback is treated as strong visual match
- Asset segment decision lacks rationale
- QC trace is incomplete
- QC adds hidden publish enforcement
- QC claims product judgment without evidence
- any output agent becomes Strategy
- any output agent becomes QC except QC itself
- any output agent modifies core pipeline
- any agent hides fallback
- any confidence is fake or constant
- deterministic replay fails without explanation
- orchestrator behavior regresses
- Account Health `HOLD` no longer blocks upstream
- existing public contracts break

## 20. Expected Residual Monitoring

Likely acceptable residuals:

- long-horizon production quality still under monitoring
- provider variability still under monitoring
- asset catalog coverage still expanding
- voice delivery realism still under monitoring
- QC product-signal calibration still maturing
- controlled validation still dominates some surfaces

Not acceptable as residuals:

- hidden fallback
- missing trace
- fake confidence
- contract break
- core mutation
- hidden publisher behavior
- Strategy boundary violation
- QC authority bypass
- Asset source fabrication
- provider substitution without trace

## 21. Final Position

Wave 2 exists to make the system's outputs stronger, more explainable, and more reliably validated.

It must raise product quality without creating hidden authority.

Script must improve narrative strength.

Voice must improve delivery alignment.

Asset must improve visual decision trace and specificity.

QC must improve product-quality validation without secretly becoming Publisher.

The correct first artifact after this plan is:

`docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_PLAN.md`

No implementation should begin until that Script-specific plan is created and approved.


---

## Source: `docs/runtime/phase-2-6/reports/PHASE_2_6_WAVES_1_AND_2_REPORT.md`

# PHASE_2_6_WAVES_1_AND_2_REPORT

## 1. Executive Summary

Phase 2.6 hardened the CortAI cognitive/runtime agent layer in two governed waves.

Wave 1 focused on upstream interpretation, risk posture and trend context.

Wave 2 focused on output construction, voice planning, visual selection and final artifact quality validation.

Final consolidated result:

```json
{
  "phase": "2.6",
  "wave_1": "GO_WITH_MONITORING",
  "wave_2": "GO_WITH_MONITORING",
  "final_master_gate": "GO_WITH_MONITORING",
  "release_state": "READY_FOR_V3_WITH_MONITORING",
  "critical_failures": 0,
  "blocking_failures": [],
  "fake_confidence_detected": false,
  "silent_failures_detected": false,
  "boundary_violations_detected": false,
  "non_determinism_detected": false,
  "trace_incomplete": false
}
```

The system is not being declared perfect. It is being declared structurally ready for v3 with explicit monitoring.

## 2. Wave 1 Scope

Wave 1 optimized the upstream intelligence and governance layer:

```json
{
  "wave_1_agents": [
    "Learning Agent v2.6",
    "Account Health Agent v2.6",
    "Trend Analysis Agent v2.6"
  ]
}
```

### 2.1 Learning Agent v2.6

Primary goal:

- make learning evidence-backed, contamination-aware, confidence-calibrated and bounded before it can influence Strategy.

Key hardening delivered:

- QC evidence analysis
- confidence calibration
- temporal weighting
- contamination guard
- bounded strategy pressure
- trace and auditability

Final state:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "ready_for_v3_with_monitoring": true,
  "critical_failures": 0,
  "blocking_failures": []
}
```

Boundary preserved:

- Learning may emit bounded pressure.
- Learning must not become Strategy.
- Learning must not decide publishability.

### 2.2 Account Health Agent v2.6

Primary goal:

- make account posture decisions auditable, evidence-backed and safe under degraded input.

Key hardening delivered:

- telemetry enrichment
- risk component scoring
- confidence calibration
- temporal health analysis
- degraded input and fail-closed behavior
- constraint rationale hardening
- health trace and auditability

Final state:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "ready_for_v3_with_monitoring": true,
  "critical_failures": 0,
  "blocking_failures": []
}
```

Boundary preserved:

- Account Health owns `SAFE`, `CAUTION`, `HOLD`.
- HOLD authority is preserved.
- Account Health must not become Strategy, QC or Learning.

### 2.3 Trend Analysis Agent v2.6

Primary goal:

- make trend context source-governed, provenance-aware, freshness-disciplined, confidence-calibrated and traceable.

Key hardening delivered:

- source governance
- evidence lineage and provenance
- freshness and validity
- confidence calibration as trust in trend context
- retrospective shift analysis without forecasting
- downstream utility clarification
- trend trace and auditability

Final state:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "ready_for_v3_with_monitoring": true,
  "critical_failures": 0,
  "blocking_failures": []
}
```

Boundary preserved:

- Trend provides context only.
- Trend must not become Strategy, Asset, QC, Publisher or performance predictor.

## 3. Wave 1 Master Gate

Canonical artifact:

- `OUT/audit/phase_2_6_wave_1_master_gate/final_verdict.json`

Result:

```json
{
  "audit_type": "PHASE_2_6_WAVE_1_MASTER_GATE",
  "verdict": "GO_WITH_MONITORING",
  "blocks": "16/16 passed",
  "tests": "265 passed",
  "critical_failures": 0,
  "blocking_failures": [],
  "recommendation": "PROCEED_TO_PHASE_2_6_WAVE_2_PLAN"
}
```

Wave 1 proved:

- upstream agents are ready for v3 with monitoring
- Account Health HOLD semantics are preserved
- Learning pressure remains bounded
- Trend context remains advisory
- fallback is explicit
- traces are reconstructible
- no boundary violations were detected

## 4. Wave 2 Scope

Wave 2 optimized the output-quality layer:

```json
{
  "wave_2_agents": [
    "Script Agent v2.6",
    "Voice Agent v2.6",
    "Asset Selection Agent v2.6",
    "Video QC Agent v2.6"
  ]
}
```

### 4.1 Script Agent v2.6

Primary goal:

- make script construction governed, measurable and reconstructible without turning Script into Strategy or QC.

Key hardening delivered:

- context governance
- quality rubric
- hook strength analysis
- setup progression analysis
- payoff memorability analysis
- diversity and anti-cliche analysis
- provider and fallback honesty
- confidence calibration as trust in script construction
- script trace and auditability

Final state:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "ready_for_v3_with_monitoring": true,
  "critical_failures": 0,
  "blocking_failures": []
}
```

Boundary preserved:

- Script constructs narrative.
- Script must not become Strategy, Voice, Asset, QC or Publisher.

### 4.2 Voice Agent v2.6

Primary goal:

- make voice planning auditable and honest about execution evidence without becoming the TTS Router.

Key hardening delivered:

- voice plan contract governance
- delivery profile semantics
- segment timing and pause hardening
- monotony and contrast analysis
- provider and fallback honesty
- audio validation linkage
- confidence calibration as trust in voice plan execution readiness
- voice trace and auditability

Final state:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "ready_for_v3_with_monitoring": true,
  "critical_failures": 0,
  "blocking_failures": []
}
```

Boundary preserved:

- Voice plans delivery.
- Voice must not fabricate TTS execution.
- Voice must not become TTS Router, QC, Strategy or Publisher.

### 4.3 Asset Selection Agent v2.6

Primary goal:

- make visual selection explainable, metadata-only, fallback-honest and confidence-calibrated without changing ranking or selection behavior.

Key hardening delivered:

- asset context governance
- catalog and source governance
- segment visual intent mapping
- visual semantic alignment
- visual truthfulness and mismatch risk
- fallback and safe-default honesty
- diversity and repetition guard
- confidence calibration as trust in asset selection
- asset trace and auditability

Final state:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "ready_for_v3_with_monitoring": true,
  "critical_failures": 0,
  "blocking_failures": []
}
```

Boundary preserved:

- Asset Selection selects from governed metadata/catalog surfaces.
- Asset Selection must not become Strategy, QC, Publisher or pixel-level visual truth authority.

### 4.4 Video QC Agent v2.6

Primary goal:

- make final artifact evaluation explainable, evidence-scored and traceable without changing APPROVE/HOLD/REJECT or publishable semantics.

Key hardening delivered:

- QC input and artifact governance
- confidence and evidence scoring
- decision semantics and severity
- QC trace and auditability

Final state:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "ready_for_v3_with_monitoring": true,
  "critical_failures": 0,
  "blocking_failures": []
}
```

Boundary preserved:

- Video QC evaluates final artifacts.
- Video QC must not repair, publish, rewrite, rerender, resynthesize voice, replace assets or predict performance.

## 5. Wave 2 Master Gate

Canonical artifact:

- `OUT/audit/phase_2_6_wave_2_master_gate/final_verdict.json`

Result:

```json
{
  "audit_type": "PHASE_2_6_WAVE_2_MASTER_GATE",
  "verdict": "GO_WITH_MONITORING",
  "blocks": "16/16 passed",
  "tests": "343 passed",
  "critical_failures": 0,
  "blocking_failures": [],
  "recommendation": "PROCEED_TO_PHASE_2_6_FINAL_MASTER_GATE"
}
```

Wave 2 proved:

- Script output feeds Voice without contract drift
- Script output feeds Asset and QC surfaces where applicable
- Voice remains planning-only and does not fabricate TTS execution
- Asset remains metadata-only and does not become QC or Strategy
- Video QC remains final artifact evaluator
- no output-quality agent overrides Strategy
- no new publishability authority exists outside existing QC semantics
- output traces are reconstructible

## 6. Final Master Gate

Canonical artifact:

- `OUT/audit/phase_2_6_final_master_gate/final_verdict.json`

Result:

```json
{
  "audit_type": "PHASE_2_6_FINAL_MASTER_GATE",
  "verdict": "GO_WITH_MONITORING",
  "release_state": "READY_FOR_V3_WITH_MONITORING",
  "v3_ready_with_monitoring": true,
  "blocks": "16/16 passed",
  "tests": "604 passed",
  "critical_failures": 0,
  "blocking_failures": [],
  "boundary_violations_detected": false,
  "silent_failures_detected": false,
  "fake_confidence_detected": false,
  "non_determinism_detected": false,
  "trace_incomplete": false
}
```

Final interpretation:

- Phase 2.6 is structurally ready for v3 with monitoring.
- Remaining risk is operational maturity, not architecture.
- Core pipeline remains frozen and validated.
- Strategy remains the control layer.
- Publisher remains out of scope and must not be smuggled through QC.

## 7. Residual Monitoring

Residuals are explicit and non-structural.

Wave 1 residual classes:

- Account Health runtime history still short
- Account Health telemetry producer coverage still expanding
- Learning longitudinal production history still short
- Trend runtime history still short
- Trend producer/source coverage still bounded
- controlled scenarios complement but do not replace long-horizon runtime monitoring

Wave 2 residual classes:

- Script provider/runtime history still short
- Script repair metadata still not reported by generator
- Voice TTS trace not available at Voice layer
- Voice audio validation/provider execution history still short
- Asset catalog coverage still expanding
- Asset pixel-level validation outside selection layer
- Video QC runtime history still short
- Video QC product signal calibration still maturing
- Video QC layer attribution evidence still limited
- Video QC media probe coverage environment-dependent

These residuals do not block v3 readiness with monitoring because they are explicit, bounded and tied to runtime maturity.

## 8. Agents Not Directly Optimized In Waves 1 And 2

These agents/surfaces were validated by integration, boundary and pipeline gates, but were not the direct optimization target of Wave 1 or Wave 2:

```json
[
  "Strategy Agent",
  "Experiment Capability",
  "Editor Agent",
  "Publisher / Publish layer",
  "Content Performance Attribution",
  "Saturation / Novelty Engine",
  "Creative Orchestrator"
]
```

Correct reading:

- They were not ignored.
- They were protected from accidental mutation.
- Their integration and boundaries were validated where relevant.
- They remain candidates for future operational governance/maturity work.

## 9. Engineering Outcome

Phase 2.6 converted the system from a functional multi-agent pipeline into an audit-grade governed runtime surface.

Before Phase 2.6:

- agents could function but were not uniformly reconstructible
- confidence and fallback semantics were uneven
- traces were fragmented
- boundary risk was harder to audit

After Phase 2.6:

- all Wave 1 and Wave 2 target agents have explicit gates
- every target agent is ready for v3 with monitoring
- confidence semantics are explicit per agent
- fallback is visible
- degraded/missing evidence is visible
- traces are reconstructible
- Strategy remains control layer
- QC remains artifact evaluator
- Publisher remains out of scope
- core pipeline remains unchanged

## 10. Current Authorized Next Step

The correct next step is not more hidden optimization.

Authorized next state:

```json
{
  "next_authorized_work": "PHASE_3_OPERATIONAL_GOVERNANCE_AND_MATURITY_PLAN",
  "starting_point": "READY_FOR_V3_WITH_MONITORING",
  "must_preserve": [
    "core_pipeline_frozen",
    "strategy_control_layer",
    "qc_not_publisher",
    "fallback_honesty",
    "trace_reconstructibility",
    "boundary_integrity"
  ]
}
```

Recommended Phase 3 operational governance and maturity direction:

Observability and maturity work:

- Publisher / Publish Governance
- Creative Orchestrator execution trace
- Attribution closed-loop maturity
- Experiment governance

Candidate reopen only after evidence:

- Strategy trace and input influence hardening
- Saturation / Novelty governance
- Editor Agent auditability

## 11. Final Statement

Wave 1 and Wave 2 did not make the system perfect.

They made the system:

- governed
- traceable
- confidence-honest
- fallback-honest
- boundary-preserving
- deterministic where required
- structurally ready for v3 with monitoring

That is the correct readiness standard for the next phase.


---

## Source: `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_GATE.md`

# SCRIPT_AGENT_V2_6_EXCELLENCE_GATE

## 1. Purpose

`SCRIPT_AGENT_V2_6_EXCELLENCE_GATE` is the formal validation gate for the Script Agent after the Phase 2.6 excellence-hardening workstreams.

This gate validates Script Agent v2.6 as implemented. It must not mutate runtime behavior to make validation pass.

The gate determines whether Script is:

- runtime-real
- context-governed
- quality-rubric backed
- hook/setup/payoff aware
- anti-cliche and diversity aware
- provider/fallback honest
- confidence-calibrated
- traceable end-to-end
- deterministic under controlled inputs
- boundary-preserving
- free of silent failures

This gate is not a feature and is not a runtime behavior change. It is an audit artifact that can produce `GO`, `GO_WITH_MONITORING`, or `HOLD`.

## 2. Scope

In scope:

- Script Agent runtime service execution
- context governance
- deterministic script quality rubric
- hook strength analysis
- setup progression analysis
- payoff memorability analysis
- diversity and anti-cliche analysis
- provider and fallback honesty
- confidence calibration as trust in script construction
- consolidated `script_trace`
- deterministic replay
- backward-compatible `ScriptAgentResult`
- Strategy, Voice, Asset, QC, Experiment, orchestrator, and core boundary preservation

Out of scope:

- modifying Script runtime logic to pass the gate
- rewriting generated scripts in the gate
- adding providers or changing provider order
- modifying Strategy, Voice, Asset, QC, Experiment, orchestrator, or core pipeline
- adding publishability logic
- predicting performance
- converting Script into Strategy or QC
- converting failures into residual monitoring

## 3. Preconditions

The gate may run only after these Script v2.6 workstreams exist:

- Context Governance Hardening
- Script Quality Rubric
- Hook Strength Hardening
- Setup Progression Hardening
- Payoff Memorability Hardening
- Diversity And Anti-Cliche Hardening
- Provider And Fallback Honesty
- Confidence Calibration
- Trace And Auditability Hardening

Required code surfaces:

- `backend/app/creative/agents/script/models.py`
- `backend/app/creative/agents/script/service.py`
- `backend/app/creative/agents/script/context_governance.py`
- `backend/app/creative/agents/script/quality_rubric.py`
- `backend/app/creative/agents/script/hook_analysis.py`
- `backend/app/creative/agents/script/setup_analysis.py`
- `backend/app/creative/agents/script/payoff_analysis.py`
- `backend/app/creative/agents/script/diversity_analysis.py`
- `backend/app/creative/agents/script/provider_fallback_trace.py`
- `backend/app/creative/agents/script/confidence_calibration.py`
- `backend/app/creative/agents/script/trace_auditability.py`

Required validation command:

`python tests/gates/agents/script/run_script_agent_v2_6_excellence_gate.py`

Required output artifact:

`OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`

## 4. Evaluation Dimensions

`runtime_real`

Means Script executes through `ScriptAgentService`, not a stubbed agent.

Failure if the service cannot execute, valid provider output falls into fallback unexpectedly, or only synthetic result objects are inspected.

`context_governed`

Means upstream context is classified as available, used, ignored, missing, or degraded.

Failure if missing/degraded context is hidden or upstream context is silently promoted into Strategy authority.

`quality_rubric_explicit`

Means deterministic construction components are present with score, level, reason, evidence, and rationale.

Failure if rubric components are missing, non-serializable, or imply QC/publishability authority.

`hook_analysis_explicit`

Means hook presence, strength, genericity, tension, specificity, and unsupported claims are visible.

Failure if generic or unsupported hooks are not detected.

`setup_analysis_explicit`

Means setup progression, hook/payoff connection, repetition, and unsupported context are visible.

Failure if setup repetition or unsupported context is hidden.

`payoff_analysis_explicit`

Means payoff presence, memorability, specificity, genericity, vague motivational language, and hook resolution are visible.

Failure if generic/vague payoff evidence is hidden.

`diversity_anti_cliche_explicit`

Means cliche risk, repetition risk, generic phrases, generic CTA, and current-script-only analysis are visible.

Failure if cliche/repetition risk is hidden or external memory is fabricated.

`provider_fallback_honest`

Means provider used, attempts, failures, repair status, fallback mode, fallback reason, and fallback type are visible.

Failure if fallback is hidden, provider order changes, or missing repair metadata is fabricated.

`confidence_calibrated`

Means confidence measures trust in script construction, varies by evidence state, and is not performance prediction.

Failure if confidence is constant, high under fallback/weak evidence, lacks rationale, or predicts performance.

`traceability_complete`

Means `script_trace` reconstructs why the `ScriptPlan` was emitted.

Failure if required trace sections are missing, reconstructibility is faked, or silent failure indicators are ignored.

`boundary_preserved`

Means Script remains a narrative construction agent and does not become Strategy, Voice, Asset, QC, Experiment, Publisher, or core.

Failure if Script emits hidden constraints, publishability decisions, downstream commands, or ownership drift.

`determinism_where_required`

Means controlled identical input produces stable script output, analysis, confidence, and trace.

Failure if stable output drifts without input changes.

`fallback_honest`

Means fallback remains explicit, bounded, and lower trust than successful provider construction.

Failure if fallback is represented as provider success or high-trust clean construction.

`silent_failures_detected`

Means missing sections, fake confidence, hidden fallback, boundary violations, and non-determinism are detected as blockers.

Failure if critical defects exist while the verdict passes.

## 5. Controlled Scenario Battery

The runner executes controlled scenarios through `ScriptAgentService`.

Controlled generator dependencies are allowed so the gate can create deterministic provider success/failure conditions. The Script Agent service itself must not be stubbed.

Required scenarios:

- `rich_context_strong_script`
- `missing_optional_context`
- `degraded_upstream_context`
- `generic_low_quality_script`
- `unsupported_claim_hook`
- `provider_fallback`
- `determinism_replay`
- `backward_compatibility`

## 6. Checklist

The runner validates:

- runtime execution
- context governance
- quality rubric
- hook analysis
- setup analysis
- payoff analysis
- diversity and anti-cliche analysis
- provider/fallback honesty
- confidence calibration
- trace completeness
- fallback honesty
- boundary preservation
- deterministic replay
- backward compatibility
- silent failure detection

Any failed checklist block becomes a blocking failure.

## 7. Verdict Semantics

`GO`

Allowed only when all critical dimensions pass and no meaningful residual monitoring remains.

`GO_WITH_MONITORING`

Allowed when all critical dimensions pass and remaining issues are explicit, bounded, non-structural, or related to provider/runtime history and long-horizon script quality evidence.

`HOLD`

Required when any critical failure exists, including trace incompleteness, fake confidence, hidden fallback, non-determinism, boundary violation, or silent failure.

The expected likely outcome is `GO_WITH_MONITORING`, but the runner must derive the verdict from evidence.

## 8. Failure Conditions

The gate must return `HOLD` if any of the following occur:

- Script cannot execute through `ScriptAgentService`
- context governance is missing
- quality rubric is incomplete
- hook/setup/payoff analysis is incomplete
- cliche or repetition risk is hidden
- provider fallback is hidden
- repair metadata is fabricated
- confidence is constant or fake
- confidence predicts performance
- fallback receives high confidence
- `script_trace` is incomplete
- deterministic replay fails
- Script crosses into Strategy, Voice, Asset, QC, Experiment, Publisher, or core ownership
- silent failure indicators are present without being classified as blockers

## 9. Output Artifacts

The runner writes:

- `OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/metrics.json`

## 10. Final Criteria

Script Agent v2.6 may pass only if the gate proves:

- runtime execution is real
- context governance is explicit
- quality rubric is deterministic and bounded
- hook/setup/payoff analyses are explicit
- diversity and anti-cliche analysis is honest
- provider and fallback paths are visible
- confidence means trust in script construction
- `script_trace` reconstructs the emitted `ScriptPlan`
- fallback remains explicit and lower trust
- deterministic replay holds
- Script remains within its boundary

Final rule:

> Script Agent is ready for v3 only when it can explain why a `ScriptPlan` was emitted without pretending weak context, fallback, or low-quality construction is stronger than it is.


---

## Source: `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_PLAN.md`

# Script Agent v2.6 Excellence Plan

## 1. Purpose

This document defines the formal Phase 2.6 excellence plan for the Script Agent.

The Script Agent is the first Wave 2 output agent. It consumes upstream context from Strategy, Trend, Learning, Account Health, and Experiment surfaces where available, then produces a bounded script plan for downstream Voice, Asset, Editor, and QC stages.

This is not an implementation artifact.

This plan defines how Script must evolve from a runtime-real structured generation surface into an audit-grade, context-governed, confidence-aware, fallback-honest, traceable narrative construction subsystem.

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

The Script v2.6 work must preserve:

- core pipeline frozen
- Strategy ownership
- Account Health ownership
- Learning ownership
- Trend ownership
- Voice ownership
- Asset ownership
- QC ownership
- Experiment ownership
- Publisher out of scope
- no hidden enforcement
- no provider expansion
- no fake confidence
- no fake quality claims
- no downstream behavior changes without explicit governance

## 3. Current State

The Script Agent is already runtime-real and integrated into the creative pipeline.

Current capabilities include:

- `ScriptAgentInput` with account, niche, topic, account health, Strategy, Trend, Learning, and Experiment context surfaces.
- `ScriptAgentResult` returning a structured `ScriptPlan` and fallback information.
- provider-backed generation through the local script generation service.
- deterministic fallback when provider generation is unavailable or invalid.
- structured narrative fields such as hook, setup, and payoff.
- screen text adaptation after script generation.
- existing payoff and concreteness heuristics in the local script generator path.

Current limitations for Phase 2.6:

- context usage is not yet audit-grade.
- upstream signal influence is not fully explained.
- quality criteria are not explicit as a deterministic rubric.
- hook, setup, payoff, and CTA quality are not traceable as separate quality dimensions.
- fallback and provider path are not sufficiently visible for audit.
- confidence is not yet calibrated as trust in script construction.
- script decisions are not reconstructible from a consolidated trace.

## 4. Objective

Script v2.6 must make script generation more:

- context-governed
- quality-rubric backed
- hook-aware
- setup-aware
- payoff-aware
- anti-cliche and diversity-aware
- provider/fallback honest
- confidence-aware
- traceable end-to-end
- ready for v3 with monitoring

The goal is to improve the reliability, explainability, and auditability of script construction.

The goal is not to make Script a strategic decision layer, QC judge, publisher, trend engine, or performance predictor.

## 5. Scope

In scope:

- Script context intake governance.
- field-level rationale for script construction.
- deterministic script quality rubric.
- hook strength hardening.
- setup progression hardening.
- payoff memorability hardening.
- diversity and anti-cliche hardening.
- provider and fallback honesty.
- confidence calibration for trust in script construction.
- consolidated `script_trace`.
- Script v2.6 excellence gate.

Out of scope:

- core pipeline changes.
- Strategy behavior changes.
- Account Health decision changes.
- Learning policy changes.
- Trend source or confidence changes.
- Voice selection or synthesis changes.
- Asset selection behavior changes.
- QC publishability decisions.
- Publisher work.
- provider expansion.
- uncontrolled prompt experimentation.
- performance prediction.

## 6. Boundary Rules

Script may:

- use Strategy as the controlling creative direction.
- use Trend as advisory context.
- use Learning as bounded historical signal.
- respect Account Health constraints.
- respect Experiment assignment when provided.
- produce a script plan for downstream execution.
- explain how upstream context influenced script fields.

Script must not:

- override Strategy.
- decide publishability.
- decide final content quality.
- decide voice, asset, or edit execution.
- create experiments.
- decide rollout or posting policy.
- infer account health.
- create hidden constraints.
- hide fallback.
- claim confidence without evidence.
- predict performance.

## 7. Required Workstream Order

Script v2.6 must be implemented in bounded workstreams:

1. Context Governance Hardening
2. Script Quality Rubric
3. Hook Strength Hardening
4. Setup Progression Hardening
5. Payoff Memorability Hardening
6. Diversity And Anti-Cliche Hardening
7. Provider And Fallback Honesty
8. Confidence Calibration
9. Trace And Auditability Hardening
10. Script Excellence Gate

Do not implement all workstreams at once.

Each workstream must pass focused validation before the next workstream begins.

## 8. Workstream 1: Context Governance Hardening

### Goal

Make Script context intake explicit, bounded, and auditable.

### Required Behavior

The Script Agent must identify which upstream context was available, used, ignored, missing, or degraded.

Expected context classes:

- strategy_context
- trend_context
- learning_context
- account_health_context
- experiment_context
- topic_context
- niche_context

### Required Output

Additive trace structure:

```json
{
  "context_governance": {
    "available_context": [],
    "used_context": [],
    "ignored_context": [],
    "missing_context": [],
    "degraded_context": [],
    "context_priority": [],
    "policy_respected": true,
    "rationale": []
  }
}
```

### Constraints

- Strategy remains the primary creative control context.
- Trend remains advisory.
- Learning remains bounded historical signal.
- Account Health constraints must remain visible and respected.
- Missing context must not be fabricated.
- Missing optional context must not automatically fail generation.

### Validation

Focused tests must prove that context usage is explicit and no upstream signal is silently promoted into Strategy authority.

## 9. Workstream 2: Script Quality Rubric

### Goal

Create a deterministic rubric that explains script construction quality without becoming QC or publishability logic.

### Required Dimensions

At minimum:

- hook_clarity
- hook_specificity
- setup_coherence
- setup_progression
- payoff_specificity
- payoff_memorability
- cta_fit
- trend_alignment
- strategy_alignment
- repetition_risk
- cliche_risk

### Required Output

Each rubric component should expose:

```json
{
  "score": 0.0,
  "level": "low | medium | high",
  "reason_code": "...",
  "evidence": {},
  "rationale": "..."
}
```

### Constraints

- The rubric must not decide publishability.
- The rubric must not replace QC.
- The rubric must not predict performance.
- The rubric must not produce fake precision.
- Scores must be deterministic and explainable.

### Validation

Tests must prove rubric scores vary across controlled scripts and include rationale for every component.

## 10. Workstream 3: Hook Strength Hardening

### Goal

Improve and audit hook quality as a bounded script construction concern.

### Required Checks

- clarity
- specificity
- immediate tension or payoff promise
- topic fit
- strategy fit
- avoidance of generic hooks
- avoidance of unsupported claims

### Required Trace

```json
{
  "hook_analysis": {
    "hook_present": true,
    "strength_level": "low | medium | high",
    "generic_hook_detected": false,
    "unsupported_claim_detected": false,
    "reason_codes": [],
    "rationale": []
  }
}
```

### Constraints

- Do not create clickbait optimization.
- Do not overrule Strategy.
- Do not make performance claims.
- Do not hide weak hooks.

## 11. Workstream 4: Setup Progression Hardening

### Goal

Ensure setup text progresses from hook to payoff coherently.

### Required Checks

- setup exists.
- setup connects to hook.
- setup prepares payoff.
- setup does not repeat hook without development.
- setup does not introduce unsupported context.
- setup remains compatible with voice and edit execution.

### Required Trace

```json
{
  "setup_analysis": {
    "setup_present": true,
    "progression_level": "low | medium | high",
    "repetition_detected": false,
    "unsupported_context_detected": false,
    "reason_codes": [],
    "rationale": []
  }
}
```

### Constraints

- Do not become Editor.
- Do not change downstream timing behavior.
- Do not create hidden rewrite authority.

## 12. Workstream 5: Payoff Memorability Hardening

### Goal

Make payoff quality explicit, concrete, and auditable.

### Required Checks

- payoff exists.
- payoff is specific.
- payoff resolves or reframes the hook.
- payoff is not generic.
- payoff is not a vague motivational line.
- payoff is compatible with Strategy and topic.

### Required Trace

```json
{
  "payoff_analysis": {
    "payoff_present": true,
    "memorability_level": "low | medium | high",
    "generic_payoff_detected": false,
    "weak_payoff_terms": [],
    "reason_codes": [],
    "rationale": []
  }
}
```

### Constraints

- Do not fabricate facts.
- Do not claim the payoff will perform.
- Do not turn payoff scoring into QC publishability.

## 13. Workstream 6: Diversity And Anti-Cliche Hardening

### Goal

Reduce repeated, generic, or cliche script patterns while preserving deterministic behavior.

### Required Checks

- repeated hook phrases.
- repeated payoff structures.
- overused CTA patterns.
- generic creator advice.
- trend overfitting.
- weak novelty within the allowed Script boundary.

### Required Trace

```json
{
  "diversity_analysis": {
    "cliche_risk_level": "low | medium | high",
    "repetition_risk_level": "low | medium | high",
    "detected_patterns": [],
    "reason_codes": [],
    "rationale": []
  }
}
```

### Constraints

- Do not become Novelty Agent.
- Do not become Learning.
- Do not invent historical memory outside available inputs.
- Do not add randomness to create diversity.

## 14. Workstream 7: Provider And Fallback Honesty

### Goal

Make provider path, provider failure, repair, and fallback behavior explicit.

### Required Checks

- selected provider.
- provider attempts.
- provider failure reasons.
- repair attempts if any.
- fallback usage.
- fallback mode.
- fallback reason.
- whether fallback script is contextual or safe default.

### Required Trace

```json
{
  "provider_fallback_trace": {
    "provider_path": [],
    "provider_used": "...",
    "provider_success": true,
    "repair_applied": false,
    "fallback_used": false,
    "fallback_mode": null,
    "fallback_reason": null,
    "rationale": []
  }
}
```

### Constraints

- Do not hide provider failure.
- Do not treat fallback as provider success.
- Do not assign high confidence to fallback without explicit rationale.
- Do not add providers.
- Do not change provider order unless separately governed.

## 15. Workstream 8: Confidence Calibration

### Goal

Add confidence as a trust signal for script construction.

Confidence must answer:

"How much can the system trust that this script plan was constructed from sufficient context, valid provider output, and acceptable script structure?"

Confidence must not answer:

"How likely is this script to perform?"

### Required Components

- context_completeness
- provider_reliability
- structure_integrity
- rubric_strength
- fallback_penalty
- genericity_penalty
- upstream_alignment

### Required Output

```json
{
  "confidence": 0.0,
  "confidence_level": "low | medium | high",
  "confidence_components": {},
  "confidence_rationale": {},
  "confidence_meaning": "trust_in_script_construction"
}
```

### Rules

- Confidence must be deterministic.
- Confidence must not be constant.
- Fallback must reduce confidence.
- missing context must reduce confidence proportionally.
- generic hook/setup/payoff must reduce confidence.
- high confidence requires strong construction evidence.

## 16. Workstream 9: Trace And Auditability Hardening

### Goal

Create a consolidated `script_trace` that allows an auditor to reconstruct why a script plan was emitted.

### Required Structure

```json
{
  "script_trace": {
    "context_governance": {},
    "quality_rubric": {},
    "hook_analysis": {},
    "setup_analysis": {},
    "payoff_analysis": {},
    "diversity_analysis": {},
    "provider_fallback_trace": {},
    "confidence_calibration": {},
    "final_script_rationale": {},
    "missing_or_degraded_inputs": [],
    "audit_summary": {}
  }
}
```

### Audit Summary

```json
{
  "reconstructible": true,
  "required_sections_present": true,
  "fallback_visible": true,
  "confidence_explained": true,
  "boundary_preserved": true,
  "silent_failure_indicators": []
}
```

### Constraints

- Do not recalculate generation.
- Do not change script output just to improve trace.
- Do not fake reconstructibility.
- Do not remove existing output fields.

## 17. Script Excellence Gate

After all workstreams pass, create:

- `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_GATE.md`
- `tests/gates/agents/script/run_script_agent_v2_6_excellence_gate.py`
- `OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`

Optional supporting artifacts:

- `OUT/audit/script_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/metrics.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/script_examples.json`

The gate must validate:

- runtime_real
- context_governed
- quality_rubric_explicit
- hook_strength_hardened
- setup_progression_hardened
- payoff_memorability_hardened
- diversity_guarded
- provider_fallback_honest
- confidence_calibrated
- traceability_complete
- boundary_preserved
- determinism_where_required
- backward_compatible
- silent_failures_detected false

## 18. Controlled Scenario Battery

The Script v2.6 gate must include scenarios for:

- clean strong context.
- missing Trend context.
- missing Learning context.
- Account Health CAUTION constraints.
- Account Health HOLD boundary representation where applicable.
- weak hook.
- weak setup progression.
- generic payoff.
- cliche script pattern.
- provider success.
- provider failure with fallback.
- deterministic replay.
- backward compatibility.

Each scenario must use the real Script service path or the actual public service entry point.

Do not stub the Script Agent itself.

## 19. Test Strategy

Focused workstream tests must be created as each implementation step begins.

Expected test families:

- `tests/agents/script/test_script_context_governance_unittest.py`
- `tests/agents/script/test_script_quality_rubric_unittest.py`
- `tests/agents/script/test_script_hook_strength_unittest.py`
- `tests/agents/script/test_script_setup_progression_unittest.py`
- `tests/agents/script/test_script_payoff_memorability_unittest.py`
- `tests/agents/script/test_script_diversity_anti_cliche_unittest.py`
- `tests/agents/script/test_script_provider_fallback_honesty_unittest.py`
- `tests/agents/script/test_script_confidence_calibration_unittest.py`
- `tests/agents/script/test_script_trace_auditability_unittest.py`
- `tests/gates/agents/script/run_script_agent_v2_6_excellence_gate.py`

Existing relevant tests must continue to pass, including:

- Script Agent phase tests.
- creative orchestrator tests.
- Strategy integration tests.
- Voice tests where script contract compatibility matters.
- Asset tests where script text compatibility matters.
- QC tests where script plan compatibility matters.

## 20. Final Verdict Schema

The final gate must emit:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "agent": "script",
  "audit_type": "SCRIPT_AGENT_V2_6_EXCELLENCE_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "runtime_real": true,
  "context_governed": true,
  "quality_rubric_explicit": true,
  "hook_strength_hardened": true,
  "setup_progression_hardened": true,
  "payoff_memorability_hardened": true,
  "diversity_guarded": true,
  "provider_fallback_honest": true,
  "confidence_calibrated": true,
  "traceability_complete": true,
  "boundary_preserved": true,
  "determinism_where_required": true,
  "backward_compatible": true,
  "silent_failures_detected": false,
  "blocking_failures": [],
  "residual_monitoring": []
}
```

## 21. Failure Conditions

The Script gate must return `HOLD` if any of the following occur:

- Script output is not runtime-real.
- provider failure is hidden.
- fallback is hidden or treated as provider success.
- confidence is fake or constant.
- high confidence is assigned to weak fallback output without rationale.
- context usage is not traceable.
- Strategy boundary is violated.
- Account Health constraints are ignored.
- Script decides publishability.
- Script becomes QC.
- hook/setup/payoff rationale is missing.
- trace is incomplete.
- deterministic replay fails.
- backward compatibility breaks.
- silent failure is detected.

## 22. Residual Monitoring

Acceptable residual monitoring may include:

- `SCRIPT_RUNTIME_HISTORY_STILL_SHORT`
- `SCRIPT_PROVIDER_RELIABILITY_STILL_MONITORED`
- `SCRIPT_QUALITY_RUBRIC_NEEDS_PRODUCTION_CALIBRATION`

These are acceptable only if:

- they are explicit.
- they are non-structural.
- they do not hide blocking failures.
- they do not affect boundary preservation.

## 23. Exit Criteria

Script v2.6 is complete only when:

- context usage is explicit.
- quality rubric is deterministic.
- hook strength is traceable.
- setup progression is traceable.
- payoff memorability is traceable.
- genericity and cliche risks are visible.
- provider path is visible.
- fallback is honest.
- confidence is calibrated as trust in script construction.
- script trace reconstructs the emitted script plan.
- existing `ScriptAgentResult` compatibility is preserved.
- downstream Voice, Asset, Editor, and QC contracts remain stable.
- Strategy remains the control layer.
- QC remains the final product quality authority.
- core pipeline remains unchanged.
- excellence gate passes.

## 24. Final Position

Script Agent v2.6 exists to make script construction more governed, explainable, and reliable.

It must improve narrative output quality and auditability without becoming Strategy, QC, Publisher, or a performance prediction engine.


---

## Source: `docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_GATE.md`

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


---

## Source: `docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_PLAN.md`

# TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_PLAN

## 1. Executive Summary

`Trend Analysis Agent v2.6` is the third Wave 1 excellence artifact in the Phase 2.6 hardening program, after the approved Learning and Account Health Phase 2.6 gates.

Authoritative upstream gate state:

- `OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/final_verdict.json`

Current consolidated upstream state:

```json
{
  "learning_agent_v2_6": "GO_WITH_MONITORING",
  "account_health_agent_v2_6": "GO_WITH_MONITORING",
  "phase_2_6_partial_master_gate_learning_account_health": "GO_WITH_MONITORING",
  "recommendation": "PROCEED_TO_TREND_ANALYSIS_AGENT_V2_6_PLAN"
}
```

Trend Analysis enters Wave 1 because it is an upstream strategic context provider. Weak trend evidence does not merely reduce style quality. It can distort Strategy, weaken Asset specificity, flatten Script context, and contaminate downstream generation with stale or low-credibility directional priors.

Trend Analysis is not:

- Strategy
- Learning
- Novelty
- QC
- a publisher surface
- a broad scraping platform
- an autonomous external intelligence system

Trend Analysis owns a bounded trend evidence layer. It should provide governed, provenance-aware, freshness-aware, confidence-aware trend context that downstream agents may consume. It must not silently become a strategic brain or an uncontrolled collection system.

Target Trend state after Phase 2.6:

- runtime-real
- evidence-backed
- provenance-rich
- freshness-disciplined
- confidence-aware
- shift-aware
- traceable
- deterministic where required
- bounded in authority
- ready for v3 with monitoring

Canonical principle:

> Trend Analysis must become a stronger governed evidence layer for strategic context without becoming an uncontrolled trend intelligence platform.

## 2. Current State Of Trend Analysis

Trend Analysis is already more mature than a Phase 1 niche-file loader, but it is not yet excellence-grade.

Current proven capabilities:

- it is runtime-real
- it runs before Learning and Strategy in orchestrator flow
- it returns a real `TrendAnalysisResult`
- it emits `trend_profile`, `fallback`, `validation_summary`, and `collector_trace`
- it supports a canonical storage layout with `current`, `history`, `manual_curation`, and `cache`
- it can assemble trend state from multiple source records
- it can validate candidate profiles
- it can score confidence
- it can detect shifts against previous stored state
- it persists current, validated-cache, and history snapshots
- it exposes evidence references in `TrendProfile.evidence`
- it remains deterministic under controlled inputs
- fallback is explicit and traceable
- downstream influence on Strategy and Asset is real

Current governed classification:

```json
{
  "agent": "trend_analysis",
  "runtime_real": true,
  "authority": "bounded_trend_context_provider",
  "current_maturity": "partially_mature",
  "primary_consumers": [
    "Strategy",
    "Asset",
    "Script",
    "Editor"
  ],
  "phase_2_6_target": "evidence_backed_confidence_aware_freshness_disciplined"
}
```

Current residues:

- source governance is still relatively narrow
- manual curation remains a major source surface
- external collection must remain sustainable and bounded
- confidence exists but still needs stronger semantics and stricter gating
- freshness handling exists but can become more explicit and operationally safer
- shift analysis exists but is still limited in meaning and downstream interpretation
- downstream utility is uneven across Strategy, Script, Asset, and Editor
- audit surfaces are useful but not yet consolidated into a dedicated excellence gate
- long-horizon trend evidence remains comparatively short

Trend is not broken. It is implemented, causally active, and already better than a symbolic placeholder. Phase 2.6 exists to harden it before v3.

## 3. Correct Boundary Of Trend Analysis In Phase 2.6

Trend Analysis 2.6 must preserve the runtime governance model:

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

### 3.1 Trend Analysis Owns

Trend Analysis may own:

- trend source intake within approved bounded producers
- source governance and source prioritization
- provenance and evidence reference lineage
- freshness and validity evaluation
- confidence scoring for trend fields
- shift detection against prior trend state
- trend profile assembly
- explicit fallback behavior
- trend-specific traceability
- bounded advisory context for downstream consumers

### 3.2 Trend Analysis Does Not Own

Trend Analysis must not own:

- Strategy decisions
- Learning policy
- Novelty pressure
- publishability
- QC authority
- experiment assignment
- rollout optimization
- topic-level performance learning
- autonomous scraping expansion
- unsupported regional claims
- external automation beyond sustainable collection boundaries

Boundary rule:

> Trend Analysis may influence downstream direction, but Strategy remains the control layer.

Corollary:

> Trend Analysis should supply better governed context, not hidden strategic enforcement.

## 4. Why Trend Analysis Must Be Hardened Before v3

v3 should not scale trend context that is only partially governed.

Trend Analysis matters because it sits upstream of Strategy and Asset. If Trend emits stale or weakly justified context, downstream agents may behave consistently but incorrectly. That is a governance problem, not just a style problem.

Hardening Trend before v3 is necessary because:

- Strategy already consumes trend pacing and hook families causally
- Asset already consumes trend pacing and visual style materially
- Script receives trend context in prompt assembly
- Editor receives trend context indirectly through style surfaces
- stale trend evidence can create false strategic confidence
- weak provenance can make trend claims look stronger than they are
- source mix can become uneven without explicit governance
- shift detection without disciplined semantics can create ornamental intelligence
- v3 must not depend on unsupported live-trend claims or uncontrolled collection

The risk is not only that Trend is too weak. The larger risk is that it appears mature enough to trust while still carrying avoidable uncertainty around source quality, freshness, and shift meaning.

## 5. Current Deficits To Fix

Phase 2.6 must address the following Trend deficits.

### 5.1 Source Governance

Trend now supports multiple sources, but source policy is still comparatively narrow.

Deficit:

- source intake exists, but source governance should be more explicit, bounded, and auditable

Required fix:

- define allowed source classes, allowed producer paths, source priority, and source fallback semantics more clearly

### 5.2 Evidence Provenance

Trend evidence references exist, but provenance can become stronger.

Deficit:

- an auditor can see evidence items, but source-quality semantics and field-level rationale are still limited

Required fix:

- make provenance explain which fields came from which source mix and why they were considered usable

### 5.3 Freshness And Validity Discipline

Trend already validates freshness windows, but stale behavior should become more explicit.

Deficit:

- stale source handling exists, but stale impact on confidence and downstream safety can be clearer

Required fix:

- make stale, expiring, cached, and fallback conditions more reconstructible and more conservative when appropriate

### 5.4 Confidence Calibration

Trend confidence exists, but it still needs stronger semantics.

Deficit:

- confidence can be present without enough explicit relation to source quality, source mix, sample size, freshness, and validation outcome

Required fix:

- calibrate confidence as a trust signal for trend context, not as a decorative score

### 5.5 Shift Analysis Semantics

Trend already detects changes, but the meaning of change is still shallow.

Deficit:

- not every field change should carry the same operational meaning

Required fix:

- clarify what counts as meaningful trend shift, what is minor variation, and how this should appear in trace

### 5.6 Downstream Utility Clarification

Trend has real downstream effect, but utility is uneven.

Deficit:

- some trend fields are strongly consumed, others remain weak or symbolic

Required fix:

- clarify which fields are expected to materially influence downstream agents and which are trace-only or advisory

### 5.7 Audit Surface Coherence

Trend trace exists, but excellence-grade reconstruction is still missing.

Deficit:

- `validation_summary`, `collector_trace`, and `TrendProfile` together are useful but not yet consolidated into a stronger audit-grade surface

Required fix:

- make trend artifacts easier to reconstruct end-to-end from source intake to downstream-safe output

### 5.8 Longitudinal Maturity

Trend history exists, but runtime maturity remains short.

Deficit:

- controlled and manually curated evidence still outweigh broad real longitudinal runtime variability

Required fix:

- preserve this residue honestly and harden the subsystem without pretending it already has long-horizon maturity

## 6. Phase 2.6 Objectives For Trend Analysis

Trend Analysis 2.6 objectives:

- improve source governance
- improve evidence provenance
- improve freshness and validity discipline
- improve confidence calibration
- improve shift analysis semantics
- improve stale evidence behavior
- improve manual curation discipline
- improve downstream utility clarity
- improve trace and auditability
- preserve deterministic behavior
- preserve fallback honesty
- preserve Strategy ownership
- prepare Trend for v3 with monitoring

Trend Analysis 2.6 must not optimize for breadth. It must optimize for credibility, traceability, and bounded strategic usefulness.

Target state:

```json
{
  "trend_analysis_v2_6": {
    "runtime_real": true,
    "source_governed": true,
    "evidence_backed": true,
    "freshness_disciplined": true,
    "confidence_calibrated": true,
    "shift_analysis_meaningful": true,
    "traceability_complete": true,
    "boundary_preserved": true
  }
}
```

## 7. Workstreams Of Trend Analysis 2.6

Trend Analysis 2.6 must be implemented in bounded workstreams.

### 7.1 Source Governance Hardening

Objective:

- make Trend source intake more explicit, bounded, and policy-driven

Must improve:

- allowed source classes
- source priority rules
- cache use semantics
- collector enablement rules
- regional input discipline
- manual curation acceptance rules

Rules:

- no uncontrolled scraping
- no hidden producers
- no fake regionalization
- no broad external automation
- no source accepted without explicit type and validity semantics

Expected result:

- Trend inputs become more governable and easier to audit.

### 7.2 Evidence Lineage And Provenance Hardening

Objective:

- make trend evidence lineage more reconstructible

Must improve:

- source-level evidence references
- field-to-source explanation
- sample-size visibility
- source metadata discipline
- why a source was usable or ignored

Rules:

- no fake evidence
- no field lineage without a producer
- no provenance inflation from weak or empty sources

Expected result:

- an auditor can understand where trend context came from and what supported it.

### 7.3 Freshness And Validity Hardening

Objective:

- make stale and expiring trend evidence safer and clearer

Must improve:

- updated-at handling
- valid-until semantics
- stale source downgrade
- cache fallback explanation
- safe default fallback clarity

Rules:

- stale evidence must not silently behave like fresh evidence
- invalid evidence must not become strong context
- freshness must be visible in trace and confidence

Expected result:

- Trend becomes safer under stale or partially expired evidence.

### 7.4 Confidence Calibration Hardening

Objective:

- make Trend confidence evidence-backed and bounded

Confidence should consider:

- source quality
- source mix
- sample size
- freshness state
- validation outcome
- fallback path
- evidence richness

Rules:

- confidence must not be decorative
- fallback must not carry strong confidence
- weak legacy profiles must not look equivalent to validated source assemblies

Expected result:

- downstream consumers can distinguish trusted trend context from thin or stale trend context.

### 7.5 Shift Analysis Hardening

Objective:

- make trend shift detection more meaningful and less ornamental

Must improve:

- significance semantics
- change classification
- baseline comparison rationale
- which fields matter operationally
- how shifts appear in trace

Rules:

- not every field difference is a strong shift
- shift detection must not become pseudo-forecasting
- change semantics must remain deterministic and bounded

Expected result:

- shift analysis becomes operationally useful rather than merely descriptive.

### 7.6 Downstream Utility Clarification

Objective:

- clarify and strengthen how Trend should be consumed downstream without changing ownership

Must improve:

- field usefulness semantics
- Strategy-facing trend utility
- Asset-facing trend utility
- low-utility field handling
- advisory versus materially consumed trend fields

Rules:

- Trend must not become hidden Strategy logic
- weak fields must not be overstated as causal
- unused fields should either gain clear purpose or remain explicitly low-authority

Expected result:

- Trend outputs become more interpretable and more consistently useful downstream.

### 7.7 Trace And Auditability Hardening

Objective:

- make Trend outputs reconstructible from source intake to final emitted `TrendProfile`

Must improve:

- collector trace coherence
- validation rationale
- confidence rationale
- freshness rationale
- fallback rationale
- shift rationale

Rules:

- no fake trace fields
- no trace-only intelligence with no producer logic
- no hidden downgrade paths

Expected result:

- Trend Analysis becomes audit-grade enough for a dedicated excellence gate.

## 8. Proposed Contract Evolution

Trend Analysis 2.6 may evolve contracts only in additive, backward-compatible ways.

The public surface must remain centered on:

- `TrendAnalysisInput`
- `TrendAnalysisResult`
- `TrendProfile`
- explicit fallback

### 8.1 Proposed `TrendAnalysisInput` Additions

Possible additive fields:

```json
{
  "account_id": "",
  "region": "US",
  "allow_cached": true,
  "force_refresh": false,
  "current_time": "",
  "source_policy": {},
  "freshness_policy": {}
}
```

Purpose:

- make runtime policy around source use and freshness more explicit without opening uncontrolled collection scope

### 8.2 Proposed `TrendAnalysisResult` Additions

Possible additive fields:

```json
{
  "validation_summary": {},
  "collector_trace": {},
  "confidence_summary": {},
  "shift_summary": {},
  "provenance_summary": {},
  "trend_trace": {}
}
```

Purpose:

- consolidate trend reasoning into a stronger audit surface

### 8.3 Proposed `TrendProfile` Additions

Possible additive fields:

```json
{
  "trend_source": "",
  "confidence_scores": {},
  "updated_at": "",
  "valid_until": "",
  "sample_size": 0,
  "evidence": [],
  "trend_version": "2.0",
  "collector_version": ""
}
```

Purpose:

- preserve evidence-backed trend context in runtime contracts

### 8.4 Contract Rules

Contract evolution must satisfy:

- backward compatibility where practical
- deterministic serialization
- no required field without a real producer
- no fake provenance
- no unsupported live-trend semantics
- no field implying ownership outside Trend Analysis
- no ornamental schema growth

## 9. Validation Strategy For Trend Analysis 2.6

Trend Analysis 2.6 must be validated through layered proof.

Required validation layers:

- unit validation
- controlled source-mix battery
- freshness and stale-evidence scenarios
- confidence scenarios
- shift-analysis scenarios
- downstream Strategy and Asset integration checks
- deterministic replay checks
- audit trace checks
- governance boundary checks

### 9.1 Unit Validation

Must prove:

- source loading remains deterministic
- source assembly remains deterministic
- fallback remains explicit
- confidence scoring is stable
- stale and invalid sources are downgraded correctly

### 9.2 Controlled Source Battery

Must include:

- manual curation only
- creative center only
- hybrid source assembly
- cache fallback
- history fallback
- safe default fallback
- stale source rejection

### 9.3 Confidence Validation

Must prove:

- high-quality fresh source mix can yield stronger confidence
- stale or thin source surfaces reduce confidence
- fallback stays low-confidence
- legacy manual file paths do not masquerade as high-confidence validated profiles

### 9.4 Shift Analysis Validation

Must prove:

- meaningful field changes are visible
- no-change scenarios stay stable
- weak changes are not overstated
- shift summary is deterministic

### 9.5 Downstream Integration Validation

Must prove:

- Strategy consumes trend context materially where designed
- Asset consumes trend context materially where designed
- Trend does not override Health
- Trend does not replace Strategy
- fallback trend context remains safe and bounded downstream

### 9.6 Determinism Checks

Must prove:

- same source inputs yield same `TrendProfile`
- same `TrendProfile` yields same downstream Strategy response where applicable
- replay does not create unexplained drift

### 9.7 Audit Trace Checks

Must prove:

- source lineage is reconstructible
- freshness state is visible
- confidence rationale is visible
- fallback path is visible
- shift rationale is visible

Invalid improvements:

- fake confidence
- fake provenance
- unsupported regional claims
- uncontrolled collection expansion
- hidden fallback
- Strategy ownership drift
- ornamental shift intelligence

## 10. Trend Analysis Excellence Gate

At the end of Trend Analysis 2.6, a dedicated gate must be generated:

`OUT/audit/trend_analysis_agent_v2_6_excellence_gate/final_verdict.json`

Required documentation:

`docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_GATE.md`

Required runner:

`tests/gates/agents/trend_analysis/run_trend_analysis_agent_v2_6_excellence_gate.py`

The gate must prove at minimum:

- `runtime_real = true`
- `source_governed = true`
- `evidence_backed = true`
- `freshness_disciplined = true`
- `confidence_calibrated = true`
- `shift_analysis_meaningful = true`
- `fallback_honest = true`
- `traceability_complete = true`
- `boundary_preserved = true`
- `determinism_where_required = true`
- `silent_failures_detected = false`

Suggested final verdict schema:

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
  "blocking_failures": [],
  "residual_monitoring": []
}
```

Verdict semantics:

- `GO`: all critical dimensions pass and no meaningful Trend-specific residuals remain
- `GO_WITH_MONITORING`: all critical dimensions pass and remaining residues are explicit, bounded, and tied to evidence horizon or producer coverage
- `HOLD`: any critical dimension fails, provenance is weak or fake, freshness behavior is unsafe, boundary is violated, or fallback is hidden

## 11. What Trend Analysis 2.6 Must Not Do

Trend Analysis 2.6 must not:

- become Strategy
- become Learning
- become Novelty
- become QC
- decide publishability
- decide experiment assignment
- become an uncontrolled scraping platform
- make unsupported live trend claims
- fabricate source quality
- fabricate provenance
- fabricate regional confidence
- hide stale evidence
- hide fallback
- use fake confidence
- create hidden strategic enforcement
- mutate the core pipeline
- expand externally beyond sustainable bounded collection

Forbidden failure modes:

- stale trend context treated as fresh strategic truth
- low-quality source mix presented as strong evidence
- fallback trend context presented as validated trend intelligence
- shift analysis overstated as real trend movement without support
- Trend silently becoming a de facto Strategy surface

## 12. Exit Criteria

Trend Analysis 2.6 is complete only when:

- source governance is explicit
- evidence provenance is visible
- freshness handling is disciplined
- confidence is calibrated
- shift analysis is meaningful and bounded
- stale evidence behavior is safe
- fallback remains explicit
- downstream utility is clearer
- trace reconstructs source-to-profile formation
- deterministic replay remains valid
- Strategy ownership remains preserved
- Health authority remains preserved
- no uncontrolled collection expansion occurs
- the Trend Analysis excellence gate passes

Minimum accepted closure state:

```json
{
  "trend_analysis_agent_v2_6": {
    "runtime_real": true,
    "source_governed": true,
    "evidence_backed": true,
    "freshness_disciplined": true,
    "confidence_calibrated": true,
    "shift_analysis_meaningful": true,
    "boundary_preserved": true,
    "excellence_gate_passed": true
  }
}
```

## 13. Final Position

Trend Analysis 2.6 exists to convert the current Trend subsystem from a valid but only partially governed context provider into a more credible, provenance-aware, confidence-aware, freshness-disciplined evidence layer.

It must improve downstream strategic context without becoming downstream strategy.

It must improve source quality without inventing fake intelligence.

It must improve confidence without overstating what the runtime truly knows.

It must strengthen trend evidence while preserving governance boundaries and operational sustainability.


---

## Source: `docs/runtime/phase-2-6/agents/video-qc/VIDEO_QC_AGENT_V2_6_EXCELLENCE_GATE.md`

# VIDEO_QC_AGENT_V2_6_EXCELLENCE_GATE

## 1. Purpose

`VIDEO_QC_AGENT_V2_6_EXCELLENCE_GATE` is the formal validation gate for the Video QC Agent after the Phase 2.6 output-excellence hardening workstreams.

This gate validates Video QC v2.6 as implemented. It must not mutate runtime behavior to make validation pass.

The gate determines whether Video QC is:

- runtime-real
- input and artifact governed
- evidence-scoring explicit
- confidence-calibrated as trust in the QC decision
- decision-semantics and severity explicit
- traceable end-to-end through `qc_trace`
- deterministic under controlled inputs
- boundary-preserving
- free of silent failures

This gate is an audit artifact, not a feature. It can produce `GO`, `GO_WITH_MONITORING`, or `HOLD`.

## 2. Scope

In scope:

- `VideoQcAgentService` execution
- `APPROVE / HOLD / REJECT` semantics
- `publishable` semantics
- `qc_input_governance`
- `qc_evidence_scoring`
- `confidence_calibration`
- `decision_semantics`
- `qc_trace`
- missing/degraded/ignored input visibility
- metadata fallback and media-probe environment visibility
- orchestrator QC governance preservation
- Strategy/core boundary preservation
- deterministic replay
- backward-compatible `VideoQcResult`

Out of scope:

- changing QC decision logic
- changing thresholds or score math
- changing `publishable`
- changing product signals
- changing Strategy
- changing the orchestrator
- changing the core pipeline
- adding Publisher behavior
- adding repair, rerender, rewrite, asset replacement, or resynthesis
- adding performance prediction
- adding ML/audio/video pixel inspection

## 3. Preconditions

Required workstreams:

- QC Input And Artifact Governance
- Confidence And Evidence Scoring Hardening
- Decision Semantics And Severity Hardening
- Trace And Auditability Hardening

Required code surfaces:

- `backend/app/creative/agents/video_qc/models.py`
- `backend/app/creative/agents/video_qc/service.py`
- `backend/app/creative/agents/video_qc/input_governance.py`
- `backend/app/creative/agents/video_qc/confidence_evidence.py`
- `backend/app/creative/agents/video_qc/decision_semantics.py`
- `backend/app/creative/agents/video_qc/trace_auditability.py`

Required validation command:

`python tests/gates/agents/video_qc/run_video_qc_agent_v2_6_excellence_gate.py`

Required output artifact:

`OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json`

## 4. Evaluation Dimensions

`runtime_real`

Means Video QC executes through `VideoQcAgentService`, not fabricated result objects.

Failure if service execution is skipped, result payloads are fabricated, or exceptions are hidden as success.

`input_governed`

Means input availability, usage, missing/degraded/ignored state, and environment dependency are explicit.

Failure if missing metadata, missing artifacts, missing traces, or metadata fallback are hidden.

`evidence_scoring_complete`

Means existing score evidence and failure categories are visible without changing score math.

Failure if scores lack evidence rationale, failure categories are missing, or product evidence is treated as performance prediction.

`confidence_honest`

Means confidence measures `trust_in_qc_decision`, varies across scenarios, and drops under missing/fallback/ambiguous evidence.

Failure if confidence is constant, high under metadata fallback or borderline `HOLD`, lacks rationale, or claims performance prediction.

`decision_semantics_explicit`

Means `APPROVE / HOLD / REJECT`, `blocker`, `warning`, `monitorable`, severity, and publishability rationale are explicit.

Failure if hard failures are not blockers, soft failures are treated as blockers, `HOLD` becomes publishable, or `REJECT` becomes publishable.

`qc_trace_reconstructible`

Means `qc_trace` consolidates input governance, evidence scoring, confidence, decision semantics, final rationale, missing/degraded inputs, and audit summary.

Failure if required sections are missing, reconstructibility is faked, confidence is inconsistent, or decision trace contradicts the result.

`approve_hold_reject_semantics_preserved`

Means the current status behavior remains stable for clean approve, borderline hold, technical reject, perceptual reject, and product-veto reject.

Failure if any controlled scenario returns an unexpected status.

`publishability_semantics_preserved`

Means `APPROVE` may be publishable, while `HOLD` and `REJECT` remain non-publishable.

Failure if `HOLD` or `REJECT` is publishable, or clean `APPROVE` is non-publishable without an explicit existing reason.

`orchestrator_qc_governance_preserved`

Means existing orchestrator tests still pass and downstream publish/non-publish paths remain governed by QC status.

Failure if orchestrator phase2 tests fail or publish behavior is changed by this gate.

`boundary_preserved`

Means Video QC remains final artifact evaluator and does not become Strategy, Publisher, renderer, editor, Script, Voice, or Asset.

Failure if QC emits Strategy commands, publishes, repairs, rerenders, rewrites, resynthesizes, replaces assets, or predicts performance.

`determinism_where_required`

Means identical controlled inputs produce stable status, publishable, confidence, evidence scoring, decision semantics, and `qc_trace`.

Failure if stable fields drift without input changes.

`silent_failures_detected`

Means missing trace sections, hidden fallback, fake confidence, hidden degraded input, publishability inconsistency, and boundary violations are blockers.

Failure if any critical defect is present while the verdict passes.

## 5. Controlled Scenario Battery

The runner executes controlled scenarios through `VideoQcAgentService`.

Required scenarios:

- `clean_approve`
- `borderline_hold`
- `missing_metadata_reject`
- `missing_video_reject`
- `missing_audio_reject`
- `invalid_subtitle_cues_reject`
- `broken_glyph_reject`
- `payoff_too_dark_reject`
- `product_veto_reject`
- `metadata_fallback_visible`
- `missing_optional_traces_visible`
- `determinism_replay`
- `backward_compatibility`

Controlled media-probe subclasses may be used only to make `ffprobe` environment paths deterministic. They must still execute the real `VideoQcAgentService.evaluate` path and must not fabricate final `VideoQcResult` objects.

## 6. Checklist

The runner validates:

- required files exist
- service execution is real
- required public fields exist
- `qc_input_governance` is complete
- `qc_evidence_scoring` is complete
- confidence is calibrated and non-constant
- confidence has correct meaning
- metadata fallback lowers confidence
- `HOLD` is not high confidence
- reason codes are classified by category and disposition
- blockers/warnings/monitorables are explicit
- `qc_trace` required sections are present
- `qc_trace.audit_summary.reconstructible` is honest
- `decision_trace` remains backward-compatible and includes additive audit sections
- `publishable` is consistent with status
- orchestrator, Strategy, and pipeline tests pass
- no forbidden performance-prediction keys appear
- no silent failure indicators are present in passing scenarios

Any failed critical checklist item becomes a blocking failure.

## 7. Verdict Semantics

`HOLD`

Required if any critical failure, blocking failure, fake confidence, silent failure, boundary violation, non-determinism, missing trace section, publishability inconsistency, orchestrator regression, Strategy/core regression, or performance-prediction field is detected.

`GO_WITH_MONITORING`

Allowed when all critical checks pass and remaining residues are explicit, bounded, and non-structural.

Expected acceptable residuals:

- `VIDEO_QC_RUNTIME_HISTORY_STILL_SHORT`
- `VIDEO_QC_PRODUCT_SIGNAL_CALIBRATION_STILL_MATURING`
- `VIDEO_QC_MEDIA_PROBE_COVERAGE_ENVIRONMENT_DEPENDENT`
- `VIDEO_QC_LAYER_ATTRIBUTION_EVIDENCE_STILL_LIMITED`

`GO`

Allowed only if all checks pass and no meaningful residual monitoring remains.

## 8. Failure Conditions

Critical failures include:

- service cannot execute
- status semantics regress
- `publishable` semantics regress
- confidence is fake or constant
- confidence is high under metadata fallback or ambiguous `HOLD`
- score evidence lacks rationale
- reason codes lack semantic classification
- `qc_trace` is missing or not reconstructible
- missing/degraded input is hidden
- metadata fallback is hidden
- decision trace contradicts final result
- orchestrator/Strategy/core tests fail
- QC creates publishability logic beyond existing behavior
- QC predicts performance
- QC mutates upstream outputs
- silent failure indicators are present

## 9. Output Artifacts

The runner writes:

- `OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/metrics.json`

## 10. Final Criteria

Video QC v2.6 passes this gate only if:

- `APPROVE / HOLD / REJECT` are preserved
- `publishable` is preserved
- confidence is honest and evidence-backed
- evidence scoring is complete enough to audit emitted scores
- severity semantics are correct
- `qc_trace` reconstructs why the result was emitted
- missing/degraded/fallback evidence is visible
- no Strategy/orchestrator/core behavior changes occur
- no new publishability authority is created
- no performance prediction is introduced
- no silent failures are detected

Final principle:

Video QC does not decide better in this gate. It proves whether it explains its existing decisions well enough to deserve release.


---

## Source: `docs/runtime/phase-2-6/agents/video-qc/VIDEO_QC_AGENT_V2_6_EXCELLENCE_PLAN.md`

# Video QC Agent v2.6 Excellence Plan

## 1. Purpose

This document defines the formal Phase 2.6 excellence plan for the Video QC Agent.

The Video QC Agent is the fourth Wave 2 output agent. It consumes rendered video, audio, metadata, script text, TTS trace, visual trace, and edit trace where available, then emits the final product-quality decision used by the orchestrator.

This is not an implementation artifact.

This plan defines how Video QC must evolve from a functional post-render validator into an audit-grade, evidence-governed, confidence-aware, product-signal-explicit final quality authority.

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

Video QC v2.6 work must preserve:

- frozen core pipeline
- current orchestrator QC governance semantics
- Strategy ownership over creative control
- Script ownership over narrative text
- Voice ownership over voice planning
- Asset Selection ownership over visual selection
- Trend ownership over context
- Account Health upstream `SAFE / CAUTION / HOLD` authority
- Learning bounded pressure
- Experiment ownership
- Publisher out of scope
- no hidden publish behavior
- no repair or regeneration loop
- no provider expansion
- no fake confidence
- no fake product evidence
- no hidden fallback
- no downstream behavior changes without explicit governance

## 3. Current State

The Video QC subsystem is runtime-real and already integrated into the creative orchestrator.

Current capabilities include:

- `VideoQcInput` carries `render_job_id`, video path, audio path, metadata path, script text, `tts_trace`, `visual_trace`, and `edit_trace`.
- `VideoQcDecision` supports `APPROVE`, `HOLD`, and `REJECT`.
- `VideoQcDecision` exposes `publishable`, `hard_failures`, `soft_failures`, `product_vetoes`, `score_summary`, `product_signals`, `decision_trace`, and `checked_at`.
- `VideoQcResult` exposes `decision`, `status`, `reasons`, `checked_at`, `publishable`, and `details`.
- `VideoQcAgentService` evaluates final artifacts through the real service path.
- hard technical failures include missing render job id, missing video, missing audio, missing metadata, invalid subtitle cues, broken glyphs, payoff darkness, invalid resolution, and missing audio stream.
- product signals include hook quality, payoff quality, publishability signal, setup luma state, component quality scores, and overall score.
- `HOLD` is already represented for borderline product-quality conditions.
- the orchestrator applies QC governance after render: `APPROVE` finalizes publish state, while `HOLD` and `REJECT` mark output non-publishable and remove publish manifest from the returned pipeline output.
- QC emits creative events through the orchestrator.

Current limitations for Phase 2.6:

- input and artifact observability is not yet audit-grade.
- technical checks have reason codes but not full severity/evidence rationale.
- product signals are computed but not fully explained.
- `decision_trace` is shallow and not reconstructible enough.
- layer attribution is implicit.
- environment fallback, such as `ffprobe` absence and metadata fallback, is not clearly separated from full media probing.
- confidence is not calibrated as trust in the QC decision.
- missing traces from Script, Voice, Asset, and Editor are not consistently exposed as limited evidence.
- no consolidated `qc_trace` exists.

## 4. Objective

Video QC v2.6 must make final output validation more:

- input-governed
- artifact-evidence aware
- technical-check explicit
- product-signal explicit
- decision-semantics clear
- severity-aware
- layer-attributed when evidence supports it
- fallback/environment honest
- confidence-calibrated
- traceable end-to-end
- ready for v3 with monitoring

The goal is to improve reliability, explainability, and auditability of final product-quality decisions.

The goal is not to make QC a repair engine, Publisher, Strategy layer, renderer, editor, model-based critic, or performance predictor.

## 5. Scope

In scope:

- QC input and artifact governance.
- artifact presence and metadata evidence trace.
- technical validation rationale and severity.
- bounded product signal rationale.
- `APPROVE / HOLD / REJECT` decision semantics.
- publishability flag rationale.
- layer attribution to Script, Voice, Asset, Editor, Render, Pipeline, or Environment where evidence supports it.
- fallback and environment honesty.
- confidence calibration for trust in QC decision.
- consolidated `qc_trace`.
- Video QC v2.6 excellence gate.

Out of scope:

- core pipeline changes.
- Strategy behavior changes.
- Script behavior changes.
- Voice behavior changes.
- Asset Selection behavior changes.
- Trend behavior changes.
- Account Health behavior changes.
- Experiment behavior changes.
- Publisher implementation.
- changing current orchestrator QC governance semantics.
- rewriting script.
- resynthesizing voice.
- selecting replacement assets.
- re-editing video.
- rerendering video.
- adding computer vision, image ML, audio ML, or performance prediction.
- introducing subjective taste claims without evidence.

## 6. Boundary Rules

Video QC may:

- inspect final rendered artifacts.
- inspect metadata emitted by the pipeline.
- inspect supplied `tts_trace`, `visual_trace`, and `edit_trace`.
- compute deterministic technical and product-signal checks.
- issue `APPROVE`, `HOLD`, or `REJECT`.
- declare `publishable` based on QC status and product signals.
- explain why output is not publishable.
- attribute findings to layers when evidence is available.
- expose confidence as trust in the QC decision.

Video QC must not:

- rewrite Script.
- regenerate Voice.
- replace Assets.
- modify EditPlan.
- rerender content.
- execute publishing.
- implement Publisher.
- override Strategy.
- override Account Health.
- create Learning policy.
- fabricate traces.
- fabricate ffprobe/media evidence.
- treat metadata fallback as full media inspection.
- claim human-level visual or audio judgment without real evidence.
- predict content performance.

## 7. Required Workstream Order

Video QC v2.6 must be implemented in bounded workstreams:

1. QC Input And Artifact Governance
2. Technical Validation Rationale Hardening
3. Product Signal Rationale Hardening
4. Decision Semantics And Severity Hardening
5. Layer Attribution Hardening
6. Fallback And Environment Honesty
7. Confidence Calibration
8. Trace And Auditability Hardening
9. Video QC Excellence Gate

Do not implement all workstreams at once.

Each workstream must pass focused validation before the next workstream begins.

## 8. Workstream 1: QC Input And Artifact Governance

### Goal

Make QC input intake explicit, bounded, and auditable.

### Required Behavior

Video QC must identify which input and artifact classes are:

- available
- used
- missing
- degraded
- ignored
- environment-dependent

Expected input classes:

- render_job_id
- video_artifact
- audio_artifact
- metadata_artifact
- script_text
- tts_trace
- visual_trace
- edit_trace
- media_probe_capability
- metadata_fallback_probe

### Required Output

Additive structure:

```json
{
  "qc_input_governance": {
    "governance_version": "qc_input_governance_v2_6",
    "available_inputs": [],
    "used_inputs": [],
    "missing_inputs": [],
    "degraded_inputs": [],
    "ignored_inputs": [],
    "input_priority": [],
    "artifact_summary": {},
    "environment_summary": {},
    "policy_respected": true,
    "boundary_statement": "Video QC evaluates final artifacts only; it does not repair or publish.",
    "rationale": []
  }
}
```

### Constraints

- Do not change QC decision logic in this workstream.
- Do not change artifact probing behavior.
- Do not fabricate missing paths or trace data.
- Do not hide missing `tts_trace`, `visual_trace`, or `edit_trace`.

### Validation

Focused tests must prove input availability, missing inputs, degraded inputs, environment fallback, and serialization are explicit.

## 9. Workstream 2: Technical Validation Rationale Hardening

### Goal

Make each technical QC check explicit with severity, evidence, and rationale.

### Required Checks

Existing checks must be represented without changing behavior:

- render job id presence
- video artifact presence and non-empty size
- audio artifact presence and non-empty size
- metadata presence
- render duration minimum
- subtitle cue count validity
- subtitle cue text validity
- broken glyph detection
- payoff darkness via metadata luma proxy
- resolution validation
- audio stream validation
- media probe mode

### Required Output

Additive structure:

```json
{
  "technical_validation": {
    "validation_version": "qc_technical_validation_v2_6",
    "checks": {
      "video_artifact": {
        "passed": true,
        "severity": "none | low | medium | high | critical",
        "reason_code": "...",
        "evidence": {},
        "rationale": []
      }
    },
    "hard_failures": [],
    "technical_valid": true,
    "rationale": []
  }
}
```

### Constraints

- Do not add hidden thresholds.
- Do not weaken existing hard failures.
- Do not convert product weaknesses into technical failures without evidence.
- Do not treat metadata fallback as equivalent to full media probe.

### Validation

Focused tests must cover clean artifacts, missing metadata, missing audio, bad resolution, subtitle errors, broken glyphs, payoff darkness, and media probe fallback.

## 10. Workstream 3: Product Signal Rationale Hardening

### Goal

Make existing product-signal scoring explainable and bounded.

### Required Signals

Existing product signals must be explained:

- script_quality
- voice_quality
- asset_quality
- edit_quality
- hook_quality
- payoff_quality
- product_quality
- publishability_signal
- overall_score
- setup_luma_ok

### Required Output

Additive structure:

```json
{
  "product_signal_analysis": {
    "analysis_version": "qc_product_signal_v2_6",
    "signals": {
      "hook_quality": {
        "score": 0.0,
        "level": "low | medium | high",
        "evidence": {},
        "reason_codes": [],
        "rationale": []
      }
    },
    "score_summary": {},
    "product_signals": {},
    "boundedness_statement": "Product signals are deterministic proxies, not performance predictions.",
    "rationale": []
  }
}
```

### Constraints

- Do not claim human-level taste.
- Do not use ML.
- Do not predict performance.
- Do not change existing score math in this workstream.
- Do not replace Script, Voice, Asset, or Editor judgments.

### Validation

Focused tests must prove product-signal rationale exists, varies across controlled cases, and remains deterministic.

## 11. Workstream 4: Decision Semantics And Severity Hardening

### Goal

Make `APPROVE / HOLD / REJECT`, `publishable`, hard failures, soft failures, and product vetoes fully auditable.

### Required Semantics

`APPROVE`:

- no hard failures
- no product vetoes
- no soft failures
- `publishable = true`
- final output is eligible for current orchestrator publish-finalization path

`HOLD`:

- no hard technical failure
- one or more bounded soft failures
- product quality is borderline or requires review
- `publishable = false`
- current orchestrator non-publishable path remains preserved

`REJECT`:

- hard technical failure or product veto exists
- output is invalid or below minimum product threshold
- `publishable = false`
- current orchestrator non-publishable path remains preserved

### Required Output

Additive structure:

```json
{
  "decision_semantics": {
    "status": "APPROVE | HOLD | REJECT",
    "publishable": false,
    "hard_failures": [],
    "soft_failures": [],
    "product_vetoes": [],
    "severity_level": "none | low | medium | high | critical",
    "dominant_reason_codes": [],
    "decision_rule_applied": "...",
    "rationale": []
  }
}
```

### Constraints

- Do not change status thresholds in this workstream unless explicitly scoped and tested.
- Do not introduce hidden publish enforcement.
- Do not alter orchestrator/core publish order.
- Do not overblock without evidence.

### Validation

Focused tests must cover clean `APPROVE`, borderline `HOLD`, technical `REJECT`, product-veto `REJECT`, and publishability flag consistency.

## 12. Workstream 5: Layer Attribution Hardening

### Goal

Link QC findings to the producing layer when evidence supports attribution.

### Attribution Targets

Allowed attribution targets:

- script
- voice
- asset
- editor
- render
- pipeline
- environment
- unknown

### Required Output

Additive structure:

```json
{
  "layer_attribution": {
    "attribution_complete": true,
    "findings": [
      {
        "reason_code": "...",
        "layer": "script | voice | asset | editor | render | pipeline | environment | unknown",
        "evidence": {},
        "confidence": "low | medium | high",
        "rationale": []
      }
    ],
    "unattributed_findings": [],
    "boundary_statement": "QC attributes findings for audit only; it does not mutate upstream outputs."
  }
}
```

### Rules

- Missing audio file may attribute to pipeline/render/voice only when evidence supports it.
- Subtitle cue issues may attribute to editor/render unless metadata indicates another source.
- Hook/payoff text proxy issues may attribute to script/editor only with available script/cue evidence.
- Asset luma issues may attribute to asset/editor/render depending on metadata evidence.
- Unknown must be used when evidence is insufficient.

### Constraints

- Do not assign blame without evidence.
- Do not mutate upstream outputs.
- Do not create hidden repair instructions.

### Validation

Focused tests must prove attribution exists, unknown is used honestly, and attribution does not rewrite outputs.

## 13. Workstream 6: Fallback And Environment Honesty

### Goal

Expose environment-dependent and fallback-derived QC evidence.

### Required Behavior

Video QC must distinguish:

- full media probe available
- `ffprobe` unavailable
- metadata fallback probe used
- metadata missing
- trace missing
- trace partial
- environment limited
- artifact unobservable

### Required Output

Additive structure:

```json
{
  "qc_fallback_environment": {
    "media_probe_mode": "ffprobe | metadata_fallback | unavailable",
    "metadata_fallback_used": false,
    "tts_trace_available": true,
    "visual_trace_available": true,
    "edit_trace_available": true,
    "environment_limitations": [],
    "fallback_evidence_used": [],
    "rationale": []
  }
}
```

### Constraints

- Do not fabricate ffprobe evidence.
- Do not hide metadata fallback.
- Do not treat missing trace as clean evidence.
- Do not fail closed solely because optional traces are missing unless the decision requires them.

### Validation

Focused tests must cover ffprobe unavailable, metadata fallback, missing trace, partial trace, and missing metadata.

## 14. Workstream 7: Confidence Calibration

### Goal

Add confidence as a trust signal for the QC decision.

Confidence must answer:

> How much can the system trust that this QC decision is supported by available artifact, metadata, trace, and product-signal evidence?

Confidence must not answer:

> How likely is the video to perform?

### Required Components

Confidence may consider:

- artifact_evidence_completeness
- technical_validation_completeness
- product_signal_coverage
- trace_evidence_quality
- media_probe_quality
- decision_consistency
- fallback_environment_penalty
- missing_trace_penalty

### Required Output

```json
{
  "confidence": 0.0,
  "confidence_level": "low | medium | high",
  "confidence_components": {
    "artifact_evidence_completeness": 0.0,
    "technical_validation_completeness": 0.0,
    "product_signal_coverage": 0.0,
    "trace_evidence_quality": 0.0,
    "media_probe_quality": 0.0,
    "decision_consistency": 0.0,
    "fallback_environment_penalty": 0.0
  },
  "confidence_rationale": {
    "confidence_meaning": "trust_in_qc_decision",
    "penalties": [],
    "boundary_statement": "QC confidence is not performance prediction."
  }
}
```

### Rules

- Confidence must be deterministic.
- Confidence must not be constant.
- Confidence must decrease under missing artifacts, missing metadata, missing traces, metadata fallback, partial evidence, and internal errors.
- Confidence may be high for clean technical decisions with complete evidence.
- Confidence may be high for clear technical reject if evidence is complete.
- Confidence must not be high for ambiguous `HOLD` with partial evidence.
- Confidence must not decide publishability by itself.

### Validation

Focused tests must cover high-confidence approve, high-confidence hard reject, lower-confidence hold, missing metadata, metadata fallback, missing traces, and deterministic replay.

## 15. Workstream 8: Trace And Auditability Hardening

### Goal

Create a consolidated `qc_trace` that allows an auditor to reconstruct why QC returned `APPROVE`, `HOLD`, or `REJECT`.

### Required Trace

```json
{
  "qc_trace": {
    "qc_input_governance": {},
    "technical_validation": {},
    "product_signal_analysis": {},
    "decision_semantics": {},
    "layer_attribution": {},
    "qc_fallback_environment": {},
    "confidence_calibration": {},
    "final_qc_decision_rationale": {},
    "missing_or_degraded_inputs": [],
    "audit_summary": {}
  }
}
```

### Required Final Rationale

Must answer:

- what artifacts were evaluated.
- which technical checks passed or failed.
- which product signals influenced the decision.
- why status is `APPROVE`, `HOLD`, or `REJECT`.
- why publishable is true or false.
- which layer likely produced each issue.
- whether media probe was full or fallback-based.
- whether upstream traces were available.
- how trustworthy the QC decision is.

### Required Audit Summary

```json
{
  "reconstructible": true,
  "required_sections_present": true,
  "decision_explained": true,
  "publishability_explained": true,
  "fallback_environment_visible": true,
  "confidence_explained": true,
  "boundary_preserved": true,
  "silent_failure_indicators": []
}
```

### Constraints

- Do not recalculate the QC decision.
- Do not change `APPROVE / HOLD / REJECT`.
- Do not fake reconstructibility.
- Do not remove existing fields.
- Do not hide missing or degraded evidence.

### Validation

Focused tests must prove `qc_trace` reconstructs approve, hold, reject, technical failure, product veto, and fallback/environment cases.

## 16. Workstream 9: Video QC Excellence Gate

### Required Artifacts

Create:

- `docs/runtime/phase-2-6/agents/video-qc/VIDEO_QC_AGENT_V2_6_EXCELLENCE_GATE.md`
- `tests/gates/agents/video_qc/run_video_qc_agent_v2_6_excellence_gate.py`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json`

Recommended:

- `OUT/audit/video_qc_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/metrics.json`

### Required Gate Dimensions

The gate must validate:

- runtime_real
- input_governed
- technical_validation_explicit
- product_signals_explicit
- decision_semantics_explicit
- layer_attribution_explicit
- fallback_environment_honest
- confidence_calibrated
- traceability_complete
- approve_hold_reject_semantics_preserved
- publishability_semantics_preserved
- orchestrator_qc_governance_preserved
- boundary_preserved
- determinism_where_required
- backward_compatible
- silent_failures_detected false

### Required Scenarios

At minimum:

1. clean rendered output -> `APPROVE`
2. missing metadata -> `REJECT`
3. missing video -> `REJECT`
4. missing audio -> `REJECT`
5. invalid subtitle cues -> `REJECT`
6. broken glyph -> `REJECT`
7. payoff too dark -> `REJECT`
8. borderline hook/payoff -> `HOLD`
9. low product signal with no hard failure -> `HOLD` or `REJECT` according to existing decision semantics
10. metadata fallback probe visible
11. missing optional traces visible
12. layer attribution unknown when evidence is insufficient
13. deterministic replay
14. backward compatibility
15. orchestrator approve path finalizes publish state
16. orchestrator hold/reject path remains non-publishable

### Verdict Rules

`HOLD` if:

- QC cannot execute through real service.
- required trace sections are missing.
- confidence is fake or constant.
- missing artifact evidence is hidden.
- metadata fallback is hidden.
- `APPROVE / HOLD / REJECT` semantics regress.
- `publishable` is inconsistent with status.
- orchestrator QC governance regresses.
- QC rewrites upstream outputs.
- QC becomes Publisher.
- core pipeline is modified.
- deterministic replay fails without explanation.
- boundary violation exists.
- silent failure is detected.

`GO_WITH_MONITORING` if:

- all critical checks pass.
- remaining residues are explicit, bounded, and tied to runtime media-probe coverage, product-signal calibration horizon, or limited longitudinal QC history.

`GO` only if:

- all checks pass and no meaningful residual monitoring remains.

## 17. Required Output By End Of Video QC v2.6

`VideoQcResult`, `VideoQcDecision`, or nested details/trace should expose additive fields such as:

- `qc_input_governance`
- `technical_validation`
- `product_signal_analysis`
- `decision_semantics`
- `layer_attribution`
- `qc_fallback_environment`
- `confidence`
- `confidence_level`
- `confidence_components`
- `confidence_rationale`
- `qc_trace`

Do not remove existing fields:

- `decision`
- `status`
- `reasons`
- `checked_at`
- `publishable`
- `details`

Do not break existing fields:

- `VideoQcDecision.status`
- `VideoQcDecision.publishable`
- `VideoQcDecision.hard_failures`
- `VideoQcDecision.soft_failures`
- `VideoQcDecision.product_vetoes`
- `VideoQcDecision.score_summary`
- `VideoQcDecision.product_signals`
- `VideoQcDecision.decision_trace`

## 18. Test Strategy

Focused workstream tests must be created as each implementation step begins.

Expected test families:

- `tests/agents/video_qc/test_video_qc_input_governance_unittest.py`
- `tests/test_video_qc_technical_validation_unittest.py`
- `tests/test_video_qc_product_signal_rationale_unittest.py`
- `tests/agents/video_qc/test_video_qc_decision_semantics_unittest.py`
- `tests/test_video_qc_layer_attribution_unittest.py`
- `tests/test_video_qc_fallback_environment_unittest.py`
- `tests/test_video_qc_confidence_calibration_unittest.py`
- `tests/agents/video_qc/test_video_qc_trace_auditability_unittest.py`
- `tests/gates/agents/video_qc/run_video_qc_agent_v2_6_excellence_gate.py`

Existing relevant tests must continue to pass, including:

- `tests/agents/video_qc/test_video_qc_agent_phase2_unittest.py`
- `tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py`
- `tests/content/test_content_pipeline_d27_unittest.py`
- `tests/agents/script/test_script_agent_phase2_unittest.py`
- `tests/agents/voice/test_voice_agent_phase2_unittest.py`
- `tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py`
- `tests/agents/trend_analysis/test_trend_analysis_agent_phase2_unittest.py`
- `tests/agents/strategy/test_strategy_agent_phase2_unittest.py`
- `tests/experiment/test_experiment_capability_phase2_unittest.py`

## 19. Failure Conditions

Video QC v2.6 must pause if any of the following occurs:

- hidden missing artifact.
- hidden metadata fallback.
- hidden missing trace.
- fake confidence.
- confidence high under ambiguous partial evidence.
- `APPROVE` with hard failures.
- `HOLD` marked publishable.
- `REJECT` marked publishable.
- product veto treated as clean approve.
- hard technical failure treated as soft warning.
- layer attribution fabricated.
- QC rewrites Script, Voice, Asset, or Edit output.
- QC rerenders content.
- QC implements Publisher.
- core pipeline is changed without governance reopen.
- orchestrator QC governance regresses.
- `qc_trace.audit_summary.reconstructible = true` while required sections are missing.
- existing QC/orchestrator/pipeline tests regress.

## 20. Residual Monitoring Candidates

Acceptable non-structural residuals may include:

- `VIDEO_QC_RUNTIME_HISTORY_STILL_SHORT`
- `VIDEO_QC_PRODUCT_SIGNAL_CALIBRATION_STILL_MATURING`
- `VIDEO_QC_MEDIA_PROBE_COVERAGE_ENVIRONMENT_DEPENDENT`
- `VIDEO_QC_LAYER_ATTRIBUTION_EVIDENCE_STILL_LIMITED`
- `VIDEO_QC_LONGITUDINAL_PRODUCT_OUTCOME_HISTORY_STILL_SHORT`

These are acceptable only if:

- they are explicit.
- they are non-structural.
- they do not hide missing trace, fake confidence, or broken decisions.
- they do not affect boundary preservation.
- they do not mask publishability inconsistency.

Structural blockers must not be reclassified as residual monitoring.

## 21. Exit Criteria

Video QC v2.6 is complete only when:

- input/artifact governance is explicit.
- technical validation rationale is explicit.
- product signal rationale is explicit and bounded.
- decision semantics are clear.
- severity is visible.
- layer attribution is evidence-backed or honestly unknown.
- fallback/environment limitations are visible.
- confidence is calibrated as trust in QC decision.
- `qc_trace` reconstructs `APPROVE / HOLD / REJECT`.
- publishability rationale is explicit.
- current orchestrator QC governance remains stable.
- existing `VideoQcResult` compatibility is preserved.
- Script, Voice, Asset, Trend, Strategy, Account Health, Learning, Experiment, Publisher, and core boundaries remain stable.
- dedicated Video QC v2.6 gate passes.

## 22. Current Authorized Next Step

The first implementation workstream after this plan is:

```text
Video QC Agent v2.6 - QC Input And Artifact Governance
```

Allowed scope:

- inspect `VideoQcInput`, `VideoQcDecision`, `VideoQcResult`, and `VideoQcAgentService`.
- add additive input/artifact governance structures.
- expose available, used, missing, degraded, ignored, and environment-dependent inputs.
- expose artifact and trace availability.
- preserve existing `APPROVE / HOLD / REJECT`.
- preserve existing `publishable` behavior.
- preserve current orchestrator/core/pipeline behavior.

Forbidden in the first workstream:

- confidence calibration.
- product-signal redesign.
- technical threshold changes.
- decision semantics changes.
- layer attribution.
- trace consolidation.
- core pipeline changes.
- orchestrator behavior changes.
- Publisher behavior.

## 23. Final Principle

Video QC Agent v2.6 must make final product-quality decisions explainable and evidence-backed.

It must not become a repair engine, hidden Publisher, Strategy layer, or performance prediction system.


---

## Source: `docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_GATE.md`

# VOICE_AGENT_V2_6_EXCELLENCE_GATE

## 1. Purpose

`VOICE_AGENT_V2_6_EXCELLENCE_GATE` is the formal validation gate for the Voice Agent after the Phase 2.6 excellence-hardening workstreams.

This gate validates Voice Agent v2.6 as implemented. It must not mutate runtime behavior to make validation pass.

The gate determines whether Voice is:

- runtime-real
- contract-governed
- delivery-semantics aware
- segment timing and pause aware
- monotony and contrast aware
- provider/fallback honest
- audio-validation linked when evidence exists
- confidence-calibrated
- traceable end-to-end
- deterministic under controlled inputs
- boundary-preserving
- free of silent failures

This gate is not a feature and is not a runtime behavior change. It is an audit artifact that can produce `GO`, `GO_WITH_MONITORING`, or `HOLD`.

## 2. Scope

In scope:

- Voice Agent runtime service execution
- `VoicePlan` contract governance
- delivery profile semantics
- hook/setup/payoff segment timing and pause analysis
- monotony and contrast analysis
- provider and fallback honesty
- audio validation linkage
- confidence calibration as trust in voice plan execution readiness
- consolidated `voice_trace`
- deterministic replay
- backward-compatible `VoiceAgentResult`
- TTS Router, Strategy, Script, Asset, QC, orchestrator, and core boundary preservation

Out of scope:

- modifying Voice runtime logic to pass the gate
- changing `VoicePlan` generation
- changing provider order
- adding providers
- synthesizing audio
- reading audio files without supplied artifacts
- modifying `TtsRouter`
- modifying Strategy, Script, Asset, QC, orchestrator, or core pipeline
- predicting performance
- converting Voice into TTS Router, Strategy, QC, Publisher, or core

## 3. Preconditions

The gate may run only after these Voice v2.6 workstreams exist:

- Voice Plan Contract Governance
- Delivery Profile Semantics
- Segment Timing And Pause Hardening
- Monotony And Contrast Analysis
- Provider And Fallback Honesty
- Audio Validation Linkage
- Confidence Calibration
- Trace And Auditability Hardening

Required code surfaces:

- `backend/app/creative/agents/voice/models.py`
- `backend/app/creative/agents/voice/service.py`
- `backend/app/creative/agents/voice/voice_plan_governance.py`
- `backend/app/creative/agents/voice/delivery_semantics.py`
- `backend/app/creative/agents/voice/segment_timing.py`
- `backend/app/creative/agents/voice/monotony_contrast.py`
- `backend/app/creative/agents/voice/provider_fallback_honesty.py`
- `backend/app/creative/agents/voice/audio_validation_linkage.py`
- `backend/app/creative/agents/voice/confidence_calibration.py`
- `backend/app/creative/agents/voice/trace_auditability.py`

Required validation command:

`python tests/gates/agents/voice/run_voice_agent_v2_6_excellence_gate.py`

Required output artifact:

`OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json`

## 4. Evaluation Dimensions

`runtime_real`

Means Voice executes through `VoiceAgentService`, not a stubbed result object.

Failure if the service cannot execute or if the gate validates only synthetic result objects.

`contract_governed`

Means requested provider, voice id, style, fallback order, delivery profile, and hook/setup/payoff segment completeness are visible and semantically validated.

Failure if degraded fields are hidden or fallback policy incoherence is accepted as complete.

`delivery_semantics_explicit`

Means hook/setup/payoff are mapped to voice roles and delivery intent is explicit.

Failure if semantics are missing or imply synthesis authority.

`segment_timing_explicit`

Means rate, emphasis, pauses, timing validity, and hook/setup/payoff timing contrast are visible.

Failure if invalid timing is hidden or timing analysis mutates the plan.

`monotony_contrast_explicit`

Means monotony risk, contrast level, variation metrics, role alignment, reason codes, and rationale are visible.

Failure if low contrast or missing segments are hidden, or if the analyzer predicts performance.

`provider_fallback_honest`

Means Voice reports requested provider and fallback order while separating Voice fallback from TTS Router execution fallback.

Failure if Voice fabricates executed provider, TTS fallback usage, provider attempts, or router execution.

`audio_validation_linked`

Means supplied TTS trace can link provider execution and durations, while missing trace remains explicit.

Failure if missing trace is treated as verified execution, duration is fabricated, or files are inspected without supplied artifacts.

`confidence_calibrated`

Means confidence measures trust in voice plan execution readiness, varies by evidence state, and is not performance prediction.

Failure if confidence is constant, high without `tts_trace`, high under monotony/degraded inputs, lacks rationale, or predicts performance.

`traceability_complete`

Means `voice_trace` reconstructs why the `VoicePlan` was emitted and what evidence was unavailable.

Failure if required trace sections are missing, reconstructibility is faked, or silent failure indicators are ignored.

`boundary_preserved`

Means Voice remains a voice planning and audit agent and does not become TTS Router, Strategy, Script, Asset, QC, Publisher, or core.

Failure if Voice executes TTS, changes provider order, adds providers, emits publishability decisions, or changes downstream behavior.

`determinism_where_required`

Means controlled identical input produces stable voice plan, analyses, confidence, and trace.

Failure if stable output drifts without input changes.

`fallback_honest`

Means fallback remains explicit, scoped, and never confused with router execution.

Failure if fallback is hidden or treated as clean executed provider evidence.

`silent_failures_detected`

Means missing trace, fake confidence, hidden fallback, boundary violations, and non-determinism are detected as blockers.

Failure if critical defects exist while the verdict passes.

## 5. Controlled Scenario Battery

The runner executes controlled scenarios through `VoiceAgentService` and direct helper evaluators where supplied TTS trace evidence is required.

Required scenarios:

- `clean_voice_plan_missing_tts_trace`
- `strong_voice_plan_with_tts_trace`
- `monotony_high`
- `degraded_contract`
- `provider_order_deviation`
- `audio_trace_partial`
- `fallback_executed_trace`
- `determinism_replay`
- `backward_compatibility`

## 6. Checklist

The runner validates:

- runtime execution
- contract governance
- delivery semantics
- segment timing
- monotony and contrast
- provider/fallback honesty
- audio validation linkage
- confidence calibration
- trace completeness
- fallback honesty
- boundary preservation
- deterministic replay
- backward compatibility
- TTS Router tests
- silent failure detection

Any failed critical checklist item becomes a blocking failure.

## 7. Verdict Semantics

`GO`

Allowed only when all critical dimensions pass and no meaningful residual monitoring remains.

`GO_WITH_MONITORING`

Allowed when all critical checks pass and remaining residuals are explicit, bounded, non-structural, and related to missing runtime TTS trace history or operational maturity.

`HOLD`

Required if any critical failure, blocking failure, fake confidence, silent failure, boundary violation, non-determinism, incomplete trace, hidden fallback, provider order mutation, or TTS Router mutation is detected.

Expected likely verdict is `GO_WITH_MONITORING`. The runner must derive it from evidence and must not hardcode it.

## 8. Failure Conditions

Critical failures include:

- Voice service cannot execute
- `VoicePlan` provider order changes from `kokoro -> piper`
- `TtsRouter` behavior changes or tests fail
- executed provider is fabricated without TTS trace
- fallback execution is fabricated without TTS trace
- missing audio trace is hidden
- confidence is high without audio trace
- confidence is high under high monotony
- trace required sections are missing
- `voice_trace.audit_summary.reconstructible` is false for normal service output
- boundary violation
- non-deterministic replay
- failed critical test battery

## 9. Output Artifacts

The runner must write:

- `OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/metrics.json`

## 10. Final Criteria

The Voice Agent v2.6 gate may recommend proceeding only when:

- Voice Agent runs through real `VoiceAgentService`
- all v2.6 additive fields exist and serialize
- contract governance is semantically complete
- delivery semantics, timing, monotony/contrast, provider/fallback honesty, audio linkage, confidence, and trace are visible
- missing `tts_trace` is explicit and prevents high confidence
- fallback and executed provider are not fabricated
- `TtsRouter` remains unchanged and tests pass
- provider order remains `kokoro -> piper`
- no boundary violation exists
- no silent failures exist
- residuals are non-structural and explicitly monitorable

Final recommendation values:

- `PROCEED_TO_ASSET_SELECTION_AGENT_V2_6_PLAN`
- `HOLD_BEFORE_ASSET_SELECTION`


---

## Source: `docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_PLAN.md`

# Voice Agent v2.6 Excellence Plan

## 1. Purpose

This document defines the formal Phase 2.6 excellence plan for the Voice Agent.

The Voice Agent is the second Wave 2 output agent. It consumes `ScriptPlan` and bounded Strategy context, then produces a `VoicePlan` for downstream TTS execution through the existing pipeline router.

This is not an implementation artifact.

This plan defines how Voice must evolve from a functional provider-routing surface into an audit-grade, segment-aware, fallback-honest, confidence-aware voice delivery planning subsystem.

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

Voice v2.6 work must preserve:

- frozen core pipeline
- TTS Router ownership over provider execution
- Kokoro as current local primary provider
- Piper as hard fallback
- Script ownership over narrative text
- Strategy ownership over creative control
- Asset ownership over visual selection
- QC ownership over product-quality validation
- Experiment ownership
- no Publisher work
- no provider expansion unless a later explicit gated provider plan authorizes it
- no hidden audio enforcement
- no fake confidence
- no fake perceptual claims
- no direct runtime synthesis inside the Voice Agent

## 3. Current State

The Voice subsystem is already operational after Phase 2.5A and Phase 2.5B.

Current capabilities include:

- `VoicePlan` exists and is operative.
- `VoiceInterpreter` exists and is deterministic/rule-based.
- `TtsRouter` is the canonical provider execution router.
- Kokoro is the current local primary provider.
- Piper remains fallback.
- `VoicePlan.provider` is no longer decorative.
- `VoicePlan.runtime_constraints.fallback_order` is present.
- Segment plans exist for `hook`, `setup`, and `payoff`.
- The pipeline can materialize `tts_trace` with requested/executed provider and fallback state.

Current limitations for Phase 2.6:

- requested vs executed provider is traceable in pipeline, but not yet consolidated at Voice Agent level.
- delivery intent is implicit in deterministic interpreter rules.
- segment-level timing rationale is shallow.
- monotony/contrast analysis is not audit-grade.
- voice confidence is not calibrated as trust in voice plan construction or execution readiness.
- fallback and provider metadata are not yet consolidated into a reconstructible `voice_trace`.
- audio validation remains primarily pipeline-side and should be linked without moving synthesis into Voice.

## 4. Objective

Voice v2.6 must make voice planning more:

- contract-governed
- segment-aware
- timing-aware
- monotony/contrast-aware through bounded proxies
- provider/fallback honest
- audio-validation aware
- confidence-calibrated
- traceable end-to-end
- ready for v3 with monitoring

The goal is to improve delivery reliability, auditability, and alignment with Script intent.

The goal is not to make Voice a synthesis engine, provider marketplace, Strategy layer, QC judge, publisher, or performance predictor.

## 5. Scope

In scope:

- Voice plan contract audit and additive trace fields.
- requested vs planned provider semantics.
- segment-level delivery intent for hook/setup/payoff.
- deterministic timing and pause rationale.
- bounded monotony and contrast analysis.
- provider and fallback honesty.
- audio validation linkage where existing pipeline artifacts allow it.
- confidence calibration for trust in voice plan construction/execution readiness.
- consolidated `voice_trace`.
- Voice v2.6 excellence gate.

Out of scope:

- modifying the core pipeline.
- changing `TtsRouter` provider order unless a focused workstream explicitly audits metadata without behavior change.
- adding new TTS providers.
- cloud/provider benchmarking expansion.
- voice cloning.
- emotion engine redesign.
- changing Script text.
- changing Strategy behavior.
- changing Asset behavior.
- changing QC behavior.
- changing publish manifest semantics.
- generating audio directly inside the Voice Agent.
- predicting performance.

## 6. Boundary Rules

Voice may:

- interpret `ScriptPlan` structure into delivery intent.
- use Strategy as bounded context for style/rate where already available.
- produce a `VoicePlan`.
- describe requested provider, fallback order, delivery profile, segment timing, and voice-plan confidence.
- consume or link existing pipeline `tts_trace` in audit contexts when available.

Voice must not:

- rewrite script text.
- choose assets.
- decide Strategy.
- decide QC outcome.
- decide publishability.
- execute TTS directly.
- create or add providers.
- bypass `TtsRouter`.
- hide fallback.
- claim perceptual excellence without evidence.
- treat fallback execution as clean primary execution.

## 7. Required Workstream Order

Voice v2.6 must be implemented in bounded workstreams:

1. Voice Plan Contract Governance
2. Delivery Profile Semantics
3. Segment Timing And Pause Hardening
4. Monotony And Contrast Analysis
5. Provider And Fallback Honesty
6. Audio Validation Linkage
7. Confidence Calibration
8. Trace And Auditability Hardening
9. Voice Excellence Gate

Do not implement all workstreams at once.

Each workstream must pass focused validation before the next workstream begins.

## 8. Workstream 1: Voice Plan Contract Governance

### Goal

Make the `VoicePlan` contract explicit, validated, and audit-friendly without changing provider execution.

### Required Behavior

The Voice Agent must expose:

- provider requested by Voice.
- voice id requested by Voice.
- style requested by Voice.
- runtime fallback order.
- delivery profile completeness.
- segment plan completeness.
- missing/degraded contract fields.
- contract compatibility status.

### Required Output

Additive structure:

```json
{
  "voice_plan_governance": {
    "contract_version": "voice_plan_governance_v2_6",
    "contract_complete": true,
    "provider_requested": "kokoro",
    "voice_id_requested": "...",
    "style_requested": "...",
    "fallback_order": ["kokoro", "piper"],
    "segments_present": ["hook", "setup", "payoff"],
    "missing_fields": [],
    "degraded_fields": [],
    "boundary_statement": "Voice plans delivery only; TTS Router executes providers.",
    "rationale": []
  }
}
```

### Constraints

- Do not add providers.
- Do not change provider order.
- Do not modify TTS Router behavior.
- Do not mutate `VoicePlan` semantics beyond additive trace.

### Validation

Focused tests must prove the contract is complete, serializable, backward-compatible, and boundary-preserving.

## 9. Workstream 2: Delivery Profile Semantics

### Goal

Make delivery intent explicit for the emitted `VoicePlan`.

### Required Behavior

The Voice Agent must explain:

- why overall style was selected.
- why overall rate was selected.
- why overall intensity was selected.
- how hook/setup/payoff delivery roles differ.
- how Script context influenced delivery intent.
- whether Strategy context was used.

### Required Output

Additive structure:

```json
{
  "delivery_semantics": {
    "overall_mode": "...",
    "overall_rate": 0.97,
    "overall_intensity": "high",
    "segment_roles": {
      "hook": "attention_and_tension",
      "setup": "continuity_and_escalation",
      "payoff": "reveal_or_resolution"
    },
    "script_alignment": {...},
    "strategy_alignment": {...},
    "rationale": []
  }
}
```

### Constraints

- Keep deterministic rule-based semantics.
- Do not create freeform emotional generation.
- Do not predict performance.
- Do not change Script output.

## 10. Workstream 3: Segment Timing And Pause Hardening

### Goal

Make timing and pause decisions explicit and auditable.

### Required Behavior

The Voice Agent must explain:

- hook rate and pause.
- setup rate and pause.
- payoff rate and pause.
- before/after pause semantics.
- timing contrast between segments.
- missing timing evidence.

### Required Output

Additive structure:

```json
{
  "segment_timing_summary": {
    "segments": {
      "hook": {"rate": 0.93, "emphasis": "high", "pause_after_ms": 320},
      "setup": {"rate": 0.97, "emphasis": "medium", "pause_after_ms": 180},
      "payoff": {"rate": 0.90, "emphasis": "high", "pause_before_ms": 420}
    },
    "timing_contrast_present": true,
    "pause_profile_complete": true,
    "rationale": []
  }
}
```

### Constraints

- Do not alter audio files.
- Do not bypass TTS Router.
- Do not hide missing segment timing.

## 11. Workstream 4: Monotony And Contrast Analysis

### Goal

Add deterministic proxies for delivery monotony and contrast without claiming human perceptual certainty.

### Required Behavior

The Voice Agent must evaluate:

- rate variation.
- emphasis variation.
- pause variation.
- segment contrast strength.
- monotony risk.
- weak contrast warnings.

### Required Output

Additive structure:

```json
{
  "monotony_contrast_analysis": {
    "monotony_risk_level": "low | medium | high",
    "contrast_level": "low | medium | high",
    "rate_variation": 0.0,
    "emphasis_variation": true,
    "pause_variation_ms": 0,
    "reason_codes": [],
    "rationale": []
  }
}
```

### Constraints

- These are proxies, not perceptual truth.
- Do not use ML.
- Do not inspect audio waveform unless an explicit later workstream has real audio artifacts.
- Do not claim expected retention improvement.

## 12. Workstream 5: Provider And Fallback Honesty

### Goal

Make provider and fallback state explicit at Voice Agent level and compatible with pipeline `tts_trace`.

### Required Behavior

The Voice Agent must expose:

- provider requested.
- fallback order.
- provider execution responsibility boundary.
- known executed provider if pipeline trace is available.
- fallback used if pipeline trace is available.
- provider trace completeness.
- fallback reason if known.

### Required Output

Additive structure:

```json
{
  "provider_fallback_trace": {
    "provider_requested": "kokoro",
    "provider_executed": null,
    "execution_trace_available": false,
    "fallback_order": ["kokoro", "piper"],
    "fallback_allowed": true,
    "fallback_used": null,
    "fallback_reason": null,
    "boundary_statement": "Voice Agent requests provider; TTS Router executes provider.",
    "rationale": []
  }
}
```

### Constraints

- Do not fabricate executed provider when only `VoicePlan` exists.
- Do not fabricate latency or duration.
- Do not change provider order.
- Do not add providers.

## 13. Workstream 6: Audio Validation Linkage

### Goal

Link Voice planning to audio validation evidence when available, without moving synthesis into Voice.

### Required Behavior

The Voice Agent or an audit utility may summarize:

- audio trace present or absent.
- requested vs executed provider when `tts_trace` exists.
- duration available or missing.
- segment durations available or missing.
- fallback execution visible.
- validation limitations.

### Required Output

Additive structure:

```json
{
  "audio_validation_summary": {
    "audio_trace_available": false,
    "provider_execution_verified": false,
    "duration_available": false,
    "segment_durations_available": false,
    "validation_status": "not_available | partial | valid | degraded",
    "rationale": []
  }
}
```

### Constraints

- Voice Agent must not synthesize audio.
- Voice Agent must not inspect files unless provided with existing artifacts.
- Absence of audio trace must be explicit, not hidden.

## 14. Workstream 7: Confidence Calibration

### Goal

Add confidence as trust in voice plan construction and execution readiness.

Confidence must answer:

> How much can the system trust this voice plan and its execution readiness?

Confidence must not answer:

> How well will the video perform?

### Inputs

Confidence may consider:

- VoicePlan contract completeness.
- delivery semantics completeness.
- segment timing completeness.
- monotony/contrast proxy strength.
- provider/fallback trace completeness.
- audio validation linkage if available.
- missing or degraded fields.
- fallback visibility.

### Required Output

```json
{
  "confidence": 0.0,
  "confidence_level": "low | medium | high",
  "confidence_components": {
    "contract_completeness": 0.0,
    "delivery_semantics": 0.0,
    "timing_completeness": 0.0,
    "contrast_strength": 0.0,
    "provider_trace_quality": 0.0,
    "audio_validation_support": 0.0,
    "fallback_penalty": 0.0
  },
  "confidence_rationale": {
    "confidence_meaning": "trust_in_voice_plan_execution_readiness",
    "penalties": [],
    "boundary_statement": "Voice confidence is not performance prediction."
  }
}
```

### Constraints

- Confidence must not be constant.
- Confidence must decrease under fallback, missing provider execution evidence, incomplete segment plans, or weak contrast.
- Confidence must not override Strategy, Script, Asset, QC, or TTS Router.
- No fake confidence.

## 15. Workstream 8: Trace And Auditability Hardening

### Goal

Create a consolidated `voice_trace` that reconstructs why the `VoicePlan` was emitted.

### Required Trace

```json
{
  "voice_trace": {
    "voice_plan_governance": {...},
    "delivery_semantics": {...},
    "segment_timing_summary": {...},
    "monotony_contrast_analysis": {...},
    "provider_fallback_trace": {...},
    "audio_validation_summary": {...},
    "confidence_calibration": {...},
    "final_voice_plan_rationale": {...},
    "missing_or_degraded_inputs": [],
    "audit_summary": {...}
  }
}
```

### Required Final Rationale

Must answer:

- why this provider was requested.
- why this voice id was selected.
- why this style was selected.
- why segment delivery differs.
- whether fallback is allowed.
- whether execution evidence is available.
- how trustworthy the plan is.
- which inputs were missing or degraded.

### Constraints

- Do not recalculate provider execution.
- Do not synthesize audio.
- Do not change VoicePlan.
- Do not fake reconstructibility.

## 16. Workstream 9: Voice Excellence Gate

### Required Artifacts

Create:

- `docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_GATE.md`
- `tests/gates/agents/voice/run_voice_agent_v2_6_excellence_gate.py`
- `OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json`

Recommended:

- `OUT/audit/voice_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/metrics.json`

### Required Scenarios

At minimum:

1. `clean_kokoro_voice_plan`
2. `horror_high_tension_delivery`
3. `true_crime_investigative_delivery`
4. `missing_script_defaults_visible`
5. `weak_segment_contrast_detected`
6. `provider_trace_without_execution_is_honest`
7. `router_kokoro_success_if_available_or_classified`
8. `router_kokoro_to_piper_fallback`
9. `determinism_replay`
10. `backward_compatibility`

### Required Validations

The gate must prove:

- VoicePlan is complete and serializable.
- requested provider is explicit.
- fallback order is explicit.
- delivery semantics are segment-aware.
- timing and pause rationale are explicit.
- monotony/contrast proxies are deterministic.
- provider/fallback trace is honest.
- no executed provider is fabricated without TTS trace.
- audio validation limitations are explicit.
- confidence is calibrated and non-constant.
- `voice_trace` is reconstructible.
- Strategy, Script, Asset, QC, Publisher, TTS Router and core boundaries are preserved.

### Verdict Rules

`HOLD` if:

- provider/fallback is hidden.
- executed provider is fabricated.
- confidence is fake or constant.
- `voice_trace` is incomplete.
- Voice becomes Strategy, Script, Asset, QC, Publisher or TTS Router.
- provider order is changed without governance.
- core pipeline is modified.
- deterministic replay fails without explanation.

`GO_WITH_MONITORING` if:

- all critical checks pass.
- remaining residues are explicit and tied to provider/runtime/audio evidence horizon.

`GO` only if:

- all checks pass and no meaningful residual monitoring remains.

## 17. Required Output By End Of Voice v2.6

`VoiceAgentResult` or related trace should expose additive fields such as:

- `voice_plan_governance`
- `delivery_semantics`
- `segment_timing_summary`
- `monotony_contrast_analysis`
- `provider_fallback_trace`
- `audio_validation_summary`
- `confidence`
- `confidence_level`
- `confidence_components`
- `confidence_rationale`
- `voice_trace`

Do not remove existing fields:

- `voice_plan`
- `fallback`

Do not break:

- `VoicePlan.provider`
- `VoicePlan.voice_id`
- `VoicePlan.style`
- `VoicePlan.delivery_profile`
- `VoicePlan.segments`
- `VoicePlan.runtime_constraints`

## 18. Voice Exit Criteria

Voice is v2.6-complete only when:

- contract governance is explicit.
- delivery semantics are explicit.
- segment timing rationale is explicit.
- monotony/contrast proxies are deterministic and bounded.
- provider/fallback state is honest.
- audio validation linkage is honest.
- confidence is trust-in-voice-plan readiness, not performance prediction.
- `voice_trace` is reconstructible.
- Kokoro remains primary.
- Piper remains fallback.
- provider order is unchanged unless a later governance-approved plan says otherwise.
- no provider expansion occurred.
- Script/Strategy/Asset/QC/core behavior remains unchanged.
- dedicated Voice v2.6 gate passes.

## 19. Failure Conditions

Voice v2.6 must pause if any of the following occurs:

- hidden provider fallback.
- provider execution fabricated.
- missing segment timing hidden.
- weak contrast hidden.
- confidence high under missing/fallback execution evidence without rationale.
- confidence predicts performance.
- Voice rewrites Script.
- Voice chooses Asset.
- Voice issues QC or publish decisions.
- Voice modifies TTS Router behavior outside a bounded trace-only workstream.
- provider order changes silently.
- new provider is added without gated provider plan.
- `voice_trace.audit_summary.reconstructible = true` while required sections are missing.
- existing Voice tests regress.
- orchestrator or pipeline integration regresses.

## 20. Current Authorized Next Step

The first implementation workstream after this plan is:

```text
Voice Agent v2.6 - Voice Plan Contract Governance
```

Allowed scope:

- inspect current `VoicePlan`, `VoiceAgentResult`, `VoiceAgentService`, `VoiceInterpreter`, and TTS trace interfaces.
- add additive contract governance structures.
- expose requested provider, voice id, style, fallback order, segment completeness, missing/degraded fields, and boundary statement.
- preserve current `VoicePlan` output.
- preserve Kokoro/Piper provider order.
- preserve Strategy, Script, Asset, QC, Experiment, Publisher and core boundaries.

Forbidden in the first workstream:

- provider expansion.
- TTS Router behavior change.
- audio synthesis.
- confidence calibration.
- monotony analysis.
- trace consolidation.
- downstream behavior changes.

## 21. Final Principle

Voice Agent v2.6 must make delivery planning explainable and trustworthy.

It must not become the TTS Router, Strategy, QC, Publisher, or a hidden provider expansion layer.
