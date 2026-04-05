# Pipeline Multiagent Heavy Audit Checklist v1.0

## 1. Objective
Prove that the current multiagent pipeline is:
- structurally correct
- individually valid by subsystem
- causally active across agent boundaries
- governed
- deterministic where required
- stable in real execution
- safe to continue evolving

This is a master audit gate.

Rule:
- no next subsystem should advance if the current pipeline cannot prove integrity, causality, governance, and stability end to end

## 2. Scope
Covered layers:
- Account Health
- Trend Analysis
- Learning / Optimization
- Novelty / Saturation
- Strategy
- Script
- Voice
- Asset
- Editor
- QC
- Orchestrator
- Content pipeline / render

## 3. Final Question
At the end of the gate, the system must be able to answer:

```json
{
  "pipeline_integrity": true,
  "individual_agents_valid": true,
  "cross_agent_orchestration_valid": true,
  "downstream_causality_valid": true,
  "governance_valid": true,
  "real_execution_valid": true,
  "quality_stable": true,
  "promotion_blockers": []
}
```

## 4. Block A: Structural Integrity
### Objective
Guarantee that the real architecture exists and runs in the correct order.

### Required checks
- orchestrator calls all critical agents in valid order
- no critical agent is skipped
- no critical output is `None`
- final `CreativePack` contains all required blocks
- pipeline reaches render and QC without structural break
- execution outputs preserve agent blocks

### Blocking failures
- missing critical agent call
- broken order
- incomplete pack
- pipeline breaks before QC

## 5. Block B: Contracts And Serialization
### Objective
Guarantee that producer/consumer contracts remain intact.

### Required checks
- `AccountHealthDecision` serializable
- `TrendProfile` serializable
- `LearningInsights` serializable
- `LearningPolicy` serializable
- `StrategyProfile` serializable
- `ScriptPlan` serializable
- `VoicePlan` serializable
- `AssetPlan` / `AssetSelectionResult` serializable
- `EditPlan` serializable
- `VideoQcDecision` serializable
- `CreativePack` preserves cross-block compatibility

### Blocking failures
- missing mandatory field
- non-serializable contract
- producer/consumer incompatibility

## 6. Block C: Individual Agent Validation
### Objective
Guarantee that each subsystem is operational on its own terms.

### Required checks
#### Account Health
- returns `SAFE` / `HOLD` coherently
- constraints coherent
- fallback traceable
- does not break pipeline

#### Trend
- real evidence active
- provenance present
- freshness enforced
- validation summary coherent
- fallback hierarchy operational
- deterministic under controlled inputs

#### Learning
- consumes real QC
- forms real policy
- separates clean vs contaminated evidence
- influences Strategy
- deterministic

#### Novelty
- recent memory works
- pressure rises with repetition
- structural blocks work
- visual blocks work
- diversity rises without quality collapse

#### Strategy
- reacts to Health
- reacts to Trend
- reacts to Learning
- reacts to Novelty
- decision trace coherent
- deterministic

#### Script
- always produces valid `hook/setup/payoff`
- strategic context is real
- fallback exists
- does not regress to weak phase-1 behavior
- remains semantically coherent

#### Voice
- style coherent with Strategy and Script
- segment plans coherent
- pacing and intensity valid
- provider fallback operational
- no silent contamination

#### Asset
- valid assets by segment
- responds to Trend
- responds to Strategy
- responds to Novelty
- does not reintroduce excessive repetition
- safe visual fallback exists

#### Editor
- `EditPlan` operational
- captions coherent
- timing coherent
- motion coherent
- color and atmosphere coherent
- render obeys plan
- does not regress to slideshow/subtitle-only

#### QC
- score summary coherent
- product signals coherent
- `APPROVE/HOLD/REJECT` operational
- publishability governed for real
- no bypass

## 7. Block D: Downstream Causality
### Objective
Prove that agents are not decorative.

### Required checks
- Trend alters Strategy
- Trend alters Asset
- Learning alters Strategy
- Novelty alters Strategy
- Novelty alters Script
- Novelty alters Asset
- Strategy alters Script
- Strategy alters Voice
- Strategy alters Asset
- Script alters Voice
- Script + Trend + Strategy alter Asset
- Asset + Voice + Script alter Editor
- Editor alters QC evaluation surface
- QC alters final publishability

### Blocking failures
- only cosmetic change
- symbolic causality only
- agent present but behaviorally inert

## 8. Block E: Cross-Agent Orchestration
### Objective
Guarantee that agents work together rather than only in isolation.

### Required checks
- `Health -> Trend -> Learning -> Novelty -> Strategy` coherent
- `Strategy -> Script -> Voice -> Asset -> Editor` coherent
- `Editor -> QC -> Pipeline status` coherent
- final `CreativePack` remains semantically consistent
- traces do not contradict each other
- one agent fallback does not break the others

### Blocking failures
- semantic divergence between plans
- inconsistent pack
- partially connected orchestration

## 9. Block F: Governance And Authority
### Objective
Guarantee that authority layers remain correct.

### Required checks
- Health remains above Strategy
- Strategy remains the control layer
- Learning does not invade Strategy ownership
- Trend does not invade Learning ownership
- Novelty does not invade Trend ownership
- QC remains final authority over publishability
- publish manifest is not born before QC authority
- `HOLD` and `REJECT` block correctly
- fallback does not hide real failure

### Blocking failures
- boundary violation
- QC bypass
- wrong publishability
- agent absorbing another layer's responsibility

## 10. Block G: Determinism And Replay
### Objective
Guarantee predictability and auditability.

### Required checks
- same controlled input => same Trend
- same controlled input => same LearningPolicy
- same controlled input => same StrategyProfile
- same controlled input => same AssetPlan
- same controlled input => same QC decision
- controlled replay batch consistent

### Blocking failures
- drift without reason
- divergent outputs in controlled scenario

## 11. Block H: Fallbacks And Graceful Degradation
### Objective
Guarantee resilience without silent corruption.

### Required checks
- Trend fallback explicit
- Learning fallback explicit
- Voice fallback explicit
- Asset fallback explicit
- fallback in one agent is not treated as clean evidence by another
- fallback path recorded in traces/events
- system remains operational under controlled degradation

### Blocking failures
- invisible fallback
- fallback contaminates learning
- degraded pipeline breaks

## 12. Block I: Controlled Batch
### Objective
Test varied deterministic scenarios.

### Minimum scenarios
- healthy baseline
- strong Trend
- stale Trend
- Learning winner cluster
- Learning loser cluster
- Learning contamination cluster
- Novelty low / medium / high
- Trend fallback
- QC hold
- QC reject
- Asset pressure
- strong Editor with borderline asset

### Required proof
- each scenario yields expected decision
- governance remains intact
- downstream remains coherent

## 13. Block J: Real Batch
### Objective
Prove the system works outside the lab.

### Minimum proof
- `3-5` fresh real executions or canonical recent real batch reference
- valid `.mp4`
- valid audio
- valid captions/subtitles
- valid metadata
- complete per-agent outputs
- no systemic new failure pattern

## 14. Required Artifacts
The heavy audit gate must generate at minimum:
- `OUT/audit/pipeline_multiagent_heavy_audit_gate/final_verdict.json`
- `OUT/audit/pipeline_multiagent_heavy_audit_gate/block_summary.json`
- `OUT/audit/pipeline_multiagent_heavy_audit_gate/agent_matrix.json`
- `OUT/audit/pipeline_multiagent_heavy_audit_gate/execution_batch.json`
- `OUT/audit/pipeline_multiagent_heavy_audit_gate/metrics.json`
- `OUT/audit/pipeline_multiagent_heavy_audit_gate/human_review.json`

## 15. Verdict Logic
### `GO`
Use only if:
- all critical blocks pass
- no systemic failure remains
- causality proven
- governance intact
- determinism holds
- real execution valid
- quality stable
- no meaningful methodological reservation remains

### `GO_WITH_MONITORING`
Use if:
- all critical blocks pass
- only non-blocking residuals remain
- residuals are explicit and monitorable

### `HOLD`
Use if:
- structural break exists
- governance fails
- determinism fails
- causality fails
- material quality collapse exists
- new systemic failure pattern exists

## 16. Operational Principle
This gate converts the pipeline from:
- complex and functional

into:
- auditable and defensible

Rule:
- if stable, do not touch
