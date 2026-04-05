# EXPERIMENT_CAPABILITY_v2_0_VALIDATION_GATE

## 1. Objective
Prove that `Experiment Capability v2.0` is now a real runtime subsystem rather than a contextual scaffold.

This gate must answer:
1. does `Health HOLD` block experiment assignment?
2. does novelty pressure enable `standard` experiment eligibility?
3. does quality instability force `conservative` eligibility?
4. does missing config remain explicit fallback rather than fake assignment?
5. are assignment and result recording both real?
6. is experiment replay deterministic?
7. can the system prove a traceable A/B downstream difference?

## 2. Scope
### Included
- `ExperimentCapabilityService`
- experiment eligibility rules
- runtime assignment persistence
- runtime result persistence
- `decision_trace`
- `experiment_trace`
- orchestrator integration
- script-level A/B causality proof

### Out of scope
- winner selection
- adaptive rollout
- learning optimization
- strategy redesign
- multi-agent causal expansion beyond the minimum experiment proof

## 3. Block A: Health Hold Blocking
The gate must prove:
- `account_health == HOLD` prevents real assignment
- `experiment_assignment` remains `null`
- eligibility reason is `ACCOUNT_HEALTH_HOLD`
- no assignment or result rows are created

## 4. Block B: Standard Eligibility By Novelty
The gate must prove:
- high novelty pressure enables experiment execution
- eligibility envelope is `standard`
- assignment is recorded
- result is recorded

## 5. Block C: Conservative Eligibility By Instability
The gate must prove:
- unstable quality signals allow experiment only under `conservative`
- assignment is still real
- experiment plan payload is constrained by the safe envelope

## 6. Block D: Honest Fallback
The gate must prove:
- missing config yields explicit fallback
- no fake assignment is synthesized
- no fake result is recorded
- fallback remains visible in artifacts and events

## 7. Block E: Deterministic Replay
The gate must prove:
- same config + same subject key + same eligibility inputs -> same eligibility decision
- same config + same subject key + same eligibility inputs -> same assignment id
- same config + same subject key + same eligibility inputs -> same variant id
- result recording remains stable under replay

## 8. Block F: Controlled A/B Causality
The gate must prove:
- two different eligible subjects can resolve into `A` and `B`
- script output differs because of experiment assignment
- that difference is traceable in artifacts
- assignment and result rows link cleanly to each run

## 9. Required Artifacts
The gate must generate:
- `OUT/audit/experiment_capability_v2_0_validation/final_verdict.json`
- `OUT/audit/experiment_capability_v2_0_validation/block_summary.json`
- `OUT/audit/experiment_capability_v2_0_validation/decision_examples.json`
- `OUT/audit/experiment_capability_v2_0_validation/execution_batch.json`
- `OUT/audit/experiment_capability_v2_0_validation/metrics.json`
- `OUT/audit/experiment_capability_v2_0_validation/human_review.json`
- `OUT/audit/experiment_capability_v2_0_validation/event_summary.json`

## 10. Success Standard
### `GO`
Use only if:
- all required blocks pass
- assignment is real
- result recording is real
- fallback remains honest
- determinism holds
- A/B difference is traceable
- no boundary violation is introduced

### `GO_WITH_MONITORING`
Use only if:
- the core loop and causal proof pass
- one non-blocking methodological limitation remains

### `HOLD`
Use if any of the following happen:
- `HOLD` does not block assignment
- fallback synthesizes fake assignment/result
- determinism breaks
- A/B proof cannot be demonstrated
- result recording is not linked cleanly to runtime execution

## 11. Final Question
At the end of the gate, the subsystem must answer:

```json
{
  "experiment_v2_implemented": true,
  "eligibility_explicit": true,
  "assignment_real": true,
  "result_recording_real": true,
  "fallback_honest": true,
  "deterministic": true,
  "causal_difference_proven": true,
  "promotion_ready": false
}
```

`promotion_ready` remains `false` until the subsystem is reviewed against broader pipeline governance and monitoring.
