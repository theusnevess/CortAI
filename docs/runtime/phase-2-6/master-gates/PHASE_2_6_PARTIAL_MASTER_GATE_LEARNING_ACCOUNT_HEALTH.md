# PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH

## 1. Purpose

`PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH` is the partial master gate for Phase 2.6 after the Learning Agent and Account Health Agent excellence hardening workstreams.

The gate validates whether the already-hardened Wave 1 subsystems can be considered ready for v3 with monitoring before any Trend Analysis v2.6 work starts.

This gate does not implement features, mutate runtime behavior, fix code to pass, modify Strategy, modify the orchestrator, or change the core pipeline. It audits, executes controlled validation, consolidates artifacts, and emits a verdict.

## 2. Scope

In scope:

- Learning Agent v2.6 gate integrity
- Account Health Agent v2.6 gate integrity
- Account Health to Strategy integration
- Learning to Strategy integration
- governed orchestrator behavior through existing tests
- contract import and serialization
- governance artifact consistency
- deterministic replay
- fallback honesty
- boundary preservation
- trace completeness
- silent failure detection
- consistency with previous master/runtime artifacts

Out of scope:

- starting Trend Analysis v2.6
- changing Strategy
- changing Learning
- changing Account Health
- changing QC
- changing Experiment
- changing the orchestrator
- changing the core pipeline
- converting failures into residual monitoring

## 3. Preconditions

Required subsystem gates:

- `OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json`

Required planning and governance references:

- `docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md`
- `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md`
- `OUT/audit/system_governance_registry.json`

Required global audit references:

- `OUT/audit/cortai_runtime_v2_5_all_agents_extreme_checklist/final_verdict.json`
- `OUT/audit/cortai_runtime_v2_5_max_integrity_gate/final_verdict.json`
- `OUT/audit/cortai_runtime_v2_5_final_audit/final_audit_report.json`

Required command:

`python tests/gates/phase_2_6/run_phase_2_6_partial_master_gate_learning_account_health.py`

## 4. Blocks A-P

### Block A - Repository And Artifact Integrity

Validates that required documents, runners, and JSON artifacts exist and parse.

Fails if a mandatory document, runner, artifact, or valid JSON payload is missing.

### Block B - Governance Consistency

Validates frozen governance posture, no core modification policy, no subsystem mutation without governance reopen, and isolated subsystem work.

Fails if governance policy is absent, false, contradictory, or indicates unauthorized core/Strategy/QC/Learning/Experiment mutation.

### Block C - Learning v2.6 Gate Integrity

Validates the Learning Agent v2.6 excellence gate verdict and critical dimensions.

Fails on `HOLD`, fake confidence, silent failure, trace incompleteness, boundary violation, contamination mishandling, unbounded Strategy pressure, or missing policy safety.

### Block D - Account Health v2.6 Gate Integrity

Validates the Account Health Agent v2.6 excellence gate verdict and critical dimensions.

Fails on `HOLD`, missing telemetry enrichment, incomplete risk components, fake confidence, hidden degraded input, missing constraint rationale, broken `HOLD`, boundary violation, or silent failure.

### Block E - Learning Runtime Contract Integrity

Imports and validates Learning contracts and runtime output shape.

Required surfaces include `LearningAgentResult`, `LearningInsights`, `LearningPolicy`, `PatternFindingSummary`, `LearningStrategyPressure`, `LearningStrategyPressureTarget`, `learning_trace`, `policy_trace`, and `confidence_summary`.

Fails if contracts cannot import, serialize, or expose required backward-compatible fields.

### Block F - Account Health Runtime Contract Integrity

Imports and validates Account Health contracts and runtime output shape.

Required surfaces include `AccountHealthInput`, `AccountHealthResult`, `AccountHealthDecision`, `telemetry_summary`, `risk_score`, `risk_components`, `confidence`, `confidence_level`, `temporal_health`, `degraded_input_decision`, `constraint_rationale`, `health_trace`, and backward-compatible `decision_trace`.

Fails if contracts cannot import, serialize, or expose required fields.

### Block G - Unit Test Battery

Runs the Learning, Account Health, Strategy, orchestrator, Experiment, Attribution, and pipeline test battery.

Fails if a critical test fails, times out without explicit classification, or is skipped silently.

### Block H - Controlled Cross-Agent Scenarios

Runs controlled scenarios through real Learning, Account Health, and Strategy services.

Scenarios cover `SAFE`, `CAUTION`, `HOLD`, degraded Account Health, contaminated Learning, and mixed confidence/authority cases.

Fails if Learning overrides Health, Health becomes Strategy, Strategy ownership disappears, constraints vanish, or traces contradict outcomes.

### Block I - Determinism And Replay

Replays Learning, Account Health, and cross-agent scenarios.

Fails if stable fields drift without input changes.

### Block J - Fallback Honesty

Validates explicit Learning fallback/contamination handling and Account Health fallback/degraded input visibility.

Fails if fallback is hidden, treated as clean evidence, or produces inflated confidence.

### Block K - Boundary Preservation

Validates that Learning does not become Strategy/QC/Experiment/core and Account Health does not become Strategy/QC/Learning/Experiment/core.

Fails on ownership drift or hidden enforcement.

### Block L - Security And Logical Vulnerability Surface

Checks for fake confidence, fake telemetry, fake lineage, fake rationale, hidden degraded input, orphan constraints, silent `HOLD` downgrade, silent `SAFE` upgrade, contamination dominance, unsupported overblocking, and missing evidence treated as success.

Fails on any critical logical vulnerability.

### Block M - Trace And Auditability Completeness

Validates Learning trace reconstruction and Account Health `health_trace` reconstruction.

Fails if trace is incomplete, contradictory, or missing critical audit sections.

### Block N - Master Artifact Consistency

Compares Learning gate, Account Health gate, global audit artifacts, governance registry, and master state.

Fails if a recent artifact contradicts readiness, contains `HOLD`, or treats blockers as residual monitoring.

### Block O - Residual Monitoring Classification

Classifies known residuals as monitorable only when they are non-structural and explicit.

Fails if structural blockers are classified as residuals.

### Block P - Final Release Decision

Derives final verdict from all previous blocks.

Fails if any critical block fails, silent failure is detected, non-determinism appears, boundary is violated, trace is incomplete, or `HOLD` authority is broken.

## 5. Critical Failure Definitions

Critical failures include:

- missing mandatory artifact or invalid JSON artifact
- `HOLD` verdict in Learning or Account Health gate
- critical failures greater than zero in a subsystem gate
- non-empty blocking failures in a subsystem gate
- fake or constant confidence
- silent failure detected
- boundary violation
- trace incompleteness
- missing constraint rationale
- hidden fallback or hidden degraded input
- non-deterministic replay
- `HOLD` downgrade
- Learning pressure overriding Health or Strategy
- Account Health becoming Strategy
- Strategy/core/orchestrator mutation during this gate
- failed critical test battery

## 6. Verdict Semantics

`HOLD`:

Required if any blocking failure, critical failure, fake confidence, silent failure, boundary violation, trace incompleteness, critical test failure, non-determinism, or broken `HOLD` authority is detected.

`GO_WITH_MONITORING`:

Allowed when all critical blocks pass and remaining residues are explicit, bounded, and related to runtime maturity, longitudinal history, producer coverage, or already-known operational monitoring.

`GO`:

Allowed only when all blocks pass and no meaningful residual monitoring remains.

The expected likely result before Trend Analysis is `GO_WITH_MONITORING`. The runner must derive it from evidence and must not hardcode it.

## 7. Required Artifacts

The runner must write:

- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/final_verdict.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/checklist_results.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/scenario_outputs.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/metrics.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/cross_agent_consistency.json`

The final verdict must include:

- Learning Agent v2.6 readiness summary
- Account Health Agent v2.6 readiness summary
- block results A-P
- tests executed
- metrics
- blocking failures
- residual monitoring
- recommendation to proceed or hold before Trend Analysis

## 8. Final Decision Rule

The partial master gate may recommend proceeding to Trend Analysis v2.6 only when:

- Learning Agent v2.6 gate is `GO` or `GO_WITH_MONITORING`
- Account Health Agent v2.6 gate is `GO` or `GO_WITH_MONITORING`
- all blocks A-P pass
- all critical tests pass
- no fake confidence is detected
- no silent failure is detected
- no boundary violation is detected
- no non-determinism is detected
- no missing critical trace exists
- all residuals are explicit, bounded, and non-structural

Final recommendation values:

- `PROCEED_TO_TREND_ANALYSIS_AGENT_V2_6_PLAN`
- `HOLD_BEFORE_PROCEEDING`
