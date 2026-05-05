# PUBLISHER_TRACE_IMPLEMENTATION_GATE

## 1. Purpose

`PUBLISHER_TRACE_IMPLEMENTATION_GATE` is the formal executable-gate specification for the future Publisher trace-only implementation.

This document freezes the contract for:

- `tests/gates/publisher/run_publisher_trace_implementation_gate.py`
- `OUT/audit/publisher_trace_implementation_gate/final_verdict.json`

This gate must only be executed after the Publisher trace-only implementation exists.

Until then, this document is a specification artifact only.

The gate must validate that Publisher trace implementation is append-only, dry-run first, deterministic, non-fabricating and unable to bypass QC or Account Health.

Final principle:

> Publisher trace implementation may make publish lifecycle observable. It must not enable real publishing or fabricate publish success.

## 2. Scope

In scope for the future gate:

- Publisher trace builders
- publish eligibility trace
- publish attempt trace
- publish result trace
- publish lifecycle event trace
- append-only lifecycle writer
- skip/failure reason normalization
- incident hook placeholders
- dry-run execution behavior
- deterministic replay
- boundary preservation
- absence of hidden publish side effects

Out of scope:

- real publishing
- platform API integration
- upload behavior
- scheduling behavior
- post-publish metrics collection
- Publisher optimization
- QC behavior changes
- Account Health behavior changes
- Strategy changes
- Orchestrator changes
- Attribution changes
- Experiment changes
- core pipeline changes

## 3. Execution Preconditions

The gate must refuse or return `HOLD` if the trace-only implementation is not present.

Required planning artifacts:

- `docs/runtime/phase-3/PHASE_3_OPERATIONAL_GOVERNANCE_AND_MATURITY_PLAN.md`
- `docs/runtime/phase-3/monitoring/PRODUCTION_MONITORING_AND_RUNTIME_EVIDENCE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE.md`
- `docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_PLAN.md`
- `docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_GATE_PLAN.md`

Required prior audit artifact:

- `OUT/audit/publisher_governance_and_publish_trace_gate/final_verdict.json`

Required future implementation surfaces:

- Publisher-owned trace builder module or modules
- Publisher-owned append-only lifecycle writer
- Publisher-owned skip/failure semantics
- Publisher-owned incident hook structure
- unit tests for trace builders and writer

Expected runner:

- `tests/gates/publisher/run_publisher_trace_implementation_gate.py`

Expected output directory:

- `OUT/audit/publisher_trace_implementation_gate/`

## 4. Runner Contract

The future runner must:

- import Publisher trace-only implementation surfaces
- avoid real publishing
- avoid platform credentials
- avoid network publishing calls
- execute controlled dry-run scenarios
- validate append-only writer behavior in an isolated test output path
- validate serialization
- validate determinism
- generate all required artifacts
- derive verdict from evidence

The runner must not:

- call platform APIs
- upload content
- schedule publication
- mutate QC, Account Health, Strategy, Orchestrator, Attribution, Experiment or core
- fabricate success evidence
- hide failed scenarios
- treat implementation absence as success

## 5. Evaluation Dimensions

The future gate must evaluate these dimensions:

```json
[
  "trace_builders_present",
  "eligibility_trace_complete",
  "attempt_trace_complete",
  "result_trace_complete",
  "lifecycle_event_complete",
  "lifecycle_writer_append_only",
  "dry_run_has_no_publish_side_effects",
  "account_health_hold_blocks_eligibility",
  "qc_reject_blocks_eligibility",
  "qc_hold_blocks_eligibility",
  "qc_non_publishable_blocks_eligibility",
  "missing_evidence_not_success",
  "fake_success_rejected",
  "fake_url_or_platform_id_rejected",
  "incident_hooks_present",
  "skip_failure_normalization_valid",
  "determinism_where_required",
  "boundary_preserved",
  "no_core_or_upstream_mutation",
  "silent_failures_detected"
]
```

Each dimension must include:

- meaning
- validation method
- failure condition
- evidence reference in `scenario_outputs.json` or `checklist_results.json`

## 6. Required Trace Schemas

### Publish Eligibility Trace

Required fields:

```json
{
  "trace_version": "publisher_governance_v1",
  "run_id": "string",
  "content_id": "string",
  "eligibility_checked": true,
  "eligible": false,
  "qc_dependency": {},
  "account_health_dependency": {},
  "strategy_dependency": {},
  "artifact_dependency": {},
  "policy_dependency": {},
  "blocking_reasons": [],
  "warnings": [],
  "rationale": []
}
```

### Publish Attempt Trace

Required fields:

```json
{
  "attempt_id": "string",
  "run_id": "string",
  "content_id": "string",
  "timestamp": "ISO-8601",
  "attempted": false,
  "publish_target": "string | null",
  "artifact_manifest_ref": "string | null",
  "eligibility_trace_ref": "string | null",
  "preconditions_satisfied": false,
  "fallback_used": false,
  "attempt_status": "not_attempted | attempted | failed | succeeded | unknown",
  "skip_reason": "string | null",
  "failure_reason": "string | null",
  "rationale": []
}
```

### Publish Result Trace

Required fields:

```json
{
  "attempt_id": "string",
  "content_id": "string",
  "observed_at": "ISO-8601",
  "result_status": "not_attempted | succeeded | failed | skipped | pending | unknown",
  "published_url": "string | null",
  "platform_content_id": "string | null",
  "failure_reason": "string | null",
  "skip_reason": "string | null",
  "result_evidence_ref": "string | null",
  "result_evidence_available": false,
  "rationale": []
}
```

### Publish Lifecycle Event

Required fields:

```json
{
  "publish_event_id": "string",
  "run_id": "string",
  "content_id": "string",
  "timestamp": "ISO-8601",
  "event_type": "PUBLISH_ELIGIBILITY_CHECKED | PUBLISH_ATTEMPTED | PUBLISH_SUCCEEDED | PUBLISH_FAILED | PUBLISH_SKIPPED",
  "eligibility": {},
  "attempt": {},
  "result": {},
  "qc_dependency": {},
  "account_health_dependency": {},
  "strategy_dependency": {},
  "artifact_refs": [],
  "fallback_used": false,
  "skip_reason": "string | null",
  "failure_reason": "string | null",
  "boundary_statement": "Publisher is explicit publish authority; QC evaluates artifact quality; Strategy controls creative direction; Account Health can block via HOLD."
}
```

## 7. Controlled Scenario Battery

The future runner must execute at least:

1. `eligible_dry_run_trace_created`
2. `account_health_hold_blocks_eligibility`
3. `qc_reject_blocks_eligibility`
4. `qc_hold_blocks_eligibility`
5. `qc_not_publishable_blocks_eligibility`
6. `missing_qc_trace_blocks_or_degrades`
7. `missing_artifact_manifest_blocks_eligibility`
8. `dry_run_does_not_publish`
9. `append_only_writer_preserves_existing_events`
10. `publish_attempt_failed_emits_incident_hook`
11. `fake_success_without_evidence_rejected`
12. `fake_url_without_evidence_rejected`
13. `fake_platform_id_without_evidence_rejected`
14. `pending_result_not_treated_as_success`
15. `skip_failure_reason_normalization`
16. `determinism_replay`
17. `backward_compatibility`

Negative scenarios pass only when unsafe behavior is rejected, blocked or surfaced as an incident.

## 8. Append-Only Writer Requirements

The future gate must prove:

- writer creates parent directory if needed
- writer appends one JSON object per line
- writer preserves existing lines
- writer never overwrites prior events
- writer never deletes failures
- writer never rewrites skipped or pending as success
- writer output is parseable JSONL
- writer can operate in an isolated audit/test path

The gate must not write production publish evidence unless explicitly configured for a controlled audit path.

## 9. Dry-Run Safety Requirements

Dry-run must guarantee:

- no platform API calls
- no upload
- no scheduling
- no real publish target side effect
- no real URL
- no real platform content ID
- no success status without explicit evidence
- dry-run skip or pending state remains explicit

The gate must fail if dry-run produces a publish success.

## 10. Incident Hook Requirements

Incident hooks must exist for:

- `ACCOUNT_HEALTH_HOLD_OVERRIDE_ATTEMPT`
- `QC_BYPASS_ATTEMPT`
- `PUBLISH_SUCCESS_WITHOUT_EVIDENCE`
- `FAKE_URL_OR_PLATFORM_ID`
- `PUBLISH_ATTEMPT_FAILED`
- `MISSING_QC_TRACE`
- `MISSING_ARTIFACT_MANIFEST`
- `PUBLISH_RESULT_PENDING_TOO_LONG`

Recommended incident hook shape:

```json
{
  "incident_type": "string",
  "severity": "monitorable | warning | critical",
  "content_id": "string",
  "run_id": "string",
  "rationale": []
}
```

Critical unsafe states must not pass without an incident hook.

## 11. Boundary Requirements

The future gate must prove:

- Publisher remains explicit publish authority
- QC remains final artifact evaluator
- QC does not publish
- Account Health `HOLD` blocks eligibility
- Strategy remains control layer
- Orchestrator remains coordinator
- Attribution remains observer of outcomes
- Experiment remains experiment governance layer
- core pipeline remains unchanged

Boundary statement required in lifecycle events:

```text
Publisher is explicit publish authority; QC evaluates artifact quality; Strategy controls creative direction; Account Health can block via HOLD.
```

## 12. Checklist

The future runner must evaluate checklist items for:

- implementation surfaces import
- trace builders present
- schema completeness
- serialization
- append-only writer behavior
- dry-run safety
- Account Health HOLD blocking
- QC blocking
- missing evidence honesty
- fake success rejection
- fake URL/platform ID rejection
- incident hooks
- skip/failure normalization
- determinism
- boundary preservation
- no silent failures

## 13. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

`HOLD` if:

- trace implementation is absent
- any required builder is absent
- append-only writer overwrites or deletes prior events
- dry-run performs real publishing
- platform API is called
- fake success is accepted
- fake URL or platform ID is accepted
- Account Health `HOLD` is overridden
- QC non-publishable artifact is eligible
- QC `HOLD` or `REJECT` is eligible
- missing evidence becomes success
- incident hooks are absent for critical unsafe states
- determinism fails
- boundary violation is detected
- core or upstream agent mutation is required
- silent failure is detected

`GO_WITH_MONITORING` if:

- all critical checks pass
- implementation is trace-only
- dry-run is safe
- real publishing remains disabled
- production publish evidence is not yet available
- residuals are explicit, bounded and non-structural

`GO` only if:

- all checks pass
- trace implementation exists
- real operational publish evidence exists
- no meaningful residual monitoring remains

Expected first executable result:

- `GO_WITH_MONITORING`

The runner must not hardcode the expected result.

## 14. Required Output Artifacts

The future runner must write:

- `OUT/audit/publisher_trace_implementation_gate/final_verdict.json`
- `OUT/audit/publisher_trace_implementation_gate/checklist_results.json`
- `OUT/audit/publisher_trace_implementation_gate/scenario_outputs.json`
- `OUT/audit/publisher_trace_implementation_gate/metrics.json`

Recommended additional artifacts:

- `OUT/audit/publisher_trace_implementation_gate/append_only_writer_checks.json`
- `OUT/audit/publisher_trace_implementation_gate/determinism_replay.json`

## 15. Final Verdict Schema

Minimum schema:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "PUBLISHER_TRACE_IMPLEMENTATION_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "trace_builders_present": true,
  "eligibility_trace_complete": true,
  "attempt_trace_complete": true,
  "result_trace_complete": true,
  "lifecycle_event_complete": true,
  "lifecycle_writer_append_only": true,
  "dry_run_has_no_publish_side_effects": true,
  "account_health_hold_blocks_eligibility": true,
  "qc_non_publishable_blocks_eligibility": true,
  "missing_evidence_not_success": true,
  "fake_success_rejected": true,
  "fake_url_or_platform_id_rejected": true,
  "incident_hooks_present": true,
  "determinism_where_required": true,
  "boundary_preserved": true,
  "silent_failures_detected": false,
  "scenario_results": {},
  "checklist_results": {},
  "metrics": {},
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_PLAN | HOLD_BEFORE_PUBLISHER_TRACE_USAGE"
}
```

## 16. Residual Monitoring

Acceptable residuals after first implementation:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`
- `PUBLISH_INCIDENT_HISTORY_STILL_SHORT`

Forbidden residual classification:

- fake success accepted
- fake URL accepted
- Account Health HOLD bypass
- QC bypass
- append-only violation
- boundary violation
- trace implementation absence
- silent failure

Structural failures must remain blockers.

## 17. Final Criteria

The future gate is valid only if:

- it can fail when implementation is absent
- it can fail when fake success is accepted
- it can fail when URL/platform ID is fabricated
- it can fail when HOLD is overridden
- it can fail when QC non-publishable is eligible
- it can fail when writer is not append-only
- it can fail when dry-run has side effects
- it produces all required artifacts
- it derives verdict from evidence
- it does not modify runtime behavior

## 18. Next Authorized Step

This document authorizes creation of the future runner only after trace-only implementation exists:

- `tests/gates/publisher/run_publisher_trace_implementation_gate.py`

If that future gate returns `GO` or `GO_WITH_MONITORING`, the next planning artifact is:

- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_PLAN.md`

Real publishing and platform API integration remain unauthorized.
