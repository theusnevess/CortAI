# Script Agent v2.6 Excellence Plan

## 1. Purpose

This document defines the formal Phase 2.6 excellence plan for the Script Agent.

The Script Agent is the first Wave 2 output agent. It consumes upstream context from Strategy, Trend, Learning, Account Health, and Experiment surfaces where available, then produces a bounded script plan for downstream Voice, Asset, Editor, and QC stages.

This is not an implementation artifact.

This plan defines how Script must evolve from a runtime-real structured generation surface into an audit-grade, context-governed, confidence-aware, fallback-honest, traceable narrative construction subsystem.

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

The Script v2.6 work must preserve:

- core pipeline frozen
- Strategy ownership
- Account Health ownership
- Learning ownership
- Trend ownership
- Voice ownership
- Asset ownership
- QC ownership
- Experiment ownership
- Publisher out of scope
- no hidden enforcement
- no provider expansion
- no fake confidence
- no fake quality claims
- no downstream behavior changes without explicit governance

## 3. Current State

The Script Agent is already runtime-real and integrated into the creative pipeline.

Current capabilities include:

- `ScriptAgentInput` with account, niche, topic, account health, Strategy, Trend, Learning, and Experiment context surfaces.
- `ScriptAgentResult` returning a structured `ScriptPlan` and fallback information.
- provider-backed generation through the local script generation service.
- deterministic fallback when provider generation is unavailable or invalid.
- structured narrative fields such as hook, setup, and payoff.
- screen text adaptation after script generation.
- existing payoff and concreteness heuristics in the local script generator path.

Current limitations for Phase 2.6:

- context usage is not yet audit-grade.
- upstream signal influence is not fully explained.
- quality criteria are not explicit as a deterministic rubric.
- hook, setup, payoff, and CTA quality are not traceable as separate quality dimensions.
- fallback and provider path are not sufficiently visible for audit.
- confidence is not yet calibrated as trust in script construction.
- script decisions are not reconstructible from a consolidated trace.

## 4. Objective

Script v2.6 must make script generation more:

- context-governed
- quality-rubric backed
- hook-aware
- setup-aware
- payoff-aware
- anti-cliche and diversity-aware
- provider/fallback honest
- confidence-aware
- traceable end-to-end
- ready for v3 with monitoring

The goal is to improve the reliability, explainability, and auditability of script construction.

The goal is not to make Script a strategic decision layer, QC judge, publisher, trend engine, or performance predictor.

## 5. Scope

In scope:

- Script context intake governance.
- field-level rationale for script construction.
- deterministic script quality rubric.
- hook strength hardening.
- setup progression hardening.
- payoff memorability hardening.
- diversity and anti-cliche hardening.
- provider and fallback honesty.
- confidence calibration for trust in script construction.
- consolidated `script_trace`.
- Script v2.6 excellence gate.

Out of scope:

- core pipeline changes.
- Strategy behavior changes.
- Account Health decision changes.
- Learning policy changes.
- Trend source or confidence changes.
- Voice selection or synthesis changes.
- Asset selection behavior changes.
- QC publishability decisions.
- Publisher work.
- provider expansion.
- uncontrolled prompt experimentation.
- performance prediction.

## 6. Boundary Rules

Script may:

- use Strategy as the controlling creative direction.
- use Trend as advisory context.
- use Learning as bounded historical signal.
- respect Account Health constraints.
- respect Experiment assignment when provided.
- produce a script plan for downstream execution.
- explain how upstream context influenced script fields.

Script must not:

- override Strategy.
- decide publishability.
- decide final content quality.
- decide voice, asset, or edit execution.
- create experiments.
- decide rollout or posting policy.
- infer account health.
- create hidden constraints.
- hide fallback.
- claim confidence without evidence.
- predict performance.

## 7. Required Workstream Order

Script v2.6 must be implemented in bounded workstreams:

1. Context Governance Hardening
2. Script Quality Rubric
3. Hook Strength Hardening
4. Setup Progression Hardening
5. Payoff Memorability Hardening
6. Diversity And Anti-Cliche Hardening
7. Provider And Fallback Honesty
8. Confidence Calibration
9. Trace And Auditability Hardening
10. Script Excellence Gate

Do not implement all workstreams at once.

Each workstream must pass focused validation before the next workstream begins.

## 8. Workstream 1: Context Governance Hardening

### Goal

Make Script context intake explicit, bounded, and auditable.

### Required Behavior

The Script Agent must identify which upstream context was available, used, ignored, missing, or degraded.

Expected context classes:

- strategy_context
- trend_context
- learning_context
- account_health_context
- experiment_context
- topic_context
- niche_context

### Required Output

Additive trace structure:

```json
{
  "context_governance": {
    "available_context": [],
    "used_context": [],
    "ignored_context": [],
    "missing_context": [],
    "degraded_context": [],
    "context_priority": [],
    "policy_respected": true,
    "rationale": []
  }
}
```

### Constraints

- Strategy remains the primary creative control context.
- Trend remains advisory.
- Learning remains bounded historical signal.
- Account Health constraints must remain visible and respected.
- Missing context must not be fabricated.
- Missing optional context must not automatically fail generation.

### Validation

Focused tests must prove that context usage is explicit and no upstream signal is silently promoted into Strategy authority.

## 9. Workstream 2: Script Quality Rubric

### Goal

Create a deterministic rubric that explains script construction quality without becoming QC or publishability logic.

### Required Dimensions

At minimum:

- hook_clarity
- hook_specificity
- setup_coherence
- setup_progression
- payoff_specificity
- payoff_memorability
- cta_fit
- trend_alignment
- strategy_alignment
- repetition_risk
- cliche_risk

### Required Output

Each rubric component should expose:

```json
{
  "score": 0.0,
  "level": "low | medium | high",
  "reason_code": "...",
  "evidence": {},
  "rationale": "..."
}
```

### Constraints

- The rubric must not decide publishability.
- The rubric must not replace QC.
- The rubric must not predict performance.
- The rubric must not produce fake precision.
- Scores must be deterministic and explainable.

### Validation

Tests must prove rubric scores vary across controlled scripts and include rationale for every component.

## 10. Workstream 3: Hook Strength Hardening

### Goal

Improve and audit hook quality as a bounded script construction concern.

### Required Checks

- clarity
- specificity
- immediate tension or payoff promise
- topic fit
- strategy fit
- avoidance of generic hooks
- avoidance of unsupported claims

### Required Trace

```json
{
  "hook_analysis": {
    "hook_present": true,
    "strength_level": "low | medium | high",
    "generic_hook_detected": false,
    "unsupported_claim_detected": false,
    "reason_codes": [],
    "rationale": []
  }
}
```

### Constraints

- Do not create clickbait optimization.
- Do not overrule Strategy.
- Do not make performance claims.
- Do not hide weak hooks.

## 11. Workstream 4: Setup Progression Hardening

### Goal

Ensure setup text progresses from hook to payoff coherently.

### Required Checks

- setup exists.
- setup connects to hook.
- setup prepares payoff.
- setup does not repeat hook without development.
- setup does not introduce unsupported context.
- setup remains compatible with voice and edit execution.

### Required Trace

```json
{
  "setup_analysis": {
    "setup_present": true,
    "progression_level": "low | medium | high",
    "repetition_detected": false,
    "unsupported_context_detected": false,
    "reason_codes": [],
    "rationale": []
  }
}
```

### Constraints

- Do not become Editor.
- Do not change downstream timing behavior.
- Do not create hidden rewrite authority.

## 12. Workstream 5: Payoff Memorability Hardening

### Goal

Make payoff quality explicit, concrete, and auditable.

### Required Checks

- payoff exists.
- payoff is specific.
- payoff resolves or reframes the hook.
- payoff is not generic.
- payoff is not a vague motivational line.
- payoff is compatible with Strategy and topic.

### Required Trace

```json
{
  "payoff_analysis": {
    "payoff_present": true,
    "memorability_level": "low | medium | high",
    "generic_payoff_detected": false,
    "weak_payoff_terms": [],
    "reason_codes": [],
    "rationale": []
  }
}
```

### Constraints

- Do not fabricate facts.
- Do not claim the payoff will perform.
- Do not turn payoff scoring into QC publishability.

## 13. Workstream 6: Diversity And Anti-Cliche Hardening

### Goal

Reduce repeated, generic, or cliche script patterns while preserving deterministic behavior.

### Required Checks

- repeated hook phrases.
- repeated payoff structures.
- overused CTA patterns.
- generic creator advice.
- trend overfitting.
- weak novelty within the allowed Script boundary.

### Required Trace

```json
{
  "diversity_analysis": {
    "cliche_risk_level": "low | medium | high",
    "repetition_risk_level": "low | medium | high",
    "detected_patterns": [],
    "reason_codes": [],
    "rationale": []
  }
}
```

### Constraints

- Do not become Novelty Agent.
- Do not become Learning.
- Do not invent historical memory outside available inputs.
- Do not add randomness to create diversity.

## 14. Workstream 7: Provider And Fallback Honesty

### Goal

Make provider path, provider failure, repair, and fallback behavior explicit.

### Required Checks

- selected provider.
- provider attempts.
- provider failure reasons.
- repair attempts if any.
- fallback usage.
- fallback mode.
- fallback reason.
- whether fallback script is contextual or safe default.

### Required Trace

```json
{
  "provider_fallback_trace": {
    "provider_path": [],
    "provider_used": "...",
    "provider_success": true,
    "repair_applied": false,
    "fallback_used": false,
    "fallback_mode": null,
    "fallback_reason": null,
    "rationale": []
  }
}
```

### Constraints

- Do not hide provider failure.
- Do not treat fallback as provider success.
- Do not assign high confidence to fallback without explicit rationale.
- Do not add providers.
- Do not change provider order unless separately governed.

## 15. Workstream 8: Confidence Calibration

### Goal

Add confidence as a trust signal for script construction.

Confidence must answer:

"How much can the system trust that this script plan was constructed from sufficient context, valid provider output, and acceptable script structure?"

Confidence must not answer:

"How likely is this script to perform?"

### Required Components

- context_completeness
- provider_reliability
- structure_integrity
- rubric_strength
- fallback_penalty
- genericity_penalty
- upstream_alignment

### Required Output

```json
{
  "confidence": 0.0,
  "confidence_level": "low | medium | high",
  "confidence_components": {},
  "confidence_rationale": {},
  "confidence_meaning": "trust_in_script_construction"
}
```

### Rules

- Confidence must be deterministic.
- Confidence must not be constant.
- Fallback must reduce confidence.
- missing context must reduce confidence proportionally.
- generic hook/setup/payoff must reduce confidence.
- high confidence requires strong construction evidence.

## 16. Workstream 9: Trace And Auditability Hardening

### Goal

Create a consolidated `script_trace` that allows an auditor to reconstruct why a script plan was emitted.

### Required Structure

```json
{
  "script_trace": {
    "context_governance": {},
    "quality_rubric": {},
    "hook_analysis": {},
    "setup_analysis": {},
    "payoff_analysis": {},
    "diversity_analysis": {},
    "provider_fallback_trace": {},
    "confidence_calibration": {},
    "final_script_rationale": {},
    "missing_or_degraded_inputs": [],
    "audit_summary": {}
  }
}
```

### Audit Summary

```json
{
  "reconstructible": true,
  "required_sections_present": true,
  "fallback_visible": true,
  "confidence_explained": true,
  "boundary_preserved": true,
  "silent_failure_indicators": []
}
```

### Constraints

- Do not recalculate generation.
- Do not change script output just to improve trace.
- Do not fake reconstructibility.
- Do not remove existing output fields.

## 17. Script Excellence Gate

After all workstreams pass, create:

- `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_GATE.md`
- `tests/gates/agents/script/run_script_agent_v2_6_excellence_gate.py`
- `OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`

Optional supporting artifacts:

- `OUT/audit/script_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/metrics.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/script_examples.json`

The gate must validate:

- runtime_real
- context_governed
- quality_rubric_explicit
- hook_strength_hardened
- setup_progression_hardened
- payoff_memorability_hardened
- diversity_guarded
- provider_fallback_honest
- confidence_calibrated
- traceability_complete
- boundary_preserved
- determinism_where_required
- backward_compatible
- silent_failures_detected false

## 18. Controlled Scenario Battery

The Script v2.6 gate must include scenarios for:

- clean strong context.
- missing Trend context.
- missing Learning context.
- Account Health CAUTION constraints.
- Account Health HOLD boundary representation where applicable.
- weak hook.
- weak setup progression.
- generic payoff.
- cliche script pattern.
- provider success.
- provider failure with fallback.
- deterministic replay.
- backward compatibility.

Each scenario must use the real Script service path or the actual public service entry point.

Do not stub the Script Agent itself.

## 19. Test Strategy

Focused workstream tests must be created as each implementation step begins.

Expected test families:

- `tests/agents/script/test_script_context_governance_unittest.py`
- `tests/agents/script/test_script_quality_rubric_unittest.py`
- `tests/agents/script/test_script_hook_strength_unittest.py`
- `tests/agents/script/test_script_setup_progression_unittest.py`
- `tests/agents/script/test_script_payoff_memorability_unittest.py`
- `tests/agents/script/test_script_diversity_anti_cliche_unittest.py`
- `tests/agents/script/test_script_provider_fallback_honesty_unittest.py`
- `tests/agents/script/test_script_confidence_calibration_unittest.py`
- `tests/agents/script/test_script_trace_auditability_unittest.py`
- `tests/gates/agents/script/run_script_agent_v2_6_excellence_gate.py`

Existing relevant tests must continue to pass, including:

- Script Agent phase tests.
- creative orchestrator tests.
- Strategy integration tests.
- Voice tests where script contract compatibility matters.
- Asset tests where script text compatibility matters.
- QC tests where script plan compatibility matters.

## 20. Final Verdict Schema

The final gate must emit:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "agent": "script",
  "audit_type": "SCRIPT_AGENT_V2_6_EXCELLENCE_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "runtime_real": true,
  "context_governed": true,
  "quality_rubric_explicit": true,
  "hook_strength_hardened": true,
  "setup_progression_hardened": true,
  "payoff_memorability_hardened": true,
  "diversity_guarded": true,
  "provider_fallback_honest": true,
  "confidence_calibrated": true,
  "traceability_complete": true,
  "boundary_preserved": true,
  "determinism_where_required": true,
  "backward_compatible": true,
  "silent_failures_detected": false,
  "blocking_failures": [],
  "residual_monitoring": []
}
```

## 21. Failure Conditions

The Script gate must return `HOLD` if any of the following occur:

- Script output is not runtime-real.
- provider failure is hidden.
- fallback is hidden or treated as provider success.
- confidence is fake or constant.
- high confidence is assigned to weak fallback output without rationale.
- context usage is not traceable.
- Strategy boundary is violated.
- Account Health constraints are ignored.
- Script decides publishability.
- Script becomes QC.
- hook/setup/payoff rationale is missing.
- trace is incomplete.
- deterministic replay fails.
- backward compatibility breaks.
- silent failure is detected.

## 22. Residual Monitoring

Acceptable residual monitoring may include:

- `SCRIPT_RUNTIME_HISTORY_STILL_SHORT`
- `SCRIPT_PROVIDER_RELIABILITY_STILL_MONITORED`
- `SCRIPT_QUALITY_RUBRIC_NEEDS_PRODUCTION_CALIBRATION`

These are acceptable only if:

- they are explicit.
- they are non-structural.
- they do not hide blocking failures.
- they do not affect boundary preservation.

## 23. Exit Criteria

Script v2.6 is complete only when:

- context usage is explicit.
- quality rubric is deterministic.
- hook strength is traceable.
- setup progression is traceable.
- payoff memorability is traceable.
- genericity and cliche risks are visible.
- provider path is visible.
- fallback is honest.
- confidence is calibrated as trust in script construction.
- script trace reconstructs the emitted script plan.
- existing `ScriptAgentResult` compatibility is preserved.
- downstream Voice, Asset, Editor, and QC contracts remain stable.
- Strategy remains the control layer.
- QC remains the final product quality authority.
- core pipeline remains unchanged.
- excellence gate passes.

## 24. Final Position

Script Agent v2.6 exists to make script construction more governed, explainable, and reliable.

It must improve narrative output quality and auditability without becoming Strategy, QC, Publisher, or a performance prediction engine.
