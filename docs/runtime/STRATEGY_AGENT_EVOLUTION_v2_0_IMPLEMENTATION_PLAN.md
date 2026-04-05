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
