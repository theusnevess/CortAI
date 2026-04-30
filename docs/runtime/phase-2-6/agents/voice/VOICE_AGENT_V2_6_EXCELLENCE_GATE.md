# VOICE_AGENT_V2_6_EXCELLENCE_GATE

## 1. Purpose

`VOICE_AGENT_V2_6_EXCELLENCE_GATE` is the formal validation gate for the Voice Agent after the Phase 2.6 excellence-hardening workstreams.

This gate validates Voice Agent v2.6 as implemented. It must not mutate runtime behavior to make validation pass.

The gate determines whether Voice is:

- runtime-real
- contract-governed
- delivery-semantics aware
- segment timing and pause aware
- monotony and contrast aware
- provider/fallback honest
- audio-validation linked when evidence exists
- confidence-calibrated
- traceable end-to-end
- deterministic under controlled inputs
- boundary-preserving
- free of silent failures

This gate is not a feature and is not a runtime behavior change. It is an audit artifact that can produce `GO`, `GO_WITH_MONITORING`, or `HOLD`.

## 2. Scope

In scope:

- Voice Agent runtime service execution
- `VoicePlan` contract governance
- delivery profile semantics
- hook/setup/payoff segment timing and pause analysis
- monotony and contrast analysis
- provider and fallback honesty
- audio validation linkage
- confidence calibration as trust in voice plan execution readiness
- consolidated `voice_trace`
- deterministic replay
- backward-compatible `VoiceAgentResult`
- TTS Router, Strategy, Script, Asset, QC, orchestrator, and core boundary preservation

Out of scope:

- modifying Voice runtime logic to pass the gate
- changing `VoicePlan` generation
- changing provider order
- adding providers
- synthesizing audio
- reading audio files without supplied artifacts
- modifying `TtsRouter`
- modifying Strategy, Script, Asset, QC, orchestrator, or core pipeline
- predicting performance
- converting Voice into TTS Router, Strategy, QC, Publisher, or core

## 3. Preconditions

The gate may run only after these Voice v2.6 workstreams exist:

- Voice Plan Contract Governance
- Delivery Profile Semantics
- Segment Timing And Pause Hardening
- Monotony And Contrast Analysis
- Provider And Fallback Honesty
- Audio Validation Linkage
- Confidence Calibration
- Trace And Auditability Hardening

Required code surfaces:

- `backend/app/creative/agents/voice/models.py`
- `backend/app/creative/agents/voice/service.py`
- `backend/app/creative/agents/voice/voice_plan_governance.py`
- `backend/app/creative/agents/voice/delivery_semantics.py`
- `backend/app/creative/agents/voice/segment_timing.py`
- `backend/app/creative/agents/voice/monotony_contrast.py`
- `backend/app/creative/agents/voice/provider_fallback_honesty.py`
- `backend/app/creative/agents/voice/audio_validation_linkage.py`
- `backend/app/creative/agents/voice/confidence_calibration.py`
- `backend/app/creative/agents/voice/trace_auditability.py`

Required validation command:

`python tests/gates/agents/voice/run_voice_agent_v2_6_excellence_gate.py`

Required output artifact:

`OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json`

## 4. Evaluation Dimensions

`runtime_real`

Means Voice executes through `VoiceAgentService`, not a stubbed result object.

Failure if the service cannot execute or if the gate validates only synthetic result objects.

`contract_governed`

Means requested provider, voice id, style, fallback order, delivery profile, and hook/setup/payoff segment completeness are visible and semantically validated.

Failure if degraded fields are hidden or fallback policy incoherence is accepted as complete.

`delivery_semantics_explicit`

Means hook/setup/payoff are mapped to voice roles and delivery intent is explicit.

Failure if semantics are missing or imply synthesis authority.

`segment_timing_explicit`

Means rate, emphasis, pauses, timing validity, and hook/setup/payoff timing contrast are visible.

Failure if invalid timing is hidden or timing analysis mutates the plan.

`monotony_contrast_explicit`

Means monotony risk, contrast level, variation metrics, role alignment, reason codes, and rationale are visible.

Failure if low contrast or missing segments are hidden, or if the analyzer predicts performance.

`provider_fallback_honest`

Means Voice reports requested provider and fallback order while separating Voice fallback from TTS Router execution fallback.

Failure if Voice fabricates executed provider, TTS fallback usage, provider attempts, or router execution.

`audio_validation_linked`

Means supplied TTS trace can link provider execution and durations, while missing trace remains explicit.

Failure if missing trace is treated as verified execution, duration is fabricated, or files are inspected without supplied artifacts.

`confidence_calibrated`

Means confidence measures trust in voice plan execution readiness, varies by evidence state, and is not performance prediction.

Failure if confidence is constant, high without `tts_trace`, high under monotony/degraded inputs, lacks rationale, or predicts performance.

`traceability_complete`

Means `voice_trace` reconstructs why the `VoicePlan` was emitted and what evidence was unavailable.

Failure if required trace sections are missing, reconstructibility is faked, or silent failure indicators are ignored.

`boundary_preserved`

Means Voice remains a voice planning and audit agent and does not become TTS Router, Strategy, Script, Asset, QC, Publisher, or core.

Failure if Voice executes TTS, changes provider order, adds providers, emits publishability decisions, or changes downstream behavior.

`determinism_where_required`

Means controlled identical input produces stable voice plan, analyses, confidence, and trace.

Failure if stable output drifts without input changes.

`fallback_honest`

Means fallback remains explicit, scoped, and never confused with router execution.

Failure if fallback is hidden or treated as clean executed provider evidence.

`silent_failures_detected`

Means missing trace, fake confidence, hidden fallback, boundary violations, and non-determinism are detected as blockers.

Failure if critical defects exist while the verdict passes.

## 5. Controlled Scenario Battery

The runner executes controlled scenarios through `VoiceAgentService` and direct helper evaluators where supplied TTS trace evidence is required.

Required scenarios:

- `clean_voice_plan_missing_tts_trace`
- `strong_voice_plan_with_tts_trace`
- `monotony_high`
- `degraded_contract`
- `provider_order_deviation`
- `audio_trace_partial`
- `fallback_executed_trace`
- `determinism_replay`
- `backward_compatibility`

## 6. Checklist

The runner validates:

- runtime execution
- contract governance
- delivery semantics
- segment timing
- monotony and contrast
- provider/fallback honesty
- audio validation linkage
- confidence calibration
- trace completeness
- fallback honesty
- boundary preservation
- deterministic replay
- backward compatibility
- TTS Router tests
- silent failure detection

Any failed critical checklist item becomes a blocking failure.

## 7. Verdict Semantics

`GO`

Allowed only when all critical dimensions pass and no meaningful residual monitoring remains.

`GO_WITH_MONITORING`

Allowed when all critical checks pass and remaining residuals are explicit, bounded, non-structural, and related to missing runtime TTS trace history or operational maturity.

`HOLD`

Required if any critical failure, blocking failure, fake confidence, silent failure, boundary violation, non-determinism, incomplete trace, hidden fallback, provider order mutation, or TTS Router mutation is detected.

Expected likely verdict is `GO_WITH_MONITORING`. The runner must derive it from evidence and must not hardcode it.

## 8. Failure Conditions

Critical failures include:

- Voice service cannot execute
- `VoicePlan` provider order changes from `kokoro -> piper`
- `TtsRouter` behavior changes or tests fail
- executed provider is fabricated without TTS trace
- fallback execution is fabricated without TTS trace
- missing audio trace is hidden
- confidence is high without audio trace
- confidence is high under high monotony
- trace required sections are missing
- `voice_trace.audit_summary.reconstructible` is false for normal service output
- boundary violation
- non-deterministic replay
- failed critical test battery

## 9. Output Artifacts

The runner must write:

- `OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/metrics.json`

## 10. Final Criteria

The Voice Agent v2.6 gate may recommend proceeding only when:

- Voice Agent runs through real `VoiceAgentService`
- all v2.6 additive fields exist and serialize
- contract governance is semantically complete
- delivery semantics, timing, monotony/contrast, provider/fallback honesty, audio linkage, confidence, and trace are visible
- missing `tts_trace` is explicit and prevents high confidence
- fallback and executed provider are not fabricated
- `TtsRouter` remains unchanged and tests pass
- provider order remains `kokoro -> piper`
- no boundary violation exists
- no silent failures exist
- residuals are non-structural and explicitly monitorable

Final recommendation values:

- `PROCEED_TO_ASSET_SELECTION_AGENT_V2_6_PLAN`
- `HOLD_BEFORE_ASSET_SELECTION`
