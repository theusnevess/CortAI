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
