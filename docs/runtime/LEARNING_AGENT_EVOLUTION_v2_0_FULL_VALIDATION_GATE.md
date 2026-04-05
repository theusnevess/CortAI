# Learning Agent Evolution v2.0 Full Validation Gate

## 1. Objective
Prove that `Learning Agent v2.0` has crossed the line from weak summarization into a minimally closed, conservative, causal optimization layer.

This gate must answer:
1. does `Learning` ingest real `QC` evidence?
2. does it form coherent policy rather than decorative hints?
3. does `Strategy` change because of that policy?
4. does fallback contamination handling prevent poisoned conclusions?
5. is determinism preserved?
6. does the small validation batch avoid regression?
7. is quality stability preserved?
8. is governance preserved?

## 2. Scope
### Included
- `LearningAgentService`
- `LearningAgentResult`
- `LearningInsights`
- `LearningPolicy`
- `PatternFindingSummary`
- `StrategyInput`
- `StrategyAgentService`
- Learning-to-Strategy orchestration path
- fallback contamination handling
- controlled validation scenarios

### Out of scope
- direct `Voice` integration
- direct `Asset` integration
- direct `Editor` integration
- experiment engine redesign
- online adaptive learning
- production soak

## 3. Block A: QC Ingestion
The gate must prove that `Learning` reads real quality evidence, not only views and completion.

### Required proof
- `APPROVE`, `HOLD`, `REJECT` are ingested
- `overall_score` is ingested
- `product_quality` is ingested
- `hook_quality` is ingested
- `payoff_quality` is ingested
- `reasons` are available to the learning layer when present

## 4. Block B: Policy Formation
The gate must prove that `Learning` emits structured policy.

### Required proof
- `learning_policy` is populated
- policy values change when history changes materially
- policy remains stable when equivalent history is replayed
- policy trace is auditable
- confidence and evidence counts are populated coherently

## 5. Block C: Strategy Reaction
The gate must prove that `Strategy` consumes `LearningPolicy` causally.

### Required proof
- duration bias can alter `target_duration_range`
- risk hint can alter `content_mode`
- hook bias can alter `hook_aggressiveness`
- variation tolerance can alter `variation_policy`
- payoff specificity bias reaches strategic hints
- `decision_trace` records the learning-driven adjustments

## 6. Block D: Fallback Contamination Handling
The gate must prove that contaminated evidence is not treated as clean evidence.

### Required proof
- contaminated runs are identified
- clean execution count is separated from total execution count
- fallback contamination rate is exposed
- high-scoring contaminated evidence does not dominate policy confidence by itself

## 7. Block E: Determinism
The gate must prove:
- same historical inputs -> same `LearningAgentResult`
- same `LearningPolicy` -> same `StrategyResult`
- no chaotic drift across equivalent replays

## 8. Block F: Controlled Batch
Run a small controlled scenario batch with at least:
- winner cluster
- loser cluster
- contaminated cluster

### Expected proof
- winner cluster yields stronger policy
- loser cluster yields conservative risk adjustment
- contaminated cluster shows downgraded evidence trust
- downstream strategy posture changes for the right reasons

## 9. Block G: Quality Stability
This gate is primarily about Learning and Strategy, but it must still remain honest about quality.

### Required proof
- no evidence that `Learning` pushes `Strategy` into unsafe escalation under low-score clusters
- controlled batch keeps outputs valid and governed
- if pipeline-wide real batch evidence is reused instead of rerendered, that must be declared explicitly

## 10. Block H: Governance
The gate must prove:
- `Learning` does not override account health hierarchy
- `Learning` does not bypass `QC`
- `Learning` strengthens governance through `Strategy`, not around it

## 11. Audit Artifacts
The gate must generate at minimum:
- `OUT/audit/learning_agent_evolution_v2_0_full_validation_gate/block_summary.json`
- `OUT/audit/learning_agent_evolution_v2_0_full_validation_gate/final_verdict.json`
- `OUT/audit/learning_agent_evolution_v2_0_full_validation_gate/policy_examples.json`
- `OUT/audit/learning_agent_evolution_v2_0_full_validation_gate/execution_batch.json`
- `OUT/audit/learning_agent_evolution_v2_0_full_validation_gate/metrics.json`
- `OUT/audit/learning_agent_evolution_v2_0_full_validation_gate/human_review.json`

## 12. Success Standard
### `GO`
Use only if all of the following are true:
- QC ingestion is real
- policy formation is coherent
- strategy reaction is real
- contamination handling works
- determinism holds
- controlled batch passes
- no material quality regression is visible
- governance is preserved
- no methodological honesty issue remains

### `GO_WITH_MONITORING`
Use if the core causal proof passes but one non-blocking limitation remains.

Examples:
- pipeline-wide quality evidence reused from persisted artifacts instead of rerendered post-change
- controlled batch is strong, but fresh small real batch is still pending

### `HOLD`
Use if any of the following happen:
- policy does not change when history changes
- strategy does not react materially
- contamination handling fails
- determinism breaks
- low-score clusters trigger unsafe escalation
- governance weakens

## 13. Final Question
At the end of the gate, the system must answer clearly:

```json
{
  "learning_v2_implemented": true,
  "qc_feedback_real": true,
  "policy_forming": true,
  "strategy_causal_response": true,
  "contamination_handling": true,
  "deterministic": true,
  "promotion_ready": false
}
```

`promotion_ready` only becomes `true` if the gate concludes without material reservation.
