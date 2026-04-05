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
