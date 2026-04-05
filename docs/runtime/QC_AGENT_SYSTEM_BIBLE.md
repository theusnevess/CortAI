# QC Agent System Bible Phase 1

## 1. Executive Summary

The QC Agent implemented today is a narrow runtime validator for rendered video outputs. It exists to inspect the final generated artifacts after the pipeline has already produced audio, video, metadata, and a publish manifest. Its current job is to detect obvious technical and render-quality failures and return a binary decision: `APPROVE` or `REJECT`.

What it solves today:
- catches missing or empty final artifacts
- catches missing runtime metadata
- catches obviously invalid subtitle cue structure
- catches broken glyph output in subtitles
- catches extremely dark payoff frames through a metadata proxy
- catches invalid output resolution
- catches missing audio stream

What it does not solve today:
- it does not score or compare overall product quality
- it does not reason about hook strength, payoff landing, retention, or audiovisual cohesion as a first-class product judge
- it does not issue `HOLD`
- it does not repair, re-render, or mutate upstream outputs
- it does not currently enforce a true publish gate in code after a `REJECT`

Current maturity:
- implemented: yes
- integrated in the orchestrator: yes
- deterministic technical validator: mostly yes
- baseline-ready as a full strategic QC subsystem: no
- baseline-ready as a basic technical post-render validator: yes
- governed/versioned as an independent subsystem: no
- validated: partially

Brutally honest status:
- the QC Agent Phase 1 exists and works
- it is useful as a technical sanity gate
- it is not yet the richer product-level judge implied by the broader CortAI architecture documents

## 2. Current Mission of the QC Agent

Actual operational mission in code:
- evaluate the final rendered output after the content pipeline finishes
- inspect files and render metadata
- return `APPROVE` when no QC failures are found
- return `REJECT` with explicit reason codes when any QC failure is found

What it is today:
- a post-render technical validator
- a binary quality gate result producer
- an explainable source of rejection reasons

What it is not today:
- not a fixer
- not a repair loop
- not a rerender controller
- not a scoring engine
- not a ranking engine
- not a batch judge
- not a full publish gate enforcer
- not a perceptual/video-style critic in the human-review sense

What it does not mutate:
- `ScriptPlan`
- `VoicePlan`
- `AssetPlan`
- `EditPlan`
- rendered outputs

Files:
- `backend/app/creative/agents/video_qc/service.py`
- `backend/app/creative/agents/video_qc/models.py`

## 3. Responsibility Boundary

### Script Agent
Owns:
- narrative generation
- hook/setup/payoff structure
- textual story intent

QC does not:
- rewrite script
- score script quality explicitly
- edit script output

### Voice Agent
Owns:
- voice provider selection
- voice identity
- delivery profile
- TTS execution policy

QC does not:
- change voice provider
- resynthesize audio
- score prosody, emotion, or naturalness directly

### Asset Agent
Owns:
- asset choice
- visual query formulation
- retrieval and selection
- runtime asset resolution

QC does not:
- re-run retrieval
- select replacement assets
- judge asset semantics directly except through one indirect luma proxy

### Editor Agent
Owns:
- captions
- motion
- transitions
- color/polish
- timing

QC does not:
- rewrite edit plan
- change captions
- change motion or timing
- re-edit final video

### QC Agent
Owns today:
- final artifact validation
- metadata-based sanity checks
- binary approve/reject result
- rejection reasons

### Publish / downstream layers
Own today:
- publish manifest creation
- event persistence
- downstream scheduling/publish usage

Important boundary fact:
- in current code, publish manifest creation happens before QC evaluation
- QC does not currently cancel or revoke the publish manifest

## 4. Architectural Position in the Pipeline

The intended conceptual pipeline is:

`Script -> Voice -> Assets -> Editor -> QC -> Publish/Hold/Reject`

The actual implemented runtime order is:

`Script -> Voice -> Assets -> Editor -> Content Pipeline (TTS -> Render -> Publish manifest) -> QC -> event emission -> return result`

Actual call chain:
- `backend/app/creative/orchestrator/service.py`
- `backend/app/content/pipeline/service.py`
- `backend/app/content/pipeline/orchestrator.py`
- `backend/app/creative/agents/video_qc/service.py`

Actual position:
1. `CreativeOrchestratorService.execute(...)` builds the creative pack
2. `ContentPipelineService.run_pipeline(...)` executes TTS, render, and publish-manifest creation
3. only after pipeline completion does `VideoQcAgentService.evaluate(...)` run
4. orchestrator emits either `CREATIVE/video_qc_approved` or `CREATIVE/video_qc_rejected`
5. `CreativePipelineExecution` returns both `pipeline_output` and `video_qc`

Upstream dependencies:
- final artifact paths from pipeline result
- render metadata JSON
- runtime video file
- runtime audio file

Downstream consequences currently implemented:
- event emission
- `VideoQcResult` inclusion in execution result

Downstream consequences not implemented:
- no publish rollback
- no pipeline status rewrite from `READY` to `REJECT`
- no automatic `HOLD`
- no automatic remediation

## 5. End-to-End Flow

Actual runtime flow:

1. `CreativeOrchestratorService.execute(...)` is called.
2. Upstream context is resolved:
   - account health
   - trend analysis
   - learning
   - strategy
   - experiment
3. If account health returns `HOLD`, execution stops before pipeline and QC is not called.
4. If not held, creative pack is built.
5. `ContentPipelineService.run_pipeline(...)` runs:
   - TTS
   - render
   - publish manifest creation
6. The orchestrator calls:
   - `VideoQcAgentService.evaluate(render_job_id=..., artifacts=..., base_dir=...)`
7. QC reads:
   - `artifacts["video"]`
   - `artifacts["audio"]`
   - metadata JSON under `base_dir / "metadata" / f"{render_job_id}.json"`
8. QC returns `VideoQcResult`.
9. Orchestrator emits:
   - `CREATIVE/video_qc_approved` or
   - `CREATIVE/video_qc_rejected`
10. `CreativePipelineExecution` is returned to caller.

Files:
- `backend/app/creative/orchestrator/service.py`
- `backend/app/content/pipeline/service.py`
- `backend/app/content/pipeline/orchestrator.py`
- `backend/app/creative/orchestrator/models.py`

Important actual behavior:
- pipeline result may already be `READY` with a publish manifest before QC returns `REJECT`

## 6. Contracts and Data Structures

### `VideoQcInput`
File:
- `backend/app/creative/agents/video_qc/models.py`

Fields:
- `render_job_id: str`
- `video_path: str`
- `audio_path: str`
- `metadata_path: str | None`

Status:
- defined
- serializable via `to_dict()`
- not used by `VideoQcAgentService`

Assessment:
- currently decorative / unused contract residue

### `VideoQcDecision`
File:
- `backend/app/creative/agents/video_qc/models.py`

Fields:
- `status: Literal["APPROVE", "REJECT"]`
- `reasons: list[str]`
- `checked_at: str`

Status:
- defined
- serializable via `to_dict()`
- not used by `VideoQcAgentService`

Assessment:
- currently decorative / unused contract residue

### `VideoQcResult`
File:
- `backend/app/creative/agents/video_qc/models.py`

Fields:
- `status: Literal["APPROVE", "REJECT"]`
- `reasons: list[str]`
- `checked_at: str`
- `details: dict[str, Any]`

Status:
- operational
- serializable via `to_dict()`
- returned by the QC service
- embedded into `CreativePipelineExecution`

Actual `details` fields observed in code and artifacts:
- `render_job_id`
- `video_path`
- `audio_path`
- `metadata_path`
- `render_duration_s`
- `setup_background_mean_luma`
- `payoff_background_mean_luma`
- `width`
- `height`
- `has_audio`
- `probe_mode`
- on internal error: `error`

Operational note:
- `details` is not schema-enforced beyond being a dict
- field presence depends on how far evaluation progressed

### `CreativePipelineExecution.video_qc`
File:
- `backend/app/creative/orchestrator/models.py`

Status:
- operational
- carries `VideoQcResult | None`
- serialized by `CreativePipelineExecution.to_dict()`

### `CreativeOrchestratorResult.qc_required`
File:
- `backend/app/creative/contracts/orchestrator_io.py`

Field:
- `qc_required: bool = True`

Status:
- present
- returned by build-only path
- not used to control runtime execution

Assessment:
- metadata flag only; not operational gating logic

## 7. Decision Model

The decision model is simple and binary.

There are only two statuses in actual QC code:
- `APPROVE`
- `REJECT`

There is no `HOLD` in QC Phase 1.

Top-level rule:
- `APPROVE` if `reasons` is empty
- `REJECT` if `reasons` contains one or more reason codes

There is no:
- numeric score
- confidence score
- weighted blending
- layered final arbitration
- soft-pass threshold

Decision procedure in `VideoQcAgentService._evaluate(...)`:

1. Reject immediately with `QC_ARTIFACTS_INVALID` if `artifacts` is not a dict.
2. Collect missing-file failures:
   - `QC_VIDEO_MISSING`
   - `QC_AUDIO_MISSING`
   - `QC_METADATA_MISSING`
3. If metadata exists, load metadata JSON and run checks:
   - minimum render duration
   - subtitle cue list validity
   - empty cue text
   - broken glyph characters
   - payoff luma minimum
4. Probe video stream via `ffprobe` when available.
5. If `ffprobe` unavailable, infer dimensions from metadata and assume audio presence from audio file existence.
6. Apply stream checks:
   - resolution must be exactly `1080x1920`
   - audio stream must exist
7. Return final `VideoQcResult`.

Exception handling:
- any unexpected exception is caught in `evaluate(...)`
- returned as `REJECT` with reason `QC_INTERNAL_ERROR`

## 8. Evaluation Layers

The QC Agent does not implement explicit upstream-layer evaluation modules.

### Script quality
Implemented: no

What exists:
- no script scoring
- no narrative evaluation
- no hook/setup/payoff textual assessment

Influence on QC today:
- none direct

### Voice quality
Implemented: only a minimal stream-presence check

What exists:
- `has_audio` must be true
- if false: `QC_AUDIO_STREAM_MISSING`

What does not exist:
- intelligibility scoring
- prosody scoring
- emotion scoring
- pacing scoring
- clipping/noise analysis

### Asset quality
Implemented: only one indirect visual proxy

What exists:
- `payoff_background_mean_luma` from render metadata
- if payoff luma `< 45`: `QC_PAYOFF_TOO_DARK`

What does not exist:
- asset relevance scoring
- semantic correctness
- repetition detection
- motif loop detection
- diversity judgment

### Edit quality
Implemented: partially and only via subtitle/render sanity checks

What exists:
- subtitle cue list must be a list with length `3..9`
- cue text cannot be empty
- cue text cannot contain known broken-glyph markers
- minimum duration and output resolution checks

What does not exist:
- caption timing quality judgment
- motion quality judgment
- transition quality judgment
- color grade quality judgment
- editor punch or memorability judgment

### Product quality
Implemented: no true product layer

What exists:
- basic render completeness checks
- one payoff darkness proxy

What does not exist:
- first-2-second retention estimate
- publishability scoring
- hook strength
- payoff landing
- audiovisual cohesion
- human-like product judgment

Conclusion:
- QC Phase 1 evaluates final runtime artifacts structurally
- it does not evaluate Script, Voice, Asset, or Editor as distinct quality layers in code

## 9. Score Model and Weights

No explicit score model exists.

There are:
- no weights
- no calibrated thresholds beyond hardcoded rules
- no layer scores
- no weighted sum
- no confidence weighting

Current QC is rule-based only.

Determinism:
- mostly deterministic on the same artifacts and same environment
- not fully environment-invariant because `ffprobe` availability changes behavior

Hardcoded thresholds actually in code:
- minimum duration: `MIN_VIDEO_DURATION_S` imported from `backend/app/content/pipeline/render.py`
  - current value in render code: `8.0`
- subtitle cue count:
  - minimum `3`
  - maximum `9`
- payoff luma:
  - reject if `< 45`
- resolution:
  - must be exactly `1080x1920`

Important caveat:
- metadata fallback for `ffprobe` can infer `1280x720` for `aspect_ratio == "16:9"`, which would still fail current resolution rule
- in practice, the pipeline is operating in portrait, so this has not surfaced as an operational success case

## 10. Hard Failures, Soft Failures, and Failure Hierarchy

There is no explicit severity hierarchy in QC Phase 1.

Everything collected in `reasons` behaves as a hard reject.

Implemented failure behavior:
- any reason code -> `REJECT`
- no reason code -> `APPROVE`

Reason codes implemented today:
- `QC_INTERNAL_ERROR`
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

There is no implemented distinction between:
- critical
- major
- minor
- soft warning

There is also no partial pass state.

## 11. Publishability / Product Judgment

The QC Agent does not implement explicit publishability judgment in the richer product sense.

What it judges today:
- whether required output files exist
- whether render metadata exists
- whether duration clears a minimum
- whether subtitles are structurally valid
- whether payoff frame is not too dark
- whether video dimensions are correct
- whether audio stream exists

What it does not judge:
- first-2-second retention
- hook strength
- setup progression
- payoff memorability
- perceptual cohesion
- atmosphere
- whether the video feels publishable to a human viewer

Brutally honest assessment:
- current QC is not a true product judge
- it is a technical validity judge with one weak perceptual proxy (`QC_PAYOFF_TOO_DARK`)

Important architectural consequence:
- current code creates a publish manifest before QC runs
- therefore the QC Agent is not yet a hard publish gate in execution order

## 12. Traceability and Auditability

What exists:
- `VideoQcResult` is explainable through explicit reason codes
- `details` contains concrete paths and measured fields
- orchestrator emits:
  - `CREATIVE/video_qc_approved`
  - `CREATIVE/video_qc_rejected`
- many validation scripts persist full `CreativePipelineExecution` payloads including `video_qc`

Examples:
- `OUT/audit/camera_blackout_comfyui_reassessment/video_qc.json`
- `OUT/audit/editor_final_parity_validation/execution_batch.json`
- `OUT/audit/editor_final_parity_validation/events/creative_events.jsonl`

What does not exist:
- no dedicated QC decision repository
- no `qc_history/` implementation in current code
- no dedicated QC audit directory produced by the QC service itself
- no structured confidence field
- no explicit layer-by-layer explanation object

Explainability level:
- moderate for technical reject reasons
- low for anything beyond the technical checks, because those richer checks do not exist

## 13. Baseline, Comparison, and Regression Handling

Not implemented.

There is no current support for:
- baseline comparison
- prior-batch comparison
- regression detection
- top-performer comparison
- dynamic thresholding
- novelty handling
- relative ranking against account history

The QC Agent does not read:
- historical QC decisions
- performance history
- batch diversity history
- recent publish outcomes

Any notion of baseline or product regression in current CortAI audits lives outside the QC service, in standalone validation scripts or human review artifacts.

## 14. Batch-Aware Behavior

Not implemented.

Current QC reasons only at single-video level.

No implemented support for:
- batch ranking
- top-k publish selection
- intra-batch redundancy detection
- diversity checks
- batch-level hold conditions
- novelty or saturation management

If five videos are evaluated, QC processes them independently.

## 15. Determinism and Governance

### Determinism

Current QC is mostly deterministic for the same artifacts.

Deterministic inputs:
- file existence
- metadata fields
- hardcoded thresholds
- ffprobe stream results

Environment-sensitive behavior:
- if `ffprobe` exists, QC uses real stream probing
- if `ffprobe` does not exist, QC falls back to metadata inference

That means:
- the same video can theoretically be judged slightly differently depending on environment tooling availability

### Governance

Not meaningfully implemented as an independent subsystem.

What does not exist:
- QC version field
- threshold config file
- freeze rule for QC
- baseline artifacts specific to QC
- confidence calibration policy
- explicit governance document for QC

Important observation:
- architecture docs mention richer QC ideas and even artifacts like `save_video_qc_decision(...)`
- those are not implemented in the current Phase 1 code

## 16. Test Surface

### Unit tests

Primary QC unit test:
- `tests/test_video_qc_agent_phase2_unittest.py`

What it proves:
- valid generated video can be approved
- missing metadata causes `REJECT`
- dark payoff metadata causes `REJECT`

What it does not prove:
- product quality correctness
- batch behavior
- downstream handling of rejection

### Integration / smoke tests

Files:
- `tests/test_phase2_block1_smoke_unittest.py`
- `tests/test_phase2_block2_smoke_unittest.py`
- `tests/test_phase2_block3_smoke_unittest.py`
- `tests/test_phase2_block4_smoke_unittest.py`

What they prove:
- QC is invoked in successful orchestrator flows
- successful executions return `video_qc.status == "APPROVE"`
- upstream `AccountHealth HOLD` prevents QC from running
- trend/learning/experiment context can flow through the pipeline and still reach QC

What they do not prove:
- reject-path orchestration behavior
- publish gating after reject
- perceptual accuracy of decisions

### Validation scripts / audit scripts

QC appears inside broader validation artifacts, for example:
- `tests/run_editor_agent_full_validation.py`
- `tests/run_editor_expression_validation.py`
- `tests/run_editor_punch_and_variation_validation.py`
- `tests/run_editor_final_parity_validation.py`

What those prove:
- batches of real videos can complete with `video_qc.status == "APPROVE"`
- QC result is persisted in execution batches and event logs

What they do not prove:
- that QC is a strong independent quality judge
- that QC can meaningfully reject bad but technically valid videos

## 17. Validation History / Audit History

Observed evidence in filesystem:

### Real QC artifact example
- `OUT/audit/camera_blackout_comfyui_reassessment/video_qc.json`
- proves `VideoQcResult` can be serialized and persisted in a real run

### Execution batches containing QC results
- `OUT/audit/editor_agent_full_validation_gate/execution_batch.json`
- `OUT/audit/editor_expression_validation_gate/execution_batch.json`
- `OUT/audit/editor_punch_and_variation_validation/execution_batch.json`
- `OUT/audit/editor_final_parity_validation/execution_batch.json`

What these prove:
- QC is actually executed in validation runs
- QC results are attached to pipeline execution records
- approved videos commonly yield `APPROVE`

What they do not prove:
- standalone QC baseline validation
- calibrated reject behavior on a production batch
- batch-aware intelligence

Missing from observed history:
- no dedicated `OUT/audit/qc_*` full validation gate for QC itself
- no QC baseline promotion artifacts
- no historical decision ledger

## 18. Current Strengths

Actual strengths supported by implementation:

1. Simple and explainable
- binary result
- explicit reason codes
- inspectable details

2. Integrated into orchestrator runtime
- called automatically after pipeline completion
- result is returned in `CreativePipelineExecution`

3. Catches obvious technical failures
- missing video/audio/metadata
- invalid subtitle cue structure
- broken glyphs
- invalid resolution
- missing audio stream

4. Uses real runtime artifacts
- evaluates actual files and metadata, not only planned state

5. Handles internal failures safely
- unexpected exception becomes controlled `REJECT` with `QC_INTERNAL_ERROR`

6. Auditable enough for technical debugging
- paths, luma, dimensions, and probe mode are recorded in `details`

## 19. Current Weaknesses / Limitations

Actual weaknesses:

1. No `HOLD`
- current QC cannot express a softer gating state
- only `APPROVE` or `REJECT`

2. Not a real publish gate yet
- publish manifest is created before QC
- orchestrator does not currently convert QC reject into pipeline failure or publish cancellation

3. No scoring model
- no numeric score
- no weights
- no thresholds beyond hardcoded rule checks

4. No explicit product judgment
- no hook strength
- no payoff landing
- no cohesion judgment
- no retention estimate

5. No layer-specific evaluation
- no separate Script/Voice/Asset/Edit assessments

6. No batch intelligence
- no diversity awareness
- no ranking
- no top-k logic

7. Unused contract residue
- `VideoQcInput` unused
- `VideoQcDecision` unused

8. Environment-dependent probing behavior
- `ffprobe` presence changes evaluation path

9. No governance as its own subsystem
- no version
- no baseline
- no freeze rule
- no threshold config

10. Limited perceptual coverage
- only a single visual proxy for darkness
- no broader visual or auditory product critique

## 20. Current Maturity Assessment

### Technical integrity
- medium to high
- code is small, understandable, and tested

### Perceptual usefulness
- low
- current checks are mostly structural, not perceptual

### Explainability
- medium
- reason codes are clear, but evaluation depth is shallow

### Governance
- low
- no independent QC governance layer

### Batch intelligence
- none

### Strategic value
- medium as a technical guardrail
- low as a strategic quality subsystem

### Overall status
- implemented: yes
- integrated: yes
- useful: yes, as a technical validator
- phase-1 only: yes
- safe to rely on in production as the only quality judge: no
- safe to rely on in production as a basic post-render sanity validator: yes
- baseline-ready as a strategic QC subsystem: no

Recommended honest label:
- **implemented, integrated, and technically useful, but still partial and not baseline-complete as a true CortAI QC Agent**

## 21. Next Correct Move

The next correct move is not to add more ad hoc reject rules.

The next correct move is:

**promote QC from a technical post-render validator into a true product-aware publish gate**

Concretely, the highest-value next step is:

1. make QC downstream-consequential
- a `REJECT` must affect publish eligibility in code, not only event logs

2. add product-level perceptual evaluation
- hook strength
- readability quality
- payoff landing
- audiovisual cohesion

3. add an explicit `HOLD`
- for ambiguous or borderline cases where hard reject is too strong

4. add a real QC contract and governance layer
- versioned thresholds
- persistent decision history
- explicit baseline artifacts

5. only after that, add batch-aware QC
- ranking
- repetition awareness
- relative quality gating

Why this is the next correct move:
- current QC already catches technical defects
- its largest gap is not more structural validation
- its largest gap is lack of real product judgment and lack of downstream enforcement

## Appendix: Implementation vs Intention

### Implemented now
- `VideoQcAgentService`
- `VideoQcResult`
- technical rule-based post-render checks
- orchestrator integration
- approve/reject events
- basic unit and smoke-test coverage

### Mentioned elsewhere but not implemented in current Phase 1 code
- `HOLD` as a QC decision
- score-based QC
- layer-specific QC scoring
- batch-aware QC
- dynamic baseline comparison
- confidence model
- persistent QC history repository
- explicit `save_video_qc_decision(...)`
- automatic corrective loop
- real publish blocking after QC reject
