# VIDEO_QC_AGENT_V2_6_EXCELLENCE_GATE

## 1. Purpose

`VIDEO_QC_AGENT_V2_6_EXCELLENCE_GATE` is the formal validation gate for the Video QC Agent after the Phase 2.6 output-excellence hardening workstreams.

This gate validates Video QC v2.6 as implemented. It must not mutate runtime behavior to make validation pass.

The gate determines whether Video QC is:

- runtime-real
- input and artifact governed
- evidence-scoring explicit
- confidence-calibrated as trust in the QC decision
- decision-semantics and severity explicit
- traceable end-to-end through `qc_trace`
- deterministic under controlled inputs
- boundary-preserving
- free of silent failures

This gate is an audit artifact, not a feature. It can produce `GO`, `GO_WITH_MONITORING`, or `HOLD`.

## 2. Scope

In scope:

- `VideoQcAgentService` execution
- `APPROVE / HOLD / REJECT` semantics
- `publishable` semantics
- `qc_input_governance`
- `qc_evidence_scoring`
- `confidence_calibration`
- `decision_semantics`
- `qc_trace`
- missing/degraded/ignored input visibility
- metadata fallback and media-probe environment visibility
- orchestrator QC governance preservation
- Strategy/core boundary preservation
- deterministic replay
- backward-compatible `VideoQcResult`

Out of scope:

- changing QC decision logic
- changing thresholds or score math
- changing `publishable`
- changing product signals
- changing Strategy
- changing the orchestrator
- changing the core pipeline
- adding Publisher behavior
- adding repair, rerender, rewrite, asset replacement, or resynthesis
- adding performance prediction
- adding ML/audio/video pixel inspection

## 3. Preconditions

Required workstreams:

- QC Input And Artifact Governance
- Confidence And Evidence Scoring Hardening
- Decision Semantics And Severity Hardening
- Trace And Auditability Hardening

Required code surfaces:

- `backend/app/creative/agents/video_qc/models.py`
- `backend/app/creative/agents/video_qc/service.py`
- `backend/app/creative/agents/video_qc/input_governance.py`
- `backend/app/creative/agents/video_qc/confidence_evidence.py`
- `backend/app/creative/agents/video_qc/decision_semantics.py`
- `backend/app/creative/agents/video_qc/trace_auditability.py`

Required validation command:

`python tests/gates/agents/video_qc/run_video_qc_agent_v2_6_excellence_gate.py`

Required output artifact:

`OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json`

## 4. Evaluation Dimensions

`runtime_real`

Means Video QC executes through `VideoQcAgentService`, not fabricated result objects.

Failure if service execution is skipped, result payloads are fabricated, or exceptions are hidden as success.

`input_governed`

Means input availability, usage, missing/degraded/ignored state, and environment dependency are explicit.

Failure if missing metadata, missing artifacts, missing traces, or metadata fallback are hidden.

`evidence_scoring_complete`

Means existing score evidence and failure categories are visible without changing score math.

Failure if scores lack evidence rationale, failure categories are missing, or product evidence is treated as performance prediction.

`confidence_honest`

Means confidence measures `trust_in_qc_decision`, varies across scenarios, and drops under missing/fallback/ambiguous evidence.

Failure if confidence is constant, high under metadata fallback or borderline `HOLD`, lacks rationale, or claims performance prediction.

`decision_semantics_explicit`

Means `APPROVE / HOLD / REJECT`, `blocker`, `warning`, `monitorable`, severity, and publishability rationale are explicit.

Failure if hard failures are not blockers, soft failures are treated as blockers, `HOLD` becomes publishable, or `REJECT` becomes publishable.

`qc_trace_reconstructible`

Means `qc_trace` consolidates input governance, evidence scoring, confidence, decision semantics, final rationale, missing/degraded inputs, and audit summary.

Failure if required sections are missing, reconstructibility is faked, confidence is inconsistent, or decision trace contradicts the result.

`approve_hold_reject_semantics_preserved`

Means the current status behavior remains stable for clean approve, borderline hold, technical reject, perceptual reject, and product-veto reject.

Failure if any controlled scenario returns an unexpected status.

`publishability_semantics_preserved`

Means `APPROVE` may be publishable, while `HOLD` and `REJECT` remain non-publishable.

Failure if `HOLD` or `REJECT` is publishable, or clean `APPROVE` is non-publishable without an explicit existing reason.

`orchestrator_qc_governance_preserved`

Means existing orchestrator tests still pass and downstream publish/non-publish paths remain governed by QC status.

Failure if orchestrator phase2 tests fail or publish behavior is changed by this gate.

`boundary_preserved`

Means Video QC remains final artifact evaluator and does not become Strategy, Publisher, renderer, editor, Script, Voice, or Asset.

Failure if QC emits Strategy commands, publishes, repairs, rerenders, rewrites, resynthesizes, replaces assets, or predicts performance.

`determinism_where_required`

Means identical controlled inputs produce stable status, publishable, confidence, evidence scoring, decision semantics, and `qc_trace`.

Failure if stable fields drift without input changes.

`silent_failures_detected`

Means missing trace sections, hidden fallback, fake confidence, hidden degraded input, publishability inconsistency, and boundary violations are blockers.

Failure if any critical defect is present while the verdict passes.

## 5. Controlled Scenario Battery

The runner executes controlled scenarios through `VideoQcAgentService`.

Required scenarios:

- `clean_approve`
- `borderline_hold`
- `missing_metadata_reject`
- `missing_video_reject`
- `missing_audio_reject`
- `invalid_subtitle_cues_reject`
- `broken_glyph_reject`
- `payoff_too_dark_reject`
- `product_veto_reject`
- `metadata_fallback_visible`
- `missing_optional_traces_visible`
- `determinism_replay`
- `backward_compatibility`

Controlled media-probe subclasses may be used only to make `ffprobe` environment paths deterministic. They must still execute the real `VideoQcAgentService.evaluate` path and must not fabricate final `VideoQcResult` objects.

## 6. Checklist

The runner validates:

- required files exist
- service execution is real
- required public fields exist
- `qc_input_governance` is complete
- `qc_evidence_scoring` is complete
- confidence is calibrated and non-constant
- confidence has correct meaning
- metadata fallback lowers confidence
- `HOLD` is not high confidence
- reason codes are classified by category and disposition
- blockers/warnings/monitorables are explicit
- `qc_trace` required sections are present
- `qc_trace.audit_summary.reconstructible` is honest
- `decision_trace` remains backward-compatible and includes additive audit sections
- `publishable` is consistent with status
- orchestrator, Strategy, and pipeline tests pass
- no forbidden performance-prediction keys appear
- no silent failure indicators are present in passing scenarios

Any failed critical checklist item becomes a blocking failure.

## 7. Verdict Semantics

`HOLD`

Required if any critical failure, blocking failure, fake confidence, silent failure, boundary violation, non-determinism, missing trace section, publishability inconsistency, orchestrator regression, Strategy/core regression, or performance-prediction field is detected.

`GO_WITH_MONITORING`

Allowed when all critical checks pass and remaining residues are explicit, bounded, and non-structural.

Expected acceptable residuals:

- `VIDEO_QC_RUNTIME_HISTORY_STILL_SHORT`
- `VIDEO_QC_PRODUCT_SIGNAL_CALIBRATION_STILL_MATURING`
- `VIDEO_QC_MEDIA_PROBE_COVERAGE_ENVIRONMENT_DEPENDENT`
- `VIDEO_QC_LAYER_ATTRIBUTION_EVIDENCE_STILL_LIMITED`

`GO`

Allowed only if all checks pass and no meaningful residual monitoring remains.

## 8. Failure Conditions

Critical failures include:

- service cannot execute
- status semantics regress
- `publishable` semantics regress
- confidence is fake or constant
- confidence is high under metadata fallback or ambiguous `HOLD`
- score evidence lacks rationale
- reason codes lack semantic classification
- `qc_trace` is missing or not reconstructible
- missing/degraded input is hidden
- metadata fallback is hidden
- decision trace contradicts final result
- orchestrator/Strategy/core tests fail
- QC creates publishability logic beyond existing behavior
- QC predicts performance
- QC mutates upstream outputs
- silent failure indicators are present

## 9. Output Artifacts

The runner writes:

- `OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/metrics.json`

## 10. Final Criteria

Video QC v2.6 passes this gate only if:

- `APPROVE / HOLD / REJECT` are preserved
- `publishable` is preserved
- confidence is honest and evidence-backed
- evidence scoring is complete enough to audit emitted scores
- severity semantics are correct
- `qc_trace` reconstructs why the result was emitted
- missing/degraded/fallback evidence is visible
- no Strategy/orchestrator/core behavior changes occur
- no new publishability authority is created
- no performance prediction is introduced
- no silent failures are detected

Final principle:

Video QC does not decide better in this gate. It proves whether it explains its existing decisions well enough to deserve release.
