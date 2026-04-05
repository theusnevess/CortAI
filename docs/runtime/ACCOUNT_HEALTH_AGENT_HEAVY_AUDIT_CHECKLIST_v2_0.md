# ACCOUNT_HEALTH_AGENT_HEAVY_AUDIT_CHECKLIST_v2_0

## 1. Objective

Prove that `Account Health Agent v2.0` is:
- a real upstream governor
- based on real runtime input, not synthetic placeholder input
- deterministic
- auditably explainable
- correctly limited in boundary
- operationally authoritative through `HOLD`
- causally relevant in the pipeline

This checklist does not ask whether Health merely exists.
It asks whether Health now does exactly what was defined for it:
- no less
- no more

## 2. Success Question

The audit must answer:

```json
{
  "account_health_v2_implemented": true,
  "input_activation_real": true,
  "auditability_real": true,
  "safe_caution_hold_operational": true,
  "fallback_explicit": true,
  "deterministic_under_controlled_inputs": true,
  "downstream_constraints_propagate": true,
  "orchestrator_enforcement_real": true,
  "boundary_respected": true,
  "baseline_behavior_stable": true
}
```

## 3. Block A — Contract Integrity

Objective:
- prove that the Health contract is correct, stable, and serializable

Must prove:
- `AccountHealthInput` contains:
  - `account_id`
  - `recent_publish_count`
  - `recent_views_drop_ratio`
  - `recent_low_performance_streak`
  - `recent_format_repetition_ratio`
- `AccountHealthDecision` contains:
  - `status`
  - `reasons`
  - `recommended_constraints`
- `AccountHealthResult` contains:
  - `decision`
  - `fallback`
  - `input_summary`
  - `decision_trace`

Critical failures:
- missing field
- inconsistent type
- non-serializable payload
- missing trace fields

## 4. Block B — Real Input Activation

Objective:
- prove that Health uses real runtime-local data

Must prove:
- `recent_publish_count` comes from `publish_records.jsonl`
- `recent_views_drop_ratio` comes from `video_metrics.jsonl`
- `recent_low_performance_streak` comes from `execution_outputs.json`
- `recent_format_repetition_ratio` comes from recent payoff-family history

Must also prove:
- values are not all default-zero in exercised runtime cases
- inputs vary between executions

Critical failures:
- constant default values
- no input variation
- runtime input detached from actual artifacts

## 5. Block C — Decision Logic Integrity

Objective:
- prove that the implemented threshold logic behaves exactly as defined

Required scenarios:
- `SAFE`
  - low signals
  - output `SAFE`
  - reason `HEALTHY_BASELINE`
- `CAUTION`
  - medium signals
  - output `CAUTION`
  - constraints emitted
- `HOLD`
  - `recent_views_drop_ratio >= 0.75` or `recent_low_performance_streak >= 4`
  - output `HOLD`

Must prove:
- thresholds are respected exactly
- invalid conditions do not generate `HOLD`
- critical conditions do not pass as `SAFE`

Critical failures:
- false `SAFE`
- false `HOLD`
- inconsistent threshold behavior

## 6. Block D — Decision Trace Auditability

Objective:
- prove that every decision is reconstructible

Must prove `decision_trace` contains:
- aggregated inputs
- thresholds evaluated
- triggered conditions
- constraints emitted
- final status
- fallback used
- fallback reason

Must prove:
- trace is consistent with output
- trace is sufficient for logical replay

Critical failures:
- incomplete trace
- trace/output mismatch
- decision without explanation

## 7. Block E — Orchestrator Enforcement

Objective:
- prove that Health has real authority in runtime

Must prove:
- `HOLD` interrupts pipeline before:
  - `creative_pack`
  - render
  - QC
- `SAFE` and `CAUTION` allow normal execution
- events are emitted:
  - `CREATIVE/account_health_safe`
  - `CREATIVE/account_health_caution`
  - `CREATIVE/account_health_hold`

Critical failures:
- `HOLD` does not block
- pipeline continues incorrectly
- health events missing

## 8. Block F — Downstream Propagation

Objective:
- prove that Health affects the system and is not decorative

Must prove:
- `Strategy` receives:
  - `health_status`
  - `recommended_constraints`
- `Strategy` changes:
  - aggressiveness
  - duration
  - variation
- `Script` receives:
  - `account_health_status`

Critical failures:
- no real Strategy effect
- constraints ignored
- only symbolic payload propagation

## 9. Block G — Determinism

Objective:
- prove total replay predictability

Must prove:
- same input -> same output
- same input -> same `decision_trace`

Required test:
- run same input multiple times

Critical failures:
- divergent outputs
- divergent traces

## 10. Block H — Fallback Integrity

Objective:
- prove that fallback is explicit, visible, and bounded

Must prove:
- fallback occurs when required
- fallback returns:
  - `SAFE`
  - `fallback_used = true`
  - non-empty `fallback_reason`
- fallback never returns `HOLD`
- fallback is never silent

Critical failures:
- invisible fallback
- inconsistent fallback
- fallback masking error without trace

## 11. Block I — Boundary Integrity

Objective:
- prove that Health still respects its own domain

Must prove that Health does not become:
- trend analysis
- learning policy formation
- QC scoring
- content generation

Must prove that Health does not require:
- `Trend`
- `Strategy`
- `Asset`
- `Editor`

Critical failures:
- responsibility mixing
- hidden domain coupling

## 12. Block J — Controlled Battery

Objective:
- prove correctness under varied deterministic scenarios

Minimum scenarios:
- stable `SAFE`
- `CAUTION` by views drop
- `CAUTION` by repetition
- `CAUTION` by streak
- `HOLD` by views drop
- `HOLD` by streak
- fallback scenario
- mixed/conflicting signals

Must prove:
- correct decisions in every case
- consistent trace
- coherent pipeline behavior

## 13. Block K — Real Execution Validation

Objective:
- prove behavior outside pure unit conditions

Must prove:
- multiple real orchestrator executions
- naturally varying inputs
- coherent outputs
- no degenerate baseline behavior

Important honesty rule:
- “real” here means runtime-local real execution through the orchestrator using actual persisted runtime artifacts
- not hypothetical platform telemetry

## 14. Block L — Audit Artifacts

Required artifacts:
- `final_verdict.json`
- `block_summary.json`
- `decision_examples.json`
- `execution_batch.json`
- `metrics.json`
- `human_review.json`
- `event_summary.json`

Critical failures:
- missing artifacts
- missing traceability

## 15. Block M — Baseline Behavior Stability

Objective:
- prove that baseline behavior is stable enough for operation

Must prove:
- no unexpected drift
- consistent behavior across executions
- no structural regressions

This block may still yield `GO_WITH_MONITORING` if:
- behavior is stable
- but standalone operational history is still short
- or telemetry richness is still intentionally limited

## 16. Verdict Logic

### `GO`

Only if:
- every critical block passes
- no meaningful methodological reservations remain
- behavior is fully consistent

### `GO_WITH_MONITORING`

If:
- the subsystem works
- critical blocks pass
- but operational history is still short
- or telemetry richness is still intentionally limited

### `HOLD`

If:
- any critical block fails

## 17. Final Question

```json
{
  "from": "simple deterministic gate with weak input",
  "to": "real, input-activated, auditable upstream governance subsystem"
}
```

## 18. Honest Expected Current Outcome

```json
{
  "verdict": "GO_WITH_MONITORING",
  "account_health_v2_implemented": true,
  "input_activation_real": true,
  "auditability_real": true,
  "safe_caution_hold_operational": true,
  "fallback_explicit": true,
  "deterministic_under_controlled_inputs": true,
  "downstream_constraints_propagate": true,
  "orchestrator_enforcement_real": true,
  "boundary_respected": true,
  "baseline_behavior_stable": true
}
```

Reason:
- capability is now real
- validation is strong
- governance is already promoted
- remaining residues are methodological, not blocking

## 19. One-Line Summary

This heavy audit does not merely validate that Account Health works.
It proves that Account Health became exactly what it was supposed to become:
- a real
- governed
- explainable
- causal
- upstream account governor
