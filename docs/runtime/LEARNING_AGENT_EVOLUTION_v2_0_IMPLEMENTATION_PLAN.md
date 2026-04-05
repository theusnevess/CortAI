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
