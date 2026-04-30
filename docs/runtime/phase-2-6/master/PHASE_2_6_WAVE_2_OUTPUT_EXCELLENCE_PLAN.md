# PHASE_2_6_WAVE_2_OUTPUT_EXCELLENCE_PLAN

## 1. Purpose

`PHASE_2_6_WAVE_2_OUTPUT_EXCELLENCE_PLAN` is the formal excellence plan for Phase 2.6 Wave 2.

Wave 2 focuses on the output-quality agents:

- Script Agent
- Voice Agent
- Asset Selection Agent
- Video QC Agent

Wave 1 hardened the upstream evidence and governance layer:

- Learning Agent v2.6
- Account Health Agent v2.6
- Trend Analysis Agent v2.6

The Absolute Master Gate before Wave 2 returned:

```json
{
  "absolute_master_gate_pre_wave_2": "GO_WITH_MONITORING",
  "critical_failures": 0,
  "blocking_failures": [],
  "silent_failures": false,
  "fake_confidence": false,
  "boundary_violations": false,
  "non_determinism": false,
  "trace_incomplete": false,
  "recommendation": "PROCEED_TO_PHASE_2_6_WAVE_2_PLAN"
}
```

This authorizes planning for Wave 2.

It does not authorize broad runtime redesign.

Wave 2 exists to make the final produced content stronger, more traceable, more robust under variation, and more honestly validated without weakening the frozen runtime governance model.

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

Wave 2 must preserve:

- frozen core pipeline
- Creative Orchestrator ownership
- Strategy ownership
- Account Health `SAFE / CAUTION / HOLD` authority
- Learning bounded pressure
- Trend advisory context boundary
- QC final product-quality authority
- Experiment ownership
- Asset ownership over visual selection only
- Voice ownership over delivery plan only
- Script ownership over narrative text only
- no Publisher work
- no hidden publish enforcement
- no external expansion
- no provider expansion unless explicitly justified by a later gated plan
- no fake confidence
- no hidden fallback
- no silent schema break

## 3. Scope

In scope:

- narrative quality hardening
- voice delivery quality hardening
- visual decision and asset trace hardening
- QC product-signal hardening
- output trace consolidation
- fallback honesty
- product-quality scenario batteries
- deterministic replay where required
- contract-preserving additive fields
- dedicated excellence gates per agent
- Wave 2 master gate before Wave 3

Out of scope:

- modifying the core pipeline
- changing Strategy behavior
- changing Account Health behavior
- changing Learning behavior
- changing Trend behavior
- changing Experiment ownership
- implementing Publisher
- changing publish manifest semantics
- adding uncontrolled external data or provider dependencies
- broad prompt/provider expansion
- making QC silently enforce publish policy outside existing governance
- turning output agents into a hidden strategic brain

## 4. Wave 2 Objective

Wave 2 must move the output layer from:

- technically functional
- integrated
- traceable enough for operation
- quality-monitored
- `GO_WITH_MONITORING`

into:

- product-quality stronger
- narrative-specific
- voice-aligned
- visually justified
- QC-auditable
- fallback-honest
- contract-stable
- deterministic where required
- ready for v3 with monitoring

The goal is not aesthetic perfection.

The goal is to remove hidden output fragility before v3.

## 5. Operating Policy

Wave 2 must follow the same discipline as Wave 1.

Policy:

```json
{
  "phase_2_6_wave_2_policy": {
    "current_focus": "OUTPUT_AGENTS_ONLY",
    "do_not_implement_all_at_once": true,
    "advance_only_after_validation": true,
    "no_core_pipeline_modification": true,
    "no_strategy_modification": true,
    "no_publisher_work": true,
    "no_hidden_enforcement": true
  }
}
```

The correct order is:

1. Script Agent v2.6 Excellence Plan
2. Script Agent v2.6 bounded workstreams and gate
3. Voice Agent v2.6 Excellence Plan
4. Voice Agent v2.6 bounded workstreams and gate
5. Asset Selection Agent v2.6 Excellence Plan
6. Asset Selection Agent v2.6 bounded workstreams and gate
7. Video QC Agent v2.6 Excellence Plan
8. Video QC Agent v2.6 bounded workstreams and gate
9. Phase 2.6 Wave 2 Master Gate

No agent should start implementation without its own formal plan.

No downstream workstream should begin until the current workstream has been validated.

## 6. Agent Boundaries

### 6.1 Script Agent Boundary

Script owns:

- hook text
- setup text
- payoff text
- narration structure
- narrative specificity
- text-level style and clarity
- script generation trace

Script must not own:

- Strategy decisions
- Account Health posture
- Trend source authority
- Learning policy
- Voice provider selection
- Asset selection
- QC publishability
- Experiment assignment
- core pipeline execution

### 6.2 Voice Agent Boundary

Voice owns:

- `VoicePlan`
- voice provider request
- voice identity
- delivery profile
- segment-level delivery semantics
- provider and fallback trace
- voice-plan interpretation

Voice must not own:

- script text
- strategy
- asset selection
- QC decision
- publishability
- direct runtime publish policy
- provider expansion without gated justification

### 6.3 Asset Selection Boundary

Asset owns:

- visual interpretation
- `AssetPlan`
- segment-level visual decisions
- asset category/tag/source requests
- local catalog selection
- visual trace
- fallback visual selection

Asset must not own:

- script text
- voice delivery
- strategy
- QC decision
- publisher behavior
- uncontrolled external collection
- runtime HTTP fetching
- ungoverned image generation

### 6.4 Video QC Boundary

QC owns:

- final rendered artifact evaluation
- technical validity checks
- product-quality signals
- QC reason codes
- QC trace
- `APPROVE / HOLD / REJECT` if introduced through additive bounded contract
- publishability assessment as a product-quality decision, not as hidden runtime publish enforcement

QC must not own:

- script rewriting
- voice resynthesis
- asset replacement
- Strategy
- Account Health
- Learning
- Trend
- Experiment
- Publisher implementation
- core pipeline mutation
- hidden publish cancellation outside governance

Important boundary rule:

If true publish-manifest enforcement requires changing pipeline order or publish semantics, that requires explicit governance reopen. Wave 2 may expose stronger QC decisions and traces, but must not smuggle publisher behavior through QC.

## 7. Agent Sequence And Rationale

### 7.1 Script First

Script is first because it defines the content spine:

- weak hook limits retention
- weak setup weakens pacing
- weak payoff weakens memorability
- voice and asset quality depend on script intent
- QC product signals need clear script structure to evaluate

Script must become sharper before Voice and Asset can align properly.

### 7.2 Voice Second

Voice is second because it materializes script intent:

- monotone delivery weakens good scripts
- poor pacing weakens retention
- weak contrast between hook/setup/payoff reduces product impact
- voice trace must be strong before QC can audit audio delivery

Voice should harden after Script structure is clearer.

### 7.3 Asset Third

Asset is third because visual selection depends on Script and Trend:

- hook visuals must materialize the anomaly
- setup visuals must create escalation, not filler
- payoff visuals must support the reveal
- current asset gap is largely trace and decision-contract maturity

Asset must be hardened before QC can judge final audiovisual cohesion meaningfully.

### 7.4 QC Fourth

QC is fourth because it validates the combined output:

- Script, Voice, and Asset must expose stronger traces first
- QC should not invent signals that upstream agents cannot explain
- QC needs product-layer evidence, not only technical proxies
- QC must remain authority without becoming a repair engine

QC is the final Wave 2 agent before the Wave 2 Master Gate.

## 8. Script Agent v2.6 Plan

### 8.1 Current State

Script is already operational:

- real provider path active
- structured `hook / setup / payoff` output
- fallback chain explicit
- context from Strategy, Trend, Learning, and Experiment reaches script generation
- prior excellence gate proved material improvement

Known risk:

- output may remain conservative under some contexts
- hooks can be technically valid but not sufficiently sharp
- setup can be functional rather than escalating
- payoff can be coherent but not memorable enough
- script-quality trace is not yet audit-grade enough for v3

### 8.2 Objective

Make Script more specific, varied, memorable, and auditable without weakening structure or provider fallback safety.

Script confidence must describe trust in script construction, not expected video performance.

### 8.3 Workstreams

1. `script_context_governance`
   - validate what context Script consumes
   - distinguish Strategy, Trend, Learning, Experiment, and Account Health constraints
   - prevent unsupported context from becoming narrative claims
   - expose context use trace

2. `script_quality_rubric`
   - define deterministic rubric for hook, setup, payoff, specificity, clarity, novelty, and coherence
   - do not use fake scoring
   - expose rubric rationale
   - use as audit layer first, not as hidden rewrite logic

3. `hook_strength_hardening`
   - improve anomaly-first hooks
   - reduce generic openers
   - preserve niche and topic coherence
   - expose hook reason codes

4. `setup_progression_hardening`
   - make setup escalate the initial anomaly
   - reduce filler/context-only setup
   - preserve concise runtime format
   - expose setup function in trace

5. `payoff_memorability_hardening`
   - strengthen final reveal specificity
   - reduce generic explanation endings
   - connect payoff to hook anomaly
   - expose payoff rationale

6. `script_diversity_and_anti_cliche`
   - detect repeated structures
   - identify clichÃ© patterns
   - avoid overfitting to a single hook family
   - preserve deterministic behavior

7. `script_fallback_and_provider_honesty`
   - ensure fallback mode is always visible
   - avoid high quality/confidence claims under emergency fallback
   - preserve provider trace
   - do not add provider expansion

8. `script_trace_and_auditability`
   - consolidate context use, rubric, hook/setup/payoff rationale, provider path, fallback, and warnings
   - create reconstructible `script_trace`

9. `script_agent_v2_6_excellence_gate`
   - run controlled script scenarios
   - run provider/fallback scenarios
   - run anti-clichÃ© battery
   - run orchestrator integration
   - write final verdict artifact

### 8.4 Required Output By End Of Script v2.6

Script result or trace should expose additive fields such as:

- `script_trace`
- `context_usage_summary`
- `script_quality_rubric`
- `hook_rationale`
- `setup_rationale`
- `payoff_rationale`
- `fallback_honesty`
- `provider_trace`

Do not remove existing script fields.

### 8.5 Script Exit Criteria

Script is v2.6-complete only when:

- hook/setup/payoff rationale is explicit
- context use is traceable
- fallback is visible
- emergency fallback does not claim excellence
- script quality rubric is deterministic
- anti-clichÃ© behavior is measurable
- controlled output battery passes
- orchestrator integration remains stable
- Strategy unchanged
- core pipeline unchanged
- dedicated Script v2.6 gate passes

## 9. Voice Agent v2.6 Plan

### 9.1 Current State

Voice is operational:

- `VoicePlan` exists
- voice interpreter exists
- TTS router exists
- Kokoro is current local baseline
- Piper remains hard fallback
- provider trace exists
- fallback is explicit

Known risk:

- delivery can still be monotone
- segment-level contrast can be weak
- timing alignment may not fully follow hook/setup/payoff intensity
- provider execution trace can be strengthened
- quality validation remains proxy-based

### 9.2 Objective

Make Voice more expressive, segment-aware, auditable, and aligned with Script and Strategy without adding uncontrolled provider expansion.

Voice confidence must measure trust in voice-plan execution and delivery fit, not expected video performance.

### 9.3 Workstreams

1. `voice_plan_contract_hardening`
   - verify `VoicePlan` fields are complete and backward-compatible
   - expose requested vs executed voice parameters
   - ensure provider trace is complete

2. `delivery_profile_semantics`
   - define segment-level delivery intent
   - distinguish hook urgency, setup tension, payoff reveal
   - preserve deterministic mapping
   - avoid freeform delivery drift

3. `segment_timing_and_pause_hardening`
   - audit pause placement
   - align timing with script segments
   - expose timing rationale
   - avoid hidden audio mutation

4. `monotony_and_contrast_analysis`
   - add deterministic proxies for monotony and contrast
   - identify weak contrast under long narration
   - keep proxy honest and bounded

5. `provider_and_fallback_honesty`
   - distinguish requested provider, executed provider, and fallback provider
   - preserve Kokoro baseline and Piper fallback
   - do not add provider expansion in this workstream

6. `voice_audio_validation`
   - verify output audio existence, duration, format, and basic integrity
   - keep technical validation separate from perceptual claims
   - expose validation summary

7. `voice_trace_and_auditability`
   - consolidate provider, delivery profile, segment timing, monotony/contrast, fallback, and validation
   - create reconstructible `voice_trace`

8. `voice_agent_v2_6_excellence_gate`
   - run textual battery
   - run provider/fallback battery
   - run audio validation battery
   - run orchestrator/pipeline integration
   - write final verdict artifact

### 9.4 Required Output By End Of Voice v2.6

Voice result or trace should expose additive fields such as:

- `voice_trace`
- `requested_provider`
- `executed_provider`
- `fallback_path`
- `delivery_profile_summary`
- `segment_timing_summary`
- `monotony_proxy_summary`
- `audio_validation_summary`

Do not remove existing `VoicePlan` fields.

### 9.5 Voice Exit Criteria

Voice is v2.6-complete only when:

- requested vs executed provider is explicit
- fallback path is explicit
- segment-level delivery semantics are traceable
- monotony/contrast proxies are deterministic
- audio validation is explicit
- no provider expansion occurred
- script and strategy alignment is visible
- orchestrator/pipeline integration remains stable
- dedicated Voice v2.6 gate passes

## 10. Asset Selection Agent v2.6 Plan

### 10.1 Current State

Asset Selection is operational and sophisticated:

- segment-level asset planning exists
- local catalog selection exists
- visual trace exists
- deterministic selection exists under stable catalog state
- event-aware scoring exists
- visual-world and atmosphere scoring exist
- offline ingestion infrastructure exists

Known risk:

- formal decision contract is incomplete in persisted runtime outputs
- segment-level entity/anomaly/photographability/justification are not fully materialized
- setup can remain visually weak or phase-1-like
- visual-world enforcement is still mostly soft
- runner-up/candidate explanation is not audit-grade
- fallback visual quality is not sufficiently explained

### 10.2 Objective

Make Asset Selection explainable, visually specific, traceable, and robust under topic variety without adding runtime external fetching or ungoverned generation.

Asset confidence must describe trust in visual selection fit, not expected performance.

### 10.3 Workstreams

1. `asset_decision_contract_hardening`
   - materialize segment-level decision fields
   - include entity, event, anomaly, visibility, photographability, and justification
   - preserve `AssetPlan` backward compatibility
   - expose decision contract in trace

2. `asset_provenance_and_source_trace`
   - distinguish local catalog, curated source, imported source, generated source, and fallback
   - expose asset source class
   - do not add runtime external fetching
   - do not claim source quality without evidence

3. `asset_candidate_scoring_explainability`
   - expose winning candidate rationale
   - expose relevant score components
   - optionally expose bounded runner-up summary
   - avoid opaque ranking claims

4. `setup_specificity_hardening`
   - reduce filler setup visuals
   - strengthen event/context escalation
   - preserve deterministic selector behavior
   - do not broaden ontology without evidence

5. `visual_world_consistency_hardening`
   - make video-level visual-world rationale explicit
   - detect world breaks
   - expose style/coherence trace
   - avoid hidden hard enforcement unless explicitly tested

6. `family_diversity_and_repetition_control`
   - identify family-level repetition, not only file-level repetition
   - preserve legitimate continuity
   - avoid over-penalizing coherent visual worlds

7. `asset_fallback_quality_honesty`
   - make fallback visual selection explicit
   - distinguish safe fallback from high-quality match
   - prevent fallback from inflating visual confidence

8. `asset_trace_and_auditability`
   - consolidate segment decisions, source/provenance, scoring, world consistency, diversity, fallback, and unresolved gaps
   - create reconstructible `asset_trace`

9. `asset_selection_agent_v2_6_excellence_gate`
   - run controlled segment batteries
   - run setup/payoff specificity scenarios
   - run family repetition scenarios
   - run fallback scenarios
   - run orchestrator/pipeline integration
   - write final verdict artifact

### 10.4 Required Output By End Of Asset v2.6

Asset result or trace should expose additive fields such as:

- `asset_trace`
- `segment_decision_contract`
- `source_provenance_summary`
- `candidate_scoring_summary`
- `visual_world_summary`
- `family_diversity_summary`
- `fallback_visual_summary`
- `unresolved_visual_warnings`

Do not remove existing `AssetPlan`, `visual_trace`, or runtime path fields.

### 10.5 Asset Exit Criteria

Asset is v2.6-complete only when:

- every segment has explicit decision rationale
- source/provenance is visible
- fallback is not treated as strong visual evidence
- setup specificity improves in controlled scenarios
- visual-world consistency is traceable
- family repetition is detectable
- candidate selection is explainable
- no runtime external fetching is added
- orchestrator/pipeline integration remains stable
- dedicated Asset v2.6 gate passes

## 11. Video QC Agent v2.6 Plan

### 11.1 Current State

QC is operational as a technical validator:

- evaluates rendered artifacts
- returns `APPROVE / REJECT`
- catches missing files, invalid metadata, subtitles, darkness proxy, resolution, and audio stream issues
- is integrated after pipeline completion
- emits QC events

Known risk:

- QC is not yet a full product-quality judge
- `HOLD` is not currently present in the core QC model
- product signal trace is shallow
- publish manifest is created before QC, so QC is not currently a hard publish gate in pipeline order
- `VideoQcInput` and `VideoQcDecision` are partially unused contract surfaces
- confidence and severity are not explicit

### 11.2 Objective

Make QC more product-aware, traceable, and explicit without secretly modifying publish behavior or core pipeline order.

QC should become a stronger final product-quality authority while preserving governance.

### 11.3 Governance Constraint For QC

QC may improve:

- decision trace
- reason codes
- severity
- product-signal scoring
- confidence
- technical validation clarity
- layer-specific audit
- optional additive `HOLD` state only if bounded and backward-compatible

QC must not:

- silently cancel publish manifests
- rewrite pipeline status
- implement Publisher
- rerender content
- repair Script/Voice/Asset/Editor outputs
- change core pipeline order
- create hidden enforcement

If true publish-order enforcement is required, it must be handled by a separate governance reopen or later publisher/pipeline gate, not hidden inside QC Wave 2.

### 11.4 Workstreams

1. `qc_contract_and_status_governance`
   - audit current `VideoQcInput`, `VideoQcDecision`, and `VideoQcResult`
   - define whether `HOLD` can be added additively
   - preserve backward compatibility
   - document status semantics

2. `qc_technical_validation_hardening`
   - strengthen existing technical checks
   - expose severity per reason code
   - distinguish artifact invalidity from product weakness
   - preserve deterministic behavior

3. `qc_product_signal_layer`
   - add bounded product signals for hook readability, caption quality, payoff visibility, audiovisual cohesion, and runtime completeness
   - avoid ML or opaque scoring
   - do not claim human-level taste

4. `qc_confidence_and_severity`
   - calibrate confidence as trust in QC decision
   - confidence must drop when evidence is partial or environment-dependent
   - expose severity and rationale

5. `qc_layer_attribution`
   - link QC findings to Script, Voice, Asset, Editor, or Render layer when evidence supports it
   - do not mutate upstream outputs
   - do not assign blame without evidence

6. `qc_hold_semantics_if_allowed`
   - define `HOLD` for borderline or ambiguous output issues if backward-compatible
   - avoid overblocking
   - preserve `REJECT` for hard technical failures
   - preserve `APPROVE` for clean outputs

7. `qc_trace_and_auditability`
   - consolidate artifacts, reason codes, severity, confidence, layer attribution, product signals, and fallback/environment notes
   - create reconstructible `qc_trace`

8. `qc_agent_v2_6_excellence_gate`
   - run approve/hold/reject controlled scenarios if HOLD is introduced
   - run technical failure scenarios
   - run product-signal edge cases
   - run orchestrator/pipeline integration
   - verify no hidden publisher behavior
   - write final verdict artifact

### 11.5 Required Output By End Of QC v2.6

QC result or trace should expose additive fields such as:

- `qc_trace`
- `qc_version`
- `severity_summary`
- `confidence`
- `confidence_level`
- `product_signal_summary`
- `layer_attribution`
- `environment_probe_summary`
- `publish_boundary_statement`

Existing `VideoQcResult.status`, `reasons`, `checked_at`, and `details` must remain backward-compatible.

### 11.6 QC Exit Criteria

QC is v2.6-complete only when:

- technical checks remain deterministic
- product signals are explicit and bounded
- confidence is honest
- severity is visible
- layer attribution is evidence-backed
- fallback/environment degradation is visible
- `APPROVE / HOLD / REJECT` semantics are explicit if HOLD is introduced
- no hidden publish enforcement is added
- orchestrator/pipeline integration remains stable
- dedicated QC v2.6 gate passes

## 12. Wave 2 Cross-Agent Requirements

Wave 2 must prove not only per-agent improvement, but output-layer consistency.

Required cross-agent checks:

- Script intent reaches Voice
- Script intent reaches Asset
- Strategy constraints still influence Script/Voice/Asset through existing channels
- Trend remains context-only
- Learning pressure remains bounded
- Account Health `HOLD` still blocks before output generation
- QC evaluates rendered output, not planned output only
- QC does not mutate Script/Voice/Asset
- Asset fallback does not hide visual weakness
- Voice fallback does not hide delivery weakness
- Script fallback does not claim excellence
- final execution traces are not contradictory

## 13. Common Trace Requirements

By the end of Wave 2, every output agent should expose reconstructible trace data:

- `script_trace`
- `voice_trace`
- `asset_trace`
- `qc_trace`

Each trace must include:

- inputs consumed
- evidence used
- fallback state
- confidence or trust signal where applicable
- decision rationale
- degraded/missing input notes
- boundary statement
- deterministic reason codes
- audit summary

Trace must not fabricate evidence.

Trace must not claim reconstructibility when required sections are missing.

## 14. Common Confidence Rules

Any confidence added in Wave 2 must follow these rules:

- confidence measures trust in the agent output or decision, not expected video performance
- confidence must not be constant
- confidence must decrease under fallback, missing evidence, degraded inputs, or weak trace
- confidence must include rationale
- confidence must not create hidden enforcement
- confidence must not override Strategy, Account Health, Learning, Trend, Experiment, or QC boundaries

No fake confidence is allowed.

## 15. Common Fallback Rules

Fallback must remain:

- explicit
- traceable
- non-inflated
- lower-authority than clean evidence
- visible in agent result or trace

Forbidden fallback behaviors:

- hidden fallback
- fallback represented as clean execution
- fallback with high confidence without rationale
- fallback silently changing downstream semantics
- fallback used to hide provider, asset, script, voice, or QC weakness

## 16. Common Determinism Rules

Determinism is required where the same controlled input and same local state are expected to produce stable output.

Determinism must be validated for:

- script audit scoring
- voice delivery mapping
- asset selection under fixed catalog and seed
- QC decision under fixed artifacts
- trace reconstruction
- fallback decisions

Allowed non-determinism:

- external provider raw generations, if provider path is explicitly marked and output is not treated as deterministic
- timestamps, if explicitly ignored in replay comparison
- catalog state changes that are explicitly caused by usage-count updates

Any non-determinism must be documented.

## 17. Workstream Advancement Rules

Each workstream may proceed only if:

- the previous workstream has focused tests
- no runtime/core mutation occurred
- no boundary violation occurred
- no existing public contract was broken
- fallback remains honest
- trace is additive
- validation output is documented

Hard stop:

```json
{
  "critical_failures": 0,
  "blocking_failures": [],
  "silent_failures_detected": false,
  "fake_confidence_detected": false,
  "boundary_violations_detected": false,
  "core_pipeline_modified": false
}
```

If violated, Wave 2 must pause.

## 18. Wave 2 Master Gate

After all four agents complete their own gates, create:

- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_2_MASTER_GATE.md`
- `tests/run_phase_2_6_wave_2_output_master_gate.py`
- `OUT/audit/phase_2_6_wave_2_output_master_gate/final_verdict.json`

The Wave 2 Master Gate must validate:

- Script v2.6 gate integrity
- Voice v2.6 gate integrity
- Asset v2.6 gate integrity
- QC v2.6 gate integrity
- cross-agent output consistency
- orchestrator compatibility
- content pipeline compatibility
- fallback honesty
- trace completeness
- confidence honesty
- product-quality scenario battery
- deterministic replay
- boundary preservation
- no hidden publish enforcement
- no core pipeline mutation

Minimum verdict schema:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "audit_type": "PHASE_2_6_WAVE_2_OUTPUT_MASTER_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "script_agent_v2_6": {
    "ready_for_v3_with_monitoring": true,
    "blocking_failures": []
  },
  "voice_agent_v2_6": {
    "ready_for_v3_with_monitoring": true,
    "blocking_failures": []
  },
  "asset_selection_agent_v2_6": {
    "ready_for_v3_with_monitoring": true,
    "blocking_failures": []
  },
  "video_qc_agent_v2_6": {
    "ready_for_v3_with_monitoring": true,
    "blocking_failures": []
  },
  "output_quality_improved": true,
  "fallback_honest": true,
  "traceability_complete": true,
  "boundary_preserved": true,
  "core_pipeline_unchanged": true,
  "hidden_publish_enforcement_detected": false,
  "silent_failures_detected": false,
  "blocking_failures": [],
  "residual_monitoring": []
}
```

## 19. Wave 2 Failure Conditions

Wave 2 must return `HOLD` if any of the following occurs:

- Script outputs generic/clichÃ© text while claiming high confidence
- Voice fallback is hidden
- Voice provider trace is incomplete
- Asset source/provenance is hidden
- Asset fallback is treated as strong visual match
- Asset segment decision lacks rationale
- QC trace is incomplete
- QC adds hidden publish enforcement
- QC claims product judgment without evidence
- any output agent becomes Strategy
- any output agent becomes QC except QC itself
- any output agent modifies core pipeline
- any agent hides fallback
- any confidence is fake or constant
- deterministic replay fails without explanation
- orchestrator behavior regresses
- Account Health `HOLD` no longer blocks upstream
- existing public contracts break

## 20. Expected Residual Monitoring

Likely acceptable residuals:

- long-horizon production quality still under monitoring
- provider variability still under monitoring
- asset catalog coverage still expanding
- voice delivery realism still under monitoring
- QC product-signal calibration still maturing
- controlled validation still dominates some surfaces

Not acceptable as residuals:

- hidden fallback
- missing trace
- fake confidence
- contract break
- core mutation
- hidden publisher behavior
- Strategy boundary violation
- QC authority bypass
- Asset source fabrication
- provider substitution without trace

## 21. Final Position

Wave 2 exists to make the system's outputs stronger, more explainable, and more reliably validated.

It must raise product quality without creating hidden authority.

Script must improve narrative strength.

Voice must improve delivery alignment.

Asset must improve visual decision trace and specificity.

QC must improve product-quality validation without secretly becoming Publisher.

The correct first artifact after this plan is:

`docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_PLAN.md`

No implementation should begin until that Script-specific plan is created and approved.
