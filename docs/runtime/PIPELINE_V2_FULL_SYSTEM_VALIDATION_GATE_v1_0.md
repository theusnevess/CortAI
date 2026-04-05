# Pipeline v2 Full System Validation Gate v1.0

## 1. Objective
Prove that the current `pipeline v2` remains operationally solid as one integrated system.

This gate is not a subsystem-specific validation.
It is a system-level validation for the combined behavior of:
- `Strategy`
- `Script`
- `Voice`
- `Assets`
- `Editor`
- `QC`

The gate must answer, with audit evidence:
1. is the pipeline v2 structurally intact?
2. do the agents still have causal effect?
3. is the system still governed correctly?
4. is product quality still strong enough?
5. is repetition still under control?
6. is there any hidden regression that should block continued operation?

## 2. Decision Standard
The gate must not rely on isolated unit tests or anecdotal runs.

It must combine:
- contract validation
- unit validation
- inter-agent integration validation
- governance enforcement validation
- controlled batch validation
- repetitive batch validation
- small real batch validation
- artifact auditability
- human-readable product review

## 3. Scope
### Included
- `StrategyResult`
- `ScriptPlan`
- `VoicePlan`
- `AssetSelectionResult` / `AssetPlan`
- `EditPlan`
- `VideoQcDecision` / `VideoQcResult`
- `CreativePack`
- `CreativePipelineExecution`
- pipeline orchestration
- publishability governance
- novelty enforcement

### Out of scope
- new subsystem design
- large contract redesign
- Strategy v3 expansion
- Editor novelty expansion beyond current implementation
- long-horizon production soak as promotion substitute

## 4. Block A: Contracts And Serialization
The gate must validate the integrity of the main pipeline contracts.

### Checklist
- `StrategyResult` serializes and deserializes without loss
- `ScriptPlan` serializes and deserializes without loss
- `VoicePlan` serializes and deserializes without loss
- `AssetSelectionResult` and `AssetPlan` serialize and deserialize without loss
- `EditPlan` serializes and deserializes without loss
- `VideoQcDecision` and `VideoQcResult` serialize and deserialize without loss
- enum-like fields remain valid and clamped
- required fields remain present
- `CreativePack` remains compatible with all upstream outputs
- `CreativePipelineExecution` remains compatible with full pipeline outputs

## 5. Block B: Unit Validation By Agent
### Strategy
- `health_status` changes the profile correctly
- `recent_metrics_summary` influences the profile correctly
- `recommended_constraints` influence the profile correctly
- `trend_profile` influences the profile correctly
- `novelty_pressure_profile` influences the profile correctly
- final clamp preserves valid values
- `decision_trace` is coherent and auditable
- deterministic behavior is preserved

### Script
- `hook`, `setup`, `payoff` are always present
- strategic context enters prompt construction
- fallback remains coherent
- payoff does not collapse into weak empty closure
- `generation_mode` remains coherent
- deterministic controlled mode remains stable

### Voice
- provider and fallback chain remain valid
- style remains coherent with niche and strategy
- segment timing remains valid
- rate and emphasis remain valid
- runtime constraints remain valid
- fallback does not break output integrity

### Assets
- selection works per segment
- runtime constraints remain valid
- `variation_policy` alters selection behavior
- novelty blocks are obeyed
- safe fallback remains available
- no regression into phase-1-like weak behavior

### Editor
- `EditPlan` remains structurally valid
- caption plan remains valid
- music plan remains valid
- transition plan remains valid
- motion plan remains valid
- color plan remains valid
- timing plan remains valid
- editor version remains expected
- render path obeys `EditPlan`

### QC
- `APPROVE`, `HOLD`, `REJECT` remain coherent
- score summary remains coherent
- product signals remain coherent
- publishability remains coherent
- enforcement remains coherent
- decision trace remains coherent

## 6. Block C: Inter-Agent Integration
The gate must prove that agents still affect one another for the right reasons.

### Strategy -> Script
- `hook_aggressiveness` alters Script context materially
- `target_duration_range` alters Script context materially when applicable

### Strategy -> Voice
- `content_mode` alters Voice interpretation
- duration intent alters speech behavior when applicable
- differences remain deterministic

### Strategy -> Assets
- `variation_policy` alters asset behavior
- novelty pressure alters payoff visual family when repeated patterns accumulate

### Strategy -> Editor
- confirm current real effect if present
- otherwise explicitly record weak or symbolic consumption

### Script -> Voice
- textual structure impacts segment pacing or delivery behavior

### Script + Strategy -> Assets
- payoff text plus strategic context can alter payoff visual evidence selection

### Assets + Voice + Script -> Editor
- Editor receives coherent upstream inputs
- final timing remains consistent with audio and text

### Editor -> QC
- QC evaluates final product outcome, not only structural metadata

### QC -> Pipeline
- `APPROVE` produces publishable result
- `HOLD` blocks publishability
- `REJECT` blocks publishability

## 7. Block D: Governance And Enforcement
### QC enforcement
- publish does not occur before QC approval
- `HOLD` blocks publishability
- `REJECT` blocks publishability
- `APPROVE` promotes correctly

### Novelty enforcement
- blocked payoff structures are avoided when saturation requires it
- blocked visual payoff categories are avoided when saturation requires it
- novelty pressure escalates with repeated approved patterns
- `variation_policy` rises when repetition requires it

### Strategy governance
- Strategy remains causal
- Strategy has not regressed back into decorative context passing

## 8. Block E: Controlled Batch
Run a small controlled batch with deliberately constructed cases.

### Required case families
- healthy baseline case
- weak-retention case
- conservative-constraint case
- fast-trend case
- repeated-pattern saturation case
- justified `HOLD` case
- justified `APPROVE` case

### Required proof
- outputs change for the correct reasons
- QC responds coherently
- the pipeline remains deterministic under controlled inputs

## 9. Block F: Repetitive Batch
Run a sequence of highly similar topics to validate repetition control.

### Required metrics
- `structural_repetition_rate`
- `visual_repetition_rate`
- `diversity_index`
- `approve_rate`
- `average_overall_score`

### Expected outcome
- repetition does not rise without control
- novelty pressure reacts
- QC does not collapse
- quality does not collapse

## 10. Block G: Small Real Batch
Run `3` to `5` real executions with real encode/render when the environment is available.

### Checklist
- valid `.mp4`
- valid audio
- valid metadata
- outputs captured for all agents
- at least one justified `APPROVE`
- any `HOLD` is understandable and justified
- no structural break in the pipeline

If real render is unavailable for environment reasons, the gate must record that explicitly instead of pretending the check passed.

## 11. Block H: Product Audit
This gate is systemic, but it still requires product-level reading.

### Sample review checklist
- hook is strong enough
- payoff is strong enough
- voice is coherent
- assets are coherent
- editor output does not regress into slideshow-like output
- captions remain legible
- atmosphere remains present
- no large perceptual regression is visible

## 12. Block I: Determinism And Stability
- same controlled input produces same strategic output
- same controlled input produces same QC decision
- batch order does not create hidden chaos beyond intended novelty memory
- no invisible drift appears across repeated controlled runs

## 13. Block J: Audit Artifacts
The gate must generate at minimum:
- `OUT/audit/pipeline_v2_full_system_validation_gate/block_summary.json`
- `OUT/audit/pipeline_v2_full_system_validation_gate/final_verdict.json`
- `OUT/audit/pipeline_v2_full_system_validation_gate/unit_test_summary.json`
- `OUT/audit/pipeline_v2_full_system_validation_gate/integration_summary.json`
- `OUT/audit/pipeline_v2_full_system_validation_gate/batch_controlled_summary.json`
- `OUT/audit/pipeline_v2_full_system_validation_gate/batch_real_summary.json`
- `OUT/audit/pipeline_v2_full_system_validation_gate/metrics.json`
- `OUT/audit/pipeline_v2_full_system_validation_gate/human_review.json`
- `OUT/audit/pipeline_v2_full_system_validation_gate/execution_examples.json`

## 14. Success Standard
### GO
Use `GO` only if:
- unit validation passes
- integration validation passes
- governance enforcement passes
- controlled batch passes
- repetitive batch passes
- real batch passes or is explicitly replaced by justified environment note plus no systemic failure
- quality does not materially regress
- repetition remains under control
- no systemic hidden failure appears

### GO_WITH_MONITORING
Use `GO_WITH_MONITORING` if:
- all primary checks pass
- only residual non-blocking known limitations remain
- examples include weak but known areas such as low Strategy effect in Editor or limited observation of natural `HOLD`/`REJECT` in small real batches

### HOLD
Use `HOLD` if any of the following occur:
- structural regression
- lost causal effect
- failed QC enforcement
- failed novelty enforcement
- product quality collapse
- uncontrolled repetition
- hidden systemic break

## 15. Final Questions The Gate Must Answer
At the end, the gate must answer clearly:
1. is pipeline v2 structurally intact?
2. do the agents still have real causal effect?
3. is the system still governed correctly?
4. is quality still high enough?
5. is repetition still controlled?
6. is there any hidden regression that should block continued operation?

## 16. Operational Principle
This gate exists to validate the current integrated system before opening another subsystem.

The principle is:
- do not open new system complexity while hidden regression risk is still unresolved
