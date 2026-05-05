# CortAI Script Agent

## 1. Purpose

The Script Agent is the CortAI narrative construction agent responsible for producing and auditing the short-form story structure used by the creative pipeline.

Its central output is a structured `ScriptPlan` organized around:

```text
HOOK -> SETUP -> PAYOFF
```

The Script Agent exists to transform bounded upstream context into a concise narrative plan for downstream voice, asset, editing and quality-control surfaces. It is not a publishing authority, not a performance predictor, not a QC layer and not an external execution layer.

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

This document describes the Script Agent as observed in the repository. It does not authorize runtime integration, external calls, provider execution, upload, scheduling, publishing or production readiness.

Related documents:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Creative_Orchestrator]]
- [[CortAI_Voice_Agent]]
- [[CortAI_Content_Pipeline]]
- [[CortAI_Boundary_Specification]]

## 2. Narrative Model: HOOK -> SETUP -> PAYOFF

The Script Agent uses a three-part narrative model designed for short-form video retention:

| Segment | Function | Required Behavior |
| --- | --- | --- |
| `HOOK` | Capture attention immediately | Introduce tension, anomaly, contradiction or concrete story evidence. |
| `SETUP` | Develop context | Connect the hook to the eventual payoff without repeating the hook or inventing unsupported context. |
| `PAYOFF` | Resolve or reframe | Deliver a memorable closing beat that resolves, reverses or reframes the initial tension. |

This structure is represented by `ScriptPlan` in `backend/app/creative/contracts/creative_pack.py`.

The plan stores:

- `hook`
- `setup`
- `payoff`
- `generation_mode`

The `narration_text()` method composes the three segments into narration-ready text, but that does not make Script responsible for speech synthesis. Script produces narrative text; Voice interprets delivery and TTS execution remains outside Script ownership.

The model is intentionally bounded. The Script Agent must not treat a strong hook, a coherent setup or a memorable payoff as proof that the final video is publishable.

## 3. Script Agent Role

The Script Agent is implemented around `ScriptAgentService` in `backend/app/creative/agents/script/service.py`.

Its responsibilities are:

- consume bounded context from account health, strategy, trend, learning and experiment surfaces;
- produce a structured `ScriptPlan`;
- adapt the script into screen-text-safe blocks through the screen text adapter;
- expose fallback use explicitly;
- evaluate context governance;
- evaluate narrative construction quality;
- analyze hook strength;
- analyze setup progression;
- analyze payoff memorability;
- analyze cliche and repetition risk;
- expose provider and fallback honesty;
- calibrate confidence as trust in script construction;
- consolidate audit evidence into `script_trace`.

The Script Agent does not own:

- Strategy decisions;
- Account Health HOLD decisions;
- Voice planning;
- TTS execution;
- Asset selection;
- video rendering;
- Video QC decisions;
- Publisher decisions;
- publishability authority;
- external platform execution.

The Script Agent can explain why a script was emitted. It cannot decide whether the final artifact should be published.

## 4. Inputs / Outputs

### Inputs

`ScriptAgentInput` is defined in `backend/app/creative/agents/script/models.py`.

Observed input fields:

| Field | Role |
| --- | --- |
| `account_id` | Identifies the account context. |
| `niche` | Provides the content domain or vertical. |
| `topic` | Provides the base narrative subject. |
| `account_health_status` | Carries Account Health state into Script context governance. |
| `strategy_profile` | Provides bounded creative-control context from Strategy. |
| `trend_profile` | Provides advisory trend context. |
| `learning_insights` | Provides bounded historical learning context. |
| `experiment_plan` | Provides bounded experiment variation context. |

The Script context governance layer classifies context as available, used, ignored, missing or degraded. Required base context includes account health, topic and niche. Strategy remains the creative control layer; Script only consumes the context.

### Outputs

`ScriptAgentResult` includes:

| Field | Meaning |
| --- | --- |
| `script_plan` | The emitted `ScriptPlan` with `hook`, `setup`, `payoff` and `generation_mode`. |
| `fallback` | Fallback decision metadata. |
| `context_governance` | Context intake trace. |
| `quality_rubric` | Narrative construction scoring. |
| `hook_analysis` | Hook strength and claim-risk audit. |
| `setup_analysis` | Setup progression audit. |
| `payoff_analysis` | Payoff memorability audit. |
| `diversity_analysis` | Cliche and repetition-risk audit. |
| `provider_fallback_trace` | Provider path, failures and fallback honesty. |
| `confidence` | Numeric confidence for script construction trust only. |
| `confidence_level` | `low`, `medium` or `high`. |
| `confidence_components` | Component scores for confidence calculation. |
| `confidence_rationale` | Explanation of penalties and confidence meaning. |
| `script_trace` | Consolidated audit trace. |
| `decision_trace` | Backward-compatible trace surface including `script_trace`. |

`script_trace` is reconstructive, not executive. It explains the emitted plan; it does not authorize downstream execution.

## 5. Provider Chain

The Script Agent delegates text generation to `LocalScriptGeneratorService` in `backend/app/content/script_gen/service.py`.

Observed provider chain behavior:

- Groq can be included when `GROQ_API_KEY` is present and provider preference permits it.
- Ollama can be used as a local model provider through `CORTAI_OLLAMA_BASE_URL` and `CORTAI_OLLAMA_MODEL`.
- Default model names are configured through environment variables.
- The generator records provider attempts in `provider_attempt_trace`.
- If provider generation fails, the generator can return deterministic fallback content.
- The Script Agent can also fall back to deterministic contextual script blocks after `ScriptGenerationError`.

Provider metadata is exposed through `ScriptProviderFallbackTracer`, including:

- `provider_path`
- `provider_used`
- `model_used`
- `provider_success`
- `provider_failures`
- `repair_status`
- `fallback_used`
- `fallback_mode`
- `fallback_reason`
- `fallback_type`
- `contextual_fallback_used`
- `safe_default_used`
- `generation_mode`

Important boundary:

Provider availability is not execution authorization. The existence of Groq/Ollama provider code does not authorize external calls, runtime integration, publishing, upload, scheduling or production operation.

The provider chain is a Script Generator capability under its own governed execution context. It must not be confused with the Publisher external sandbox chain. Script provider invocation, if used, must remain subject to the repository's runtime, environment and governance controls.

Fallback is explicit and is not treated as provider success.

## 6. Screen Text Relationship

The Script Agent uses `ScreenTextAdapterService` from `backend/app/content/screen_text/service.py`.

The screen text adapter is responsible for shaping script text into concise screen-text blocks. It can:

- adapt structured `hook`, `setup` and `payoff` text;
- normalize punctuation and formatting;
- remove segment labels such as `hook:`, `setup:` or `payoff:`;
- compress blocks to short on-screen phrases;
- generate narration blocks;
- generate timed cue structures when explicit timing is supplied.

The relationship is additive and bounded:

- Script owns the narrative structure.
- Screen text adapts the narrative into visible short text.
- Screen text does not decide publishability.
- Screen text does not synthesize audio.
- Screen text does not validate final video quality.
- Screen text does not authorize external execution.

The adapter can improve display suitability, but it can also lose nuance because of compression and uppercase normalization. That limitation must remain visible to downstream QC and audit surfaces.

## 7. TTS / Voice Relationship

Script and Voice are separate layers.

Script produces:

- narrative text;
- `ScriptPlan`;
- narration-ready text through `ScriptPlan.narration_text()`;
- script audit trace.

Voice consumes the script surface and interprets delivery. Voice is responsible for delivery profile, segment timing, pauses, contrast, provider/fallback honesty and audio validation linkage where evidence exists.

Script must not:

- choose final TTS execution semantics;
- execute TTS;
- fabricate audio trace;
- rewrite Voice output;
- treat a script as audio-ready evidence;
- become the TTS Router.

A script can be suitable for narration without proving that audio exists or that audio execution succeeded.

See [[CortAI_Voice_Agent]].

## 8. Quality Criteria

Script quality is evaluated through deterministic audit surfaces. These criteria explain construction quality; they do not decide publishability.

### Context Governance

`ScriptContextGovernanceEvaluator` checks whether upstream context is present, missing or degraded. It also preserves the boundary that Strategy remains the creative control layer.

### Quality Rubric

`ScriptQualityRubricEvaluator` scores construction components such as:

- hook clarity;
- hook specificity;
- setup coherence;
- setup progression;
- payoff specificity;
- payoff memorability;
- CTA fit;
- trend alignment;
- strategy alignment;
- repetition risk;
- cliche risk.

The rubric meaning is `script_construction_quality_not_publishability`.

### Hook Analysis

`ScriptHookStrengthAnalyzer` checks:

- hook presence;
- generic hook phrases;
- unsupported claim risk;
- tension;
- specificity.

### Setup Analysis

`ScriptSetupProgressionAnalyzer` checks whether setup connects hook to payoff, avoids repetition and avoids unsupported context.

### Payoff Analysis

`ScriptPayoffMemorabilityAnalyzer` checks payoff specificity, generic payoff phrases, vague motivational language and whether the payoff resolves or reframes the hook.

### Diversity Analysis

`ScriptDiversityAnalyzer` detects local cliche and repetition patterns within the current script. It does not use external memory or randomness.

### Confidence Calibration

`ScriptConfidenceCalibrator` defines confidence as:

```text
trust_in_script_construction
```

Its components include:

- context completeness;
- provider reliability;
- structure integrity;
- rubric strength;
- fallback penalty;
- genericity penalty;
- upstream alignment.

Confidence is not product performance, not QC approval and not publishability.

### Trace Auditability

`ScriptTraceBuilder` consolidates:

- context governance;
- quality rubric;
- hook analysis;
- setup analysis;
- payoff analysis;
- diversity analysis;
- provider/fallback trace;
- confidence calibration;
- final script rationale;
- missing or degraded inputs;
- audit summary.

The trace reconstructs why a `ScriptPlan` was emitted. It does not rewrite the script and does not authorize execution.

## 9. Boundaries

The Script Agent has strict boundaries.

It may:

- construct a narrative plan;
- consume upstream context;
- expose degraded or missing context;
- expose provider/fallback metadata;
- evaluate script construction;
- calibrate confidence in construction;
- emit traceable rationale.

It must not:

- override Strategy;
- override Account Health HOLD;
- decide publishability;
- become QC;
- become Voice;
- become Asset Selection;
- become Publisher;
- execute external calls by implication;
- treat provider availability as execution authorization;
- treat fallback as success;
- treat confidence as performance prediction;
- treat a passing gate as unlimited permission;
- close production residuals.

Critical non-authorization rules:

- `ScriptPlan` is not publish permission.
- `script_trace` is not execution.
- `confidence=high` is not QC approval.
- provider configured does not mean provider execution is authorized.
- fallback emitted does not mean provider success.
- screen text emitted does not mean final captions are validated.
- narration text emitted does not mean audio exists.

See [[CortAI_Boundary_Specification]].

## 10. Known Limitations

Known limitations observed from code and audit surfaces:

- Provider execution depends on runtime configuration and environment variables; provider code presence is not authorization.
- Groq availability depends on `GROQ_API_KEY`; missing credentials are treated by the generator as provider failure, not hidden success.
- Ollama depends on a configured local base URL and model; local provider availability is environment-dependent.
- Provider repair status is currently exposed as `not_reported_by_generator` in the provider/fallback trace.
- Deterministic fallback keeps the pipeline explainable, but fallback content remains weaker evidence than provider success.
- Screen text adaptation is heuristic and can compress nuance.
- Diversity analysis is local to the emitted script and does not prove long-horizon novelty across production history.
- Script confidence measures construction trust only and must not be interpreted as expected performance.
- Script does not validate video pixels, audio artifacts, edit timing, final render quality or publish lifecycle.
- The repository contains the Script v2.6 excellence gate runner and runtime documentation, but the active `OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json` artifact is not present in the current cleaned workspace snapshot.

Validation evidence available in the repository includes:

- unit tests under `tests/agents/script/`;
- the Script v2.6 excellence gate runner at `tests/gates/agents/script/run_script_agent_v2_6_excellence_gate.py`;
- Script v2.6 runtime documentation under `docs/runtime/phase-2-6/agents/script/`;
- consolidated release documentation under `docs/active/PHASE_2_6_RELEASE_RECORD.md`.

Current bottlenecks are evidence and interpretation bottlenecks, not permissions to execute:

- stronger longitudinal script-performance evidence remains separate from Script confidence;
- provider history and repair metadata remain limited by the generator contract;
- cross-run novelty evidence is not owned by Script alone;
- downstream audio/video validation remains owned by Voice, Editor and QC layers;
- publish readiness remains outside Script authority.

## 11. Obsidian Links

Primary links:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Creative_Orchestrator]]
- [[CortAI_Voice_Agent]]
- [[CortAI_Content_Pipeline]]
- [[CortAI_Boundary_Specification]]

Related governance links:

- [[CortAI_Execution_Model]]
- [[CortAI_Governance_Model]]
- [[CortAI_System_State_Definition]]
- [[KERNEL_BIBLE]]

Final invariant:

> Script constructs and explains narrative. It does not authorize execution, publication, runtime integration or external calls.
