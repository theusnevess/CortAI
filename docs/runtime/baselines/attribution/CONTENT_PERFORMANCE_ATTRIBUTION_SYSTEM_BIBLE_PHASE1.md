# CONTENT_PERFORMANCE_ATTRIBUTION_SYSTEM_BIBLE_PHASE1

## 1. Executive Summary

The `Content Performance Attribution System` already exists in the CortAI codebase in partial but real form.
It is not only an idea.
It is not only a future architecture note.
It does have executable code, canonical contracts, persistence, and downstream consumption.

But it is also not yet a fully closed attribution subsystem in the strict governance sense used by the frozen `CORTAI_RUNTIME_V2_5`.

What is true today:
- there is a canonical `content attribution` record in `backend/app/product/attribution/`
- there is a deterministic builder that joins publish record, video metrics, window metrics, and optional scorecard
- there is append-only persistence for canonical attribution rows
- there is post-window runtime wiring for scorecard -> attribution -> strategy learning
- strategy learning already consumes attribution rows behaviorally

What is also true today:
- the subsystem is still post hoc, not upstream runtime control
- it does not decide publishability
- it does not decide experiment assignment
- it does not prove strong multi-factor causal attribution
- it does not yet have its own validation gate, governance decision, or frozen baseline classification
- there is still an older parallel attribution track in `backend/app/attribution/` that is analytical but not the canonical product path

Current classification:
- runtime-real: yes, in post-pipeline/product flow
- structurally integrated: yes
- causally useful: yes, but conservatively
- experimentally authoritative: no
- upstream-governing: no
- governance-closed as subsystem: no
- maturity level: real Phase 3 candidate with live product value, not yet a frozen baseline subsystem

Direct answers:
- Is Content Performance Attribution real today? Yes.
- Is it already part of the core frozen pipeline? No.
- Does it already affect behavior? Yes, through downstream strategy learning.
- Is it already a closed-loop causal performance operating system? No.
- Is this the correct place to start Phase 3? Yes.

## 2. Why This Is Phase 3

The current system registry for `CORTAI_RUNTIME_V2_5` says:
- core pipeline is frozen and validated
- subsystem mutation requires governance reopen
- new work must be isolated subsystems

That means the correct next move is not reopening Strategy, QC, Experiment Capability, or the core orchestrator as a broad redesign.
The correct next move is opening a new isolated subsystem that:
- consumes existing runtime artifacts
- produces its own auditable outputs
- can later feed bounded improvements downstream
- does not violate the frozen core boundary

`Content Performance Attribution System` is exactly that kind of subsystem.

## 3. Current Mission Of The Subsystem

Conceptually, this subsystem should do four things:
- attribute observed outcome back to content decisions
- normalize raw performance into decision-usable signals
- link experiment context to outcome where experiment context exists
- package stable learning-ready evidence for downstream consumers

What it actually does today:
- builds one canonical attribution row per `publish_id`
- joins publish metadata with observed video metrics
- resolves `policy_stage`
- extracts `hook_strategy`
- carries failure reason and duration-related fields when available
- persists append-only attribution outputs
- supplies attribution rows to strategy learning

What it does not actually do today:
- it does not isolate true causal contribution of each creative factor
- it does not infer robust contribution for script vs voice vs asset vs edit separately
- it does not own experiment assignment or result recording
- it does not score final quality governance
- it does not directly mutate baseline agents in runtime
- it does not produce a promotion/governance verdict for itself

Most precise description:
- today it is a post-pipeline attribution and feedback packaging subsystem
not:
- a full causal explanation engine

## 4. Responsibility Boundary

Correct boundary:

```json
{
  "content_performance_attribution": {
    "owns": [
      "content outcome attribution records",
      "performance signal normalization for learning use",
      "experiment-aware outcome linkage when experiment context exists",
      "downstream feedback packaging for learning consumers"
    ],
    "does_not_own": [
      "strategy policy",
      "experiment assignment",
      "experiment result governance",
      "publish governance",
      "content generation",
      "direct mutation of frozen baseline agents"
    ]
  }
}
```

Operational consequence:
- this subsystem may observe and summarize downstream truth
- it may package signals for later policy updates
- it may not become a hidden controller of the frozen pipeline

This boundary is mandatory if Phase 3 is to remain governance-clean.

## 5. Architectural Position

The real product-oriented position today is:

1. content is created and published earlier
2. video/window metrics are collected later
3. scorecard is generated for the completed window
4. attribution is generated for that same window/publish surface
5. strategy learning consumes attribution rows

This is wired in:
- `backend/app/jobs/window_post_pipeline.py`

That makes the subsystem:
- downstream of production runtime
- downstream of metrics capture
- downstream of scorecard generation
- upstream of strategy learning feedback packaging

This is the correct place for attribution.
Attribution should observe outcomes after the fact.
It should not masquerade as an upstream generation authority.

## 6. Real Implemented Surface In Code

### Canonical product attribution path

The strongest current implementation is in:
- `backend/app/product/attribution/builder.py`
- `backend/app/product/attribution/schema.py`
- `backend/app/product/attribution/repo.py`
- `backend/app/product/attribution/store_jsonl.py`

What this path already proves:
- canonical record exists
- schema validation exists
- append-only persistence exists
- idempotent save behavior exists
- the subsystem is not only free-form analytics

### Post-pipeline wiring

The subsystem already has a real orchestration slot in:
- `backend/app/jobs/window_post_pipeline.py`

The job order is:
- guard
- scorecard
- attribution
- strategy learning

This matters because it proves attribution is already in an operational chain, not just a notebook-style side analysis.

### Older analytical attribution track

There is also a separate attribution track in:
- `backend/app/attribution/service.py`

That older track computes:
- hook performance
- structure performance
- duration analysis
- pattern performance

It is useful evidence.
It is not the clean product baseline for Phase 3.

The most honest reading is:
- `backend/app/attribution/` is analytical support infrastructure
- `backend/app/product/attribution/` is the better canonical base for the Phase 3 subsystem

## 7. Current End-To-End Flow

Actual operational flow today:

1. A publish record exists.
2. Video metrics become available.
3. Window metrics become available.
4. Optional scorecard becomes available.
5. `build_attribution(...)` resolves a canonical row for `publish_id`.
6. The row is validated against the attribution schema.
7. The row is persisted append-only.
8. Strategy learning reads attribution rows and may emit a bounded strategy patch.

Important honesty points:
- attribution depends on downstream metrics existence
- attribution can be skipped when metrics are missing
- attribution is not guaranteed to exist for every theoretical publish event
- current learning use is still conservative and heuristic

## 8. Contracts And Data Model

### Canonical attribution record

The canonical schema in `backend/app/product/attribution/schema.py` currently requires:
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

Optional fields currently include:
- `dominant_failure_reason`
- `effective_duration_s`
- `rare_fact_placement_s`
- `likes`
- `follows`
- `rpm`

This is already a meaningful contract.
It is strong enough to support deterministic downstream learning.
It is not yet strong enough to support high-confidence full causal decomposition.

### Policy stage resolution

The builder resolves `policy_stage` from:
- publish record
- window metrics
- optional scorecard

That is a good architectural decision because attribution should preserve the strategic context under which the content was produced.

### Hook strategy resolution

The builder resolves `hook_strategy` from publish metadata and creative-pack metadata.

This is important because it gives the subsystem one real bridge from content decision to outcome.
But the bridge is still narrow.
It is not yet a full creative-factor graph.

## 9. Downstream Behavioral Effect

The subsystem already has real downstream effect because:
- `backend/app/product/strategy_learning/learner.py` consumes attribution rows
- attribution patterns can activate bounded overrides in strategy learning

Current examples of behaviorally active outcomes:
- detecting high share of `missing_number`
- detecting high share of `low_tension`
- detecting repeated `curiosity_gap` hook pattern

This means attribution is already more than observability.
It is already part of a conservative feedback loop.

But the loop is still limited:
- it is aggregate and heuristic
- it is not a general causal optimizer
- it does not prove which specific content component caused the result

## 10. Relationship To Experiment Capability

This subsystem must be experiment-aware.
It must not become experiment-owning.

Correct relationship:
- Experiment Capability owns assignment and result lifecycle
- Content Performance Attribution may consume experiment context as explanatory metadata
- Attribution may help compare outcome by variant after the fact
- Attribution must not silently replace experiment governance

There is evidence of experiment-aware attribution in the repo, including the older analytical path in `backend/app/attribution/service.py`.
That is useful, but the ownership line must remain clean.

The correct Phase 3 target is:
- experiment-linked attribution
not:
- attribution pretending to be the experiment subsystem

## 11. Runtime Reality Vs System Claim

If the subsystem claims:
- "we know why content wins"

that claim would be false today.

If the subsystem claims:
- "we can build auditable, normalized outcome records tied to content metadata and feed them into bounded learning"

that claim is true today.

If the subsystem claims:
- "we can already separate the causal effect of script, hook, duration, asset, voice, edit, policy stage, and experiment variant with strong confidence"

that claim is false today.

The correct honest statement is:
- current attribution is real, useful, and operationally relevant
- but still conservative, partial, and not yet a closed causal truth layer

## 12. Main Gaps

The subsystem still lacks:
- a dedicated validation gate
- a dedicated governance decision
- a subsystem-level frozen baseline classification
- richer canonical factor coverage beyond the current narrow fields
- stronger experiment linkage on the canonical product path
- stronger handling of multiple simultaneous creative factors
- long-horizon runtime evidence proving stability

There is also a repo-level clarity gap:
- two attribution tracks exist
- one should become canonical for governance
- the other should either support it explicitly or remain clearly non-canonical

If this is not cleaned up, the subsystem will drift into ambiguous ownership.

## 13. What The Subsystem Should Not Be Allowed To Do In Phase 3

It should not:
- reopen the frozen core pipeline
- directly rewrite Strategy runtime behavior outside approved downstream interfaces
- own experiment assignment
- own publish decisions
- claim causal certainty that the evidence cannot support
- bypass governance by shipping "analytics" that secretly changes baseline behavior

These constraints are not optional.
They are the condition for adding the subsystem without breaking `CORTAI_RUNTIME_V2_5`.

## 14. Correct Phase 3 Objective

The correct Phase 3 objective is:
- establish `Content Performance Attribution` as an isolated, auditable, product-grade subsystem with canonical contracts, deterministic outputs, experiment-aware linkage, bounded downstream effect, and its own validation/governance path

That objective is narrower and better than:
- "build full AI causal understanding of content performance"

The narrow objective is achievable.
The broader claim would produce architectural drift.

## 15. Recommended Next Moves

Immediate next moves:

1. Declare `backend/app/product/attribution/` as the canonical subsystem root for Phase 3.
2. Define the official subsystem contract and required evidence set.
3. Add a dedicated validation gate for attribution correctness, determinism, missing-metrics honesty, and downstream learning effect.
4. Prove experiment-aware linkage on the canonical path without taking over experiment ownership.
5. Produce a governance decision only after the subsystem has real operational evidence.

Recommended target state after Phase 3 validation:
- runtime-real: yes
- deterministic where required: yes
- downstream-causal relevance: yes
- experiment-aware: yes
- governance-closed: yes
- frozen unless governance reopen: yes

## 16. Final Verdict

The `Content Performance Attribution System` is the correct Phase 3 subsystem to open next.

It already has:
- real code
- real contracts
- real persistence
- real post-pipeline wiring
- real downstream effect

It does not yet have:
- full causal closure
- subsystem governance closure
- baseline-frozen status

Most accurate verdict:
- `Phase 3 candidate approved to define and isolate`
not:
- `baseline subsystem already certified`
