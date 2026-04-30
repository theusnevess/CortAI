# SCRIPT_AGENT_V2_6_EXCELLENCE_GATE

## 1. Purpose

`SCRIPT_AGENT_V2_6_EXCELLENCE_GATE` is the formal validation gate for the Script Agent after the Phase 2.6 excellence-hardening workstreams.

This gate validates Script Agent v2.6 as implemented. It must not mutate runtime behavior to make validation pass.

The gate determines whether Script is:

- runtime-real
- context-governed
- quality-rubric backed
- hook/setup/payoff aware
- anti-cliche and diversity aware
- provider/fallback honest
- confidence-calibrated
- traceable end-to-end
- deterministic under controlled inputs
- boundary-preserving
- free of silent failures

This gate is not a feature and is not a runtime behavior change. It is an audit artifact that can produce `GO`, `GO_WITH_MONITORING`, or `HOLD`.

## 2. Scope

In scope:

- Script Agent runtime service execution
- context governance
- deterministic script quality rubric
- hook strength analysis
- setup progression analysis
- payoff memorability analysis
- diversity and anti-cliche analysis
- provider and fallback honesty
- confidence calibration as trust in script construction
- consolidated `script_trace`
- deterministic replay
- backward-compatible `ScriptAgentResult`
- Strategy, Voice, Asset, QC, Experiment, orchestrator, and core boundary preservation

Out of scope:

- modifying Script runtime logic to pass the gate
- rewriting generated scripts in the gate
- adding providers or changing provider order
- modifying Strategy, Voice, Asset, QC, Experiment, orchestrator, or core pipeline
- adding publishability logic
- predicting performance
- converting Script into Strategy or QC
- converting failures into residual monitoring

## 3. Preconditions

The gate may run only after these Script v2.6 workstreams exist:

- Context Governance Hardening
- Script Quality Rubric
- Hook Strength Hardening
- Setup Progression Hardening
- Payoff Memorability Hardening
- Diversity And Anti-Cliche Hardening
- Provider And Fallback Honesty
- Confidence Calibration
- Trace And Auditability Hardening

Required code surfaces:

- `backend/app/creative/agents/script/models.py`
- `backend/app/creative/agents/script/service.py`
- `backend/app/creative/agents/script/context_governance.py`
- `backend/app/creative/agents/script/quality_rubric.py`
- `backend/app/creative/agents/script/hook_analysis.py`
- `backend/app/creative/agents/script/setup_analysis.py`
- `backend/app/creative/agents/script/payoff_analysis.py`
- `backend/app/creative/agents/script/diversity_analysis.py`
- `backend/app/creative/agents/script/provider_fallback_trace.py`
- `backend/app/creative/agents/script/confidence_calibration.py`
- `backend/app/creative/agents/script/trace_auditability.py`

Required validation command:

`python tests/gates/agents/script/run_script_agent_v2_6_excellence_gate.py`

Required output artifact:

`OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`

## 4. Evaluation Dimensions

`runtime_real`

Means Script executes through `ScriptAgentService`, not a stubbed agent.

Failure if the service cannot execute, valid provider output falls into fallback unexpectedly, or only synthetic result objects are inspected.

`context_governed`

Means upstream context is classified as available, used, ignored, missing, or degraded.

Failure if missing/degraded context is hidden or upstream context is silently promoted into Strategy authority.

`quality_rubric_explicit`

Means deterministic construction components are present with score, level, reason, evidence, and rationale.

Failure if rubric components are missing, non-serializable, or imply QC/publishability authority.

`hook_analysis_explicit`

Means hook presence, strength, genericity, tension, specificity, and unsupported claims are visible.

Failure if generic or unsupported hooks are not detected.

`setup_analysis_explicit`

Means setup progression, hook/payoff connection, repetition, and unsupported context are visible.

Failure if setup repetition or unsupported context is hidden.

`payoff_analysis_explicit`

Means payoff presence, memorability, specificity, genericity, vague motivational language, and hook resolution are visible.

Failure if generic/vague payoff evidence is hidden.

`diversity_anti_cliche_explicit`

Means cliche risk, repetition risk, generic phrases, generic CTA, and current-script-only analysis are visible.

Failure if cliche/repetition risk is hidden or external memory is fabricated.

`provider_fallback_honest`

Means provider used, attempts, failures, repair status, fallback mode, fallback reason, and fallback type are visible.

Failure if fallback is hidden, provider order changes, or missing repair metadata is fabricated.

`confidence_calibrated`

Means confidence measures trust in script construction, varies by evidence state, and is not performance prediction.

Failure if confidence is constant, high under fallback/weak evidence, lacks rationale, or predicts performance.

`traceability_complete`

Means `script_trace` reconstructs why the `ScriptPlan` was emitted.

Failure if required trace sections are missing, reconstructibility is faked, or silent failure indicators are ignored.

`boundary_preserved`

Means Script remains a narrative construction agent and does not become Strategy, Voice, Asset, QC, Experiment, Publisher, or core.

Failure if Script emits hidden constraints, publishability decisions, downstream commands, or ownership drift.

`determinism_where_required`

Means controlled identical input produces stable script output, analysis, confidence, and trace.

Failure if stable output drifts without input changes.

`fallback_honest`

Means fallback remains explicit, bounded, and lower trust than successful provider construction.

Failure if fallback is represented as provider success or high-trust clean construction.

`silent_failures_detected`

Means missing sections, fake confidence, hidden fallback, boundary violations, and non-determinism are detected as blockers.

Failure if critical defects exist while the verdict passes.

## 5. Controlled Scenario Battery

The runner executes controlled scenarios through `ScriptAgentService`.

Controlled generator dependencies are allowed so the gate can create deterministic provider success/failure conditions. The Script Agent service itself must not be stubbed.

Required scenarios:

- `rich_context_strong_script`
- `missing_optional_context`
- `degraded_upstream_context`
- `generic_low_quality_script`
- `unsupported_claim_hook`
- `provider_fallback`
- `determinism_replay`
- `backward_compatibility`

## 6. Checklist

The runner validates:

- runtime execution
- context governance
- quality rubric
- hook analysis
- setup analysis
- payoff analysis
- diversity and anti-cliche analysis
- provider/fallback honesty
- confidence calibration
- trace completeness
- fallback honesty
- boundary preservation
- deterministic replay
- backward compatibility
- silent failure detection

Any failed checklist block becomes a blocking failure.

## 7. Verdict Semantics

`GO`

Allowed only when all critical dimensions pass and no meaningful residual monitoring remains.

`GO_WITH_MONITORING`

Allowed when all critical dimensions pass and remaining issues are explicit, bounded, non-structural, or related to provider/runtime history and long-horizon script quality evidence.

`HOLD`

Required when any critical failure exists, including trace incompleteness, fake confidence, hidden fallback, non-determinism, boundary violation, or silent failure.

The expected likely outcome is `GO_WITH_MONITORING`, but the runner must derive the verdict from evidence.

## 8. Failure Conditions

The gate must return `HOLD` if any of the following occur:

- Script cannot execute through `ScriptAgentService`
- context governance is missing
- quality rubric is incomplete
- hook/setup/payoff analysis is incomplete
- cliche or repetition risk is hidden
- provider fallback is hidden
- repair metadata is fabricated
- confidence is constant or fake
- confidence predicts performance
- fallback receives high confidence
- `script_trace` is incomplete
- deterministic replay fails
- Script crosses into Strategy, Voice, Asset, QC, Experiment, Publisher, or core ownership
- silent failure indicators are present without being classified as blockers

## 9. Output Artifacts

The runner writes:

- `OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/metrics.json`

## 10. Final Criteria

Script Agent v2.6 may pass only if the gate proves:

- runtime execution is real
- context governance is explicit
- quality rubric is deterministic and bounded
- hook/setup/payoff analyses are explicit
- diversity and anti-cliche analysis is honest
- provider and fallback paths are visible
- confidence means trust in script construction
- `script_trace` reconstructs the emitted `ScriptPlan`
- fallback remains explicit and lower trust
- deterministic replay holds
- Script remains within its boundary

Final rule:

> Script Agent is ready for v3 only when it can explain why a `ScriptPlan` was emitted without pretending weak context, fallback, or low-quality construction is stronger than it is.
