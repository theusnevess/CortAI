# Video QC Agent v2.6 Excellence Plan

## 1. Purpose

This document defines the formal Phase 2.6 excellence plan for the Video QC Agent.

The Video QC Agent is the fourth Wave 2 output agent. It consumes rendered video, audio, metadata, script text, TTS trace, visual trace, and edit trace where available, then emits the final product-quality decision used by the orchestrator.

This is not an implementation artifact.

This plan defines how Video QC must evolve from a functional post-render validator into an audit-grade, evidence-governed, confidence-aware, product-signal-explicit final quality authority.

## 2. Governance Context

The system remains under:

```json
{
  "system_version": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "governance_model": "SUBSYSTEM_BASELINE_WITH_MONITORING",
  "change_policy": "FROZEN_UNLESS_GOVERNANCE_REOPEN",
  "no_core_modification": true,
  "no_subsystem_mutation_without_reopen": true,
  "new_work_must_be_isolated_subsystems": true
}
```

Video QC v2.6 work must preserve:

- frozen core pipeline
- current orchestrator QC governance semantics
- Strategy ownership over creative control
- Script ownership over narrative text
- Voice ownership over voice planning
- Asset Selection ownership over visual selection
- Trend ownership over context
- Account Health upstream `SAFE / CAUTION / HOLD` authority
- Learning bounded pressure
- Experiment ownership
- Publisher out of scope
- no hidden publish behavior
- no repair or regeneration loop
- no provider expansion
- no fake confidence
- no fake product evidence
- no hidden fallback
- no downstream behavior changes without explicit governance

## 3. Current State

The Video QC subsystem is runtime-real and already integrated into the creative orchestrator.

Current capabilities include:

- `VideoQcInput` carries `render_job_id`, video path, audio path, metadata path, script text, `tts_trace`, `visual_trace`, and `edit_trace`.
- `VideoQcDecision` supports `APPROVE`, `HOLD`, and `REJECT`.
- `VideoQcDecision` exposes `publishable`, `hard_failures`, `soft_failures`, `product_vetoes`, `score_summary`, `product_signals`, `decision_trace`, and `checked_at`.
- `VideoQcResult` exposes `decision`, `status`, `reasons`, `checked_at`, `publishable`, and `details`.
- `VideoQcAgentService` evaluates final artifacts through the real service path.
- hard technical failures include missing render job id, missing video, missing audio, missing metadata, invalid subtitle cues, broken glyphs, payoff darkness, invalid resolution, and missing audio stream.
- product signals include hook quality, payoff quality, publishability signal, setup luma state, component quality scores, and overall score.
- `HOLD` is already represented for borderline product-quality conditions.
- the orchestrator applies QC governance after render: `APPROVE` finalizes publish state, while `HOLD` and `REJECT` mark output non-publishable and remove publish manifest from the returned pipeline output.
- QC emits creative events through the orchestrator.

Current limitations for Phase 2.6:

- input and artifact observability is not yet audit-grade.
- technical checks have reason codes but not full severity/evidence rationale.
- product signals are computed but not fully explained.
- `decision_trace` is shallow and not reconstructible enough.
- layer attribution is implicit.
- environment fallback, such as `ffprobe` absence and metadata fallback, is not clearly separated from full media probing.
- confidence is not calibrated as trust in the QC decision.
- missing traces from Script, Voice, Asset, and Editor are not consistently exposed as limited evidence.
- no consolidated `qc_trace` exists.

## 4. Objective

Video QC v2.6 must make final output validation more:

- input-governed
- artifact-evidence aware
- technical-check explicit
- product-signal explicit
- decision-semantics clear
- severity-aware
- layer-attributed when evidence supports it
- fallback/environment honest
- confidence-calibrated
- traceable end-to-end
- ready for v3 with monitoring

The goal is to improve reliability, explainability, and auditability of final product-quality decisions.

The goal is not to make QC a repair engine, Publisher, Strategy layer, renderer, editor, model-based critic, or performance predictor.

## 5. Scope

In scope:

- QC input and artifact governance.
- artifact presence and metadata evidence trace.
- technical validation rationale and severity.
- bounded product signal rationale.
- `APPROVE / HOLD / REJECT` decision semantics.
- publishability flag rationale.
- layer attribution to Script, Voice, Asset, Editor, Render, Pipeline, or Environment where evidence supports it.
- fallback and environment honesty.
- confidence calibration for trust in QC decision.
- consolidated `qc_trace`.
- Video QC v2.6 excellence gate.

Out of scope:

- core pipeline changes.
- Strategy behavior changes.
- Script behavior changes.
- Voice behavior changes.
- Asset Selection behavior changes.
- Trend behavior changes.
- Account Health behavior changes.
- Experiment behavior changes.
- Publisher implementation.
- changing current orchestrator QC governance semantics.
- rewriting script.
- resynthesizing voice.
- selecting replacement assets.
- re-editing video.
- rerendering video.
- adding computer vision, image ML, audio ML, or performance prediction.
- introducing subjective taste claims without evidence.

## 6. Boundary Rules

Video QC may:

- inspect final rendered artifacts.
- inspect metadata emitted by the pipeline.
- inspect supplied `tts_trace`, `visual_trace`, and `edit_trace`.
- compute deterministic technical and product-signal checks.
- issue `APPROVE`, `HOLD`, or `REJECT`.
- declare `publishable` based on QC status and product signals.
- explain why output is not publishable.
- attribute findings to layers when evidence is available.
- expose confidence as trust in the QC decision.

Video QC must not:

- rewrite Script.
- regenerate Voice.
- replace Assets.
- modify EditPlan.
- rerender content.
- execute publishing.
- implement Publisher.
- override Strategy.
- override Account Health.
- create Learning policy.
- fabricate traces.
- fabricate ffprobe/media evidence.
- treat metadata fallback as full media inspection.
- claim human-level visual or audio judgment without real evidence.
- predict content performance.

## 7. Required Workstream Order

Video QC v2.6 must be implemented in bounded workstreams:

1. QC Input And Artifact Governance
2. Technical Validation Rationale Hardening
3. Product Signal Rationale Hardening
4. Decision Semantics And Severity Hardening
5. Layer Attribution Hardening
6. Fallback And Environment Honesty
7. Confidence Calibration
8. Trace And Auditability Hardening
9. Video QC Excellence Gate

Do not implement all workstreams at once.

Each workstream must pass focused validation before the next workstream begins.

## 8. Workstream 1: QC Input And Artifact Governance

### Goal

Make QC input intake explicit, bounded, and auditable.

### Required Behavior

Video QC must identify which input and artifact classes are:

- available
- used
- missing
- degraded
- ignored
- environment-dependent

Expected input classes:

- render_job_id
- video_artifact
- audio_artifact
- metadata_artifact
- script_text
- tts_trace
- visual_trace
- edit_trace
- media_probe_capability
- metadata_fallback_probe

### Required Output

Additive structure:

```json
{
  "qc_input_governance": {
    "governance_version": "qc_input_governance_v2_6",
    "available_inputs": [],
    "used_inputs": [],
    "missing_inputs": [],
    "degraded_inputs": [],
    "ignored_inputs": [],
    "input_priority": [],
    "artifact_summary": {},
    "environment_summary": {},
    "policy_respected": true,
    "boundary_statement": "Video QC evaluates final artifacts only; it does not repair or publish.",
    "rationale": []
  }
}
```

### Constraints

- Do not change QC decision logic in this workstream.
- Do not change artifact probing behavior.
- Do not fabricate missing paths or trace data.
- Do not hide missing `tts_trace`, `visual_trace`, or `edit_trace`.

### Validation

Focused tests must prove input availability, missing inputs, degraded inputs, environment fallback, and serialization are explicit.

## 9. Workstream 2: Technical Validation Rationale Hardening

### Goal

Make each technical QC check explicit with severity, evidence, and rationale.

### Required Checks

Existing checks must be represented without changing behavior:

- render job id presence
- video artifact presence and non-empty size
- audio artifact presence and non-empty size
- metadata presence
- render duration minimum
- subtitle cue count validity
- subtitle cue text validity
- broken glyph detection
- payoff darkness via metadata luma proxy
- resolution validation
- audio stream validation
- media probe mode

### Required Output

Additive structure:

```json
{
  "technical_validation": {
    "validation_version": "qc_technical_validation_v2_6",
    "checks": {
      "video_artifact": {
        "passed": true,
        "severity": "none | low | medium | high | critical",
        "reason_code": "...",
        "evidence": {},
        "rationale": []
      }
    },
    "hard_failures": [],
    "technical_valid": true,
    "rationale": []
  }
}
```

### Constraints

- Do not add hidden thresholds.
- Do not weaken existing hard failures.
- Do not convert product weaknesses into technical failures without evidence.
- Do not treat metadata fallback as equivalent to full media probe.

### Validation

Focused tests must cover clean artifacts, missing metadata, missing audio, bad resolution, subtitle errors, broken glyphs, payoff darkness, and media probe fallback.

## 10. Workstream 3: Product Signal Rationale Hardening

### Goal

Make existing product-signal scoring explainable and bounded.

### Required Signals

Existing product signals must be explained:

- script_quality
- voice_quality
- asset_quality
- edit_quality
- hook_quality
- payoff_quality
- product_quality
- publishability_signal
- overall_score
- setup_luma_ok

### Required Output

Additive structure:

```json
{
  "product_signal_analysis": {
    "analysis_version": "qc_product_signal_v2_6",
    "signals": {
      "hook_quality": {
        "score": 0.0,
        "level": "low | medium | high",
        "evidence": {},
        "reason_codes": [],
        "rationale": []
      }
    },
    "score_summary": {},
    "product_signals": {},
    "boundedness_statement": "Product signals are deterministic proxies, not performance predictions.",
    "rationale": []
  }
}
```

### Constraints

- Do not claim human-level taste.
- Do not use ML.
- Do not predict performance.
- Do not change existing score math in this workstream.
- Do not replace Script, Voice, Asset, or Editor judgments.

### Validation

Focused tests must prove product-signal rationale exists, varies across controlled cases, and remains deterministic.

## 11. Workstream 4: Decision Semantics And Severity Hardening

### Goal

Make `APPROVE / HOLD / REJECT`, `publishable`, hard failures, soft failures, and product vetoes fully auditable.

### Required Semantics

`APPROVE`:

- no hard failures
- no product vetoes
- no soft failures
- `publishable = true`
- final output is eligible for current orchestrator publish-finalization path

`HOLD`:

- no hard technical failure
- one or more bounded soft failures
- product quality is borderline or requires review
- `publishable = false`
- current orchestrator non-publishable path remains preserved

`REJECT`:

- hard technical failure or product veto exists
- output is invalid or below minimum product threshold
- `publishable = false`
- current orchestrator non-publishable path remains preserved

### Required Output

Additive structure:

```json
{
  "decision_semantics": {
    "status": "APPROVE | HOLD | REJECT",
    "publishable": false,
    "hard_failures": [],
    "soft_failures": [],
    "product_vetoes": [],
    "severity_level": "none | low | medium | high | critical",
    "dominant_reason_codes": [],
    "decision_rule_applied": "...",
    "rationale": []
  }
}
```

### Constraints

- Do not change status thresholds in this workstream unless explicitly scoped and tested.
- Do not introduce hidden publish enforcement.
- Do not alter orchestrator/core publish order.
- Do not overblock without evidence.

### Validation

Focused tests must cover clean `APPROVE`, borderline `HOLD`, technical `REJECT`, product-veto `REJECT`, and publishability flag consistency.

## 12. Workstream 5: Layer Attribution Hardening

### Goal

Link QC findings to the producing layer when evidence supports attribution.

### Attribution Targets

Allowed attribution targets:

- script
- voice
- asset
- editor
- render
- pipeline
- environment
- unknown

### Required Output

Additive structure:

```json
{
  "layer_attribution": {
    "attribution_complete": true,
    "findings": [
      {
        "reason_code": "...",
        "layer": "script | voice | asset | editor | render | pipeline | environment | unknown",
        "evidence": {},
        "confidence": "low | medium | high",
        "rationale": []
      }
    ],
    "unattributed_findings": [],
    "boundary_statement": "QC attributes findings for audit only; it does not mutate upstream outputs."
  }
}
```

### Rules

- Missing audio file may attribute to pipeline/render/voice only when evidence supports it.
- Subtitle cue issues may attribute to editor/render unless metadata indicates another source.
- Hook/payoff text proxy issues may attribute to script/editor only with available script/cue evidence.
- Asset luma issues may attribute to asset/editor/render depending on metadata evidence.
- Unknown must be used when evidence is insufficient.

### Constraints

- Do not assign blame without evidence.
- Do not mutate upstream outputs.
- Do not create hidden repair instructions.

### Validation

Focused tests must prove attribution exists, unknown is used honestly, and attribution does not rewrite outputs.

## 13. Workstream 6: Fallback And Environment Honesty

### Goal

Expose environment-dependent and fallback-derived QC evidence.

### Required Behavior

Video QC must distinguish:

- full media probe available
- `ffprobe` unavailable
- metadata fallback probe used
- metadata missing
- trace missing
- trace partial
- environment limited
- artifact unobservable

### Required Output

Additive structure:

```json
{
  "qc_fallback_environment": {
    "media_probe_mode": "ffprobe | metadata_fallback | unavailable",
    "metadata_fallback_used": false,
    "tts_trace_available": true,
    "visual_trace_available": true,
    "edit_trace_available": true,
    "environment_limitations": [],
    "fallback_evidence_used": [],
    "rationale": []
  }
}
```

### Constraints

- Do not fabricate ffprobe evidence.
- Do not hide metadata fallback.
- Do not treat missing trace as clean evidence.
- Do not fail closed solely because optional traces are missing unless the decision requires them.

### Validation

Focused tests must cover ffprobe unavailable, metadata fallback, missing trace, partial trace, and missing metadata.

## 14. Workstream 7: Confidence Calibration

### Goal

Add confidence as a trust signal for the QC decision.

Confidence must answer:

> How much can the system trust that this QC decision is supported by available artifact, metadata, trace, and product-signal evidence?

Confidence must not answer:

> How likely is the video to perform?

### Required Components

Confidence may consider:

- artifact_evidence_completeness
- technical_validation_completeness
- product_signal_coverage
- trace_evidence_quality
- media_probe_quality
- decision_consistency
- fallback_environment_penalty
- missing_trace_penalty

### Required Output

```json
{
  "confidence": 0.0,
  "confidence_level": "low | medium | high",
  "confidence_components": {
    "artifact_evidence_completeness": 0.0,
    "technical_validation_completeness": 0.0,
    "product_signal_coverage": 0.0,
    "trace_evidence_quality": 0.0,
    "media_probe_quality": 0.0,
    "decision_consistency": 0.0,
    "fallback_environment_penalty": 0.0
  },
  "confidence_rationale": {
    "confidence_meaning": "trust_in_qc_decision",
    "penalties": [],
    "boundary_statement": "QC confidence is not performance prediction."
  }
}
```

### Rules

- Confidence must be deterministic.
- Confidence must not be constant.
- Confidence must decrease under missing artifacts, missing metadata, missing traces, metadata fallback, partial evidence, and internal errors.
- Confidence may be high for clean technical decisions with complete evidence.
- Confidence may be high for clear technical reject if evidence is complete.
- Confidence must not be high for ambiguous `HOLD` with partial evidence.
- Confidence must not decide publishability by itself.

### Validation

Focused tests must cover high-confidence approve, high-confidence hard reject, lower-confidence hold, missing metadata, metadata fallback, missing traces, and deterministic replay.

## 15. Workstream 8: Trace And Auditability Hardening

### Goal

Create a consolidated `qc_trace` that allows an auditor to reconstruct why QC returned `APPROVE`, `HOLD`, or `REJECT`.

### Required Trace

```json
{
  "qc_trace": {
    "qc_input_governance": {},
    "technical_validation": {},
    "product_signal_analysis": {},
    "decision_semantics": {},
    "layer_attribution": {},
    "qc_fallback_environment": {},
    "confidence_calibration": {},
    "final_qc_decision_rationale": {},
    "missing_or_degraded_inputs": [],
    "audit_summary": {}
  }
}
```

### Required Final Rationale

Must answer:

- what artifacts were evaluated.
- which technical checks passed or failed.
- which product signals influenced the decision.
- why status is `APPROVE`, `HOLD`, or `REJECT`.
- why publishable is true or false.
- which layer likely produced each issue.
- whether media probe was full or fallback-based.
- whether upstream traces were available.
- how trustworthy the QC decision is.

### Required Audit Summary

```json
{
  "reconstructible": true,
  "required_sections_present": true,
  "decision_explained": true,
  "publishability_explained": true,
  "fallback_environment_visible": true,
  "confidence_explained": true,
  "boundary_preserved": true,
  "silent_failure_indicators": []
}
```

### Constraints

- Do not recalculate the QC decision.
- Do not change `APPROVE / HOLD / REJECT`.
- Do not fake reconstructibility.
- Do not remove existing fields.
- Do not hide missing or degraded evidence.

### Validation

Focused tests must prove `qc_trace` reconstructs approve, hold, reject, technical failure, product veto, and fallback/environment cases.

## 16. Workstream 9: Video QC Excellence Gate

### Required Artifacts

Create:

- `docs/runtime/phase-2-6/agents/video-qc/VIDEO_QC_AGENT_V2_6_EXCELLENCE_GATE.md`
- `tests/gates/agents/video_qc/run_video_qc_agent_v2_6_excellence_gate.py`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json`

Recommended:

- `OUT/audit/video_qc_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/metrics.json`

### Required Gate Dimensions

The gate must validate:

- runtime_real
- input_governed
- technical_validation_explicit
- product_signals_explicit
- decision_semantics_explicit
- layer_attribution_explicit
- fallback_environment_honest
- confidence_calibrated
- traceability_complete
- approve_hold_reject_semantics_preserved
- publishability_semantics_preserved
- orchestrator_qc_governance_preserved
- boundary_preserved
- determinism_where_required
- backward_compatible
- silent_failures_detected false

### Required Scenarios

At minimum:

1. clean rendered output -> `APPROVE`
2. missing metadata -> `REJECT`
3. missing video -> `REJECT`
4. missing audio -> `REJECT`
5. invalid subtitle cues -> `REJECT`
6. broken glyph -> `REJECT`
7. payoff too dark -> `REJECT`
8. borderline hook/payoff -> `HOLD`
9. low product signal with no hard failure -> `HOLD` or `REJECT` according to existing decision semantics
10. metadata fallback probe visible
11. missing optional traces visible
12. layer attribution unknown when evidence is insufficient
13. deterministic replay
14. backward compatibility
15. orchestrator approve path finalizes publish state
16. orchestrator hold/reject path remains non-publishable

### Verdict Rules

`HOLD` if:

- QC cannot execute through real service.
- required trace sections are missing.
- confidence is fake or constant.
- missing artifact evidence is hidden.
- metadata fallback is hidden.
- `APPROVE / HOLD / REJECT` semantics regress.
- `publishable` is inconsistent with status.
- orchestrator QC governance regresses.
- QC rewrites upstream outputs.
- QC becomes Publisher.
- core pipeline is modified.
- deterministic replay fails without explanation.
- boundary violation exists.
- silent failure is detected.

`GO_WITH_MONITORING` if:

- all critical checks pass.
- remaining residues are explicit, bounded, and tied to runtime media-probe coverage, product-signal calibration horizon, or limited longitudinal QC history.

`GO` only if:

- all checks pass and no meaningful residual monitoring remains.

## 17. Required Output By End Of Video QC v2.6

`VideoQcResult`, `VideoQcDecision`, or nested details/trace should expose additive fields such as:

- `qc_input_governance`
- `technical_validation`
- `product_signal_analysis`
- `decision_semantics`
- `layer_attribution`
- `qc_fallback_environment`
- `confidence`
- `confidence_level`
- `confidence_components`
- `confidence_rationale`
- `qc_trace`

Do not remove existing fields:

- `decision`
- `status`
- `reasons`
- `checked_at`
- `publishable`
- `details`

Do not break existing fields:

- `VideoQcDecision.status`
- `VideoQcDecision.publishable`
- `VideoQcDecision.hard_failures`
- `VideoQcDecision.soft_failures`
- `VideoQcDecision.product_vetoes`
- `VideoQcDecision.score_summary`
- `VideoQcDecision.product_signals`
- `VideoQcDecision.decision_trace`

## 18. Test Strategy

Focused workstream tests must be created as each implementation step begins.

Expected test families:

- `tests/agents/video_qc/test_video_qc_input_governance_unittest.py`
- `tests/test_video_qc_technical_validation_unittest.py`
- `tests/test_video_qc_product_signal_rationale_unittest.py`
- `tests/agents/video_qc/test_video_qc_decision_semantics_unittest.py`
- `tests/test_video_qc_layer_attribution_unittest.py`
- `tests/test_video_qc_fallback_environment_unittest.py`
- `tests/test_video_qc_confidence_calibration_unittest.py`
- `tests/agents/video_qc/test_video_qc_trace_auditability_unittest.py`
- `tests/gates/agents/video_qc/run_video_qc_agent_v2_6_excellence_gate.py`

Existing relevant tests must continue to pass, including:

- `tests/agents/video_qc/test_video_qc_agent_phase2_unittest.py`
- `tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py`
- `tests/content/test_content_pipeline_d27_unittest.py`
- `tests/agents/script/test_script_agent_phase2_unittest.py`
- `tests/agents/voice/test_voice_agent_phase2_unittest.py`
- `tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py`
- `tests/agents/trend_analysis/test_trend_analysis_agent_phase2_unittest.py`
- `tests/agents/strategy/test_strategy_agent_phase2_unittest.py`
- `tests/experiment/test_experiment_capability_phase2_unittest.py`

## 19. Failure Conditions

Video QC v2.6 must pause if any of the following occurs:

- hidden missing artifact.
- hidden metadata fallback.
- hidden missing trace.
- fake confidence.
- confidence high under ambiguous partial evidence.
- `APPROVE` with hard failures.
- `HOLD` marked publishable.
- `REJECT` marked publishable.
- product veto treated as clean approve.
- hard technical failure treated as soft warning.
- layer attribution fabricated.
- QC rewrites Script, Voice, Asset, or Edit output.
- QC rerenders content.
- QC implements Publisher.
- core pipeline is changed without governance reopen.
- orchestrator QC governance regresses.
- `qc_trace.audit_summary.reconstructible = true` while required sections are missing.
- existing QC/orchestrator/pipeline tests regress.

## 20. Residual Monitoring Candidates

Acceptable non-structural residuals may include:

- `VIDEO_QC_RUNTIME_HISTORY_STILL_SHORT`
- `VIDEO_QC_PRODUCT_SIGNAL_CALIBRATION_STILL_MATURING`
- `VIDEO_QC_MEDIA_PROBE_COVERAGE_ENVIRONMENT_DEPENDENT`
- `VIDEO_QC_LAYER_ATTRIBUTION_EVIDENCE_STILL_LIMITED`
- `VIDEO_QC_LONGITUDINAL_PRODUCT_OUTCOME_HISTORY_STILL_SHORT`

These are acceptable only if:

- they are explicit.
- they are non-structural.
- they do not hide missing trace, fake confidence, or broken decisions.
- they do not affect boundary preservation.
- they do not mask publishability inconsistency.

Structural blockers must not be reclassified as residual monitoring.

## 21. Exit Criteria

Video QC v2.6 is complete only when:

- input/artifact governance is explicit.
- technical validation rationale is explicit.
- product signal rationale is explicit and bounded.
- decision semantics are clear.
- severity is visible.
- layer attribution is evidence-backed or honestly unknown.
- fallback/environment limitations are visible.
- confidence is calibrated as trust in QC decision.
- `qc_trace` reconstructs `APPROVE / HOLD / REJECT`.
- publishability rationale is explicit.
- current orchestrator QC governance remains stable.
- existing `VideoQcResult` compatibility is preserved.
- Script, Voice, Asset, Trend, Strategy, Account Health, Learning, Experiment, Publisher, and core boundaries remain stable.
- dedicated Video QC v2.6 gate passes.

## 22. Current Authorized Next Step

The first implementation workstream after this plan is:

```text
Video QC Agent v2.6 - QC Input And Artifact Governance
```

Allowed scope:

- inspect `VideoQcInput`, `VideoQcDecision`, `VideoQcResult`, and `VideoQcAgentService`.
- add additive input/artifact governance structures.
- expose available, used, missing, degraded, ignored, and environment-dependent inputs.
- expose artifact and trace availability.
- preserve existing `APPROVE / HOLD / REJECT`.
- preserve existing `publishable` behavior.
- preserve current orchestrator/core/pipeline behavior.

Forbidden in the first workstream:

- confidence calibration.
- product-signal redesign.
- technical threshold changes.
- decision semantics changes.
- layer attribution.
- trace consolidation.
- core pipeline changes.
- orchestrator behavior changes.
- Publisher behavior.

## 23. Final Principle

Video QC Agent v2.6 must make final product-quality decisions explainable and evidence-backed.

It must not become a repair engine, hidden Publisher, Strategy layer, or performance prediction system.
