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
