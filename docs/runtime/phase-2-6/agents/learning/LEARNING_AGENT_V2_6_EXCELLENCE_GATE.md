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
