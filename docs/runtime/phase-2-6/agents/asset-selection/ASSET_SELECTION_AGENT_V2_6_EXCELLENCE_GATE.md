# ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_GATE

## 1. Purpose

`ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_GATE` is the formal validation gate for the Asset Selection Agent after the Phase 2.6 excellence-hardening workstreams.

This gate validates Asset Selection Agent v2.6 as implemented. It must not mutate runtime behavior to make validation pass.

The gate determines whether Asset Selection is:

- runtime-real
- context-governed
- catalog/source-governed
- segment visual-intent aware
- metadata-alignment aware
- visual-truthfulness and mismatch-risk aware
- fallback and safe-default honest
- diversity and repetition guarded
- confidence-calibrated
- traceable end-to-end
- deterministic under controlled inputs
- boundary-preserving
- free of silent failures

This gate is not a feature and is not a runtime behavior change. It is an audit artifact that can produce `GO`, `GO_WITH_MONITORING`, or `HOLD`.

## 2. Scope

In scope:

- Asset Selection runtime service execution
- context governance
- local catalog and source governance
- hook/setup/payoff visual intent mapping
- metadata-only visual semantic alignment
- visual truthfulness and mismatch risk
- fallback and safe-default honesty
- diversity and repetition guard
- confidence calibration as trust in asset selection
- consolidated `asset_trace`
- deterministic replay
- backward-compatible `AssetSelectionResult`
- Strategy, Script, Voice, Trend, QC, orchestrator, and core boundary preservation

Out of scope:

- modifying Asset Selection runtime logic to pass the gate
- changing selected assets, ranking, or fallback behavior
- changing catalog contents
- adding external providers or image scraping
- using ML/image inspection
- modifying Strategy, Script, Voice, Trend, QC, orchestrator, or core pipeline
- adding publishability logic
- predicting performance
- converting Asset Selection into Strategy, QC, Publisher, or a visual intelligence authority

## 3. Preconditions

The gate may run only after these Asset Selection v2.6 workstreams exist:

- Asset Context Governance
- Catalog And Source Governance
- Segment Visual Intent Mapping
- Visual Semantic Alignment
- Visual Truthfulness And Mismatch Risk
- Fallback And Safe Default Honesty
- Diversity And Repetition Guard
- Confidence Calibration
- Trace And Auditability Hardening

Required code surfaces:

- `backend/app/creative/agents/asset_selection/models.py`
- `backend/app/creative/agents/asset_selection/service.py`
- `backend/app/creative/agents/asset_selection/context_governance.py`
- `backend/app/creative/agents/asset_selection/catalog_source_governance.py`
- `backend/app/creative/agents/asset_selection/segment_visual_intent.py`
- `backend/app/creative/agents/asset_selection/visual_semantic_alignment.py`
- `backend/app/creative/agents/asset_selection/visual_truthfulness.py`
- `backend/app/creative/agents/asset_selection/fallback_honesty.py`
- `backend/app/creative/agents/asset_selection/diversity_guard.py`
- `backend/app/creative/agents/asset_selection/confidence_calibration.py`
- `backend/app/creative/agents/asset_selection/trace_auditability.py`

Required validation command:

`python tests/gates/agents/asset_selection/run_asset_selection_agent_v2_6_excellence_gate.py`

Required output artifact:

`OUT/audit/asset_selection_agent_v2_6_excellence_gate/final_verdict.json`

## 4. Evaluation Dimensions

`runtime_real`

Means Asset Selection executes through `AssetSelectionAgentService`, not a stubbed result object.

Failure if the service cannot execute, valid local catalog inputs unexpectedly fall into fallback, or only synthetic result objects are inspected.

`context_governed`

Means upstream context is classified as available, used, ignored, missing, or degraded.

Failure if missing/degraded context is hidden or upstream context silently becomes Strategy authority.

`catalog_source_governed`

Means selected assets are checked against `local_catalog_only_v2_6`, eligible local catalog sources are explicit, and ineligible sources remain visible.

Failure if unsupported, legacy, or unregistered sources are accepted as strong governed evidence.

`segment_visual_intent_explicit`

Means hook/setup/payoff visual intent, narrative role, requested category, tags, completeness, and rationale are visible.

Failure if segment intent is missing, fake, or used to change ranking in the gate.

`visual_alignment_explicit`

Means category match, tag/query overlap, metadata availability, mismatch status, and metadata-only boundaries are visible.

Failure if mismatches are hidden, image inspection is claimed without evidence, or alignment mutates selection.

`visual_truthfulness_explicit`

Means generic assets, unsupported visual claims, fallback visual weakness, and mismatch risk are visible.

Failure if visually weak or unsupported assets are represented as strong truthfulness.

`fallback_safe_default_honest`

Means global and segment fallback are explicit and `safe_default` is treated as weak visual evidence.

Failure if fallback is hidden or safe default can produce high-confidence strong semantic evidence.

`diversity_repetition_guarded`

Means repeated asset paths, repeated categories, and weak hook/setup/payoff visual progression are visible.

Failure if repetition or weak progression is hidden, or if randomness is added to solve repetition.

`confidence_calibrated`

Means confidence measures trust in asset selection, varies by evidence state, and is not performance prediction.

Failure if confidence is constant, high under fallback/safe default, high under high mismatch, lacks rationale, or predicts performance.

`traceability_complete`

Means `asset_trace` reconstructs why the `AssetPlan` was emitted and what evidence was unavailable.

Failure if required trace sections are missing, reconstructibility is faked, mismatch is not exposed, fallback is hidden, or confidence lacks rationale.

`selection_ranking_fallback_preserved`

Means the gate validates audit layers without changing selected assets, ranking policy, or fallback behavior.

Failure if the gate or workstream changes asset choice, ranking semantics, or fallback selection to pass.

`boundary_preserved`

Means Asset Selection remains a visual selection and audit agent and does not become Strategy, Script, Voice, Trend, QC, Publisher, or core.

Failure if Asset Selection emits publishability decisions, Strategy commands, QC decisions, provider execution, external collection, or hidden enforcement.

`determinism_where_required`

Means controlled identical input produces stable asset selection, analyses, confidence, and trace.

Failure if stable output drifts without input changes.

`silent_failures_detected`

Means missing trace sections, fake confidence, hidden fallback, hidden mismatch, hidden safe default, boundary violations, and non-determinism are detected as blockers.

Failure if critical defects exist while the verdict passes.

## 5. Controlled Scenario Battery

The runner executes controlled scenarios through `AssetSelectionAgentService` and component probes using the same v2.6 evaluators where direct mismatch/repetition evidence is required.

Required scenarios:

- `strong_catalog_match`
- `missing_script_context`
- `empty_segment_context`
- `safe_default_fallback`
- `metadata_mismatch_probe`
- `repetition_probe`
- `confidence_cap_probe`
- `determinism_replay`
- `backward_compatibility`

Controlled component probes are allowed only to validate audit logic that cannot be reliably forced through the service without changing selector behavior. The service itself must not be stubbed.

## 6. Checklist

The runner validates:

- runtime execution
- context governance
- catalog/source governance
- segment visual intent
- metadata-only visual alignment
- visual truthfulness and mismatch risk
- fallback and safe-default honesty
- diversity and repetition guard
- confidence calibration
- trace completeness
- selection/ranking/fallback preservation
- boundary preservation
- deterministic replay
- backward compatibility
- critical Asset, Strategy, Script, Voice, Trend, orchestrator, and selector tests
- silent failure detection

Any failed critical checklist item becomes a blocking failure.

## 7. Verdict Semantics

`GO`

Allowed only when all critical dimensions pass and no meaningful residual monitoring remains.

`GO_WITH_MONITORING`

Allowed when all critical checks pass and remaining residuals are explicit, bounded, non-structural, and related to catalog coverage, visual history, or lack of pixel-level validation at the selection layer.

`HOLD`

Required if any critical failure, blocking failure, fake confidence, silent failure, boundary violation, non-determinism, incomplete trace, hidden fallback, hidden mismatch, safe-default inflation, selection mutation, ranking mutation, or core/downstream mutation is detected.

Expected likely verdict is `GO_WITH_MONITORING`. The runner must derive it from evidence and must not hardcode it.

## 8. Failure Conditions

Critical failures include:

- Asset Selection service cannot execute
- local catalog path unexpectedly falls back under valid input
- selected sources are not governed
- ineligible or unsupported sources are accepted as strong evidence
- visual intent is missing for emitted segments
- visual mismatch is hidden
- visual truthfulness risk is hidden
- fallback or safe default is hidden
- safe default produces high confidence
- confidence is constant or fake
- confidence predicts performance
- repeated assets/categories are hidden
- `asset_trace` is incomplete
- `asset_trace.audit_summary.reconstructible` is false for normal service output
- selected assets, ranking, or fallback behavior are mutated by the gate
- boundary violation
- non-deterministic replay
- failed critical test battery

## 9. Output Artifacts

The runner must write:

- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/metrics.json`

## 10. Final Criteria

The Asset Selection Agent v2.6 gate may recommend proceeding only when:

- Asset Selection runs through real `AssetSelectionAgentService`
- all v2.6 additive fields exist and serialize
- context governance is explicit
- catalog/source governance is explicit
- segment visual intent is explicit
- visual alignment is metadata-only and exposes mismatch
- visual truthfulness exposes weak/generic/unsupported visual evidence
- fallback and safe default remain explicit and weak
- diversity/repetition risk is visible
- confidence means trust in asset selection
- `asset_trace` reconstructs the emitted `AssetPlan`
- deterministic replay holds
- selected assets, ranking, and fallback behavior remain unchanged
- Asset Selection remains within its boundary

Final recommendation values:

- `PROCEED_TO_VIDEO_QC_AGENT_V2_6_PLAN`
- `HOLD_BEFORE_VIDEO_QC`
