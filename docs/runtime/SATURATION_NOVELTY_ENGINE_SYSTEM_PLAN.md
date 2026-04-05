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
