# EXPERIMENT_CAPABILITY_SYSTEM_BIBLE_PHASE1

## 1. Executive Summary

The `Experiment Capability` in the current CortAI codebase is real, implemented, and integrated into the orchestrator.
It is not fake.
It is not only a document-level concept.
It does run in the runtime path.

But it is also not yet a real experimental control subsystem in the full operational sense.

What is true today:
- it generates an `ExperimentPlan`
- it injects that plan into `CreativePack`
- it emits experiment events in the orchestrator
- it can influence script generation through `experiment_plan`
- its variant selection is deterministic

What is also true today:
- the default runtime path falls back to `exp_default`
- the default config path does not exist in the current repo
- the service does not persist a real assignment through `ExperimentService.assign(...)`
- the service does not record experiment results in runtime
- the runtime default does not persist `experiment_plan.json` either, because `default_output_path` is `None`
- only a narrow part of the pipeline consumes experiment output behaviorally

Current classification:
- runtime-real: yes
- structurally integrated: yes
- causally meaningful: weakly, and mostly through Script
- experimentally authoritative: no
- audit-closed as a subsystem: no
- fallback/default dominant in current frozen runtime: yes
- maturity level: integrated experimental scaffold, not an operational experiment governor

Direct answers:
- Is Experiment Capability real in runtime today? Yes.
- Is it integrated into the orchestrator? Yes.
- Does it affect behavior? Yes, but narrowly.
- Is the current production-like runtime exercising real controlled experiments? Mostly no.
- Is it operating as a closed-loop experiment system? No.

## 2. Current Mission Of The Subsystem

Conceptually, Experiment Capability should do four things:
- decide whether an execution is experiment-eligible
- assign control vs variant
- define the experiment type and safe envelope
- make that assignment auditable and comparable over time

What it actually does today:
- load a local experiment config if one exists
- create or resolve a deterministic experiment identity
- resolve deterministic variant payload `A` or `B`
- build an `ExperimentPlan`
- pass that plan downstream

What it does not actually do today:
- it does not decide eligibility from live policy
- it does not own rollout policy
- it does not persist true runtime assignment records through the framework
- it does not record results in the creative runtime
- it does not select winners
- it does not update learning or strategy policy
- it does not enforce a safe experiment envelope beyond whatever is encoded in variant payload

Most precise description:
- today it is a deterministic experiment-context emitter
not:
- a full experiment operating system

## 3. Responsibility Boundary

Correct boundary:

```json
{
  "experiment_capability": {
    "owns": [
      "experiment eligibility",
      "control_vs_variant assignment",
      "experiment type selection",
      "safe experiment envelope"
    ],
    "does_not_own": [
      "strategy policy",
      "learning policy",
      "trend collection",
      "qc governance",
      "content generation directly"
    ]
  }
}
```

Actual ownership in code today:
- generate an `ExperimentPlan`
- choose deterministic `variant_id`
- carry `variant_params`
- expose fallback/default experiment state

Actual non-ownership in code today:
- no direct ownership of strategy policy
- no direct ownership of learning policy
- no direct ownership of trend interpretation
- no QC authority
- no direct generation authority
- no automatic winner promotion

Important honesty point:
- the current subsystem does not yet own a real persisted assignment lifecycle, even though the broader experiment framework exists elsewhere in the repo

## 4. Architectural Position In The Pipeline

The current runtime order in the orchestrator is:

1. Account Health
2. Trend Analysis
3. Learning
4. Novelty
5. Strategy
6. Experiment Capability
7. Script
8. Voice
9. Asset
10. Editor
11. Render
12. QC

This ordering is real in:
- `backend/app/creative/orchestrator/service.py`

That means the subsystem is:
- upstream of content generation
- downstream of Strategy
- structurally able to condition generation

But there is an important architectural truth:
- it runs after Strategy, so it is not defining strategic policy
- it runs before Script, so it can still shape realization

That is the correct boundary for this subsystem.

## 5. End-To-End Flow

Actual runtime flow today:

1. Orchestrator resolves upstream context.
2. `ExperimentCapabilityService.generate(...)` is called.
3. It tries to read `config_path` or `default_config_path`.
4. If config exists:
- create or resolve deterministic experiment identity through `ExperimentService.create_experiment(...)`
- compute deterministic variant payload through `resolve_variant_payload(...)`
- build `ExperimentPlan`

5. If config does not exist or an exception occurs:
- return fallback plan:
  - `experiment_id = "exp_default"`
  - `variant_id = "A"`
  - `variant_type = "baseline"`
  - `variant_params = {}`
  - `fallback_used = true`

6. Orchestrator emits:
- `CREATIVE/experiment_plan_generated`
or:
- `CREATIVE/experiment_plan_fallback`

7. Orchestrator passes `experiment_plan` into:
- Script Agent
- `CreativePack`
- execution result

8. Orchestrator synthesizes a lightweight `experiment_assignment` inside `CreativePack` with:
- `experiment_id`
- `variant_id`

Important limitations:
- the service does not call `ExperimentService.assign(...)`
- the service does not call `ExperimentService.record_result(...)`
- the assignment embedded in `CreativePack` is not a real assignment entity from the framework
- it contains no `assignment_id`
- it contains no `subject_key`
- it is not persisted through the framework as a runtime assignment record

This is the sharpest distinction in the current implementation.

## 6. Contracts And Data Structures

### `ExperimentCapabilityInput`

Location:
- `backend/app/creative/experiments/models.py`

Fields:
- `account_id`
- `niche`
- `topic`
- `publish_slot`
- `learning_insights`
- optional `config_path`
- optional `output_path`

Operational meaning:
- enough context exists to support richer experiment decisions later
- but most of this context is not used meaningfully today

What is actually used today:
- `account_id`
- `topic`
- `publish_slot`
- optional config path

What is not materially used today:
- `niche`
- `learning_insights`

### `ExperimentPlan`

Location:
- `backend/app/creative/contracts/creative_pack.py`

Fields:
- `experiment_id`
- `variant_id`
- `variant_type`
- `variant_params`
- `fallback_used`

Operational status:
- serializable: yes
- propagated in runtime: yes
- behaviorally consumed: partially
- sufficient as a minimal experiment context contract: yes
- sufficient as a full assignment contract: no

### `ExperimentAssignment`

Location:
- `backend/app/creative/contracts/creative_pack.py`

Fields:
- `experiment_id`
- `variant_id`

Critical honesty point:
- this is not the same as the framework-level `ExperimentAssignment`
- it omits `assignment_id`
- it omits `subject_key`
- it omits `assigned_at`

So the `CreativePack` assignment object is a thin annotation, not a full framework artifact.

### `ExperimentCapabilityResult`

Location:
- `backend/app/creative/experiments/models.py`

Fields:
- `experiment_plan`
- `fallback`

Operational status:
- real
- serializable
- visible in runtime result
- sufficient for context emission
- insufficient for closed-loop experiment governance

## 7. Current Decision Model

The current decision model is:
- deterministic
- config-driven
- binary A/B
- payload-emitting
- not policy-rich

Actual logic in `backend/app/creative/experiments/service.py`:

1. try to load experiment config
2. if config missing:
- emit fallback experiment

3. if config exists:
- create experiment identity from name + scope
- resolve `A` or `B` deterministically from `account_id|publish_slot|topic`
- return payload from `variant_a` or `variant_b`

What it does not do:
- no eligibility filter
- no holdout window policy
- no traffic allocation other than deterministic 50/50 A/B
- no per-account throttling
- no guardrails based on health, QC, or novelty
- no learning-conditioned experimental risk envelope

Most accurate label:
- deterministic variant resolver with fallback

## 8. Input Surface

What it consumes in theory:
- account identity
- topic
- niche
- publish slot
- learning insights
- config path

What it actually consumes meaningfully:
- config file presence
- config payload
- subject key built from `account_id|publish_slot|topic`

What it does not consume meaningfully today:
- account health
- strategy output
- learning policy
- pattern findings
- trend profile
- novelty pressure
- QC history
- prior experiment results

This matters because the subsystem is named like an experimental controller, but the current implementation does not yet reason over the system state that would justify controlled experimentation.

## 9. Output Surface

The subsystem emits:
- `ExperimentPlan`
- fallback metadata
- orchestrator events

Actual outputs with strong runtime meaning:

### `variant_id`
- deterministic: yes
- runtime-visible: yes
- consumed by Script Generator: yes
- broader causal power: weak

### `variant_params`
- deterministic given config and subject key: yes
- runtime-visible: yes
- consumed by Script Generator: yes
- broader causal power: weak

### `fallback_used`
- runtime-visible: yes
- used for audit/event visibility: yes
- broader causal power: indirect only

Important operational truth:
- the current system emits experiment structure reliably
- but that structure is only weakly behavior-changing today

## 10. Downstream Consumption

### Script

This is the strongest real consumer.

Files:
- `backend/app/creative/agents/script/service.py`
- `backend/app/content/script_gen/service.py`

Real effects:
- `experiment_plan` is passed into `ScriptGenerationContext`
- prompt includes:
  - `Experiment variant`
  - `Experiment payload`
- `variant_params.narrative_mode` can force narrative mode directly
- if no forced narrative mode exists, `variant_id` still participates in deterministic mode selection

This means:
- Experiment Capability is not purely decorative
- it does have real behavioral influence on script generation

But the influence is still narrow:
- it mainly affects narrative mode / prompt context
- it does not own script policy

### Voice

No direct behavioral consumption found.

### Asset

No direct behavioral consumption found.

### Editor

No direct behavioral consumption found.

### QC

No direct behavioral consumption found.

### Attribution / analysis

There is downstream experiment-aware analysis in:
- `backend/app/attribution/service.py`

But that analysis is not part of the main creative runtime loop.
It is post hoc analysis, not live experiment control.

Most accurate summary:
- Script consumes experiments behaviorally
- attribution can observe experiment variants afterward
- the rest of the runtime mostly carries experiment structure without acting on it

## 11. Runtime Reality Vs Framework Reality

This subsystem sits on top of a broader experiment framework that is more complete than the runtime integration.

Framework capabilities exist in:
- `backend/app/experiments/service.py`
- `docs/experiments/experiment_framework_v1_0.md`

That framework supports:
- `create_experiment`
- deterministic `assign`
- `record_result`
- append-only persistence

But the creative runtime integration currently uses only a subset:
- `create_experiment`
- `resolve_variant_payload`

It does not use:
- `assign`
- `record_result`

This creates a gap:

What the framework says exists:
- auditable experiments
- persisted assignments
- persisted results

What the creative runtime actually does:
- emits plan context
- does not close the assignment/result loop

That gap must be stated explicitly.

## 12. Fallback And Default Dominance

The current frozen runtime is fallback/default dominant.

Evidence in code:
- `default_config_path` is `backend/data/experiments/experiment_config.json`
- that path does not exist in the current repo

Evidence in audit artifacts:
- repeated `CREATIVE/experiment_plan_fallback`
- repeated `experiment_id = "exp_default"` in heavy audit outputs

Additional limitation:
- `default_output_path` is `None`
- so in default runtime, the service does not persist a standalone `experiment_plan.json`

Practical conclusion:
- the subsystem is present in runtime
- but the current production-like path is mostly running the safe default experiment state

This matches the user's current reading:
- contract present
- integration present
- value causal low
- fallback/default dominant

## 13. Traceability And Auditability

What exists today:
- orchestrator events for experiment generated/fallback
- `ExperimentPlan` embedded in `CreativePack`
- `experiment_assignment` annotation embedded in `CreativePack`
- top-level experiment result in execution payload

What does not exist in the creative runtime path:
- persisted framework assignment row
- persisted framework result row
- assignment_id in runtime pack
- subject_key persisted as assignment record
- evidence that winner selection is acting on runtime output

Auditability verdict:
- shallow runtime traceability: yes
- full experiment auditability: no

The current subsystem can tell you:
- what variant context was attached to a run

It cannot yet fully tell you:
- that a framework assignment was formally recorded
- that the result was recorded back into the experiment system
- that a winner pipeline exists in live runtime

## 14. Determinism And Governance

### Determinism

Determinism is real.

Given the same:
- experiment name
- scope
- account id
- topic
- publish slot

the subsystem resolves the same experiment identity and variant.

There is no hidden randomness in current selection.

### Governance

Governance is weak.

What exists:
- safe default fallback
- deterministic A/B assignment logic
- explicit experiment events

What does not exist:
- no standalone experiment capability gate in current runtime docs
- no baseline promotion artifact for this subsystem
- no frozen baseline rules
- no runtime enforcement of safe eligibility envelope
- no direct QC or health gating on experiments

Most honest label:
- deterministic scaffold
- not baseline-governed subsystem yet

## 15. Test Surface

### Dedicated tests

File:
- `tests/test_experiment_capability_phase2_unittest.py`

What it proves:
- config-backed generation works
- fallback works when config is missing
- deterministic experiment plan shape exists

What it does not prove:
- runtime assignment persistence
- result recording
- meaningful downstream causal effect beyond presence

### Orchestrator smoke

File:
- `tests/test_phase2_block4_smoke_unittest.py`

What it proves:
- experiment capability is integrated into orchestrator
- non-fallback path can flow into full execution
- `creative_pack.experiment_plan` is present in runtime output

What it does not prove:
- real operating experiment governance in the default repo runtime

### Indirect coverage

Heavy audit artifacts show:
- fallback events
- experiment plan serialization

This proves runtime presence.
It does not prove subsystem maturity.

## 16. Current Strengths

Real strengths:
- implemented in code
- integrated into orchestrator
- deterministic
- clean minimal contract
- real behavioral effect on Script path
- aligned with correct architectural boundary
- broader experiment framework already exists in the repo

This matters because the subsystem does not need invention from zero.
It needs promotion from scaffold to operational subsystem.

## 17. Current Weaknesses / Limitations

Real weaknesses:
- default runtime config path is missing
- fallback/default dominates in current frozen runtime
- no true eligibility logic
- no runtime call to `assign(...)`
- no runtime call to `record_result(...)`
- no full persisted assignment artifact in creative runtime
- no result feedback loop in creative runtime
- narrow downstream effect, mostly Script-only
- no authority over strategy, QC, or publish governance
- learning context is accepted but mostly ignored
- experiment assignment inside `CreativePack` is only structural shorthand
- auditability is shallow, not full-cycle

Brutally honest summary:
- the subsystem exists
- but it is still closer to an ornamented context layer than to a true operating experimentation layer

## 18. Maturity Assessment

Assessment by dimension:
- implementation presence: high
- runtime integration: high
- causal effect: low to medium
- audit closure: low
- policy authority: low
- experimental governance maturity: low
- readiness for v2 evolution: high

Overall classification:
- not fake
- not merely decorative
- not yet strong enough to be called a real experiment operating subsystem

Most honest label:
- runtime-real but operationally underdeveloped

## 19. Gap Between Current State And Correct v2

The current subsystem is missing the exact pieces that would make it real:

### Eligibility
- current: absent
- needed: explicit safe experiment eligibility decision

### Assignment persistence
- current: synthetic only in `CreativePack`
- needed: real framework assignment in runtime path

### Result recording
- current: absent in runtime path
- needed: record experiment outcomes back into the framework

### Safe envelope
- current: implicit in variant payload only
- needed: explicit experiment type and boundary policy

### Multi-consumer impact
- current: mostly Script-only
- needed: at least one more controlled downstream consumer or stronger script-level enforcement proof

### Governance
- current: no subsystem gate/promotion/freeze logic
- needed: standalone validation, governance decision, audit, monitoring

## 20. Next Correct Move

The next correct move is:
- write `EXPERIMENT_CAPABILITY_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`

That v2 plan should do four things and only four things:

1. activate real experiment eligibility
2. wire real assignment persistence into runtime
3. wire real result recording into runtime
4. prove at least one controlled causal effect that is stronger than ornamental context

What should not happen:
- turning Experiment Capability into a second Strategy
- letting it mutate content directly outside downstream agents
- expanding it into winner-selection policy before assignment/result loop is real
- broad redesign of the frozen pipeline core

Correct v2 target:
- controlled experiment orchestrator
- not strategic brain
- not learning brain
- not content generator

## Appendix: Implementation Fact Vs Inference Vs Intended Future Role

### Implementation fact

- Experiment Capability exists in code.
- Orchestrator calls it in runtime.
- It emits `ExperimentPlan`.
- Script generation consumes `experiment_plan`.
- Default config path is missing in the current repo.
- Heavy audit runtime repeatedly shows fallback/default experiment state.
- Runtime integration does not call `assign(...)` or `record_result(...)`.

### Inference from code and artifacts

- current production-like runs are mostly not exercising real experiment control
- current causal value is narrow and mostly script-scoped

### Intended future role

- eligibility controller
- control vs variant allocator
- safe experiment envelope owner
- audit-closed experiment runtime subsystem

That future role is the correct v2 direction.
It is not what Phase 1 is yet.
