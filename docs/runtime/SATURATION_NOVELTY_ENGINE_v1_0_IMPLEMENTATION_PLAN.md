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
