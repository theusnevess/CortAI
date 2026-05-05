# PHASE_2_6_WAVE_2_MASTER_GATE

## 1. Purpose

`PHASE_2_6_WAVE_2_MASTER_GATE` is the official consolidated gate for Phase 2.6 Wave 2.

The gate validates whether the output-quality agents that completed their own excellence gates can be considered ready for v3 with monitoring as an integrated Wave 2 surface.

This is an audit artifact. It must not implement features, mutate runtime behavior, fix code to pass, modify Strategy, modify Script, Voice, Asset Selection, Video QC, Publisher, the orchestrator, or the core pipeline.

The gate exists to prove readiness, not to create readiness.

## 2. Scope

In scope:

- Script Agent v2.6
- Voice Agent v2.6
- Asset Selection Agent v2.6
- Video QC Agent v2.6
- output-quality contract compatibility
- Strategy and orchestrator compatibility
- content pipeline compatibility
- deterministic replay
- fallback honesty
- boundary preservation
- trace completeness
- silent failure detection
- residual monitoring classification
- consistency with child excellence gates

Out of scope:

- changing Script, Voice, Asset Selection, Video QC, Strategy, Publisher, orchestrator, or core pipeline
- changing provider order
- changing asset ranking
- changing QC thresholds
- changing publishability logic
- adding repair, regeneration, rerender, publishing, or performance prediction
- converting blockers into residual monitoring

## 3. Preconditions

Required child gates:

- `OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json`

Required planning and governance references:

- `docs/runtime/phase-2-6/master/PHASE_2_6_WAVE_2_OUTPUT_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/video-qc/VIDEO_QC_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md`
- `OUT/audit/system_governance_registry.json`

Required command:

`python tests/gates/phase_2_6/run_phase_2_6_wave_2_master_gate.py`

## 4. Blocks A-P

### Block A - Artifact Integrity

Validates required docs, child gate artifacts, runners, and JSON payloads.

Fails if any mandatory artifact is missing or invalid.

### Block B - Governance Consistency

Validates frozen governance posture, core immutability, isolated subsystem work, and no unauthorized Strategy/orchestrator/core mutation implied by artifacts.

Fails on governance contradiction or ownership drift.

### Block C - Script Gate Integrity

Validates Script v2.6 child gate readiness, including context governance, quality rubric, hook/setup/payoff analysis, fallback honesty, calibrated confidence, traceability, boundary preservation, determinism, and no silent failures.

### Block D - Voice Gate Integrity

Validates Voice v2.6 child gate readiness, including contract governance, delivery semantics, timing, monotony/contrast, provider fallback honesty, audio validation linkage, calibrated confidence, traceability, TTS Router boundary, determinism, and no silent failures.

### Block E - Asset Gate Integrity

Validates Asset Selection v2.6 child gate readiness, including context governance, catalog/source governance, visual intent, semantic alignment, truthfulness, fallback honesty, diversity, confidence, traceability, selection/ranking/fallback preservation, boundary preservation, determinism, and no silent failures.

### Block F - Video QC Gate Integrity

Validates Video QC v2.6 child gate readiness, including input governance, evidence scoring, confidence honesty, decision semantics, severity, reconstructible `qc_trace`, `APPROVE/HOLD/REJECT` preservation, publishability preservation, boundary preservation, determinism, and no silent failures.

### Block G - Contract Integrity

Imports and serializes representative outputs/contracts for Script, Voice, Asset Selection, Video QC, and Strategy integration surfaces.

Fails if imports break, serialization fails, or required additive fields disappear.

### Block H - Output Pipeline Integration

Executes controlled real-service scenarios proving Script output can feed Voice and Asset surfaces, and QC can evaluate final artifact surfaces without repairing, publishing, rewriting, rerendering, or predicting performance.

### Block I - Orchestrator Compatibility

Runs orchestrator compatibility tests and validates that existing QC governance remains the final output publishability path.

### Block J - Determinism And Replay

Replays controlled Script, Voice, Asset, Video QC, and combined output scenarios.

Fails on stable-field drift without input change.

### Block K - Fallback Honesty

Validates Script fallback, Voice fallback/trace absence, Asset safe-default fallback, and Video QC missing/fallback evidence remain explicit and not represented as success.

### Block L - Boundary Preservation

Validates:

- Script does not become Strategy, Voice, Asset, QC, or Publisher
- Voice does not become TTS Router, Strategy, QC, or Publisher
- Asset Selection does not become Strategy, QC, Publisher, or visual truth authority beyond metadata
- Video QC does not repair, publish, rewrite, rerender, replace assets, resynthesize voice, or predict performance
- Strategy remains the control layer
- Publisher remains out of scope

### Block M - Trace And Auditability

Validates:

- `script_trace` reconstructs `ScriptPlan`
- `voice_trace` reconstructs `VoicePlan`
- `asset_trace` reconstructs `AssetPlan`
- `qc_trace` reconstructs `APPROVE/HOLD/REJECT`
- audit summaries are honest

### Block N - Security And Logical Vulnerability Surface

Fails on fake confidence, fake evidence, hidden fallback, hidden degraded input, hidden safe default, silent publishability authority, hidden QC override, non-determinism, performance prediction, or silent failure indicators.

### Block O - Residual Monitoring Classification

Collects residuals from the four child gates and classifies only non-structural residues as monitoring.

Acceptable categories include runtime history still short, provider execution history still short, catalog coverage expanding, product signal calibration maturing, media probe coverage environment-dependent, and layer attribution evidence still limited.

Fails if structural blockers are classified as residual monitoring.

### Block P - Final Release Decision

Derives the final verdict from all blocks.

Fails if any critical block fails.

## 5. Critical Failure Definitions

Critical failures include:

- missing mandatory child gate artifact
- child gate verdict `HOLD`
- child gate blocking failures
- child gate critical failures
- failed critical test battery
- fake confidence
- silent failure detected
- boundary violation
- trace incompleteness
- hidden fallback
- non-deterministic replay
- publishability inconsistency
- output-quality agent overriding Strategy
- Video QC changing status/publishability semantics
- Publisher behavior introduced
- core/orchestrator mutation implied by audit evidence
- performance prediction introduced
- structural blocker classified as residual monitoring

## 6. Verdict Semantics

`HOLD`:

Required when any critical block fails, any child gate is `HOLD`, any blocking failure exists, fake confidence is detected, silent failure is detected, boundary is violated, trace is incomplete, fallback is hidden, publishability is inconsistent, or non-determinism is detected.

`GO_WITH_MONITORING`:

Allowed when all critical blocks pass and remaining residuals are explicit, bounded, non-structural, and related to runtime maturity, provider/catalog/media-probe coverage, or longitudinal evidence maturity.

`GO`:

Allowed only when all blocks pass and no meaningful residual monitoring remains.

Expected likely verdict is `GO_WITH_MONITORING`. The runner must derive it from evidence and must not hardcode it.

## 7. Required Artifacts

The runner writes:

- `OUT/audit/phase_2_6_wave_2_master_gate/final_verdict.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/checklist_results.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/scenario_outputs.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/metrics.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/cross_agent_consistency.json`

The final verdict must include child gate readiness summaries, block results A-P, test execution records, metrics, blocking failures, residual monitoring, and recommendation to proceed or hold.

## 8. Final Decision Rule

The Wave 2 Master Gate may recommend proceeding only when:

- Script Agent v2.6 is `GO` or `GO_WITH_MONITORING`
- Voice Agent v2.6 is `GO` or `GO_WITH_MONITORING`
- Asset Selection Agent v2.6 is `GO` or `GO_WITH_MONITORING`
- Video QC Agent v2.6 is `GO` or `GO_WITH_MONITORING`
- all blocks A-P pass
- critical tests pass
- no fake confidence is detected
- no silent failure is detected
- no boundary violation is detected
- no non-determinism is detected
- all required traces are reconstructible
- all residuals are bounded and non-structural

Final recommendation values:

- `PROCEED_TO_PHASE_2_6_FINAL_MASTER_GATE`
- `HOLD_BEFORE_PHASE_2_6_FINAL_MASTER_GATE`
