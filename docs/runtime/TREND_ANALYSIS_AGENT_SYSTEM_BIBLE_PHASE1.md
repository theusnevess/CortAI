# TREND_ANALYSIS_AGENT_SYSTEM_BIBLE_PHASE1

## 1. Executive Summary

The `Trend Analysis Agent` exists in the current CortAI codebase as a real runtime subsystem, but it is still a Phase 1 prototype.

What it is today:
- a deterministic loader that reads a niche-specific JSON file
- assembles a small `TrendProfile`
- returns either that profile or a safe default fallback
- is called by the orchestrator before `Learning`, `Novelty`, and `Strategy`
- persists its output into runtime execution payloads and into `CreativePack`

What it is not today:
- not a live trend intelligence subsystem
- not an external evidence collector
- not an account-adaptive trend model
- not a baseline-governed subsystem
- not a strongly audited strategic authority on its own

Direct answers:
- Is the Trend Analysis Agent real in runtime today? Yes.
- Is it integrated into the orchestrator? Yes.
- Does it actually influence downstream generation? Yes, but unevenly.
- Is it mostly structural/contextual at this stage? Partly yes. It has real causal effect, but the decision model is still simple and file-backed.

Operational reality:
- `Strategy` consumes `trend_profile.pacing` and `trend_profile.dominant_hooks` and changes `hook_aggressiveness` accordingly.
- `Script` passes trend data into the prompt context used by the structured script generator.
- `Asset` uses trend fields materially, especially `pacing` and `visual_style`.
- `Editor` uses `visual_style` and the presence of trend context to shape style and mood naming.
- `Voice` does not consume trend directly.
- `Learning` does not influence Trend and Trend does not consume Learning.
- `Novelty` does not consume Trend directly.

Bottom line:
- the subsystem is implemented and runtime-real
- it is not merely decorative
- but it is still prototype-grade, file-driven, low-intelligence, and not baseline-ready

## 2. Current Mission Of The Trend Analysis Agent

The Trend Analysis Agent's actual mission today is narrow:
- load a manual, niche-scoped trend profile from disk
- provide a stable `TrendProfile` context block to the rest of the pipeline
- fail safely to a default profile when the niche file is missing or invalid

In current code it does:
- summarize niche trends only through pre-authored JSON
- expose `dominant_hooks`
- expose `avg_duration`
- expose `pacing`
- expose `visual_style`
- expose `text_style`

In current code it does not:
- inspect account history
- inspect platform telemetry
- inspect publish performance
- inspect topic-specific live evidence
- inspect time-sensitive trend shifts
- infer anything from downstream outcomes

Precision answers:
- Is it summarizing niche trends? Yes, but only by loading a niche JSON profile.
- Is it selecting dominant hooks? Only by reading `dominant_hooks` from file.
- Is it deriving pacing hints? Only by reading `pacing` from file.
- Is it deriving visual style? Only by reading `visual_style` from file.
- Is it account-aware or niche-only? Niche-only.
- Is it dynamic or mostly static/default? Mostly static.
- Does it consume external evidence or just local defaults? Just local file input or fallback.
- Is it changing how downstream agents behave? Yes, especially `Strategy`, `Asset`, and partially `Script` and `Editor`.
- Is it only producing a static/default `TrendProfile`? Yes.
- Is it consuming live context or only fallbacks/defaults? Only file-backed local context and fallback.

## 3. Responsibility Boundary

Conceptual ownership boundary:

`Account Health`
- owns risk posture and safety constraints
- does not own trend style or niche hook norms

`Trend Analysis`
- should own strategic context about niche-level trend conditions
- today it only owns loading a manual niche profile from disk
- it does not own performance feedback, repetition control, or optimization

`Learning Agent`
- owns historical feedback consumption from metrics and QC
- does not own external trend discovery
- today it does not feed Trend

`Novelty Engine`
- owns repetition and saturation control
- does not own trend style discovery
- today it does not consume Trend directly

`Strategy Agent`
- owns top-level runtime directional policy
- today it consumes Trend and converts part of it into actual control

`Script Agent`
- owns script generation and structured text output
- today it receives Trend context but does not interpret it itself; the underlying script generator uses it in prompt assembly

`Voice Agent`
- owns voice selection and delivery shaping
- today it does not consume Trend directly

`Asset Agent / Asset Selection`
- owns visual planning and asset selection
- today it consumes Trend materially

`Editor Agent`
- owns edit plan construction
- today it consumes Trend weakly but real

`QC Agent`
- owns evaluation and publishability governance
- does not use Trend directly as a control signal

Actual Trend authority today starts at:
- loading `TrendProfile` in orchestrator context resolution

Actual Trend authority today ends at:
- providing advisory context that downstream agents may consume
- influencing `Strategy`, `Script` prompt context, `Asset`, and `Editor`

What Trend does not do today:
- it does not overrule health
- it does not overrule QC
- it does not directly govern publishability
- it does not learn
- it does not monitor novelty
- it does not maintain temporal memory

## 4. Architectural Position In The Pipeline

Expected conceptual position:
- `Account Health -> Trend Analysis -> Learning -> Novelty -> Strategy -> Script -> Voice -> Asset -> Editor -> QC`

Current code confirms this order is real enough at orchestration level.

Actual runtime order in `backend/app/creative/orchestrator/service.py`:
1. `AccountHealthAgentService.evaluate(...)`
2. `TrendAnalysisAgentService.load(...)`
3. `LearningAgentService.generate(...)`
4. `NoveltyEngineService.generate(...)`
5. `StrategyAgentService.generate(...)`
6. `ExperimentCapabilityService.generate(...)`
7. `ScriptAgentService.generate(...)`
8. `VoiceAgentService.resolve(...)`
9. `AssetSelectionAgentService.select(...)`
10. `EditorAgentService.plan(...)`
11. pipeline render
12. `VideoQcAgentService.evaluate(...)`

Key files/classes:
- `backend/app/creative/agents/trend_analysis/service.py`
- `backend/app/creative/agents/trend_analysis/models.py`
- `backend/app/creative/contracts/creative_pack.py`
- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/models.py`
- `backend/app/creative/contracts/orchestrator_io.py`

Integration reality:
- Trend is actually called at runtime.
- Orchestrator does not skip it.
- Orchestrator does not depend on it strongly for survival because fallback exists.
- Downstream agents do read `TrendProfile`, but not uniformly.

## 5. End-To-End Flow

Actual flow:

1. Orchestrator receives `CreativeOrchestratorInput`.
- file: `backend/app/creative/contracts/orchestrator_io.py`

2. Orchestrator resolves account context.
- file: `backend/app/creative/orchestrator/service.py`
- method: `_resolve_account_context(...)`
- call: `trend_result = self.trend_analysis_agent.load(TrendAnalysisInput(niche=data.niche))`

3. Trend service normalizes `niche`.
- file: `backend/app/creative/agents/trend_analysis/service.py`

4. Trend service checks for a JSON file.
- path pattern: `<trends_dir>/<niche>.json`
- default service path: `backend/data/trends`

5. If the file exists, it loads JSON and assembles `TrendProfile`.
- fields loaded: `niche`, `dominant_hooks`, `avg_duration`, `pacing`, `visual_style`, `text_style`

6. If the file is missing, niche is empty, or an exception occurs, fallback is returned.
- fallback reason: `TREND_PROFILE_FALLBACK`
- fallback profile is hardcoded

7. Orchestrator emits either:
- `CREATIVE/trend_profile_loaded`
- or `CREATIVE/trend_profile_fallback`

8. Orchestrator passes `trend_result.trend_profile` downstream into:
- `StrategyInput`
- `ScriptAgentInput`
- `AssetSelectionInput`
- `EditorAgentInput`

9. Orchestrator also stores `trend_profile` in `CreativePack`.
- file: `backend/app/creative/contracts/creative_pack.py`

10. Execution payload persists `trend_analysis` in `CreativePipelineExecution.to_dict()`.
- file: `backend/app/creative/orchestrator/models.py`

Unused or weakly used path details:
- `trend_context_ref` exists in orchestrator input contracts but is not consumed anywhere.
- `avg_duration` and `text_style` are loaded and serialized, but current downstream consumption is effectively absent.

## 6. Contracts And Data Structures

### 6.1 `TrendProfile`
- file: `backend/app/creative/contracts/creative_pack.py`

Fields:
- `niche: str = "default"`
- `dominant_hooks: list[str] = []`
- `avg_duration: str = "8-12"`
- `pacing: str = "baseline"`
- `visual_style: str = "phase1_baseline"`
- `text_style: str = "caption_focus"`

Operational status by field:
- `niche`: operational as identity/context label
- `dominant_hooks`: operational in `Strategy`; advisory in `Script` prompt
- `avg_duration`: mostly symbolic today
- `pacing`: operational in `Strategy` and `Asset`; present in `Script` prompt
- `visual_style`: operational in `Asset`, weakly operational in `Editor`, present in `Script` prompt
- `text_style`: currently symbolic in runtime behavior

Serialization:
- fully serializable through `to_dict()`
- stored inside `CreativePack`
- visible in execution artifacts

### 6.2 `TrendAnalysisInput`
- file: `backend/app/creative/agents/trend_analysis/models.py`

Fields:
- `niche: str`

Operational status:
- fully operational
- notably minimal
- no `account_id`, no topic, no metrics, no time window, no platform source

### 6.3 `TrendAnalysisResult`
- file: `backend/app/creative/agents/trend_analysis/models.py`

Fields:
- `trend_profile: TrendProfile`
- `fallback: FallbackDecision`

Operational status:
- fully operational
- traceability limited to profile plus fallback flag

### 6.4 `CreativePack.trend_profile`
- file: `backend/app/creative/contracts/creative_pack.py`

Status:
- operational
- persisted in final creative pack
- used as handoff context for downstream agents

### 6.5 `CreativePipelineExecution.trend_analysis`
- file: `backend/app/creative/orchestrator/models.py`

Status:
- operational
- makes trend output visible in `execution_outputs.json`

### 6.6 `CreativeOrchestratorInput.trend_context_ref`
- file: `backend/app/creative/contracts/orchestrator_io.py`

Status:
- symbolic / placeholder only
- exists in contract
- not consumed in current code

Important note:
- there are no fields like `trend_source`, `trend_strength`, `confidence`, `updated_at`, or temporal validity in current Trend contracts.
- naming suggests a trend subsystem, but the actual contract is closer to `manual niche style profile` than to `trend intelligence model`.

## 7. Input Surface

Trend consumes exactly one meaningful runtime input today:
- `niche`

Indirect dependency:
- `trends_dir`

How inputs work today:

### 7.1 `niche`
- direct input through `TrendAnalysisInput`
- operational and required for non-fallback behavior
- used to construct `<trends_dir>/<niche>.json`

### 7.2 `trends_dir`
- service configuration, not part of `TrendAnalysisInput`
- default in code: `backend/data/trends`
- in the current repository snapshot this default path does not exist
- real tests and runners usually inject a custom `trends_dir`

This matters operationally:
- the service is implemented
- but the default path is not self-sufficient in the current repo snapshot
- runtime success depends on orchestrator/test/runner wiring a valid trends directory

### 7.3 Local JSON profile contents
Consumed fields from file:
- `niche`
- `dominant_hooks`
- `avg_duration`
- `pacing`
- `visual_style`
- `text_style`

### 7.4 Inputs it does not consume
Not consumed today:
- `account_id`
- topic
- publish history
- metrics
- QC
- platform trend APIs
- crawled social signals
- cache freshness
- temporal windows
- trend confidence
- account segment

Meaningfulness assessment:
- input surface is real but extremely narrow
- live context is absent
- direct evidence source is absent
- the subsystem is prototype-simple, not data-rich

## 8. Output Surface

Trend emits one main output object:
- `TrendProfile`

And one control trace:
- `fallback`

Field-by-field output assessment:

### 8.1 `dominant_hooks`
- deterministic: yes
- consumed downstream: yes
- used by: `Strategy`, `Script` prompt
- governance strength: advisory in `Script`, causal in `Strategy`

### 8.2 `avg_duration`
- deterministic: yes
- consumed downstream: effectively no direct operational use found
- governance strength: symbolic today

### 8.3 `pacing`
- deterministic: yes
- consumed downstream: yes
- used by: `Strategy`, `Asset`, `Script` prompt
- governance strength: moderate

### 8.4 `visual_style`
- deterministic: yes
- consumed downstream: yes
- used by: `Asset`, `Editor`, `Script` prompt
- governance strength: moderate in `Asset`, weak in `Editor`, advisory in `Script`

### 8.5 `text_style`
- deterministic: yes
- consumed downstream: no meaningful runtime use found
- governance strength: symbolic

### 8.6 `fallback`
- deterministic: yes
- consumed downstream indirectly through event emission and execution traces
- operational value: traceability and safe continuation

## 9. Current Decision Model

The Trend Analysis decision model today is:
- rule-free in the sense of no real inference engine
- file-backed
- deterministic
- niche-conditioned
- fallback-safe

What it actually does:
- normalize niche string
- open a JSON file by niche name
- copy a small set of fields into `TrendProfile`
- return fallback if missing or invalid

What it does not do:
- no ranking of competing trends
- no weighting
- no freshness computation
- no signal aggregation
- no temporal decay
- no account segmentation
- no topic adaptation
- no cross-run memory
- no evidence reasoning

Brutally honest characterization:
- current Trend Analysis is mostly static profile assembly

That does not mean it is useless.
It means its current value comes from:
- stable context injection
- deterministic style conditioning
- simple strategic hook/pacing activation

It is not a trend intelligence engine yet.

## 10. Downstream Consumption

### 10.1 Strategy
- reads `TrendProfile`: yes
- file: `backend/app/creative/agents/strategy/service.py`
- fields used:
  - `pacing`
  - `dominant_hooks`
- runtime effect:
  - `pacing == fast_first_3s` can upshift `hook_aggressiveness`
  - `dominant_hooks` containing `shock_statement` or `story_opening` can upshift `hook_aggressiveness`
- strength: strong relative to other Trend consumers

### 10.2 Script
- reads `TrendProfile`: yes
- file: `backend/app/content/script_gen/service.py`
- fields used in prompt assembly:
  - `dominant_hooks`
  - `pacing`
  - `visual_style`
- runtime effect:
  - indirect and prompt-mediated
  - no hard-coded script rule directly branches on trend fields inside `ScriptAgentService`
- strength: weak-to-moderate, because effect depends on generator response or deterministic fallback path

### 10.3 Voice
- reads `TrendProfile`: no direct use found
- strength: none

### 10.4 Asset / Asset Selection
- reads `TrendProfile`: yes
- files:
  - `backend/app/creative/agents/asset_selection/service.py`
  - `backend/app/creative/agents/asset/interpreter.py`
- fields used:
  - `visual_style`
  - `pacing`
- runtime effect:
  - `visual_style` populates `AssetPlan.visual_style`
  - `pacing == fast_first_3s` sets `motion_profile="subtle_push_in"`
  - `pacing` is added into segment tags
  - `pacing` changes segment effects in `_segment_effects(...)`
- strength: strong

### 10.5 Editor
- reads `TrendProfile`: yes
- files:
  - `backend/app/creative/agents/editor/service.py`
  - `backend/app/creative/agents/editor/interpreter.py`
- fields used:
  - `visual_style`
- runtime effect:
  - affects `editor_style_profile` naming when present
  - contributes to `_resolve_mood(...)` string material
- strength: weak-to-moderate
- note:
  - no direct use of `pacing`, `dominant_hooks`, or `text_style` found in editor logic

Important distinction:
- `TrendProfile` existing inside `CreativePack` is not the same as strong downstream control.
- strong consumption exists mainly in `Strategy` and `Asset`.
- `Script` and `Editor` consume it more softly.
- `Voice` does not consume it.

## 11. Relation To Learning / Strategy / Novelty

### Trend and Strategy
- Trend feeds Strategy materially.
- This is the clearest causal Trend relationship in current runtime.
- Strategy now converts Trend hook and pacing hints into actual profile shifts.

### Trend and Learning
- Learning does not feed Trend.
- Trend does not consume Learning.
- They are parallel upstream context layers, not a closed loop.

### Trend and Novelty
- Novelty does not depend on Trend directly.
- Trend does not consume Novelty.
- Both feed or complement downstream strategy behavior from different responsibilities.

Current relationship summary:
- Trend is upstream of Strategy causally.
- Trend is upstream of Learning only structurally in orchestrator order, not logically.
- Trend is upstream of Novelty only structurally in orchestrator order, not logically.
- Strategy is the stronger control layer.
- Learning and Novelty are becoming stronger strategic layers than Trend in the broader architecture.

This means Trend remains relevant, but not dominant.
Its current role is best described as:
- stable strategic context provider
- not optimization engine
- not adaptive intelligence layer

## 12. Fallback / Default Paths

Fallback exists and is explicit.

Fallback triggers when:
- `niche` is empty
- trend file does not exist
- any exception happens during loading/parsing

Fallback return:
- `TrendProfile(niche="default", dominant_hooks=["question"], avg_duration="8-12", pacing="baseline", visual_style="phase1_baseline", text_style="caption_focus")`
- `FallbackDecision(used=True, mode="SAFE_DEFAULT", reason="TREND_PROFILE_FALLBACK")`

Operational assessment:
- fallback is safe
- fallback is deterministic
- fallback is traceable through result payload and orchestrator event

Dominant operational path assessment:
- in tests and controlled runners, non-fallback path is often exercised by explicitly providing `trends_dir`
- in the current repository snapshot, the default path configured in the service does not appear to exist
- therefore, absent explicit injection of `trends_dir`, fallback would likely be the dominant path

This is a major maturity limitation.

## 13. Traceability And Auditability

Traceability exists, but is basic.

What is traceable today:
- `TrendAnalysisResult` is persisted in execution payloads
- `trend_profile` is persisted in `CreativePack`
- orchestrator emits:
  - `CREATIVE/trend_profile_loaded`
  - `CREATIVE/trend_profile_fallback`
- fallback use is visible

Where trace exists:
- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/models.py`
- runtime `execution_outputs.json` artifacts

What is not traceable today:
- no trend confidence
- no explanation of why a given trend profile was chosen beyond file identity
- no evidence provenance beyond the existence of the JSON file
- no timestamped trend source lineage
- no trend version field inside the profile

Auditability assessment:
- audit-friendly for fallback vs non-fallback
- audit-friendly for the exact profile emitted
- not audit-rich for evidence provenance or decision reasoning

## 14. Determinism And Governance

Determinism:
- yes
- same `niche` plus same JSON file content yields same `TrendProfile`
- fallback path is also deterministic

Versioning:
- no Trend-specific version field found
- no frozen baseline policy found for Trend

Policy freeze:
- none

Baseline governance:
- none found

Promotion status:
- no evidence found that Trend was promoted to baseline
- no dedicated Trend promotion artifact found
- no Trend-specific full validation gate found

Direct conclusion:
- Trend is deterministic
- Trend is not baseline-governed
- Trend is still prototype-governed only by code simplicity and surrounding pipeline governance

## 15. Test Surface

### 15.1 Direct Trend unit tests
- file: `tests/test_trend_analysis_agent_phase2_unittest.py`

What it proves:
- loads manual curated profile from a provided directory
- falls back when profile is missing

What it does not prove:
- downstream effect
- runtime usefulness
- live evidence handling
- account adaptation

### 15.2 Block 3 smoke
- file: `tests/test_phase2_block3_smoke_unittest.py`

What it proves:
- orchestrator calls Trend
- Trend output can reach the pipeline
- asset selection and QC still complete

What it does not prove:
- strategic strength of Trend
- robustness of default path

### 15.3 Strategy integration tests
- file: `tests/test_strategy_agent_phase2_unittest.py`
- file: `tests/test_strategy_agent_evolution_v2_0_integration_unittest.py`

What they prove about Trend:
- `TrendProfile` is a real Strategy input
- `pacing` and `dominant_hooks` can change strategy behavior

What they do not prove:
- Trend intelligence quality
- live trend validity

### 15.4 Script-related validation
- file: `backend/scripts/run_script_agent_excellence_gate.ps1`

What it proves indirectly:
- script generation contexts include `TrendProfile`
- different trend contexts are intentionally exercised

What it does not prove:
- stable product lift from Trend itself

### 15.5 Asset visual query validation
- file: `tests/validate_visual_query_pipeline.py`
- artifact: `OUT/audit/visual_query_validation/final_verdict.json`

What it proves indirectly:
- asset interpretation behaves coherently under different `TrendProfile` inputs
- especially `pacing` and `visual_style` combinations in scenario construction

What it does not prove:
- Trend agent loading behavior itself
- live trend evidence quality

Coverage assessment:
- direct Trend test coverage is small but clear
- integration coverage exists through Strategy, Asset, and orchestrator smoke paths
- governance-grade coverage is weak
- there is no dedicated full validation gate for Trend

## 16. Validation / Audit History

Meaningful Trend-specific audit history is limited.

Evidence found:
- `tests/test_trend_analysis_agent_phase2_unittest.py`
- `tests/test_phase2_block3_smoke_unittest.py`
- references in `backend/scripts/run_pre_phase3_system_final_gate.ps1`
- Trend appears inside broader execution artifacts and certification artifacts because it is part of full pipeline runs

What was actually validated:
- Trend can load a profile from an injected directory
- Trend fallback works
- Trend is present in full pipeline runtime artifacts
- Trend is structurally integrated into the orchestrator
- Trend contributes to downstream behavior in broader system tests

What was not found:
- no dedicated Trend full validation gate
- no dedicated Trend promotion verdict
- no Trend baseline promotion artifact
- no Trend-specific operational audit folder analogous to Strategy, Learning, Novelty, or QC

Conclusion:
- Trend has validation presence
- Trend does not have standalone governance history
- it was prototyped and integrated, but not formally promoted

## 17. Current Strengths

Actual strengths already present:
- deterministic profile generation
- explicit safe fallback
- runtime integration in orchestrator
- output persistence in `CreativePack`
- execution-level traceability through `trend_analysis`
- event emission for loaded vs fallback paths
- real downstream causality in `Strategy`
- real downstream causality in `Asset`
- prompt-level context injection into `Script`
- light style influence in `Editor`
- extremely small and understandable implementation surface

These are real strengths.
They are not enough to call the subsystem mature.

## 18. Current Weaknesses / Limitations

Brutally honest limitations:
- no live external trend evidence
- no account-specific trend adaptation
- no topic-level reasoning
- no temporal awareness
- no trend confidence model
- no memory of prior trend states
- no link to performance feedback
- no connection to Learning loop
- no connection to Novelty loop
- `avg_duration` is effectively unused
- `text_style` is effectively unused
- default configured path appears absent in current repo snapshot
- successful runtime often depends on manually injected `trends_dir`
- no dedicated baseline governance
- no dedicated promotion gate
- weak explainability beyond "file was loaded"
- lower strategic authority than `Strategy`, `Learning`, and `Novelty`

Most important limitation:
- the subsystem is called Trend Analysis, but today it is closer to `manual niche trend profile loader` than to a true analysis engine.

## 19. Maturity Assessment

### Technical implementation
- status: implemented
- assessment: solid for a small file-backed prototype

### Pipeline integration
- status: real
- assessment: good

### Downstream influence
- status: real but uneven
- assessment: moderate overall

### Strategic intelligence
- status: weak
- assessment: low

### Explainability
- status: partial
- assessment: moderate for emitted profile, low for reasoning depth

### Governance
- status: weak
- assessment: low

### Baseline readiness
- status: not ready
- assessment: no

Overall maturity stage:
- prototype / early alpha

More precise classification:
- `implemented, runtime-real, deterministic, context-providing prototype`

Safe to rely on strategically in production?
- not as a primary intelligence layer
- yes as a stable, low-risk context provider when wired with explicit `trends_dir`
- no as a source of true trend intelligence

## 20. Gap Between Current Prototype And Target Trend Analysis Agent

### Niche trend detection
- current: manual JSON by niche
- target: actual evidence-based niche trend detection
- gap: large

### Hook trend detection
- current: static `dominant_hooks` from file
- target: empirically updated hook family detection
- gap: large

### Pacing inference
- current: static `pacing` from file
- target: inferred pacing from platform or performance evidence
- gap: large

### Visual style inference
- current: static `visual_style` from file
- target: live style trend inference or validated style priors
- gap: large

### Text style inference
- current: field exists but is not meaningfully consumed
- target: real text style policy influencing script/editor/caption behavior
- gap: very large

### Account-level trend adaptation
- current: none
- target: account-aware trend conditioning
- gap: very large

### Temporal trend memory
- current: none
- target: time-aware trend state with refresh and decay
- gap: very large

### Trend confidence
- current: none
- target: confidence and provenance metadata
- gap: very large

### Downstream enforcement
- current: strongest in `Strategy` and `Asset`, weaker elsewhere
- target: more consistent downstream behavioral control
- gap: medium-to-large

### Live platform evidence
- current: none
- target: live or recent evidence ingestion
- gap: very large

## 21. Next Correct Move

The next correct move is not a broad roadmap.
It is this:

- write a formal `Trend Analysis Agent v2` implementation plan centered on input activation and contract hardening

Why this is the correct next move:
- the current prototype is real enough to analyze clearly
- it is not governed strongly enough for baseline promotion
- its main weakness is not orchestration absence; it is evidence absence
- the biggest improvement opportunity is activating real inputs, not adding more symbolic fields

Concretely, the next move should focus on:
- replacing or augmenting manual niche-only loading with a defined evidence source model
- hardening contracts with provenance and confidence
- deciding whether Trend remains a separate layer or is intentionally kept as a lightweight context provider beneath stronger layers like `Strategy`, `Learning`, and `Novelty`

The wrong next move would be:
- promoting Trend as if it were already a mature intelligence subsystem
- adding aspirational fields without activating real inputs
- overstating current capability

## Implementation Grounding Notes

Primary implementation files inspected:
- `backend/app/creative/agents/trend_analysis/service.py`
- `backend/app/creative/agents/trend_analysis/models.py`
- `backend/app/creative/contracts/creative_pack.py`
- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/models.py`
- `backend/app/creative/contracts/orchestrator_io.py`
- `backend/app/creative/agents/strategy/service.py`
- `backend/app/content/script_gen/service.py`
- `backend/app/creative/agents/asset/interpreter.py`
- `backend/app/creative/agents/asset_selection/service.py`
- `backend/app/creative/agents/editor/interpreter.py`

Primary tests inspected:
- `tests/test_trend_analysis_agent_phase2_unittest.py`
- `tests/test_phase2_block3_smoke_unittest.py`
- `tests/test_phase2_block4_smoke_unittest.py`
- `tests/test_strategy_agent_evolution_v2_0_integration_unittest.py`
- `tests/validate_visual_query_pipeline.py`

Relevant artifacts inspected:
- `OUT/manual_pipeline_batch_5_current_run/all_agents_all_videos_outputs.json`
- `OUT/audit/visual_query_validation/final_verdict.json`

Final classification in one line: 
- the Trend Analysis Agent Phase 1 is a real, deterministic, file-backed context provider with partial downstream causal effect, but it is still prototype-grade and not baseline-worthy.
