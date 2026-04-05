# EXPERIMENT_CAPABILITY_v2_0_GOVERNANCE_DECISION

## Objective

This phase exists to decide whether `Experiment Capability v2.0` is ready for governance classification after formal validation.

This is not another implementation phase.
This is not another capability expansion phase.

It is a formal decision phase that must answer:
- is `Experiment Capability v2.0` now a real runtime subsystem
- is the correct verdict `GO` or `GO_WITH_MONITORING`
- are the remaining residues blocking or only governance-related

## Decision Inputs

The governance decision must be based on:
- the Phase 1 system bible
- the v2.0 implementation plan
- the formal validation gate artifacts
- the broader pipeline context where Experiment Capability now operates inside the frozen runtime

Primary evidence sources:
- `docs/runtime/EXPERIMENT_CAPABILITY_SYSTEM_BIBLE_PHASE1.md`
- `docs/runtime/EXPERIMENT_CAPABILITY_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/EXPERIMENT_CAPABILITY_v2_0_VALIDATION_GATE.md`
- `OUT/audit/experiment_capability_v2_0_validation/combined_outputs.json`
- `OUT/audit/pipeline_total_heavy_audit/combined_outputs.json`

## Required Questions

The decision must answer:
- `experiment_v2_implemented`
- `eligibility_explicit`
- `assignment_real`
- `result_recording_real`
- `auditability_hardened`
- `deterministic`
- `causal_difference_proven`
- `baseline_ready`
- `main_failures`
- `residual_monitoring`

## Promotion Standard

`Experiment Capability v2.0` should be considered governance-ready if:
- explicit eligibility is active
- assignment is real and persisted
- result recording is real and persisted
- fallback remains explicit and honest
- `decision_trace` and `experiment_trace` are present
- deterministic replay is proven
- controlled A/B downstream difference is proven
- no blocking failures remain in the formal gate

## Why `GO_WITH_MONITORING` Is Correct

Even with a clean `GO` validation gate, `GO_WITH_MONITORING` remains the correct governance verdict when:
- standalone runtime history is still short
- controlled validation is strong but still recent
- real production diversity is still narrower than a mature experiment subsystem should eventually see
- broader interaction with frozen pipeline operations is still in early monitored use

That is not a technical deficiency.
It is the correct governance posture.

## Why Direct Baseline Promotion Is Too Early

Direct promotion to an unmonitored baseline would overstate the subsystem today because:
- the subsystem is newly loop-closed in runtime
- the validation battery is controlled rather than long-horizon operational
- result recording and eligibility are now real, but their production history is still shallow

So the correct reading is:
- technically validated
- operationally real
- governance-ready only with monitoring

## Why `HOLD` Is Not Correct

`HOLD` would be required only if any of the following were true:
- assignment were not real
- result recording were not real
- eligibility were implicit or unstable
- fallback corrupted the audit trail
- determinism failed
- A/B proof failed

That is not the current state.

The gate proved:
- `verdict = GO`
- all controlled blocks passed
- `deterministic = true`
- `causal_difference_proven = true`
- `main_failures = []`

So `HOLD` would now be technically indefensible.

## Current Classification

Most honest classification:

```json
{
  "experiment_capability_v2": {
    "implementation": "DONE",
    "loop_closed": true,
    "eligibility": "EXPLICIT_AND_DETERMINISTIC",
    "assignment": "REAL",
    "result_recording": "REAL",
    "auditability": "HARDENED",
    "determinism": "PROVEN",
    "causality": "PROVEN",
    "validation_gate": "PASSED",
    "verdict": "GO_WITH_MONITORING",
    "baseline_status": "ACTIVE_WITH_MONITORING",
    "correct_state": "READY_FOR_GOVERNANCE_DECISION"
  }
}
```

## Formal Governance Decision

The correct governance decision is:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "experiment_v2_implemented": true,
  "eligibility_explicit": true,
  "assignment_real": true,
  "result_recording_real": true,
  "auditability_hardened": true,
  "deterministic": true,
  "causal_difference_proven": true,
  "baseline_ready": true,
  "main_failures": [],
  "residual_monitoring": [
    "EXPERIMENT_RUNTIME_HISTORY_STILL_SHORT",
    "CONTROLLED_VALIDATION_DOMINANT_OVER_LONG_HORIZON_RUNTIME",
    "REAL_PRODUCTION_VARIETY_STILL_UNDER_MONITORING"
  ],
  "baseline_status": "ACTIVE_WITH_MONITORING",
  "promotion_decision": "PROMOTE_TO_BASELINE_WITH_MONITORING",
  "next_action": "freeze_experiment_capability_v2_and_monitor"
}
```

## Operational Meaning

This means:
- the subsystem is no longer an experimental scaffold
- it is now a real experiment runtime subsystem
- it may remain active in the frozen architecture
- changes should now be conservative and governance-driven

It does not mean:
- broad redesign is justified
- adaptive rollout should start now
- winner selection should be added now
- the subsystem should expand into Strategy or Learning

## Monitoring Focus

Monitoring should focus on:
- real assignment volume over time
- real result recording continuity
- fallback rate
- blocked-by-health rate
- standard vs conservative envelope distribution
- variant diversity under real runtime
- absence of audit gaps in execution artifacts

## One-Line Decision

`Experiment Capability v2.0` is technically validated and governance-ready, but the correct classification today is `GO_WITH_MONITORING` and `PROMOTE_TO_BASELINE_WITH_MONITORING`, not immediate unmonitored baseline finality.
