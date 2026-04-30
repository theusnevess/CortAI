# Legacy Runtime Archive

Archived reference for superseded runtime phase, pipeline, pilot and v1/v2 gate documents.

## Consolidation Notice

This file consolidates documentation that was previously split across multiple legacy files. The source contents are preserved below for auditability.

## Source Files

- `docs/runtime/ACCOUNT_HEALTH_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/ACCOUNT_HEALTH_AGENT_HEAVY_AUDIT_CHECKLIST_v2_0.md`
- `docs/runtime/ACCOUNT_HEALTH_AGENT_STANDALONE_GOVERNANCE_DECISION_v2_0.md`
- `docs/runtime/ASSET_AGENT_DECISION_GATE_v1_0.md`
- `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_GOVERNANCE_DECISION.md`
- `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_VALIDATION_GATE.md`
- `docs/runtime/d23_first_12_hours_monitoring_map_v1_0.md`
- `docs/runtime/d23_pilot_day_go_no_go_checklist_v1_0.md`
- `docs/runtime/d23_pilot_learning_plan_v1_0.md`
- `docs/runtime/d23_pilot_operational_checklist_v1_0.md`
- `docs/runtime/d23_pilot_operator_index_v1_0.md`
- `docs/runtime/distributed_execution_v1_0.md`
- `docs/runtime/distributed_scheduler_v1_0.md`
- `docs/runtime/EXPERIMENT_CAPABILITY_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/EXPERIMENT_CAPABILITY_v2_0_GOVERNANCE_DECISION.md`
- `docs/runtime/EXPERIMENT_CAPABILITY_v2_0_VALIDATION_GATE.md`
- `docs/runtime/LEARNING_AGENT_EVOLUTION_v2_0_FULL_VALIDATION_GATE.md`
- `docs/runtime/LEARNING_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/phase1_completion_report_v1_0.md`
- `docs/runtime/phase2_5_voice_agent_definition_v1_0.md`
- `docs/runtime/phase2_5_voice_agent_file_list_v1_0.md`
- `docs/runtime/phase2_5b_kokoro_file_list_v1_0.md`
- `docs/runtime/phase2_5b_kokoro_integration_definition_v1_0.md`
- `docs/runtime/phase2_block1_file_list_v1_0.md`
- `docs/runtime/phase2_block2_definition_v1_0.md`
- `docs/runtime/phase2_block2_file_list_v1_0.md`
- `docs/runtime/phase2_block3_definition_v1_0.md`
- `docs/runtime/phase2_block3_file_list_v1_0.md`
- `docs/runtime/phase2_block4_definition_v1_0.md`
- `docs/runtime/phase2_block4_file_list_v1_0.md`
- `docs/runtime/phase2_completion_report_v1_0.md`
- `docs/runtime/phase2_definition_report_v1_0.md`
- `docs/runtime/phase2_implementation_map_v1_0.md`
- `docs/runtime/PIPELINE_FULL_SYSTEM_MASTER_CERTIFICATION_CHECKLIST_v1_0.md`
- `docs/runtime/PIPELINE_MULTIAGENT_HEAVY_AUDIT_CHECKLIST_v1_0.md`
- `docs/runtime/PIPELINE_TOTAL_HEAVY_AUDIT_CHECKLIST_v1_0.md`
- `docs/runtime/PIPELINE_V2_FULL_SYSTEM_CERTIFICATION_CHECKLIST.md`
- `docs/runtime/PIPELINE_V2_FULL_SYSTEM_VALIDATION_GATE_v1_0.md`
- `docs/runtime/pre_d23_final_release_audit_gate_v1_0.md`
- `docs/runtime/pre_d23_integration_merge_checklist_v1_0.md`
- `docs/runtime/pre_phase3_system_final_gate_v1_0.md`
- `docs/runtime/QC_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/real_batch_rollout_v1_0.md`
- `docs/runtime/SATURATION_NOVELTY_ENGINE_FULL_VALIDATION_GATE_v1_0.md`
- `docs/runtime/SATURATION_NOVELTY_ENGINE_PRODUCTION_SOAK_PLAN.md`
- `docs/runtime/SATURATION_NOVELTY_ENGINE_SYSTEM_PLAN.md`
- `docs/runtime/SATURATION_NOVELTY_ENGINE_v1_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/script_agent_excellence_gate_v1_0.md`
- `docs/runtime/SCRIPT_AGENT_PAYOFF_INTELLIGENCE_UPGRADE_PLAN.md`
- `docs/runtime/STRATEGY_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/TREND_ANALYSIS_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/TREND_ANALYSIS_AGENT_GATE_EVENT_ARTIFACT_FREEZE_v1_0.md`
- `docs/runtime/TREND_ANALYSIS_AGENT_MANUAL_CURATION_CANONICAL_FORMAT_v1_0.md`
- `docs/runtime/TREND_ANALYSIS_AGENT_POST_GATE_MONITORING_PLAN_v1_0.md`
- `docs/runtime/voice_agent_excellence_gate_v1_0.md`

## Consolidated Contents

---

## Source: `docs/runtime/ACCOUNT_HEALTH_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`

# ACCOUNT_HEALTH_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN

## 1. Objective

The objective of `Account Health Agent v2.0` is to evolve the current subsystem from:
- execution gate v1 with health semantics

into:
- account health subsystem with real input activation

The v2.0 goal is not to build a full risk intelligence engine.
The v2.0 goal is not to create a complex scoring brain.
The v2.0 goal is to activate real upstream signals while preserving the current clean governance boundary.

Target outcome for v2.0:
- Health stops operating as a mostly default-safe status emitter
- Health starts making decisions from real internal evidence already present in CortAI
- `SAFE`, `CAUTION`, and `HOLD` remain the public decision surface
- `recommended_constraints` remains stable for downstream consumers
- `HOLD` continues to block the pipeline early in the orchestrator
- the subsystem remains deterministic, auditable, and narrow in authority

## 2. Current State

Current Phase 1 state:
- Health is implemented and runtime-real
- Health is called first in the creative orchestrator
- `HOLD` is operationally enforced and stops pipeline execution
- `SAFE` and `CAUTION` allow the pipeline to proceed
- `recommended_constraints` are consumed primarily by `Strategy`
- orchestrator runtime currently passes only `account_id`
- real health telemetry is not activated
- the subsystem is mostly default-safe in nominal runtime

Current classification:
- `implemented`
- `runtime-real`
- `authoritative-but-narrow`
- `telemetry-poor`
- `operationally-sufficient`
- `not baseline-grade as a health intelligence subsystem`

v2.0 exists to fix the correct deficit:
- input activation

v2.0 does not exist to fix the wrong deficit:
- sophistication for its own sake

## 3. Boundary

This boundary must remain explicit.

### 3.1 Health
Health owns:
- precondition governance before creative generation
- account execution posture
- upstream `SAFE` / `CAUTION` / `HOLD`
- conservative pre-generation constraints
- health decision determinism and traceability

Health does not own:
- final creative direction
- trend discovery
- learning policy formation
- repetition control
- post-render publishability
- moderation enforcement beyond its own decision surface

### 3.2 Learning
Learning owns:
- what works for us
- internal performance interpretation
- policy formation from execution history
- QC-linked optimization feedback

Health may consume summarized signals derived from Learning-owned artifacts.
Health must not absorb Learning logic.

### 3.3 Strategy
Strategy owns:
- what to do with upstream context
- translation of Health + Trend + Learning + Novelty into runtime direction

Health may inject posture and constraints.
Health must not become a creative control layer.

### 3.4 QC
QC owns:
- final publishability after render
- product-level approve / hold / reject authority

Health remains upstream.
Health must not replace QC.

### 3.5 Hard boundary rule
The implementation must preserve:
- `Health = upstream precondition governor`
- `Learning = internal performance truth`
- `Strategy = control layer`
- `QC = post-render publishability governor`

Account Health v2.0 must not become a catch-all governance brain.

## 4. v2.0 Scope

Included in scope:
- activation of real internal inputs already available in CortAI
- ingestion from QC outputs
- ingestion from publish records
- ingestion from learning summaries or equivalent internal performance signals
- deterministic health aggregation
- preservation of `SAFE` / `CAUTION` / `HOLD`
- preservation of `recommended_constraints`
- explicit traceability of which signals were used
- integration without breaking current downstream consumers

Excluded from scope:
- moderation API integration
- strike/violation platform integrations
- external account telemetry systems
- opaque health scoring systems
- probabilistic or model-based health inference
- replacing QC or Learning
- downstream policy inflation across all agents

## 5. Input Activation Strategy

The core of v2.0 is input activation.

### 5.1 QC ingestion
This is the highest-value new input.

Health v2.0 should ingest summarized QC evidence such as:
- recent approve count
- recent hold count
- recent reject count
- recent average overall score
- recent publishability failure rate
- recent consecutive non-approve streak

Purpose:
- detect when the account is degrading at the product governance layer
- allow Health to react before continuing blind generation

Important constraint:
- Health should consume summarized QC evidence
- QC remains the owner of final product evaluation

### 5.2 Publish ingestion
Health v2.0 should ingest publishing activity signals such as:
- recent publish count over a bounded window
- spacing between recent publishes
- burst posting indicator
- recent delay / cooldown-adjacent indicators if already derivable from internal records

Purpose:
- make `recent_publish_count` and pacing-related signals real instead of synthetic placeholders

Important constraint:
- v2.0 should use only repository-local or runtime-local publish data already present
- do not invent external account telemetry

### 5.3 Learning ingestion
Health v2.0 should ingest narrow summarized performance risk signals from Learning-owned outputs, for example:
- recent low-performance streak
- recent quality degradation cluster signal
- contamination warning if needed

Purpose:
- activate the existing low-performance dimensions without making Health own Learning logic

Important constraint:
- Health consumes already summarized signals
- Learning still owns evidence interpretation and policy intelligence

### 5.4 Non-goal at this phase
Do not add new rich signal categories unless they are backed by real available internal data.
The correct v2.0 move is to activate existing signals first.

## 6. Contract Preservation And Evolution

v2.0 should preserve the current public decision contract.

### 6.1 Preserve decision surface
Keep:
- `SAFE`
- `CAUTION`
- `HOLD`
- `reasons`
- `recommended_constraints`
- `fallback`

This is important because downstream consumers already rely on it.

### 6.2 Preserve current downstream compatibility
The following consumers must remain compatible without rewrites:
- orchestrator `HOLD` enforcement
- `StrategyInput.health_status`
- `StrategyInput.recommended_constraints`
- `CreativePack.account_health_status`
- `CreativePack.recommended_constraints`
- script context `account_health_status`

### 6.3 Expand input contract without breaking callers
`AccountHealthInput` may grow, but must do so conservatively.

Current fields to retain:
- `account_id`
- `recent_publish_count`
- `recent_format_repetition_ratio`
- `recent_views_drop_ratio`
- `recent_low_performance_streak`

Possible v2.0 additions:
- `recent_approve_count`
- `recent_hold_count`
- `recent_reject_count`
- `recent_avg_overall_score`
- `recent_publish_spacing_hours`
- `recent_publish_burst_flag`
- `signal_trace` or equivalent derived-input visibility block

Rule:
- new fields should represent derived deterministic summaries
- do not add symbolic fields with no immediate use

### 6.4 Optional output evolution
If added, the output expansion should remain minimal.
Possible additions:
- `decision_trace`
- `input_summary_used`

These are for auditability only.
They must not break current consumers.

## 7. Data Sources And Activation Paths

### 7.1 QC source path
Likely source families already available in the repo/runtime:
- `execution_outputs.json`
- creative events with QC outcomes
- QC audit outputs when relevant

Correct activation model:
- derive bounded-window account QC summary
- feed that into Health input assembly

### 7.2 Publish source path
Likely source families already available:
- `publish_records.jsonl`
- runtime publish manifests / publish records

Correct activation model:
- compute recent publish count and spacing deterministically per account
- derive burst or pacing signals conservatively

### 7.3 Learning source path
Likely source families already available:
- learning outputs persisted by the Learning subsystem
- execution history already used by Learning

Correct activation model:
- consume only stable summarized signals
- do not have Health read raw execution history and duplicate Learning logic unless necessary as an intermediate step

### 7.4 Input assembly rule
The new runtime path should be:
- orchestrator or a dedicated health input assembler resolves real signals
- assembler builds `AccountHealthInput`
- Health service evaluates deterministically

This keeps the evaluation logic simple and keeps data activation explicit.

## 8. Decision Model Policy For v2.0

The correct v2.0 policy is:
- keep decision logic simple
- keep thresholds explicit
- keep determinism intact
- only revisit thresholds after real data is activated

### 8.1 What should remain stable initially
- `SAFE` default semantics
- `CAUTION` as degraded-but-allowed
- `HOLD` as pre-generation stop
- conservative constraint emission

### 8.2 What can evolve after data activation
Threshold tuning may be revisited only after:
- QC input is active
- publish input is active
- learning-derived low-performance input is active
- observed batch behavior is validated

### 8.3 What must not happen in v2.0
- no health score with opaque math
- no confidence system invented before evidence quality matters
- no ML or pseudo-ML health classifier
- no overfitting to one batch or one audit artifact

## 9. Orchestrator Enforcement

The current orchestrator behavior is correct and must be preserved.

### 9.1 `HOLD`
Must continue to:
- emit `CREATIVE/account_health_hold`
- stop before creative pack generation
- stop before render
- stop before QC
- return `CreativePipelineExecution` with `creative_pack=None`

### 9.2 `SAFE` and `CAUTION`
Must continue to:
- flow through trend, learning, novelty, strategy, script, voice, asset, editor, pipeline, QC
- emit account health events
- propagate status and constraints into `Strategy`

### 9.3 Constraint propagation
Must continue unchanged initially:
- `recommended_constraints` into `StrategyInput`
- `account_health_status` into script context
- persistence into `CreativePack`

This is already correct and should not be redesigned during input activation.

## 10. Determinism Requirements

Determinism is mandatory in v2.0.

The same resolved evidence must produce:
- the same `AccountHealthInput`
- the same health decision
- the same constraints
- the same reasons

To preserve this:
- use bounded deterministic aggregation windows
- avoid non-deterministic ordering of records
- avoid hidden heuristic blending
- avoid confidence systems with unstable thresholds in this phase

The correct shape is:
- explicit aggregation
- explicit thresholds
- explicit mapping from signal to decision

## 11. Traceability And Auditability

v2.0 should improve auditability, but conservatively.

Minimum target:
- make it visible which summarized inputs were used
- make it visible why `SAFE`, `CAUTION`, or `HOLD` was returned
- keep fallback explicit

Recommended minimal additions:
- `decision_trace` with triggered rules
- `input_summary_used` or equivalent serialized summary
- event payload enrichment for health decision inputs

Non-goal:
- full evidence provenance system like Trend v2.0

Health v2.0 needs better visibility, not an oversized audit framework.

## 12. Validation Path

Health v2.0 needs stronger direct validation than Phase 1, but the gate should follow implementation maturity.

### 12.1 Unit validation
Add tests proving:
- QC-derived inputs feed `CAUTION` / `HOLD` correctly
- publish-derived inputs feed constraints correctly
- learning-derived streak inputs feed `CAUTION` / `HOLD` correctly
- fallback remains explicit and deterministic

### 12.2 Integration validation
Add tests proving:
- orchestrator still blocks on `HOLD`
- `SAFE` and `CAUTION` still reach downstream execution
- Strategy still consumes propagated constraints correctly under real activated inputs

### 12.3 Controlled execution validation
Add a small deterministic battery of health scenarios such as:
- healthy account with stable QC
- degraded account with repeated holds/rejects
- bursty publish pattern
- low-performance streak from learning-derived summary
- fallback path

### 12.4 Gate timing
Do not force a standalone heavy audit gate before input activation is complete.
The correct order is:
1. activate inputs
2. validate behavior
3. then consider standalone gate/promotion

## 13. Implementation Phases

### 13.1 Phase A: Health Input Assembly Activation
Objective:
- stop feeding only `account_id`

Work:
- implement deterministic health input assembler
- read QC summaries
- read publish summaries
- read learning-derived summaries
- build real `AccountHealthInput`

Deliverable:
- orchestrator passes non-default health input values in real runtime

### 13.2 Phase B: Health Auditability Hardening
Objective:
- make the new health decisions inspectable

Work:
- add minimal decision trace
- enrich health events
- persist health input summaries where appropriate

Deliverable:
- post-run auditing can explain why the health decision happened

### 13.3 Phase C: Validation And Controlled Battery
Objective:
- prove the activated health path works and remains deterministic

Work:
- dedicated unit coverage
- integration coverage
- controlled scenario battery

Deliverable:
- evidence that Health decisions now respond to real internal signals

### 13.4 Phase D: Standalone Governance Decision
Objective:
- decide whether Health is ready for standalone promotion treatment

Work:
- assess if direct audit gate is justified
- assess if baseline promotion is appropriate or premature

Deliverable:
- explicit governance classification after v2 implementation

## 14. Risks

### Risk 1: Health starts duplicating Learning
Mitigation:
- consume summarized learning-derived inputs only
- keep Learning as the owner of performance interpretation

### Risk 2: Health starts replacing QC
Mitigation:
- keep Health strictly upstream
- keep QC as final publishability governor

### Risk 3: complexity rises without value
Mitigation:
- freeze decision logic initially
- activate data first
- tune thresholds later only if evidence justifies it

### Risk 4: opaque health scoring appears too early
Mitigation:
- prohibit magic scoring in v2.0
- require explicit threshold logic

### Risk 5: downstream contract breakage
Mitigation:
- preserve current decision/output contract
- preserve orchestrator enforcement path
- preserve Strategy consumption path

## 15. Success Criteria

Health v2.0 should be considered successful if:
- orchestrator no longer passes only `account_id`
- QC-derived signals are active
- publish-derived signals are active
- learning-derived degradation signals are active
- `SAFE` / `CAUTION` / `HOLD` remain stable
- `HOLD` still blocks early
- `recommended_constraints` still propagate cleanly
- same evidence still yields same decision
- post-run audit can explain the decision better than in Phase 1

Success does not require:
- real moderation APIs
- platform strike ingestion
- sophisticated scoring
- baseline promotion in the same step

## 16. Next Correct Move After This Plan

After this implementation plan is written, the next correct move is:
- implement `Phase A: Health Input Assembly Activation`

Reason:
- that is the highest-leverage change
- it activates the subsystem without inflating its logic
- it turns existing thresholds from mostly dormant code into real runtime behavior
- it preserves the current clean architecture while making Health materially more meaningful

## Final Implementation Position

Account Health v2.0 should be built as:
- deterministic
- input-activated
- narrow in authority
- upstream-only
- contract-stable
- audit-improved
- simple in logic

It should not be built as:
- a risk intelligence brain
- a replacement for Learning
- a replacement for QC
- a replacement for Strategy
- a scoring-heavy opaque subsystem

Final one-line target:
- `Account Health Agent v2.0` must turn Health from a mostly default-safe execution gate into a real evidence-fed upstream account governor without breaking its current boundary or deterministic behavior.


---

## Source: `docs/runtime/ACCOUNT_HEALTH_AGENT_HEAVY_AUDIT_CHECKLIST_v2_0.md`

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

## 3. Block A â€” Contract Integrity

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

## 4. Block B â€” Real Input Activation

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

## 5. Block C â€” Decision Logic Integrity

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

## 6. Block D â€” Decision Trace Auditability

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

## 7. Block E â€” Orchestrator Enforcement

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

## 8. Block F â€” Downstream Propagation

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

## 9. Block G â€” Determinism

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

## 10. Block H â€” Fallback Integrity

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

## 11. Block I â€” Boundary Integrity

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

## 12. Block J â€” Controlled Battery

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

## 13. Block K â€” Real Execution Validation

Objective:
- prove behavior outside pure unit conditions

Must prove:
- multiple real orchestrator executions
- naturally varying inputs
- coherent outputs
- no degenerate baseline behavior

Important honesty rule:
- â€œrealâ€ here means runtime-local real execution through the orchestrator using actual persisted runtime artifacts
- not hypothetical platform telemetry

## 14. Block L â€” Audit Artifacts

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

## 15. Block M â€” Baseline Behavior Stability

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


---

## Source: `docs/runtime/ACCOUNT_HEALTH_AGENT_STANDALONE_GOVERNANCE_DECISION_v2_0.md`

# ACCOUNT_HEALTH_AGENT_STANDALONE_GOVERNANCE_DECISION_v2_0

## Objective

This phase exists to decide whether `Account Health Agent v2.0` is ready for standalone governance treatment.

This is not another implementation phase.
This is not another capability expansion phase.

It is a formal decision phase that must answer:
- does `Account Health v2.0` already deserve standalone baseline treatment
- is the correct verdict `GO` or `GO_WITH_MONITORING`
- are the remaining residues methodological or blocking

## Decision Inputs

The standalone governance decision must be based on:
- the canonical Phase 1 system bible
- the v2.0 implementation plan
- Phase A input activation results
- Phase B auditability hardening results
- Phase C controlled validation artifacts
- broader pipeline certification context where Health acts as an upstream governor

Primary evidence sources:
- `docs/runtime/baselines/account-health/ACCOUNT_HEALTH_AGENT_SYSTEM_BIBLE_PHASE1.md`
- `docs/runtime/ACCOUNT_HEALTH_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `OUT/audit/account_health_agent_v2_phase_c_validation/*`
- `OUT/audit/pipeline_multiagent_heavy_audit_gate/*`
- `OUT/audit/pipeline_v2_full_system_certification/*`

## Required Questions

The decision must answer:
- `account_health_v2_implemented`
- `real_inputs_active`
- `auditability_present`
- `safe_caution_hold_governed`
- `deterministic`
- `baseline_ready`
- `main_failures`
- `residual_monitoring`

## Promotion Standard

`Account Health v2.0` should be considered promotion-ready if:
- real input activation is present
- auditability is present
- `SAFE`, `CAUTION`, and `HOLD` are operational
- `HOLD` still blocks the pipeline early
- fallback is explicit
- deterministic replay is proven
- downstream propagation to `Strategy` remains real
- no blocking failures remain

## Why `GO_WITH_MONITORING` Is Plausible

Even if the subsystem is technically sound, `GO_WITH_MONITORING` remains the correct decision when:
- telemetry richness is still narrower than a mature health intelligence subsystem
- standalone governance history is still short
- validation is strong but still concentrated in controlled batteries and indirect pipeline evidence

That is not a technical failure.
It is a governance posture.

## Why `HOLD` Would Be Required

`HOLD` is required only if:
- input activation is not real
- auditability is broken
- `SAFE` / `CAUTION` / `HOLD` are not stable
- determinism fails
- fallback is not explicit
- downstream enforcement is broken
- or standalone promotion would materially overstate the subsystem

## Expected Output Shape

The runner for this phase should emit:

```json
{
  "verdict": "GO or GO_WITH_MONITORING or HOLD",
  "baseline_ready": true,
  "main_failures": [],
  "residual_monitoring": []
}
```

It should also emit a standalone promotion verdict artifact.

## Honest Expected Outcome

Given the current state of implementation, the most plausible outcome is:
- `verdict = GO_WITH_MONITORING`
- `baseline_ready = true`

Reason:
- the subsystem is now technically real, input-activated, auditable, deterministic, and operationally governed
- but it still does not qualify as a telemetry-rich mature health intelligence layer

So the likely correct classification is:
- baseline-worthy as an upstream governor
- with short monitoring as the correct standalone governance posture


---

## Source: `docs/runtime/ASSET_AGENT_DECISION_GATE_v1_0.md`

# ASSET_AGENT_DECISION_GATE_v1_0

## A. Decision Integrity

For each segment:

- [ ] entity defined correctly
- [ ] anomaly defined
- [ ] photographability evaluated
- [ ] source decision coherent (`real` vs `ai`)
- [ ] justification present

---

## B. Narrative Alignment

- [ ] hook is specific and strong
- [ ] setup is not generic
- [ ] setup contextualizes correctly
- [ ] payoff is stronger than setup
- [ ] payoff reveals or intensifies

---

## C. Source Discipline

- [ ] REAL used as default
- [ ] AI used only when necessary
- [ ] AI does not replace adequate real assets
- [ ] source decision is explainable

---

## D. System Compatibility

- [ ] image is legible with text
- [ ] does not conflict with voice
- [ ] respects narrative rhythm
- [ ] does not overload the frame

---

## E. Visual Quality

- [ ] not generic
- [ ] not placeholder
- [ ] adequate to tone
- [ ] coherent with setting

---

## F. Fail Conditions

FAIL automatically if any:

- [ ] generic hook
- [ ] generic setup without context
- [ ] weak payoff
- [ ] AI used unnecessarily
- [ ] unexplained decision

---

## G. Final Verdict

```json
{
  "verdict": "GO | HOLD | NO-GO",
  "decision_integrity": "high | medium | low",
  "narrative_alignment": "high | medium | low",
  "source_discipline": "high | medium | low",
  "system_compatibility": "high | medium | low",
  "main_failures": []
}
```


---

## Source: `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`

# CONTENT_PERFORMANCE_ATTRIBUTION_EVOLUTION_v2_0_IMPLEMENTATION_PLAN

## 1. Objective

The objective of `Content Performance Attribution v2.0` is to evolve the current subsystem from:
- partially real post-pipeline attribution logic

into:
- a canonical, isolated, auditable attribution subsystem with bounded downstream effect

The v2.0 goal is not to claim full causal truth.
The v2.0 goal is not to reopen the frozen creative core.
The v2.0 goal is not to absorb Experiment Capability, Strategy, QC, or publish governance.

The v2.0 goal is to make attribution:
- canonical
- contract-stable
- experiment-aware
- honest under missing evidence
- deterministic where required
- operationally useful downstream without violating subsystem ownership

Target outcome for v2.0:
- one canonical attribution path exists
- the legacy analytical path has an explicit non-owning role
- required evidence inputs are fixed
- experiment-aware fields are defined cleanly
- allowed downstream effect is explicit and bounded
- missing-metrics behavior is explicit and auditable
- the subsystem becomes ready for a dedicated validation gate

## 2. Current State

Current Phase 1 state:
- `backend/app/product/attribution/` already exists
- a canonical row can be built per `publish_id`
- schema validation exists
- append-only persistence exists
- idempotent save behavior exists
- `window_post_pipeline` already wires scorecard -> attribution -> strategy learning
- strategy learning already consumes attribution rows behaviorally

At the same time:
- `backend/app/attribution/` still exists as a parallel analytical path
- canonical ownership is not yet declared
- experiment-aware fields are not formalized on the product path
- required evidence is not yet declared as a subsystem contract
- missing-evidence honesty is partly runtime-real but not yet fully specified as subsystem policy
- validation and governance artifacts do not yet exist

Current classification:
- implemented: yes
- runtime-real: yes, in post-pipeline flow
- canonicalized: no
- governance-closed: no
- experiment-aware in canonical contract: not yet fully
- downstream effect: real but still loosely bounded at subsystem-definition level

## 3. Core Diagnosis

The core diagnosis is:

```json
{
  "content_performance_attribution_v1": {
    "real_code_exists": true,
    "post_pipeline_wiring_exists": true,
    "append_only_persistence_exists": true,
    "downstream_effect_exists": true,
    "canonical_root_frozen": false,
    "legacy_boundary_explicit": false,
    "required_evidence_fixed": false,
    "experiment_aware_contract_complete": false,
    "honesty_policy_complete": false,
    "validation_ready": false
  }
}
```

Brutally honest translation:
- the subsystem is already useful
- but its operating surface is not yet fully crystallized

The exact deficit is not absence of implementation.
The exact deficit is absence of canonicalization and operational definition.

So v2.0 must fix:
- canonical root
- boundary clarity
- contract clarity
- evidence clarity
- allowed-effect clarity
- honesty clarity

before:
- validation gate
- governance decision
- registry inclusion

## 4. Boundary

This boundary must remain explicit.

### 4.1 Content Performance Attribution owns

Content Performance Attribution owns:
- canonical outcome attribution records
- normalization of selected performance signals into a stable contract
- experiment-aware linkage fields where experiment evidence already exists
- honest representation of missing or unavailable evidence
- packaging of attribution evidence for approved downstream consumers

### 4.2 Content Performance Attribution does not own

Content Performance Attribution does not own:
- strategy policy
- strategy patch governance
- experiment assignment
- experiment result recording ownership
- publish decisions
- QC authority
- content generation
- direct mutation of frozen baseline agents

### 4.3 Relationship to Strategy Learning

Strategy Learning may consume attribution outputs.
Attribution does not own:
- patch activation policy
- strategy override policy
- rollout authority

Attribution may provide evidence.
It may not become a hidden strategy controller.

### 4.4 Relationship to Experiment Capability

Experiment Capability owns:
- assignment lifecycle
- result lifecycle
- variant governance

Attribution may consume:
- experiment identity
- variant identity
- assignment/result metadata already persisted elsewhere

Attribution must not:
- synthesize fake experiment ownership
- infer assignment that the experiment subsystem did not record
- create a parallel experiment ledger

### 4.5 Hard boundary rule

The subsystem must remain:
- post-pipeline attribution and evidence packaging

It must not become:
- a general causal optimizer
- a replacement for the experiment subsystem
- a replacement for learning governance

## 5. Canonical Root Decision

The canonical subsystem root for v2.0 must be:
- `backend/app/product/attribution/`

Why this is the correct root:
- it already has a canonical record builder
- it already has schema validation
- it already has append-only persistence
- it already sits on the product/post-pipeline path
- it already feeds a real downstream consumer

The legacy analytical path:
- `backend/app/attribution/`

must be classified as:
- supporting analytical infrastructure
not:
- the subsystem root for governance

Required v2.0 decision:
- all subsystem governance, contract definition, validation, and runtime claims should anchor on `backend/app/product/attribution/`

## 6. Legacy Boundary Policy

The boundary between the two attribution tracks must be made explicit.

### 6.1 `backend/app/product/attribution/`

This path should own:
- canonical record schema
- canonical record builder
- persistence contract
- post-pipeline attribution write path
- downstream learning-facing output

### 6.2 `backend/app/attribution/`

This path may remain for:
- exploratory analytics
- secondary summaries
- research-oriented decomposition
- experiment-aware descriptive analysis

It should not be treated as:
- the canonical contract source
- the governance root
- the required write path for v2.0 subsystem correctness

### 6.3 Required repo posture

v2.0 should make it impossible to be confused about:
- which path is canonical
- which path is optional/supporting

If both paths remain active without an explicit boundary, governance will remain ambiguous.

## 7. Required Evidence Set

This is the first core pillar of v2.0.

Attribution should not accept arbitrary evidence shape.
It should operate on a fixed required evidence set plus explicit optional enrichments.

### 7.1 Required evidence

The canonical builder must require:
- publish record
- video metrics
- window metrics

These are the minimum needed to say the subsystem has observed:
- what was published
- how it performed
- under which window context it is being evaluated

### 7.2 Conditionally required evidence

`scorecard` remains conditional.

Rule:
- if scorecard exists, attribution may consume it
- if scorecard does not exist, attribution must still behave honestly and deterministically

### 7.3 Required evidence policy

The implementation plan should enforce:
- missing publish record -> hard failure
- missing video metrics -> explicit attribution skip/failure path
- missing window metrics -> explicit attribution skip/failure path
- missing optional scorecard -> allowed, with honest reduced-evidence behavior

### 7.4 Evidence auditability

Each attribution row or attribution result wrapper should make clear:
- which evidence was present
- which evidence was missing
- whether the record is canonical-complete or reduced-evidence

This does not require exaggerated complexity.
It requires explicitness.

## 8. Canonical Contract Plan

This is the second core pillar of v2.0.

The canonical record already has a good base.
v2.0 exists to freeze the final minimum contract needed for Phase 3 validation.

### 8.1 Required base fields

The base contract should continue to require:
- `attribution_id`
- `account_id`
- `publish_id`
- `video_id`
- `job_id`
- `window_id`
- `policy_stage`
- `hook_strategy`
- `human_patch_detected`
- `views`
- `retention_3s`
- `completion_rate`
- `captured_at`
- `generated_at`

### 8.2 Allowed optional base enrichments

The following remain valid optional enrichments:
- `dominant_failure_reason`
- `effective_duration_s`
- `rare_fact_placement_s`
- `likes`
- `follows`
- `rpm`

### 8.3 Contract design rule

The contract should favor:
- stable narrow fields with strong meaning

not:
- premature giant creative ontologies

The subsystem needs a strong base contract first.
Broader decomposition can come later if it remains auditable and deterministic.

## 9. Experiment-Aware Contract Plan

This is the third core pillar of v2.0.

The subsystem must become experiment-aware without invading Experiment Capability ownership.

### 9.1 Required ownership-safe principle

Attribution may only carry experiment metadata that was already produced by the experiment subsystem or canonical runtime records.

It must not:
- infer or invent assignment identities
- decide experiment eligibility
- fabricate variant lineage

### 9.2 Recommended experiment-aware fields

Recommended additions or wrapper-level fields:
- `experiment_id`
- `variant_id`
- `assignment_id` when available
- `experiment_result_available`
- `experiment_linkage_status`

Recommended linkage status values:
- `LINKED`
- `NOT_PRESENT`
- `MISSING_ASSIGNMENT`
- `MISSING_RESULT`
- `UNSAFE_TO_INFER`

### 9.3 Experiment-aware contract rule

If experiment evidence is absent:
- attribution must say so explicitly

If experiment evidence is partially present:
- attribution must preserve the partial state honestly

If experiment evidence is fully present:
- attribution may carry linkage metadata for downstream explanation

### 9.4 Ownership preservation

Even when experiment fields are present, Attribution still does not own:
- the truth of assignment
- the truth of result recording
- the truth of experiment envelope

It only owns:
- linking existing experiment evidence to observed content outcome records

## 10. Honest Missing-Metrics Policy

This is the fourth core pillar of v2.0.

Attribution must be explicitly honest when evidence is incomplete.
Silent fabrication is unacceptable.

### 10.1 Mandatory honesty scenarios

The subsystem must define explicit behavior for:
- publish record missing
- video metrics missing
- window metrics missing
- scorecard missing
- experiment linkage missing
- malformed metadata needed for optional enrichments

### 10.2 Required behavior

Recommended policy:

- missing publish record:
  - hard error
  - no attribution record generated

- missing video metrics:
  - explicit skipped/error attribution result
  - no false normalized record

- missing window metrics:
  - explicit skipped/error attribution result
  - no false canonical-complete record

- missing scorecard:
  - allowed reduced-evidence mode
  - record remains possible

- missing experiment linkage:
  - allowed
  - explicit `experiment_linkage_status`

- malformed optional metadata:
  - optional fields degrade to `null`
  - base contract remains valid when possible

### 10.3 Honesty artifact requirement

The write path should produce enough visibility to prove:
- why attribution was written
- why attribution was skipped
- why enrichment fields were absent

This is necessary for the future validation gate.

## 11. Allowed Downstream Effect

This is the fifth core pillar of v2.0.

The subsystem must have downstream effect.
That effect must also be bounded.

### 11.1 Allowed downstream consumers

Allowed v2.0 consumers:
- `backend/app/product/strategy_learning/`
- reporting/audit layers
- future validation runners

### 11.2 Allowed downstream effect

Allowed effect:
- evidence supply to deterministic strategy-learning logic
- descriptive analysis outputs
- audit summaries

### 11.3 Disallowed downstream effect

Disallowed effect:
- direct mutation of frozen strategy runtime without approved learning interface
- direct publish blocking
- direct QC override
- direct orchestrator control
- direct experimental assignment control

### 11.4 Enforcement principle

Attribution may influence the system only through approved consuming layers.
It may not become a hidden command channel.

## 12. Determinism And Idempotency Plan

The subsystem should remain deterministic under fixed evidence.

Required v2.0 properties:
- same evidence -> same canonical attribution row
- same `publish_id` -> idempotent persistence behavior
- optional enrichment absence -> explicit stable output, not random omission
- linkage states -> stable enumerations

This is already partly true.
v2.0 must make it a declared subsystem property.

## 13. Output Surfaces

v2.0 should define the output surfaces clearly.

### 13.1 Canonical persisted row

Primary output:
- canonical attribution record persisted through `backend/app/product/attribution/`

### 13.2 Result wrapper

Recommended write-path wrapper fields:
- `status`
- `reason_code`
- `record_written`
- `evidence_summary`
- `experiment_linkage_status`

This wrapper is useful because validation should assess both:
- record correctness
- honesty of the write decision

### 13.3 Optional analytical summaries

Analytical summaries may still exist.
They should be explicitly classified as:
- non-canonical support outputs

## 14. Implementation Phases

The implementation should be executed in narrow phases.

### 14.1 Phase A: Canonicalization And Boundary Freeze

Objective:
- make the canonical subsystem root and legacy boundary explicit

Required work:
- document `backend/app/product/attribution/` as canonical root
- document `backend/app/attribution/` as supporting analytical path
- remove ambiguity in comments, docs, and runtime references where needed
- define the final ownership statement for the subsystem

Phase A success condition:
- a reader can tell immediately which path is canonical and which path is not

### 14.2 Phase B: Contract And Evidence Hardening

Objective:
- finalize the canonical contract and required evidence set

Required work:
- freeze required base fields
- formalize optional enrichments
- formalize required evidence vs optional evidence
- add explicit evidence-presence reporting in the result surface where needed
- ensure missing-evidence behavior is explicit

Phase B success condition:
- the subsystem has a stable minimum contract and a declared honesty policy

### 14.3 Phase C: Experiment-Aware Linkage Activation

Objective:
- add ownership-safe experiment-aware linkage on the canonical path

Required work:
- define safe experiment-aware fields
- wire those fields only from canonical experiment/runtime records
- add explicit linkage-state reporting
- ensure no fake experiment ownership is introduced

Phase C success condition:
- attribution can represent experiment linkage honestly without becoming the experiment subsystem

### 14.4 Phase D: Downstream Effect Hardening

Objective:
- prove that attribution has bounded but real downstream effect

Required work:
- verify strategy-learning consumption on the canonical path
- ensure allowed effect remains bounded to approved consumers
- expose enough audit visibility to show what attribution influenced downstream

Phase D success condition:
- the subsystem has real but bounded effect that can be validated later

## 15. Explicit Non-Goals

v2.0 will not:
- solve full creative causal attribution
- decompose every content factor with strong confidence
- replace experiment result recording
- redesign strategy learning broadly
- redesign the frozen creative orchestrator
- add direct governance authority over publishability
- force registry/governance inclusion before validation exists

These non-goals matter because this phase should stay executable.

## 16. Validation Readiness Criteria

The subsystem will be ready for a dedicated validation gate only after:
- canonical root is explicit
- legacy boundary is explicit
- required evidence set is fixed
- missing-metrics honesty policy is implemented
- experiment-aware fields are ownership-safe and runtime-real
- allowed downstream effect is explicit and observable
- deterministic/idempotent behavior is demonstrated

Only after that should the repo add:
- `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_VALIDATION_GATE.md`

## 17. Governance Readiness Criteria

Governance should happen only after a clean validation artifact set exists.

The governance decision should answer:
- is the canonical path operationally real
- is the honesty model reliable
- is experiment linkage clean
- is downstream effect real but bounded
- is the subsystem stable enough to freeze

Only after those answers exist should the repo add:
- subsystem governance decision
- registry classification

## 18. Immediate Next Step

The immediate next step after this plan is:
- implement `Phase A: Canonicalization And Boundary Freeze`

That is the correct first move because validation is still premature until:
- canonical ownership is fixed
- the subsystem surface is operationally defined

## 19. Final Verdict

`Content Performance Attribution v2.0` should proceed now as a Phase 3 implementation track.

The correct sequence is:
1. implementation plan
2. phased implementation
3. validation gate
4. governance decision
5. registry inclusion

Most accurate verdict:
- `approved for implementation definition`
not:
- `approved for baseline governance`


---

## Source: `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_GOVERNANCE_DECISION.md`

# CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_GOVERNANCE_DECISION

## Objective

This phase exists to decide whether `Content Performance Attribution v2.0` is ready for governance classification after formal validation.

This is not another implementation phase.
This is not another capability expansion phase.

It is a formal decision phase that must answer:
- is `Content Performance Attribution v2.0` now a real subsystem in the frozen runtime architecture
- is the correct verdict `GO`, `GO_WITH_MONITORING`, or `HOLD`
- are the remaining residues blocking or only governance-related

## Decision Inputs

The governance decision must be based on:
- the Phase 1 system bible
- the v2.0 implementation plan
- the formal validation gate artifacts
- the broader frozen runtime context where the subsystem now exists as an isolated Phase 3 addition

Primary evidence sources:
- `docs/runtime/baselines/attribution/CONTENT_PERFORMANCE_ATTRIBUTION_SYSTEM_BIBLE_PHASE1.md`
- `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_VALIDATION_GATE.md`
- `OUT/audit/content_performance_attribution_v2_0_validation/combined_outputs.json`
- `OUT/audit/pipeline_full_master_certification/combined_outputs.json`

## Required Questions

The decision must answer:
- `canonical_path_active`
- `legacy_path_bounded`
- `contract_hardened`
- `required_evidence_explicit`
- `honest_written_vs_skipped`
- `experiment_linkage_safe`
- `unsafe_inference_blocked`
- `bounded_downstream_effect_proven`
- `deterministic`
- `ownership_preserved`
- `baseline_ready`
- `main_failures`
- `residual_monitoring`

## Promotion Standard

`Content Performance Attribution v2.0` should be considered governance-ready if:
- the canonical path is explicit
- the legacy path is bounded
- the contract is hardened
- required evidence is explicit
- `WRITTEN` vs `SKIPPED` remains honest
- experiment-aware linkage is explicit and safe
- unsafe inference is blocked
- bounded downstream effect is proven
- determinism and idempotency are preserved
- no ownership boundary violation remains in the formal gate

## Why `GO_WITH_MONITORING` Is Correct

Even with a clean `GO` validation gate, `GO_WITH_MONITORING` remains the correct governance verdict when:
- the subsystem is newly formalized as a canonical Phase 3 subsystem
- operational history is still short
- bounded downstream behavior is validated mainly under controlled proofs rather than long-horizon production diversity
- experiment-aware linkage is now safe, but real production linkage variety is still recent
- the subsystem is technically mature enough to activate but not yet mature enough for unmonitored baseline finality

That is not a technical deficiency.
It is the correct governance posture.

## Why Direct Unmonitored Baseline Promotion Is Too Early

Direct promotion to an unmonitored baseline would overstate the subsystem today because:
- the subsystem has only just completed its canonicalization and validation sequence
- the strongest evidence is still controlled and recent
- real production variety for attribution inputs and linkage patterns is still narrower than a mature subsystem should eventually see

So the correct reading is:
- technically validated
- operationally real
- governance-ready only with monitoring

## Why `HOLD` Is Not Correct

`HOLD` would be required only if any of the following were true:
- canonical ownership were still ambiguous
- missing required evidence still wrote false canonical records
- unsafe inference were observed
- downstream effect were fake or unbounded
- experiment-aware linkage violated ownership
- determinism failed

That is not the current state.

The gate proved:
- `verdict = GO`
- all validation blocks passed
- `bounded_downstream_effect_proven = true`
- `unsafe_inference_blocked = true`
- `main_failures = []`

So `HOLD` would now be technically indefensible.

## Current Classification

Most honest classification:

```json
{
  "content_performance_attribution_v2": {
    "implementation": "DONE",
    "canonical_root": "FROZEN",
    "contract": "HARDENED",
    "evidence_model": "EXPLICIT",
    "experiment_linkage": "LIMITED_AND_SAFE",
    "downstream_effect": "REAL_BUT_BOUNDED",
    "determinism": "PROVEN",
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
  "canonical_path_active": true,
  "legacy_path_bounded": true,
  "contract_hardened": true,
  "required_evidence_explicit": true,
  "honest_written_vs_skipped": true,
  "experiment_linkage_safe": true,
  "unsafe_inference_blocked": true,
  "bounded_downstream_effect_proven": true,
  "deterministic": true,
  "ownership_preserved": true,
  "baseline_ready": true,
  "main_failures": [],
  "residual_monitoring": [
    "ATTRIBUTION_RUNTIME_HISTORY_STILL_SHORT",
    "CONTROLLED_VALIDATION_DOMINANT_OVER_LONG_HORIZON_RUNTIME",
    "REAL_PRODUCTION_LINKAGE_VARIETY_STILL_UNDER_MONITORING"
  ],
  "baseline_status": "ACTIVE_WITH_MONITORING",
  "promotion_decision": "PROMOTE_TO_BASELINE_WITH_MONITORING",
  "next_action": "freeze_content_performance_attribution_v2_and_monitor"
}
```

## Operational Meaning

This means:
- the subsystem is no longer just a promising Phase 3 candidate
- it is now a real canonical subsystem with validated bounded effect
- it may remain active in the frozen architecture as an isolated governed subsystem
- changes should now be conservative and governance-driven

It does not mean:
- broad redesign is justified
- strong causal attribution is already solved
- the subsystem should absorb Experiment Capability or Strategy ownership
- the subsystem should expand into a wider policy engine now

## Monitoring Focus

Monitoring should focus on:
- real attribution write continuity
- real skip-rate under missing metrics
- experiment linkage status distribution in production-like use
- absence of unsafe inference attempts
- bounded downstream patch patterns over time
- absence of ownership drift into Strategy or Experiment Capability

## One-Line Decision

`Content Performance Attribution v2.0` is technically validated and governance-ready, but the correct classification today is `GO_WITH_MONITORING` and `PROMOTE_TO_BASELINE_WITH_MONITORING`, not immediate unmonitored baseline finality.


---

## Source: `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_VALIDATION_GATE.md`

# CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_VALIDATION_GATE

## 1. Objective
Prove that `Content Performance Attribution v2.0` is now a real, canonical, bounded subsystem rather than a loose analytical helper.

This gate must answer:
1. is `backend/app/product/attribution/` the active canonical path?
2. is `backend/app/attribution/` explicitly non-canonical for subsystem governance?
3. is the canonical contract hardened and stable?
4. is the required evidence set explicit and enforced?
5. does the write path distinguish `WRITTEN` vs `SKIPPED` honestly?
6. is experiment-aware linkage limited, explicit, and safe?
7. is unsafe inference blocked?
8. is downstream effect real but bounded?
9. are determinism and idempotency preserved?
10. is ownership preserved relative to Experiment Capability, Strategy, and the frozen core?

## 2. Scope
### Included
- `backend/app/product/attribution/`
- canonical record contract
- canonical write path
- evidence-summary behavior
- missing-metrics honesty
- experiment-aware linkage behavior
- bounded integration with `backend/app/product/strategy_learning/`
- Phase A through Phase D evidence

### Out of scope
- full multi-factor causal attribution
- strategy redesign
- experiment assignment ownership
- experiment result ownership
- QC governance
- publish governance
- core pipeline redesign
- governance decision itself

## 3. Block A: Canonical Root And Legacy Boundary
The gate must prove:
- `app.product.attribution` is the canonical subsystem root
- `app.attribution` is explicitly legacy analytical support
- docs and code do not leave canonical ownership ambiguous

## 4. Block B: Canonical Contract And Evidence Hardening
The gate must prove:
- required base fields are explicit
- optional enrichment fields are explicit
- required evidence inputs are explicit
- optional evidence inputs are explicit
- scorecard remains optional without corrupting the base record

## 5. Block C: Honest Write Path
The gate must prove:
- valid required evidence yields `WRITTEN`
- missing required metrics yields honest `SKIPPED`
- no false canonical record is written when required evidence is missing
- evidence summary reflects what was present vs absent

## 6. Block D: Safe Experiment-Aware Linkage
The gate must prove:
- experiment linkage is accepted only from explicit metadata
- explicit IDs can link to canonical assignment/result records
- missing assignment/result is represented honestly
- `creative_pack_id` alone does not authorize linkage
- no unsafe inference path is used

## 7. Block E: Determinism And Idempotency
The gate must prove:
- same evidence -> same canonical attribution record
- same `publish_id` + same payload -> idempotent persistence
- different payload for same `publish_id` -> conflict, not silent overwrite
- experiment linkage statuses remain stable under replay

## 8. Block F: Bounded Downstream Effect
The gate must prove:
- valid attribution rows can influence `strategy_learning`
- influence remains within the allowed override envelope
- missing attribution does not generate a false downstream patch
- experiment linkage presence does not mutate downstream ownership

## 9. Block G: Ownership Preservation
The gate must prove:
- attribution does not own experiment assignment
- attribution does not own experiment result recording
- attribution does not directly mutate Strategy runtime
- attribution does not affect publishability or QC authority
- the frozen core pipeline remains unopened

## 10. Required Artifacts
The gate must generate:
- `OUT/audit/content_performance_attribution_v2_0_validation/final_verdict.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/block_summary.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/decision_examples.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/execution_batch.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/metrics.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/human_review.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/event_summary.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/combined_outputs.json`

## 11. Success Standard
### `GO`
Use only if:
- all required blocks pass
- canonical path is explicit
- contract/evidence behavior is explicit
- missing-metrics honesty is preserved
- experiment-aware linkage is safe
- downstream effect is real and bounded
- determinism/idempotency hold
- no ownership boundary violation is introduced

### `GO_WITH_MONITORING`
Use only if:
- all technical blocks pass
- one non-blocking operational limitation remains
- the subsystem is validation-ready but still early in production diversity

### `HOLD`
Use if any of the following happen:
- canonical ownership remains ambiguous
- missing required evidence still writes a false record
- unsafe inference is observed
- linkage invades experiment ownership
- downstream effect cannot be shown
- downstream effect exceeds the allowed envelope
- determinism/idempotency fail

## 12. Final Question
At the end of the gate, the subsystem must answer:

```json
{
  "canonical_path_active": true,
  "legacy_path_bounded": true,
  "contract_hardened": true,
  "required_evidence_explicit": true,
  "honest_written_vs_skipped": true,
  "experiment_linkage_safe": true,
  "unsafe_inference_blocked": true,
  "bounded_downstream_effect_proven": true,
  "deterministic": true,
  "ownership_preserved": true,
  "promotion_ready": false
}
```

`promotion_ready` remains `false` until the subsystem is reviewed under a dedicated governance decision with monitored operational context.


---

## Source: `docs/runtime/d23_first_12_hours_monitoring_map_v1_0.md`

# CortAI - First 12 Hours Monitoring Map

Versao: `v1.0`
Aplica-se a: `CortAI >= D33`
Uso: monitoramento intensivo apos inicio do piloto D23

## Objetivo

- detectar risco de conta cedo
- confirmar funcionamento do pipeline real
- validar coleta de metricas
- observar sinais iniciais de aprendizado

## T+10 minutos - checkpoint critico

Confirmar imediatamente apos o primeiro publish:

- [ ] `publish_record` escrito
- [ ] evento `CONTENT/publish_completed` emitido
- [ ] ausencia de `SAFETY/publish_blocked`

Arquivos esperados:

- `OUT/data/publish_records.jsonl`
- `OUT/content/video/<render_job_id>.mp4`

Se falhar:

- [ ] abrir incidente operacional
- [ ] nao esperar T+30

## T+30 minutos

Confirmar integridade do loop.

Pipeline:

- [ ] proxima task agendada
- [ ] workers ativos

Eventos esperados:

- `CONTENT/*`
- `SAFETY/*`

## T+60 minutos - checkpoint de metricas

Confirmar ingestao inicial.

Arquivo:

- `OUT/metrics/video_metrics.jsonl`

Criterio congelado:

- se nenhuma linha aparecer ate `T+60 min` -> abrir incidente operacional

Isso indica problema em:

- metrics collector
- platform API
- persistencia

## 1-3 horas

Agora observar sinais de seguranca e estabilidade.

Verificar eventos:

- `SAFETY/pacing_delay`
- `SAFETY/risk_detected`

Esses sao normais.

Alerta se aparecer:

- `SAFETY/publish_blocked`

## 3-6 horas

Primeiros sinais de performance.

### Sistema vivo

- `views > 0`
- `watch_time > 0`

Significa:

- conteudo indexado
- pipeline funcional

### Sinal inicial bom

- `completion_rate > 20%`

Nao e obrigatorio no piloto, mas e bom indicador.

## 6-12 horas

Confirmar aprendizado do sistema.

Arquivos esperados:

- `OUT/experiments/`
- `OUT/intelligence/`
- `OUT/attribution/`

Isso valida:

- D30 intelligence
- D31 experiments
- D32 attribution

## Sinais de risco precoce

Abortar piloto se ocorrer:

- `ACCOUNT_RESTRICTED`
- `REPEATED_PUBLISH_REJECTED`
- `RATE_LIMIT` em multiplas contas
- `COOLDOWN > 24h`

Procedimento:

- acionar `kill switch rollout`

## Artefatos esperados ate T+12h

Confirmar presenca de:

- `OUT/content/`
- `OUT/metrics/video_metrics.jsonl`
- `OUT/experiments/`
- `OUT/intelligence/`
- `OUT/attribution/`
- `OUT/safety/`

## Criterio de piloto saudavel nas primeiras 12h

Confirmar:

- pipeline executou
- publicacao real ocorreu
- metricas chegaram
- experimentos distribuiram
- safety nao bloqueou contas

Se todos verdadeiros:

- piloto esta saudavel

## Resumo

Esse mapa existe para responder:

`Nas primeiras 12 horas, o piloto esta vivo, seguro e produzindo aprendizado?`


---

## Source: `docs/runtime/d23_pilot_day_go_no_go_checklist_v1_0.md`

# CortAI - Pilot Day GO / NO-GO Checklist

Versao: `v1.0`
Aplica-se a: `CortAI >= D33`
Uso: imediatamente antes de iniciar o piloto de 72h

## 1. Contas

- [ ] 3 contas aquecidas e elegiveis
- [ ] nenhuma conta com warning recente
- [ ] nenhuma conta em cooldown
- [ ] login funcional nas 3 contas

NO-GO se:

- menos de 3 contas elegiveis
- qualquer conta em cooldown

## 2. Sistema CortAI

Endpoints:

- `GET /health` -> `200`
- `GET /ready` -> `ready=true`

Payload esperado:

- `ready: true`
- `scheduler: ok`
- `workers >= 1`
- `queue: ok`
- `event_index: ok`
- `hot_store: ok`

NO-GO se:

- `/ready != 200`
- `ready=false`
- `queue != ok`

## 3. Pipeline de Conteudo

Dry-run minimo executado:

- [ ] `creative_pack` gerado
- [ ] render executado
- [ ] publish adapter respondeu
- [ ] `publish_record` persistido

NO-GO se:

- render falhar
- `publish_record` nao persistir

## 4. Safety Layer

Teste rapido executado:

- [ ] pacing violation simulado -> `DELAY`
- [ ] cooldown simulado -> `BLOCK`

NO-GO se:

- `safety_gate` nao interferir no publish

## 5. Metrics Collector

- [ ] worker ativo
- [ ] coleta agendada
- [ ] primeira coleta confirmada para 1 publish de teste

Arquivo esperado:

- `OUT/metrics/video_metrics.jsonl`

NO-GO se:

- metricas nao persistirem apos teste

## 6. Experiments

- [ ] experiment framework ativo
- [ ] variantes atribuidas
- [ ] experiment assignments persistidos

## 7. Observabilidade

Eventos esperados:

- `CONTENT/*`
- `SAFETY/*`
- `METRICS/*`

- [ ] console operacional visivel
- [ ] alertas configurados

## 8. Parametros do Piloto

Configuracao inicial:

- `accounts: 3`
- `posts_per_account_per_day: 2`
- `duration: 72h`
- `total_expected_posts: 12-18`

Pacing:

- `min_interval_between_posts: 120 min`
- `jitter: +-5-8 min`

## 9. Kill Switch

Teste obrigatorio:

- [ ] kill switch acionado em ambiente de teste
- [ ] novas tasks nao sao enfileiradas
- [ ] workers nao iniciam novos publishes apos o switch

## 10. Decisao Final

Se todas as caixas estiverem marcadas:

`GO`

Iniciar piloto D23.

## Condicoes de Abort

Abortar imediatamente se ocorrer:

- `ACCOUNT_RESTRICTED`
- `RATE_LIMIT` em multiplas contas
- `COOLDOWN > 24h`
- erro persistente de publish

Procedimento:

- acionar `kill switch rollout`

## Resumo

Esse checklist existe para responder apenas uma pergunta:

`Podemos iniciar o piloto agora sem risco operacional desnecessario?`


---

## Source: `docs/runtime/d23_pilot_learning_plan_v1_0.md`

# CortAI - Pilot Learning Plan

Versao: `v1.0`
Aplica-se a: `CortAI >= D33`
Pilot stage: `D23`
Uso: planejar os primeiros 12-18 videos do piloto real para maximizar aprendizado e minimizar desperdicio

## Objetivo do piloto

Nao e viralizar. E:

- validar o loop real
- gerar sinais comparaveis
- descobrir o que funciona melhor
- evitar desperdiçar posts

## Tamanho do piloto

- `3` contas
- `4-6` videos por conta
- `12-18` videos no total
- `72h`

## Regra central

Em cada video, mude uma variavel principal.
O resto fica o mais estavel possivel.

## 1. Distribuicao dos 12-18 videos

### Estrutura recomendada

Por conta:

- Videos `1-2`: teste de hook
- Videos `3-4`: teste de estrutura
- Videos `5-6`: teste de duracao

Se fizer `4` videos por conta:

- `2` hooks
- `2` estruturas

Se fizer `6`:

- hooks + estruturas + duracao

### Exemplo por conta

#### Conta A

- `V1`: Hook A
- `V2`: Hook B
- `V3`: Estrutura A
- `V4`: Estrutura B
- `V5`: Curto
- `V6`: Medio

#### Conta B

- inverter a ordem para reduzir vies de sequencia

#### Conta C

- manter balanceado e repetir os melhores pares

## 2. Variaveis para experimentar

### Prioridade 1

Hook:

- pergunta
- afirmacao forte
- curiosidade/suspense

### Prioridade 2

Estrutura narrativa:

- linear
- suspense com payoff tardio

### Prioridade 3

Duracao:

- curta: `8-12s`
- media: `15-20s`

### Prioridade 4

Janela de publicacao:

- so se o pacing estiver estavel

## 3. Variaveis que devem ficar fixas

No piloto, manter estavel:

- macro-nicho
- identidade visual
- formato `9:16`
- voz/narracao
- CTA
- ritmo visual base
- volume por dia

Isso evita ruido.

## 4. Desenho experimental minimo

### Regra

Nao testar tudo ao mesmo tempo.

### Ordem recomendada

#### Fase 1 - Hook

- mesmos tema, duracao e estrutura
- muda so a abertura

#### Fase 2 - Estrutura

- mesmo tema, mesma duracao
- muda so a ordem narrativa

#### Fase 3 - Duracao

- mesmo tema e hook
- muda so o tamanho

## 5. Sinais esperados nas primeiras 72h

### Sistema vivo

- `views > 0`
- `watch_time > 0`

### Sinal inicial bom

- `completion_rate > 15%`

### Sinal muito bom

- `completion_rate > 25-30%`

### Sinal fraco, mas util

- pequena diferenca consistente entre variante A e B

O piloto nao precisa de numeros grandes para ensinar algo.

## 6. Como interpretar sinais fracos

Nao confundir:

- poucas views com nenhum aprendizado

Mesmo com baixo alcance, voce ainda pode comparar:

- A vs B dentro da mesma conta
- videos com mesmo tema
- retencao relativa

### Leitura correta

Se:

- Hook B tem completion maior que Hook A em `2` contas
- mesmo com views baixas

isso ja e sinal util.

## 7. Metricas que importam de verdade

### Mais importantes

1. `completion_rate`
2. `avg_watch_time`
3. `3s_view_rate`

### Importantes, mas secundarias

4. `likes`
5. `shares`
6. `comments`

### Menos importantes no piloto

- views absolutas

Views sao uteis, mas no piloto elas sao mais ruido que verdade.

## 8. O que define aprendizado util vs ruido

### Aprendizado util

- diferenca repetida em mais de 1 conta
- diferenca aparece em mais de 1 video
- diferenca alinhada com hook/estrutura/duracao

### Ruido

- um video isolado performou melhor
- diferenca pequena sem repeticao
- comparacao entre videos com muitas variaveis mudando

## 9. Erros comuns de interpretacao

### Erro 1

`Video com mais views e automaticamente melhor.`

Nem sempre. As vezes o hook abriu bem, mas a retencao foi pior.

### Erro 2

`Mudar hook, duracao e estrutura no mesmo teste.`

Ai voce nao aprende nada claro.

### Erro 3

`Abandonar variante cedo demais.`

No piloto, `2-3` repeticoes sao melhores que uma conclusao apressada.

## 10. Criterio pratico de leitura por janela

Ao final de `72h`, responder:

1. Qual tipo de hook teve melhor completion?
2. Qual estrutura segurou mais watch time?
3. Curto ou medio performou melhor?
4. Houve sinais de risco por conta?
5. Alguma combinacao parece vencedora?

Se essas `5` respostas existirem, o piloto ja valeu.

## 11. Plano operacional recomendado

### Dia 1

- primeiro bloco de hooks
- pacing conservador
- foco em estabilidade

### Dia 2

- segundo bloco de estruturas
- manter tema estavel

### Dia 3

- bloco de duracao
- repetir o que deu melhor sinal inicial

## 12. Resultado esperado do piloto

Ao final, voce deve sair com:

- `1` ou `2` hooks promissores
- `1` estrutura melhor
- `1` faixa de duracao preferivel
- `1` leitura inicial de risco por conta
- dados suficientes para `D30`, `D31` e `D32` aprenderem

## Resumo executivo

O piloto deve ser tratado como:

- baixo risco
- baixo volume
- alta comparabilidade
- alta utilidade de aprendizado


---

## Source: `docs/runtime/d23_pilot_operational_checklist_v1_0.md`

# CortAI - Piloto Real D23

## Operational Checklist v1.0

Applies to:
- `CortAI >= D32`
- `Pilot stage: D23`
- `Accounts required: 3 warmed accounts`

## Objetivo

Validar comportamento real do sistema, medir performance inicial e coletar sinais para strategy learning sem colocar contas em risco.

## 1. Pre-run

### Contas

- [ ] 3 contas elegiveis
- [ ] aquecimento minimo concluido
- [ ] nenhuma conta com warning recente
- [ ] nenhuma conta em cooldown

### Sistema

- [ ] scheduler ativo
- [ ] workers ativos
- [ ] safety layer ativa
- [ ] experiment framework habilitado

### Endpoints

- [ ] `GET /health` -> `200`
- [ ] `GET /ready` -> `ready=true`

### Diretorios operacionais

- [ ] `OUT/content/`
- [ ] `OUT/safety/`
- [ ] `OUT/intelligence/`
- [ ] `OUT/experiments/`
- [ ] `OUT/attribution/`
- [ ] `OUT/rollout/`
- [ ] `OUT/ops/`

## 2. Parametros do piloto

Configuracao inicial recomendada:

- `accounts = 3`
- `posts_per_day_per_account = 2`
- `duration = 72h`
- `total_posts_expected = 12-18`

Pacing conservador:

- `min_interval_between_posts = 120 min`
- `max_posts_per_day = 3`

Jitter ativo:

- `publish_jitter = +-5-8 min`

## 3. Sequencia de execucao

1. habilitar rollout na allowlist
2. iniciar scheduler da janela
3. monitorar o primeiro ciclo de publish

A primeira publicacao eh a mais importante.

Verificar:

- [ ] publish ocorreu
- [ ] `publish_record` criado
- [ ] safety nao bloqueou
- [ ] metricas comecaram a chegar

## 4. Gate explicito de ingestao

Congelar o SLA operacional minimo:

- primeira evidencia de `publish_record`: ate `T+5 min`
- primeira evidencia de `video_metrics`: ate `T+6 h`

Se um desses limites estourar:

- [ ] abrir investigacao operacional
- [ ] verificar provider / ingestao / account state
- [ ] considerar pausa do piloto se houver repeticao

## 5. Monitoramento nas primeiras horas

### Pipeline

- [ ] `creative_pack` gerado
- [ ] render concluido
- [ ] publish concluido

### Safety

- [ ] pacing delays dentro do esperado
- [ ] nenhum cooldown inesperado
- [ ] nenhum risk signal critico

### Experimentos

- [ ] assignment correto
- [ ] variantes distribuidas

## 6. Alertas que exigem acao imediata

Parar o piloto se aparecer:

- `ACCOUNT_RESTRICTED`
- `REPEATED_PUBLISH_REJECTED`
- `RATE_LIMIT` em multiplas contas
- `COOLDOWN > 24h`

Acao:

- [ ] acionar `kill switch rollout`

## 7. Criterios de abort por tendencia

Abortar preventivamente se ocorrer qualquer um:

- `fallback_rate` anormal e crescente
- `publish success rate < 80%` nas primeiras 12h
- `cooldown_started` em 2 contas ou mais
- `risk_detected` recorrente sem recuperacao

Esses casos sao degradacao operacional, mesmo sem evento fatal unico.

## 8. Observacao durante as 72h

A cada janela observar:

### Performance

- views
- `watch_3s_rate`
- `completion_rate`

### Experimentos

- hook A vs B
- pacing A vs B

### Safety

- delays
- cooldowns
- jitter funcionando

## 9. Artefatos esperados

Ao final do piloto:

- `OUT/rollout/pilot_rollout_report.json`
- `OUT/rollout/pilot_batch_window_summary.json`
- `OUT/rollout/pilot_alerts.json`
- `OUT/ops/slo_status.json`
- `OUT/ops/alerts.jsonl`

## 10. Metricas minimas para considerar o piloto valido

O piloto nao busca viralizacao.

Ele busca:

- publicacao estavel
- contas sem restricao
- metricas chegando corretamente
- experimentos rodando
- atribuicao funcionando

## 11. Criterio GO para expansao

O piloto e considerado bem-sucedido se:

- `publish success rate >= 95%`
- `0 contas restritas`
- experimentos gerando dados
- pipeline sem falhas criticas

## 12. Pos-piloto

Executar:

- rollout summary
- experiment summary
- strategy learning review

Gerar:

- `OUT/rollout/pilot_summary.md`

## 13. O que nao esperar do piloto

Piloto nao e para:

- viralizar
- ganhar seguidores
- bater milhoes de views

Piloto e para:

- validar o sistema
- coletar sinais
- alimentar aprendizado

## Resumo operacional

Fluxo correto:

`aquecer contas -> executar piloto D23 -> validar comportamento real -> abrir D25`


---

## Source: `docs/runtime/d23_pilot_operator_index_v1_0.md`

# CortAI - D23 Pilot Operator Index

Versao: `v1.0`
Escopo: operacao do piloto real de 72h
Aplica-se a: `CortAI >= D33`

## Objetivo

- centralizar todos os artefatos operacionais do piloto
- permitir execucao sem improviso
- reduzir tempo de decisao durante incidentes

## Estado do sistema

### Checkpoint congelado

- Tag: `cortai-pre-pilot-audit-2026-03-07`

### Status tecnico

- Engineering: `COMPLETE (D27-D33)`
- Audit Gate: `PASS`
- Operational Docs: `VERSIONED`
- Pilot: `READY (waiting accounts)`

## Sequencia operacional do piloto

Fluxo resumido:

- GO/NO-GO checklist
- Run pilot D23
- Monitor first 12 hours
- Operate remaining 72h
- Generate rollout artifacts
- Evaluate gate for D25

## Artefatos operacionais

### 1. Runbook completo

Arquivo:

- `docs/runtime/d23_pilot_runbook_v1_0.md`

Contem:

- sequencia completa de execucao
- rollback
- allowlist
- parametros do piloto
- criterios GO/NO-GO

Uso:

- referencia principal do operador

### 2. Operational Checklist

Arquivo:

- `docs/runtime/d23_pilot_operational_checklist_v1_0.md`

Contem:

- sequencia operacional detalhada
- checklist de execucao
- artefatos esperados

Uso:

- durante o piloto

### 3. GO / NO-GO Checklist

Arquivo:

- `docs/runtime/d23_pilot_day_go_no_go_checklist_v1_0.md`

Contem:

- verificacao final antes do piloto

Uso:

- imediatamente antes de iniciar o piloto

### 4. First 12 Hours Monitoring Map

Arquivo:

- `docs/runtime/d23_first_12_hours_monitoring_map_v1_0.md`

Contem:

- checkpoints de monitoramento
- sinais precoces de risco
- criterios de incidente

Uso:

- `T+0` ate `T+12h`

### 5. Pilot Learning Plan

Arquivo:

- `docs/runtime/d23_pilot_learning_plan_v1_0.md`

Contem:

- matriz de videos
- variaveis experimentais
- interpretacao de metricas
- leitura de sinais fracos

Uso:

- planejamento e analise do piloto

## Artefatos gerados pelo piloto

Apos execucao, devem existir:

- `OUT/rollout/pilot_rollout_report.json`
- `OUT/rollout/pilot_batch_window_summary.json`
- `OUT/rollout/pilot_alerts.json`
- `OUT/ops/slo_status.json`
- `OUT/ops/alerts.jsonl`

## Metricas monitoradas

Arquivo:

- `OUT/metrics/video_metrics.jsonl`

Campos principais:

- `views`
- `watch_time`
- `completion_rate`
- `avg_watch_time`
- `likes`
- `shares`
- `comments`

## Eventos esperados

### Content pipeline

- `CONTENT/tts_started`
- `CONTENT/tts_completed`
- `CONTENT/render_started`
- `CONTENT/render_completed`
- `CONTENT/publish_started`
- `CONTENT/publish_completed`

### Safety

- `SAFETY/pacing_delay`
- `SAFETY/publish_blocked`
- `SAFETY/risk_detected`

### Metrics

- `METRICS/collection_started`
- `METRICS/collection_completed`

## Condicoes de abort

Abortar piloto se ocorrer:

- `ACCOUNT_RESTRICTED`
- `REPEATED_PUBLISH_REJECTED`
- `RATE_LIMIT` em multiplas contas
- `COOLDOWN > 24h`

Procedimento:

- activate rollout kill switch
- pause scheduler
- investigate

## Criterio de sucesso do piloto

Apos `72h`:

- `publish success rate >= 95%`
- `0 contas restritas`
- metricas coletadas
- experimentos executados
- atribuicao funcional

Se atendido:

- abrir `D25 - Production Expansion`

## Operador responsavel

Preencher no momento do piloto:

- Operator: `____`
- Start time: `____`
- End time: `____`
- Accounts used: `____`

## Estrutura final de runtime docs

```text
docs/runtime/
 +- d23_pilot_runbook_v1_0.md
 +- d23_pilot_operational_checklist_v1_0.md
 +- d23_pilot_day_go_no_go_checklist_v1_0.md
 +- d23_first_12_hours_monitoring_map_v1_0.md
 +- d23_pilot_learning_plan_v1_0.md
 +- d23_pilot_operator_index_v1_0.md
```

## Beneficio desse indice

O operador precisa abrir apenas um documento:

- `d23_pilot_operator_index_v1_0.md`

E dali acessar tudo.


---

## Source: `docs/runtime/distributed_execution_v1_0.md`

# Distributed Execution v1.0

## Objetivo

Permitir que multiplos workers executem tarefas do CortAI preservando:

- exclusividade por lease
- idempotencia por `op_key`
- consistencia de snapshot
- corretude do patch loop
- observabilidade por worker

## Tipos de task

- `WINDOW_AGGREGATION`
- `WINDOW_POST_PIPELINE`
- `EVENT_INDEX_REBUILD`

## Lifecycle da task

Estados:

- `PENDING`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`
- `NOOP`
- `BLOCKED`

Fluxo:

`queue -> worker -> lease -> op_key -> handler -> finalize`

## Retry policy

- `max_attempts = 3`
- retry apenas para falhas temporarias
- `CONFLICT`, `BLOCKED` e `NOOP` nao fazem retry

## Observabilidade minima

Cada execucao deve registrar:

- `worker_id`
- `pid`
- `hostname`
- `task_id`
- `op_key`

## Regra arquitetural

O D20 nao substitui D12.

O runtime distribuido apenas usa corretamente:

- `LeaseManager`
- `IdempotencyManager`
- snapshots e pipelines ja existentes

## Fora de escopo

- Redis / Celery / Kafka
- scheduler distribuido externo
- autoscaling
- orchestration multi-host completa


---

## Source: `docs/runtime/distributed_scheduler_v1_0.md`

# Distributed Scheduler v1.0

## Objetivo

Planejar, enfileirar e disparar tasks de forma continua, previsivel e auditavel.

O scheduler:

- gera planos deterministas
- decide `scheduled_for`
- enfileira tasks
- nunca executa a task diretamente

## Tipos de schedule

- `EVERY_72H`
- `DAILY`
- `MANUAL`

## Regras congeladas

- mesma janela + mesma task = `NOOP`
- mesma chave logica com payload diferente = `CONFLICT`
- scheduler nao executa task
- scheduler apenas planeja e enfileira

## Chave de idempotencia

`op_key`

Exemplos:

- `AGG:{account_id}:{window_id}`
- `D10:{account_id}:{window_id}`
- `IDX_REBUILD:{account_id}:{date}`

## Observabilidade minima

Toda task agendada carrega:

- `task_id`
- `task_type`
- `account_id`
- `window_id`
- `scheduled_for`
- `op_key`
- `scheduler_id`

## Janela principal

Para `EVERY_72H`:

- o scheduler gera `WINDOW_AGGREGATION`
- e tambem `WINDOW_POST_PIPELINE`
- ambos para a mesma janela

## Fora de escopo

- cron real
- scheduler distribuido multi-host
- persistencia da fila em banco externo
- priorizacao dinamica


---

## Source: `docs/runtime/EXPERIMENT_CAPABILITY_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`

# EXPERIMENT_CAPABILITY_EVOLUTION_v2_0_IMPLEMENTATION_PLAN

## 1. Objective

The objective of `Experiment Capability v2.0` is to evolve the current subsystem from:
- experiment plan emitter

into:
- closed-loop experiment subsystem

The v2.0 goal is not to make the subsystem more intelligent first.
The v2.0 goal is not to add heuristic sophistication for its own sake.
The v2.0 goal is to make experimentation real in runtime.

Target outcome for v2.0:
- experiment eligibility becomes explicit
- assignment becomes real and persisted
- execution remains downstream-owned
- result recording becomes real and persisted
- experiment trace becomes auditable
- the subsystem remains narrow in authority
- the frozen pipeline core does not need broad redesign

## 2. Current State

Current Phase 1 state:
- Experiment Capability is implemented and runtime-real
- it is called by the creative orchestrator
- it emits `ExperimentPlan`
- it injects experiment context into `CreativePack`
- it influences Script behavior narrowly
- variant selection is deterministic
- fallback/default dominates in the current frozen runtime
- the default config path is missing in the current repo
- runtime does not call `assign(...)`
- runtime does not call `record_result(...)`
- runtime does not close the experiment loop

Current classification:
- `implemented`
- `runtime-real`
- `structurally-integrated`
- `causally-narrow`
- `audit-open-loop`
- `not yet a real experiment subsystem`

v2.0 exists to fix the correct deficit:
- loop closure

v2.0 does not exist to fix the wrong deficit:
- intelligence inflation before assignment and result recording are real

## 3. Core Diagnosis

The core diagnosis is simple:

```json
{
  "experiment_capability_v1": {
    "exists": true,
    "integrated": true,
    "causal_effect": "narrow",
    "loop_closed": false,
    "assignment_real": false,
    "result_recording": false,
    "fallback_dominant": true
  }
}
```

Brutally honest translation:
- this is not yet an experimentation system
- this is an experimental context emitter

The exact missing chain is:

`eligibility -> assignment -> execution -> result recording -> observability`

Today the runtime is effectively stuck at:

`plan -> script influence`

That is pre-experiment, not experiment operations.

## 4. Boundary

This boundary must remain explicit.

### 4.1 Experiment Capability
Experiment Capability owns:
- experiment eligibility
- control vs variant assignment
- experiment type selection
- safe experiment envelope
- runtime experiment traceability

Experiment Capability does not own:
- strategy policy
- learning policy
- trend collection
- QC governance
- content generation directly
- winner rollout policy

### 4.2 Strategy
Strategy owns:
- strategic posture
- risk posture for generation
- translation of upstream context into content direction

Experiment Capability may condition generation through experiment assignment.
It must not become a parallel strategy brain.

### 4.3 Learning
Learning owns:
- performance interpretation
- policy formation
- pattern learning

Experiment Capability may record outcomes for later analysis.
It must not absorb Learning logic.

### 4.4 QC
QC owns:
- final product evaluation
- publishability governance

Experiment Capability may use QC output as result evidence.
It must not replace QC.

### 4.5 Hard boundary rule
The subsystem must remain:
- experiment orchestrator

It must not become:
- strategy engine
- learning engine
- content generator
- rollout optimizer

## 5. v2.0 Scope

Included in scope:
- real runtime eligibility decision
- real runtime assignment persistence
- assignment identifiers and subject keys
- real runtime result recording
- experiment trace visibility in execution artifacts
- narrow deterministic controlled-causality proof
- preservation of current experiment context propagation

Excluded from scope:
- winner auto-selection
- adaptive rollout
- multi-arm bandits
- policy mutation
- autonomous learning integration
- broad strategy redesign
- broad downstream redesign
- more than two variants

## 6. Core Gap To Fix

The missing pieces are:

```json
{
  "missing": [
    "real assignment",
    "result recording",
    "eligibility control",
    "audit closure"
  ]
}
```

Priority order:
1. assignment
2. result recording
3. eligibility
4. audit closure

Absolute rule:
- if only one thing is implemented in v2.0, it must be real runtime `assign(...)` plus real runtime `record_result(...)`

Nothing else matters before that.

## 7. Assignment Activation Strategy

This is the heart of v2.0.

### 7.1 Current problem

Today the runtime:
- creates or resolves an experiment identity
- resolves a variant payload
- synthesizes a thin assignment annotation in `CreativePack`

It does not:
- create a real persisted assignment record

### 7.2 Required v2.0 behavior

During runtime experiment resolution, the subsystem must call:
- `ExperimentService.assign(...)`

That assignment must produce a real framework artifact containing:
- `assignment_id`
- `experiment_id`
- `subject_key`
- `variant`
- `assigned_at`

This must be persisted through the experiment framework store.

### 7.3 Subject key policy

The subject key must be deterministic and traceable.

Recommended subject key:
- `account_id|publish_slot|topic`

This keeps compatibility with current variant resolution material.

Rule:
- subject key construction must be explicit, stable, and serialized in trace

### 7.4 Creative runtime integration

`ExperimentCapabilityService.generate(...)` should evolve from:
- create experiment
- resolve variant payload

into:
- create experiment
- assign real subject
- resolve variant from the real assignment
- build experiment plan plus assignment trace

### 7.5 Contract evolution

`CreativePack.experiment_assignment` must stop being only a shorthand.

It should evolve to include at least:
- `assignment_id`
- `experiment_id`
- `subject_key`
- `variant_id`
- `assigned_at`

This is the minimum needed to make the runtime experiment assignment real and auditable.

## 8. Result Recording Strategy

This is the second core pillar.

### 8.1 Current problem

Today:
- experiment context reaches execution
- but execution does not write results back into the experiment framework

This means:
- no closed loop
- no experiment outcome ledger
- no formal experiment result history

### 8.2 Required v2.0 behavior

After execution reaches a terminal product outcome, runtime must call:
- `ExperimentService.record_result(...)`

Minimum inputs:
- experiment
- subject key
- window id or equivalent runtime slot id
- metrics

### 8.3 Result timing

The correct initial timing is:
- after pipeline execution
- after QC evaluation is available

Reason:
- QC is the first real quality governor already present in the pipeline

### 8.4 Minimum metrics to record

The result payload should remain conservative.

Recommended minimum metrics:
- `qc_status`
- `publishable`
- `overall_score`
- `product_quality`
- `hook_quality`
- `payoff_quality`
- `render_status`

Optional if cheaply available:
- `video_duration_s`
- `has_audio`

Do not overdesign a full metrics schema in v2.0.

### 8.5 Assignment linkage

The result recording path must remain explicitly linked to the real assignment context.

Even if `record_result(...)` currently resolves assignment internally by subject key, runtime artifacts must still preserve:
- `assignment_id`
- `subject_key`

This is necessary for audit closure.

## 9. Eligibility Strategy

Eligibility is required, but it should remain light.

### 9.1 Current problem

Today:
- any non-fallback config-backed run is effectively experiment-eligible
- there is no explicit policy envelope

### 9.2 v2.0 principle

Eligibility should be deterministic, explicit, and conservative.

It should not be ML-based.
It should not be a large policy system.

### 9.3 Recommended minimum rules

Initial eligibility can be:

- if `account_health == HOLD`:
  - no experiment

- if novelty pressure or repetition pressure indicates safe need for exploration:
  - allow experiment

- if recent quality is unstable:
  - allow only conservative experiment types

- else:
  - default conservative eligibility

### 9.4 Correct v2.0 scope

Eligibility is not here to decide what is best.
It is here to decide whether controlled testing is allowed and within what envelope.

### 9.5 Safe envelope examples

Safe envelope may limit:
- experiment scope type
- allowed variant family
- experimental aggressiveness

It must not:
- override Strategy
- override QC
- mutate content directly

## 10. Contract Preservation And Evolution

v2.0 should preserve the current useful contract while making it real.

### 10.1 Preserve

Keep:
- `ExperimentPlan`
- `fallback`
- deterministic `variant_id`
- downstream script visibility

### 10.2 Evolve

`ExperimentPlan` may remain compact.
The main evolution should be around assignment and traceability.

Minimum recommended additions:
- richer `ExperimentAssignment`
- `experiment_trace` or equivalent result-side trace

### 10.3 Backward compatibility

The following must remain compatible:
- Script experiment consumption
- `CreativePack.experiment_plan`
- top-level experiment result in execution output
- orchestrator events

## 11. Data Sources And Activation Paths

### 11.1 Assignment source

Assignment source is runtime input plus framework identity:
- `account_id`
- `publish_slot`
- `topic`
- experiment config

### 11.2 Result source

Result source should be existing runtime outputs:
- pipeline output status
- QC output
- score summary
- product signals

### 11.3 Input assembly rule

Correct v2.0 assembly:
- orchestrator resolves upstream context
- experiment capability decides eligibility
- experiment capability persists assignment
- downstream execution happens
- orchestrator or experiment recorder persists result

This keeps experiment control narrow and explicit.

## 12. Orchestrator Integration Plan

The orchestrator is the correct place to wire the loop closure.

### 12.1 Pre-execution stage

Before Script generation:
- call experiment capability
- persist real assignment if eligible
- emit experiment generated or fallback event with richer trace

### 12.2 Post-execution stage

After pipeline and QC:
- if a real assignment exists, record result
- emit experiment result recorded event

### 12.3 Hold and fallback behavior

If Health blocks before experiment assignment:
- no assignment should be created

If experiment capability falls back:
- fallback must remain visible
- no fake assignment should be synthesized as if it were real

This is important.
Do not create false audit artifacts.

## 13. Traceability And Auditability Plan

v2.0 must make experiment runtime traceable enough to audit.

Minimum audit targets:
- assignment is real
- subject key is visible
- experiment id is visible
- variant is visible
- result was recorded

### 13.1 Assignment visibility

Execution artifacts should make visible:
- `assignment_id`
- `experiment_id`
- `subject_key`
- `variant_id`
- `assigned_at`

### 13.2 Decision trace

The subsystem should expose a small `decision_trace` with:
- eligibility decision
- config source used
- fallback reason if any
- assignment path used

### 13.3 Result trace

The subsystem should expose a small `experiment_trace` with:
- assignment reference
- result recorded flag
- result window id
- metrics summary sent to recorder

### 13.4 Event surface

Recommended events:
- `CREATIVE/experiment_plan_generated`
- `CREATIVE/experiment_plan_fallback`
- `CREATIVE/experiment_assignment_recorded`
- `CREATIVE/experiment_result_recorded`

The current events are not enough to prove loop closure.

## 14. Determinism Requirements

Determinism is mandatory.

The same:
- experiment config
- subject key
- eligibility inputs

must produce:
- the same eligibility decision
- the same assignment
- the same variant

Result recording is allowed to vary only with actual runtime outcome metrics.

To preserve determinism:
- use explicit subject key construction
- use deterministic assignment logic only
- avoid random rollout decisions
- avoid hidden priority ordering of eligibility rules

## 15. Controlled Causality Proof

v2.0 must prove more than structure.

Minimum proof required:
- different variants produce a controlled downstream difference
- that difference is visible in runtime artifacts
- the assignment/result loop remains coherent

### 15.1 Acceptable first proof

Script-focused proof is sufficient for v2.0 if it is clean.

Examples:
- `variant A` forces one narrative mode
- `variant B` forces another narrative mode
- script output differs deterministically
- output trace records which assignment produced which result

### 15.2 Non-goal

Do not try to prove broad multi-agent behavioral divergence yet.
That is not required for v2.0.

## 16. Implementation Phases

### 16.1 Phase A: Assignment Activation

Objective:
- make assignment real

Work:
- wire `ExperimentService.assign(...)` into runtime generation path
- generate real `assignment_id`
- persist assignment row
- expand assignment contract in `CreativePack`
- serialize subject key and assigned timestamp

Deliverable:
- runtime outputs contain a real experiment assignment, not only structural shorthand

### 16.2 Phase B: Result Recording Activation

Objective:
- close the loop after execution

Work:
- wire `ExperimentService.record_result(...)` after QC / final output
- record conservative metrics set
- persist result row
- expose result recording trace

Deliverable:
- experiment runs produce persisted results tied to runtime execution

### 16.3 Phase C: Eligibility Activation

Objective:
- prevent uncontrolled experiment application

Work:
- add explicit deterministic eligibility rules
- block experimentation on `Health HOLD`
- apply conservative default envelope
- keep fallback explicit

Deliverable:
- experiments become policy-bounded, not merely config-bounded

### 16.4 Phase D: Auditability Hardening

Objective:
- make the closed loop inspectable

Work:
- add assignment trace
- add result trace
- add event enrichment
- ensure artifacts serialize cleanly

Deliverable:
- post-run review can reconstruct experiment lifecycle

### 16.5 Phase E: Controlled Validation

Objective:
- prove the subsystem is now real

Work:
- unit tests
- orchestrator integration tests
- controlled runtime battery
- deterministic A/B causality proof

Deliverable:
- evidence that experiment capability is no longer only a context emitter

## 17. Validation Path

### 17.1 Unit validation

Required tests:
- real assignment creation
- assignment determinism
- result recording
- eligibility rule behavior
- fallback behavior remains explicit
- serialization of richer assignment and trace blocks

### 17.2 Integration validation

Required tests:
- orchestrator persists assignment in eligible path
- orchestrator does not create fake assignment on fallback-only path
- post-QC result recording occurs
- execution artifact contains traceable experiment lifecycle

### 17.3 Controlled execution battery

Required scenarios:
- config-backed eligible experiment path
- fallback path
- health hold path with no experiment
- deterministic repeat of same subject
- A/B causal differentiation scenario

### 17.4 Validation gate

Recommended artifact:
- `docs/runtime/EXPERIMENT_CAPABILITY_v2_0_VALIDATION_GATE.md`

Recommended output directory:
- `OUT/audit/experiment_capability_v2_0_validation`

The gate must prove:
- assignment is real
- result recording is real
- eligibility is explicit
- causality is stronger than ornamental context
- determinism remains intact

## 18. Risks

### Risk 1: Assignment becomes real only cosmetically
Mitigation:
- require persisted framework rows
- require `assignment_id`
- require subject key visibility

### Risk 2: Result recording is added but not tied cleanly to execution
Mitigation:
- record after QC
- serialize assignment/result linkage in execution output

### Risk 3: Eligibility becomes overengineered
Mitigation:
- keep deterministic rules small
- no ML
- no large policy grammar

### Risk 4: Subsystem starts expanding into Strategy or Learning
Mitigation:
- enforce narrow boundary
- prohibit winner logic and policy mutation in v2.0

### Risk 5: Fallback path generates false confidence
Mitigation:
- keep fallback explicit
- do not synthesize fake "real" assignment on fallback-only path

## 19. Success Criteria

Experiment Capability v2.0 should be considered successful if:
- runtime creates real assignment records
- runtime records experiment results
- `assignment_id` is visible in execution artifacts
- `subject_key` is traceable
- fallback remains explicit
- health hold correctly prevents experiment application
- at least one controlled A/B downstream difference is proven
- same subject still yields same assignment deterministically
- post-run audit can reconstruct assignment -> execution -> result

Success does not require:
- winner selection
- adaptive rollout
- learning integration
- strategy redesign
- full subsystem promotion in the same step

## 20. Next Correct Move After This Plan

After this implementation plan is written, the next correct move is:
- implement `Phase A: Assignment Activation`

Reason:
- it is the irreducible core of the subsystem
- it turns structure into reality
- it unlocks result recording cleanly
- it does not require reopening the frozen core architecture broadly

## Final Implementation Position

Experiment Capability v2.0 should be built as:
- deterministic
- loop-closing
- assignment-real
- result-recording-real
- eligibility-bounded
- audit-improved
- narrow in authority

It should not be built as:
- an optimization brain
- a winner selector
- a strategy layer
- a learning layer
- a content generation layer

Final one-line target:
- `Experiment Capability v2.0` must turn experiment context into real runtime experimentation by activating assignment, result recording, eligibility, and traceability without inflating scope beyond loop closure.


---

## Source: `docs/runtime/EXPERIMENT_CAPABILITY_v2_0_GOVERNANCE_DECISION.md`

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
- `docs/runtime/baselines/experiment/EXPERIMENT_CAPABILITY_SYSTEM_BIBLE_PHASE1.md`
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


---

## Source: `docs/runtime/EXPERIMENT_CAPABILITY_v2_0_VALIDATION_GATE.md`

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


---

## Source: `docs/runtime/LEARNING_AGENT_EVOLUTION_v2_0_FULL_VALIDATION_GATE.md`

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


---

## Source: `docs/runtime/LEARNING_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`

# Learning Agent Evolution v2.0 Implementation Plan

## 1. Executive Summary

The Phase 1 Learning Agent is runtime-real, useful for observability, and partially useful for conditioning the system, but it is still not a true optimization subsystem.

Its current role is best described as:
- heuristic evidence summarizer
- partial context injector
- weakly causal support layer

What it does today:
- reads simple historical files
- emits `LearningInsights`
- influences `Strategy` partially through `signal_summary`
- influences `Script` weakly through prompt context

What it does not do today:
- close the loop on quality
- learn from `QC`
- separate winning and losing patterns
- emit strong executable policy
- protect itself from fallback contamination

The goal of `Learning v2.0` is not to make the agent richer in fields.

The goal is to make it:
- causal
- reliable
- loop-closed
- conservative
- auditable

Mission of v2.0:
- turn past evidence into actionable policy
- make that policy influence future behavior explicitly
- use `QC` results as real feedback
- distinguish winning and losing patterns
- avoid fallback poisoning
- keep the system deterministic and inspectable

Most precise framing:
- **Learning v2.0 = from heuristic summarizer to minimal conservative self-optimization layer**

## 2. Current Diagnosis

Current consolidated state:

```json
{
  "status": "weakly_causal",
  "runtime_real": true,
  "influential": "low",
  "baseline_ready": false,
  "main_gap": "lack_of_real_learning_loop"
}
```

What Learning does today:
- reads local history files
- computes simple aggregates
- produces `LearningInsights`
- persists and propagates output
- influences:
  - `Strategy` via `signal_summary`
  - `Script` via prompt hints

What Learning does not do:
- does not consume `QC`
- does not use temporal windows
- does not weight recency
- does not learn per pattern
- does not emit strong policy
- does not directly govern downstream behavior
- does not know whether its recommendations improved or worsened output quality

Current effective shape:
- `history -> summary -> suggestions`

Required future shape:
- `history -> pattern analysis -> policy -> enforcement -> qc feedback -> updated policy`

Core diagnosis:
- the subsystem summarizes evidence
- but it does not yet close the performance loop

## 3. Objective of v2.0

Learning Agent v2.0 should become the layer that:
1. reads relevant past results
2. extracts useful patterns by behavior type
3. emits executable policy rather than weak suggestions
4. injects that policy primarily into `Strategy`
5. receives feedback from `QC`
6. adjusts future recommendations based on what worked and what failed

This phase is intentionally narrow.

It should not:
- become an aggressive self-tuning system
- mutate `Script`, `Voice`, `Asset`, or `Editor` directly
- control publication
- replace `Strategy`
- replace `Novelty`
- perform stochastic optimization
- introduce a large pattern ontology

Guiding principle:
- **closed-loop, conservative, auditable**

## 4. Mission and Boundary

### Learning v2.0 will do

- consume relevant historical evidence
- consume `QC` signals
- detect winning and losing patterns
- separate evidence from policy
- emit `LearningPolicy` or equivalent actionable adjustments
- feed `Strategy` strongly
- preserve determinism and traceability

### Learning v2.0 will not do

- render anything
- correct outputs directly
- swap assets directly
- alter voice plans directly
- force publication
- rewrite scripts directly
- trigger experiments autonomously
- replace account or product governance

### Boundary principle

Learning determines what tends to work.

Strategy determines how to use that evidence.

QC determines whether results remain acceptable.

Novelty determines whether repetition must be controlled.

Learning closes the loop.

## 5. The Five Pillars of v2.0

### 5.1 Consume QC as Real Feedback

This is the most important pillar.

Learning v2.0 must consume some form of:
- `QC` status:
  - `APPROVE`
  - `HOLD`
  - `REJECT`
- `score_summary`
  - `script_quality`
  - `voice_quality`
  - `asset_quality`
  - `edit_quality`
  - `product_quality`
  - `overall_score`
- `product_signals`
  - `hook_quality`
  - `payoff_quality`
  - `publishability_signal`
- `reasons`
- `publishable`

Why:
- without `QC`, Learning cannot know:
  - what generated quality
  - what failed
  - what should be reinforced
  - what should be avoided

Operational rule:
- no strong Learning policy should be derived from views/completion averages alone without some linkage to output quality

### 5.2 Move from Suggestion to Policy

Today the agent emits:
- recommendation strings
- prompt hints
- summary metadata

v2.0 should emit a stronger and structured object, for example:

```json
{
  "learning_policy": {
    "hook_type_bias": {
      "value": "question",
      "confidence": 0.82,
      "evidence_count": 18
    },
    "target_duration_bias": {
      "value": "8-12s",
      "confidence": 0.76,
      "evidence_count": 21
    },
    "payoff_specificity_bias": {
      "value": "high",
      "confidence": 0.79,
      "evidence_count": 15
    },
    "risk_adjustment_hint": {
      "value": "conservative_if_low_score_cluster",
      "confidence": 0.73,
      "evidence_count": 12
    }
  }
}
```

Policy requirements:
- structured
- auditable
- confidence-tagged
- backed by minimum evidence count

### 5.3 Add Real Temporal Memory

Today the agent reads complete files and computes shallow global aggregates.

v2.0 needs temporal windows.

Minimum windows:
- `last_20`
- `last_100`

Intended use:
- `last_20`: recent behavior
- `last_100`: more stable tendency

If timestamps are available:
- apply simple recency decay
- newer evidence receives more weight
- older evidence receives less weight

If timestamps are not sufficiently available:
- use record order as a first approximation

What this solves:
- avoids blind global averaging
- reduces overreaction to noise
- allows recent regression detection
- allows separation between recent phase and older phase

### 5.4 Distinguish Winning and Losing Patterns

Today the agent summarizes global aggregates.

v2.0 must produce pattern-level analysis.

Examples of pattern families:
- `hook_type`
- `hook_family`
- `target_duration_range`
- `payoff_structure`
- `visual_payoff_family`
- `voice_style`
- `editor_style_profile`
- `strategy variation posture`

Metrics per pattern should include:
- frequency
- approve rate
- hold rate
- reject rate
- average overall score
- average product quality
- average hook quality
- average payoff quality

Expected shape:

```json
{
  "pattern_findings": {
    "hook_type:question": {
      "approve_rate": 0.84,
      "avg_overall_score": 0.88,
      "evidence_count": 19
    },
    "payoff_structure:named_location_removed": {
      "approve_rate": 0.61,
      "avg_payoff_quality": 0.67,
      "evidence_count": 23
    }
  }
}
```

Key requirement:
- Learning must answer:
  - what pattern works better
- not only:
  - what the system average looks like

### 5.5 Close the Learning <-> Strategy <-> QC Loop

Desired loop:

```text
Past runs
  -> Learning reads history + QC outcomes
  -> Learning emits policy
  -> Strategy consumes policy
  -> Generation happens
  -> QC judges result
  -> New result returns to Learning dataset
```

What changes:
- the system stops merely generating
- the system starts incorporating results of what it generated

Important rule:
- in v2.0 this loop may remain asynchronous and simple
- it does not need to be online or continuously self-updating in real time
- it only needs to be:
  - closed
  - consistent
  - auditable

## 6. Proposed Contract Evolution

The goal is not contract explosion.

The goal is stronger operational effect with minimal extension.

### 6.1 Keep

- `LearningInsights`

### 6.2 Evolve

Preferred additions:
- `LearningPolicy`
- `PatternFindingsSummary`

Suggested `LearningPolicy` fields:
- `hook_type_bias`
- `duration_bias`
- `payoff_specificity_bias`
- `risk_adjustment_hint`
- `variation_tolerance_hint`
- `policy_trace`
- `confidence_summary`

Suggested `PatternFindingsSummary` fields:
- `pattern_name`
- `evidence_count`
- `approve_rate`
- `hold_rate`
- `reject_rate`
- `avg_overall_score`
- `avg_product_quality`

Suggested `LearningAgentResult` shape:
- `learning_insights`
- `learning_policy`
- `pattern_findings_summary`
- `fallback`

Contract rule:
- if the contract can be extended safely without breaking consumers, do that
- if not, a policy block may be embedded inside `LearningInsights`
- operational effect matters more than formal elegance in this phase

## 7. Feedback Loop with QC

New required input family:
- historical `QC` outputs

Minimum fields:
- final status
- `overall_score`
- `hook_quality`
- `payoff_quality`
- `reasons`

Recommended weighting:
- `REJECT` weighs negatively
- `HOLD` weighs negatively, but less
- `APPROVE` weighs positively
- `overall_score` refines magnitude
- `product_signals` localize what failed

Examples:
- high-approve, high-payoff pattern -> reinforce
- high-approve, low-payoff pattern -> cautious reinforcement
- frequent `HOLD` because of payoff weakness -> penalize payoff structure
- frequent `REJECT` because of weak visual evidence -> penalize visual family

## 8. Strong Integration with Strategy

`Strategy` is the primary downstream consumer for Learning v2.0.

Today:
- `Strategy` uses only `signal_summary`

v2.0 target:
- `Strategy` should consume:
  - `learning_policy`
  - selected parts of `pattern_findings_summary`
  - `risk_adjustment_hint`
  - `duration_bias`
  - `hook_type_bias`
  - `variation_tolerance_hint`

What Strategy should then do:
- read more than simple averages
- apply policy with confidence
- prioritize winning patterns
- avoid losing patterns
- adjust aggressiveness and risk using evidence

Boundary principle:
- Learning does not govern the pipeline directly
- it governs the strategic governor more strongly

## 9. Relationship with Script, Voice, Asset, and Editor

### Script

Script may continue receiving `LearningInsights`, but may also receive:
- `hook_type_bias`
- `payoff_specificity_bias`

Expected role in this phase:
- still mostly indirect
- either via `Strategy`
- or via stronger prompt context

Do not deeply reopen Script in this phase.

### Voice

Out of scope as a strong Learning consumer in v2.0.

### Asset

Out of scope as a strong Learning consumer in v2.0.

### Editor

Out of scope as a strong Learning consumer in v2.0.

Important implementation rule:
- focus `Learning v2.0` on:
  - `QC` feedback
  - policy formation
  - strong `Strategy` integration
- do not spread shallow integrations everywhere

## 10. Fallback Tracking and Anti-Poisoning

This is critical.

If fallback dominates, Learning will learn the wrong thing.

Learning v2.0 must track contamination from:
- Learning fallback
- Script fallback
- Voice fallback
- Asset fallback where relevant

Minimum use:
- fallback-heavy runs must be identifiable in history
- they must either:
  - receive reduced weight
  - or be excluded from some analyses

Example:
- if a pattern scored highly
- but most of those runs used `Voice` fallback
- that should not count as clean evidence for the pattern

Operational rule:
- Learning v2.0 must distinguish:
  - clean evidence
  - contaminated evidence

## 11. Implementation Order

### Phase A - Contract Hardening

- define minimal output extension
- preserve backward compatibility
- introduce `LearningPolicy`
- introduce `policy_trace`

### Phase B - QC Feedback Ingestion

- read historical `QC` outcomes
- aggregate statuses and scores
- link patterns to outcomes

### Phase C - Temporal Memory

- implement `last_20` and `last_100`
- optionally apply simple decay

### Phase D - Pattern Analysis

- compute metrics by pattern
- identify winners and losers

### Phase E - Strong Strategy Integration

- Strategy consumes policy beyond `signal_summary`
- strategic behavior changes explicitly and traceably

### Phase F - Fallback Contamination Handling

- exclude or downweight contaminated evidence
- register contamination in trace

### Phase G - Validation Gate

- prove Learning is no longer just a summarizer
- prove the minimum loop is closed

## 12. Tests and Validation Gate

### Unit tests

Required coverage:
- `LearningPolicy` serialization
- temporal windows
- pattern scoring
- `QC` ingestion
- fallback contamination handling
- determinism

### Integration tests

Required proof:
- Learning influences `Strategy` strongly
- Strategy changes for justified reasons
- loop `Learning -> Strategy -> QC -> history` stays coherent

### Full validation gate

Suggested name:
- `LEARNING_AGENT_EVOLUTION_v2_0_FULL_VALIDATION_GATE`

The gate must prove:
- `QC` now enters Learning
- patterns are distinguished
- policies are generated
- `Strategy` reacts
- future behavior changes
- fallback does not poison conclusions
- the whole subsystem remains deterministic

## 13. Non-Goals of v2.0

Do not implement now:
- fully online continuous optimization
- aggressive auto-tuning
- reinforcement-learning style adaptation
- full experiment engine intelligence
- strong integration with every downstream agent
- huge pattern ontology
- black-box optimization

Phase principle:
- strong
- simple
- causal
- conservative

## 14. Final Verdict

Current Learning Phase 1 is correctly classified as:

```json
{
  "real_classification": "evidence_summarizer_with_partial_injection",
  "optimization_capability": "none",
  "learning_loop": "absent",
  "control_power": "low"
}
```

Target Learning v2.0 classification:

```json
{
  "real_classification": "policy_forming_feedback_consumer",
  "optimization_capability": "conservative_but_real",
  "learning_loop": "minimally_closed",
  "control_power": "medium_via_strategy"
}
```

## 15. Conclusion In One Line

Learning v2.0 should not try to be brilliant first.

It should finally begin to learn from what the system actually produces.


---

## Source: `docs/runtime/phase1_completion_report_v1_0.md`

# CortAI - Phase 1 Completion Report

## Status

Phase 1: `COMPLETED`

## Date

`2026-03-16`

---

## 1. Objective of Phase 1

The objective of Phase 1 was to design, implement and validate the operational infrastructure and execution loop of the CortAI system.

This phase focused on proving that the system can:

- generate short-form video content automatically
- process content through a controlled runtime
- enforce safety rules
- generate publish manifests
- persist canonical publish records
- collect metrics
- produce analysis artifacts
- operate in batch execution

Phase 1 did not aim to achieve production-grade creative quality, but rather to validate the technical pipeline and operational loop.

---

## 2. Scope Implemented in Phase 1

### Infrastructure

Validated local infrastructure:

- PostgreSQL
- Redis
- MinIO
- Docker Compose
- health and readiness probes

All services were validated through operational checks.

### Distributed Runtime

Implemented and validated components:

- distributed executor
- worker
- scheduler
- planner
- rollout runtime

Core files:

- `backend/app/runtime/executor.py`
- `backend/app/runtime/worker.py`
- `backend/app/runtime/scheduler/service.py`
- `backend/app/runtime/scheduler/planner.py`
- `backend/app/runtime/rollout/pilot_runner.py`

The runtime is capable of dispatching tasks and executing them through the pipeline.

### Content Pipeline (D27)

Implemented:

- `ExecutionEnvelope` input contract
- `PipelineResult` output contract
- content generation pipeline
- audio generation
- video rendering
- metadata generation
- `PublishManifest` generation

Key modules:

- `backend/app/content/pipeline/service.py`
- `backend/app/content/pipeline/orchestrator.py`
- `backend/app/content/pipeline/tts.py`
- `backend/app/content/pipeline/render.py`
- `backend/app/content/pipeline/publish.py`
- `backend/app/content/pipeline/models.py`

Important architectural constraint:

The pipeline does not write `publish_record` directly.

### Safety Layer (D28)

Implemented decision authority for publication.

Possible decisions:

- `ALLOW`
- `DELAY`
- `BLOCK`

Modules:

- `backend/app/safety/*`

Safety is invoked by the runtime before pipeline execution.

### Creative and Intelligence Layers

Implemented modules:

- `D29` creative packs
- `D30` intelligence
- `D31` experiments
- `D32` attribution
- `D33` metrics collector
- `D34` analysis layer

These layers enable experimentation, metrics aggregation and post-execution analysis.

### Simulation and Consistency

Implemented:

- `D37` Offline Simulation
- `D38` Consistency Checker

Outputs:

- `OUT/analysis/consistency_check.json`
- `OUT/analysis/consistency_check.md`

Final status:

- `CONSISTENCY_STATUS = OK`

---

## 3. Video Generation System

The video generation system evolved from a technical renderer to a functional audiovisual template.

Implemented components:

### Script Generation

Local generation via Ollama:

- `backend/app/content/script_gen/service.py`

### Screen Text Adapter

Canonical copy adaptation layer:

- `backend/app/content/screen_text/service.py`

Ensures the renderer receives stable text blocks.

### Audio Generation

TTS stack:

- `Piper` as default
- local offline voices

Configured via:

- `CORTAI_TTS_MODE=piper`

### Video Renderer

Features implemented:

- vertical video (`1080x1920`)
- three narrative blocks
- `hook / setup / payoff`
- multiple backgrounds
- transitions between scenes
- subtle motion
- ambient audio layer

---

## 4. Operational Validation

A full pre-release audit gate was implemented:

- `backend/scripts/run_pre_d23_final_release_audit_gate.ps1`

Documentation:

- `docs/runtime/pre_d23_final_release_audit_gate_v1_0.md`

The gate validates:

- build
- unit tests
- regressions
- contract integrity
- infrastructure probes
- security scans
- runtime smoke tests
- video QC
- consistency

Final result:

- `GO`
- `0 FAIL`

---

## 5. D23 Local Batch Execution

A controlled local batch was executed.

Entrypoint:

- `app.runtime.rollout.pilot_runner.run_pilot_rollout`

Wrapper:

- `backend/scripts/run_local_d23_18_batch.py`

Batch size:

- `18 videos`

Artifacts generated:

- `18 videos`
- `18 audio files`
- `18 metadata files`
- `18 publish_records`
- `18 metrics entries`

Consistency checker:

- `OK`

Batch result:

- `PASS`

Batch artifacts:

- `OUT/batches/local_d23_18_20260316_015054`

---

## 6. What Phase 1 Successfully Proved

Phase 1 validated the complete operational loop:

`scheduler`
-> `runtime`
-> `safety`
-> `content pipeline`
-> `publish manifest`
-> `publish_record`
-> `metrics collector`
-> `analysis`
-> `consistency validation`

The system can execute batch generation and persist all operational artifacts correctly.

---

## 7. Known Limitations

The current audiovisual template has limitations:

- TTS quality below premium systems
- simple motion
- basic visual identity
- minimal sound design

These limitations do not invalidate Phase 1, since the objective was pipeline validation rather than creative optimization.

---

## 8. Phase 1 Final Status

`PHASE 1: COMPLETED`

All operational components required for the CortAI pipeline were implemented and validated.

---

## 9. Next Phase

The focus of Phase 2 will shift from system infrastructure to creative capability and content competitiveness, including:

- premium TTS
- improved visual assets
- stronger scripts
- enhanced renderer
- creative agents

---

## Final Statement

CortAI successfully transitioned from a technical prototype to a functional automated content pipeline, capable of generating, processing and validating video batches through a controlled runtime environment.

Phase 1 is therefore considered complete.


---

## Source: `docs/runtime/phase2_5_voice_agent_definition_v1_0.md`

# Phase 2.5 Voice Agent Definition

Versao: 1.0
Status: Definicao formal de escopo
Fase: Phase 2.5A

## Objetivo
Corrigir a arquitetura de controle da voz sem redesenhar o CortAI.

Ao final da fase:

- `VoicePlan` deve ser contrato operativo real
- `Voice Interpreter` deve existir e ser deterministicamente rule-based
- `TTS Router` deve ser o ponto canÃ´nico de roteamento
- o pipeline deve obedecer `VoicePlan`
- `Piper` deve permanecer funcional

## Problema atual que esta fase corrige

- `VoicePlan` era parcialmente decorativo
- provider declarado e provider executado podiam divergir sem rastreabilidade adequada
- o Voice Agent nao interpretava `hook/setup/payoff`
- a entrega de voz nao possuia modelagem minima de ritmo, pausa e contraste

## Escopo permitido

- ampliar `VoicePlan`
- criar `Voice Interpreter`
- criar `TTS Router`
- adaptar `Creative Orchestrator -> Voice Agent -> Content Pipeline`
- adicionar observabilidade minima de provider requisitado, provider executado e fallback

## Fora de escopo

- novos providers pesados
- benchmarking amplo de TTS
- clonagem de voz
- emotion engine avancado
- refactor amplo da Fase 1

## Estado-alvo

```text
Creative Orchestrator
-> Voice Agent
-> Voice Interpreter
-> VoicePlan
-> Content Pipeline
-> TTS Router
-> Provider Adapter
-> Audio
```

## Regras

- Fase 2 decide; Fase 1 executa
- `Creative Orchestrator` continua coordenador unico
- `Voice Agent` continua cognitivo e nao sintetiza audio diretamente
- fallback deve ser explicito e auditavel
- a v1 deve ser pequena, simples e auditavel

## Criterios de aceite

- existe `Voice Interpreter`
- existe `TTS Router`
- `VoicePlan.provider` deixa de ser decorativo
- pipeline respeita `VoicePlan`
- `Piper` continua operacional
- testes, regressao e smoke passam


---

## Source: `docs/runtime/phase2_5_voice_agent_file_list_v1_0.md`

# Phase 2.5 Voice Agent File List

Versao: 1.0
Status: File list congelada para implementacao controlada
Fase: Phase 2.5A

## Objetivo
Congelar o raio de alteracao da correcao arquitetural do subsistema de voz.

## DiretÃ³rios permitidos

- `backend/app/creative/agents/voice/`
- `backend/app/creative/contracts/`
- `backend/app/creative/orchestrator/`
- `backend/app/content/pipeline/`
- `tests/`
- `docs/runtime/`
- `OUT/audit/phase2_5_voice_agent/`

## Arquivos criados nesta fase

- `backend/app/creative/agents/voice/interpreter.py`
- `backend/app/content/pipeline/tts_router.py`
- `tests/agents/voice/test_voice_interpreter_phase2_5_unittest.py`
- `tests/agents/voice/test_voice_agent_service_phase2_5_unittest.py`
- `tests/agents/voice/test_tts_router_phase2_5_unittest.py`
- `tests/agents/voice/test_voice_plan_integration_phase2_5_unittest.py`
- `docs/runtime/phase2_5_voice_agent_definition_v1_0.md`
- `docs/runtime/phase2_5_voice_agent_file_list_v1_0.md`

## Arquivos alterados permitidos

- `backend/app/creative/agents/voice/models.py`
- `backend/app/creative/agents/voice/service.py`
- `backend/app/creative/contracts/creative_pack.py`
- `backend/app/creative/orchestrator/service.py`
- `backend/app/content/pipeline/service.py`
- `backend/app/content/pipeline/orchestrator.py`
- `backend/app/content/pipeline/tts.py`

Alteracoes condicionais permitidas:

- `backend/app/content/pipeline/models.py`
- `backend/app/creative/orchestrator/events.py`

## IntegraÃ§Ãµes obrigatÃ³rias

- `Voice Agent -> Voice Interpreter`
- `Content Pipeline -> TTS Router`
- `TTS Router -> tts.py`

## IntegraÃ§Ãµes proibidas

- `Voice Agent -> provider TTS direto`
- `Creative Orchestrator -> provider TTS direto`
- `Voice Interpreter -> Content Pipeline direto`
- heuristica cognitiva escondida em `tts.py`

## Testes obrigatÃ³rios

- interpretacao de `hook/setup/payoff`
- `VoicePlan` operativo
- fallback explicito
- respeito a `VoicePlan.provider`
- compatibilidade com `Piper`

## CritÃ©rio de conclusÃ£o

- `VoicePlan` operativo
- `TTS Router` canÃ´nico
- pipeline obedece o plano
- `Piper` preservado
- regressao controlada


---

## Source: `docs/runtime/phase2_5b_kokoro_file_list_v1_0.md`

# Phase 2.5B Kokoro File List

Versao: 1.0
Status: File list congelada para integracao controlada do provider Kokoro

## Escopo permitido

Diretorios:

- `backend/app/content/pipeline/`
- `backend/scripts/`
- `tests/`
- `docs/runtime/`
- `OUT/audit/phase2_5b_kokoro/`
- `OUT/audit/voice_agent_excellence_gate/`

## Arquivos criados

- `backend/app/content/pipeline/kokoro_adapter.py`
- `tests/agents/voice/test_kokoro_adapter_phase2_5b_unittest.py`
- `tests/agents/voice/test_tts_router_kokoro_phase2_5b_unittest.py`
- `tests/agents/voice/test_kokoro_fallback_phase2_5b_unittest.py`
- `docs/runtime/phase2_5b_kokoro_integration_definition_v1_0.md`
- `docs/runtime/phase2_5b_kokoro_file_list_v1_0.md`

## Arquivos alterados permitidos

- `backend/app/content/pipeline/tts_router.py`
- `backend/app/content/pipeline/tts.py`
- `backend/app/content/pipeline/models.py`
- `backend/app/content/pipeline/orchestrator.py`
- `backend/app/content/pipeline/service.py`
- `backend/scripts/run_voice_agent_excellence_gate.ps1`

## Restricoes

- nao alterar a camada cognitiva
- nao bypassar `TTS Router`
- nao quebrar `tts_trace`
- nao remover `Piper` como fallback


---

## Source: `docs/runtime/phase2_5b_kokoro_integration_definition_v1_0.md`

# Phase 2.5B Kokoro Integration

Versao: 1.0
Status: Definicao formal da integracao do provider Kokoro
Dependencia: `Phase 2.5A` concluida

## Objetivo
Introduzir `Kokoro` como provider local principal de TTS sem reabrir a arquitetura da voz.

## Regras

- `VoicePlan`, `Voice Interpreter` e `TTS Router` continuam como base arquitetural
- roteamento de provider continua apenas no `TTS Router`
- `Piper` permanece fallback duro
- esta fase integra apenas `Kokoro`

## Arquitetura alvo

```text
VoicePlan
-> TTS Router
   -> Kokoro (primary)
   -> Piper (fallback)
-> Content Pipeline
```

## Resultado esperado

- voz mais natural que o baseline `Piper`
- arquitetura preservada
- fallback seguro
- comparacao objetiva via rerun do `Voice Agent Excellence Gate`


---

## Source: `docs/runtime/phase2_block1_file_list_v1_0.md`

CortAI - Lista de Arquivos da Primeira Entrega da Fase 2

Bloco 1

Versao: 1.0
Status: Congelado para Implementacao
Documento: `docs/runtime/phase2_block1_file_list_v1_0.md`

---

## 1. Objetivo

Este documento congela a lista exata de arquivos que devem existir na primeira entrega da Fase 2.

O Bloco 1 cobre apenas:

- Creative Orchestrator Service minimo
- Script Agent
- Voice Agent
- Video QC Agent

Este bloco nao deve antecipar:

- Trend Analysis Agent
- Strategy Agent
- Account Health Agent
- Learning Agent
- Experiment Capability formal
- Asset Selection Agent complexo

---

## 2. Regra de Escopo

O Bloco 1 existe para provar que a Fase 2 consegue:

- montar um `creative_pack` minimo
- decidir `script_plan`
- decidir `voice_plan`
- validar qualidade minima via `Video QC Agent`
- entregar a decisao para o pipeline da Fase 1 sem quebrar contratos existentes

Tudo que nao for necessario para esse fluxo fica fora do Bloco 1.

---

## 3. Arquivos a Criar no Bloco 1

### 3.1 Contratos

Criar:

- `backend/app/creative/__init__.py`
- `backend/app/creative/contracts/__init__.py`
- `backend/app/creative/contracts/creative_pack.py`
- `backend/app/creative/contracts/orchestrator_io.py`
- `backend/app/creative/contracts/agent_common.py`

Responsabilidade:

- congelar os contratos canonicos da primeira entrega

### 3.2 Orchestrator

Criar:

- `backend/app/creative/orchestrator/__init__.py`
- `backend/app/creative/orchestrator/models.py`
- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/events.py`

Responsabilidade:

- coordenar `Script Agent`, `Voice Agent` e `Video QC Agent`
- montar `CreativePack`
- aplicar fallback minimo
- emitir eventos `CREATIVE/*`

### 3.3 Script Agent

Criar:

- `backend/app/creative/agents/__init__.py`
- `backend/app/creative/agents/script/__init__.py`
- `backend/app/creative/agents/script/models.py`
- `backend/app/creative/agents/script/service.py`

Responsabilidade:

- produzir `ScriptPlan`
- gerar `hook/setup/payoff`
- usar contexto minimo do input

### 3.4 Voice Agent

Criar:

- `backend/app/creative/agents/voice/__init__.py`
- `backend/app/creative/agents/voice/models.py`
- `backend/app/creative/agents/voice/service.py`

Responsabilidade:

- produzir `VoicePlan`
- preferir provider premium quando configurado
- aplicar fallback explicito para `Piper`

### 3.5 Video QC Agent

Criar:

- `backend/app/creative/agents/video_qc/__init__.py`
- `backend/app/creative/agents/video_qc/models.py`
- `backend/app/creative/agents/video_qc/service.py`

Responsabilidade:

- validar qualidade minima do video apos render
- emitir `APPROVE` ou `REJECT`

### 3.6 Testes

Criar:

- `tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py`
- `tests/agents/script/test_script_agent_phase2_unittest.py`
- `tests/agents/voice/test_voice_agent_phase2_unittest.py`
- `tests/agents/video_qc/test_video_qc_agent_phase2_unittest.py`
- `tests/runtime/pipeline/test_phase2_block1_smoke_unittest.py`

Responsabilidade:

- travar contratos
- validar fallback
- validar integracao minima com a Fase 1

---

## 4. Arquivos que Nao Devem Ser Criados Ainda

Nao criar no Bloco 1:

- `backend/app/creative/context/repository.py`
- `backend/app/creative/context/file_store.py`
- `backend/app/creative/context/pg_store.py`
- `backend/app/creative/agents/trend_analysis/*`
- `backend/app/creative/agents/strategy/*`
- `backend/app/creative/agents/account_health/*`
- `backend/app/creative/agents/learning/*`
- `backend/app/creative/agents/asset_selection/*`
- `backend/app/creative/capabilities/experiment/*`
- testes desses modulos

Motivo:

- tudo isso pertence a blocos posteriores
- criar agora aumenta risco de deriva e acoplamento prematuro

---

## 5. Contratos Minimos por Arquivo

### 5.1 `creative_pack.py`

Deve definir:

- `CreativePack`
- `ScriptPlan`
- `VoicePlan`

Campos minimos:

- `creative_pack_id`
- `account_id`
- `niche`
- `topic`
- `script_plan`
- `voice_plan`
- `generated_at`
- `orchestrator_version`

### 5.2 `orchestrator_io.py`

Deve definir:

- `CreativeOrchestratorInput`
- `CreativeOrchestratorResult`

Campos minimos de input:

- `account_id`
- `niche`
- `topic`
- `publish_slot`

Campos minimos de result:

- `creative_pack`
- `fallbacks_used`
- `events_emitted`

### 5.3 `agent_common.py`

Deve definir:

- `AgentFailure`
- `FallbackDecision`

Enums minimos:

- `DecisionStatus`
- `FailureSeverity`

### 5.4 `script/models.py`

Deve definir:

- `ScriptAgentInput`
- `ScriptAgentResult`

### 5.5 `voice/models.py`

Deve definir:

- `VoiceAgentInput`
- `VoiceAgentResult`

### 5.6 `video_qc/models.py`

Deve definir:

- `VideoQcInput`
- `VideoQcResult`

Campos minimos:

- `status`
- `reasons`
- `checked_at`

---

## 6. Integracao Minima com a Fase 1

O Bloco 1 deve integrar sem alterar contratos existentes.

Fluxo minimo permitido:

```text
Creative Orchestrator
-> Content Pipeline (Fase 1)
-> Video QC Agent
-> Safety Layer
```

Regras:

- `Creative Orchestrator` nao escreve `publish_record`
- `Video QC Agent` roda antes do `Safety Layer`
- se `Video QC Agent` retornar `REJECT`, o fluxo para
- `Safety Layer` continua sendo a autoridade de risco

---

## 7. Criterio de Conclusao do Bloco 1

O Bloco 1 so pode ser considerado concluido se:

1. todos os arquivos desta lista existirem
2. nenhum arquivo fora do escopo tiver sido introduzido
3. os testes do Bloco 1 estiverem verdes
4. um smoke minimo provar:
   - `Creative Orchestrator`
   - `Script Agent`
   - `Voice Agent`
   - `Content Pipeline`
   - `Video QC Agent`
   - `Safety Layer`
5. a baseline da Fase 1 continuar verde

---

## 8. Conclusao

Com esta lista, a primeira entrega da Fase 2 deixa de ser ambigua.

O Bloco 1 fica congelado como um slice pequeno, auditavel e implementavel sem invadir os blocos seguintes.


---

## Source: `docs/runtime/phase2_block2_definition_v1_0.md`

CortAI - Definicao do Bloco 2 da Fase 2

Strategy and Account Health Layer

Versao: 1.0
Status: Aprovado para Implementacao
Documento: `docs/runtime/phase2_block2_definition_v1_0.md`

---

## 1. Objetivo

Este documento define o escopo, os contratos minimos, o fluxo e os criterios de conclusao do Bloco 2 da Fase 2 do CortAI.

O Bloco 2 introduz a primeira camada de decisao estrategica por conta, sem expandir para contexto externo amplo, aprendizado adaptativo completo ou experimentacao formal.

O objetivo deste bloco e responder, de forma controlada e auditavel:

- qual objetivo esta conta esta perseguindo agora
- qual abordagem de conteudo faz sentido para esta conta
- se a conta deve operar em modo `SAFE`, `CAUTION` ou `HOLD`
- se a producao atual deve ser mais agressiva ou mais conservadora

---

## 2. Escopo do Bloco 2

O Bloco 2 cobre apenas:

- `Strategy Agent`
- `Account Health Agent`

Nada alem disso.

### 2.1 Escopo proibido

Nao implementar neste bloco:

- `Trend Analysis Agent`
- `Learning Agent`
- `Experiment Capability` formal
- `Asset Selection Agent`
- qualquer mudanca estrutural na Fase 1
- qualquer alteracao em runtime, scheduler, safety, `publish_record`, metrics, analysis, simulation ou consistency fora da integracao minima permitida

---

## 3. Papel do Bloco 2 na Fase 2

O Bloco 1 provou a camada cognitiva minima:

`Creative Orchestrator -> Script Agent -> Voice Agent -> Content Pipeline -> Video QC`

O Bloco 2 adiciona a primeira decisao contextual por conta:

`Account Health Agent -> Strategy Agent -> Creative Orchestrator -> Bloco 1 -> Fase 1`

Em termos prÃ¡ticos:

- `Account Health Agent` protege a conta
- `Strategy Agent` orienta o modo de conteudo
- `Creative Orchestrator` passa a consumir essas decisoes

---

## 4. Regras Arquiteturais

### 4.1 Nao regredir a Fase 1

O Bloco 2 nao pode:

- alterar contratos da Fase 1
- alterar comportamento do runtime
- alterar comportamento do safety
- alterar `publish_record`
- alterar `metrics collector`
- alterar `analysis layer`

### 4.2 Nao regredir o Bloco 1

O Bloco 2 nao pode quebrar:

- `Creative Orchestrator` minimo
- `Script Agent`
- `Voice Agent`
- `Video QC Agent`
- smoke aprovado do Bloco 1

### 4.3 Orquestracao centralizada

`Strategy Agent` e `Account Health Agent` nao chamam runtime, safety ou pipeline diretamente.

Toda coordenacao passa pelo `Creative Orchestrator Service`.

### 4.4 Decisao, nao execucao

O Bloco 2 decide e recomenda.

O Bloco 2 nao:

- publica
- grava `publish_record`
- dispara `metrics`
- altera artefatos apos render

---

## 5. Componentes do Bloco 2

### 5.1 Account Health Agent

#### Objetivo

Avaliar a saude operacional da conta antes da geracao criativa.

#### Entrada minima

- `account_id`
- historico recente
- sinais operacionais
- frequencia de publicacao
- repeticao de formato
- queda brusca de views, quando houver

#### Saida minima

- `health_status`
- `reasons`
- `recommended_constraints`

#### Valores validos de `health_status`

- `SAFE`
- `CAUTION`
- `HOLD`

#### Papel no fluxo

- `SAFE`: fluxo segue normalmente
- `CAUTION`: fluxo segue com restricoes recomendadas
- `HOLD`: fluxo deve parar antes da geracao criativa

### 5.2 Strategy Agent

#### Objetivo

Gerar um `strategy_profile` minimo por conta, com base no estado atual da conta e sinais basicos de performance.

#### Entrada minima

- `account_id`
- `account_profile`
- metricas recentes
- objetivo da conta
- sinais basicos de performance
- `health_status`

#### Saida minima

- `strategy_profile`

#### Campos minimos de `strategy_profile`

- `goal`
- `content_mode`
- `hook_aggressiveness`
- `target_duration_range`
- `variation_policy`

#### Papel no fluxo

Orientar o `Creative Orchestrator` sem substituir `Script Agent`, `Voice Agent` ou `Video QC Agent`.

---

## 6. Fluxo do Bloco 2

Fluxo minimo permitido:

```text
Account Health Agent
-> Strategy Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline
-> Video QC Agent
-> Safety Layer
```

### 6.1 Regra de parada

Se `Account Health Agent` retornar `HOLD`:

- o fluxo deve parar
- o `Creative Orchestrator` nao deve montar `creative_pack`
- o pipeline nao deve rodar
- nenhum `publish_record` deve ser gerado

### 6.2 Regra de continuidade

Se `Account Health Agent` retornar `SAFE` ou `CAUTION`:

- o fluxo pode seguir
- `Strategy Agent` deve receber o `health_status`
- o `Creative Orchestrator` deve consumir `strategy_profile`

---

## 7. Contratos Minimos do Bloco 2

### 7.1 Account Health Agent

Entrada minima:

- `account_id`
- `recent_publish_count`
- `recent_format_repetition_ratio`
- `recent_views_drop_ratio`
- `recent_low_performance_streak`

Saida minima:

```json
{
  "status": "CAUTION",
  "reasons": ["RECENT_VIEWS_DROP"],
  "recommended_constraints": {
    "reduce_hook_aggressiveness": true,
    "max_daily_posts": 1
  }
}
```

### 7.2 Strategy Agent

Entrada minima:

- `account_id`
- `account_goal`
- `recent_metrics_summary`
- `health_status`
- `recommended_constraints`

Saida minima:

```json
{
  "goal": "stabilize_growth",
  "content_mode": "conservative_dark",
  "hook_aggressiveness": "medium",
  "target_duration_range": "8-12s",
  "variation_policy": "low"
}
```

### 7.3 Integracao com o Creative Orchestrator

O `Creative Orchestrator` passa a consumir:

- `health_status`
- `recommended_constraints`
- `strategy_profile`

Mas continua sendo o unico componente autorizado a:

- montar o `creative_pack`
- chamar `Script Agent`
- chamar `Voice Agent`
- iniciar o fluxo criativo do slice cognitivo

---

## 8. Fallbacks Obrigatorios

### 8.1 Account Health Agent

Se nao houver historico suficiente:

- retornar `SAFE`
- marcar motivo: `ACCOUNT_HEALTH_COLD_START`
- usar `recommended_constraints` vazias ou minimas

O agente nao pode falhar silenciosamente.

### 8.2 Strategy Agent

Se nao houver dados suficientes para estrategia contextual:

- usar `default_strategy_profile`
- marcar motivo: `STRATEGY_COLD_START`

O agente nao pode retornar perfil vazio.

### 8.3 Creative Orchestrator

Se o `Account Health Agent` ou o `Strategy Agent` falhar sem fallback:

- o fluxo deve falhar explicitamente
- o motivo deve ser materializado

---

## 9. Persistencia Minima do Bloco 2

Neste bloco, a persistencia deve ser minima e auditavel.

Persistir:

- `account_health_decision`
- `strategy_profile`

Formato aceitavel neste slice:

- JSON/JSONL auditavel em diretorio da camada cognitiva

Regra:

- nao criar storage paralelo arbitrario
- nao reescrever historico bruto
- nao tornar o storage mais complexo do que o necessario para o bloco

---

## 10. Eventos Minimos do Bloco 2

Eventos minimos a introduzir:

- `CREATIVE/account_health_safe`
- `CREATIVE/account_health_caution`
- `CREATIVE/account_health_hold`
- `CREATIVE/strategy_profile_generated`

Regra:

- o dominio continua sendo `CREATIVE/*`
- nao introduzir eventos `SAFETY/*`, `CONTENT/*` ou `RUNTIME/*` a partir do Bloco 2

---

## 11. Testes Obrigatorios

O Bloco 2 deve entrar com testes minimos para:

- `Account Health Agent`
- `Strategy Agent`
- integracao do `Creative Orchestrator` consumindo ambos
- smoke pequeno do fluxo:
  - `Account Health Agent`
  - `Strategy Agent`
  - `Creative Orchestrator`
  - `Script Agent`
  - `Voice Agent`
  - `Content Pipeline`
  - `Video QC Agent`

Tambem devem ser rerodados:

- testes do Bloco 1
- regresses relevantes da Fase 1

---

## 12. Criterio de Conclusao do Bloco 2

O Bloco 2 so pode ser considerado concluido se:

1. `Strategy Agent` gerar `strategy_profile` valido
2. `Account Health Agent` gerar `health_status` valido
3. `Creative Orchestrator` consumir ambos sem quebrar o fluxo do Bloco 1
4. `HOLD` impedir execucao criativa
5. `SAFE` e `CAUTION` permitirem continuidade controlada
6. testes do Bloco 2 passarem
7. smoke do Bloco 2 passar
8. nenhuma regressao da Fase 1 ou do Bloco 1 for detectada

---

## 13. Fora de Escopo

Nao fazem parte do Bloco 2:

- contexto de tendencia amplo
- aprendizado adaptativo real
- assignment experimental formal
- selecao visual estrategica avancada
- otimizacao multiagente

Esses temas pertencem aos blocos seguintes.

---

## 14. Conclusao

O Bloco 2 existe para provar a primeira decisao contextual por conta na camada cognitiva.

Ele nao amplia o sistema para contexto externo amplo nem para aprendizado pleno.

Ele apenas introduz, de forma controlada:

- protecao por saude de conta
- estrategia minima por conta
- alimentacao contextual do `Creative Orchestrator`

Com isso, a Fase 2 avanca de:

`execucao cognitiva minima`

para:

`decisao cognitiva contextual por conta`


---

## Source: `docs/runtime/phase2_block2_file_list_v1_0.md`

CortAI - Lista de Arquivos do Bloco 2 da Fase 2

Strategy and Account Health Layer

Versao: 1.0
Status: Congelado para Implementacao
Documento: `docs/runtime/phase2_block2_file_list_v1_0.md`

---

## 1. Objetivo do Documento

Este documento congela a lista exata de arquivos e modulos que podem nascer no Bloco 2 da Fase 2, evitando deriva de implementacao.

O Bloco 2 introduz apenas:

- `Strategy Agent`
- `Account Health Agent`

Nenhum outro agente deve ser criado neste slice.

---

## 2. Diretorios Permitidos

Todos os arquivos novos devem nascer dentro de:

- `backend/app/creative/agents/`

Subdiretorios permitidos neste bloco:

- `backend/app/creative/agents/strategy/`
- `backend/app/creative/agents/account_health/`

Nenhum outro diretorio novo deve ser criado neste bloco.

---

## 3. Arquivos a Criar

### 3.1 Strategy Agent

Criar:

- `backend/app/creative/agents/strategy/__init__.py`
- `backend/app/creative/agents/strategy/models.py`
- `backend/app/creative/agents/strategy/service.py`

#### `models.py`

Deve definir:

- `StrategyInput`
- `StrategyProfile`
- `StrategyResult`

#### `service.py`

Deve implementar:

- `StrategyAgentService`

Responsabilidade:

- gerar `strategy_profile`
- aplicar fallback minimo
- nao executar pipeline
- nao chamar runtime

### 3.2 Account Health Agent

Criar:

- `backend/app/creative/agents/account_health/__init__.py`
- `backend/app/creative/agents/account_health/models.py`
- `backend/app/creative/agents/account_health/service.py`

#### `models.py`

Deve definir:

- `AccountHealthInput`
- `AccountHealthStatus`
- `AccountHealthDecision`
- `AccountHealthResult`

#### `service.py`

Deve implementar:

- `AccountHealthAgentService`

Responsabilidade:

- gerar `health_status`
- produzir `reasons`
- produzir `recommended_constraints`
- aplicar fallback minimo

---

## 4. Arquivos de Teste Obrigatorios

Criar:

- `tests/agents/strategy/test_strategy_agent_phase2_unittest.py`
- `tests/agents/account_health/test_account_health_agent_phase2_unittest.py`
- `tests/runtime/pipeline/test_phase2_block2_smoke_unittest.py`

Responsabilidade:

- validar contratos minimos
- validar fallback
- validar integracao do `Creative Orchestrator` com ambos os agentes
- validar comportamento de `HOLD`

---

## 5. Arquivos que Nao Devem Nascer Agora

Proibido criar neste bloco:

- `backend/app/creative/agents/trend_analysis/*`
- `backend/app/creative/agents/learning/*`
- `backend/app/creative/agents/asset_selection/*`
- `backend/app/creative/capabilities/experiment/*`
- `backend/app/creative/context/*`
- `backend/app/creative/rag/*`

Tambem e proibido:

- alterar a lista de arquivos do Bloco 1
- criar novos contratos canonicos fora do que ja foi congelado
- criar storage paralelo para a Fase 2

Esses itens pertencem a blocos posteriores.

---

## 6. Contratos Minimos por Arquivo

### 6.1 `strategy/models.py`

Deve definir:

- `StrategyInput`
- `StrategyProfile`
- `StrategyResult`

Campos minimos de `StrategyInput`:

- `account_id`
- `account_goal`
- `recent_metrics_summary`
- `health_status`
- `recommended_constraints`

Campos minimos de `StrategyProfile`:

- `goal`
- `content_mode`
- `hook_aggressiveness`
- `target_duration_range`
- `variation_policy`

### 6.2 `account_health/models.py`

Deve definir:

- `AccountHealthInput`
- `AccountHealthStatus`
- `AccountHealthDecision`
- `AccountHealthResult`

Campos minimos de `AccountHealthInput`:

- `account_id`
- `recent_publish_count`
- `recent_format_repetition_ratio`
- `recent_views_drop_ratio`
- `recent_low_performance_streak`

Campos minimos de `AccountHealthDecision`:

- `status`
- `reasons`
- `recommended_constraints`

Valores validos de `AccountHealthStatus`:

- `SAFE`
- `CAUTION`
- `HOLD`

---

## 7. Integracao Permitida com Bloco 1

`Strategy Agent` e `Account Health Agent` podem ser utilizados apenas pelo:

- `Creative Orchestrator Service`

Fluxo permitido:

```text
Account Health Agent
-> Strategy Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline
-> Video QC
```

Regra:

- `Creative Orchestrator` continua sendo o ponto central da camada cognitiva
- os agentes do Bloco 2 nao chamam agentes do Bloco 1 diretamente

---

## 8. Integracao Proibida

Nao e permitido neste bloco:

- chamar runtime diretamente
- alterar safety
- alterar `publish_record`
- alterar `metrics`
- alterar o pipeline da Fase 1 fora do ponto minimo de integracao no `Creative Orchestrator`
- escrever diretamente em storage operacional da Fase 1

---

## 9. Fallback Obrigatorio

### 9.1 Strategy Agent

Fallback minimo:

- `strategy_profile = DEFAULT`

Exemplo minimo:

- `goal = retention`
- `content_mode = standard`
- `hook_aggressiveness = medium`
- `target_duration_range = 8-12s`
- `variation_policy = low`

Regra:

- o `Strategy Agent` nunca pode retornar perfil vazio

### 9.2 Account Health Agent

Fallback minimo:

- `health_status = SAFE`
- `reasons = ["fallback_default"]`
- `recommended_constraints = {}`

Regra:

- fallback nunca deve bloquear publicacao
- `HOLD` nao pode ser emitido por fallback

---

## 10. Criterio de Conclusao do Bloco 2

O Bloco 2 e considerado concluido quando:

1. `Strategy Agent` gera `strategy_profile`
2. `Account Health Agent` gera `health_status`
3. `Creative Orchestrator` consome ambos
4. o fluxo completo continua funcionando
5. `HOLD` impede o fluxo criativo
6. testes passam
7. smoke passa
8. nenhuma regressao da Fase 1 e do Bloco 1 e detectada

---

## 11. Conclusao

Com esta lista, o Bloco 2 fica congelado como um slice pequeno, auditavel e controlado.

O objetivo nao e ampliar a Fase 2 inteira, mas adicionar exatamente a primeira camada de decisao por conta:

- saude da conta
- estrategia por conta

Nada alem disso.


---

## Source: `docs/runtime/phase2_block3_definition_v1_0.md`

CortAI - Fase 2

Bloco 3 - Trend Context and Visual Context

Documento: `docs/runtime/phase2_block3_definition_v1_0.md`
Versao: 1.0
Status: Aprovado para Implementacao (escopo congelado)

---

## 1. Objetivo do Bloco 3

O Bloco 3 introduz contexto externo de tendencia e contexto visual na camada cognitiva do CortAI.

Ate o Bloco 2, o sistema ja possui:

- decisao de saude da conta
- decisao estrategica
- geracao de script
- escolha de voz
- pipeline de geracao
- verificacao de qualidade

O Bloco 3 adiciona duas capacidades fundamentais:

1. `Trend Analysis Agent`
2. `Asset Selection Agent`

Esses agentes permitem que o conteudo passe a considerar:

- padroes de conteudo bem-sucedidos no nicho
- estilo visual coerente com a estrategia
- variacao visual consistente

---

## 2. Escopo Estrito do Bloco 3

O Bloco 3 implementa apenas:

- `Trend Analysis Agent` (manual-curated MVP)
- `Asset Selection Agent`

Nada alem disso.

---

## 3. Escopo Proibido

Nao fazem parte do Bloco 3:

- `Learning / Optimization Agent`
- `Experiment Agent` formal
- RAG completo
- scraping automatizado de plataformas
- automacao de analise massiva de conteudo
- alteracao estrutural da Fase 1
- alteracao estrutural dos Blocos 1 ou 2

O Bloco 3 nao introduz aprendizado adaptativo.

Ele apenas adiciona contexto externo estruturado.

---

## 4. Arquitetura do Bloco 3

Apos o Bloco 3, o fluxo cognitivo passa a ser:

```text
Account Health Agent
-> Trend Analysis Agent
-> Strategy Agent
-> Asset Selection Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline (Fase 1)
-> Video QC Agent
```

---

## 5. Trend Analysis Agent

### Objetivo

Fornecer ao sistema um perfil estruturado de tendencias por nicho.

Esse perfil e utilizado para influenciar:

- estilo de hook
- estrutura narrativa
- pacing
- estilo visual

### Implementacao MVP

O `Trend Analysis Agent` nao coleta dados automaticamente.

Ele apenas le perfis de tendencia curados manualmente.

### Fonte de dados

Arquivos em:

- `backend/data/trends/`

Exemplo:

- `backend/data/trends/horror.json`
- `backend/data/trends/history.json`
- `backend/data/trends/true_crime.json`

### Estrutura minima do Trend Profile

Exemplo:

```json
{
  "niche": "horror",
  "dominant_hooks": [
    "question",
    "shock_statement",
    "story_opening"
  ],
  "avg_duration": "35-60",
  "pacing": "fast_first_3s",
  "visual_style": "dark_backgrounds",
  "text_style": "large_caption_focus"
}
```

### Saida do agente

- `trend_profile`

Esse objeto sera incluido no contexto consumido pelo `Strategy Agent` e `Asset Selection Agent`.

### Fallback obrigatorio

Se o arquivo de tendencia nao existir:

- `trend_profile = DEFAULT`

Nunca interromper o fluxo por ausencia de tendencia.

---

## 6. Asset Selection Agent

### Objetivo

Selecionar assets visuais coerentes com a estrategia e o nicho.

### Responsabilidades

Escolher:

- background do hook
- background do setup
- background do payoff
- estilo visual dominante

### Entradas

O agente recebe:

- `strategy_profile`
- `trend_profile`
- `niche`
- `topic`

### Saida

- `asset_selection`

Exemplo:

- `hook_background`
- `setup_background`
- `payoff_background`
- `visual_style`
- `motion_profile`

### Integracao

O resultado do `Asset Selection Agent` e incluido no:

- `creative_pack`

---

## 7. Integracao com Creative Orchestrator

O `Creative Orchestrator` passa a chamar:

```text
Trend Analysis Agent
-> Strategy Agent
-> Asset Selection Agent
```

E incluir no `creative_pack`:

- `trend_profile`
- `strategy_profile`
- `asset_selection`

---

## 8. Persistencia

O Bloco 3 utiliza apenas persistencia simples.

Arquivos:

- `backend/data/trends/*.json`

Nenhuma base vetorial e introduzida nesta etapa.

---

## 9. Eventos Cognitivos

Eventos minimos introduzidos:

- `TREND_PROFILE_LOADED`
- `TREND_PROFILE_FALLBACK`
- `ASSET_SELECTION_GENERATED`
- `ASSET_SELECTION_FALLBACK`

Esses eventos devem ser emitidos pelo `Creative Orchestrator`.

---

## 10. Testes Obrigatorios

Devem ser criados testes para:

- `Trend Analysis Agent`
- `Asset Selection Agent`
- smoke do Bloco 3

Arquivos esperados:

- `tests/agents/trend_analysis/test_trend_analysis_agent_phase2_unittest.py`
- `tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py`
- `tests/runtime/pipeline/test_phase2_block3_smoke_unittest.py`

---

## 11. Smoke do Bloco 3

Fluxo minimo esperado:

```text
Account Health Agent
-> Trend Analysis Agent
-> Strategy Agent
-> Asset Selection Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline
-> Video QC
```

Resultado esperado:

- `trend_profile_loaded = true`
- `asset_selection_generated = true`
- `pipeline_status = READY`
- `video_qc_status = APPROVE`

---

## 12. Criterio de Conclusao do Bloco 3

O Bloco 3 sera considerado concluido quando:

- `Trend Analysis Agent` funcionar
- `Asset Selection Agent` funcionar
- `Creative Orchestrator` consumir ambos
- `creative_pack` incluir `trend_profile` e `asset_selection`
- pipeline continuar funcionando
- testes passarem
- smoke passar
- nenhuma regressao da Fase 1
- nenhuma regressao dos Blocos 1 ou 2

---

## 13. Resultado Esperado do Bloco 3

Apos a conclusao do Bloco 3, o CortAI passa a gerar conteudo considerando:

- saude da conta
- estrategia da conta
- tendencias do nicho
- coerencia visual do conteudo

Esse e o primeiro ponto em que o sistema passa a operar com contexto criativo externo estruturado.

---

## 14. Estado da Fase 2 apos Bloco 3

### Bloco 1

- `Creative Orchestrator`
- `Script Agent`
- `Voice Agent`
- `Video QC`

### Bloco 2

- `Strategy Agent`
- `Account Health Agent`

### Bloco 3

- `Trend Analysis Agent`
- `Asset Selection Agent`


---

## Source: `docs/runtime/phase2_block3_file_list_v1_0.md`

CortAI - Lista de Arquivos do Bloco 3 da Fase 2

Trend Context and Visual Context

Versao: 1.0
Status: Congelado para Implementacao
Documento: `docs/runtime/phase2_block3_file_list_v1_0.md`

---

## 1. Objetivo do Documento

Este documento congela a lista exata de arquivos e modulos que podem nascer no Bloco 3 da Fase 2, evitando deriva de implementacao.

O Bloco 3 introduz apenas:

- `Trend Analysis Agent`
- `Asset Selection Agent`

Nenhum outro agente deve ser criado neste slice.

---

## 2. Diretorios Permitidos

Todos os arquivos novos devem nascer dentro de:

- `backend/app/creative/agents/`

Subdiretorios permitidos neste bloco:

- `backend/app/creative/agents/trend_analysis/`
- `backend/app/creative/agents/asset_selection/`

Nenhum outro diretorio novo deve ser criado neste bloco.

---

## 3. Arquivos Exatos a Criar

### 3.1 Trend Analysis Agent

Criar:

- `backend/app/creative/agents/trend_analysis/__init__.py`
- `backend/app/creative/agents/trend_analysis/models.py`
- `backend/app/creative/agents/trend_analysis/service.py`

#### `models.py`

Deve definir:

- `TrendAnalysisInput`
- `TrendProfile`
- `TrendAnalysisResult`

#### `service.py`

Deve implementar:

- `TrendAnalysisAgentService`

Responsabilidade:

- carregar `trend_profile` do nicho
- aplicar fallback para `DEFAULT`
- nao fazer scraping
- nao depender de API externa

### 3.2 Asset Selection Agent

Criar:

- `backend/app/creative/agents/asset_selection/__init__.py`
- `backend/app/creative/agents/asset_selection/models.py`
- `backend/app/creative/agents/asset_selection/service.py`

#### `models.py`

Deve definir:

- `AssetSelectionInput`
- `AssetSelection`
- `AssetSelectionResult`

#### `service.py`

Deve implementar:

- `AssetSelectionAgentService`

Responsabilidade:

- escolher `hook_background`
- escolher `setup_background`
- escolher `payoff_background`
- escolher `visual_style`
- escolher `motion_profile`
- aplicar fallback para selecao default

---

## 4. Arquivos de Teste Obrigatorios

Criar:

- `tests/agents/trend_analysis/test_trend_analysis_agent_phase2_unittest.py`
- `tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py`
- `tests/runtime/pipeline/test_phase2_block3_smoke_unittest.py`

Responsabilidade:

- validar contratos minimos
- validar fallback
- validar integracao do `Creative Orchestrator` com ambos os agentes

---

## 5. Integracao Minima Permitida

Alteracoes minimas permitidas em:

- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/models.py`
- `backend/app/creative/contracts/creative_pack.py`

Objetivo da integracao:

- permitir que o `Creative Orchestrator` consuma `trend_profile`
- permitir que o `Creative Orchestrator` consuma `asset_selection`
- incluir ambos no `creative_pack`

Nenhuma outra alteracao estrutural e permitida.

---

## 6. Integracoes Proibidas

Nao e permitido criar neste bloco:

- `Learning Agent`
- `Experiment Agent` formal
- RAG
- scraping automatico
- storage novo fora do permitido
- qualquer mudanca estrutural na Fase 1
- qualquer alteracao estrutural dos Blocos 1 ou 2

Tambem nao e permitido:

- chamar runtime diretamente
- alterar `safety`
- alterar `publish_record`
- alterar `metrics`

---

## 7. Fallback Obrigatorio

### 7.1 Trend Analysis Agent

Se nao houver profile do nicho:

- `trend_profile = DEFAULT`

Regra:

- nunca interromper o fluxo por ausencia de trend profile

### 7.2 Asset Selection Agent

Se falhar a selecao contextual:

- `asset_selection = DEFAULT`

Regra:

- nunca interromper o fluxo criativo por ausencia de asset especializado
- o fallback deve continuar compatÃ­vel com a baseline da Fase 1

---

## 8. CritÃ©rio de Conclusao do Bloco 3

O Bloco 3 sera considerado concluido quando:

1. `trend_profile` for carregado ou cair em fallback controlado
2. `asset_selection` for gerado ou cair em fallback controlado
3. o `Creative Orchestrator` consumir ambos
4. o `creative_pack` incluir ambos
5. o pipeline continuar funcionando
6. smoke do Bloco 3 passar
7. regressao do Bloco 1 passar
8. regressao do Bloco 2 passar
9. regressao relevante da Fase 1 passar

---

## 9. Conclusao

Com esta lista, o Bloco 3 fica congelado como um slice pequeno, auditavel e controlado.

O objetivo e adicionar exatamente:

- contexto externo estruturado por nicho
- contexto visual coerente com a estrategia

Nada alem disso.


---

## Source: `docs/runtime/phase2_block4_definition_v1_0.md`

CortAI - Fase 2

Bloco 4 - Learning & Experiment Control

Documento: `docs/runtime/phase2_block4_definition_v1_0.md`
Versao: 1.0
Status: Aprovado para Implementacao (escopo congelado)

---

## 1. Objetivo do Bloco 4

O Bloco 4 introduz a primeira capacidade real de adaptacao orientada por dados dentro da camada cognitiva do CortAI.

Ate o Bloco 3, o sistema ja possui:

- controle de qualidade do video
- geracao de script
- selecao de voz
- estrategia por conta
- health por conta
- contexto de tendencias
- contexto visual

O Bloco 4 adiciona duas capacidades:

1. `Learning / Optimization Agent`
2. formalizacao da `Experiment Capability`

O objetivo nao e treinar modelos nem implementar aprendizado pesado.
O objetivo e permitir que o sistema:

- leia sinais relevantes de performance
- gere recomendacoes estruturadas
- formalize variantes de experimento de forma canonica
- alimente os agentes ja existentes com contexto de otimizacao

---

## 2. Escopo Estrito do Bloco 4

O Bloco 4 implementa apenas:

- `Learning / Optimization Agent`
- formalizacao da `Experiment Capability`

Nada alem disso.

---

## 3. Escopo Proibido

Nao fazem parte do Bloco 4:

- RAG
- scraping automatizado
- fine-tuning
- LoRA
- RL
- treinamento de modelo
- agent framework generico
- `Experiment Agent` separado/autonomo alem do necessario
- alteracao estrutural da Fase 1
- alteracao estrutural dos Blocos 1, 2 ou 3 fora da integracao minima permitida

O Bloco 4 nao implementa aprendizado de pesos de modelo.
Ele implementa aprendizado estrategico e operacional leve.

---

## 4. Arquitetura do Bloco 4

Apos o Bloco 4, o fluxo cognitivo passa a ser:

```text
Account Health Agent
-> Trend Analysis Agent
-> Learning / Optimization Agent
-> Strategy Agent
-> Experiment Capability
-> Asset Selection Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline (Fase 1)
-> Video QC Agent
```

---

## 5. Learning / Optimization Agent

### Objetivo

Ler dados de performance ja existentes no sistema e produzir recomendacoes estruturadas para melhorar os proximos batches.

### Fontes permitidas

O agente pode ler apenas fontes ja existentes e aprovadas:

- `publish_records`
- `video_metrics`
- outputs de `analysis`
- outputs de `attribution`
- resultados de experimentos ja registrados
- `strategy profiles` recentes
- `qc history`

### O que ele produz

O agente gera um objeto como:

- `learning_insights`

Exemplos de conteudo:

- hooks que performaram melhor
- duracao mais eficiente
- tipos de visual mais fortes
- vozes que performaram melhor
- sinais de saturacao
- recomendacoes de variacao

### Exemplos de recomendacao

- preferir hook tipo `question`
- reduzir duracao para `35-45s`
- evitar `visual_style X` em conta `Y`
- aumentar agressividade do hook em conta `Z`
- diminuir repeticao de background

### Papel arquitetural

O agente nao altera diretamente outros agentes.
Ele apenas produz recomendacoes estruturadas e auditaveis.

Essas recomendacoes sao consumidas por:

- `Strategy Agent`
- `Script Agent`
- `Asset Selection Agent`
- `Voice Agent`

### Fallback obrigatorio

Se nao houver dados suficientes:

- `learning_insights = DEFAULT`

Nunca falhar o fluxo por ausencia de historico.

---

## 6. Experiment Capability

### Objetivo

Formalizar a variacao experimental ja prevista na arquitetura.

No Bloco 4, isso continua sendo uma capability, nao um agente autonomo completo.

### Papel

Permitir que o sistema produza variantes controladas, por exemplo:

- `hook A / hook B`
- duracao curta / media
- `visual_style A / visual_style B`
- `voice style A / voice style B`

### Base tecnica

A `Experiment Capability` deve usar o `D31 Experiment Framework` ja existente na Fase 1.

### Resultado esperado

A capability deve produzir um objeto como:

- `experiment_plan`

Exemplo:

- `experiment_id`
- `variant_id`
- `variant_type`
- `variant_params`

### Integracao

O `experiment_plan` deve ser consumido por:

- `Strategy Agent`
- `Script Agent`
- `Asset Selection Agent`
- `Voice Agent`

### Limite do Bloco 4

O Bloco 4 nao cria um `Experiment Agent` superautonomo.

Ele apenas:

- formaliza o plano experimental
- padroniza a estrutura de variantes
- injeta esse contexto no fluxo cognitivo

---

## 7. Integracao com Creative Orchestrator

O `Creative Orchestrator` passa a consumir:

- `learning_insights`
- `experiment_plan`

E incluir ambos no `creative_pack`.

---

## 8. Persistencia

O Bloco 4 utiliza persistencia simples e auditavel.

### Learning insights

Exemplo de local:

- `backend/data/learning/`

### Experiment plans

Exemplo de local:

- `backend/data/experiments/`

A persistencia principal pode continuar apoiada em storage ja existente, com backup em JSON/JSONL.

---

## 9. Eventos Cognitivos

Eventos minimos introduzidos:

- `LEARNING_INSIGHTS_GENERATED`
- `LEARNING_INSIGHTS_FALLBACK`
- `EXPERIMENT_PLAN_GENERATED`
- `EXPERIMENT_PLAN_FALLBACK`

Esses eventos devem ser emitidos pelo `Creative Orchestrator`.

---

## 10. Testes Obrigatorios

Devem ser criados testes para:

- `Learning / Optimization Agent`
- `Experiment Capability`
- smoke do Bloco 4

Arquivos esperados:

- `tests/agents/learning/test_learning_agent_phase2_unittest.py`
- `tests/experiment/test_experiment_capability_phase2_unittest.py`
- `tests/runtime/pipeline/test_phase2_block4_smoke_unittest.py`

---

## 11. Smoke do Bloco 4

Fluxo minimo esperado:

```text
Account Health Agent
-> Trend Analysis Agent
-> Learning / Optimization Agent
-> Strategy Agent
-> Experiment Capability
-> Asset Selection Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline
-> Video QC
```

Resultado esperado:

- `learning_insights_generated = true`
- `experiment_plan_generated = true`
- `pipeline_status = READY`
- `video_qc_status = APPROVE`

---

## 12. Criterio de Conclusao do Bloco 4

O Bloco 4 sera considerado concluido quando:

- `Learning / Optimization Agent` funcionar
- `Experiment Capability` funcionar
- `Creative Orchestrator` consumir ambos
- `creative_pack` incluir `learning_insights` e `experiment_plan`
- pipeline continuar funcionando
- testes passarem
- smoke passar
- nenhuma regressao da Fase 1
- nenhuma regressao dos Blocos 1, 2 ou 3

---

## 13. Resultado Esperado do Bloco 4

Apos a conclusao do Bloco 4, o CortAI passa a operar com:

- contexto de saude da conta
- contexto estrategico
- contexto de tendencia
- contexto visual
- contexto de aprendizado
- variacao experimental formalizada

Esse e o primeiro ponto em que o sistema comeca a se tornar adaptativo de forma explicita, ainda sem depender de treinamento pesado ou RAG.

---

## 14. Estado da Fase 2 apos Bloco 4

### Bloco 1

- `Creative Orchestrator`
- `Script Agent`
- `Voice Agent`
- `Video QC`

### Bloco 2

- `Strategy Agent`
- `Account Health Agent`

### Bloco 3

- `Trend Analysis Agent`
- `Asset Selection Agent`

### Bloco 4

- `Learning / Optimization Agent`
- `Experiment Capability` formalizada

---

## 15. Conclusao

O Bloco 4 encerra a primeira versao completa da camada cognitiva adaptativa leve do CortAI.

Ele nao transforma o sistema em um modelo treinado autonomamente, mas cria a base para:

- ajuste estrategico por dados
- controle formal de variantes
- evolucao incremental do conteudo

Esse e o limite correto para a Fase 2, mantendo o sistema modular, auditavel e compativel com a infraestrutura da Fase 1.


---

## Source: `docs/runtime/phase2_block4_file_list_v1_0.md`

CortAI - Fase 2

Bloco 4 - File List

Documento: docs/runtime/phase2_block4_file_list_v1_0.md
Versao: 1.0
Status: Escopo congelado

---

## 1. Objetivo

Este documento define exatamente quais arquivos podem nascer no Bloco 4 da Fase 2.

O objetivo e evitar deriva entre:

- especificacao
- implementacao
- arquitetura existente

Somente os arquivos listados aqui podem ser criados.

---

## 2. Diretorios Permitidos

Somente os seguintes diretorios podem receber novos arquivos:

- `backend/app/creative/agents/learning/`
- `backend/app/creative/experiments/`
- `backend/data/learning/`
- `backend/data/experiments/`
- `tests/`

Nenhum outro diretorio pode ser criado ou modificado fora das integracoes minimas permitidas.

---

## 3. Arquivos a Criar

### 3.1 Learning / Optimization Agent

Diretorio:

- `backend/app/creative/agents/learning/`

Arquivos obrigatorios:

- `backend/app/creative/agents/learning/__init__.py`
- `backend/app/creative/agents/learning/models.py`
- `backend/app/creative/agents/learning/service.py`

Responsabilidade

O agente deve:

- ler dados de performance existentes
- gerar `learning_insights`
- fornecer recomendacoes estruturadas

---

### 3.2 Experiment Capability

Diretorio:

- `backend/app/creative/experiments/`

Arquivos obrigatorios:

- `backend/app/creative/experiments/__init__.py`
- `backend/app/creative/experiments/models.py`
- `backend/app/creative/experiments/service.py`

Responsabilidade

A capability deve:

- gerar `experiment_plan`
- estruturar variantes experimentais
- integrar com o fluxo cognitivo existente

---

## 4. Persistencia Permitida

Diretorios:

- `backend/data/learning/`
- `backend/data/experiments/`

Esses diretorios podem conter:

- `*.json`
- `*.jsonl`

Exemplos:

- `backend/data/learning/learning_insights.json`
- `backend/data/experiments/experiment_plan.json`

Nenhum banco novo deve ser introduzido neste bloco.

---

## 5. Testes Obrigatorios

Os seguintes testes devem ser criados:

- `tests/agents/learning/test_learning_agent_phase2_unittest.py`
- `tests/experiment/test_experiment_capability_phase2_unittest.py`
- `tests/runtime/pipeline/test_phase2_block4_smoke_unittest.py`

---

## 6. Integracao Permitida

Alteracoes minimas sao permitidas apenas em:

- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/models.py`
- `backend/app/creative/contracts/creative_pack.py`

Essas alteracoes devem servir exclusivamente para:

- incluir `learning_insights`
- incluir `experiment_plan`

no `creative_pack`.

---

## 7. Integracoes Proibidas

Nao podem ser criados ou modificados:

- runtime
- scheduler
- safety layer
- publish_record
- metrics collector
- analysis layer
- simulation
- consistency
- pipeline da Fase 1

Tambem e proibido implementar:

- RAG
- scraping
- treinamento de modelo
- fine-tuning
- LoRA
- RL
- experiment agent autonomo complexo

---

## 8. Fallback Obrigatorio

### Learning Agent

Se nao houver dados suficientes:

- `learning_insights = DEFAULT`

O fluxo nunca deve falhar por ausencia de historico.

---

### Experiment Capability

Se nenhum experimento estiver configurado:

- `experiment_plan = DEFAULT`

O fluxo deve continuar normalmente.

---

## 9. Criterio de Conclusao do Bloco 4

O Bloco 4 sera considerado concluido quando:

- `Learning Agent` funcionar
- `Experiment Capability` funcionar
- `Creative Orchestrator` consumir ambos
- `creative_pack` incluir:
  - `learning_insights`
  - `experiment_plan`
- pipeline continuar funcionando
- testes passarem
- smoke passar
- nenhuma regressao da Fase 1
- nenhuma regressao dos Blocos 1, 2 ou 3

---

## 10. Arquivos que NAO devem nascer neste bloco

Explicitamente proibido criar:

- `learning_rag_service.py`
- `experiment_agent_full.py`
- `model_training_service.py`
- `data_scraper_service.py`
- `adaptive_optimizer.py`

Essas capacidades pertencem a fases futuras.

---

## 11. Ordem Esperada de Implementacao

1. `Learning Agent`
2. `Experiment Capability`
3. integracao minima com `Orchestrator`
4. atualizacao minima do `creative_pack`
5. testes unitarios
6. smoke do Bloco 4
7. regressoes dos blocos anteriores

---

## 12. Conclusao

Este documento congela o escopo tecnico do Bloco 4, garantindo que:

- a implementacao permaneca pequena
- o sistema continue auditavel
- a arquitetura da Fase 1 permaneca intacta
- a Fase 2 evolua incrementalmente

---

## Proximo passo natural

Apos criar este arquivo:

1. gerar o prompt de implementacao do Bloco 4
2. executar a implementacao controlada
3. rodar testes e smoke
4. checkpoint formal do Bloco 4


---

## Source: `docs/runtime/phase2_completion_report_v1_0.md`

CortAI - Relatorio de Conclusao da Fase 2

Creative Intelligence Layer

Versao: 1.0
Status: Fase concluida
Documento: `docs/runtime/phase2_completion_report_v1_0.md`

---

## 1. Objetivo do Documento

Este relatorio formaliza o encerramento da Fase 2 do CortAI.

A Fase 2 teve como objetivo introduzir a camada cognitiva do sistema, adicionando capacidades de decisao criativa, contexto estrategico, contexto visual e adaptacao leve orientada por dados, sem regredir a baseline operacional validada na Fase 1.

Este documento consolida:

- o objetivo da Fase 2
- os blocos implementados
- os componentes entregues
- as integracoes validadas
- os checkpoints formais gerados
- o estado final da baseline cognitiva

---

## 2. Objetivo da Fase 2

A Fase 2 teve como objetivo evoluir o CortAI de um pipeline operacional automatizado para uma camada cognitiva modular capaz de:

- decidir com base em contexto de conta
- incorporar contexto de tendencias
- incorporar contexto visual
- controlar qualidade antes da publicacao
- produzir recomendacoes baseadas em dados historicos
- formalizar variacoes experimentais

A Fase 2 nao teve como objetivo:

- treinar modelos
- introduzir RAG completo
- introduzir scraping automatizado agressivo
- substituir a infraestrutura da Fase 1

A meta foi construir uma camada cognitiva leve, auditavel e incremental, compatível com a baseline operacional ja validada.

---

## 3. Relacao entre Fase 1 e Fase 2

### Fase 1

A Fase 1 consolidou a camada operacional do CortAI, incluindo:

- runtime distribuido
- scheduler
- safety layer
- content pipeline
- publish manifest
- publish_record canonico
- metrics collector
- analysis
- simulation
- consistency checker

### Fase 2

A Fase 2 adicionou a camada cognitiva acima dessa base, sem alterar a estrutura central da Fase 1.

A separacao entre as fases foi preservada:

- Fase 1 executa e persiste
- Fase 2 decide, contextualiza e orienta

---

## 4. Blocos Implementados na Fase 2

A implementacao da Fase 2 foi dividida em quatro blocos controlados, cada um com documentos congelados, testes, smoke, regressao e checkpoint formal.

### Bloco 1 - Creative Core

Componentes entregues:

- `Creative Orchestrator Service`
- `Script Agent`
- `Voice Agent`
- `Video QC Agent`

Objetivo validado:

- montar `creative_pack` minimo
- gerar roteiro
- resolver configuracao de voz
- executar o pipeline existente da Fase 1
- avaliar o resultado com `Video QC`

Checkpoint formal:

- `cortai-phase2-block1`

### Bloco 2 - Account Decision Layer

Componentes entregues:

- `Strategy Agent`
- `Account Health Agent`

Objetivo validado:

- avaliar saude da conta
- gerar `strategy_profile`
- permitir caminho `SAFE`
- permitir interrupcao controlada em `HOLD` antes do pipeline

Checkpoint formal:

- `cortai-phase2-block2`

### Bloco 3 - Trend and Visual Context

Componentes entregues:

- `Trend Analysis Agent` (manual-curated MVP)
- `Asset Selection Agent`

Objetivo validado:

- carregar `trend_profile` local e estruturado por nicho
- gerar `asset_selection` coerente e auditavel
- incluir contexto de tendencia e contexto visual no `creative_pack`

Checkpoint formal:

- `cortai-phase2-block3`

### Bloco 4 - Learning and Experiment Control

Componentes entregues:

- `Learning / Optimization Agent`
- `Experiment Capability` formalizada

Objetivo validado:

- ler dados ja existentes do sistema
- gerar `learning_insights`
- formalizar `experiment_plan`
- incluir ambos no `creative_pack`
- permitir adaptacao leve e variacao experimental canonica

Checkpoint formal:

- `cortai-phase2-block4`

---

## 5. Componentes Cognitivos Entregues

Ao final da Fase 2, a camada cognitiva do CortAI passou a incluir:

- `Creative Orchestrator Service`
- `Script Agent`
- `Voice Agent`
- `Video QC Agent`
- `Strategy Agent`
- `Account Health Agent`
- `Trend Analysis Agent`
- `Asset Selection Agent`
- `Learning / Optimization Agent`
- `Experiment Capability`

Esses componentes formam a primeira versao completa da `Creative Intelligence Layer`.

---

## 6. Fluxo Cognitivo Final da Fase 2

Ao final da Fase 2, o fluxo cognitivo validado passou a ser:

```text
Account Health Agent
-> Trend Analysis Agent
-> Learning / Optimization Agent
-> Strategy Agent
-> Experiment Capability
-> Asset Selection Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline (Fase 1)
-> Video QC Agent
```

Esse fluxo foi validado com smoke e regressao, mantendo a Fase 1 intacta.

---

## 7. Contratos Cognitivos Consolidados

Durante a Fase 2, o `creative_pack` evoluiu para carregar o contexto cognitivo necessario ao fluxo completo.

Ao final da fase, ele passou a incluir:

- `strategy_profile`
- `trend_profile`
- `asset_selection` / `asset_plan`
- `learning_insights`
- `experiment_plan`
- `script_plan`
- `voice_plan`
- `account_health_status`

Isso consolidou o `creative_pack` como contrato canonico entre a camada cognitiva e o pipeline da Fase 1.

---

## 8. Validacoes Executadas

Cada bloco da Fase 2 foi validado com o mesmo padrao disciplinado:

- testes unitarios do proprio bloco
- smoke do fluxo integrado daquele bloco
- regressao dos blocos anteriores
- regressao relevante da Fase 1
- checkpoint formal com commit e tag

No encerramento da fase, foi validado que:

- Bloco 1 permaneceu funcional
- Bloco 2 permaneceu funcional
- Bloco 3 permaneceu funcional
- Bloco 4 permaneceu funcional
- nenhuma regressao evidente da Fase 1 foi detectada

---

## 9. O que a Fase 2 Provou

A Fase 2 provou que o CortAI ja nao opera apenas como um pipeline tecnico de geracao automatizada.

O sistema agora consegue:

- avaliar saude da conta
- gerar estrategia por conta
- aplicar contexto de tendencia por nicho
- aplicar contexto visual coerente
- gerar roteiro contextualizado
- resolver configuracao de voz
- controlar qualidade de video antes do publish
- gerar recomendacoes leves baseadas em dados existentes
- formalizar variacoes experimentais canonicamente

Em termos arquiteturais, isso significa que o CortAI passou a ter uma camada cognitiva modular, auditavel e incremental em cima da Fase 1.

---

## 10. Limitacoes Conhecidas da Fase 2

Embora concluida no escopo congelado, a Fase 2 ainda possui limites intencionais.

Nao fazem parte da Fase 2:

- RAG completo
- scraping automatizado pesado
- treinamento de modelos
- fine-tuning
- LoRA
- RL
- aprendizado de pesos
- agent framework generico
- experimentacao pesada autonomica

Essas restricoes foram mantidas deliberadamente para preservar controle arquitetural e evitar deriva prematura.

---

## 11. Estado Final da Baseline Cognitiva

Ao final da Fase 2, o projeto possui checkpoints formais claros:

- `cortai-phase2-block1`
- `cortai-phase2-block2`
- `cortai-phase2-block3`
- `cortai-phase2-block4`

Isso torna a camada cognitiva:

- auditavel
- reversivel
- versionada
- incremental

---

## 12. Veredito Final da Fase 2

**FASE 2: CONCLUIDA**

Todos os blocos previstos no escopo congelado foram implementados, validados e checkpointados formalmente.

Nao foram detectadas regressões relevantes:

- da Fase 1
- do Bloco 1
- do Bloco 2
- do Bloco 3

A Fase 2 pode, portanto, ser considerada encerrada com sucesso no escopo tecnico definido.

---

## 13. Conclusao

A Fase 2 marcou a transicao do CortAI de um sistema operacional automatizado para um sistema com camada cognitiva explicita e modular.

Sem abandonar a disciplina da Fase 1, o projeto passou a operar com:

- decisao por conta
- contexto de tendencia
- contexto visual
- contexto de aprendizado leve
- controle experimental formalizado

A Fase 2 esta, portanto, formalmente concluida.


---

## Source: `docs/runtime/phase2_definition_report_v1_0.md`

CortAI - Relatorio de Definicao da Fase 2

Creative Intelligence Layer

Versao: 1.1
Status: Aprovado para Implementacao
Documento: `docs/runtime/phase2_definition_report_v1_0.md`

---

## 1. Objetivo do Documento

Este relatorio define a arquitetura, os componentes, os contratos, os criterios de conclusao e as regras de integracao da Fase 2 do CortAI.

A Fase 2 introduz a camada cognitiva do sistema, responsavel por decisoes criativas, estrategicas e adaptativas na geracao de conteudo.

O documento consolida as revisoes tecnicas realizadas e estabelece um escopo congelado para implementacao, garantindo alinhamento com a arquitetura, o runtime e o pipeline operacional da Fase 1.

---

## 2. Contexto: Transicao entre Fases

### 2.1 Fase 1 - Infraestrutura Operacional

A Fase 1 foi dedicada a construcao da infraestrutura operacional do CortAI, incluindo:

- runtime distribuido
- scheduler
- planner
- safety layer
- content pipeline
- geracao de video automatizada
- publish manifest
- publish records
- metrics collector
- camada de analise
- sistema de auditoria e consistencia

O objetivo da Fase 1 foi provar que o sistema e capaz de gerar videos de forma automatizada, consistente e auditavel.

Essa fase foi concluida com sucesso, incluindo execucao de batch de validacao com geracao de multiplos videos e verificacao completa do pipeline.

### 2.2 Fase 2 - Camada Cognitiva

A Fase 2 introduz a Creative Intelligence Layer, responsavel por:

- aplicar contexto estrategico
- entender tendencias
- adaptar conteudo por conta
- avaliar qualidade antes da publicacao
- aprender com metricas
- melhorar decisoes criativas ao longo do tempo

Em termos conceituais:

| Fase | Papel |
| --- | --- |
| Fase 1 | Provar que o sistema funciona |
| Fase 2 | Provar que o sistema pensa e aprende |

---

## 3. Principios Arquiteturais da Fase 2

A Fase 2 segue os seguintes principios:

### Separacao de responsabilidades

A camada cognitiva nao substitui o runtime nem o pipeline da Fase 1.

Ela prepara decisoes criativas e estrategicas, enquanto a infraestrutura existente executa a producao.

### Orquestracao centralizada

Os agentes nao se chamam diretamente.
A coordenacao e feita por um servico especifico:

`Creative Orchestrator Service`

### Contexto persistente

Todos os agentes utilizam contexto armazenado e auditavel, incluindo:

- tendencias
- estrategias de conta
- resultados de experimentos
- historico de decisoes

### Aprendizado incremental

O sistema evolui a partir de metricas reais.

A Fase 2 introduz mecanismos de aprendizado baseado em dados, mas nao depende de modelos treinados internamente.

### Compatibilidade com a Fase 1

Nenhum componente da Fase 2 pode violar contratos da Fase 1.

Em especial:

- nao alterar contratos de runtime
- nao alterar contratos de safety
- nao alterar contratos canonicos de `publish_record`
- nao alterar contratos canonicos de `metrics`
- nao permitir que agentes contornem o `Creative Orchestrator`

---

## 4. Creative Orchestrator Service

### 4.1 Papel

O Creative Orchestrator Service e o componente responsavel por coordenar a execucao dos agentes da camada cognitiva.

Ele atua como ponte entre:

- camada cognitiva
- pipeline operacional da Fase 1

### 4.2 Responsabilidades

O servico e responsavel por:

- carregar contexto estrategico
- consultar perfis de tendencia
- executar agentes criativos
- consolidar decisoes
- montar o `creative_pack`
- entregar o `creative_pack` ao pipeline de renderizacao

### 4.3 Integracao com o pipeline existente

Apos a geracao do `creative_pack`, o fluxo segue normalmente:

```text
Creative Orchestrator
-> Content Pipeline (Fase 1)
-> Video Renderer
-> Video QC Agent
-> Safety Layer
-> Runtime Publish
```

### 4.4 Entrada canonica do Orchestrator

O `Creative Orchestrator Service` deve receber uma entrada canonica contendo, no minimo:

- `account_id`
- `niche`
- `topic`
- `publish_slot`
- `creative_pack_id` quando ja existir
- `experiment_assignment` quando aplicavel
- `account_context_ref`
- `trend_context_ref`

### 4.5 Saida canonica do Orchestrator

A saida do `Creative Orchestrator Service` deve ser um `creative_pack` imutavel para a execucao corrente, contendo:

- `creative_pack_id`
- `account_id`
- `niche`
- `topic`
- `strategy_profile`
- `trend_profile`
- `script_plan`
- `voice_plan`
- `asset_plan`
- `experiment_assignment`
- `generated_at`
- `orchestrator_version`

O `creative_pack` e o contrato de integracao entre a Fase 2 e o pipeline da Fase 1.

### 4.6 Regras de falha do Orchestrator

Se um agente falhar, o `Creative Orchestrator` deve:

- aplicar fallback, quando definido
- registrar decisao e motivo
- falhar de forma explicita se o fallback nao existir

O `Creative Orchestrator` nao pode:

- produzir `creative_pack` parcial silenciosamente
- esconder falhas de agente
- pular agentes obrigatorios sem registrar motivo

---

## 5. Contrato do Creative Pack

### 5.1 Objetivo

O `creative_pack` e a unidade canonica de decisao criativa da Fase 2.

### 5.2 Estrutura minima

```json
{
  "creative_pack_id": "cp_xxx",
  "account_id": "acc_xxx",
  "niche": "dark_history",
  "topic": "abandoned station mystery",
  "strategy_profile": {
    "pacing": "fast",
    "hook_intensity": "high",
    "target_duration_s": 10
  },
  "trend_profile": {
    "dominant_hooks": ["question hook"],
    "visual_style": "dark cinematic backgrounds"
  },
  "script_plan": {
    "hook": "THE LAST TRAIN NEVER STOPPED HERE",
    "setup": "SO WHY DID THE SPEAKERS ANNOUNCE IT?",
    "payoff": "THE STATION CLOSED THIRTY YEARS AGO"
  },
  "voice_plan": {
    "provider": "premium_tts",
    "voice_id": "voice_x",
    "style": "calm_dark"
  },
  "asset_plan": {
    "hook_asset": "assets/backgrounds/horror/hook_01.jpg",
    "setup_asset": "assets/backgrounds/horror/setup_01.jpg",
    "payoff_asset": "assets/backgrounds/horror/payoff_01.jpg",
    "motion_profile": "subtle_push_in"
  },
  "experiment_assignment": {
    "experiment_id": "exp_hook_style_v1",
    "variant_id": "variant_b"
  },
  "generated_at": "2026-03-16T00:00:00Z",
  "orchestrator_version": "v1"
}
```

### 5.3 Regras

- o `creative_pack` deve ser deterministicamente reconstruivel a partir das entradas e refs persistidas
- o `creative_pack` nao pode ser reescrito pelo renderer
- o pipeline da Fase 1 consome o `creative_pack`, nao o reinterpreta estrategicamente

---

## 6. Agentes da Fase 2

A Fase 2 introduz um conjunto de agentes responsaveis por decisoes criativas e estrategicas.

### 6.1 Trend Analysis Agent

#### Objetivo

Identificar padroes relevantes de conteudo dentro de um nicho.

#### Implementacao inicial

O agente utilizara curadoria manual (MVP).

Fontes utilizadas:

- TikTok Creative Center
- observacao direta de conteudo bem-sucedido
- analise manual de tendencias

#### Saida

Arquivos estruturados por nicho:

`backend/data/trends/{niche}.json`

#### Fallback

Se nao houver contexto de tendencia para um nicho:

- usar perfil generico do nicho-pai
- registrar `trend_profile_fallback_used=true`
- nunca retornar vazio silenciosamente

### 6.2 Strategy Agent

#### Objetivo

Definir a estrategia de conteudo para cada conta.

#### Entradas

- perfil da conta
- historico de metricas
- objetivos da conta
- tendencias do nicho
- recomendacoes de aprendizado

#### Saida

`account_strategy_profile`

Exemplos de parametros:

- pacing recomendado
- estilo narrativo
- intensidade do hook
- duracao ideal
- variacao de conteudo

#### Fallback

Se a conta nao tiver historico suficiente:

- usar `default_strategy_profile` por nicho
- marcar a estrategia como `cold_start=true`

### 6.3 Script Agent

#### Objetivo

Gerar roteiros adaptados ao contexto.

#### Estrutura narrativa padrao

O agente gera roteiros seguindo a estrutura:

- Hook
- Setup
- Payoff

#### Entradas

- topico
- nicho
- estrategia da conta
- perfil de tendencias
- variacao experimental quando aplicavel

#### Papel

Substituir a geracao generica de roteiros por geracao orientada por retencao e contexto.

#### Regras

- cada bloco deve ser semanticamente fechado
- hook deve ser curto e de alto impacto
- setup deve sustentar a curiosidade
- payoff deve fechar a promessa narrativa

#### Fallback

Se a geracao contextual falhar:

- usar prompt simplificado orientado por nicho
- registrar `script_generation_fallback_used=true`
- falhar explicitamente se nem o fallback produzir `hook/setup/payoff`

### 6.4 Voice Agent

#### Objetivo

Selecionar voz e estilo de narracao.

#### Requisito da Fase 2

Suporte a TTS premium.

#### Estrategia

- Primary: TTS premium, ex.: ElevenLabs
- Fallback: Piper local

#### Parametros controlados

- voz
- velocidade
- intensidade emocional
- tom narrativo

#### Regras

- a escolha de voz deve ser persistida no `voice_plan`
- o fallback para Piper deve ser explicito e auditavel
- o agente nao pode trocar provider silenciosamente

### 6.5 Asset Selection Agent

#### Objetivo

Selecionar assets visuais adequados ao conteudo.

#### Entradas

- script
- nicho
- tendencias
- estrategia da conta

#### Saida

Selecao de:

- background do hook
- background do setup
- background do payoff
- estilo visual
- parametros de motion

#### Regras

- hook usa asset forte e legivel
- setup usa asset contextual
- payoff usa asset mais dramatico ou ameacador
- assets devem respeitar luminancia minima operacional

#### Fallback

Se nao houver assets especializados:

- usar biblioteca local por nicho
- reusar asset elegivel mais forte antes de usar asset inadequado

### 6.6 Video QC Agent

#### Objetivo

Avaliar a qualidade do video antes da publicacao.

#### Verificacoes

- integridade do arquivo
- presenca de audio
- resolucao correta
- duracao valida
- legibilidade das legendas
- coerencia narrativa
- presenca de hook forte
- ausencia de falhas visuais

#### Resultado

- `APPROVE`
- `REJECT`

Se rejeitado, o video nao segue para publicacao.

#### Regras objetivas minimas

O `Video QC Agent` deve rejeitar se houver qualquer um dos seguintes:

- arquivo de video ausente ou corrompido
- resolucao diferente de `1080x1920`
- audio ausente
- legenda fora da safe area
- overflow de legenda
- texto semantica ou visualmente quebrado
- duracao abaixo do minimo operacional definido
- payoff visual ilegivel

#### Integracao com Safety

- `Video QC Agent` rejeita por qualidade de producao
- `Safety Layer` bloqueia por risco e politica

Se `Video QC Agent` retornar `REJECT`:

- nao segue para `Safety Layer`
- nao gera publicacao
- nao gera `publish_record`
- deve emitir evento proprio de rejeicao

### 6.7 Account Health Agent

#### Objetivo

Monitorar sinais de risco relacionados a saude da conta.

#### Exemplos de sinais analisados

- queda brusca de visualizacoes
- repeticao excessiva de formato
- frequencia de postagem elevada
- videos consecutivos com desempenho anormal

#### Saida

- `SAFE`
- `CAUTION`
- `HOLD`

Esse agente atua como camada de protecao de distribuicao.

#### Regras

- `SAFE`: execucao normal
- `CAUTION`: execucao permitida com sinalizacao
- `HOLD`: impedir novos videos para a conta ate revisao ou ate janela liberada

### 6.8 Learning and Optimization Agent

#### Objetivo

Extrair aprendizado a partir das metricas geradas.

#### Entradas

- `publish_records`
- metricas de video
- resultados de experimentos
- relatorios de analise

#### Saida

Recomendacoes como:

- estilos de hook mais eficazes
- duracao ideal
- assets mais performaticos
- ajustes de estrategia

#### Regras

- a camada de aprendizado e read-only sobre historico bruto
- recomenda mudancas; nao reescreve eventos historicos

### 6.9 Experiment Capability

A experimentacao sera inicialmente uma capability integrada, nao um agente independente.

#### Implementacao inicial

Integrada aos agentes:

- Strategy Agent
- Script Agent

#### Funcao

Permitir geracao de variacoes como:

- multiplos hooks
- variacoes de estilo visual
- variacoes de narracao

#### Base tecnica

Utiliza o Experiment Framework (D31) ja existente.

#### Escopo congelado da capability

Na Fase 2, a experimentacao pode variar apenas:

- hook
- estrutura narrativa curta
- voz
- visual style leve

Nao pode variar nesta fase:

- contratos do runtime
- regras de safety
- formato canonico de `publish_record`
- formato canonico de `metrics`

---

## 7. Fluxo Cognitivo

Fluxo da camada cognitiva:

```text
Account Health Agent
-> Trend Analysis Agent
-> Strategy Agent
-> Experiment Capability
-> Script Agent
-> Asset Selection Agent
-> Voice Agent
-> Creative Orchestrator
-> Content Pipeline (Fase 1)
-> Video QC Agent
-> Safety Layer
-> Runtime Publish
-> Metrics Collector
-> Learning Agent
```

### 7.1 Ordem obrigatoria e opcional

Obrigatorios:

- Creative Orchestrator
- Script Agent
- Voice Agent
- Video QC Agent

Condicionais:

- Trend Analysis Agent
- Strategy Agent
- Account Health Agent
- Learning Agent
- Experiment Capability
- Asset Selection Agent

Se um agente condicional nao puder rodar, o fallback deve ser aplicado e auditado.

### 7.2 Regra de falha parcial

Se um agente obrigatorio falhar sem fallback:

- o fluxo deve falhar
- o motivo deve ser materializado
- nenhum publish deve seguir adiante

Se um agente condicional falhar com fallback valido:

- o fluxo pode seguir
- a decisao deve ser persistida

---

## 8. Armazenamento de Contexto

A Fase 2 introduz armazenamento estruturado de contexto.

### 8.1 Estrutura recomendada

`backend/data/context/`

Subpastas:

- `trends/`
- `strategy/`
- `learning/`
- `qc_history/`

### 8.2 Estrategia de persistencia

- PostgreSQL como fonte principal
- arquivos JSON/JSONL como backup auditavel

### 8.3 Fonte canonica por dominio

| Dominio | Fonte canonica | Backup auditavel |
| --- | --- | --- |
| trend profiles | PostgreSQL | JSON |
| strategy profiles | PostgreSQL | JSON |
| learning recommendations | PostgreSQL | JSONL |
| qc decisions | PostgreSQL | JSONL |
| experiment assignments | PostgreSQL | JSONL |
| orchestrator outputs | PostgreSQL | JSON |

### 8.4 Regra de escrita

- agentes escrevem apenas no dominio que controlam
- o `Creative Orchestrator` consolida refs, nao duplica historico bruto
- arquivos JSON/JSONL servem como evidencias e backup, nao como fonte primaria em producao

---

## 9. Eventos e Observabilidade da Fase 2

Devem existir eventos proprios da camada cognitiva, separados dos eventos da Fase 1.

Eventos minimos:

- `CREATIVE/orchestrator_started`
- `CREATIVE/orchestrator_completed`
- `CREATIVE/orchestrator_failed`
- `CREATIVE/script_generated`
- `CREATIVE/voice_selected`
- `CREATIVE/assets_selected`
- `CREATIVE/video_qc_approved`
- `CREATIVE/video_qc_rejected`
- `CREATIVE/account_health_safe`
- `CREATIVE/account_health_caution`
- `CREATIVE/account_health_hold`
- `CREATIVE/learning_recommendations_generated`

Regra:

- cada agente emite apenas eventos do seu dominio
- a camada cognitiva nao emite eventos `CONTENT/*` nem `SAFETY/*`

---

## 10. Roadmap de Implementacao

A implementacao sera dividida em quatro blocos.

### Bloco 1 - Qualidade minima inteligente

- Creative Orchestrator Service minimo
- Video QC Agent
- Script Agent
- Voice Agent

### Bloco 2 - Estrategia por conta

- Strategy Agent
- Account Health Agent

### Bloco 3 - Contexto e visual

- Asset Selection Agent
- Trend Analysis Agent manual-curated

### Bloco 4 - Aprendizado e experimentacao

- Learning Agent
- formalizacao da Experiment Capability

---

## 11. Criterios de Conclusao da Fase 2

A Fase 2 sera considerada concluida quando o sistema for capaz de:

1. gerar conteudo baseado em estrategia de conta
2. utilizar contexto de tendencias na geracao de roteiros
3. operar com TTS premium integrado
4. bloquear videos ruins via Video QC Agent
5. proteger contas via Account Health Agent
6. gerar recomendacoes baseadas em metricas reais
7. produzir conteudo variado e nao repetitivo
8. executar o fluxo cognitivo completo via Creative Orchestrator

---

## 12. Criterios Tecnicos de Aceite

A Fase 2 so pode ser considerada concluida se, alem dos criterios funcionais, tambem atender aos criterios tecnicos abaixo.

### 12.1 Testes minimos

Devem existir testes unitarios e de integracao para:

- Creative Orchestrator
- Script Agent
- Voice Agent
- Video QC Agent
- Strategy Agent
- Account Health Agent
- Asset Selection Agent
- Learning Agent
- experiment assignment

### 12.2 Smoke obrigatorio

Deve existir pelo menos um smoke completo cobrindo:

`Creative Orchestrator -> Content Pipeline -> Video QC -> Safety -> Runtime -> Metrics -> Learning`

### 12.3 Evidencias obrigatorias

Para declarar Fase 2 concluida, devem ser materializadas evidencias em diretorio dedicado contendo:

- relatorio de testes
- smoke report
- eventos da camada cognitiva
- amostras de `creative_pack`
- decisoes do `Video QC Agent`
- recomendacoes do `Learning Agent`

### 12.4 Regressao proibida

A implementacao da Fase 2 nao pode quebrar:

- baseline validada da Fase 1
- gate final pre-D23
- batch local validado

---

## 13. Limitacoes da Fase 2

Nao fazem parte desta fase:

- geracao completa de video por IA
- avatares
- animacoes complexas
- edicao cinematografica avancada
- automacao de analise massiva de redes sociais
- otimizacao financeira agressiva

Esses temas pertencem a fases futuras.

---

## 14. Conclusao

A Fase 2 estabelece a camada de inteligencia do CortAI.

Com sua implementacao, o sistema evolui de um pipeline automatizado de geracao de conteudo para um sistema cognitivo capaz de tomar decisoes criativas, adaptar estrategias e aprender com metricas reais.

Esta especificacao define um escopo realista, modular e compativel com a infraestrutura ja construida na Fase 1.

Com a presente revisao, o documento passa a incluir os elementos necessarios para implementacao segura:

- contratos explicitos
- regras de fallback
- persistencia canonica por dominio
- integracao clara com safety e runtime
- criterios objetivos de qualidade
- criterios tecnicos de aceite

---

## Status Final

Fase 2 - Especificacao Tecnica Congelada para Implementacao


---

## Source: `docs/runtime/phase2_implementation_map_v1_0.md`

CortAI - Mapa de Implementacao da Fase 2

Creative Intelligence Layer

Versao: 1.0
Status: Congelado para Implementacao
Documento: `docs/runtime/phase2_implementation_map_v1_0.md`

---

## 1. Objetivo

Este documento congela a forma como a Fase 2 deve existir no repositorio.

Ele define:

- mapa de diretorios
- lista de modulos
- contratos canonicos em codigo
- fronteiras entre Fase 2 e Fase 1

O objetivo e evitar:

- acoplamento ruim
- nomes inconsistentes
- storage duplicado
- contratos divergentes

---

## 2. Regra de Ouro

A Fase 2 nao substitui a Fase 1.

A Fase 2:

- decide
- recomenda
- seleciona
- consolida contexto

A Fase 1:

- executa
- renderiza
- persiste artefatos operacionais
- publica internamente no runtime
- coleta metricas

Em codigo:

- agentes da Fase 2 nao chamam uns aos outros diretamente
- agentes da Fase 2 nao escrevem `publish_record`
- agentes da Fase 2 nao escrevem `metrics`
- agentes da Fase 2 nao chamam `Safety Layer` diretamente
- toda coordenacao passa pelo `Creative Orchestrator Service`

---

## 3. Mapa de Diretorios

Estrutura recomendada:

```text
backend/app/creative/
  orchestrator/
    __init__.py
    models.py
    service.py
    events.py

  agents/
    __init__.py

    trend_analysis/
      __init__.py
      models.py
      service.py

    strategy/
      __init__.py
      models.py
      service.py

    script/
      __init__.py
      models.py
      service.py

    voice/
      __init__.py
      models.py
      service.py

    asset_selection/
      __init__.py
      models.py
      service.py

    video_qc/
      __init__.py
      models.py
      service.py

    account_health/
      __init__.py
      models.py
      service.py

    learning/
      __init__.py
      models.py
      service.py

  capabilities/
    __init__.py
    experiment/
      __init__.py
      models.py
      service.py

  context/
    __init__.py
    models.py
    repository.py
    file_store.py
    pg_store.py

  contracts/
    __init__.py
    creative_pack.py
    orchestrator_io.py
    agent_common.py

backend/data/context/
  trends/
  strategy/
  learning/
  qc_history/

tests/
  test_creative_orchestrator_phase2_unittest.py
  test_trend_analysis_agent_phase2_unittest.py
  test_strategy_agent_phase2_unittest.py
  test_script_agent_phase2_unittest.py
  test_voice_agent_phase2_unittest.py
  test_asset_selection_agent_phase2_unittest.py
  test_video_qc_agent_phase2_unittest.py
  test_account_health_agent_phase2_unittest.py
  test_learning_agent_phase2_unittest.py
  test_experiment_capability_phase2_unittest.py
  test_phase2_context_repository_unittest.py
  test_phase2_smoke_integration_unittest.py
```

---

## 4. Lista de Modulos por Dominio

### 4.1 `backend/app/creative/orchestrator/`

Arquivos:

- `models.py`
- `service.py`
- `events.py`

Responsabilidade:

- receber entrada canonica da Fase 2
- carregar contexto
- coordenar agentes
- aplicar fallback
- consolidar o `creative_pack`
- emitir eventos da camada cognitiva

### 4.2 `backend/app/creative/agents/trend_analysis/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- carregar e consolidar perfis de tendencia por nicho
- aplicar fallback para nicho-pai ou perfil generico

### 4.3 `backend/app/creative/agents/strategy/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- gerar `account_strategy_profile`
- tratar `cold_start`
- consolidar estrategia recomendada por conta

### 4.4 `backend/app/creative/agents/script/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- gerar `hook/setup/payoff`
- produzir `script_plan`
- respeitar contexto estrategico e experimental

### 4.5 `backend/app/creative/agents/voice/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- definir provider de voz
- selecionar voz, estilo e parametros narrativos
- materializar `voice_plan`

### 4.6 `backend/app/creative/agents/asset_selection/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- selecionar assets por papel narrativo
- validar elegibilidade visual
- materializar `asset_plan`

### 4.7 `backend/app/creative/agents/video_qc/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- validar qualidade do video antes de seguir para safety
- emitir `APPROVE` ou `REJECT`

### 4.8 `backend/app/creative/agents/account_health/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- avaliar risco por conta
- emitir `SAFE`, `CAUTION` ou `HOLD`

### 4.9 `backend/app/creative/agents/learning/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- consolidar recomendacoes baseadas em metricas reais
- produzir `learning_recommendations`

### 4.10 `backend/app/creative/capabilities/experiment/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- encapsular assignment experimental
- expor variacoes permitidas
- integrar com D31 sem alterar seu contrato base

### 4.11 `backend/app/creative/context/`

Arquivos:

- `models.py`
- `repository.py`
- `file_store.py`
- `pg_store.py`

Responsabilidade:

- definir persistencia canonica da camada cognitiva
- abstrair PostgreSQL e backup em JSON/JSONL

### 4.12 `backend/app/creative/contracts/`

Arquivos:

- `creative_pack.py`
- `orchestrator_io.py`
- `agent_common.py`

Responsabilidade:

- congelar nomes de contratos em codigo
- impedir deriva de schemas entre agentes

---

## 5. Contratos Congelados em Codigo

Os nomes abaixo ficam congelados para a implementacao da Fase 2.

### 5.1 Contratos do Orchestrator

Definir em:

- `backend/app/creative/contracts/orchestrator_io.py`

Modelos canonicos:

- `CreativeOrchestratorInput`
- `CreativeOrchestratorResult`
- `CreativeOrchestratorFailure`

Campos minimos de `CreativeOrchestratorInput`:

- `account_id: str`
- `niche: str`
- `topic: str`
- `publish_slot: str`
- `creative_pack_id: str | None`
- `experiment_assignment_id: str | None`
- `account_context_ref: str | None`
- `trend_context_ref: str | None`

Campos minimos de `CreativeOrchestratorResult`:

- `creative_pack: CreativePack`
- `fallbacks_used: list[str]`
- `events_emitted: list[str]`
- `qc_required: bool`

### 5.2 Contrato Canonico do Creative Pack

Definir em:

- `backend/app/creative/contracts/creative_pack.py`

Modelos canonicos:

- `CreativePack`
- `StrategyProfile`
- `TrendProfile`
- `ScriptPlan`
- `VoicePlan`
- `AssetPlan`
- `ExperimentAssignment`

Campos minimos de `CreativePack`:

- `creative_pack_id: str`
- `account_id: str`
- `niche: str`
- `topic: str`
- `strategy_profile: StrategyProfile`
- `trend_profile: TrendProfile`
- `script_plan: ScriptPlan`
- `voice_plan: VoicePlan`
- `asset_plan: AssetPlan`
- `experiment_assignment: ExperimentAssignment | None`
- `generated_at: str`
- `orchestrator_version: str`

### 5.3 Contratos Comuns de Agente

Definir em:

- `backend/app/creative/contracts/agent_common.py`

Modelos canonicos:

- `AgentDecision`
- `AgentFailure`
- `FallbackDecision`

Enums congelados:

- `DecisionStatus`
- `FallbackMode`
- `FailureSeverity`

Valores minimos de `DecisionStatus`:

- `APPROVE`
- `REJECT`
- `SAFE`
- `CAUTION`
- `HOLD`
- `ALLOW`
- `DELAY`
- `BLOCK`

Regra:

- agentes podem ter modelos especificos locais
- mas resultados externos devem derivar destes contratos base

---

## 6. Contratos Especificos por Agente

### 6.1 Trend Analysis Agent

Definir em:

- `backend/app/creative/agents/trend_analysis/models.py`

Modelos:

- `TrendAnalysisInput`
- `TrendAnalysisProfile`
- `TrendAnalysisResult`

### 6.2 Strategy Agent

Definir em:

- `backend/app/creative/agents/strategy/models.py`

Modelos:

- `StrategyAgentInput`
- `AccountStrategyProfile`
- `StrategyAgentResult`

### 6.3 Script Agent

Definir em:

- `backend/app/creative/agents/script/models.py`

Modelos:

- `ScriptAgentInput`
- `ScriptPlan`
- `ScriptAgentResult`

Regra:

- `ScriptPlan` deste modulo deve ser alias ou reexport do contrato canonico em `creative_pack.py`

### 6.4 Voice Agent

Definir em:

- `backend/app/creative/agents/voice/models.py`

Modelos:

- `VoiceAgentInput`
- `VoicePlan`
- `VoiceAgentResult`

### 6.5 Asset Selection Agent

Definir em:

- `backend/app/creative/agents/asset_selection/models.py`

Modelos:

- `AssetSelectionInput`
- `AssetPlan`
- `AssetSelectionResult`

### 6.6 Video QC Agent

Definir em:

- `backend/app/creative/agents/video_qc/models.py`

Modelos:

- `VideoQcInput`
- `VideoQcDecision`
- `VideoQcResult`

Campos minimos:

- `status: Literal["APPROVE", "REJECT"]`
- `reasons: list[str]`
- `checked_at: str`

### 6.7 Account Health Agent

Definir em:

- `backend/app/creative/agents/account_health/models.py`

Modelos:

- `AccountHealthInput`
- `AccountHealthDecision`
- `AccountHealthResult`

Campos minimos:

- `status: Literal["SAFE", "CAUTION", "HOLD"]`
- `signals: list[str]`
- `checked_at: str`

### 6.8 Learning Agent

Definir em:

- `backend/app/creative/agents/learning/models.py`

Modelos:

- `LearningAgentInput`
- `LearningRecommendation`
- `LearningAgentResult`

### 6.9 Experiment Capability

Definir em:

- `backend/app/creative/capabilities/experiment/models.py`

Modelos:

- `ExperimentCapabilityInput`
- `ExperimentAssignment`
- `ExperimentCapabilityResult`

Regra:

- `ExperimentAssignment` deste modulo deve ser alias ou reexport do contrato canonico em `creative_pack.py`

---

## 7. Persistencia Canonica

### 7.1 Repositorio unico da camada cognitiva

Toda persistencia da Fase 2 deve passar por:

- `backend/app/creative/context/repository.py`

Interface minima:

- `load_trend_profile(...)`
- `save_trend_profile(...)`
- `load_strategy_profile(...)`
- `save_strategy_profile(...)`
- `save_learning_recommendations(...)`
- `save_video_qc_decision(...)`
- `save_orchestrator_output(...)`
- `load_account_context(...)`

### 7.2 Implementacoes de store

Implementacoes:

- `pg_store.py`
- `file_store.py`

Regra:

- `pg_store.py` e a fonte principal
- `file_store.py` materializa backup auditavel
- agentes nao acessam `PostgreSQL` ou arquivos diretamente fora do repositorio

### 7.3 O que nao pode acontecer

- agent escrevendo JSON arbitrario fora de `backend/data/context/`
- agent escrevendo tabela propria sem passar pelo repositorio
- duplicacao do mesmo dominio em varios lugares

---

## 8. Regras de Integracao com a Fase 1

### 8.1 Ponto unico de entrada

A Fase 2 deve integrar com a Fase 1 por meio do `creative_pack` entregue ao pipeline.

### 8.2 O que a Fase 2 nao pode fazer

- escrever `publish_record`
- chamar `metrics collector`
- disparar `Safety Layer` diretamente
- reescrever artefatos do pipeline apos render
- alterar contratos de `ExecutionEnvelope` e `PipelineResult` por conta propria

### 8.3 Ordem operacional congelada

Fluxo permitido:

```text
Creative Orchestrator
-> Content Pipeline
-> Video QC Agent
-> Safety Layer
-> Runtime Publish
-> Metrics Collector
-> Learning Agent
```

### 8.4 Regra de rejeicao do Video QC

Se `Video QC Agent` retornar `REJECT`:

- o fluxo para
- nao chama `Safety Layer`
- nao gera `publish_record`
- nao segue para runtime publish

---

## 9. Eventos Congelados da Camada Cognitiva

Os nomes abaixo ficam congelados para implementacao.

Definir emissores em:

- `backend/app/creative/orchestrator/events.py`

Eventos minimos:

- `CREATIVE/orchestrator_started`
- `CREATIVE/orchestrator_completed`
- `CREATIVE/orchestrator_failed`
- `CREATIVE/trend_profile_loaded`
- `CREATIVE/strategy_profile_generated`
- `CREATIVE/script_generated`
- `CREATIVE/voice_selected`
- `CREATIVE/assets_selected`
- `CREATIVE/video_qc_approved`
- `CREATIVE/video_qc_rejected`
- `CREATIVE/account_health_safe`
- `CREATIVE/account_health_caution`
- `CREATIVE/account_health_hold`
- `CREATIVE/learning_recommendations_generated`

Regra:

- nao criar eventos `CONTENT/*` na Fase 2
- nao criar eventos `SAFETY/*` na Fase 2

---

## 10. Ordem de Implementacao Recomendada

### Bloco 1

- `creative/contracts/*`
- `creative/orchestrator/*`
- `creative/context/*`

### Bloco 2

- `agents/script/*`
- `agents/voice/*`
- `agents/video_qc/*`

### Bloco 3

- `agents/strategy/*`
- `agents/account_health/*`

### Bloco 4

- `agents/trend_analysis/*`
- `agents/asset_selection/*`

### Bloco 5

- `capabilities/experiment/*`
- `agents/learning/*`
- smoke de integracao da Fase 2

---

## 11. Suite de Testes Obrigatoria

Arquivos obrigatorios:

- `tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py`
- `tests/agents/trend_analysis/test_trend_analysis_agent_phase2_unittest.py`
- `tests/agents/strategy/test_strategy_agent_phase2_unittest.py`
- `tests/agents/script/test_script_agent_phase2_unittest.py`
- `tests/agents/voice/test_voice_agent_phase2_unittest.py`
- `tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py`
- `tests/agents/video_qc/test_video_qc_agent_phase2_unittest.py`
- `tests/agents/account_health/test_account_health_agent_phase2_unittest.py`
- `tests/agents/learning/test_learning_agent_phase2_unittest.py`
- `tests/experiment/test_experiment_capability_phase2_unittest.py`
- `tests/test_phase2_context_repository_unittest.py`
- `tests/test_phase2_smoke_integration_unittest.py`

Regra:

- nenhum modulo da Fase 2 entra sem teste correspondente

---

## 12. Criterio de Congelamento

O mapa da Fase 2 sera considerado congelado se:

- os diretorios acima forem mantidos
- os nomes dos contratos acima forem respeitados
- a persistencia passar pelo repositorio unico
- a Fase 2 nao invadir contratos da Fase 1

Mudancas nesses pontos depois do inicio da implementacao devem ser tratadas como alteracoes arquiteturais, nao como detalhe de codigo.

---

## 13. Conclusao

A especificacao da Fase 2 ja esta madura no nivel conceitual.

Este documento fecha o nivel que faltava para implementacao segura:

- onde cada coisa vive
- quais modulos existem
- quais contratos sao canonicos
- como a Fase 2 integra com a Fase 1

Com isso, a proxima etapa deixa de ser definicao e passa a ser execucao controlada.


---

## Source: `docs/runtime/PIPELINE_FULL_SYSTEM_MASTER_CERTIFICATION_CHECKLIST_v1_0.md`

# PIPELINE_FULL_SYSTEM_MASTER_CERTIFICATION_CHECKLIST_v1_0

## 1. Objective

Prove that the full CortAI multi-agent pipeline is operationally sound, stable, coherent, and governed exactly as approved.

This checklist must validate:
- unit behavior of each subsystem
- integrated behavior across subsystems
- orchestrator correctness
- end-to-end real execution
- semantic consistency of `CreativePack`
- governance and enforcement
- determinism where required
- safe degradation
- absence of material regressions
- absence of silent failures
- absence of boundary violations
- readiness for continued architecture work without reopening the frozen core

## 2. Rule Of The Gate

No new structural work should proceed unless this gate closes with an acceptable verdict.

Allowed verdicts:
- `GO`
- `GO_WITH_MONITORING`

Blocking verdict:
- `HOLD`

## 3. Covered Scope

This gate covers:
- `Account Health Agent v2`
- `Trend Analysis Agent v2`
- `Learning / Optimization Agent v2`
- `Novelty / Saturation Engine v1`
- `Strategy Agent v2`
- `Experiment Capability v2`
- `Script Agent`
- `Voice Agent`
- `Asset Agent`
- `Editor Agent`
- `QC Agent`
- `Creative Orchestrator`
- `Content pipeline / render`
- artifacts / events / audit surfaces
- governance registry / frozen baseline policy

## 4. Final Success Question

At the end, the system must answer:

```json
{
  "pipeline_integrity": true,
  "all_agents_operational": true,
  "all_agents_causally_relevant_or_explicitly_bounded": true,
  "cross_agent_orchestration_valid": true,
  "contracts_and_serialization_valid": true,
  "governance_and_enforcement_valid": true,
  "fallbacks_honest_and_safe": true,
  "determinism_valid_where_required": true,
  "real_execution_valid": true,
  "quality_stable": true,
  "silent_failures_detected": false,
  "boundary_violations_detected": false,
  "promotion_blockers": []
}
```

## 5. Block A - Repository And Structural Sanity

Objective:
- guarantee that the structural base of the system remains intact

Required checks:
- main orchestrator exists
- main contracts exist
- agent services exist
- critical runners exist
- canonical data paths exist
- canonical audit paths exist
- governance registry exists
- baseline promotion artifacts exist
- canonical governed subsystem config files exist

Blocking failures:
- missing critical service
- missing critical contract
- missing registry
- broken canonical path
- missing critical runner

## 6. Block B - Contract Integrity And Serialization

Objective:
- guarantee that all producer/consumer contracts remain intact

Required checks:
- `AccountHealthResult` serializes
- `TrendAnalysisResult` serializes
- `LearningAgentResult` serializes
- `NoveltyPressureProfile` serializes
- `StrategyResult` serializes
- `ExperimentCapabilityResult` serializes
- `ScriptPlan` serializes
- `VoicePlan` serializes
- `AssetSelectionResult` / `AssetPlan` serialize
- `EditPlan` serializes
- `VideoQcResult` / `VideoQcDecision` serialize
- `CreativePack` serializes completely
- `CreativePipelineExecution.to_dict()` preserves all critical blocks
- final `execution_outputs.json` remains structurally intact

Blocking failures:
- missing mandatory field
- non-serializable structure
- producer/consumer incompatibility
- critical block disappearing from final output

## 7. Block C - Unit Validation Of Each Agent

Objective:
- prove that each agent still works correctly in isolation

### C1. Account Health Agent
- `SAFE` valid
- `CAUTION` valid
- `HOLD` valid
- fallback explicit
- real input activation present
- coherent `decision_trace`
- coherent constraints
- determinism validated

### C2. Trend Analysis Agent
- manual curation governed path valid
- creative center path valid
- source assembly valid
- provenance present
- confidence coherent
- freshness coherent
- validation summary coherent
- fallback hierarchy valid
- temporal snapshot valid
- shift detection valid
- determinism under controlled input valid

### C3. Learning Agent
- QC ingestion valid
- history ingestion valid
- contamination handling valid
- policy formation valid
- pattern findings valid
- downstream Strategy reaction valid
- determinism valid

### C4. Novelty Engine
- memory window valid
- signature extraction valid
- pressure escalation valid
- blocked payoff structures valid
- blocked visual payoff categories valid
- Strategy reaction valid
- Script enforcement valid
- Asset enforcement valid

### C5. Strategy Agent
- reacts to Health
- reacts to Trend
- reacts to Learning
- reacts to Novelty
- preserves contract
- coherent `decision_trace`
- determinism valid

### C6. Experiment Capability Agent
- explicit eligibility
- real assignment
- real result recording
- explicit fallback
- explicit `decision_trace`
- explicit `experiment_trace`
- traceable A/B difference
- determinism valid

### C7. Script Agent
- valid hook
- valid setup
- valid payoff
- valid structured generation
- functional fallback
- real strategic context consumption
- real experiment plan consumption
- real trend/learning consumption where intended

### C8. Voice Agent
- valid provider
- valid style
- valid `delivery_profile`
- valid segments
- valid runtime constraints
- explicit provider fallback
- coherence with Script and Strategy

### C9. Asset Agent
- valid assets per segment
- real Trend reaction
- real Strategy reaction
- real Novelty reaction
- safe fallback
- no uncontrolled excessive repetition

### C10. Editor Agent
- valid `EditPlan`
- valid `caption_plan`
- valid `timing_plan`
- valid `motion_plan`
- valid `color_plan`
- valid `transition_plan`
- coherence with Voice / Asset / Script

### C11. QC Agent
- valid `score_summary`
- valid `product_signals`
- valid `APPROVE` / `HOLD` / `REJECT`
- governed publishability
- final decision coherent with signals
- no rules bypass

Blocking failures:
- any critical agent fails in isolation
- any fallback is invisible
- any decision is incoherent with its own contract

## 8. Block D - Downstream Causality Validation

Objective:
- prove that agents are not decorative

Required checks:
- Health alters Strategy
- Health blocks orchestration on `HOLD`
- Trend alters Strategy
- Trend alters Asset
- Trend influences Script
- Learning alters Strategy
- Novelty alters Strategy
- Novelty alters Script
- Novelty alters Asset
- Strategy alters Script
- Strategy alters Voice
- Strategy alters Asset
- Experiment alters Script in a traceable way
- Script alters Voice
- Script + Strategy + Trend alter Asset
- Asset + Voice + Script alter Editor
- Editor alters QC evaluation surface
- QC alters final publishability

Blocking failures:
- present but inert agent
- textual or cosmetic-only causality
- expected effect not observable in artifacts

## 9. Block E - Cross-Agent Orchestration

Objective:
- guarantee that agents work together, not only alone

Required checks:
- orchestrator order is correct
- no critical agent is skipped
- no critical output arrives as `None` without explicit fallback
- `CreativePack` contains all critical blocks
- traces between agents do not contradict each other
- upstream context reaches downstream correctly
- no severe semantic divergence between Strategy / Script / Voice / Asset / Editor
- one-agent fallback does not break the others

Blocking failures:
- incorrect order
- skipped agent
- inconsistent pack
- pipeline breaks before render or QC

## 10. Block F - Governance And Authority Integrity

Objective:
- guarantee that authorities remain in the correct places

Required checks:
- Account Health remains above Strategy
- Trend does not invade Learning
- Learning does not invade Strategy
- Novelty does not invade Trend
- Experiment does not invade Strategy / Learning
- Strategy remains control layer
- QC remains final publishability authority
- publish manifest is not created before QC
- `HOLD` and `REJECT` block correctly
- `change_policy` from system registry is respected
- frozen baseline was not violated without formal reopen

Blocking failures:
- boundary violation
- QC bypass
- Health bypass
- unauthorized mutation in frozen subsystem

## 11. Block G - Fallback Honesty And Safe Degradation

Objective:
- guarantee safe degradation without silent corruption

Required checks:
- Health fallback explicit
- Trend fallback explicit
- Learning fallback explicit
- Experiment fallback explicit
- Voice fallback explicit
- Asset fallback explicit
- fallback does not create fake artifacts
- fallback does not contaminate Learning
- fallback does not contaminate Experiment
- fallback path appears in events and traces
- pipeline remains operational under controlled degradation

Blocking failures:
- invisible fallback
- fake fallback
- fallback contaminates clean data
- degraded path breaks the pipeline

## 12. Block H - Determinism And Replay

Objective:
- guarantee predictability and reproducibility where required

Required checks:
- same controlled input => same Health
- same controlled input => same Trend
- same controlled input => same `LearningPolicy`
- same controlled input => same `StrategyProfile`
- same subject/config => same experiment assignment
- same controlled input => same `AssetPlan`
- same controlled input => same QC decision
- controlled replay remains stable

Blocking failures:
- unexplained drift
- divergence under identical input
- nondeterminism in a layer that should be deterministic

## 13. Block I - Controlled Master Battery

Objective:
- exercise the system under strong and boundary conditions

Required minimum scenarios:
- baseline healthy
- Health `SAFE`
- Health `CAUTION`
- Health `HOLD`
- Trend strong valid
- Trend stale
- Trend fallback
- Learning winner cluster
- Learning loser cluster
- Learning contaminated cluster
- Novelty low
- Novelty medium
- Novelty high
- Experiment blocked by Health `HOLD`
- Experiment standard by novelty pressure
- Experiment conservative by instability
- Experiment fallback
- QC `APPROVE`
- QC `HOLD`
- QC `REJECT`
- Voice provider fallback
- Asset fallback path
- Editor under borderline asset
- Script fallback path

Required proof:
- each scenario produces the correct decision
- governance remains intact
- no unexpected collateral failure
- execution artifacts remain coherent

## 14. Block J - Real Batch Execution

Objective:
- prove that the system works outside the lab

Minimum proof:
- `3` to `5` new real executions or a canonical recent batch accepted methodologically
- valid `.mp4`
- valid audio
- valid subtitles
- valid metadata
- complete per-agent execution outputs
- no new systemic failure pattern

Required metrics:
- `ready_rate`
- `approve_rate`
- `average_overall_score`
- `valid_video_rate`
- `fallback_rate` per agent
- `new_failure_patterns`
- `publishable_rate`
- `experiment_assignment_rate`
- `experiment_result_recording_rate`

Blocking failures:
- invalid video
- real batch collapse
- new systemic failure pattern
- missing per-agent outputs

## 15. Block K - Product Quality Stability

Objective:
- guarantee that the system not only runs but delivers stable product quality

Required checks:
- `hook_quality` stable
- `payoff_quality` stable
- `product_quality` stable
- asset quality did not collapse
- edit quality did not collapse
- voice quality did not collapse
- Experiment does not collapse quality
- Novelty does not collapse `approve_rate`
- Learning does not destabilize Strategy
- Trend does not create undue operational noise
- Health does not overconstrain
- QC remains coherent with real product outcome

Blocking failures:
- material quality regression
- collapsed `approve_rate`
- inconsistency between observed quality and QC scoring

## 16. Block L - Observability And Auditability

Objective:
- guarantee full post-run reconstruction

Required checks:
- critical events exist
- event payloads are rich enough
- `decision_trace` exists where required
- `experiment_trace` exists where required
- fallback trace exists
- `execution_outputs` allow end-to-end reconstruction
- audit artifacts exist
- `event_summary.json` exists
- `human_review.json` exists
- `metrics.json` exists
- `block_summary.json` exists
- `final_verdict.json` exists

Blocking failures:
- missing critical events
- missing critical traces
- insufficient artifacts
- impossible post-run reconstruction

## 17. Block M - Performance, Bottlenecks, And Silent Failure Surface

Objective:
- detect bottlenecks or silent failures not yet declared

Required checks:
- no agent is silently failing and returning default always
- no default path dominates improperly without being made explicit
- anomalous latencies or bottlenecks are not hidden
- no recently promoted subsystem is operating as fake active
- no critical output is being ignored downstream
- no important artifact stopped being written
- no crucial event stopped being emitted

Blocking failures:
- undeclared default/fallback dominance
- relevant silent failure
- hidden material bottleneck
- active subsystem operating ornamentally

## 18. Block N - System Governance Registry Integrity

Objective:
- guarantee that the whole system formally recognizes its frozen/governed state

Required checks:
- `OUT/audit/system_governance_registry.json` exists
- core pipeline marked as `FROZEN_AND_VALIDATED`
- `account_health_v2` marked as `ACTIVE_WITH_MONITORING`
- `experiment_capability_v2` marked as `ACTIVE_WITH_MONITORING`
- `FROZEN_UNLESS_GOVERNANCE_REOPEN` is present
- `no_core_modification = true`
- `no_subsystem_mutation_without_reopen = true`
- `new_work_must_be_isolated_subsystems = true`

Blocking failures:
- missing registry
- registry inconsistent with canonical artifacts
- missing global policy

## 19. Block O - Required Artifacts

The runner for this gate must generate at minimum:
- `OUT/audit/pipeline_full_master_certification/final_verdict.json`
- `OUT/audit/pipeline_full_master_certification/block_summary.json`
- `OUT/audit/pipeline_full_master_certification/agent_matrix.json`
- `OUT/audit/pipeline_full_master_certification/integration_report.json`
- `OUT/audit/pipeline_full_master_certification/governance_report.json`
- `OUT/audit/pipeline_full_master_certification/fallback_report.json`
- `OUT/audit/pipeline_full_master_certification/determinism_report.json`
- `OUT/audit/pipeline_full_master_certification/execution_batch.json`
- `OUT/audit/pipeline_full_master_certification/metrics.json`
- `OUT/audit/pipeline_full_master_certification/event_summary.json`
- `OUT/audit/pipeline_full_master_certification/human_review.json`

## 20. Block P - Verdict Logic

### GO
Use only if:
- all critical blocks pass
- no systemic failure remains
- no material regression remains
- no relevant silent failure remains
- governance remains intact
- real batch remains healthy
- residues are only minimal

### GO_WITH_MONITORING
Use if:
- all critical blocks pass
- the system is intact and operable
- only explicit and monitorable residues remain

### HOLD
Use if:
- any critical block fails
- material regression exists
- enforcement breaks
- boundary violation exists
- relevant silent failure exists
- quality collapses
- artifacts or governance become inconsistent

## 21. Operational Principle

This gate exists to convert the state of the pipeline from:
- functional and impressive

into:
- formally certifiable, auditable, defensible, and safe for continuation

Final rule:
- if this gate does not close, `Phase 3` must not advance

## 22. Honest Expected Verdict Today

Given the current state of the system, the most honest expected verdict is:

```json
{
  "verdict": "GO_WITH_MONITORING"
}
```

Not because of technical weakness, but because the system still carries explicit monitoring residues already recognized in the governed subsystems.

## 23. Runner Scope

Recommended runner:
- `tests/gates/system/run_pipeline_full_master_certification.py`

Recommended output directory:
- `OUT/audit/pipeline_full_master_certification`

Recommended implementation principle:
- reuse existing subsystem gates and governed artifacts whenever they are already canonical
- add only the minimum new controlled and integration coverage needed to certify the system as a whole
- do not fake real-batch evidence
- do not bypass the system governance registry

## 24. One-Line Summary

This checklist is the maximum gate required to prove that the full pipeline, agents, orchestration, governance, real execution, and auditability are operating exactly as defined and approved, with no hidden critical failures.


---

## Source: `docs/runtime/PIPELINE_MULTIAGENT_HEAVY_AUDIT_CHECKLIST_v1_0.md`

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


---

## Source: `docs/runtime/PIPELINE_TOTAL_HEAVY_AUDIT_CHECKLIST_v1_0.md`

# PIPELINE_TOTAL_HEAVY_AUDIT_CHECKLIST_v1_0

## 1. Objective

Prove that the current CortAI pipeline is working as expected:
- at unit level
- at integration level
- at orchestration level
- at governance level
- at real execution level
- at stability level

And prove that no hidden bug, inconsistency, architectural vulnerability, unmapped bottleneck, or material regression exists that should block continuation into the next subsystem.

## 2. Gate Rule

No new subsystem or agent should advance unless this gate closes with an acceptable verdict.

Allowed verdicts:
- `GO`
- `GO_WITH_MONITORING`

Blocking verdict:
- `HOLD`

## 3. Scope

Covered layers:
- Account Health
- Trend Analysis
- Learning
- Novelty / Saturation
- Strategy
- Experiment Capability
- Script
- Voice
- Asset
- Editor
- QC
- Creative Orchestrator
- Content Pipeline / Render
- Audit / Events / Artifacts

## 4. Final Question

At the end of the gate, the system must be able to answer:

```json
{
  "pipeline_integrity": true,
  "unit_layers_stable": true,
  "integration_layers_stable": true,
  "cross_agent_orchestration_valid": true,
  "governance_valid": true,
  "fallbacks_safe": true,
  "determinism_valid": true,
  "real_execution_valid": true,
  "quality_stable": true,
  "regression_detected": false,
  "promotion_blockers": []
}
```

## 5. Block A â€” Repository Structural Sanity

Objective:
- guarantee that critical system structure still exists

Must verify:
- critical directories exist
- canonical contracts exist
- orchestrator exists
- agent services exist
- critical tests exist
- canonical data paths exist
- canonical audit paths exist
- no critical expected file was removed

Blocking failures:
- missing essential contract
- missing orchestrator
- missing canonical directory
- missing critical runner

## 6. Block B â€” Agent Unit Stability

Objective:
- guarantee that each critical agent still works in isolation

Must cover:
- Account Health
- Trend
- Learning
- Novelty
- Strategy
- Experiment Capability
- Script
- Voice
- Asset
- Editor
- QC

Blocking failures:
- broken critical unit test
- broken critical contract
- invisible or invalid fallback

## 7. Block C â€” Contracts And Serialization

Objective:
- guarantee compatibility between producers and consumers

Must verify:
- `AccountHealthResult`
- `TrendAnalysisResult`
- `LearningAgentResult`
- `StrategyResult`
- `ScriptPlan`
- `VoicePlan`
- `AssetPlan`
- `EditPlan`
- `VideoQcResult`
- `CreativePack`
- `execution_outputs.json`

Blocking failures:
- non-serializable contract
- producer/consumer incompatibility
- missing mandatory field

## 8. Block D â€” Direct Agent Integration

Objective:
- prove real causality between agents

Must verify:
- Health alters Strategy
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
- Editor alters QC surface
- QC alters final publishability

Blocking failures:
- decorative payloads
- only cosmetic causality
- behaviorally inert critical layer

## 9. Block E â€” End-To-End Orchestration

Objective:
- guarantee the full sequence remains correct

Must verify:
- Health runs first
- Trend runs after Health
- Learning runs after Trend
- Novelty runs after Learning
- Strategy receives all required upstream context
- Script, Voice, Asset, and Editor receive correct context
- render executes
- QC executes
- pipeline finalizes the correct status

Blocking failures:
- wrong order
- skipped agent
- broken propagation
- pipeline breaks before completion

## 10. Block F â€” Enforcement And Governance

Objective:
- guarantee authorities remain correct

Must verify:
- Account Health `HOLD` blocks early
- QC remains final publishability authority
- publish manifest is not created before QC
- QC `HOLD` and `REJECT` block correctly
- Trend does not invade Learning
- Learning does not invade Strategy
- Strategy remains the control layer
- Novelty does not invade Trend
- fallback does not mask real failure

Blocking failures:
- QC bypass
- Health bypass
- boundary violation
- wrong publishability behavior

## 11. Block G â€” Fallbacks And Graceful Degradation

Objective:
- guarantee resilience without silent corruption

Must verify:
- Health fallback explicit
- Trend fallback explicit
- Learning fallback explicit
- Voice fallback explicit
- Asset fallback explicit
- fallback does not contaminate Learning
- fallback paths are visible in trace/events
- pipeline remains operational under controlled degradation

Blocking failures:
- invisible fallback
- fallback contaminates learning
- degraded pipeline breaks
- fallback pretends to be clean evidence

## 12. Block H â€” Determinism And Replay

Objective:
- guarantee controlled predictability

Must verify:
- same input => same Trend
- same input => same Health
- same input => same LearningPolicy
- same input => same StrategyProfile
- same input => same AssetPlan
- same input => same QC decision
- controlled replay remains stable

Blocking failures:
- unexplained drift
- divergent outputs under same input

## 13. Block I â€” Controlled Scenario Battery

Objective:
- exercise boundary and difficult scenarios

Minimum scenarios:
- healthy baseline
- Health `SAFE`
- Health `CAUTION`
- Health `HOLD`
- strong Trend manual
- Trend via creative center
- stale Trend
- Trend fallback
- Learning winner cluster
- Learning loser cluster
- Learning contamination cluster
- Novelty low
- Novelty medium
- Novelty high
- QC `APPROVE`
- QC `HOLD`
- QC `REJECT`
- borderline Asset
- strong Editor with weak Asset
- Script fallback
- Voice fallback

Must prove:
- correct decisions
- preserved governance
- coherent orchestration
- no unexpected side effect

## 14. Block J â€” Real Batch

Objective:
- prove the system works outside the lab

Minimum requirement:
- `3-5` fresh real executions or a methodologically accepted recent canonical batch
- valid `.mp4`
- valid audio
- valid metadata
- valid subtitles
- complete per-agent outputs

Minimum metrics:
- `ready_rate`
- `approve_rate`
- `average_overall_score`
- `valid_video_rate`
- `new_failure_patterns`
- `publishable_rate`

Blocking failures:
- invalid videos
- quality collapse
- new systemic failure pattern

## 15. Block K â€” Final Product Quality

Objective:
- guarantee the system not only runs, but still delivers quality

Must verify:
- stable hook quality
- stable payoff quality
- Asset quality has not collapsed
- Edit quality has not regressed
- product quality remains stable
- Novelty does not collapse approve rate
- Learning does not destabilize Strategy
- Trend does not create visual noise
- Account Health does not over-constrain
- QC remains coherent with product reality

Blocking failures:
- material quality regression
- approve rate collapse
- strong mismatch between perceived quality and QC

## 16. Block L â€” Observability And Auditability

Objective:
- guarantee post-run reconstruction

Must verify:
- critical events exist
- event payloads are sufficient
- agent traces exist
- execution outputs are rich enough
- warnings are persisted
- errors are persisted
- decision traces are persisted
- artifacts are complete

Blocking failures:
- missing critical events
- insufficient artifacts
- run cannot be reconstructed

## 17. Block M â€” Architectural Safety

Objective:
- guarantee that no dangerous architecture drift appeared

Must verify:
- no agent absorbed another agent's responsibility
- no contract inflated without real consumer
- no subsystem became a mega-agent
- boundaries remain explicit
- enforcement remains in the correct layer
- no dangerous manual bypass was introduced
- no critical dependency is silently broken

Blocking failures:
- improper coupling
- boundary collapse
- dangerous operational shortcut

## 18. Block N â€” Residual Report

Objective:
- separate real residuals from real blockers

Must verify:
- every residual is explicit
- every residual is classifiable as:
  - methodological
  - operational
  - blocking
- no critical residual was hidden as monitoring
- no real blocker was deferred dishonestly

## 19. Block O â€” Required Artifacts

The runner must generate at minimum:
- `OUT/audit/pipeline_total_heavy_audit/final_verdict.json`
- `OUT/audit/pipeline_total_heavy_audit/block_summary.json`
- `OUT/audit/pipeline_total_heavy_audit/agent_matrix.json`
- `OUT/audit/pipeline_total_heavy_audit/integration_report.json`
- `OUT/audit/pipeline_total_heavy_audit/governance_report.json`
- `OUT/audit/pipeline_total_heavy_audit/fallback_report.json`
- `OUT/audit/pipeline_total_heavy_audit/determinism_report.json`
- `OUT/audit/pipeline_total_heavy_audit/execution_batch.json`
- `OUT/audit/pipeline_total_heavy_audit/metrics.json`
- `OUT/audit/pipeline_total_heavy_audit/human_review.json`

## 20. Block P â€” Verdict Logic

### `GO`

Only if:
- every critical block passes
- no systemic failure remains
- no material regression exists
- governance intact
- causality intact
- real batch healthy
- only negligible residuals remain

### `GO_WITH_MONITORING`

If:
- the pipeline is functional and intact
- there are no real blockers
- but explicit non-blocking residuals still remain

### `HOLD`

If:
- any critical block fails
- material regression exists
- governance breaks
- orchestration breaks
- critical causality is false or symbolic
- relevant silent failure exists

## 21. Operational Principle

The purpose of this checklist is to make the following statement defensible without self-deception:

> the entire current pipeline works as expected, in unit tests, in integration, and in real execution, and there is no hidden bug, inconsistency, bottleneck, or architectural vulnerability that should block continuation of development

## 22. Honest Expected Outcome

If this gate is executed honestly on the current system, the most plausible verdict is:

```json
{
  "verdict": "GO_WITH_MONITORING"
}
```

Reason:
- the system is already strong and highly governed
- but it still carries explicit, non-blocking residuals that should remain under monitoring


---

## Source: `docs/runtime/PIPELINE_V2_FULL_SYSTEM_CERTIFICATION_CHECKLIST.md`

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
This checklist exists to convert the whole pipeline from â€œcomplex and functionalâ€ into â€œauditable and defensibleâ€.

Rule:
- if stable, do not touch


---

## Source: `docs/runtime/PIPELINE_V2_FULL_SYSTEM_VALIDATION_GATE_v1_0.md`

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


---

## Source: `docs/runtime/pre_d23_final_release_audit_gate_v1_0.md`

# Pre-D23 Final Release Audit Gate v1.0

## Objetivo

Executar um gate final pre-D23 com evidencia materializada em:

- `OUT/audit/pre_d23_final_gate/`

O gate e orientado a `GO/NO-GO`.

## Script

- `backend/scripts/run_pre_d23_final_release_audit_gate.ps1`

## Saidas geradas

- `OUT/audit/pre_d23_final_gate/AUDIT_REPORT.md`
- `OUT/audit/pre_d23_final_gate/unit_tests.txt`
- `OUT/audit/pre_d23_final_gate/regression_tests.txt`
- `OUT/audit/pre_d23_final_gate/py_compile.txt`
- `OUT/audit/pre_d23_final_gate/infra_health.txt`
- `OUT/audit/pre_d23_final_gate/security_scan.txt`
- `OUT/audit/pre_d23_final_gate/smoke_runtime_checks.txt`
- `OUT/audit/pre_d23_final_gate/video_batch_qc.txt`
- `OUT/audit/pre_d23_final_gate/consistency_check.json`
- `OUT/audit/pre_d23_final_gate/consistency_check.md`

## Uso recomendado

### Execucao completa

```powershell
./backend/scripts/run_pre_d23_final_release_audit_gate.ps1
```

### Execucao sem infra local

Uso apenas para validar o script ou trabalhar fora do ambiente completo.

```powershell
./backend/scripts/run_pre_d23_final_release_audit_gate.ps1 -SkipInfra
```

### Execucao sem ferramentas externas de seguranca

Uso apenas quando `pip-audit` ou `gitleaks` nao estiverem instalados.

```powershell
./backend/scripts/run_pre_d23_final_release_audit_gate.ps1 -SkipSecurity
```

## O que o gate verifica

### Build

- `python -m compileall backend/app`

### Testes

- `D27`
- `D28`
- `D29`
- `D30`
- `D31`
- `D32`
- `D33`
- `D34`
- `D37`
- `D38`
- regressao de `screen_text`
- regressao de `script_generation`
- `publish_records`
- `D23 rollout`

### Contratos

- `pipeline` sem import de `runtime`
- `pipeline` sem import de `safety`
- `analysis` sem import de `runtime` ou `content.pipeline`

### Infra

- `docker compose ps`
- `:8000/health`
- `:8000/ready`
- `:8002/health`
- `:8002/ready`

### Seguranca

- `python -m pip check`
- `pip-audit`
- `gitleaks`

Ferramentas ausentes sao marcadas como `N/A` com justificativa.

### Smoke operacional

- `scheduler/runtime D23`
- `safety D28`
- `pipeline D27`
- `publish_records`
- `metrics_collector`

### Video QC

O gate gera um batch curto de QC com `3` videos e valida:

- artefatos reais
- `render_duration_s >= 8.0`
- `3` cues
- timings validos
- cues nao vazios

### Consistency

Materializa:

- `consistency_check.json`
- `consistency_check.md`

## Regra de decisao

### GO

Somente se o `AUDIT_REPORT.md` fechar sem nenhum `FAIL`.

### NO-GO

Qualquer `FAIL` bloqueia o D23.

## Leitura do relatorio

O `AUDIT_REPORT.md` traz:

- dominio
- check
- status
- evidencia
- detalhe

Status validos:

- `PASS`
- `FAIL`
- `N/A`

`N/A` so e aceitavel quando houver justificativa operacional real.


---

## Source: `docs/runtime/pre_d23_integration_merge_checklist_v1_0.md`

# Pre-D23 Integration Merge Checklist v1.0

## Escopo

Checklist obrigatorio para integracao das branches:
- `D34 Analysis Layer`
- `D28 Safety Layer`
- `D27 Content Pipeline`

Objetivo: garantir compatibilidade com o runtime atual antes da execucao do `D23`.

## Bloqueadores Absolutos

1. `D27` importando qualquer modulo de `runtime`
2. `D27` chamando `safety` diretamente
3. `D27` escrevendo `publish_record` diretamente
4. `D28` reagendando job; `safety` deve apenas decidir
5. `D34` escrevendo fora de `OUT/analysis/*`
6. Ausencia de idempotencia baseada em `publish_key`

## Contratos de Execucao

### 7. Orquestracao

- `runtime` e `scheduler` chamam `pipeline`
- `pipeline` nao agenda tarefas
- `pipeline` nao cria jobs
- `pipeline` nao chama `scheduler` nem `executor`

Imports proibidos dentro de:
- `backend/app/content/pipeline/`
- `backend/app/safety/`
- `backend/app/analysis/`

Imports que nao devem aparecer:
- `from backend.app.runtime.scheduler import ...`
- `from backend.app.runtime.executor import ...`
- `from backend.app.runtime.rollout import ...`

### 8. Autoridade de decisao

- `D28` decide `ALLOW`, `DELAY` ou `BLOCK`
- `pipeline` executa somente se autorizado
- `runtime` chama `safety.evaluate()`

Fluxo permitido:
- `runtime -> safety -> decision -> runtime -> pipeline`

Fluxo proibido:
- `pipeline -> safety`
- `pipeline -> runtime.policy`

### 9. Fonte de verdade

- `runtime` e a autoridade de `scheduling`
- `safety` e a autoridade de `decision`
- `pipeline` e a autoridade de `content generation`
- `publish_record` e a autoridade de `publish state`
- `metrics_collector` e a autoridade de `metrics`
- `analysis layer` e a autoridade de `analysis`

Se algum modulo novo:
- sobrescreve `publish_record`
- altera metricas
- altera estado do `scheduler`

o merge deve ser rejeitado.

## Pipeline (D27)

### 10. Execucao pura

`pipeline` deve ser executavel sob um `ExecutionEnvelope`.

Campos minimos esperados:
- `job_id`
- `account_id`
- `creative_pack_id`
- `publish_slot`
- `experiment_variant`

`pipeline` nao pode:
- ler fila
- escrever estado global
- agendar jobs
- alterar cooldown

`pipeline` pode apenas:
- gerar conteudo
- gerar `publish_manifest`
- emitir eventos `CONTENT/*`
- retornar resultado

### 11. Contrato de retorno

`pipeline.execute(...)` deve retornar um objeto explicito com, no minimo:
- `status`
- `publish_manifest`
- `artifacts`
- `events_emitted`

Nenhum resultado implicito via side effect solto.

### 12. Tratamento de falhas

Falhas em `tts` ou `render` devem:
- emitir `CONTENT/pipeline_failed`
- produzir `status` terminal consistente
- nunca gerar `publish_record` parcial

### 13. Paths e filesystem

`pipeline` pode escrever somente em:
- `OUT/content/audio/`
- `OUT/content/video/`
- `OUT/content/metadata/`

Nenhum path fora de `OUT/`.

## Eventos Canonicos

`pipeline` deve emitir:
- `CONTENT/tts_started`
- `CONTENT/tts_completed`
- `CONTENT/render_started`
- `CONTENT/render_completed`
- `CONTENT/publish_manifest_created`
- `CONTENT/pipeline_failed`

`safety` deve emitir:
- `SAFETY/publish_allowed`
- `SAFETY/publish_delayed`
- `SAFETY/publish_blocked`

`runtime` nao deve emitir eventos de conteudo.

## Contrato de Manifest

`pipeline` deve produzir um `PublishManifest` com:
- `publish_id`
- `account_id`
- `video_path`
- `caption`
- `hashtags`
- `scheduled_time`

Confirmacoes obrigatorias:
- `runtime` consome o manifest
- `pipeline` nao escreve `publish_record` diretamente

## Idempotencia

Chave obrigatoria:

`publish_key = account_id + creative_pack_id + publish_slot`

Se existir `publish_record` com essa chave:
- a execucao deve retornar `NOOP`

Revisar especificamente:
- geracao de artefatos
- criacao de `publish_record`
- ausencia de duplicacao de publish

## Analysis Layer (D34)

Confirmar que `analysis` e read-only.

Nao pode haver:
- escrita em `publish_record`
- escrita em `metrics`
- escrita em `runtime`

`analysis` so pode:
- ler
- agregar
- gerar snapshots

Saidas permitidas:
- `OUT/analysis/*`

## Dependencias Proibidas

Arquitetura permitida:

`runtime -> safety -> pipeline -> content tools`

`pipeline` nao pode importar:
- `runtime`
- `rollout`
- `scheduler`

`analysis` nao pode importar:
- `pipeline`
- `runtime`

## Procedimento de Integracao

Aplicar o checklist separadamente para cada merge:

1. `D34`
2. `D28`
3. `D27`

Nunca validar apenas apos todos os merges.

## Teste Minimo Obrigatorio Apos Merge

### 1. Gate pesado

Executar:

`scripts/run_pre_d23_full_gate.ps1`

### 2. Geracao real de video

Artefatos esperados:
- `OUT/content/video/*.mp4`
- `OUT/content/audio/*.wav`

### 3. Eventos de pipeline

Eventos esperados:
- `CONTENT/tts_started`
- `CONTENT/render_completed`
- `CONTENT/publish_manifest_created`

### 4. Safety funcionando

Eventos esperados:
- `SAFETY/publish_allowed`
- ou `SAFETY/publish_blocked`

## Criterio Final de Aprovacao

O merge e aceito somente se:
- `pipeline` executa sob `ExecutionEnvelope`
- `safety` decide `ALLOW`, `DELAY` ou `BLOCK`
- `runtime` agenda
- idempotencia funciona
- eventos sao emitidos corretamente
- geracao real de video funciona
- `gate` completo fecha em `PASS`


---

## Source: `docs/runtime/pre_phase3_system_final_gate_v1_0.md`

# Pre-Phase3 System Final Gate

Versao: 1.0
Status: Aprovado para execucao
Script: `backend/scripts/run_pre_phase3_system_final_gate.ps1`

## Objetivo
Executar uma auditoria total do sistema antes da abertura da proxima fase do CortAI.

O gate valida:

- integridade do repositorio
- dependencias
- seguranca
- compilacao global
- suite total de testes
- regressao relevante da Fase 1
- regressao da camada cognitiva da Fase 2
- smoke completo do fluxo cognitivo
- auditoria de fallbacks
- governanca de contratos
- batch basico de stress
- telemetria minima
- consistencia minima
- auditoria basica de recursos

## Saida
O gate materializa evidencia em:

- `OUT/audit/pre_phase3_final_gate/`

Arquivos principais:

- `AUDIT_REPORT.md`
- `repo_required_paths.txt`
- `repo_git_status.txt`
- `pip_check.txt`
- `pip_audit.txt`
- `gitleaks.txt`
- `py_compile_all.txt`
- `unittest_discover.txt`
- `phase1_regression.txt`
- `cognitive_regression.txt`
- `contract_schema.txt`
- `fallback_audit.txt`
- `full_smoke.txt`
- `stress_batch.txt`
- `resource_audit.txt`

## Comando padrao

```powershell
./backend/scripts/run_pre_phase3_system_final_gate.ps1
```

## Modo de validacao rapida do runner

```powershell
./backend/scripts/run_pre_phase3_system_final_gate.ps1 -SkipInfra -SkipSecurity -SkipStressBatch -SkipResourceAudit
```

Esse modo nao fecha o gate final do sistema. Ele serve apenas para validar o proprio runner e a materializacao de evidencias sem gastar tempo com os trechos mais lentos.

## Criterio de GO / NO-GO

- `GO` apenas se `FAILURES = 0`
- qualquer `FAIL` bloqueia a abertura da proxima fase

## Observacoes

- `pip-audit`, `gitleaks` e a auditoria basica de recursos aceitam `N/A` apenas quando a ferramenta nao existe no ambiente
- o batch de stress reutiliza `backend/scripts/run_local_d23_18_batch.py`
- o smoke completo valida o fluxo:

```text
Account Health
-> Trend Analysis
-> Learning
-> Strategy
-> Experiment
-> Asset Selection
-> Creative Orchestrator
-> Script
-> Voice
-> Content Pipeline
-> Video QC
```

## Resultado esperado
Quando esse gate fecha limpo, o sistema esta tecnicamente pronto para iniciar a proxima fase sem regressao evidente na Fase 1 ou na Fase 2.


---

## Source: `docs/runtime/QC_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`

# QC Agent Evolution v2.0 Implementation Plan

## 1. Executive Summary

The current QC subsystem is implemented and integrated, but it is not yet a true governor of the CortAI pipeline. Today it behaves as a post-render technical validator. It inspects final artifacts, returns `APPROVE` or `REJECT`, and emits explainable reason codes. That is useful, but insufficient for production-grade governance.

The core deficiency is not that QC is absent. The deficiency is that QC does not yet hold governing authority over publishability:
- it runs after render
- publish manifest creation already happened before QC decides
- `REJECT` is observable, but not strongly enforced as a downstream state change
- `HOLD` is not operational
- product-layer judgment is largely absent

QC v2.0 is the minimum-change, maximum-impact evolution that fixes this.

Target state of v2.0:
- QC becomes a real gate
- only `APPROVE` is publishable
- `HOLD` becomes operational
- `REJECT` becomes strongly enforced
- QC evaluates both technical sanity and a minimum viable product layer
- decisions become more explicit and audit-friendly

This is the correct next move because:
- upstream agents are already baseline-stable
- the Editor Agent now produces quality sufficient for product use
- the system now needs a real authority layer that decides whether output is allowed to exist as publishable output

This phase does **not** attempt elite QC. It implements the minimum viable governor QC.

## 2. Current State Diagnosis

### What is implemented today

Grounded in:
- `backend/app/creative/agents/video_qc/models.py`
- `backend/app/creative/agents/video_qc/service.py`
- `backend/app/creative/orchestrator/service.py`
- `backend/app/content/pipeline/orchestrator.py`

Current implemented behavior:
- QC runs after the pipeline completes
- QC evaluates:
  - artifact presence
  - metadata presence
  - minimum render duration
  - subtitle cue structural validity
  - broken glyph presence
  - payoff darkness via metadata luma proxy
  - resolution validity
  - audio stream existence
- QC emits only:
  - `APPROVE`
  - `REJECT`
- QC stores explanation through:
  - `reasons`
  - `details`
- QC is integrated into orchestrator execution
- QC emits:
  - `CREATIVE/video_qc_approved`
  - `CREATIVE/video_qc_rejected`

### What is missing

Missing today:
- `HOLD`
- score model
- weighted quality model
- layer-specific quality scoring
- product-layer judgment of hook/payoff/publishability
- real downstream enforcement
- batch-aware reasoning
- baseline comparison
- confidence model
- persistent QC history

### Contract reality today

Current contract reality:
- `VideoQcInput`: defined but unused
- `VideoQcDecision`: defined but unused
- `VideoQcResult`: actual operational contract in use

### Enforcement reality today

Current problem:
- publish manifest is created inside `ContentPipelineOrchestrator.execute(...)` before QC runs
- QC happens later in `CreativeOrchestratorService.execute(...)`
- therefore QC currently judges a completed pipeline result instead of governing publishability before publish state is materialized

### Honest diagnosis

Current QC status:
- useful as technical sanity validator: yes
- product judge: no
- governor: no
- publish gate: not strongly enough

## 3. Target State of QC v2.0

QC v2.0 target state is intentionally narrow and operational.

It must introduce:
- `APPROVE`
- `HOLD`
- `REJECT`

It must combine:
- hard failures
- score summary
- essential product signals
- explicit publishability flag

It must enforce:
- only `APPROVE` is publishable
- `HOLD` is non-publishable and review-blocking
- `REJECT` is non-publishable and failure-state-like

It must remain:
- deterministic
- explainable
- non-corrective
- minimally invasive to the rest of the pipeline

It is still **not**:
- dynamic baseline QC
- batch-aware QC
- confidence-calibrated QC
- ranking QC

This is the minimum viable governor QC, not the final strategic QC.

## 4. Responsibility Boundary

### QC v2.0 will

- judge final output
- apply hard failures
- compute a minimum viable score summary
- evaluate minimum viable product signals
- issue `APPROVE`, `HOLD`, or `REJECT`
- declare whether output is publishable
- block downstream publishability when not approved
- explain its decision

### QC v2.0 will not

- rewrite script
- regenerate voice
- choose new assets
- rerender video
- repair captions
- auto-correct the edit
- rewrite metadata from upstream agents
- rank videos against each other
- perform batch curation

This boundary must remain strict.

QC is a judge and gate.
It is not a fixer.

## 5. Enforcement Layer Plan

This is the most important change in v2.0.

### Current behavior

Today:
1. pipeline generates audio
2. pipeline renders video
3. pipeline creates publish manifest
4. QC runs
5. orchestrator records QC result

This means publishability is materialized before QC authority exists.

### Required target behavior

Minimum safe enforcement rule:
- only `APPROVE` produces a publishable output state

Operational rule:
- if `qc.status != "APPROVE"`, the system must not promote the result as publishable

### Recommended minimal implementation approach

The minimum safe change is:

1. **Move publish manifest creation behind QC**
   - current publish manifest creation occurs in `backend/app/content/pipeline/orchestrator.py`
   - v2.0 should split render completion from publishability materialization

2. **Make the pipeline return a pre-publish result**
   - after TTS and render, pipeline should return artifacts and traces
   - publish manifest creation should become conditional on QC approval

3. **Let orchestrator invoke QC before publish manifest creation**
   - orchestrator already owns the QC call
   - this is the narrowest place to introduce enforcement without reopening upstream agents

### Proposed state transitions

#### On `APPROVE`
- output remains publishable
- publish manifest is created
- execution result remains publishable and ready

#### On `HOLD`
- no publish manifest is created
- output is marked non-publishable
- pipeline execution should return a governed non-publishable state
- artifact files may still exist for audit/review

#### On `REJECT`
- no publish manifest is created
- output is marked non-publishable
- artifacts may remain for audit/debug
- decision is final for that run

### What object/artifact must no longer be created before QC approval

The key artifact is:
- `PublishManifest`

Minimum requirement:
- `PublishManifest` must not be created before QC approval

Video and audio artifacts may still be generated because QC needs them to evaluate.

### Why this is the minimal safe approach

It avoids:
- redesigning render flow
- reopening upstream agents
- implementing rollback logic

It directly turns QC into authority by changing only the point at which publishability is materialized.

## 6. Decision Model Plan

QC v2.0 decision engine should be structured as:

1. hard failure evaluation
2. score summary computation
3. product signal evaluation
4. publishability gate
5. mapping to `APPROVE` / `HOLD` / `REJECT`

### Decision states

#### `APPROVE`
Conditions:
- no hard failures
- overall score above approve threshold
- no product veto
- publishable = true

#### `HOLD`
Conditions:
- no hard failure severe enough for reject
- borderline score or borderline product quality
- non-publishable pending human or later system review

#### `REJECT`
Conditions:
- any critical hard failure
- or explicit product veto
- publishable = false

### Hard failures

Keep current hard failures and extend them.

Current hard failures to preserve:
- `QC_ARTIFACTS_INVALID`
- `QC_VIDEO_MISSING`
- `QC_AUDIO_MISSING`
- `QC_METADATA_MISSING`
- `QC_DURATION_BELOW_MINIMUM`
- `QC_SUBTITLE_CUES_INVALID`
- `QC_EMPTY_CUE_TEXT`
- `QC_GLYPH_BROKEN`
- `QC_PAYOFF_TOO_DARK`
- `QC_RESOLUTION_INVALID`
- `QC_AUDIO_STREAM_MISSING`
- `QC_INTERNAL_ERROR`

### Essential perceptual vetoes

v2.0 should introduce a very small set of vetoes, not a large heuristic cloud.

Recommended product vetoes:
- `QC_HOOK_TOO_WEAK`
- `QC_PAYOFF_TOO_WEAK`
- `QC_NOT_PUBLISHABLE`

These should be based on simple, explainable heuristics from existing traces and metadata, not complex ML.

### Priority order

Priority order must be:
1. critical hard failure -> `REJECT`
2. product veto -> `REJECT`
3. borderline quality -> `HOLD`
4. otherwise -> `APPROVE`

This keeps decision logic interpretable.

## 7. Score Model Plan

v2.0 needs a score model, but it should remain small and heuristic.

### Required score dimensions

Minimum viable score summary:
- `script_quality`
- `voice_quality`
- `asset_quality`
- `edit_quality`
- `product_quality`
- `overall_score`

### Determinism

Scores should be deterministic from:
- traces already produced by pipeline
- final metadata
- QC-computed signals

### Nature of scores

These scores will initially be:
- heuristic
- hand-weighted
- not production-calibrated

The plan must acknowledge this explicitly.

### Recommended initial weights

Initial pragmatic weights:
- `script_quality`: `0.15`
- `voice_quality`: `0.15`
- `asset_quality`: `0.20`
- `edit_quality`: `0.20`
- `product_quality`: `0.30`

Why:
- product quality should dominate
- QC v2.0 is about publishability, not only upstream correctness

### Initial scoring approach

#### `script_quality`
Use cheap existing signals:
- presence and non-emptiness of hook/setup/payoff
- structural continuity inferred from existing `ScriptPlan`

#### `voice_quality`
Use cheap existing signals:
- audio stream present
- audio duration valid
- segment duration trace present
- fallback may lower score but not necessarily veto

#### `asset_quality`
Use cheap existing signals:
- asset trace exists
- all segments resolved
- no obvious invalid asset resolution state
- payoff not too dark

#### `edit_quality`
Use cheap existing signals:
- subtitle structure valid
- editor trace present when editor is enabled
- duration and resolution valid

#### `product_quality`
Use v2.0 product layer:
- hook quality
- payoff quality
- publishability

### Why score alone is insufficient

Score must not replace vetoes because:
- missing video can never be rescued by score
- invalid resolution can never be publishable
- some weak-product cases should be `HOLD` or `REJECT` even if structural scores are otherwise acceptable

Therefore score is advisory plus decision-support, not sole authority.

## 8. Essential Product-Layer Evaluation Plan

v2.0 should add the first minimal product layer.

### Required product signals

At minimum:
- `hook_quality`
- `payoff_quality`
- `publishable`

Optional if cheap:
- `setup_progression`
- `phase1_risk`
- `repetition_risk`

### Hook quality

Purpose:
- approximate whether the opening is strong enough to justify publishability

Cheap signals available today:
- caption cue structure in first segment
- hook duration not too flat or too short
- presence of editor trace / caption plan / timing plan
- visual trace present for hook asset

This is still heuristic, but better than no product layer.

### Payoff quality

Purpose:
- approximate whether the ending lands clearly enough

Cheap signals available today:
- payoff cue presence and validity
- payoff duration
- payoff visual brightness threshold
- editor timing / landing metadata if present

### Publishability

`publishable` must become an explicit boolean output of QC decision.

It should be true only when:
- no hard failures
- no product vetoes
- score above threshold

### Structural vs perceptual

Structural checks:
- artifact existence
- metadata existence
- subtitle structure
- duration
- resolution
- audio stream

Perceptual checks:
- hook quality
- payoff quality
- minimal publishability assessment

### Veto behavior

Recommended:
- hard technical failure -> immediate `REJECT`
- clearly unpublishable product -> `REJECT`
- borderline product -> `HOLD`

## 9. Contract Evolution Plan

### Principle

Do not invent a second incompatible QC universe.

Use existing contracts, but make them operational.

### Recommended authoritative contract

Make `VideoQcDecision` the authoritative decision contract.

Reason:
- its name already matches the role of governor logic
- it should hold the formal decision state

Then make `VideoQcResult` the transport/report wrapper around that decision.

### Recommended evolution

#### `VideoQcInput`

Revive it and make it operational.

Add fields minimally:
- `render_job_id`
- `video_path`
- `audio_path`
- `metadata_path`
- `script_text` or hook/setup/payoff references if already cheaply available
- `voice_trace`
- `visual_trace`
- `edit_trace`

Purpose:
- make QC inputs explicit
- avoid hidden dependence on ad hoc artifact dicts

#### `VideoQcDecision`

Evolve to include:
- `status: Literal["APPROVE", "HOLD", "REJECT"]`
- `publishable: bool`
- `hard_failures: list[str]`
- `soft_failures: list[str]`
- `product_vetoes: list[str]`
- `score_summary: dict[str, float]`
- `decision_trace: dict[str, Any]`
- `checked_at: str`

This becomes the real decision contract.

#### `VideoQcResult`

Keep it for backward compatibility, but make it carry the decision contract explicitly.

Recommended fields:
- `decision: VideoQcDecision`
- `status` retained as compatibility mirror
- `reasons` retained as flattened reasons
- `checked_at`
- `details`

Migration note:
- existing consumers using `status` and `reasons` continue to work
- richer consumers can use `decision`

### Layer score fields

Inside `score_summary`, add:
- `script_quality`
- `voice_quality`
- `asset_quality`
- `edit_quality`
- `product_quality`
- `overall_score`

### Why this is minimal

It activates contracts that already exist conceptually, instead of inventing a totally new QC schema.

## 10. Explainability Plan

QC v2.0 decisions must be explainable by construction.

Minimum required explanation payload:
- final decision status
- `publishable`
- hard failures
- soft failures
- product vetoes
- score summary
- product signal summary
- decision trace

### Required explainability outputs

For `APPROVE`:
- why it passed
- key supporting scores/signals

For `HOLD`:
- why it is blocked but not rejected
- which quality dimensions are borderline

For `REJECT`:
- which hard or veto conditions caused rejection

### Decision trace content

Minimum `decision_trace` should include:
- `hard_failure_passed`
- `score_thresholds`
- `product_signals`
- `vetoes_applied`
- `final_mapping_rule`

This is enough for auditability without overbuilding.

## 11. File-Level Implementation Surface

### Required file changes

#### `backend/app/creative/agents/video_qc/models.py`
Required changes:
- activate `VideoQcInput`
- evolve `VideoQcDecision`
- evolve `VideoQcResult`
- add `HOLD`
- add score/dependency fields

#### `backend/app/creative/agents/video_qc/service.py`
Required changes:
- change evaluation from binary technical validator to governor decision engine
- support `VideoQcInput`
- compute hard failures
- compute score summary
- compute product signals
- emit `APPROVE` / `HOLD` / `REJECT`

#### `backend/app/creative/orchestrator/service.py`
Required changes:
- build explicit QC input from pipeline output and traces
- obey QC publishability
- change event emission to include `HOLD`
- ensure `qc != APPROVE` produces non-publishable result state

#### `backend/app/content/pipeline/orchestrator.py`
Required changes:
- move or split publish manifest creation so it no longer happens before QC approval

### Likely required file changes

#### `backend/app/content/pipeline/service.py`
Likely changes:
- preserve backward-compatible output while supporting deferred publish manifest

#### `backend/app/creative/orchestrator/models.py`
Likely changes:
- represent richer QC output and possibly non-publishable execution state cleanly

### Optional / minimal file changes

#### `backend/app/content/pipeline/models.py`
Only if needed:
- add explicit pre-publish or publishable status fields

This file should be touched only if current status model becomes too ambiguous.

## 12. Migration Strategy

Migration must be incremental and backward-safe.

### Step 1

Add richer QC contracts while preserving current `status` and `reasons`.

This allows:
- old tests and consumers to keep working
- new decision fields to be introduced safely

### Step 2

Change QC service to produce:
- `APPROVE`
- `HOLD`
- `REJECT`

while preserving a flattened `status` field in `VideoQcResult`.

### Step 3

Introduce deferred publish manifest creation.

This is the biggest behavioral change.

Safe rollout path:
- pipeline still renders exactly as before
- publish manifest creation becomes conditional after QC approval
- only publishability timing changes

### Step 4

Update orchestrator return payload so callers can still inspect:
- artifacts
- QC decision
- publish manifest if approved

### Backward compatibility rules

Must preserve:
- `VideoQcResult.status`
- `VideoQcResult.reasons`
- execution payload shape as much as possible

Can add:
- `decision`
- `publishable`
- `score_summary`
- `decision_trace`

### Why this reduces rollout risk

It avoids:
- changing upstream plans
- changing artifact generation
- changing agent interfaces outside QC/orchestrator/publish timing

## 13. Test Plan

### A. Unit tests

Required:

1. contract serialization
- `VideoQcInput`
- `VideoQcDecision`
- `VideoQcResult`

2. decision engine
- approve path
- hold path
- reject path

3. hard failure behavior
- preserve current hard failures

4. score calculation
- deterministic score summary
- overall score calculation

5. publishability evaluation
- `publishable = true` only on approve

6. explainability output
- decision trace present
- score summary present
- reason sets correct

Likely file:
- `tests/agents/video_qc/test_video_qc_agent_phase2_unittest.py`
- plus a new focused file such as `tests/test_video_qc_decision_engine_unittest.py`

### B. Integration tests

Required:

1. orchestrator obeys QC decision
- `APPROVE` -> publishable progression
- `HOLD` -> non-publishable progression
- `REJECT` -> non-publishable progression

2. publish manifest enforcement
- publish manifest absent when `qc != APPROVE`

3. execution result preservation
- artifacts still available for audit even on `HOLD` and `REJECT`

4. backward compatibility
- existing successful flows still work with `APPROVE`

Likely files:
- new orchestrator integration tests
- new pipeline enforcement tests

### C. Heavy validation gate

Create:
- `QC_AGENT_EVOLUTION_v2_0_VALIDATION_GATE`

Expected artifacts:
- `OUT/audit/qc_agent_evolution_v2_0_validation/block_summary.json`
- `OUT/audit/qc_agent_evolution_v2_0_validation/final_verdict.json`
- `OUT/audit/qc_agent_evolution_v2_0_validation/decision_examples.json`
- `OUT/audit/qc_agent_evolution_v2_0_validation/execution_batch.json`
- `OUT/audit/qc_agent_evolution_v2_0_validation/human_review.json` if a human-like review layer is added in gate logic

The gate must exercise:
- `APPROVE`
- `HOLD`
- `REJECT`
- publish enforcement
- explainability

## 14. Success Criteria

v2.0 is successful only if all of these are true:

1. `HOLD` is operational
2. `APPROVE`, `HOLD`, and `REJECT` are all exercised in tests
3. `REJECT` truly prevents publishable status
4. `HOLD` truly prevents publishable status
5. `PublishManifest` is created only after QC approval
6. QC decisions remain explainable
7. a minimal product layer exists
8. no upstream agent behavior is reopened
9. existing approve-path pipeline behavior remains compatible

## 15. Non-Goals / Out of Scope

v2.0 will not implement:
- dynamic baseline comparison
- batch-aware ranking
- novelty handling
- calibrated confidence model
- automated corrective loops
- ranking videos against each other
- top-k publish selection
- production-performance calibration
- deep multimodal perceptual modeling

These belong to later phases.

## 16. Risks and Mitigations

### Risk: QC becomes too rigid
Mitigation:
- introduce `HOLD` so borderline cases do not become forced `REJECT`

### Risk: `HOLD` blocks too much
Mitigation:
- keep v2.0 product signals minimal and explicit
- use conservative thresholds

### Risk: publish enforcement breaks downstream assumptions
Mitigation:
- change only publish manifest timing
- preserve artifacts and execution payloads

### Risk: score model approves mediocre videos
Mitigation:
- score cannot override hard failures or product vetoes
- score is advisory within a layered decision model

### Risk: product veto becomes too subjective
Mitigation:
- keep product layer small, explicit, and traceable
- only use hook/payoff/publishability in v2.0

### Risk: contract migration breaks consumers
Mitigation:
- preserve `status` and `reasons`
- add richer fields instead of replacing old ones abruptly

## 17. Next Correct Move After v2.0

If v2.0 succeeds, the next logical phase is:

1. dynamic baseline comparison
2. batch-aware QC
3. confidence model
4. ranking/selection inside batch
5. calibration from production engagement data

That next phase should happen only after:
- enforcement is real
- decision model is operational
- product layer exists

## Appendix: Minimal Change Principle

This plan is intentionally conservative.

It does not assume:
- new upstream capabilities
- new correction loops
- major pipeline redesign

It uses the narrowest possible path to convert QC from:
- observer

into:
- governing gate

The central mechanical change is simple:

**publishability must be decided after QC, not before QC**

Everything else in v2.0 should be built around that rule.


---

## Source: `docs/runtime/real_batch_rollout_v1_0.md`

# Real 72h Batch Production Rollout v1.0

## Objetivo

Executar o primeiro ciclo real de 72h em modo controlado.

O rollout desta etapa Ã©:

- piloto
- pequeno
- allowlisted
- reversÃ­vel

## Regras congeladas

- rollout comeÃ§a com poucas contas
- scheduler sÃ³ agenda contas allowlisted
- worker respeita kill switch e policy de rollout
- rollout desabilitado impede novas tasks
- kill switch impede novas execuÃ§Ãµes

## CritÃ©rio GO do Batch-0

O batch piloto Ã© vÃ¡lido se gerar:

- `window_metrics`
- `scorecard`
- `content_attribution`
- `strategy_patch`
- `patch_applied` ou `NOOP` legÃ­timo

Sem:

- `double_apply`
- `snapshot_partial`
- alerta crÃ­tico
- conflict inesperado

## CritÃ©rio NO-GO

Parar rollout se houver:

- `double_apply > 0`
- `snapshot_partial > 0`
- `event_query_error_rate` crÃ­tico
- `data_consistency_guard` bloqueando contas piloto sem justificativa

## Artefatos

SaÃ­da mÃ­nima:

- `OUT/rollout/pilot_rollout_report.md`
- `OUT/rollout/pilot_rollout_report.json`
- `OUT/rollout/pilot_batch_window_summary.json`
- `OUT/rollout/pilot_alerts.json`


---

## Source: `docs/runtime/SATURATION_NOVELTY_ENGINE_FULL_VALIDATION_GATE_v1_0.md`

# Saturation Novelty Engine Full Validation Gate v1.0

## 0. Exit Rule

The Saturation / Novelty Engine only passes without material reservation if all of the following are true:
- repeated patterns are actually detected
- memory is real, bounded, and deterministic
- novelty pressure changes Strategy behavior for the right reasons
- Script and Asset change behavior when pressure requires it
- diversity increases in a measurable way
- QC quality does not materially collapse
- APPROVE rate does not materially collapse
- the system does not fake diversity through superficial wording only
- the gate remains honest about what is still out of scope

If any of these pillars fail:
- `HOLD`
- do not promote

## 1. Signature Model

This block defines what the system is allowed to call a repeatable pattern.

### 1.1 Required signatures

The engine must define at least:
- `payoff_structure`
- `semantic_closure_type`
- `visual_payoff_family`

Optional but acceptable additional signals:
- `hook_family`
- `motif_signature`
- `strategy_variation_policy`

### 1.2 What counts as `payoff_structure`

A payoff structure is not raw text.
It is the structural pattern of the closure.

Examples:
- `named_location_removed`
- `device_points_to_impossible_place`
- `record_names_impossible_identity`
- `sealed_access_physical_reveal`
- `documentary_proof_reveal`

### 1.3 What counts as `semantic_closure_type`

A semantic closure type is not just the literal words.
It is the meaning family.

Examples:
- `removed_from_system`
- `impossible_room_reference`
- `warning_panel_contradiction`
- `identity_reveal`
- `archival_discrepancy`
- `contained_presence_reveal`

### 1.4 What counts as `visual_payoff_family`

This must come from real runtime output.

Examples:
- `map_blueprint`
- `warning_display`
- `sealed_access`
- `intercom_recorder`
- `document`

### 1.5 Anti-fake-diversity rule

The gate must explicitly reject superficial variation.

Examples of superficial variation:
- `door 16 removed from the floorplan`
- `room 12 missing from the map`

If both still map to the same structural and semantic signature:
- they count as repetition
- they do not count as meaningful diversity

## 2. Memory Window

This block defines how much history the engine remembers.

### 2.1 Required memory model

The engine must use a bounded memory window.
It must not use infinite implicit memory.

Recommended v1.0 configuration:
```json
{
  "memory_window": {
    "recent_videos": 20,
    "focus_last_n": 5,
    "weight_decay": "linear"
  }
}
```

### 2.2 Required properties

The gate must prove:
- memory window exists
- most recent videos have higher weight
- older videos still contribute lightly
- the system does not overreact to a single video
- the system does not forget too slowly

### 2.3 Determinism requirement

Given the same recent execution history:
- the same saturation state must be produced every time

## 3. Saturation Scoring

This block proves that repetition pressure is derived correctly.

### 3.1 Required dimensions

The engine must score at least:
- `semantic_saturation`
- `visual_saturation`
- `structural_saturation`

### 3.2 Required scoring behavior

The gate must prove:
- repeated `visual_payoff_family` raises visual saturation
- repeated `semantic_closure_type` raises semantic saturation
- repeated `payoff_structure` raises structural saturation
- repeated wins with `variation_policy = low` increase novelty pressure when appropriate

### 3.3 Required outputs

The engine must expose:
- saturation levels
- dominant repeated patterns
- novelty pressure profile
- trace of why the levels were assigned

## 4. Pressure Levels

This block defines the operational meaning of novelty pressure.

### 4.1 Required taxonomy

```json
{
  "pressure_levels": {
    "low": "prefer_variation",
    "medium": "bias_variation",
    "high": "force_variation",
    "critical": "block_pattern"
  }
}
```

### 4.2 Required interpretation

The gate must prove:
- `low` does not force behavior changes
- `medium` creates real but bounded bias
- `high` creates enforceable downstream deviation
- `critical` blocks repeated patterns only in extreme cases

### 4.3 Safety requirement

`critical` must be rare.
If it triggers too easily:
- the engine is overblocking
- the gate should fail or downgrade

## 5. Strategy Enforcement

This block proves that novelty pressure becomes strategic posture, not just metadata.

### 5.1 Required effects in Strategy

The gate must prove that novelty pressure can:
- raise `variation_policy`
- preserve health/risk hierarchy
- record novelty adjustments in `decision_trace`

### 5.2 Required hierarchy

The gate must prove:
- novelty does not override `HOLD`
- novelty does not break safety constraints
- novelty is applied after trend/metrics/constraints but before final clamp

### 5.3 Required causal evidence

It must be possible to show:
- same base input without novelty pressure -> one strategy output
- same base input with novelty pressure -> meaningfully different strategy output

## 6. Script Enforcement

This block proves that repeated payoff structures are actually avoided.

### 6.1 Required behavior

The gate must prove:
- blocked payoff structures are not reused when pressure requires change
- Script does not only reword the same pattern
- fallback and repair logic also obey blocked structures

### 6.2 Required examples

Examples the gate should test:
- `removed_from_floorplan` becomes saturated
- Script is asked to produce same niche/topic family
- expected: alternate closure family

Allowed alternate families:
- `warning_panel_contradiction`
- `identity_reveal`
- `archival_discrepancy`
- `sealed_access_reveal`

### 6.3 Anti-superficial-diff test

The gate must explicitly compare:
- literal diff
- structural diff
- semantic diff

A changed sentence that preserves the same structural/semantic signature:
- does not count as success

## 7. Asset Enforcement

This block proves that repeated payoff visual families are actually avoided.

### 7.1 Required behavior

The gate must prove:
- blocked visual payoff family is not selected for payoff when pressure requires change
- alternate approved families are selected deterministically
- `AssetPlan` reflects the realized runtime asset family correctly

### 7.2 Required examples

Examples the gate should test:
- `map_blueprint` saturated -> payoff must move to `warning_display` or `sealed_access`
- `warning_display` saturated -> payoff must move to `sealed_access`, `document`, or `intercom_recorder`

### 7.3 Runtime honesty

The gate must reject false compliance where:
- the plan says one category
- the selected asset belongs to another family

Only realized runtime family counts.

## 8. Controlled Repetition Batches

This is the heart of the gate.

### 8.1 Baseline repetitive batch

Build a controlled batch where the baseline system would naturally repeat a winning payoff family.

Required output:
- visible repeated signatures
- visible repeated payoff family

### 8.2 Novelty-governed batch

Run the same batch with the Saturation / Novelty Engine active.

Expected:
- repeated signature rate falls
- payoff family diversity rises
- quality remains acceptable

### 8.3 Batch types

Required:
- small synthetic repetition batch
- small realistic repetition batch

Recommended:
- `5-case` focused repetition batch
- `10-case` broader diversity batch

## 9. Metrics Before / After

This block is mandatory.

### 9.1 Required metrics

```json
{
  "metrics": {
    "pattern_repetition_rate_before": "...",
    "pattern_repetition_rate_after": "...",
    "visual_family_repetition_rate_before": "...",
    "visual_family_repetition_rate_after": "...",
    "novelty_diversity_index_before": "...",
    "novelty_diversity_index_after": "...",
    "qc_score_delta": "...",
    "approve_rate_delta": "..."
  }
}
```

### 9.2 Required success interpretation

Success means:
- repetition decreases
- diversity increases
- QC score remains materially stable
- APPROVE rate remains materially stable

Failure means either:
- diversity did not really improve
- or diversity improved by collapsing quality

## 10. QC Stability

This block proves the engine did not break the product layer.

### 10.1 Required checks

The gate must compare before/after on:
- `APPROVE rate`
- `HOLD rate`
- `REJECT rate`
- `overall_score`
- `product_quality`
- `payoff_quality`

### 10.2 Failure conditions

The gate should fail or downgrade if:
- `APPROVE rate` collapses materially
- `QC overall score` collapses materially
- the novelty-governed batch becomes visibly weaker on average

### 10.3 Acceptable tradeoff

Minor score variance is acceptable.
Material quality loss is not.

## 11. Determinism

This block is non-negotiable.

### 11.1 Same history, same novelty pressure

The gate must prove:
- same recent window -> same saturation scores
- same recent window -> same novelty pressure profile
- same recent window -> same Strategy adjustment

### 11.2 Same blocked pattern, same downstream response

The gate must prove:
- Script reacts deterministically
- Asset reacts deterministically

### 11.3 No hidden randomness

The engine must not pass if diversity comes from uncontrolled randomness rather than governed novelty pressure.

## 12. Auditability

This block proves the engine is explainable.

### 12.1 Required artifacts

- `block_summary.json`
- `final_verdict.json`
- `decision_examples.json`
- `execution_batch.json`
- `metrics.json`

### 12.2 Required traceability

It must be possible to answer:
- what patterns were detected as repeated?
- what window caused the pressure?
- what pressure level was emitted?
- what did Strategy change?
- what did Script change?
- what did Asset change?

### 12.3 Required honesty

The engine must not claim:
- structural novelty
if only wording changed

The engine must not claim:
- visual novelty
if the same payoff family still dominated

## 13. Honesty About Out-of-Scope

The gate must explicitly confirm what v1.0 does not yet do.

### 13.1 Out of scope

- general creativity optimization
- long-horizon novelty control
- account-specific adaptive fatigue tuning
- global batch ranking
- experiment controller integration
- Editor novelty governance
- Voice novelty governance

### 13.2 Honesty requirement

If the engine improves payoff diversity only:
- that is acceptable for v1.0
- but it must be stated clearly

## 14. Final Gate

The Saturation / Novelty Engine passes at high level only if:

### Signature
- signatures are real
- memory is bounded
- superficial variation is not mistaken for structural novelty

### Decision
- saturation scoring is correct
- pressure levels are correct
- Strategy reacts correctly

### Causality
- Script changes meaningfully
- Asset changes meaningfully
- repeated winning patterns are actually reduced

### Product
- QC remains stable enough
- APPROVE rate remains stable enough
- diversity rises without collapsing quality

### Honesty
- limitations are explicit
- novelty is not overstated

## 15. Operational Verdicts

### `GO`

Use when:
- repetition falls materially
- diversity rises materially
- QC remains stable
- APPROVE rate remains stable
- novelty pressure is deterministic and auditable

### `GO_WITH_MONITORING`

Use when:
- repetition control works
- quality remains acceptable
- but effect is still concentrated mostly in payoff layer
- broader novelty governance remains for later phases

### `HOLD`

Use when:
- repeated patterns are still not actually reduced
- diversity gains are superficial only
- or quality collapses materially

## 16. Practical Execution Blocks

### Block A — Signatures and memory
- signature extraction
- memory window
- weight decay
- deterministic reconstruction

### Block B — Saturation scoring
- semantic saturation
- structural saturation
- visual saturation
- repeated pattern list

### Block C — Strategy novelty pressure
- pressure levels
- Strategy trace
- hierarchy with safety and constraints

### Block D — Downstream enforcement
- Script blocked structures
- Asset blocked payoff families
- anti-superficial-diff checks

### Block E — Batch validation
- repetitive baseline batch
- novelty-governed batch
- before/after metrics
- QC stability
- audit artifacts

## 17. One-Line Summary

This gate exists to prove that CortAI can diversify in a controlled way under batch pressure without collapsing quality, and that the system is escaping repeated winning patterns structurally, not just cosmetically.


---

## Source: `docs/runtime/SATURATION_NOVELTY_ENGINE_PRODUCTION_SOAK_PLAN.md`

# Production Soak Plan

## Objective
Validate `SATURATION_NOVELTY_ENGINE_v1_0` under real production-like operation without reopening implementation.

## Scope
This soak covers only monitoring of the frozen baseline:
- `Strategy v2`
- `Script v2`
- `Asset v2`
- `QC v2`
- `SATURATION_NOVELTY_ENGINE_v1_0`

It does not include:
- new novelty logic
- new strategy fields
- editor novelty expansion
- experiment-control expansion
- architectural refactors

## Operational Rule
`if STABLE -> do not touch`

## Soak Window
Recommended minimum:
- `7 days` or `100 approved videos`, whichever comes later

Recommended preferred window:
- `14 days` or `250 approved videos`, whichever comes later

## Monitoring Metrics
Track at batch and rolling-window level.

Primary metrics:
- `structural_repetition_rate`
- `visual_repetition_rate`
- `diversity_index`
- `approve_rate`
- `average_overall_score`
- `qc_hold_rate`
- `qc_reject_rate`

Secondary metrics:
- `novelty_pressure_level_distribution`
- `variation_policy_distribution`
- `blocked_payoff_structures_frequency`
- `blocked_visual_payoff_categories_frequency`

## Baseline Reference
Use the promoted full-gate after-values as the initial baseline reference.

Reference values:
- `structural_repetition_rate = 0.6`
- `visual_repetition_rate = 0.6`
- `diversity_index = 0.4`
- `approve_rate = 1.0`
- `average_overall_score = 0.9095`

## Rolling Windows
Use two windows:
- short window: `last 20 approved videos`
- medium window: `last 100 approved videos`

Reason:
- the short window catches fast repetition drift
- the medium window catches slow saturation drift

## Success Criteria
The soak is successful if all of the following remain true:
- structural repetition does not drift materially above baseline
- visual repetition does not drift materially above baseline
- diversity does not drift materially below baseline
- approve rate does not materially collapse
- average overall QC score does not materially collapse
- novelty pressure still escalates when repeated approved patterns accumulate

## Reopen Triggers
Reopen the subsystem only if one or more of these are observed:
- `structural_repetition_rate > baseline + 0.1`
- `visual_repetition_rate > baseline + 0.1`
- `diversity_index < baseline - 0.1`
- `approve_rate < baseline - 0.2`
- `average_overall_score < baseline - 0.08`
- repeated approved batches stop causing novelty escalation
- blocked payoff structures stop changing Script output
- blocked visual payoff families stop changing Asset output

## Reopen Thresholds
Use explicit thresholds to avoid noise-driven reopens.

```json
{
  "reopen_thresholds": {
    "structural_repetition_rate_increase": 0.1,
    "visual_repetition_rate_increase": 0.1,
    "diversity_index_drop": 0.1,
    "approve_rate_drop": 0.05,
    "average_overall_score_drop": 0.05
  }
}
```

Interpretation:
- reopen only on material drift, not small variance
- keep the threshold policy fixed during the soak window
- do not override thresholds with intuition unless a separate incident is confirmed

## Incident Handling
If a regression is detected:
1. freeze deployment changes around the subsystem
2. capture a reproducible batch
3. compare against baseline gate artifacts
4. classify the issue as one of:
- novelty memory failure
- strategy enforcement failure
- script enforcement failure
- asset enforcement failure
- unrelated pipeline/environment failure

Do not patch immediately without a reproduced failure class.

## Governance Notes
Keep the following incident in the soak record:
- `backend/app/assets/catalog.json` corruption
- backup created
- rebuild completed
- treated as repaired infrastructure incident, not engine instability

## Output Artifacts
Recommended soak artifacts:
- `OUT/audit/saturation_novelty_engine_production_soak/soak_summary.json`
- `OUT/audit/saturation_novelty_engine_production_soak/rolling_metrics.json`
- `OUT/audit/saturation_novelty_engine_production_soak/regression_alerts.json`
- `OUT/audit/saturation_novelty_engine_production_soak/human_review.json`

## Exit Conditions
At the end of soak:
- if stable: keep baseline frozen
- if regression exists: open targeted correction only
- if behavior is stable but limited: defer expansion to next planned phase


---

## Source: `docs/runtime/SATURATION_NOVELTY_ENGINE_SYSTEM_PLAN.md`

# Saturation Novelty Engine System Plan

## 1. Executive Summary

The next bottleneck in the CortAI pipeline is no longer baseline content quality or baseline pipeline reliability.

Those layers are now strong enough that the dominant risk has shifted to repetition under batch production.

The current system can:
- generate publishable videos
- pass QC consistently
- preserve deterministic behavior
- maintain operational governance

The current system still cannot do well enough:
- detect that winning patterns are being reused too often
- budget novelty across a batch
- modulate repetition before it becomes perceptually obvious
- explicitly govern saturation at semantic, structural, and visual levels

This is the correct time to introduce a dedicated Saturation / Novelty Engine.

Its purpose is not to replace the existing agents.
Its purpose is to govern when repeated success patterns should be preserved, diversified, or avoided.

Most accurate goal:
- move the system from "good content generator" to "attention-competitive system with controlled novelty"

## 2. Problem Statement

Recent batch validation proved:
- multiple videos can reach `READY + APPROVE`
- QC is functioning correctly
- script payoff quality improved materially
- asset evidence strength improved materially

The same batch also revealed:
- repeated payoff structure across approved videos
- repeated payoff visual family across approved videos
- repeated semantic closure pattern
- repeated strategic posture because `variation_policy = low`

This is not a bug.
It is the expected result of a deterministic system that discovered a working pattern and has not yet been given a novelty governor.

The new problem is:
- preserving quality while preventing pattern fatigue

That is a different class of problem from earlier phases.

## 3. Mission of the Saturation / Novelty Engine

The engine should:
- observe what recently succeeded
- detect when the same motif or structural pattern is being reused too often
- convert repetition signals into bounded novelty pressure
- influence generation posture before saturation becomes obvious
- do this deterministically and auditably

It should not:
- replace QC
- replace Script, Asset, or Editor logic directly
- become a free-form creative optimizer
- introduce stochastic novelty for its own sake

Boundary principle:
- novelty is a governed response to saturation, not random variation

## 4. System Position in the Pipeline

Recommended future position:

`Account Health -> Trend Analysis -> Learning -> Saturation/Novelty -> Strategy -> Script -> Voice -> Asset -> Editor -> QC`

Alternative acceptable integration:
- Saturation / Novelty logic can be embedded inside `Strategy v3`
- but its signals should still be explicit and auditable as a separate conceptual layer

Recommended practical implementation path:
- Phase 1: standalone signal builder producing `NoveltyPressureProfile`
- Phase 2: Strategy consumes that profile
- Phase 3: downstream agents materially obey novelty pressure

Reason:
- separating the signal layer from the policy layer reduces confusion and improves auditability

## 5. Core Concepts

### 5.1 Saturation

Saturation means:
- the system is reusing the same structure, motif, evidence form, or closure pattern often enough that human viewers will perceive repetition

Saturation is not just exact duplication.
It includes:
- semantic repetition
- structural repetition
- visual family repetition
- payoff closure repetition

### 5.2 Novelty

Novelty means:
- bounded deviation from recent patterns in order to preserve freshness without breaking baseline quality

Novelty is not randomness.
Novelty is controlled, selective divergence.

### 5.3 Novelty budget

A novelty budget is:
- the allowed amount of deviation from recent winning patterns for a given batch or window

Too low:
- the system becomes repetitive

Too high:
- the system becomes unstable and loses quality

### 5.4 Repetition unit

The engine should not reason only at the full-video level.
It should reason across repeatable units such as:
- hook family
- payoff structure
- evidence family
- asset family
- visual payoff category
- narrative closure type
- motif signature

## 6. What Must Be Detected

The engine should detect at least four repetition classes.

### 6.1 Semantic repetition

Examples:
- repeated "named room/door removed from floorplan"
- repeated "sealed room non-existent" closure
- repeated "warning points to impossible location" closure

### 6.2 Structural repetition

Examples:
- same hook -> escalating setup -> documentary/map payoff shape
- same timing of reveal logic
- same narrative resolution pattern

### 6.3 Visual repetition

Examples:
- repeated `map_blueprint` payoff family
- repeated `warning_display` payoff family
- repeated `sealed_access` payoff family
- same visual evidence family appearing too often within a rolling window

### 6.4 Strategic repetition

Examples:
- `variation_policy = low` persisting through all recent winners
- same content mode and same aggression profile leading to homogeneous output

## 7. Minimum Data Model

The first version should stay compact.

### `NoveltyPressureProfile`

Recommended fields:
- `semantic_saturation_level`
- `visual_saturation_level`
- `structural_saturation_level`
- `dominant_repeated_patterns`
- `novelty_budget`
- `recommended_variation_pressure`
- `blocked_patterns`
- `preferred_alternative_families`
- `trace`

Possible enum levels:
- `none`
- `low`
- `medium`
- `high`

### `PatternSignature`

Recommended fields:
- `hook_family`
- `setup_family`
- `payoff_family`
- `payoff_structure`
- `visual_payoff_category`
- `semantic_closure_type`
- `motif_signature`

This should be derived from actual pipeline outputs, not authored manually.

## 8. Input Surface

The engine should consume only what is actually available or cheaply derivable.

### Required inputs

- recent approved execution outputs
- script plan
- asset plan
- strategy profile
- QC outcome

### Optional later inputs

- real retention / watch metrics
- publish performance
- account-specific fatigue windows

### First implementation rule

Do not wait for perfect metrics.
The system already has enough local signals to detect repetition in a controlled window.

## 9. First Decision Model

The initial decision model should be rule-based and deterministic.

### Step 1: Build signatures from recent approved videos

For each recent approved video, derive:
- semantic payoff signature
- visual payoff signature
- motif signature
- hook family
- structure family

### Step 2: Count repetition over a window

Recommended first windows:
- last 5 approved videos
- last 10 approved videos

### Step 3: Assign saturation levels

Examples:
- same payoff family appears 3 times in last 5 -> `visual_saturation = medium`
- same payoff closure type appears 3 times in last 5 -> `semantic_saturation = medium`
- same motif signature appears 2 times in last 5 -> `structural_saturation = medium`
- same pattern dominates 4 times in last 5 -> `high`

### Step 4: Emit bounded novelty pressure

Examples:
- `low saturation` -> no change
- `medium saturation` -> raise `variation_policy` from `low` to `medium`
- `high saturation` -> block specific repeated payoff family and require alternate family

### Step 5: Preserve safety clamp

Novelty must never override:
- account health constraints
- hard quality floors
- QC authority

## 10. Downstream Effects

The engine matters only if downstream behavior changes.

### 10.1 Strategy integration

First and most important:
- novelty pressure must alter Strategy output

Examples:
- raise `variation_policy`
- keep hook aggressiveness stable but rotate payoff family bias
- shift from one payoff closure family to another

### 10.2 Script integration

Script should respond to novelty pressure by avoiding repeated closure templates.

Examples:
- if `floorplan removal` pattern is saturated, do not use it again in the current window
- prefer alternate closure families:
  - timestamp contradiction
  - warning panel anomaly
  - archive discrepancy
  - intercom identity reveal

### 10.3 Asset integration

Asset should respond by avoiding repeated payoff evidence categories.

Examples:
- if `map_blueprint` saturated, prefer `warning_display` or `sealed_access`
- if `warning_display` saturated, prefer `intercom_recorder` or `document`

### 10.4 Editor integration

Editor is lower priority in the first novelty phase.
But later it can help by varying:
- payoff emphasis style
- transition emphasis profile
- caption landing behavior

## 11. Minimum Viable Scope

The first engine should be deliberately small.

It should do only this:
- detect repetition in recent approved videos
- identify dominant repeated payoff families and closure patterns
- emit bounded novelty pressure
- alter Strategy / Script / Asset behavior enough to reduce visible repetition

It should not initially do:
- performance optimization loops
- long-horizon reinforcement logic
- per-account adaptive novelty tuning
- complex experimentation policy

## 12. Recommended Implementation Path

### Phase A: Signature extraction

Create a builder that reads recent execution outputs and derives pattern signatures.

Suggested output artifact:
- `novelty_signatures.json`

### Phase B: Saturation scoring

Build deterministic scoring over recent signatures.

Suggested output artifact:
- `saturation_snapshot.json`

### Phase C: Novelty pressure output

Emit `NoveltyPressureProfile`.

Suggested output artifact:
- `novelty_pressure_profile.json`

### Phase D: Strategy hookup

Strategy v3 should consume novelty pressure and translate it into bounded policy changes.

### Phase E: Downstream enforcement

Script and Asset should obey the new variation pressure and blocked pattern list.

## 13. Validation Plan

The engine should not be approved by intuition alone.

### 13.1 Signature validation

Prove that repeated approved videos produce repeated signatures.

### 13.2 Saturation detection validation

Prove that a batch with repeated payoff families raises saturation level.

### 13.3 Novelty effect validation

Prove that once novelty pressure is raised:
- Strategy changes
- Script changes
- Asset changes

### 13.4 Quality preservation validation

Prove that novelty pressure does not collapse QC outcomes.

### 13.5 Batch validation

Run a controlled batch where the baseline system would repeat a winning pattern.
Confirm that the novelty-governed system diversifies while remaining publishable.

## 14. Operational Risks

### Risk 1: novelty for novelty's sake

If novelty pressure is too aggressive, quality can collapse.

Mitigation:
- low-cardinality novelty levels
- strict clamp
- QC remains authoritative

### Risk 2: false saturation detection

If signatures are too coarse, the engine may over-detect repetition.

Mitigation:
- use multiple repetition dimensions
- require repeated evidence before raising pressure

### Risk 3: hidden randomness

If novelty is implemented stochastically, auditability collapses.

Mitigation:
- deterministic signature extraction
- deterministic novelty pressure
- deterministic downstream routing

### Risk 4: downstream symbolic compliance

If Strategy changes but Script/Asset ignore it, the engine becomes decorative.

Mitigation:
- require measurable downstream effect in validation gate

## 15. Governance Position

The engine should not be baseline-governed immediately.

Correct maturity sequence:
1. prototype
2. prove repetition detection
3. prove bounded novelty effect
4. prove no major quality regression
5. then promote

Most honest status target for first release:
- `integrated novelty prototype`

Not yet:
- mature long-horizon growth governor

## 16. Success Criteria

The first version is successful only if:
- repeated payoff patterns are detected reliably
- novelty pressure changes Strategy output
- novelty pressure changes Script and/or Asset behavior
- visual and semantic diversity increase measurably across a batch
- QC approval rate does not materially collapse

If diversity increases but quality drops sharply:
- failure

If quality remains high but repetition remains obvious:
- failure

The engine succeeds only if it improves diversity without sacrificing baseline publishability.

## 17. Next Correct Move

The next correct move is:
- design and implement `SATURATION_NOVELTY_ENGINE_v1_0`
- keep it small, deterministic, and auditable
- integrate it into `Strategy v3`
- validate it with batch repetition tests, not isolated spot checks

This is now the correct frontier because the system has already crossed the earlier frontier:
- generating good videos reliably

The new frontier is:
- generating good videos repeatedly without perceptual fatigue

## 18. Final Principle

Do not optimize isolated videos anymore.

Optimize the behavior of the batch.

That is the level the system has now reached.


---

## Source: `docs/runtime/SATURATION_NOVELTY_ENGINE_v1_0_IMPLEMENTATION_PLAN.md`

# Saturation Novelty Engine v1.0 Implementation Plan

## 1. Executive Summary

The CortAI system has now reached a different class of bottleneck.

Earlier phases were about:
- getting agents operational
- getting agents causal
- getting QC authoritative
- raising baseline video quality

Those goals are now strong enough that the next failure mode is not poor generation.
The next failure mode is repeated generation.

Recent batch validation showed:
- videos can pass QC consistently
- payoff quality can now be materially strong
- pipeline behavior is stable under controlled batch execution
- repeated winning patterns begin to reappear too quickly

That means the next correct implementation target is not another isolated quality upgrade.
It is a controlled saturation and novelty layer.

v1.0 goal:
- detect repeated winning patterns in recent approved outputs
- emit bounded novelty pressure
- cause downstream diversification without destabilizing the pipeline

This phase must stay narrow.
It should not attempt to become a full creative optimizer.
It should only make repetition governable.

## 2. Problem Diagnosis

The current system does not fail because agents are weak.
It fails because successful structures become sticky.

Observed pattern:
- a strong payoff family is discovered
- the same payoff structure repeats
- the same visual payoff family repeats
- the same strategy posture repeats

Current missing capability:
- no explicit saturation detector
- no novelty budget
- no blocked-pattern list
- no rolling-window diversification pressure

This means the system is deterministic but not yet self-regulating against perceptual fatigue.

## 3. v1.0 Target State

The Saturation / Novelty Engine v1.0 should be:
- deterministic
- compact
- auditable
- batch-aware within a short rolling window
- strong enough to alter Strategy behavior
- strong enough to alter Script and Asset behavior

It should not yet be:
- long-horizon optimization
- full performance-aware policy
- adaptive account-level novelty intelligence
- experiment controller

Success condition:
- repeated patterns get detected
- novelty pressure becomes real
- diversification increases
- QC approval rate remains stable enough

## 4. System Shape

Recommended v1.0 shape:

1. signature extraction
2. saturation scoring
3. novelty pressure profile
4. Strategy integration
5. Script and Asset enforcement

Practical layering:
- new novelty service builds `NoveltyPressureProfile`
- Strategy consumes it and adjusts posture
- Script and Asset consume Strategy outputs plus blocked pattern hints

This keeps the engine conceptually distinct while still integrating through Strategy.

## 5. Minimal Contracts

### 5.1 `PatternSignature`

Recommended fields:
- `hook_family`
- `payoff_structure`
- `semantic_closure_type`
- `visual_payoff_category`
- `motif_signature`
- `strategy_variation_policy`
- `content_mode`

This object should be derived from actual execution outputs.

### 5.2 `NoveltyPressureProfile`

Recommended fields:
- `semantic_saturation_level`
- `visual_saturation_level`
- `structural_saturation_level`
- `dominant_repeated_patterns`
- `novelty_budget`
- `recommended_variation_policy`
- `blocked_payoff_structures`
- `blocked_visual_payoff_categories`
- `preferred_alternative_payoff_families`
- `trace`

Enum values should remain low-cardinality:
- `none`
- `low`
- `medium`
- `high`

### 5.3 Strategy integration contract

v1.0 should avoid contract explosion.

Recommended minimal Strategy evolution:
- add optional `novelty_pressure_profile` to `StrategyInput`
- add novelty-driven adjustments into `decision_trace`

Avoid adding many new public fields to `StrategyProfile`.
Instead:
- reuse `variation_policy`
- optionally add one narrow field only if strictly needed:
  - `blocked_payoff_family_hint`

Even that should be avoided unless downstream enforcement cannot work without it.

## 6. Input Surface

### Required inputs

The engine should consume recent approved execution outputs from local artifacts or execution history.

Minimum required fields from those outputs:
- `creative_pack.script_plan`
- `creative_pack.asset_plan`
- `creative_pack.strategy_profile`
- `video_qc.status`

Only approved videos should count toward saturation by default.

### Window policy

Recommended v1.0 windows:
- `rolling_last_5_approved`
- `rolling_last_10_approved`

The shorter window should drive immediate pressure.
The longer window should be used as supporting evidence.

### Non-goal for v1.0

Do not require live publish metrics.
Do not require external databases.
Do not block implementation waiting for richer telemetry.

## 7. Signature Extraction Plan

This is the first core pillar.

### 7.1 Semantic closure type

Derive a coarse semantic label from the script payoff.

Recommended first labels:
- `removed_from_floorplan`
- `missing_room_reference`
- `warning_panel_contradiction`
- `archival_discrepancy`
- `identity_reveal`
- `sealed_access_reveal`
- `other`

These should be deterministic rules, not model calls.

### 7.2 Visual payoff category

Derive directly from:
- `asset_plan.segments.payoff.category`

This is already available and operational.

### 7.3 Payoff structure

Derive a compact structure label from the script payoff.

Examples:
- `named_location_removed`
- `device_points_to_impossible_place`
- `record_names_impossible_identity`
- `sealed_access_physical_reveal`
- `documentary_proof_reveal`

### 7.4 Motif signature

Derive a compact sequence signature from current pipeline outputs.

Examples:
- hook family
- setup family
- payoff family

This should remain approximate but deterministic.

## 8. Saturation Scoring Plan

This is the second core pillar.

### 8.1 Scoring rules

Recommended initial rules:

- if same `visual_payoff_category` appears 3 times in last 5 approved videos:
  - `visual_saturation = medium`

- if same `semantic_closure_type` appears 3 times in last 5 approved videos:
  - `semantic_saturation = medium`

- if same `payoff_structure` appears 2 times in last 5 and 4 times in last 10:
  - `structural_saturation = high`

- if `variation_policy = low` dominates all last 5 winners:
  - increase novelty pressure by one band

### 8.2 Dominant repeated pattern list

The engine should explicitly list what is repeating.

Examples:
- `semantic_closure_type: removed_from_floorplan`
- `visual_payoff_category: map_blueprint`
- `payoff_structure: named_location_removed`

This is necessary for auditability and downstream blocking.

### 8.3 Novelty budget

Recommended initial mapping:
- no saturation -> `novelty_budget = low`
- medium saturation -> `novelty_budget = medium`
- high saturation -> `novelty_budget = high`

Novelty budget does not mean free creativity.
It means stronger pressure to avoid repeated families.

## 9. Strategy Integration Plan

This is the third core pillar.

Strategy should consume the novelty pressure profile after trend and learning are resolved.

### Proposed decision order in Strategy v3

1. base by `health_status`
2. apply `account_goal`
3. apply constraints
4. apply learning metrics
5. apply trend
6. apply novelty pressure
7. clamp
8. emit trace

### Novelty effects in Strategy

Recommended v1.0 effects:
- if novelty pressure is `medium` or above:
  - raise `variation_policy` from `low` to `medium`

- if visual saturation is `high`:
  - emit blocked visual payoff family hints

- if semantic saturation is `high`:
  - emit blocked payoff structure hints

Important:
- novelty must never override `HOLD`
- novelty must never reduce safety posture below constraints

## 10. Script Enforcement Plan

This is where novelty becomes real at narrative level.

### v1.0 Script behavior

Script should avoid recently repeated payoff structures when novelty pressure indicates saturation.

Recommended implementation:
- add optional blocked payoff structure hints to script generation context
- instruct generator and fallback repair layer to avoid those blocked structures

### Minimum deterministic effect

If `removed_from_floorplan` is blocked:
- fallback and repair should not produce:
  - `ROOM X REMOVED FROM THE FLOORPLAN`
  - `MISSING FROM THE MAP`

Instead prefer:
- `warning panel contradiction`
- `timestamp contradiction`
- `archival identity reveal`
- `recorded voice identity reveal`

### Important constraint

Do not redesign Script broadly.
Apply novelty only to the payoff closure family first.

## 11. Asset Enforcement Plan

This is where novelty becomes real at visual level.

### v1.0 Asset behavior

Asset should avoid repeated payoff evidence categories when novelty pressure indicates saturation.

Recommended implementation:
- if `map_blueprint` is blocked, do not allow payoff selection to land on `map_blueprint`
- if `warning_display` is blocked, reroute to allowed alternatives

### Preferred alternative families

Examples:
- if `map_blueprint` blocked -> prefer `warning_display`, `sealed_access`, `intercom_recorder`
- if `warning_display` blocked -> prefer `sealed_access`, `document`, `intercom_recorder`
- if `sealed_access` blocked -> prefer `map_blueprint`, `warning_display`, `document`

### Enforcement principle

Do not leave this as advisory only.
At least one blocked family must actually be excluded from payoff selection in v1.0.

## 12. File-Level Implementation Surface

### New files likely needed

- `backend/app/creative/agents/novelty/models.py`
- `backend/app/creative/agents/novelty/service.py`
- `backend/app/creative/agents/novelty/signatures.py`

### Existing files likely to change

- `backend/app/creative/agents/strategy/models.py`
- `backend/app/creative/agents/strategy/service.py`
- `backend/app/creative/orchestrator/service.py`
- `backend/app/content/script_gen/service.py`
- `backend/app/creative/agents/asset_selection/service.py`

### Files that should not be broadly rewritten

- `backend/app/creative/agents/voice/*`
- `backend/app/creative/agents/editor/*`
- QC runtime files

## 13. Migration Strategy

The rollout must stay conservative.

### Step 1

Implement novelty signature extraction as read-only.

### Step 2

Implement novelty pressure profile generation.

### Step 3

Pass novelty profile into Strategy as optional input.

### Step 4

Activate one narrow Script novelty effect.

### Step 5

Activate one narrow Asset novelty effect.

### Step 6

Validate that batch diversity rises without collapsing approval quality.

### Compatibility rule

If no novelty profile is present:
- behavior should remain equivalent to current baseline

## 14. Validation Plan

This subsystem must be validated with batches, not isolated examples.

### 14.1 Unit tests

Required:
- repeated signatures are extracted consistently
- saturation levels are assigned correctly
- novelty profile is deterministic

### 14.2 Strategy integration tests

Required:
- novelty pressure raises `variation_policy` when saturation is present
- novelty pressure does not override `HOLD`

### 14.3 Script causality tests

Required:
- blocked payoff structure prevents repeated closure family in fallback/repair
- same topic with blocked pattern yields different payoff family

### 14.4 Asset causality tests

Required:
- blocked visual payoff category prevents repeated payoff family selection
- same topic with blocked category yields alternate payoff family

### 14.5 Batch validation gate

Create:
- `SATURATION_NOVELTY_ENGINE_FULL_VALIDATION_GATE_v1_0`

Expected artifacts:
- `OUT/audit/saturation_novelty_engine_validation/block_summary.json`
- `OUT/audit/saturation_novelty_engine_validation/final_verdict.json`
- `OUT/audit/saturation_novelty_engine_validation/decision_examples.json`
- `OUT/audit/saturation_novelty_engine_validation/execution_batch.json`
- `OUT/audit/saturation_novelty_engine_validation/metrics.json`

### 14.6 Success bar

The gate should prove:
- repeated patterns are detected
- novelty pressure becomes real
- Script changes when blocked pattern is present
- Asset changes when blocked category is present
- batch diversity improves
- QC approval rate does not materially collapse

## 15. Risks and Mitigations

### Risk 1: novelty pressure is detected but not enforced

Mitigation:
- require at least one real Script effect and one real Asset effect

### Risk 2: diversity rises but quality drops

Mitigation:
- keep novelty pressure low-cardinality
- preserve QC authority
- constrain alternatives to high-quality families only

### Risk 3: signatures are too crude and overblock useful patterns

Mitigation:
- start with payoff-only focus
- use short window
- require repeated evidence before blocking

### Risk 4: implementation spreads too broadly

Mitigation:
- limit v1.0 to payoff structure + payoff visual family
- keep Editor and Voice out of scope

## 16. Success Criteria

v1.0 is successful only if:
- repeated payoff structure is detectable
- repeated payoff visual category is detectable
- Strategy reacts to saturation
- Script stops reusing blocked payoff structures
- Asset stops reusing blocked payoff categories
- short-batch diversity increases measurably
- quality remains acceptable under QC

If the system still repeats the same payoff family across a short batch despite novelty pressure:
- v1.0 has failed

## 17. Non-Goals

This phase does not implement:
- full novelty optimization
- account-level adaptive fatigue tuning
- experiment controller integration
- Editor novelty governance
- Voice novelty governance
- long-horizon performance-aware strategic loops
- full baseline governance for novelty layer

## 18. Next Correct Move After v1.0

If v1.0 works, the next move is:
- widen novelty control beyond payoff
- connect deeper to Strategy v3
- add production monitoring over rolling approved batches

But not before v1.0 proves one thing clearly:
- the system can detect and reduce repetition without breaking publishability

## 19. Final Principle

Do not solve all creativity now.

Solve repetition first.

The correct v1.0 success condition is:
- repeated winning patterns are now visible to the system
- the system can selectively step away from them
- quality does not collapse when it does


---

## Source: `docs/runtime/script_agent_excellence_gate_v1_0.md`

# Script Agent Excellence Gate

Versao: 1.0
Status: Aprovado para execucao
Script: `backend/scripts/run_script_agent_excellence_gate.ps1`

## Objetivo
Executar um gate de excelencia especifico do `Script Agent` antes de liberar o proximo gargalo criativo da Fase 2.5.

O gate valida se o agente:

- usa contexto cognitivo real
- gera copy perceptivelmente melhor
- preserva a melhora ate o video final
- continua operacionalmente confiavel

## Escopo
O runner cobre:

- compilacao do `Script Agent` e adjacentes alterados
- testes unitarios do `Script Agent`
- regressao cognitiva minima com `Creative Orchestrator` e smokes dos blocos 1 a 4
- influencia real de `strategy_profile`, `trend_profile`, `learning_insights` e `experiment_plan`
- robustez do parsing estruturado
- cadeia de fallback `Gemini -> Ollama -> fallback deterministico`
- bateria de 20 roteiros para anti-cliche e diversidade
- lote de 5 videos reais para impacto perceptivel e estabilidade

## Evidencia gerada
O gate materializa evidencia em:

- `OUT/audit/script_agent_excellence_gate/`

Arquivos principais:

- `AUDIT_REPORT.md`
- `py_compile_script_agent.txt`
- `script_agent_unit_tests.txt`
- `script_agent_cognitive_regression.txt`
- `context_influence_audit.json`
- `structured_parsing_audit.json`
- `fallback_path_audit.json`
- `script_battery_20.json`
- `video_batch_5.json`

## Comando padrao

```powershell
./backend/scripts/run_script_agent_excellence_gate.ps1
```

## Modo de validacao rapida do runner

```powershell
./backend/scripts/run_script_agent_excellence_gate.ps1 -SkipScriptBattery -SkipVideoBatch
```

Esse modo nao fecha o gate de excelencia. Ele serve apenas para validar o runner e a materializacao de evidencia sem executar as baterias mais caras.

## Criterio de GO / NO-GO

- `GO` apenas se `FAILURES = 0`
- qualquer `FAIL` bloqueia a liberacao do proximo agente

Thresholds minimos embutidos no runner:

- contexto precisa alterar `4/4` variantes controladas
- parser estruturado precisa aceitar os `4` casos representativos
- fallback precisa fechar `Gemini -> Ollama` e `Ollama -> fallback deterministico`
- bateria de 20 roteiros:
  - `20` roteiros gerados
  - `distinct_hooks >= 16`
  - `distinct_modes >= 5`
  - `cliche_hits <= 3`
  - `weak_payoff_hits <= 2`
- lote de 5 videos:
  - `5` execucoes
  - pelo menos `4/5` com `pipeline_status = READY` e `video_qc_status = APPROVE`
  - `distinct_hooks >= 4`

## Interpretacao
Quando esse gate fecha limpo, o `Script Agent` deixa de estar apenas integrado e passa a estar validado como componente criativo liberavel.


---

## Source: `docs/runtime/SCRIPT_AGENT_PAYOFF_INTELLIGENCE_UPGRADE_PLAN.md`

# Script Agent Payoff Intelligence Upgrade Plan

## 1. Executive Summary

The current Script Agent is operational, integrated, and already capable of producing strong hooks and workable setups. The main product weakness now is not general script generation. It is payoff density.

Current observed state:
- hooks are often strong enough to secure early attention
- setups usually sustain tension adequately
- payoffs can still land as semantically weak, abstract, or insufficiently concrete
- the system prompt already asks for a concrete reveal, but the enforcement is weak
- current validation rejects only a narrow set of abstract payoff terms

This plan does not redesign the Script Agent.

It upgrades one specific layer:
- payoff intensity

Objective:
- move the Script Agent from "three-block generator with weak payoff enforcement" to "three-block generator with materially stronger payoff closure"

This is a product-quality upgrade, not a pipeline-governance upgrade.

## 2. Current State Diagnosis

Grounded in current implementation:

- `backend/app/creative/agents/script/service.py`
  - builds `ScriptGenerationContext`
  - calls structured generation
  - adapts hook/setup/payoff through `ScreenTextAdapterService`
  - falls back to deterministic contextual scripts on generation failure

- `backend/app/content/script_gen/service.py`
  - prompt already contains explicit payoff guidance:
    - concrete unsettling closure
    - specific enough to visualize instantly
    - observable reveal, not abstract mystery
  - `_validate_payload(...)` only enforces:
    - distinct blocks
    - block length bounds
    - anti-cliche phrases
    - a small weak-payoff term blacklist

What is implemented:
- payoff intent exists in prompt language
- weak payoff blacklist exists
- deterministic fallback payloads already tend to be more concrete than some live generations

What is missing:
- no explicit payoff scoring inside script generation
- no structured check for reveal concreteness
- no check that payoff resolves the promise introduced by hook/setup
- no distinction between:
  - interesting final line
  - strong final reveal
- no repair pass when payoff is weak but not invalid

Most honest label:
- payoff guidance exists
- payoff intelligence is still shallow

## 3. Product Problem To Solve

The failure mode is specific:

- hook creates a strong anomaly
- setup sustains tension
- payoff ends in a vague or low-impact reveal

Typical weak payoff patterns:
- abstract mystery statements
- weak semantic closure
- insufficiently visualizable ending
- conceptually interesting but emotionally flat final line
- reveal lacks concrete object, place, person, number, timestamp, warning, or observable anomaly

This is not a system reliability problem.
This is a closure-strength problem.

## 4. Target State

After this upgrade, the Script Agent should:

- produce payoffs that are more concrete by default
- reject or repair weak payoff closures before finalizing the script
- preserve current hook/setup strengths
- remain deterministic in fallback and validation behavior
- improve downstream product quality without requiring a redesign of Voice, Asset, Editor, or QC

This phase is successful if:
- weak abstract payoffs are meaningfully reduced
- stronger reveal-style payoffs become more common
- downstream QC HOLDs caused by weak payoff landing materially decrease in controlled validation

## 5. Scope

Allowed:
- strengthen prompt instructions for payoff construction
- add deterministic payoff validation heuristics
- add a narrow payoff repair layer
- improve fallback payload quality
- add unit/integration validation around payoff intensity

Out of scope:
- redesigning the Script Agent end to end
- changing Voice logic
- changing Editor logic
- changing QC thresholds
- adding a large narrative ontology
- introducing a new model orchestration layer

## 6. Root Cause In Current Code

The current code already says the right thing in the prompt, but does not enforce it strongly enough.

Current gap by layer:

### Prompt layer

Strength:
- already instructs concrete payoff closure

Weakness:
- instructions are advisory only
- there is no structured preference for:
  - room numbers
  - names
  - timestamps
  - documents
  - warnings
  - physical evidence
  - impossible system states

### Validation layer

Strength:
- blocks must be distinct
- cliches are partially filtered

Weakness:
- only a narrow blacklist of weak payoff terms is used
- a payoff can still be weak while avoiding blacklist words

### Recovery layer

Strength:
- deterministic fallback exists

Weakness:
- there is no intermediate repair path:
  - weak but parse-valid payoff goes through unchanged

## 7. Upgrade Strategy

The correct move is not "generate more creatively."

The correct move is:
- make payoff strength explicit
- make weakness detectable
- repair weak payoffs deterministically when possible

Recommended implementation order:

1. strengthen prompt constraints
2. add payoff-intensity validation
3. add deterministic payoff repair
4. strengthen fallback payloads
5. validate on controlled payoff cases

## 8. Prompt Upgrade Plan

File:
- `backend/app/content/script_gen/service.py`

Current prompt already asks for a concrete reveal.

vNext prompt should add stronger payoff-specific requirements:

- payoff must contain at least one concrete reveal anchor
- payoff should preferably name one of:
  - room number
  - name
  - timestamp
  - device
  - document
  - warning text
  - sealed place
  - impossible state
- payoff must convert mystery into visible evidence, not just continued vagueness

Recommended additions:

- "The payoff must reveal one concrete, observable fact."
- "Prefer a payoff containing a named room, number, date, warning, file, tape, key, voice, body, floor, station, or sealed location."
- "Do not end only on a broad eerie concept such as empty room, strange feeling, unanswered mystery, or unknown presence."
- "The payoff must make the viewer picture the final reveal instantly."

Important:
- keep this as prompt reinforcement, not the only defense

## 9. Payoff Validation Plan

File:
- `backend/app/content/script_gen/service.py`

Add a narrow deterministic payoff validator inside `_validate_payload(...)`.

### 9.1 New signal families

Recommended heuristic checks:

- concrete evidence presence
- specificity strength
- visualizability strength
- closure strength

### 9.2 Concrete evidence heuristic

Reward or require payoff presence of at least one concrete anchor type:

- number or room marker
- proper-name-like token
- device/object evidence
- place evidence
- timestamp/date evidence
- explicit system anomaly

Examples of acceptable anchors:
- `ROOM 312`
- `03:14`
- `WARNING PANEL`
- `TAPE`
- `LOCK`
- `BADGE`
- `ELEVATOR`
- `ARCHIVE`
- `DOOR`
- `INTERCOM`

### 9.3 Weak payoff patterns to penalize

Expand beyond current blacklist.

New weak-pattern examples:
- "empty room" with no stronger qualifier
- "something answered"
- "nobody understood why"
- "it was never explained"
- "someone was there"
- "something was waiting"
- "the room was wrong"

Important:
- do not overfit to phrase-level only
- use pattern families, not brittle exact strings

### 9.4 Closure-strength rule

The payoff should:
- resolve the promise introduced by hook/setup
- add a final concrete escalation or reveal

Reject or repair if the payoff:
- merely restates tension
- remains purely atmospheric
- ends without evidence

## 10. Payoff Repair Layer Plan

This is the highest-value addition.

When payload is parse-valid but payoff is weak:
- do not immediately accept it
- run a deterministic payoff repair step

### 10.1 Repair input

Use:
- topic
- hook
- setup
- payoff
- narrative mode
- niche

### 10.2 Repair objective

Transform weak payoff into:
- more concrete
- more visual
- more final

without changing overall premise

### 10.3 Repair method

Minimum-change deterministic approach:

- build a candidate payoff from the topic and existing anomaly
- preserve emotional tone
- inject one stronger reveal anchor

Examples:

Weak:
- `The caller whispered the number of an empty room.`

Stronger repaired variants:
- `The caller whispered Room 312, sealed since 1997.`
- `The caller named Room 312, a room removed from the floorplan.`
- `The last whisper matched a room listed as non-existent.`

### 10.4 Repair safety rule

If repair cannot confidently produce a stronger payoff:
- fall back to deterministic contextual payload

## 11. Fallback Payload Upgrade Plan

File:
- `backend/app/content/script_gen/service.py`

Current fallback payloads are often already better than weak live payoffs.
Still, they can be tightened further.

Upgrade rule:
- every fallback payoff should contain a concrete reveal anchor

Preferred patterns:
- room number
- date
- sealed object
- impossible physical condition
- named file/tape/witness

This matters because fallback quality defines the floor.

## 12. Contract Surface

No major contract expansion is needed.

Keep:
- `ScriptPlan`
- `StructuredScriptPayload`
- `ScriptGenerationResponse`

Optional narrow addition:
- internal payoff validation trace in `raw_output`-side diagnostics or provider trace

Recommendation:
- avoid adding new public Script contracts in this phase

## 13. File-Level Implementation Surface

Required:
- `backend/app/content/script_gen/service.py`
  - prompt strengthening
  - weak-payoff detection
  - payoff repair step
  - stronger fallback payloads

Likely touched:
- `backend/app/creative/agents/script/service.py`
  - only if a post-generation payoff-repair hook is cleaner at agent layer

Tests:
- `tests/agents/script/test_script_agent_phase2_unittest.py`
- likely add:
  - `tests/test_script_payoff_intensity_unittest.py`
  - or extend existing script generation tests

Optional validation scripts:
- dedicated payoff audit runner in `tests/run_*.py`

## 14. Migration Strategy

This upgrade should be introduced safely:

1. strengthen validation and repair behind deterministic logic
2. preserve current behavior when payoff is already strong
3. only intervene on weak payoffs
4. keep public output contracts unchanged

Backward compatibility requirement:
- existing consumers of `ScriptPlan` must not break

## 15. Validation Plan

### 15.1 Unit tests

Add tests proving:

- strong payoff passes unchanged
- weak payoff is rejected or repaired
- repair is deterministic
- fallback payoff is concrete
- abstract endings are filtered more reliably

Required case families:

- strong_hook + strong_setup + weak_payoff
- strong_hook + strong_setup + concrete_payoff
- generic eerie payoff
- specific room/number payoff
- specific document/tape/date payoff

### 15.2 Integration tests

Add integration checks proving:

- repaired payoff reaches `ScriptPlan`
- downstream `Asset` gets more concrete payoff material
- same input produces same repaired payoff

### 15.3 Product validation

Create a focused gate:

- `SCRIPT_AGENT_PAYOFF_INTELLIGENCE_VALIDATION_GATE`

Expected artifacts:
- `OUT/audit/script_agent_payoff_intelligence_validation/block_summary.json`
- `OUT/audit/script_agent_payoff_intelligence_validation/final_verdict.json`
- `OUT/audit/script_agent_payoff_intelligence_validation/payoff_examples.json`
- `OUT/audit/script_agent_payoff_intelligence_validation/execution_batch.json`
- `OUT/audit/script_agent_payoff_intelligence_validation/metrics.json`

### 15.4 Success signals

The gate should show:

- fewer weak abstract payoffs
- stronger concrete reveal frequency
- improved payoff examples on controlled cases
- no regression in hook/setup quality

## 16. Success Criteria

This upgrade is successful if:

1. weak abstract payoffs are caught more reliably
2. weak payoffs are repaired or replaced deterministically
3. concrete reveal anchors become materially more common
4. current hook strength does not regress
5. downstream inputs become more visually actionable
6. no contract breakage occurs

## 17. Risks And Mitigations

### Risk 1: Overcorrection into formulaic payoffs

Mitigation:
- use a small set of anchor families
- do not force the same payoff template everywhere

### Risk 2: Validator becomes too brittle

Mitigation:
- use coarse heuristics
- combine weak-pattern detection with positive evidence checks

### Risk 3: Repair changes premise too aggressively

Mitigation:
- constrain repair to preserve original anomaly and topic
- prefer minimal semantic lift, not rewrite

### Risk 4: Hooks or setups degrade because prompt becomes too payoff-heavy

Mitigation:
- add payoff instructions without weakening hook/setup instructions
- validate all three blocks in regression tests

## 18. Next Correct Move After This Upgrade

If this payoff upgrade works, the next correct move is:

- strengthen `Asset` payoff evidence selection to mirror the stronger reveal

After that:
- re-run end-to-end QC product checks
- only then consider a dedicated pre-QC payoff scoring layer

The order matters:

1. fix generation quality first
2. then fix reveal visualization
3. then decide whether extra scoring is still needed

## 19. Final Implementation Principle

Do not solve this with more abstract narrative language.

Solve it by making the payoff:
- more concrete
- more visual
- more final

The success condition is simple:

- the last line should land harder
- and the system should do that consistently


---

## Source: `docs/runtime/STRATEGY_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`

# Strategy Agent Evolution v2.0 Implementation Plan

## 1. Executive Summary

The current Strategy Agent is real, integrated, and partially influential, but it is still too shallow to be considered a true strategic layer. Its main failure is not absence of structure. Its main failure is absence of causal effect.

Current Phase 1 state:
- Strategy runs in runtime
- Strategy emits a real `StrategyProfile`
- downstream agents receive that profile
- Script and Voice consume parts of it
- Asset and Editor currently do not use it behaviorally

Current insufficiency:
- `recent_metrics_summary` is passed in and ignored
- `recommended_constraints` is passed in and ignored
- `TrendProfile` is not passed into Strategy at all
- `variation_policy` exists but governs nothing meaningful
- Strategy is still mostly a deterministic profile assembler keyed by health status

v2.0 goal:
- move Strategy from integrated prototype to causal strategy layer

This phase is intentionally narrow.

It will not:
- redesign the entire Strategy Agent
- add a large strategic ontology
- introduce complex experiment governance
- introduce dynamic baseline or long-horizon governance

It will:
- activate real inputs already present
- add explicit trend input
- make the decision model materially context-conditioned
- make at least one downstream visual subsystem obey strategy behaviorally

Most accurate target state:
- Strategy v2.0 remains simple
- but stops being mostly decorative

## 2. Current State Diagnosis

Grounded in current implementation:

- `StrategyAgentService.generate(...)` exists and runs
- `StrategyInput` currently includes:
  - `account_id`
  - `account_goal`
  - `recent_metrics_summary`
  - `health_status`
  - `recommended_constraints`
- `StrategyResult` returns:
  - `strategy_profile`
  - `fallback`
- orchestrator stores Strategy output into:
  - `CreativePack.strategy_profile`
  - `CreativePipelineExecution.strategy`

Current decision behavior:
- mainly maps `health_status` to a small fixed profile
- does not read `recent_metrics_summary`
- does not read `recommended_constraints`
- does not consume `TrendProfile`

Current downstream reality:
- Script uses several strategy fields via prompt context
- Voice uses some strategy fields directly
- Asset does not use strategy behaviorally
- Editor does not use strategy behaviorally

Current maturity gap:
- the Strategy layer exists
- but it does not yet mediate upstream context into downstream behavior strongly enough to justify the word "strategy"

## 3. Target State of Strategy v2.0

Strategy v2.0 should be the minimum viable causal strategy layer.

It should still be:
- deterministic
- compact
- low-risk to migrate

But it must become:
- context-conditioned by more than health status
- behaviorally relevant downstream
- auditable in terms of why it produced a given profile

Target state:
- `recent_metrics_summary` materially affects at least one strategy field
- `recommended_constraints` materially affects at least one strategy field
- `TrendProfile` becomes a direct Strategy input
- `variation_policy` becomes operational downstream
- at least one strong downstream effect exists in Asset or Editor
- Strategy output can be explained in a simple decision trace

What v2.0 still will not be:
- a sophisticated strategic optimizer
- a batch-aware governor
- an experimentation brain
- a full policy engine

## 4. Responsibility Boundary

### Strategy v2.0 will do

- interpret account health into strategy posture
- interpret trend context into strategy posture
- interpret recent learning summary into limited strategic adjustments
- interpret recommended constraints into limited strategic adjustments
- produce a `StrategyProfile` whose fields affect downstream behavior
- explain, at minimum, which inputs drove the profile

### Strategy v2.0 will not do

- rewrite script text itself
- choose the TTS provider
- select concrete assets itself
- render or edit video itself
- perform QC
- perform publish gating
- run corrective loops
- choose experiments in a complex system

### Boundary principle

Strategy remains a governor of behavior, not an executor of content generation.

## 5. Input Activation Plan

This is the first core pillar of v2.0.

### 5.1 `recent_metrics_summary`

Current state:
- present in `StrategyInput`
- ignored

v2.0 plan:
- activate a small, deterministic parser for a known subset of metrics signals

Minimum signals Strategy should read:
- retention weakness or strength
- hook weakness or strength
- repetition fatigue or saturation hint
- recent quality consistency signal

This does not require a new contract if the summary is already a dict.

Recommended implementation rule:
- Strategy should read only a small whitelist of keys, not arbitrary dict contents

Example effects:
- weak retention -> raise `hook_aggressiveness` one step
- repetition fatigue -> increase `variation_policy`
- unstable recent quality -> move `content_mode` toward `conservative`

Minimum safe principle:
- if a metric key is absent, Strategy must fall back cleanly
- no hidden stochastic interpretation

### 5.2 `recommended_constraints`

Current state:
- present in `StrategyInput`
- ignored

v2.0 plan:
- activate a small ruleset that maps constraint hints to strategic posture

Recommended minimum constraints to honor:
- reduce aggressiveness
- prefer safer pacing/duration
- avoid high variation
- keep conservative generation posture

Example effects:
- `{"reduce_aggressiveness": true}` -> lower `hook_aggressiveness`
- `{"prefer_shorter_duration": true}` -> move `target_duration_range` toward `8-10s`
- `{"low_variation_only": true}` -> cap `variation_policy` at `low`

Important:
- Strategy should not interpret arbitrary free-form constraints
- v2.0 should use a small supported constraint vocabulary

### 5.3 `TrendProfile`

Current state:
- not passed into Strategy
- trend context reaches downstream agents directly in parallel

v2.0 plan:
- extend `StrategyInput` to include `trend_profile: TrendProfile | None`
- pass the already-resolved `TrendProfile` from orchestrator into Strategy

Reason:
- Strategy cannot be strategic if trend posture bypasses it

Minimum trend fields Strategy should read:
- dominant hooks
- pacing
- visual style

Example effects:
- fast first 3 seconds trend pacing -> slightly higher `hook_aggressiveness`
- calmer visual style -> lower variation pressure
- trend hook family indicating question/opening/shock -> adjust hook posture

Important:
- Trend should not override account health
- health/risk posture remains higher priority

## 6. Decision Model Plan

Strategy v2.0 should remain rule-based, but no longer shallow.

### Proposed decision order

1. start from a base profile driven by `health_status`
2. apply `account_goal`
3. apply `recommended_constraints`
4. apply `recent_metrics_summary`
5. apply `trend_profile`
6. clamp final values to supported enums/ranges
7. emit a simple `decision_trace`

### Base profile layer

This remains similar to Phase 1:

`SAFE`
- `content_mode = "standard"`
- `hook_aggressiveness = "medium"`
- `target_duration_range = "8-12s"`
- `variation_policy = "low"`

`CAUTION`
- `content_mode = "conservative"`
- `hook_aggressiveness = "medium"`
- `target_duration_range = "8-12s"`
- `variation_policy = "low"`

`HOLD`
- `content_mode = "paused"`
- `hook_aggressiveness = "low"`
- `target_duration_range = "8-12s"`
- `variation_policy = "none"`

### Causal adjustment layer

Then Strategy should adjust the base profile.

Recommended minimal adjustment rules:

- if recent retention is weak and health is not `HOLD`:
  - increase `hook_aggressiveness`

- if repetition/saturation signal is present and health is `SAFE`:
  - increase `variation_policy`

- if recent quality consistency is weak:
  - force `content_mode = "conservative"`

- if constraints request lower risk:
  - lower aggressiveness
  - cap variation
  - prefer shorter duration

- if trend pacing is fast and constraints do not oppose:
  - prefer stronger hook posture

### Output values should remain low-cardinality

Recommended enum-like values for v2.0:

`hook_aggressiveness`
- `low`
- `medium`
- `high`

`target_duration_range`
- `8-10s`
- `8-12s`
- `10-14s`

`variation_policy`
- `none`
- `low`
- `medium`

`content_mode`
- `paused`
- `conservative`
- `standard`

The goal is to activate behavior, not create a high-dimensional policy space.

## 7. Contract Evolution Plan

This phase should evolve contracts minimally.

### `StrategyInput`

Current:
- no trend input

Required change:
- add `trend_profile: TrendProfile | None = None`

Optional addition:
- no other new fields should be added unless strictly necessary

### `StrategyProfile`

Current fields:
- already sufficient for v2.0

Recommendation:
- do not add many new fields now
- keep the contract compact

Optional narrow addition:
- only if needed for traceability, add a field like `strategy_version`
- this is optional, not required for v2.0

### `StrategyResult`

Current:
- `strategy_profile`
- `fallback`

Recommended evolution:
- add a lightweight `decision_trace: dict[str, Any]`

This trace should include:
- base profile source
- metric adjustments applied
- constraint adjustments applied
- trend adjustments applied

This is the smallest high-value explainability addition.

## 8. Downstream Enforcement Plan

This is the second core pillar of v2.0.

The Strategy Agent only becomes causal if downstream agents materially obey it.

### 8.1 Script

Current:
- Script prompt already includes several strategy fields

v2.0 plan:
- keep Script consumption as-is
- do not redesign Script Agent

Why:
- Script already has partial real consumption
- this phase should spend causal budget where Strategy is still symbolic

### 8.2 Voice

Current:
- Voice already consumes `content_mode` and `target_duration_range`

v2.0 plan:
- keep current consumption
- optionally tighten mapping so new duration ranges and conservative modes remain meaningful

This is optional support work, not the core of v2.0.

### 8.3 Asset

Current:
- Strategy is passed in structurally and ignored behaviorally

v2.0 preferred plan:
- make `variation_policy` influence asset selection behavior

Recommended minimum behavioral effects:
- `variation_policy = "none"`:
  - minimize novelty/variation pressure
  - keep safer/more literal asset selection

- `variation_policy = "low"`:
  - current baseline behavior

- `variation_policy = "medium"`:
  - stronger anti-repetition behavior in selection
  - stronger effort to differentiate hook/setup/payoff families
  - stronger hook-first diversity bias

This should be implemented in the existing selection/interpreter layer, not via major redesign.

Recommended concrete implementation points:
- `backend/app/creative/agents/asset_selection/service.py`
- `backend/app/creative/agents/asset/interpreter.py`

Goal:
- prove Strategy can alter visual behavior, not just text/voice hints

### 8.4 Editor

Current:
- Strategy is passed in and ignored

v2.0 optional or secondary plan:
- make `variation_policy` and/or `content_mode` affect edit intensity

Possible minimal effects:
- conservative mode -> less aggressive caption emphasis / motion
- medium variation -> more differentiated hook/setup/payoff treatment

If one strong effect can already be achieved in Asset, Editor changes can remain smaller in v2.0.

Priority rule:
- Asset or Editor must gain at least one strong behavioral effect
- both are desirable, but one is the minimum

## 9. File-Level Implementation Surface

### Required changes

- `backend/app/creative/agents/strategy/models.py`
  - add `trend_profile` to `StrategyInput`
  - optionally add `decision_trace` to `StrategyResult`

- `backend/app/creative/agents/strategy/service.py`
  - activate metrics input
  - activate constraints input
  - consume trend input
  - implement decision trace

- `backend/app/creative/orchestrator/service.py`
  - pass `TrendProfile` into `StrategyInput`

- `backend/app/creative/agents/asset_selection/service.py`
  - add real strategy-conditioned behavior

### Likely changes

- `backend/app/creative/agents/asset/interpreter.py`
  - if visual planning needs variation-policy awareness

### Optional minimal changes

- `backend/app/creative/agents/editor/interpreter.py`
  - only if a small strategy-conditioned edit behavior is added

- `backend/app/creative/contracts/creative_pack.py`
  - only if a tiny contract extension is truly needed

### Files that should not be broadly rewritten

- `backend/app/creative/agents/script/service.py`
- `backend/app/creative/agents/voice/service.py`
- large pipeline orchestration files unrelated to Strategy input passing

## 10. Migration Strategy

v2.0 must preserve current stability.

### Step 1

Extend `StrategyInput` with optional `trend_profile`.

Why safe:
- optional field
- backward-compatible with current construction paths if any exist outside orchestrator

### Step 2

Implement Strategy rules so absent metrics/constraints/trend still produce Phase 1-like output.

Why safe:
- default behavior remains stable when new signals are missing

### Step 3

Introduce downstream behavior for `variation_policy` in Asset first.

Why safe:
- Asset is already modular
- it is the highest-value place to prove causal strategy

### Step 4

Optionally add a small Editor effect only after Asset effect is stable.

### Backward compatibility requirements

- `StrategyProfile` must remain serializable in the same places
- `CreativePack` consumers must continue to work
- Script/Voice current behavior must not regress when no new input signals exist

## 11. Validation Plan

This is the third core pillar of v2.0.

The goal is to prove Strategy stopped being decorative.

### 11.1 Unit tests for Strategy decision logic

Required new tests:
- metrics summary changes profile
- recommended constraints change profile
- trend profile changes profile
- health still dominates when risk is high
- absent inputs preserve baseline-like output

Examples:
- weak retention signal -> `hook_aggressiveness` rises
- repetition signal -> `variation_policy` rises
- low-risk constraint -> aggressiveness capped
- fast trend pacing -> hook posture increases unless constrained

### 11.2 Integration tests for downstream causal effect

Required:
- Strategy output alters asset behavior in a deterministic way

Minimum proof:
- same topic/script with different `variation_policy` produces measurably different asset-plan behavior

Acceptable evidence:
- different category bias
- different selection strictness
- different hook differentiation path

Optional additional proof:
- Strategy alters editor behavior in a measurable and deterministic way

### 11.3 Orchestrator integration tests

Required:
- orchestrator passes `TrendProfile` into Strategy
- `CreativePipelineExecution.strategy` contains the updated result
- `CreativePack.strategy_profile` still propagates correctly

### 11.4 Explainability tests

Required if `decision_trace` is added:
- trace includes which signal families changed the output
- trace serializes without breaking execution output

### 11.5 Heavy validation gate

Create:
- `STRATEGY_AGENT_EVOLUTION_v2_0_VALIDATION_GATE`

Expected artifacts:
- `OUT/audit/strategy_agent_evolution_v2_0_validation/block_summary.json`
- `OUT/audit/strategy_agent_evolution_v2_0_validation/final_verdict.json`
- `OUT/audit/strategy_agent_evolution_v2_0_validation/decision_examples.json`
- `OUT/audit/strategy_agent_evolution_v2_0_validation/execution_batch.json`
- `OUT/audit/strategy_agent_evolution_v2_0_validation/metrics.json`

### Validation success bar

The gate must prove:
- Strategy now uses metrics
- Strategy now uses constraints
- Strategy now uses trend input
- `variation_policy` changes at least one downstream behavior
- Strategy remains deterministic
- no major regression in safe baseline flows

## 12. Success Criteria

v2.0 is successful only if all of the following are true:

1. `recent_metrics_summary` is no longer inert
2. `recommended_constraints` are no longer inert
3. `TrendProfile` is a real Strategy input
4. `variation_policy` is no longer symbolic
5. Strategy has at least one strong behavioral effect in Asset or Editor
6. Script and Voice current partial consumption remain intact
7. Strategy remains deterministic
8. the pipeline remains backward-compatible

If Strategy still produces a profile that mostly behaves the same regardless of metrics, constraints, and trend:
- v2.0 has failed

## 13. Non-Goals / Out of Scope

This phase will not implement:

- large new strategic schemas
- full experiment controller logic
- dynamic baseline or adaptive governance
- saturation intelligence across batches
- novelty ranking
- top-performer comparison
- production calibration loops
- deep rework of Script, Voice, Asset, or Editor architectures
- full Strategy baseline governance

The phase is intentionally constrained to causal activation.

## 14. Risks and Mitigations

### Risk 1: Strategy remains cosmetically richer but still causally weak

Mitigation:
- require downstream behavioral proof, not just new profile values

### Risk 2: Strategy becomes too brittle from over-reading noisy metrics

Mitigation:
- use a small whitelist of metric keys
- use coarse rule bands, not fragile numeric optimization

### Risk 3: Trend overwhelms health/risk posture

Mitigation:
- health remains highest-priority base layer
- trend only adjusts within allowed bounds

### Risk 4: Downstream changes cause regression in stable asset/editor behavior

Mitigation:
- keep Strategy-conditioned behavior low-cardinality
- preserve baseline behavior for `variation_policy = low`

### Risk 5: Explainability is still too weak to debug

Mitigation:
- add `decision_trace`
- keep it small and explicit

## 15. Next Correct Move After v2.0

If v2.0 succeeds, the next correct move is not more field growth.

The next correct move after v2.0 is:
- validate Strategy as a first-class subsystem
- then expand toward stronger strategic governance

Likely next phase:
- richer saturation control
- experiment-aware strategy
- stronger Editor/Asset coordination
- baseline governance and promotion

But only after v2.0 proves causal effect first.

## 16. Final Implementation Principle

Do not make Strategy broader first.

Make Strategy causal first.

The success condition for v2.0 is not:
- "more strategic language in the contract"

The success condition is:
- "existing strategic fields and inputs now change real downstream behavior in a deterministic and auditable way"


---

## Source: `docs/runtime/TREND_ANALYSIS_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`

# TREND_ANALYSIS_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN

## 1. Objective

The objective of `Trend Analysis Agent v2.0` is to evolve the current subsystem from:
- manual niche profile loader

into:
- evidence-driven TikTok-native trend subsystem

The v2.0 goal is not to build a perfect trend intelligence platform.
The v2.0 goal is to introduce the minimum real architecture necessary for Trend to become:
- evidence-backed
- time-aware
- provenance-aware
- validation-aware
- operationally useful
- governable

Target outcome for v2.0:
- Trend stops being just a static context file loader
- Trend becomes a runtime subsystem that assembles a `TrendProfile` from explicit evidence sources
- downstream agents continue to consume Trend causally, with strongest effect concentrated in `Strategy` and `Asset`
- the subsystem remains conservative, deterministic, and auditable

## 2. Current State

Current state in Phase 1:
- Trend loads a niche JSON file from disk
- returns `TrendProfile`
- falls back to a safe default when file loading fails
- is integrated into orchestrator runtime
- has real downstream effect in `Strategy` and `Asset`
- has no provenance, freshness, confidence, temporal memory, or dedicated gate

Current classification:
- `implemented`
- `runtime-real`
- `deterministic`
- `prototype-grade`
- `not baseline-ready`

v2.0 exists to fix the right deficits:
- evidence absence
- provenance absence
- freshness absence
- validation absence
- governance absence

v2.0 does not exist to solve every strategic intelligence problem in one iteration.

## 3. Boundary

This boundary is mandatory and must remain explicit in implementation.

### 3.1 Trend
Trend owns:
- what is happening outside
- external platform trend evidence
- niche-level trend context
- freshness and provenance of trend evidence
- temporal snapshots of trend state

Trend does not own:
- internal performance optimization
- repetition or saturation control
- final runtime directional policy
- publishability governance

### 3.2 Learning
Learning owns:
- what works for us
- internal performance evidence
- QC-linked optimization feedback
- pattern learning from our executions

Learning does not own:
- external platform trend collection
- trend freshness policy
- trend provenance governance

### 3.3 Strategy
Strategy owns:
- what to do with available context
- how to translate Health + Trend + Learning + Novelty into runtime direction

Strategy does not own:
- collecting trend evidence
- validating evidence provenance
- storing trend history snapshots

### 3.4 Novelty
Novelty owns:
- repetition control
- saturation pressure
- anti-pattern blocking

Novelty does not own:
- external trend discovery

### 3.5 Hard boundary rule
The implementation must preserve this separation:
- `Trend = external trend context`
- `Learning = internal performance truth`
- `Strategy = control layer`

Trend v2.0 must not absorb Learning, Novelty, or Strategy responsibilities.

## 4. v2.0 Scope

v2.0 is intentionally minimal and causal.

Included in scope:
- evidence source activation
- provenance fields
- confidence fields
- freshness fields
- evidence references
- validation rules
- fallback hierarchy
- temporal snapshot storage
- stronger but still conservative downstream integration
- Trend gate design and execution path

Excluded from scope:
- full autonomous trend scraping across arbitrary TikTok surfaces
- advanced ML pattern detection
- account-specific Trend models
- multi-region production rollout
- overly sophisticated confidence heuristics
- deep downstream hard enforcement in all agents

## 5. Evidence Sources

Trend v2.0 must move to explicit evidence sources.

### 5.1 Primary source: TikTok Creative Center
Status in v2.0:
- primary planned external source
- should be implemented first

Role:
- provide baseline external trend evidence
- provide platform-level trend priors by niche/category and region

Expected outputs from source adapter:
- trending hashtags
- trending sounds
- top trend categories
- category-specific directional hints
- collection metadata

Constraints:
- v2.0 should remain conservative
- collection may be scheduled, not real-time
- if automated collection is not yet available in the first code slice, the source contract must still be formalized and the collector stub must be implemented explicitly

### 5.2 Secondary source: manual curation
Status in v2.0:
- complement, not replacement

Role:
- provide structured human-curated evidence for niche nuance
- support cases where Creative Center is too broad

Expected usage:
- hand-authored evidence records, not anonymous opinion
- each curated record must carry provenance

### 5.3 Tertiary source: internal metrics
Status in v2.0:
- validation/complement source
- not a replacement for external trend evidence

Role:
- refine or reweight trend context using internal performance evidence
- must remain clearly distinguished from Learning ownership

Rule:
- Trend may consume summarized internal validation signals
- Learning remains the owner of internal performance analysis logic

### 5.4 Source policy
Initial v2.0 source policy:
- primary: `creative_center`
- secondary: `manual_curation`
- tertiary: `internal_metrics_validation`

If only one source is available:
- Trend may still operate
- confidence must reflect reduced certainty
- provenance must remain explicit

## 6. Contract Evolution

Trend v2.0 needs contract hardening.

### 6.1 `TrendProfile` v2.0 target fields
Current fields to retain:
- `niche`
- `dominant_hooks`
- `avg_duration`
- `pacing`
- `visual_style`
- `text_style`

New fields to add:
- `region: str = "US"`
- `trend_source: str`
- `confidence_scores: dict[str, float]`
- `updated_at: str`
- `valid_until: str`
- `sample_size: int`
- `evidence: list[dict[str, Any]]`
- `trend_version: str`
- `collector_version: str`

Optional v2.0 fields if implemented immediately without bloat:
- `source_mix: list[str]`
- `overall_confidence: float`

Fields that must not be added unless there is immediate runtime use:
- extra symbolic style fields
- weakly defined qualitative labels with no consumer

### 6.2 `TrendEvidenceReference`
A dedicated evidence record structure should be introduced.

Minimum fields:
- `evidence_type`
- `source`
- `reference_id`
- `reference_url`
- `captured_at`
- `region`
- `metadata`

### 6.3 `TrendAnalysisInput` v2.0
Current input is too small.

Minimum v2.0 additions:
- `niche`
- `account_id` optional
- `region`
- `allow_cached`
- `force_refresh`
- `current_time` optional for testing determinism

Important:
- topic does not need to become a first-class Trend input in v2.0 unless a concrete use case is implemented
- avoid widening the input surface without evidence-backed behavior

### 6.4 `TrendAnalysisResult` v2.0
Must contain at least:
- `trend_profile`
- `fallback`
- `validation_summary`
- `collector_trace`

### 6.5 CreativePack persistence
`CreativePack` should continue to embed full `trend_profile`.

Additionally, v2.0 should consider embedding:
- `trend_validation_summary` or equivalent if needed for audit visibility

## 7. Data Layout

v2.0 should formalize storage instead of relying on ad hoc files only.

Proposed layout:
- `backend/data/trends/current/<niche>.json`
- `backend/data/trends/history/<niche>/<timestamp>.json`
- `backend/data/trends/manual_curation/<niche>.json`
- `backend/data/trends/cache/<source>/<niche>.json`

Audit layout:
- `OUT/audit/trend_analysis/trend_snapshots/`
- `OUT/audit/trend_analysis/trend_shifts/`
- `OUT/audit/trend_analysis/validation_reports/`
- `OUT/audit/trend_analysis/gate_decisions/`
- `OUT/audit/trend_analysis/performance_tracking/`

Key operational point:
- the current default path problem must be fixed in v2.0
- Trend must have a canonical repository-resident data layout, even if population remains initially manual or semi-automated

## 8. Freshness Policy

Trend v2.0 must treat trends as expiring context.

### 8.1 Freshness windows
Initial policy:
- `creative_center`: 7 days
- `manual_curation`: 14 days
- `internal_metrics_validation`: 30 days

### 8.2 Refresh rules
Refresh required when:
- trend is stale
- trend is within 2 days of expiry
- overall confidence is below threshold
- explicit `force_refresh` is requested

### 8.3 Expiry behavior
If refresh fails:
1. try latest valid cached trend
2. try previous acceptable snapshot
3. fallback to safe default trend

### 8.4 Freshness implementation requirement
Freshness must be explicit in code, not implied.

At minimum:
- `updated_at`
- `valid_until`
- validator check against time window

## 9. Confidence Policy

Confidence is required in v2.0, but it must start simple.

### 9.1 Confidence model for v2.0
Use simple, transparent factors only:
- source quality
- sample size
- freshness
- internal agreement if available

### 9.2 Confidence granularity
Required:
- per-field confidence for key fields
- overall confidence

Minimum field set:
- `dominant_hooks`
- `avg_duration`
- `pacing`
- `visual_style`
- `text_style` only if it gains a real consumer

### 9.3 Non-goal
Do not implement opaque or pseudo-intelligent scoring too early.

Wrong v2.0 behavior:
- complex confidence math no one can explain
- hidden heuristics without provenance

Correct v2.0 behavior:
- simple scoring
- explicit rules
- auditable mapping from source quality and sample size to confidence

## 10. Validation Policy

Trend v2.0 needs validation before application.

### 10.1 Validation checks
At minimum:
- freshness check
- provenance presence
- evidence presence
- sample size floor
- confidence floor
- internal consistency check

### 10.2 Validation outputs
Validation should yield:
- `valid: bool`
- `warnings: list[str]`
- `errors: list[str]`
- `overall_confidence`

### 10.3 Acceptance rules
Suggested v2.0 policy:
- `APPROVE` when all critical checks pass
- `HOLD` when non-critical issues exist but trend is still potentially usable
- `REJECT` when provenance, evidence, or confidence fail critically

### 10.4 Critical failures
Critical failures should include:
- missing provenance
- no evidence
- stale beyond acceptable fallback window
- confidence materially below minimum

## 11. Fallback Hierarchy

Trend v2.0 must degrade gracefully.

Required fallback order:
1. current validated trend
2. latest cached validated trend
3. previous historical validated trend within fallback age threshold
4. safe default trend

Fallback must remain observable via:
- result payload
- event emission
- audit artifact

Safe default trend requirements:
- deterministic
- niche-safe when possible
- minimally conservative
- explicit fallback reason

## 12. Downstream Enforcement Strategy

Trend v2.0 should strengthen consumption selectively.

### 12.1 Strategy
This is the primary downstream target.

v2.0 should preserve and strengthen:
- hook family conditioning from `dominant_hooks`
- pacing conditioning
- duration conditioning if `avg_duration` becomes operationally trusted

Trend should remain advisory input into Strategy, not a controller that bypasses Strategy.

### 12.2 Asset
This is the second primary downstream target.

v2.0 should preserve and strengthen:
- `visual_style`
- `pacing`
- style-dependent tag generation
- motion/effects bias

### 12.3 Script
Script may continue consuming Trend more lightly in v2.0.

Rule:
- keep prompt-context influence
- do not harden into many direct branching rules unless real evidence justifies it

### 12.4 Editor
Editor may continue consuming Trend lightly in v2.0.

Rule:
- keep light stylistic conditioning
- only strengthen if there is a concrete product-level case

### 12.5 Voice
No Trend-specific hardening is required in v2.0.

## 13. Non-Goals

Trend v2.0 must explicitly avoid these mistakes:
- becoming a mega agent
- absorbing Learning responsibilities
- absorbing Novelty responsibilities
- absorbing Strategy responsibilities
- turning confidence into an opaque scoring machine
- introducing too many symbolic fields without consumers
- trying to solve full account-specific personalization immediately
- trying to reach perfection before becoming evidence-real

This is a minimum viable causal evolution, not a maximal system rewrite.

## 14. Temporal Memory

Temporal awareness should begin in v2.0 at a conservative level.

Minimum implementation:
- store trend snapshots over time
- compare latest trend to previous trend
- detect significant changes in:
  - `dominant_hooks`
  - `pacing`
  - `visual_style`
  - `avg_duration`

Output:
- `TrendShiftAnalysis`
- stored audit artifact when meaningful shift is detected

Important:
- full advanced temporal strategy adaptation is not required in initial v2.0
- but trend history storage is required so the subsystem stops being stateless

## 15. Observability

Trend v2.0 must become auditable.

### 15.1 Required runtime visibility
It must be possible to answer:
- where the trend came from
- when it was updated
- how fresh it is
- how confident it is
- which evidence supports it
- whether fallback was used

### 15.2 Required event surface
Proposed events:
- `CREATIVE/trend_collection_started`
- `CREATIVE/trend_collection_completed`
- `CREATIVE/trend_validation_approved`
- `CREATIVE/trend_validation_hold`
- `CREATIVE/trend_validation_rejected`
- `CREATIVE/trend_profile_loaded`
- `CREATIVE/trend_profile_fallback`
- `CREATIVE/trend_shift_detected`

### 15.3 Audit artifacts
Required audit artifacts for gate and certification work:
- trend snapshot files
- validation reports
- gate decision reports
- shift reports

## 16. TikTok-Native Design Rules

Trend v2.0 must remain TikTok-first.

Implications:
- evidence sources should be TikTok-specific, not generic social abstractions
- duration assumptions should remain short-form oriented
- hook, pacing, visual style, text style, sound, and format cues should be considered in TikTok-native framing
- region should be explicit because TikTok trend surfaces vary by market

Important caution:
- TikTok-native does not mean TikTok-overfit everywhere in v2.0 contract design
- it means source model and behavioral priorities must be aligned with TikTok reality

## 17. Implementation Phases

## 17.1 Phase A: Contract And Storage Hardening

Objective:
- make Trend structurally capable of evidence, provenance, freshness, and fallback hierarchy

Work:
- extend Trend contracts
- add evidence reference structure
- formalize canonical storage directories
- add temporal snapshot persistence
- fix default path issue

Deliverable:
- contracts compile
- serialization works
- backward-safe fallback path exists

## 17.2 Phase B: Evidence Source Activation

Objective:
- stop relying on manual niche loader as the sole meaningful source

Work:
- introduce Creative Center collector interface
- introduce manual curation input format
- introduce source assembly logic
- produce first hybridizable `TrendProfile`

Deliverable:
- TrendProfile can be built from explicit evidence payloads
- provenance fields are populated

## 17.3 Phase C: Validation And Fallback Governance

Objective:
- prevent low-quality trend data from silently entering runtime

Work:
- validation service
- confidence scoring service
- fallback hierarchy
- trend decision traces

Deliverable:
- validated trend output path
- reject/hold/approve semantics

## 17.4 Phase D: Downstream Hardening

Objective:
- make v2.0 causally stronger where it matters most

Work:
- strengthen `Strategy` use of validated trend data
- strengthen `Asset` use of validated trend data
- keep `Script` and `Editor` conservative unless justified

Deliverable:
- measurable downstream causal effect

## 17.5 Phase E: Gate And Promotion Readiness

Objective:
- make Trend baseline-eligible

Work:
- Trend Excellence Gate runner
- audit artifact generation
- promotion policy definition

Deliverable:
- standalone Trend validation path

## 18. Validation Path

Trend v2.0 requires its own gate path.

### 18.1 Required validation layers
- unit tests for collectors, validator, freshness, fallback
- integration tests for orchestrator + Trend + Strategy + Asset
- audit runner for Trend Excellence Gate
- controlled execution batch proving downstream influence remains coherent

### 18.2 What Trend gate must prove
- provenance is present
- freshness works
- confidence is computed and usable
- fallback hierarchy works
- downstream causal use exists
- deterministic behavior holds under same evidence input
- invalid trend evidence does not silently contaminate runtime

### 18.3 Baseline criteria
Trend v2.0 should only be baseline-promoted if:
- evidence-backed path is operational
- default path issue is resolved
- validation and fallback hierarchy work
- Strategy and Asset causal consumption are proven under v2.0 context
- audit artifacts are generated consistently

## 19. Success Criteria

Trend v2.0 should be considered successful if it achieves all of the following:
- no longer depends on manual niche file loading as sole meaningful mechanism
- emits a provenance-aware `TrendProfile`
- tracks freshness and expiry
- validates trend evidence before application
- preserves graceful degradation
- strengthens real downstream influence without absorbing other subsystems
- becomes gateable

Success does not require:
- perfect trend intelligence
- full automation across all sources
- advanced ML inference
- account-specific per-user adaptation

## 20. Risks

### Risk 1: Trend grows into a mega layer
Mitigation:
- enforce boundary rule explicitly in plan and code review

### Risk 2: confidence becomes opaque
Mitigation:
- keep initial confidence scoring simple and explicit

### Risk 3: Creative Center becomes single point of truth
Mitigation:
- maintain multi-source design from the start

### Risk 4: symbolic field inflation
Mitigation:
- require real consumer before keeping new fields like `text_style`

### Risk 5: runtime regression from source failures
Mitigation:
- implement fallback hierarchy before making Trend source logic mandatory

## 21. Next Correct Move After This Plan

After this implementation plan is written, the next correct move is:
- implement `Phase A: Contract And Storage Hardening`

Reason:
- the current blocker is structural, not sophistication
- Trend cannot become evidence-governed until contracts and storage are made real
- source activation without contract hardening would create fragile and ungoverned behavior

## Final Implementation Position

Trend v2.0 should be built as:
- minimal
- evidence-backed
- TikTok-native
- provenance-aware
- freshness-aware
- validation-aware
- conservative
- auditable

It should not be built as:
- all-knowing strategic brain
- replacement for Learning
- replacement for Strategy
- high-complexity scoring system in its first real evolution

Final one-line target:
- `Trend Analysis Agent v2.0` must turn Trend from a static file-backed context block into a governed evidence-driven TikTok trend subsystem without breaking system boundaries.


---

## Source: `docs/runtime/TREND_ANALYSIS_AGENT_GATE_EVENT_ARTIFACT_FREEZE_v1_0.md`

# Trend Analysis Agent Gate Event And Artifact Freeze v1.0

## Objective
Freeze the minimum event and artifact surface used by:
- `Trend Excellence Gate`
- post-gate monitoring
- promotion review

This freeze exists to prevent observability drift during the short monitoring window between:
- `GO_WITH_MONITORING`
- formal baseline promotion

## Scope
Frozen in this version:
- Trend-related orchestrator events
- Trend gate artifact file set
- monitoring artifact file set

Not frozen in this version:
- internal collector implementation details
- confidence formula internals
- downstream business logic outside emitted fields

## Frozen Trend Events
The following event types are frozen for the monitoring window:
- `CREATIVE/trend_profile_loaded`
- `CREATIVE/trend_profile_fallback`
- `CREATIVE/trend_collection_completed`
- `CREATIVE/trend_collection_failed`
- `CREATIVE/trend_validation_approved`
- `CREATIVE/trend_validation_hold`
- `CREATIVE/trend_validation_rejected`
- `CREATIVE/strategy_profile_generated`
- `CREATIVE/asset_selection_generated`

## Required Event Fields
### `CREATIVE/trend_profile_loaded`
Required details:
- `account_id`
- `niche`
- `fallback_used`
- `trend_source`
- `source_mix`
- `validation_status`
- `overall_confidence`
- `freshness_state`
- `pacing`
- `visual_style`

### `CREATIVE/trend_profile_fallback`
Required details:
- `account_id`
- `niche`
- `fallback_used`
- `fallback_reason`
- `fallback_path`
- `trend_source`
- `source_mix`
- `validation_status`
- `overall_confidence`
- `freshness_state`
- `pacing`
- `visual_style`

### `CREATIVE/trend_collection_completed`
Required details:
- `account_id`
- `niche`
- `source`
- `collector_version`
- `status`
- `region_requested`
- `region_effective`
- `region_filter_applied`
- `hashtags_count`
- `songs_count`
- `error`

### `CREATIVE/trend_collection_failed`
Required details:
- same contract as `CREATIVE/trend_collection_completed`

### `CREATIVE/trend_validation_approved`
### `CREATIVE/trend_validation_hold`
### `CREATIVE/trend_validation_rejected`
Required details:
- `account_id`
- `niche`
- `status`
- `trend_source`
- `source_mix`
- `overall_confidence`
- `freshness_state`
- `warnings`
- `errors`
- `fallback_path`
- `collector_version`
- `trend_version`

### `CREATIVE/strategy_profile_generated`
Required details:
- `account_id`
- `goal`
- `content_mode`
- `hook_aggressiveness`
- `target_duration_range`
- `variation_policy`
- `health_status`
- `fallback_used`

### `CREATIVE/asset_selection_generated`
Required details:
- `account_id`
- `hook_asset`
- `setup_asset`
- `payoff_asset`
- `visual_style`
- `visual_anchor`
- `semantic_pattern`
- `fallback_used`

## Frozen Gate Artifact Set
The Trend gate artifact set is frozen as:
- `OUT/audit/trend_analysis_full_validation_gate/block_summary.json`
- `OUT/audit/trend_analysis_full_validation_gate/final_verdict.json`
- `OUT/audit/trend_analysis_full_validation_gate/decision_examples.json`
- `OUT/audit/trend_analysis_full_validation_gate/execution_batch.json`
- `OUT/audit/trend_analysis_full_validation_gate/metrics.json`
- `OUT/audit/trend_analysis_full_validation_gate/human_review.json`
- `OUT/audit/trend_analysis_full_validation_gate/event_summary.json`

## Frozen Monitoring Artifact Set
The post-gate monitoring artifact set is frozen as:
- `OUT/audit/trend_analysis_post_gate_monitoring/monitoring_summary.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/rolling_metrics.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/regression_alerts.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/human_review.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/execution_examples.json`

## Change Rule During Monitoring
During the short monitoring window:
- do not rename these event types
- do not remove required fields
- do not rename artifact files
- do not weaken fallback visibility

Allowed changes:
- additive non-breaking fields
- internal collector fixes
- parser robustness fixes
- operational threshold tuning outside the frozen event keys

## Reason For Freeze
The Trend gate concluded `GO_WITH_MONITORING`, not unconditional promotion.

That means the subsystem is technically approved, but observability must remain stable long enough to answer:
- is Creative Center collection operationally stable
- is validation behavior stable
- is fallback pressure acceptable
- do `Strategy` and `Asset` continue to respond causally

The monitoring window should evaluate subsystem stability, not event schema churn.


---

## Source: `docs/runtime/TREND_ANALYSIS_AGENT_MANUAL_CURATION_CANONICAL_FORMAT_v1_0.md`

# TREND_ANALYSIS_AGENT_MANUAL_CURATION_CANONICAL_FORMAT_v1_0

## Objective

This document defines the canonical `manual_curation` input format for `Trend Analysis Agent v2.0`.

This format exists to provide:
- structured human-curated trend evidence
- explicit provenance
- freshness metadata
- evidence references compatible with Trend validation and fallback governance

This is not a legacy profile file format.
This is the governed manual evidence format that feeds Trend source assembly in Phase B and Phase C.

## Storage Location

Canonical location:
- `backend/data/trends/manual_curation/<niche>.json`

Examples:
- `backend/data/trends/manual_curation/horror.json`
- `backend/data/trends/manual_curation/true_crime.json`

## Required Fields

Minimum required fields:
- `niche`
- `region`
- `source`
- `collected_at`
- `sample_size`
- `dominant_hooks`
- `avg_duration`
- `pacing`
- `visual_style`
- `evidence`
- `source_metadata`

## Optional Fields

Optional but allowed:
- `text_style`
- `updated_at`
- `valid_until`
- `trend_version`
- `collector_version`

Important:
- `text_style` remains weakly consumed downstream and should not be inflated with unnecessary complexity.
- `valid_until` may be present for documentation, but the current source-record assembly path derives freshness primarily from `collected_at` and source freshness policy.

## Canonical JSON Shape

```json
{
  "niche": "horror",
  "region": "US",
  "source": "manual_curation",
  "collected_at": "2026-04-03T00:00:00Z",
  "updated_at": "2026-04-03T00:00:00Z",
  "valid_until": "2026-04-17T00:00:00Z",
  "sample_size": 8,
  "dominant_hooks": ["story_opening", "ominous_question"],
  "avg_duration": "8-12s",
  "pacing": "fast_first_3s",
  "visual_style": "dark_backgrounds",
  "text_style": "large_caption_focus",
  "evidence": [
    {
      "evidence_type": "manual_top_video",
      "source": "manual_curation",
      "reference_id": "horror_seed_001",
      "reference_url": "https://example.com/horror_seed_001",
      "captured_at": "2026-04-03T00:00:00Z",
      "region": "US",
      "metadata": {
        "rank": 1,
        "notes": "Fast cold-open with high-contrast captions."
      }
    }
  ],
  "source_metadata": {
    "curation_method": "human_structured_review",
    "curator_id": "trend_seed_v1",
    "sample_window": "last_14_days",
    "record_version": "manual-curation-v1"
  },
  "trend_version": "2.0",
  "collector_version": "manual-curation-v1"
}
```

## Rules

### Provenance

`source` must be:
- `manual_curation`

Each `evidence` item must include:
- `evidence_type`
- `source`
- `reference_id`

Recommended:
- `reference_url`
- `captured_at`
- `metadata.rank`

### Freshness

Manual curation is governed by the 14-day freshness window currently defined in Trend v2.0.

Operational implication:
- stale manual curation should not be treated as primary approved evidence
- stale manual curation may only survive through explicit fallback paths if separately validated

### Sample Size

`sample_size` should reflect the number of manually reviewed items contributing to the summary.

Rule of thumb:
- `< 3` is weak
- `3-5` may degrade to `HOLD`
- `>= 6` is preferred for stable manual seeds

### Hook Ordering

`dominant_hooks` should be ordered from strongest to weakest manual signal.

The current Trend assembly path preserves ordering significance and combines it with source priority.

### Niche Discipline

Each file must be niche-specific.

Do not mix:
- `horror`
- `true_crime`
- `facts`
- `history`
- `conspiracy`

inside the same record.

## Non-Goals

This format is not intended to:
- replace Creative Center
- replace Learning
- encode downstream strategy directly
- become an ungoverned opinion dump

## Current Status

This format is operational in the current Trend runtime as a source-record input for:
- source assembly
- confidence assembly
- validation
- fallback hierarchy

It is the correct interim evidence path before Creative Center real collection is activated.


---

## Source: `docs/runtime/TREND_ANALYSIS_AGENT_POST_GATE_MONITORING_PLAN_v1_0.md`

# Trend Analysis Agent Post-Gate Monitoring Plan v1.0

## Objective
Run a short monitoring window after the Trend gate verdict:
- `GO_WITH_MONITORING`

This monitoring window exists to confirm:
- operational stability under continued use
- collector resilience on the public Creative Center surface
- validation and fallback stability
- continued causal effect into `Strategy` and `Asset`

This plan does not reopen Trend architecture.

## Scope
Included:
- Trend collection stability
- validation status stability
- fallback hierarchy pressure
- event and artifact continuity
- downstream causal proxies in `Strategy` and `Asset`

Excluded:
- redesign of Trend contracts
- Learning redesign
- Novelty redesign
- Strategy redesign
- new confidence model
- baseline promotion itself

## Monitoring Window
Recommended minimum:
- `7 days` or `20 executions`, whichever comes later

Recommended preferred window:
- `7 days` and `30 executions`

Reason:
- the gate already proved technical validity
- this window is only for stability confirmation

## Frozen Inputs
Run monitoring against the frozen surface defined in:
- `docs/runtime/TREND_ANALYSIS_AGENT_GATE_EVENT_ARTIFACT_FREEZE_v1_0.md`

Do not change event names, required fields, or artifact names during this window unless a critical incident forces it.

## Primary Metrics
Track:
- `creative_center_rate`
- `collection_completed_rate`
- `collection_failed_rate`
- `validation_status_distribution`
- `safe_default_fallback_rate`
- `strategy_fast_pacing_alignment_rate`
- `asset_visual_alignment_rate`
- `qc_approve_rate`

## Interpretation
### `creative_center_rate`
Shows how often Trend actually runs with external Creative Center-backed context instead of living only on fallback paths.

### `collection_failed_rate`
Shows operational stability of the public Creative Center collector.

### `safe_default_fallback_rate`
Shows whether Trend is collapsing too often to the lowest fallback tier.

### `strategy_fast_pacing_alignment_rate`
Proxy for continued Trend-to-Strategy causality:
- when Trend says `fast_first_3s`
- Strategy should usually reflect a stronger hook posture

### `asset_visual_alignment_rate`
Proxy for continued Trend-to-Asset causality:
- Asset visual style should continue to match Trend visual style in normal runs

## Reopen Triggers
Reopen only on material signals:
- `collection_failed_rate > 0.35`
- `safe_default_fallback_rate > 0.10`
- any `TREND_VALIDATION_REJECT_OBSERVED`
- `strategy_fast_pacing_alignment_rate < 0.80`
- `asset_visual_alignment_rate < 0.80`
- Creative Center stops being the dominant source unexpectedly

## Monitoring Runner
Use:

```powershell
python tests/gates/agents/trend_analysis/run_trend_analysis_agent_post_gate_monitoring.py
```

Output artifacts:
- `OUT/audit/trend_analysis_post_gate_monitoring/monitoring_summary.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/rolling_metrics.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/regression_alerts.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/human_review.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/execution_examples.json`

## Promotion Standard After Monitoring
Promote Trend to baseline only if all remain true through the short monitoring window:
- Creative Center-backed execution remains operational
- validation stays governed
- fallback hierarchy stays safe
- no material new failure pattern appears
- Strategy causal response remains visible
- Asset causal response remains visible
- public-surface limitations remain explicit, not hidden

## Final Rule
If stable:
- promote

If unstable:
- open a narrow corrective slice only

Do not reopen Trend broadly unless monitoring shows a real failure class.


---

## Source: `docs/runtime/voice_agent_excellence_gate_v1_0.md`

# Voice Agent Excellence Gate

Versao: 1.0
Status: Aprovado para execucao
Script: `backend/scripts/run_voice_agent_excellence_gate.ps1`

## Objetivo
Medir a qualidade real do subsistema de voz apos a correcao estrutural da `Phase 2.5A`.

O gate valida:

- obediencia arquitetural a `VoicePlan`
- rastreabilidade de provider requisitado e executado
- contraste narrativo entre `hook/setup/payoff`
- distribuicao de pausas
- monotonia perceptiva por proxies deterministicas
- latencia e fallback operacional
- comportamento em bateria textual e em lote minimo de videos

## Pre-requisitos

- `Phase 2.5A` concluida e estruturalmente validada
- `Voice Interpreter` presente
- `TTS Router` presente
- `Piper` funcional

## Evidencia gerada

- `OUT/audit/voice_agent_excellence_gate/AUDIT_REPORT.md`
- `OUT/audit/voice_agent_excellence_gate/voice_battery_25.json`
- `OUT/audit/voice_agent_excellence_gate/video_batch_5.json`
- `OUT/audit/voice_agent_excellence_gate/fallback_trace.json`
- `OUT/audit/voice_agent_excellence_gate/delivery_profile_summary.json`
- `OUT/audit/voice_agent_excellence_gate/latency_summary.json`
- `OUT/audit/voice_agent_excellence_gate/segment_pause_analysis.json`
- `OUT/audit/voice_agent_excellence_gate/monotony_proxy_analysis.json`

## Bateria minima

- 25 casos textuais:
  - 5 horror
  - 5 true crime
  - 5 investigative
  - 5 curiosity
  - 5 dark storytelling
- 5 videos completos
- 1 bateria forcada de fallback

## Criterio de GO / NO-GO

O gate retorna `GO` apenas se:

- `VoicePlan` continuar obedecido
- provider traceability estiver materializada
- fallback permanecer explicito
- `Piper` continuar funcional
- a bateria textual permanecer estavel
- o lote de video continuar operacional
- proxies de contraste/pausa/monotonia passarem thresholds minimos

## Interpretacao

`GO` significa que o subsistema de voz esta:

- arquiteturalmente coerente
- perceptivelmente melhor que o baseline simbolico anterior
- operacionalmente auditavel

`NO-GO` significa que a voz ainda nao e componente forte do produto.
