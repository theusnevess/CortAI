# ACCOUNT_HEALTH_AGENT_BASELINE_OPERATION_RULES_v1_0

## 1. Current Baseline State

`Account Health Agent v2.0` is now in the following state:

```json
{
  "standalone_governance": "DONE",
  "verdict": "GO_WITH_MONITORING",
  "baseline_promoted": true,
  "baseline_status": "ACTIVE_WITH_MONITORING",
  "current_state": "FROZEN_WITH_MONITORING"
}
```

Authoritative source artifacts:
- `OUT/audit/account_health_agent_v2_standalone_governance_decision/final_verdict.json`
- `OUT/audit/account_health_agent_v2_baseline_promotion_verdict.json`

## 2. Operational Rule

The operative rule is:

- `freeze_account_health_v2_and_monitor`

This means:
- the subsystem is baseline-active
- the subsystem is not open for opportunistic redesign
- the subsystem should only be reopened if monitoring produces materially new evidence

## 3. What Must Stay Frozen

The following must remain frozen during baseline monitoring:
- the public decision surface: `SAFE`, `CAUTION`, `HOLD`
- the existing `recommended_constraints` contract
- fallback semantics
- early orchestrator `HOLD` enforcement
- the current deterministic threshold logic
- the current subsystem boundary

This also means:
- do not widen Health into Learning
- do not widen Health into QC
- do not widen Health into Strategy
- do not add opaque scoring
- do not add probabilistic heuristics

## 4. What Monitoring Must Observe

Monitoring should observe:
- actual frequency of `SAFE`, `CAUTION`, and `HOLD`
- whether `HOLD` remains operationally correct
- whether `recommended_constraints` continue to propagate cleanly into `Strategy`
- whether decision traces remain present and reconstructible
- whether fallback remains explicit and rare
- whether any new failure pattern emerges in real pipeline usage

Monitoring is not for speculative tuning.
Monitoring is for detecting whether reality contradicts the validated baseline.

## 5. Active Residual Monitoring

The current non-blocking residuals are:
- `ACCOUNT_HEALTH_STANDALONE_HISTORY_STILL_SHORT`
- `ACCOUNT_HEALTH_TELEMETRY_RICHNESS_STILL_LIMITED`

Interpretation:
- the subsystem is baseline-worthy now
- but the monitoring window is still needed because standalone operational history is short
- and because telemetry richness is still intentionally narrower than a mature health intelligence system

These are not blockers.
They are explicit governance reservations.

## 6. What Does Not Justify Reopening

The following do not justify reopening the subsystem:
- desire for a more sophisticated score
- desire for a richer-looking health model
- cosmetic audit output improvements
- speculative boundary expansion
- isolated intuition that the subsystem could be "smarter"

Reopening without material evidence would be complexity inflation, not justified engineering.

## 7. What Does Justify Reopening

Reopening is justified only if at least one of the following becomes true:
- monitoring shows `HOLD` is firing incorrectly in real usage
- monitoring shows `CAUTION` is not propagating usable constraints downstream
- deterministic replay stops holding under the same evidence shape
- decision trace becomes incomplete or operationally unhelpful
- real telemetry becomes available that materially upgrades the Health input surface
- baseline monitoring reveals a consistent failure mode the current narrow logic cannot represent

## 8. Correct Reopening Order

If reopening becomes necessary, the order must be:
1. prove the monitoring evidence
2. define the exact deficit
3. confirm the deficit belongs to Health and not to `Learning`, `QC`, or `Strategy`
4. write a new bounded implementation plan
5. only then modify the subsystem

This prevents boundary drift and avoids turning Health into a catch-all policy layer.

## 9. Operational Classification

The correct current classification is:
- runtime-real
- input-activated
- auditably explainable
- deterministic
- upstream-governed
- baseline-active
- frozen with monitoring

The subsystem should not currently be described as:
- a rich risk intelligence engine
- a platform telemetry brain
- a generalized governance super-layer

## 10. One-Line Rule

`Account Health Agent v2.0` is baseline-active and frozen: monitor it, do not expand it, and reopen only when new evidence materially justifies change.
