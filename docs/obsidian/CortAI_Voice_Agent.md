# CortAI Voice Agent

## 1. Purpose

The Voice Agent is the CortAI voice-planning layer responsible for converting narrative structure into a voice delivery plan.

It plans how the script should be spoken. It does not synthesize speech, execute TTS providers, inspect audio files, validate produced audio as successful output, publish content or authorize external execution.

The Voice Agent operates on the narrative structure:

```text
HOOK -> SETUP -> PAYOFF
```

Its purpose is to make voice delivery explicit, auditable and bounded before downstream TTS execution may occur through the content pipeline.

Current system state remains:

```json
{
  "system_state": "SAFE_PRE_CROSSING",
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "implementation_authorized": false,
  "production_ready": false
}
```

This document is descriptive. It does not authorize provider calls, runtime integration, external calls, upload, scheduling, publishing or production operation.

## 2. Voice Agent Role

The Voice Agent is implemented primarily by `VoiceAgentService` in `backend/app/creative/agents/voice/service.py`.

Its core role is to produce a `VoicePlan` from:

- account identity;
- niche;
- `ScriptPlan`;
- optional `StrategyProfile`.

The Voice Agent decides voice-planning properties such as:

- requested TTS provider;
- requested voice ID;
- voice style;
- delivery profile;
- segment-level rate;
- segment-level emphasis;
- segment-level pauses;
- provider fallback policy in the plan;
- audit interpretation of delivery semantics;
- monotony/contrast risk based on the plan;
- confidence in voice plan execution readiness.

The Voice Agent does not decide:

- whether TTS execution occurred;
- which provider actually executed;
- whether generated audio exists;
- whether audio duration is valid unless trace evidence is supplied;
- whether final video is publishable;
- whether Publisher may publish;
- whether external calls are allowed;
- whether runtime integration is authorized.

The most important boundary is:

```text
Voice Agent requests and explains voice delivery.
TTS Router executes TTS providers.
```

## 3. Inputs / Outputs

### Inputs

`VoiceAgentInput` is defined in `backend/app/creative/agents/voice/models.py`.

| Field | Meaning |
| --- | --- |
| `account_id` | Account identifier for the voice planning request. |
| `niche` | Content category used to determine voice style and intensity. |
| `script_plan` | Optional `ScriptPlan` containing `hook`, `setup` and `payoff`. |
| `strategy_profile` | Optional Strategy context used for bounded delivery choices. |

If no script plan is supplied, the service uses an empty default `ScriptPlan` with `generation_mode="voice_default"`. That is a degraded planning condition, not evidence of audio execution.

### Outputs

`VoiceAgentResult` exposes:

| Field | Meaning |
| --- | --- |
| `voice_plan` | The requested voice provider, voice ID, style, delivery profile, segments and runtime constraints. |
| `fallback` | Voice-agent-level fallback decision. Current service path uses no voice-agent fallback by default. |
| `voice_plan_governance` | Contract completeness and provider/fallback policy audit. |
| `delivery_semantics` | Mapping from script roles to voice delivery roles. |
| `segment_timing` | Planned timing, emphasis and pause assessment. |
| `monotony_contrast_analysis` | Planned monotony and contrast audit. |
| `provider_fallback_honesty` | Requested provider, fallback order and TTS trace honesty. |
| `audio_validation_linkage` | Linkage to supplied TTS/audio trace evidence, when present. |
| `confidence` | Trust in voice plan execution readiness, not audio quality. |
| `confidence_level` | `low`, `medium` or `high`. |
| `confidence_components` | Component scores used by confidence calibration. |
| `confidence_rationale` | Penalties, evidence summary and boundary statement. |
| `confidence_calibration` | Full confidence calibration payload. |
| `voice_trace` | Consolidated audit trace for reconstruction. |

The output is a planning and audit surface. It is not an audio artifact.

## 4. Voice Plan Semantics

`VoicePlan` is defined in `backend/app/creative/contracts/creative_pack.py`.

It contains:

- `provider`
- `voice_id`
- `style`
- `fallback_used`
- `delivery_profile`
- `segments`
- `runtime_constraints`

Current `VoiceAgentService` emits:

| Field | Current Behavior |
| --- | --- |
| `provider` | `kokoro` |
| `voice_id` | default Kokoro voice from `DEFAULT_KOKORO_VOICE` |
| `fallback_order` | `kokoro`, then `piper` |
| `allow_provider_fallback` | `true` |
| `fallback_used` | `false` at Voice Agent planning level |

The `VoiceInterpreter` determines style and delivery profile deterministically:

| Niche / Strategy | Style |
| --- | --- |
| `horror` | `ominous_minimal` |
| `true_crime` | `investigative` |
| `facts` | `neutral_archive` |
| conservative Strategy content mode | `measured_dark` |
| default | `dark_calm` |

Segment defaults follow the narrative role sequence:

| Segment | Voice Role | Default Shape |
| --- | --- | --- |
| `hook` | `open_tension` | Slightly slower rate, high emphasis, attention pause after. |
| `setup` | `controlled_progression` | Measured rate, medium emphasis, lighter pause after. |
| `payoff` | `memorable_close` | Slower landing, high emphasis, pause before payoff. |

If hook text is missing, the hook segment is softened. If payoff text is missing, the payoff segment is softened. This is degradation handling, not audio correction.

The Voice Agent also audits the plan through:

- voice plan governance;
- delivery semantics;
- segment timing;
- monotony and contrast analysis;
- provider/fallback honesty;
- audio validation linkage;
- confidence calibration;
- voice trace consolidation.

## 5. Relationship With Script Agent

The Script Agent owns narrative text. The Voice Agent interprets that text for delivery.

Script produces:

- `hook`;
- `setup`;
- `payoff`;
- narrative construction confidence;
- `script_trace`.

Voice consumes the `ScriptPlan` and maps each narrative segment into voice intent:

| Script Segment | Script Role | Voice Role |
| --- | --- | --- |
| `hook` | attention capture | open tension |
| `setup` | context bridge | controlled progression |
| `payoff` | resolution or reframe | memorable close |

The Voice Agent must not rewrite Script output. It may detect degraded voice support when script text is missing or incomplete, but it must not repair the script or claim script quality as audio readiness.

A good script does not prove good audio. A complete `VoicePlan` does not prove synthesized speech exists.

See [[CortAI_Script_Agent]].

## 6. Relationship With TTS

The content pipeline contains TTS execution components, including:

- `TtsRouter` in `backend/app/content/pipeline/tts_router.py`;
- `StubTtsAdapter` and provider-specific TTS paths in `backend/app/content/pipeline/tts.py`;
- `KokoroAdapter` in `backend/app/content/pipeline/kokoro_adapter.py`;
- `TtsExecutionTrace` in `backend/app/content/pipeline/models.py`.

The TTS Router can execute providers when the content pipeline is operating under its own authorized runtime context. The Voice Agent does not execute that router.

The observed TTS Router behavior includes:

- reads the requested provider from `VoicePlan`;
- uses fallback order from `VoicePlan.runtime_constraints`;
- attempts provider execution in order;
- records `provider_requested` and `provider_executed`;
- records executed voice ID;
- records fallback usage and fallback reason;
- records latency and duration when available;
- returns `TtsExecutionTrace` with the pipeline result.

The Voice Agent only links or reports TTS execution evidence if a real trace is supplied. Without a supplied TTS trace:

- `tts_executed_provider` remains `null` at the Voice Agent level;
- TTS fallback usage remains not reported by Voice Agent;
- audio trace status is `missing_trace`;
- provider execution is not verified;
- duration is unavailable;
- segment durations are unavailable;
- confidence cannot be high.

The audio validation linkage is explicit:

```text
missing tts_trace = not observable
missing tts_trace != TTS failure
missing tts_trace != TTS success
```

Voice plan and TTS execution are separate. TTS trace can support auditability, but it does not equal publish success.

See [[CortAI_Content_Pipeline]].

## 7. Current Limitations

Current limitations are evidence limitations and boundary limitations, not permissions to execute.

Known limitations:

- Voice Agent does not synthesize audio.
- Voice Agent does not inspect audio files.
- Voice Agent links audio artifacts only when supplied and marks them as `provided_not_inspected`.
- Without `tts_trace`, provider execution is not verified.
- Without `tts_trace`, audio duration and segment durations are unavailable.
- Voice confidence is capped when audio trace is missing.
- Monotony/contrast analysis is based on planned timing, not actual waveform analysis.
- Delivery semantics explain intent, not produced sound.
- Provider/fallback honesty reports requested provider and fallback order, but executed provider is reported only from TTS Router trace.
- Current requested provider policy is Kokoro primary with Piper fallback.
- Historical runtime audio validation and provider execution history remain short.
- The active cleaned workspace snapshot does not include `OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json`, although the repository contains the gate runner and Phase 2.6 runtime documentation.

Validation evidence available in the repository includes:

- unit tests under `tests/agents/voice/`;
- the Voice v2.6 excellence gate runner at `tests/gates/agents/voice/run_voice_agent_v2_6_excellence_gate.py`;
- Voice v2.6 runtime documentation under `docs/runtime/phase-2-6/agents/voice/`;
- consolidated Phase 2.6 release documentation under `docs/active/PHASE_2_6_RELEASE_RECORD.md`.

Current residuals associated with Voice remain monitorable rather than closed:

- `VOICE_TTS_TRACE_NOT_AVAILABLE_AT_VOICE_AGENT_LAYER`;
- `VOICE_RUNTIME_AUDIO_VALIDATION_HISTORY_STILL_SHORT`;
- `VOICE_PROVIDER_EXECUTION_HISTORY_STILL_SHORT`.

## 8. Boundaries

The Voice Agent may:

- request a provider in the voice plan;
- define fallback order in the voice plan;
- plan voice style;
- plan segment rate, emphasis and pauses;
- map hook/setup/payoff into delivery roles;
- classify timing completeness;
- classify monotony and contrast risk from planned values;
- report requested provider and fallback policy;
- link supplied TTS trace evidence;
- calibrate confidence in voice plan execution readiness;
- consolidate `voice_trace`.

The Voice Agent must not:

- execute TTS;
- call Kokoro, Piper, OpenAI, Edge, pyttsx3 or any provider directly;
- authorize provider execution;
- authorize external calls;
- authorize runtime integration;
- inspect audio files without supplied artifacts;
- fabricate executed provider;
- fabricate fallback execution;
- treat fallback order as executed fallback;
- treat `voice_plan` as produced audio;
- treat `audio_trace_available=false` as success;
- treat audio existence as publish success;
- decide publishability;
- override QC;
- override Strategy;
- override Account Health HOLD;
- become Publisher.

Critical semantic boundaries:

- `VoicePlan` is not audio.
- requested provider is not executed provider.
- fallback allowed is not fallback used.
- fallback order is not execution trace.
- audio artifact path is not audio validation unless supporting trace exists.
- duration missing is not duration failure; it is absent evidence.
- confidence is not performance prediction.
- TTS trace is not publish success.
- gate pass is not unlimited permission.

See [[CortAI_Boundary_Specification]].

## 9. Failure Conditions

Voice Agent behavior must be treated as unsafe or degraded if any of the following occurs:

- `VoicePlan` is missing provider, voice ID, style or required segments.
- Provider order deviates from the governed Kokoro/Piper policy without visible degradation.
- Voice Agent reports an executed provider without TTS Router trace.
- Voice Agent reports TTS fallback usage without TTS Router trace.
- Missing `tts_trace` is treated as success.
- Missing audio duration is treated as valid duration.
- Missing segment durations are treated as valid timing evidence.
- Audio artifact path is treated as inspected audio when no inspection occurred.
- `voice_plan` is treated as generated audio.
- Voice confidence becomes high while audio trace is unavailable.
- Monotony risk is hidden or ignored.
- Provider fallback is hidden.
- Voice rewrites Script output.
- Voice decides publishability.
- Voice becomes TTS Router, QC, Publisher, Strategy or external client.
- A passing test or gate is interpreted as runtime integration authorization.

Fail-closed rule:

```text
If execution evidence is missing, Voice must report missing evidence and reduce confidence. It must not infer success.
```

## 10. Obsidian Links

Primary links:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Script_Agent]]
- [[CortAI_Content_Pipeline]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_Governance_Model]]

Related links:

- [[CortAI_Creative_Orchestrator]]
- [[CortAI_Execution_Model]]
- [[CortAI_System_State_Definition]]
- [[KERNEL_BIBLE]]

Final invariant:

> Voice plans and explains delivery. It does not synthesize audio, execute providers, validate production audio, authorize runtime integration or prove publish success.
