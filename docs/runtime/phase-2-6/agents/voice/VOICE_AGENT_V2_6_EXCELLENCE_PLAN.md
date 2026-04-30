# Voice Agent v2.6 Excellence Plan

## 1. Purpose

This document defines the formal Phase 2.6 excellence plan for the Voice Agent.

The Voice Agent is the second Wave 2 output agent. It consumes `ScriptPlan` and bounded Strategy context, then produces a `VoicePlan` for downstream TTS execution through the existing pipeline router.

This is not an implementation artifact.

This plan defines how Voice must evolve from a functional provider-routing surface into an audit-grade, segment-aware, fallback-honest, confidence-aware voice delivery planning subsystem.

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

Voice v2.6 work must preserve:

- frozen core pipeline
- TTS Router ownership over provider execution
- Kokoro as current local primary provider
- Piper as hard fallback
- Script ownership over narrative text
- Strategy ownership over creative control
- Asset ownership over visual selection
- QC ownership over product-quality validation
- Experiment ownership
- no Publisher work
- no provider expansion unless a later explicit gated provider plan authorizes it
- no hidden audio enforcement
- no fake confidence
- no fake perceptual claims
- no direct runtime synthesis inside the Voice Agent

## 3. Current State

The Voice subsystem is already operational after Phase 2.5A and Phase 2.5B.

Current capabilities include:

- `VoicePlan` exists and is operative.
- `VoiceInterpreter` exists and is deterministic/rule-based.
- `TtsRouter` is the canonical provider execution router.
- Kokoro is the current local primary provider.
- Piper remains fallback.
- `VoicePlan.provider` is no longer decorative.
- `VoicePlan.runtime_constraints.fallback_order` is present.
- Segment plans exist for `hook`, `setup`, and `payoff`.
- The pipeline can materialize `tts_trace` with requested/executed provider and fallback state.

Current limitations for Phase 2.6:

- requested vs executed provider is traceable in pipeline, but not yet consolidated at Voice Agent level.
- delivery intent is implicit in deterministic interpreter rules.
- segment-level timing rationale is shallow.
- monotony/contrast analysis is not audit-grade.
- voice confidence is not calibrated as trust in voice plan construction or execution readiness.
- fallback and provider metadata are not yet consolidated into a reconstructible `voice_trace`.
- audio validation remains primarily pipeline-side and should be linked without moving synthesis into Voice.

## 4. Objective

Voice v2.6 must make voice planning more:

- contract-governed
- segment-aware
- timing-aware
- monotony/contrast-aware through bounded proxies
- provider/fallback honest
- audio-validation aware
- confidence-calibrated
- traceable end-to-end
- ready for v3 with monitoring

The goal is to improve delivery reliability, auditability, and alignment with Script intent.

The goal is not to make Voice a synthesis engine, provider marketplace, Strategy layer, QC judge, publisher, or performance predictor.

## 5. Scope

In scope:

- Voice plan contract audit and additive trace fields.
- requested vs planned provider semantics.
- segment-level delivery intent for hook/setup/payoff.
- deterministic timing and pause rationale.
- bounded monotony and contrast analysis.
- provider and fallback honesty.
- audio validation linkage where existing pipeline artifacts allow it.
- confidence calibration for trust in voice plan construction/execution readiness.
- consolidated `voice_trace`.
- Voice v2.6 excellence gate.

Out of scope:

- modifying the core pipeline.
- changing `TtsRouter` provider order unless a focused workstream explicitly audits metadata without behavior change.
- adding new TTS providers.
- cloud/provider benchmarking expansion.
- voice cloning.
- emotion engine redesign.
- changing Script text.
- changing Strategy behavior.
- changing Asset behavior.
- changing QC behavior.
- changing publish manifest semantics.
- generating audio directly inside the Voice Agent.
- predicting performance.

## 6. Boundary Rules

Voice may:

- interpret `ScriptPlan` structure into delivery intent.
- use Strategy as bounded context for style/rate where already available.
- produce a `VoicePlan`.
- describe requested provider, fallback order, delivery profile, segment timing, and voice-plan confidence.
- consume or link existing pipeline `tts_trace` in audit contexts when available.

Voice must not:

- rewrite script text.
- choose assets.
- decide Strategy.
- decide QC outcome.
- decide publishability.
- execute TTS directly.
- create or add providers.
- bypass `TtsRouter`.
- hide fallback.
- claim perceptual excellence without evidence.
- treat fallback execution as clean primary execution.

## 7. Required Workstream Order

Voice v2.6 must be implemented in bounded workstreams:

1. Voice Plan Contract Governance
2. Delivery Profile Semantics
3. Segment Timing And Pause Hardening
4. Monotony And Contrast Analysis
5. Provider And Fallback Honesty
6. Audio Validation Linkage
7. Confidence Calibration
8. Trace And Auditability Hardening
9. Voice Excellence Gate

Do not implement all workstreams at once.

Each workstream must pass focused validation before the next workstream begins.

## 8. Workstream 1: Voice Plan Contract Governance

### Goal

Make the `VoicePlan` contract explicit, validated, and audit-friendly without changing provider execution.

### Required Behavior

The Voice Agent must expose:

- provider requested by Voice.
- voice id requested by Voice.
- style requested by Voice.
- runtime fallback order.
- delivery profile completeness.
- segment plan completeness.
- missing/degraded contract fields.
- contract compatibility status.

### Required Output

Additive structure:

```json
{
  "voice_plan_governance": {
    "contract_version": "voice_plan_governance_v2_6",
    "contract_complete": true,
    "provider_requested": "kokoro",
    "voice_id_requested": "...",
    "style_requested": "...",
    "fallback_order": ["kokoro", "piper"],
    "segments_present": ["hook", "setup", "payoff"],
    "missing_fields": [],
    "degraded_fields": [],
    "boundary_statement": "Voice plans delivery only; TTS Router executes providers.",
    "rationale": []
  }
}
```

### Constraints

- Do not add providers.
- Do not change provider order.
- Do not modify TTS Router behavior.
- Do not mutate `VoicePlan` semantics beyond additive trace.

### Validation

Focused tests must prove the contract is complete, serializable, backward-compatible, and boundary-preserving.

## 9. Workstream 2: Delivery Profile Semantics

### Goal

Make delivery intent explicit for the emitted `VoicePlan`.

### Required Behavior

The Voice Agent must explain:

- why overall style was selected.
- why overall rate was selected.
- why overall intensity was selected.
- how hook/setup/payoff delivery roles differ.
- how Script context influenced delivery intent.
- whether Strategy context was used.

### Required Output

Additive structure:

```json
{
  "delivery_semantics": {
    "overall_mode": "...",
    "overall_rate": 0.97,
    "overall_intensity": "high",
    "segment_roles": {
      "hook": "attention_and_tension",
      "setup": "continuity_and_escalation",
      "payoff": "reveal_or_resolution"
    },
    "script_alignment": {...},
    "strategy_alignment": {...},
    "rationale": []
  }
}
```

### Constraints

- Keep deterministic rule-based semantics.
- Do not create freeform emotional generation.
- Do not predict performance.
- Do not change Script output.

## 10. Workstream 3: Segment Timing And Pause Hardening

### Goal

Make timing and pause decisions explicit and auditable.

### Required Behavior

The Voice Agent must explain:

- hook rate and pause.
- setup rate and pause.
- payoff rate and pause.
- before/after pause semantics.
- timing contrast between segments.
- missing timing evidence.

### Required Output

Additive structure:

```json
{
  "segment_timing_summary": {
    "segments": {
      "hook": {"rate": 0.93, "emphasis": "high", "pause_after_ms": 320},
      "setup": {"rate": 0.97, "emphasis": "medium", "pause_after_ms": 180},
      "payoff": {"rate": 0.90, "emphasis": "high", "pause_before_ms": 420}
    },
    "timing_contrast_present": true,
    "pause_profile_complete": true,
    "rationale": []
  }
}
```

### Constraints

- Do not alter audio files.
- Do not bypass TTS Router.
- Do not hide missing segment timing.

## 11. Workstream 4: Monotony And Contrast Analysis

### Goal

Add deterministic proxies for delivery monotony and contrast without claiming human perceptual certainty.

### Required Behavior

The Voice Agent must evaluate:

- rate variation.
- emphasis variation.
- pause variation.
- segment contrast strength.
- monotony risk.
- weak contrast warnings.

### Required Output

Additive structure:

```json
{
  "monotony_contrast_analysis": {
    "monotony_risk_level": "low | medium | high",
    "contrast_level": "low | medium | high",
    "rate_variation": 0.0,
    "emphasis_variation": true,
    "pause_variation_ms": 0,
    "reason_codes": [],
    "rationale": []
  }
}
```

### Constraints

- These are proxies, not perceptual truth.
- Do not use ML.
- Do not inspect audio waveform unless an explicit later workstream has real audio artifacts.
- Do not claim expected retention improvement.

## 12. Workstream 5: Provider And Fallback Honesty

### Goal

Make provider and fallback state explicit at Voice Agent level and compatible with pipeline `tts_trace`.

### Required Behavior

The Voice Agent must expose:

- provider requested.
- fallback order.
- provider execution responsibility boundary.
- known executed provider if pipeline trace is available.
- fallback used if pipeline trace is available.
- provider trace completeness.
- fallback reason if known.

### Required Output

Additive structure:

```json
{
  "provider_fallback_trace": {
    "provider_requested": "kokoro",
    "provider_executed": null,
    "execution_trace_available": false,
    "fallback_order": ["kokoro", "piper"],
    "fallback_allowed": true,
    "fallback_used": null,
    "fallback_reason": null,
    "boundary_statement": "Voice Agent requests provider; TTS Router executes provider.",
    "rationale": []
  }
}
```

### Constraints

- Do not fabricate executed provider when only `VoicePlan` exists.
- Do not fabricate latency or duration.
- Do not change provider order.
- Do not add providers.

## 13. Workstream 6: Audio Validation Linkage

### Goal

Link Voice planning to audio validation evidence when available, without moving synthesis into Voice.

### Required Behavior

The Voice Agent or an audit utility may summarize:

- audio trace present or absent.
- requested vs executed provider when `tts_trace` exists.
- duration available or missing.
- segment durations available or missing.
- fallback execution visible.
- validation limitations.

### Required Output

Additive structure:

```json
{
  "audio_validation_summary": {
    "audio_trace_available": false,
    "provider_execution_verified": false,
    "duration_available": false,
    "segment_durations_available": false,
    "validation_status": "not_available | partial | valid | degraded",
    "rationale": []
  }
}
```

### Constraints

- Voice Agent must not synthesize audio.
- Voice Agent must not inspect files unless provided with existing artifacts.
- Absence of audio trace must be explicit, not hidden.

## 14. Workstream 7: Confidence Calibration

### Goal

Add confidence as trust in voice plan construction and execution readiness.

Confidence must answer:

> How much can the system trust this voice plan and its execution readiness?

Confidence must not answer:

> How well will the video perform?

### Inputs

Confidence may consider:

- VoicePlan contract completeness.
- delivery semantics completeness.
- segment timing completeness.
- monotony/contrast proxy strength.
- provider/fallback trace completeness.
- audio validation linkage if available.
- missing or degraded fields.
- fallback visibility.

### Required Output

```json
{
  "confidence": 0.0,
  "confidence_level": "low | medium | high",
  "confidence_components": {
    "contract_completeness": 0.0,
    "delivery_semantics": 0.0,
    "timing_completeness": 0.0,
    "contrast_strength": 0.0,
    "provider_trace_quality": 0.0,
    "audio_validation_support": 0.0,
    "fallback_penalty": 0.0
  },
  "confidence_rationale": {
    "confidence_meaning": "trust_in_voice_plan_execution_readiness",
    "penalties": [],
    "boundary_statement": "Voice confidence is not performance prediction."
  }
}
```

### Constraints

- Confidence must not be constant.
- Confidence must decrease under fallback, missing provider execution evidence, incomplete segment plans, or weak contrast.
- Confidence must not override Strategy, Script, Asset, QC, or TTS Router.
- No fake confidence.

## 15. Workstream 8: Trace And Auditability Hardening

### Goal

Create a consolidated `voice_trace` that reconstructs why the `VoicePlan` was emitted.

### Required Trace

```json
{
  "voice_trace": {
    "voice_plan_governance": {...},
    "delivery_semantics": {...},
    "segment_timing_summary": {...},
    "monotony_contrast_analysis": {...},
    "provider_fallback_trace": {...},
    "audio_validation_summary": {...},
    "confidence_calibration": {...},
    "final_voice_plan_rationale": {...},
    "missing_or_degraded_inputs": [],
    "audit_summary": {...}
  }
}
```

### Required Final Rationale

Must answer:

- why this provider was requested.
- why this voice id was selected.
- why this style was selected.
- why segment delivery differs.
- whether fallback is allowed.
- whether execution evidence is available.
- how trustworthy the plan is.
- which inputs were missing or degraded.

### Constraints

- Do not recalculate provider execution.
- Do not synthesize audio.
- Do not change VoicePlan.
- Do not fake reconstructibility.

## 16. Workstream 9: Voice Excellence Gate

### Required Artifacts

Create:

- `docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_GATE.md`
- `tests/gates/agents/voice/run_voice_agent_v2_6_excellence_gate.py`
- `OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json`

Recommended:

- `OUT/audit/voice_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/metrics.json`

### Required Scenarios

At minimum:

1. `clean_kokoro_voice_plan`
2. `horror_high_tension_delivery`
3. `true_crime_investigative_delivery`
4. `missing_script_defaults_visible`
5. `weak_segment_contrast_detected`
6. `provider_trace_without_execution_is_honest`
7. `router_kokoro_success_if_available_or_classified`
8. `router_kokoro_to_piper_fallback`
9. `determinism_replay`
10. `backward_compatibility`

### Required Validations

The gate must prove:

- VoicePlan is complete and serializable.
- requested provider is explicit.
- fallback order is explicit.
- delivery semantics are segment-aware.
- timing and pause rationale are explicit.
- monotony/contrast proxies are deterministic.
- provider/fallback trace is honest.
- no executed provider is fabricated without TTS trace.
- audio validation limitations are explicit.
- confidence is calibrated and non-constant.
- `voice_trace` is reconstructible.
- Strategy, Script, Asset, QC, Publisher, TTS Router and core boundaries are preserved.

### Verdict Rules

`HOLD` if:

- provider/fallback is hidden.
- executed provider is fabricated.
- confidence is fake or constant.
- `voice_trace` is incomplete.
- Voice becomes Strategy, Script, Asset, QC, Publisher or TTS Router.
- provider order is changed without governance.
- core pipeline is modified.
- deterministic replay fails without explanation.

`GO_WITH_MONITORING` if:

- all critical checks pass.
- remaining residues are explicit and tied to provider/runtime/audio evidence horizon.

`GO` only if:

- all checks pass and no meaningful residual monitoring remains.

## 17. Required Output By End Of Voice v2.6

`VoiceAgentResult` or related trace should expose additive fields such as:

- `voice_plan_governance`
- `delivery_semantics`
- `segment_timing_summary`
- `monotony_contrast_analysis`
- `provider_fallback_trace`
- `audio_validation_summary`
- `confidence`
- `confidence_level`
- `confidence_components`
- `confidence_rationale`
- `voice_trace`

Do not remove existing fields:

- `voice_plan`
- `fallback`

Do not break:

- `VoicePlan.provider`
- `VoicePlan.voice_id`
- `VoicePlan.style`
- `VoicePlan.delivery_profile`
- `VoicePlan.segments`
- `VoicePlan.runtime_constraints`

## 18. Voice Exit Criteria

Voice is v2.6-complete only when:

- contract governance is explicit.
- delivery semantics are explicit.
- segment timing rationale is explicit.
- monotony/contrast proxies are deterministic and bounded.
- provider/fallback state is honest.
- audio validation linkage is honest.
- confidence is trust-in-voice-plan readiness, not performance prediction.
- `voice_trace` is reconstructible.
- Kokoro remains primary.
- Piper remains fallback.
- provider order is unchanged unless a later governance-approved plan says otherwise.
- no provider expansion occurred.
- Script/Strategy/Asset/QC/core behavior remains unchanged.
- dedicated Voice v2.6 gate passes.

## 19. Failure Conditions

Voice v2.6 must pause if any of the following occurs:

- hidden provider fallback.
- provider execution fabricated.
- missing segment timing hidden.
- weak contrast hidden.
- confidence high under missing/fallback execution evidence without rationale.
- confidence predicts performance.
- Voice rewrites Script.
- Voice chooses Asset.
- Voice issues QC or publish decisions.
- Voice modifies TTS Router behavior outside a bounded trace-only workstream.
- provider order changes silently.
- new provider is added without gated provider plan.
- `voice_trace.audit_summary.reconstructible = true` while required sections are missing.
- existing Voice tests regress.
- orchestrator or pipeline integration regresses.

## 20. Current Authorized Next Step

The first implementation workstream after this plan is:

```text
Voice Agent v2.6 - Voice Plan Contract Governance
```

Allowed scope:

- inspect current `VoicePlan`, `VoiceAgentResult`, `VoiceAgentService`, `VoiceInterpreter`, and TTS trace interfaces.
- add additive contract governance structures.
- expose requested provider, voice id, style, fallback order, segment completeness, missing/degraded fields, and boundary statement.
- preserve current `VoicePlan` output.
- preserve Kokoro/Piper provider order.
- preserve Strategy, Script, Asset, QC, Experiment, Publisher and core boundaries.

Forbidden in the first workstream:

- provider expansion.
- TTS Router behavior change.
- audio synthesis.
- confidence calibration.
- monotony analysis.
- trace consolidation.
- downstream behavior changes.

## 21. Final Principle

Voice Agent v2.6 must make delivery planning explainable and trustworthy.

It must not become the TTS Router, Strategy, QC, Publisher, or a hidden provider expansion layer.
