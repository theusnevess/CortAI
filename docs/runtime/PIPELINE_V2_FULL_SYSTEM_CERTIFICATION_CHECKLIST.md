# Pipeline v2 Full System Certification Checklist

## 1. Objective
Prove that the full pipeline:

`Health -> Trend -> Learning -> Novelty -> Strategy -> Script -> Voice -> Asset -> Editor -> QC`

is:
- functional
- causal
- deterministic
- governed
- stable
- ready for controlled production

## 2. Decision Standard
Certification is not a single subsystem test.

It must combine:
- structural integrity
- contract integrity
- per-agent causality
- inter-agent integration
- governance enforcement
- learning loop closure
- novelty enforcement
- determinism
- real execution evidence
- quality and stability evidence

## 3. Block A: Structural Integrity
### Objective
Guarantee that the orchestrated pipeline exists and runs end-to-end.

### Checks
- orchestrator executes the full chain without structural error
- all agents are called in valid order
- no stage returns `None` or invalid structure
- `CreativePack` is formed completely
- pipeline reaches `QC`

## 4. Block B: Contracts And Data
### Objective
Guarantee contract consistency across the full system.

### Checks
- `StrategyProfile` valid and complete
- `ScriptPlan` includes `hook`, `setup`, `payoff`
- `VoicePlan` includes coherent segments
- `AssetPlan` includes valid segment plans
- `EditPlan` includes consistent timing
- `VideoQcDecision` / `VideoQcResult` complete
- critical fields are not empty
- field types remain valid
- cross-agent compatibility holds

## 5. Block C: Per-Agent Causality
### Objective
Prove that no key agent is decorative.

### Required proof
- `Strategy` reacts to constraints, trend, metrics, novelty, and learning policy
- `Script` changes with strategic context
- `Voice` changes with script/strategy context
- `Asset` changes with variation and novelty constraints
- `Editor` remains coherent with upstream plans
- `QC` governs outcomes
- `Learning` consumes QC and alters Strategy
- `Novelty` detects repetition and alters downstream behavior

## 6. Block D: Inter-Agent Integration
### Objective
Prove that agents affect one another through real runtime paths.

### Required proof
- `Learning -> Strategy`
- `Strategy -> Script`
- `Strategy -> Asset`
- `Script -> Voice`
- `Script -> Asset`
- `Asset + Voice + Script -> Editor`
- `Editor -> QC`
- `QC -> Pipeline governance`

## 7. Block E: Governance
### Objective
Prove that `QC` remains real authority.

### Required proof
- `APPROVE` => publishable
- `HOLD` => blocked
- `REJECT` => blocked
- no publish manifest before QC authority
- governance remains stronger than downstream generation behavior

## 8. Block F: Learning Loop
### Objective
Prove that the system now closes the learning loop minimally but for real.

### Required proof
- QC enters Learning
- Learning forms policy
- Strategy reacts to policy
- contaminated evidence is downgraded
- post-learning batch shows policy application

## 9. Block G: Novelty Engine
### Objective
Prove that repetition remains controlled.

### Required proof
- structural repetition detected
- visual repetition detected
- pressure rises with repetition
- variation policy rises when needed
- Script and Asset escape blocked patterns
- diversity improves without material quality collapse

## 10. Block H: Determinism
### Objective
Prove reproducibility.

### Required proof
- same controlled input => same `StrategyProfile`
- same controlled input => same `ScriptPlan`
- same controlled input => same `AssetPlan`
- same controlled input => same QC decision
- no chaotic replay drift

## 11. Block I: Real Execution
### Objective
Prove that the system generates valid real artifacts.

### Required proof
- valid `.mp4`
- valid audio
- valid metadata
- valid subtitles
- captured `execution_outputs.json`
- reproducible artifact audit path

## 12. Block J: Quality And Stability
### Objective
Prove that the system does not degrade materially.

### Required proof
- approve rate >= recent baseline or within declared tolerance
- average score >= recent baseline within declared tolerance
- no new systemic failure pattern
- QC does not collapse
- Strategy does not become chaotic

## 13. Required Audit Artifacts
The certification runner must generate:
- `OUT/audit/pipeline_v2_full_system_certification/final_verdict.json`
- `OUT/audit/pipeline_v2_full_system_certification/block_summary.json`
- `OUT/audit/pipeline_v2_full_system_certification/agent_causality_report.json`
- `OUT/audit/pipeline_v2_full_system_certification/integration_report.json`
- `OUT/audit/pipeline_v2_full_system_certification/execution_batch.json`
- `OUT/audit/pipeline_v2_full_system_certification/metrics.json`
- `OUT/audit/pipeline_v2_full_system_certification/determinism_report.json`
- `OUT/audit/pipeline_v2_full_system_certification/governance_report.json`
- `OUT/audit/pipeline_v2_full_system_certification/human_review.json`

## 14. Verdict Rules
### GO
Use `GO` only if:
- all critical blocks pass
- no systemic failure exists
- causality is proven
- governance is intact
- determinism holds
- real execution holds
- quality stability holds

### GO_WITH_MONITORING
Use if:
- all critical blocks pass
- only non-blocking residuals remain
- residuals are explicit and monitorable

### HOLD
Use if any of the following occur:
- structural break
- failed governance
- failed determinism
- failed learning loop
- failed novelty enforcement
- material quality collapse
- new systemic failure pattern

## 15. Operational Principle
This checklist exists to convert the whole pipeline from “complex and functional” into “auditable and defensible”.

Rule:
- if stable, do not touch
