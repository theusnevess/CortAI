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
