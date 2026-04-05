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
- `tests/test_video_qc_agent_phase2_unittest.py`
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
