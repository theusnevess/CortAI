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
