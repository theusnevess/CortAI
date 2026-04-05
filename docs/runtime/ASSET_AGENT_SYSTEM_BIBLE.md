# ASSET_AGENT_SYSTEM_BIBLE

## 1. Executive Summary
The Asset Agent is now a governed, deterministic, multi-stage visual selection subsystem integrated into the CortAI creative pipeline. It no longer behaves as a simple phase-1 asset picker. It now includes:
- script-aware interpretation into an `AssetPlan`
- segment-level planning for `hook`, `setup`, and `payoff`
- explicit runtime-local source routing
- local catalog selection with offline-ingested external supply
- event-aware scoring
- visual-world and atmosphere-aware scoring
- legacy-family rejection and documentary-transition correction
- runtime traceability via `visual_trace`

What is solid today:
- architectural position and runtime integration are solid
- deterministic local runtime is solid
- catalog and offline ingestion infrastructure are solid
- external real-asset routing exists and is operational
- ranking logic is deep and heavily constrained
- tests cover interpreter, selector, router, supply ingestion, SD registration, and runtime integration

What is unresolved today:
- the formal decision contract is incomplete in persisted runtime outputs
- segment-level `entity`, `anomaly`, `photographability`, and human-readable justification are not persisted in the runtime trace even though the interpreter computes approximations of them
- product-level visual maturity is still below the level of the reference videos and below Script/Voice
- visual-world enforcement is still soft enough that some videos remain structurally similar to phase 1
- atmosphere coherence and intra-video cinematic continuity remain partial

Honest subsystem status today:
- **HOLD**

Why `HOLD`:
- `OUT/audit/asset_agent_decision_gate_v1_0/final_verdict.json` is `HOLD`
- `OUT/audit/script_voice_asset_pipeline_final_gate/final_verdict.json` is `HOLD`
- retained refinements show local wins, including documentary-transition improvement, but not a clean subsystem-wide promotion state
- human review of recent videos still identified residual phase-1 visual structure, especially in setup and family repetition

## 2. Current Mission of the Asset Agent
In current code, the Asset Agent does more than asset selection and less than a full cinematic director.

Operationally, today it behaves as:
- an **event-aware selector**
- a **partial visual director**
- a **partial cinematic/world-constrained selector**

It does not yet behave as a fully mature cinematic director, because:
- it defines a video-level visual world only through soft tag-based constraints
- it still resolves assets segment by segment
- runtime outputs do not persist formal segment justifications
- human review still observes legacy visual solution lock-in and setup weakness

Practical description of what it does today:
- reads the script triplet (`hook/setup/payoff`)
- derives `visual_anchor`, `semantic_pattern`, `entity`
- derives per-segment event/anomaly/visibility/photographability signals
- derives a video-level visual world profile
- converts all of that into segment categories, tags, and source requests
- lets the selector compete local catalog candidates under many scoring rules
- routes to local catalog or safe fallback
- passes a resolved `AssetPlan` into the render pipeline

## 3. What the Asset Agent Is and Is Not Responsible For
### Asset Agent responsibilities
Belongs to Asset Agent today:
- decide visual representation per segment
- infer segment categories
- infer event/anomaly signals per segment
- infer source request (`local`)
- score and select backgrounds from the local catalog
- maintain asset usage pressure via runtime `usage_count` increments
- provide runtime `visual_trace`
- influence setup/payoff handling via scoring and rejection logic
- influence visual world continuity through soft selection constraints

### Script Agent responsibilities
Belongs to Script Agent:
- generate `hook/setup/payoff`
- define narrative wording and content structure
- decide text-level storytelling
- produce narration text

### Voice Agent responsibilities
Belongs to Voice Agent:
- resolve `VoicePlan`
- determine provider/voice/style/delivery metadata
- govern voice routing constraints
- not select visual assets

### Editor / future video-layer responsibilities
Does not belong to Asset Agent today:
- transitions
- pacing edits beyond segment-level indirect effects
- montage grammar
- shot order redesign beyond `hook/setup/payoff`
- true scene construction through compositing logic
- advanced cinematic editing

### Video QC responsibilities
Belongs to Video QC, not Asset Agent:
- final accept/reject on rendered output
- detect dark payoff / missing metadata / invalid final product conditions

This boundary matters because the Asset Agent currently controls selection and some framing pressure, but not a full editorial layer.

## 4. Architectural Position in the CortAI Pipeline
Primary files:
- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/agents/asset_selection/service.py`
- `backend/app/creative/agents/asset/interpreter.py`
- `backend/app/runtime/asset_router.py`
- `backend/app/content/pipeline/orchestrator.py`

Text diagram:

```text
CreativeOrchestratorService
  -> ScriptAgentService
  -> AssetSelectionAgentService
       -> AssetInterpreterService
       -> AssetSelector
  -> VoiceAgentService
  -> ContentPipelineService
       -> ContentPipelineOrchestrator
            -> AssetRouter
                 -> AssetSelector
            -> RenderAdapter
            -> PublishAdapter
  -> VideoQcAgentService
```

Inputs received by Asset Agent path:
- `niche`
- `topic`
- `StrategyProfile`
- `TrendProfile`
- `ScriptPlan`
- deterministic seed derived from niche/topic/script content

Outputs created:
- `AssetPlan` embedded inside `CreativePack`
- later, a resolved `AssetPlan` with concrete asset paths in runtime
- runtime `visual_trace`

## 5. End-to-End Runtime Flow
Actual implemented flow:

1. `CreativeOrchestratorService._build_creative_pack_from_context(...)` in `backend/app/creative/orchestrator/service.py`
2. `ScriptAgentService.generate(...)` creates the `ScriptPlan`
3. `AssetSelectionAgentService.select(...)` in `backend/app/creative/agents/asset_selection/service.py`
4. `AssetInterpreterService.build_plan(...)` in `backend/app/creative/agents/asset/interpreter.py`
   - computes anchor/entity/pattern
   - computes per-segment event profiles
   - computes visual world profile
   - returns an unresolved `AssetPlan`
5. `AssetSelectionAgentService.select(...)`
   - tries local selection for each segment using `AssetSelector.select(...)`
   - if no local path wins, leaves the segment unresolved for runtime fallback
6. `CreativePack` is built with `asset_plan`
7. `ContentPipelineService.run_pipeline(...)`
8. `ContentPipelineOrchestrator.execute(...)` in `backend/app/content/pipeline/orchestrator.py`
9. `AssetRouter.resolve_plan(...)` in `backend/app/runtime/asset_router.py`
   - resolves each segment in order: `hook`, `setup`, `payoff`
   - uses explicit local path if already present
   - otherwise re-selects local runtime asset via `AssetSelector`
   - otherwise uses safe fallback if allowed
10. resolved `AssetPlan` is passed into `RenderAdapter.render_video(...)`
11. render pipeline writes video and metadata
12. `VideoQcAgentService.evaluate(...)` runs after render

Important consequence:
- there are two selection layers: creative-time unresolved planning and runtime path resolution
- runtime remains authoritative for final path resolution

## 6. Contracts and Data Structures
Primary contract file:
- `backend/app/creative/contracts/creative_pack.py`

### Operational contract
#### `AssetBackgroundPlan`
Fields:
- `source`
- `path`
Used operationally:
- yes
- runtime reads `source` and `path`

#### `AssetSegmentPlan`
Fields:
- `background`
- `category`
- `tags`
- `effects`

Used operationally:
- yes
- selector and router depend on `category` and `tags`
- render uses resolved plan paths and effects indirectly

#### `AssetRuntimeConstraints`
Fields:
- `allow_safe_fallback`
- `deterministic_seed`

Used operationally:
- yes
- router depends on all three

#### `AssetPlan`
Fields:
- `hook_asset`
- `setup_asset`
- `payoff_asset`
- `visual_style`
- `motion_profile`
- `visual_anchor`
- `semantic_pattern`
- `entity`
- `segments`
- `runtime_constraints`

Used operationally:
- yes
- resolved paths are persisted into `hook_asset/setup_asset/payoff_asset`
- `visual_anchor`, `semantic_pattern`, `entity` are also used in runtime trace and query text

### Intended vs operational contract gap
Documented/expected by `docs/runtime/ASSET_AGENT_DECISION_STANDARD.md` but not present as first-class persisted fields in `AssetPlan`:
- segment-level `entity`
- segment-level `anomaly`
- segment-level `photographability`
- human-readable `justification`
- compatibility notes for voice/text/music

What exists only implicitly today:
- segment-level event/anomaly/visibility/photographability are encoded as tags
- video-level world and emotion fields are encoded as tags

What is operational but not explicit as structured contract:
- event profile fields produced by interpreter:
  - `entity`
  - `event`
  - `anomaly_type`
  - `visibility_requirement`
  - `photographability`
- visual world fields produced by interpreter:
  - `visual_family`
  - `environment_type`
  - `lighting_style`
  - `color_palette`
  - `texture_profile`
  - `realism_level`
  - `dominant_emotion`
  - `secondary_emotion`
  - `tension_level`
  - `mood`
  - `preferred_families`
  - `preferred_moods`
  - `allowed_categories`
  - `forbidden_patterns`

These are not persisted as structured nested objects in `AssetPlan`. They are flattened into tags.

### Runtime trace structures
`AssetRouter.resolve_plan(...)` returns a trace with:
- `render_job_id`
- `visual_anchor`
- `semantic_pattern`
- `entity`
- `rows`

Each row contains:
- `segment`
- `requested_asset`
- `resolved_asset`
- `category`
- `tags`
- `effects`
- `source`

What is persisted to runtime outputs:
- yes, via `PipelineResult.visual_trace`
- also written by pipeline orchestrator to `OUT/audit/asset_agent_runtime/visual_trace.json`

What is still missing from runtime trace:
- explicit segment `entity`
- explicit segment `event`
- explicit segment `anomaly`
- explicit segment `photographability`
- human-readable explanation for why the winning asset beat alternatives
## 7. Asset Decision Logic
Main files:
- `backend/app/creative/agents/asset/interpreter.py`
- `backend/app/runtime/asset_selector.py`

### High-level flow
The actual decision chain is:
- detect hook type
- derive `visual_anchor`
- derive `semantic_pattern`
- derive `entity`
- derive per-segment category
- derive per-segment event profile
- derive per-segment tags and source request
- select assets under scoring and rejection rules

### Hook / setup / payoff handling
#### Hook
Interpreter behavior:
- prefers explicit anomaly/event categories
- examples: `warning_display`, `intercom_recorder`, `document`
- tags include `high_impact`

Selector behavior:
- boosts hook strength heavily via `_segment_strength(..., role='hook')`
- gives framing bonus to `closeup`/`medium`
- prefers immediate event evidence

#### Setup
Interpreter behavior:
- category is usually contextual, e.g. `archive`, `institutional_space`, `horror_interior`
- tags include `context`
- event visibility is often downgraded from explicit to implicit for setup

Selector behavior:
- setup is the most constrained role
- setup uses `setup_specificity_score`
- setup uses `setup_event_alignment_score`
- setup can be hard rejected if generic or legacy and below quality floor
- setup is also affected by documentary-specific floor and legacy-family detection

#### Payoff
Interpreter behavior:
- payoff category usually returns to strongest event-bearing category
- tags include `reveal`
- payoff often requires explicit event visibility

Selector behavior:
- payoff heavily weights `payoff_strength_score`
- payoff gets closeup/detail framing bonus
- payoff is penalized if under-delivering or not explicit enough

### Entity usage
Entity is computed at plan level in interpreter and persisted in `AssetPlan.entity`.
Current values are things like:
- `camera`
- `door`
- `room`
- `intercom`
- `recorder`
- `signal`
- `corridor`
- `document`
- `device`
- `map`

Entity influences:
- category derivation
- query text used by selector/router
- segment event profiles indirectly

### Event and anomaly usage
Interpreter computes per segment:
- `event`
- `anomaly_type`
- `visibility_requirement`
- `photographability`

These influence:
- source choice (`local` vs `sd`)
- tags like `event_*`, `anomaly_*`, `evidence_*`, `visibility_*`, `photo_*`
- selector scoring through `event_evidence_score`, setup alignment, documentary linkage, world scoring

### Quality floor behavior
Implemented in selector:
- `_setup_has_quality_floor(...)`
- `_documentary_setup_quality_floor(...)`

Setup quality floor accepts setup only if at least one is true:
- event hint exists
- contextual evidence exists with enough setup-event alignment
- tension increase exists

Documentary setup floor is stronger and requires things like:
- anomaly marker
- case surface
- institutional signal plus closer framing
- investigative context beyond room ambience

### Setup rejection behavior
+Actual hard rejections in `AssetSelector.select(...)`:
- reject setup if legacy family and not above setup quality floor
- reject documentary setup if documentary floor not met
- reject generic setup if generic and weak on both event alignment and visual world support
- reject non-positive or below-threshold candidates

### Payoff enforcement behavior
Implemented by:
- `_segment_role_bonus(... role='payoff')`
- `_payoff_under_delivery_penalty(...)`
- `_framing_bonus(... role='payoff')`

Operationally payoff is enforced as:
- more detail/closeup preference
- stronger event evidence requirement
- penalty if too similar to generic setup framing

## 8. Source Decision Logic (REAL vs AI)
Primary files:
- `backend/app/creative/agents/asset/interpreter.py`
- `backend/app/runtime/asset_router.py`
- `backend/app/agents/asset/sd_generator.py`

### Real is default
Current logic makes `local` the default source for most segments.

Implemented in `_background_source(...)`:
- if `event_profile.photographability == 'needs_generation'` -> `sd`
- if payoff is explicit and event is one of:
  - `containment_breach`
  - `impossible_state`
  - `distorted_presence`
  then `sd`
- otherwise `local`

### What photographability means in current code
Current photographability is heuristic, not model-based. It means:
- `real`: the event is judged representable with real-world imagery
- `needs_generation`: the event is judged visually impossible or too dependent on synthetic anomaly rendering

Triggers for `needs_generation` include:
- words like `impossible`, `wrong shadow`, `distorted`, `warped`, `moved by itself`
- glitch/device anomaly in hook or payoff in some conditions
- some presence/breach payoff cases outside strongly representable anchors

### How SD is actually used
The runtime no longer includes synthetic image generation.
Asset resolution is constrained to runtime-eligible real catalog entries and safe fallback.

Actual runtime behavior in `AssetRouter._resolve_segment(...)`:
1. explicit path if already present
2. if requested source is `sd`, generate immediately
3. else try local selector
4. else if `allow_safe_fallback`, use safe fallback asset

This means SD is:
- explicit when interpreter asks for it
- otherwise fallback only

### Runtime locality
This is a hard architectural rule and current code honors it:
- runtime does not call Pexels/Unsplash/Pixabay
- runtime uses local catalog only
- ingestion is offline

## 9. Catalog and Supply System
Primary files:
- `backend/app/assets/catalog.json`
- `backend/app/assets/catalog_registry.py`
- `backend/app/assets/import_assets.py`
- `backend/app/assets/ingestion_common.py`
- `backend/app/assets/pexels_ingestor.py`
- `backend/app/assets/unsplash_ingestor.py`
- `backend/app/assets/pixabay_ingestor.py`

### Catalog structure
Operational fields in catalog entries include:
- `path`
- `source_type`
- `category`
- `subtype`
- `tags`
- `resolution`
- `hook_strength_score`
- `payoff_strength_score`
- `realism_score`
- `usage_count`
- `family`
- `framing`
- `mood`
- `semantic_pattern_fit`
- `entity_fit`
- `setup_specificity_score`
- `genericity`
- `strength`
- `freshness_score`
- `prompt`
- `seed`
- `ingested_at`

### Current catalog composition
Current catalog counts from `backend/app/assets/catalog.json`:
- total assets: `161`
- `pexels`: `85`
- `local_curated`: `52`
- `unsplash`: `23`
- `sd`: `1`
- `pixabay`: `0`

Top categories currently present:
- `corridor`: `28`
- `archive`: `24`
- `warning_display`: `19`
- `intercom_recorder`: `19`
- `sealed_access`: `19`
- `document`: `17`
- `institutional_space`: `15`

Important note:
- provider integration exists for Pixabay, but the retained catalog currently contains no `pixabay` entries

### Ingestion workflow
Offline ingestion flow:
1. call `backend/app/assets/import_assets.py --source ...`
2. pick ingestor based on source
3. ingestor calls provider API
4. download image bytes
5. `normalize_and_store(...)` in `ingestion_common.py`
6. resize/crop to `1080x1920`
7. write file under `assets/imports/<source>/<category>/...`
8. upsert into `catalog.json`

### What is implemented vs validated
Implemented:
- Pexels API ingestion
- Unsplash API ingestion
- Pixabay API ingestion
- local SD generation
- catalog upsert and usage-count incrementing

Validated in current retained tests:
- Pexels ingestor mocked unit test
- Pixabay ingestor mocked unit test
- Unsplash missing-key guard
- SD generator mocked pipeline registration

Validated in retained audits:
- external ingestion infrastructure is present in code
- documentary and cinematic batches use imported assets from `pexels` and `unsplash`

Not fully proven by retained artifacts today:
- large-scale ongoing supply refresh operations as a persistent operational regimen
- strong real usage of Pixabay specifically

## 10. Selection and Ranking System
Primary file:
- `backend/app/runtime/asset_selector.py`

### Scoring dimensions currently active
The selector currently scores by all of the following:
- category correctness via `_category_score(...)`
- raw tag overlap
- query-token overlap
- subtype overlap
- semantic overlap
- segment strength (`hook_strength_score`, `payoff_strength_score`, blended setup strength)
- `realism_score`
- `freshness_score`
- `strength`
- fit bonus from semantic/entity/mood/subtype matches
- framing bonus
- subtype bonus
- `event_evidence_score`
- `visual_world_score`
- `atmosphere_emotion_score`
- `setup_event_alignment_score`
- `documentary_case_linkage_score`
- `style_coherence_score`
- controlled bonus for newer real sources via `_new_real_source_bonus(...)`
- segment-role-specific logic via `_segment_role_bonus(...)`

Penalties currently active:
- `genericity`
- usage penalty via `_usage_penalty(...)`
- family repetition via `_family_usage_penalty(...)`
- generic setup penalty via `_setup_generic_penalty(...)`
- visual world break penalty via `_visual_world_break_penalty(...)`
- style break penalty via `_style_break_penalty(...)`
- payoff under-delivery penalty via `_payoff_under_delivery_penalty(...)`
- legacy dominance penalty via `_legacy_dominance_penalty(...)`
- legacy family penalty via `_legacy_family_penalty(...)`
- documentary transition penalty via `_documentary_transition_penalty(...)`
- SD penalty: `generated_sd` gets penalized; `sd` gets only a small payoff/hook allowance

Hard filters / rejections:
- setup legacy family without quality floor -> reject
- documentary setup without documentary floor -> reject
- generic setup with weak event/world support -> reject
- non-positive final score -> reject
- below minimum score -> reject

### What dominates ranking in practice
Current ranking is dominated by a combination of:
1. category correctness
2. segment-role strength
3. event evidence
4. world/style compatibility
5. setup-specific quality filters

In practice this means:
- the selector is no longer a simple semantic matcher
- but it still behaves as a soft weighted system, not a hard compositional scene planner
### Where conflicts exist
The current main internal conflict is:
- **event specificity vs world continuity**

Observed failure pattern from retained audits:
- world constraints sometimes overpower event-specific evidence
- example: a video can stay atmospherically coherent while drifting from the exact event representation requested

Another conflict:
- **documentary ambience vs evidence progression**
- partially corrected by documentary transition rules, but not universally solved

## 11. Event Representation Logic
Primary file:
- `backend/app/creative/agents/asset/interpreter.py`

### How the system moved beyond entity-only selection
The shift happened through `_segment_event_profile(...)` and event-signal tags.

Per segment, the interpreter now emits:
- `entity`
- `event`
- `anomaly_type`
- `visibility_requirement`
- `photographability`

Examples of current event labels:
- `active_warning_state`
- `data_inconsistency`
- `document_anomaly`
- `unauthorized_presence`
- `sealed_containment`
- `containment_breach`
- `route_erasure`
- `impossible_state`
- `archive_context`
- `institutional_context`
- `ambient_context`

Examples of anomaly types:
- `audio_triggered_device_state`
- `temporal_contradiction`
- `evidence_irregularity`
- `presence_signal`
- `restricted_access`
- `containment_breach`
- `navigation_contradiction`
- `signal_distortion`
- `visual_impossibility`

### How these signals influence selection
The interpreter converts them into tags such as:
- `event_*`
- `anomaly_*`
- `visibility_*`
- `photo_*`
- `evidence_*`
- `context_*`

The selector then interprets those tags in:
- `_requested_event_signals(...)`
- `_event_signal_expansion(...)`
- `_event_evidence_score(...)`
- `_setup_event_alignment_score(...)`
- documentary linkage logic

### What event visibility means today
Operationally:
- `explicit` means the frame should show direct evidence of the anomaly/event
- `implicit` means setup can suggest the anomaly or its environment without full reveal

Strength of current event logic:
- strong for documents and warning/intercom/device anomalies
- reasonably strong for sealed-access horror families
- weaker when the system must represent a specific event while also preserving world continuity in contextual middle segments

## 12. Visual World / Cinematic Direction Logic
Primary file:
- `backend/app/creative/agents/asset/interpreter.py`
- selector support in `backend/app/runtime/asset_selector.py`

### Global video-level fields that exist today
The interpreter computes a `visual_world_profile` with:
- `visual_family`
- `environment_type`
- `lighting_style`
- `color_palette`
- `texture_profile`
- `realism_level`
- `dominant_emotion`
- `secondary_emotion`
- `tension_level`
- `mood`
- `preferred_families`
- `preferred_moods`
- `allowed_categories`
- `forbidden_patterns`

### How atmosphere/emotion are derived
The interpreter derives them heuristically from:
- `niche`
- `visual_anchor`
- `semantic_pattern`
- `entity`
- topic tokens
- set of segment events

Examples:
- documents -> `documentary_caseworld`
- devices/intercoms -> `institutional_device_alert`
- sealed/voice anomaly -> `sealed_institutional_horror`
- corridor worlds -> `institutional_passage_tension`

### How they constrain selection
They are translated into tags:
- `visual_family_*`
- `environment_type_*`
- `lighting_style_*`
- `dominant_emotion_*`
- `secondary_emotion_*`
- `mood_*`
- `world_allow_*`
- `world_family_*`
- `world_mood_*`
- `world_forbid_*`
- emotion-derived `constraint_*` tags

The selector uses them through:
- `_visual_world_fields(...)`
- `_visual_world_score(...)`
- `_atmosphere_emotion_score(...)`
- `_visual_world_break_penalty(...)`
- `_style_break_penalty(...)`

### Are they hard or soft constraints?
Mostly soft.
Hardness exists only indirectly through setup rejection and forbidden-pattern penalties.
There is no hard global video-level world object persisted in runtime that blocks out-of-world choices structurally.

### Why the cinematic layer is still insufficient
Retained audits and human review show:
- `visual_world_consistency` remains medium
- `atmosphere_coherence` remains low in the cinematic audit
- videos can still feel like three selected images rather than one scene evolving
- some setup segments remain world-compatible but event-light or visually phase-1-like

So the cinematic/world layer is operational, but still partial.

## 13. Setup / Payoff Handling Rules
This is the most critical practical section of the current subsystem.

### Setup today
Setup is handled through a combination of:
- interpreter category assignment toward contextual families
- `setup_specificity_score`
- `setup_event_alignment_score`
- setup-specific penalties
- hard rejection of weak legacy setups
- documentary setup floor

What setup must do operationally today:
- not be generic filler
- support the same world
- carry event hint, contextual evidence, or tension

What still leaks:
- contextual middle segments can still be plausible but not vivid
- documentary mid-video progression improved, but not fully system-wide cinematic
- some non-documentary setups still read as refined context rather than live event progression

### Payoff today
Payoff is more strongly enforced than setup.
Current rules favor:
- close/detail framing
- explicit event evidence
- stronger event score than setup
- stronger payoff strength score

This is why recent audits repeatedly showed:
- hook good
- setup weaker
- payoff acceptable/good

### Actual difference between setup and payoff
Current implementation makes payoff much more direct and explicit. Setup is intentionally allowed to be more implicit, but the system still struggles to make that implicitness feel cinematic rather than functional.

## 14. Legacy Dependency Handling
Primary file:
- `backend/app/runtime/asset_selector.py`

### Current legacy family detection
Implemented in `_legacy_visual_family(...)`.
Detected legacy families include:
- `generic_archive_shelf`
- `open_walkway`
- `neutral_hallway`
- `generic_corridor`
- `empty_room_context`

### How legacy families are penalized
Mechanisms:
- `_legacy_family_penalty(...)`
- hard setup rejection when legacy family fails quality floor
- `_legacy_dominance_penalty(...)`
- `_family_usage_penalty(...)`

### Which phase-1 families still survive
They survive mainly when:
- they carry enough contextual evidence to pass quality floor
- no better alternative exists
- they fit world/style sufficiently

Retained documentary-transition audit shows the residual issue was concentrated in:
- archive ambience / records room / shelf families

Status after documentary transition refinement:
- generic documentary transition is reduced materially but not eliminated absolutely
- one residual case still used `archive_storage_real_02`

### Where dependency on phase 1 still remains
Based on retained audits and human review:
- structural setup logic still risks phase-1 visual solution lock-in
- especially in documentary and contextual mid-video slots
- dependency is now narrower than before, but not gone globally

## 15. Determinism Guarantees
Determinism exists in multiple layers.

### Selection determinism
- `AssetSelectionAgentService._selection_key(...)` hashes niche/topic/script triplet
- `AssetSelector._deterministic_jitter(...)` uses `sha256(seed::entry_path)`
- selection order is deterministic for same seed/catalog/query state

### Router determinism
- `AssetRouter` resolves segments in fixed order
- runtime seed is `deterministic_seed` or `render_job_id`
- segment-level seeds are `seed:hook`, `seed:setup`, `seed:payoff`

### SD determinism
- no synthetic-generation determinism remains in the runtime path

### Runtime locality
- runtime does not fetch from external image APIs
- all ingestion is offline
- SD runs locally

### Weak points
- determinism depends on catalog state staying fixed; if `usage_count` changes between runs, ranking can change by design
- SD determinism still depends on the local model/runtime stack remaining stable
- one retained integrated gate noted an SD fallback OOM issue on a separate voice integration test path

## 16. Runtime Traceability
Traceability exists, but is incomplete.

### What exists
`visual_trace` currently gives:
- requested vs resolved asset per segment
- segment category
- full tag set used at runtime
- effects
- resolved source
- top-level anchor/pattern/entity

Catalog also tracks:
- `source_type`
- `usage_count`
- `freshness_score`
- `prompt` and `seed` for SD-generated assets

Usage counts are incremented in runtime via:
- `increment_usage_counts(...)` in `backend/app/assets/catalog_registry.py`

### What can be reconstructed today
Can reconstruct:
- which asset path won
- whether it came from local vs SD vs fallback
- what tags and category were requested
- what world/event tags were active
- whether usage_count increased

### What cannot yet be reconstructed cleanly
Cannot reconstruct cleanly from persisted runtime outputs:
- formal segment-level `entity`
- formal segment-level `anomaly`
- formal segment-level `photographability`
- explicit textual justification of why winner beat runner-up
- runner-up candidate list and score breakdown

This is exactly why the decision gate still holds.
## 17. Current Test Surface
Asset-relevant tests retained today:
- `tests/test_asset_interpreter_unittest.py`
- `tests/test_asset_selection_agent_phase2_unittest.py`
- `tests/test_asset_router_unittest.py`
- `tests/test_asset_plan_runtime_integration_unittest.py`
- `tests/test_asset_event_representation_unittest.py`
- `tests/test_asset_selector_adoption_unittest.py`
- `tests/test_asset_ingestors_unittest.py`
- `tests/test_sd_generator_unittest.py`
- `tests/test_phase2_block3_smoke_unittest.py`
- `tests/test_phase2_block4_smoke_unittest.py`

### Coverage meaningfully explained
#### Interpreter tests
Verify that:
- anchor/entity derivation works
- documentary hooks map to document anchor
- intercom warnings produce correct categories and event tags
- sealed-room whisper produces breach/presence signals
- visual-world profile is shared across segments

#### Asset selection agent tests
Verify that:
- local asset selection works end to end
- fallback triggers when local assets are unavailable
- intercom warning uses specialized local assets

#### Router tests
Verify that:
- explicit local path wins when present
- SD generation works when requested
- plan-requested SD takes priority over local catalog matches

#### Runtime integration test
Verifies that:
- resolved asset plan is what render receives
- `visual_trace` is passed through runtime result

#### Event representation tests
Verify that:
- event-bearing evidence beats generic same-entity assets
- generic corridor loses when archive context is requested
- corporate setup is penalized under dark documentary world
- legacy corridor setup can be rejected or allowed based on event support
- documentary setup prefers case-linked evidence over archive ambience
- documentary ambience can be rejected entirely without case linkage

#### Adoption test
Verifies that:
- a semantically-equivalent new real asset can beat a legacy one under current selector logic

#### Ingestor tests
Verify that:
- Pexels and Pixabay ingest query register assets (mocked)
- Unsplash key requirement is enforced

#### SD test
Verifies that:
- local SD generation registers an SD asset and metadata

#### Smoke tests
Phase 2 block smokes verify that:
- trend/asset context reaches pipeline and QC
- learning/experiment context also reaches pipeline and QC

### What is still not well covered
- no test persists full formal decision contract because contract does not exist yet
- no goldens for cinematic/world coherence at product level
- limited direct test coverage for all selector sub-scores as a score breakdown contract
- little explicit test coverage for inter-video family repetition behavior as a batch-level policy
- no direct test coverage for runner-up analysis or explanation trace persistence

## 18. Audit History and What Each Audit Proved
Important note: `OUT/audit` was cleaned aggressively earlier. Retained audit folders represent the currently preserved evidence. Some earlier supply/adoption audit folders are no longer on disk and must therefore be treated as historically referenced but not retained as current filesystem evidence.

### `asset_agent_decision_gate_v1_0`
Purpose:
- formal gate against the canonical decision standard

What it proved:
- source discipline was high
- system compatibility was medium
- narrative alignment was medium
- formal decision integrity was low

Verdict:
- `HOLD`

Why:
- justifications and explicit entity/anomaly fields were not persisted in runtime outputs

### `asset_event_representation`
Purpose:
- prove move from entity-based toward event-aware selection

What it proved:
- event representation improved materially
- payoff strength high
- setup specificity medium
- 5 real rendered videos approved by QC

Verdict:
- `GO` for that narrow refinement, not final subsystem promotion

### `asset_visual_direction_refinement`
Purpose:
- improve setup specificity, family repetition, intra-video style coherence

What it proved:
- event expression improved
- setup-event alignment improved
- payoff remained strong
- repetition and style coherence remained only medium

Verdict:
- `HOLD`

### `cinematic_asset_direction`
Purpose:
- introduce visual-world and cinematic-direction layer

What it proved:
- event visibility high
- scene continuity medium
- visual-world consistency medium
- atmosphere coherence low

Verdict:
- `HOLD`

### `asset_setup_phase1_dependency_break`
Purpose:
- break phase-1 dependence in setup/middle segments

What it proved:
- generic filler was reduced
- but setup generic rate in rendered videos was still too high

Verdict:
- `HOLD`

### `asset_documentary_transition_break`
Purpose:
- break residual documentary archive-ambience transition pattern

What it proved:
- documentary setups materially shifted toward evidence-linked middle frames
- video documentary setup generic rate dropped to `0.0`
- case linkage became high
- one residual archive ambience case still existed

Verdict:
- `GO` for this narrow refinement

### `script_voice_asset_pipeline_final_gate`
Purpose:
- integrated final gate across Script, Voice, Asset, and runtime pipeline

What it proved:
- script, voice, and asset governance are intact
- runtime traceability is high
- pipeline coherence medium
- perceptual unity partial

Verdict:
- `HOLD`

Why:
- formal asset decision contract missing in runtime outputs
- retained SD fallback regression noted in a voice integration test path

### Human-review-driven corrections
Human review repeatedly corrected over-optimistic subsystem verdicts. Across recent iterations, human review established that:
- the system improved structurally before it improved perceptually
- setup remained the main leak
- family repetition, not just file repetition, remained a major problem
- documentary transitions required targeted hardening
- even after cinematic/world additions, the subsystem still looked too phase-1-derived overall

## 19. Evolution Timeline (Major Phases / Refinements)
This timeline reflects what can be reconstructed from current code, tests, retained docs, and retained audits.

1. **Phase 2 asset selection baseline**
- objective: basic governed asset planning and selection
- outcome: `AssetPlan`, selector, router, runtime integration established
- current relevance: foundation; still active

2. **Decision standard documentation**
- objective: define what the Asset Agent should decide per segment
- outcome: `docs/runtime/ASSET_AGENT_DECISION_STANDARD.md` and gate doc created
- current relevance: canonical standard; not fully satisfied operationally

3. **Event representation refinement**
- objective: move from entity-only toward event-aware selection
- outcome: interpreter emits event/anomaly tags; selector uses event evidence
- retained verdict: narrow `GO`
- current relevance: active and foundational

4. **Visual direction refinement**
- objective: setup specificity, event-state prioritization, family de-duplication, style coherence
- outcome: soft improvements; not enough for promotion
- retained verdict: `HOLD`
- current relevance: active but incomplete

5. **Cinematic asset direction**
- objective: video-level visual world and emotion-aware selection
- outcome: operational visual-world layer exists
- retained verdict: `HOLD`
- current relevance: active, still partial

6. **Setup phase-1 dependency break**
- objective: hard reject generic middle patterns
- outcome: reduced broad filler, but still insufficient globally
- retained verdict: `HOLD`
- current relevance: legacy rejection remains active in selector

7. **Documentary transition break**
- objective: break `document -> archive room -> document` middle formula
- outcome: documentary middle improved materially
- retained verdict: narrow `GO`
- current relevance: currently active and important

8. **Integrated pipeline gate**
- objective: determine promotion readiness
- outcome: subsystem still not ready for baseline promotion
- retained verdict: `HOLD`
- current relevance: authoritative subsystem status remains `HOLD`
## 20. Current Strengths
Genuinely strong today:
- deterministic local runtime architecture
- clean orchestration boundary between creative planning and runtime resolution
- rich selector scoring surface
- offline supply integration exists for Pexels/Unsplash/Pixabay
- real local SD generation exists
- event-aware selection is real, not cosmetic
- documentary transition handling is materially better than earlier phase-1-style behavior
- runtime traceability is high relative to many media pipelines
- setup hard rejection and quality floors exist
- tests cover core subsystem surfaces

Things that should not be touched lightly:
- runtime locality and no-runtime-HTTP rule
- `AssetPlan` as runtime authority
- deterministic seed flow
- selector hard setup rejections
- documentary transition case-linkage logic
- usage-count feedback into catalog

## 21. Current Weaknesses
Still weak today:
- formal decision contract persistence
- product-level cinematic maturity
- atmosphere coherence under visual-world logic
- world continuity across all video families
- setup remains the weakest segment role overall, despite local improvements
- some videos still rely on structural patterns inherited from phase 1
- selector remains a weighted chooser, not a true scene constructor

Perceptual leaks that still matter:
- middle segments can still feel like context rather than escalation
- some world-consistent setups are still event-light
- family repetition can persist even when file repetition does not
- emotional alignment is present but not yet dominant enough to produce reference-level output

## 22. Current Blocking Gap(s)
Most accurate names, based on retained code and audits:

1. **Formal asset decision contract gap**
- runtime outputs still do not persist explicit per-segment entity/anomaly/photographability/justification
- this blocks the canonical decision gate

2. **Visual world enforcement gap**
- the visual-world layer exists, but acts mostly as soft scoring pressure
- it does not yet guarantee one dominant world per video with reference-level strength

3. **Legacy visual solution lock-in**
- broad legacy dependence has been reduced, but the subsystem can still resolve middle segments through familiar phase-1-adjacent visual structures

4. **Cinematic scene construction gap**
- current system is still closer to selecting strong images than to directing consistent micro-scenes
- this is the main product-level reason it remains below the reference videos

The earlier `documentary transition specificity gap` has been narrowed materially by the latest documentary refinement, but should not be considered universally extinct.

## 23. Honest Subsystem Maturity Assessment
### Architecture maturity
- **high**
- orchestration, runtime authority, and boundaries are solid

### Supply maturity
- **medium-high**
- offline supply system exists and catalog contains real imported assets
- provider breadth exists in code, but active catalog is still concentrated in curated + Pexels + Unsplash

### Adoption maturity
- **medium**
- ranking no longer ignores new supply entirely
- but adoption is still subordinate to stronger legacy/world-fit logic in some families

### Event representation maturity
- **medium-high**
- event tags and event evidence are now central to selection
- but event-state does not dominate enough in every contextual segment

### Cinematic/world maturity
- **medium-low**
- world/emotion layer exists
- but retained cinematic audit still held on world consistency and atmosphere coherence

### Product-level visual maturity
- **medium**
- outputs are no longer broken
- outputs are better than phase 1
- outputs are still below the reference level and below Script/Voice maturity

### Overall subsystem status
- **HOLD**

Precise justification:
- architecture is mature enough
- supply and SD infrastructure are real
- event-aware selection is real
- some targeted refinements have succeeded narrowly
- but the subsystem still fails the combination of:
  - formal decision-contract completeness
  - fully convincing visual-world continuity
  - reference-level cinematic scene construction

## 24. Recommended Next Move (Based Only on Current Reality)
The single most correct next move is:

- **make the formal asset decision contract operational in runtime outputs before any further visual refinement**

Why this is the right next move:
- the retained decision gate and integrated gate are both blocked by missing explicit decision persistence
- without that, future refinements keep changing behavior without closing the authoritative gate
- current selector/interpreter complexity is already high; more perceptual tweaking without formal traceability will keep increasing opacity

Concrete scope of that move:
- persist per-segment structured fields into `AssetPlan` or runtime trace:
  - `entity`
  - `event`
  - `anomaly_type`
  - `visibility_requirement`
  - `photographability`
  - concise selection justification
- keep runtime deterministic and local
- rerun:
  - `asset_agent_decision_gate_v1_0`
  - `script_voice_asset_pipeline_final_gate`

What should not be the next move:
- not another broad ranking refinement
- not more supply work
- not more architecture changes
- not more cinematic tuning before the formal contract is explicit

Until that gap is closed, the subsystem remains hard to promote and hard to evolve safely.

