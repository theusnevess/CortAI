# PUBLISHER_TRACE_IMPLEMENTATION_PLAN

## 1. Purpose

`PUBLISHER_TRACE_IMPLEMENTATION_PLAN` defines the minimum implementation plan for Publisher traceability in Phase 3.

This is a planning artifact only.

It does not implement publishing, modify Publisher runtime behavior, integrate platform APIs, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The purpose is to plan an append-only, dry-run-first Publisher trace layer that can record publish eligibility, publish attempts, publish results, skips, failures and incident hooks without claiming publish success without evidence.

Final principle:

> Publisher trace implementation must make publish authority observable before any real publishing behavior is enabled.

## 2. Starting State

Canonical inputs:

- `docs/runtime/phase-3/PHASE_3_OPERATIONAL_GOVERNANCE_AND_MATURITY_PLAN.md`
- `docs/runtime/phase-3/monitoring/PRODUCTION_MONITORING_AND_RUNTIME_EVIDENCE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE.md`
- `OUT/audit/publisher_governance_and_publish_trace_gate/final_verdict.json`

Accepted gate state:

```json
{
  "audit_type": "PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE",
  "verdict": "GO_WITH_MONITORING",
  "critical_failures": 0,
  "blocking_failures": [],
  "recommendation": "PROCEED_TO_PUBLISHER_TRACE_IMPLEMENTATION_PLAN"
}
```

Known residuals:

- `PUBLISHER_RUNTIME_IMPLEMENTATION_NOT_STARTED`
- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`

This plan exists to reduce the first residual by defining a safe trace-only implementation path.

It does not close production evidence residuals.

## 3. Scope

Allowed implementation scope for the future trace workstream:

- append-only `publish_lifecycle` writer
- publish eligibility trace builder
- publish attempt trace builder
- publish result trace builder
- skip reason normalization
- failure reason normalization
- incident hook placeholders
- dry-run execution path first
- deterministic trace serialization
- no-success-without-evidence validation

Forbidden scope:

- real publishing
- platform API integration
- upload behavior
- scheduling behavior
- changing QC decisions
- changing QC `publishable`
- overriding Account Health `HOLD`
- changing Strategy
- changing Orchestrator
- changing Attribution
- changing Experiment
- changing core pipeline
- fabricating publish success
- fabricating URL or platform content ID
- using performance prediction as publish authority

## 4. Implementation Boundary

The trace implementation may create Publisher-owned trace primitives only.

Allowed future code surfaces should be limited to Publisher trace modules, Publisher-owned result/trace contracts, and append-only evidence writers.

The implementation must not:

- call external publishing APIs
- create publish targets that perform side effects
- alter upstream agent outputs
- reinterpret QC authority
- downgrade Account Health `HOLD`
- make Strategy publish-aware
- make Orchestrator a publish decision layer
- write success without result evidence

If a future implementation requires touching non-Publisher modules, governance must reopen that scope explicitly before code changes.

## 5. Proposed Components

Recommended future module names:

- `backend/app/creative/agents/publisher/publish_trace.py`
- `backend/app/creative/agents/publisher/publish_lifecycle_writer.py`
- `backend/app/creative/agents/publisher/publish_semantics.py`

Recommended structures:

- `PublishEligibilityTrace`
- `PublishAttemptTrace`
- `PublishResultTrace`
- `PublishLifecycleEvent`
- `PublishTraceBundle`
- `PublishTraceBuilder`
- `PublishLifecycleWriter`
- `PublishIncidentHook`

All structures must be:

- deterministic
- serializable
- additive
- trace-only
- safe under missing evidence

## 6. Eligibility Trace Builder

The eligibility builder should consume only available runtime evidence:

- QC decision
- QC `publishable`
- QC trace reference
- Account Health decision
- Account Health trace reference
- Strategy reference
- artifact manifest reference
- runtime policy reference

Required output:

```json
{
  "publish_eligibility_trace": {
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
}
```

Eligibility must be false when:

- Account Health is `HOLD`
- QC decision is `HOLD` or `REJECT`
- QC `publishable` is false
- QC trace is missing
- artifact manifest is missing
- runtime policy blocks publish
- required evidence is absent and cannot be verified

Eligibility must not become true from missing evidence.

## 7. Attempt Trace Builder

The attempt builder should record whether a publish attempt would occur under the current dry-run policy.

Required output:

```json
{
  "publish_attempt_trace": {
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
}
```

Dry-run rule:

- A dry-run may emit an `attempt_status` of `not_attempted`, `skipped`, or dry-run-equivalent metadata.
- It must not emit real publish success.
- It must not emit a real URL or platform content ID.

No future trace implementation may attempt publish when eligibility is false.

## 8. Result Trace Builder

The result builder must represent observed outcome evidence only.

Required output:

```json
{
  "publish_result_trace": {
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
}
```

Result rules:

- `succeeded` requires explicit result evidence.
- `published_url` requires explicit result evidence.
- `platform_content_id` requires explicit result evidence.
- `pending` is not success.
- `unknown` is not success.
- `skipped` is not success.
- missing evidence remains missing evidence.

## 9. Append-Only Lifecycle Writer

The future writer should append publish lifecycle events to:

- `OUT/runtime_evidence/publish_lifecycle.jsonl`

Required behavior:

- append one JSON object per lifecycle event
- never overwrite previous events
- never delete failures
- never collapse skip/failure/pending into success
- preserve trace references
- tolerate missing parent directory by creating it
- write deterministic keys where practical

Recommended event shape:

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

## 10. Skip And Failure Normalization

Allowed skip reasons:

```json
[
  "ACCOUNT_HEALTH_HOLD",
  "QC_REJECTED",
  "QC_HOLD",
  "QC_NOT_PUBLISHABLE",
  "MISSING_QC_TRACE",
  "MISSING_ARTIFACT_MANIFEST",
  "MISSING_VIDEO_ARTIFACT",
  "MISSING_STRATEGY_CONTEXT",
  "RUNTIME_POLICY_BLOCKED",
  "PUBLISH_TARGET_NOT_CONFIGURED",
  "MANUAL_APPROVAL_REQUIRED",
  "DRY_RUN_MODE",
  "UNKNOWN_PRECONDITION"
]
```

Allowed failure reasons:

```json
[
  "PUBLISH_TARGET_ERROR",
  "AUTHENTICATION_FAILURE",
  "UPLOAD_FAILURE",
  "PLATFORM_REJECTION",
  "ARTIFACT_READ_FAILURE",
  "METADATA_VALIDATION_FAILURE",
  "NETWORK_FAILURE",
  "RATE_LIMITED",
  "UNKNOWN_EXTERNAL_FAILURE",
  "UNKNOWN_INTERNAL_FAILURE"
]
```

Unknown values must be normalized to known `UNKNOWN_*` forms and must remain monitorable.

## 11. Incident Hook Placeholders

The trace implementation should define incident hook payloads but does not need to implement incident routing in the first trace workstream.

Incident hooks should be emitted for:

- `ACCOUNT_HEALTH_HOLD_OVERRIDE_ATTEMPT`
- `QC_BYPASS_ATTEMPT`
- `PUBLISH_SUCCESS_WITHOUT_EVIDENCE`
- `FAKE_URL_OR_PLATFORM_ID`
- `PUBLISH_ATTEMPT_FAILED`
- `MISSING_QC_TRACE`
- `MISSING_ARTIFACT_MANIFEST`
- `PUBLISH_RESULT_PENDING_TOO_LONG`

Recommended shape:

```json
{
  "incident_type": "string",
  "severity": "monitorable | warning | critical",
  "content_id": "string",
  "run_id": "string",
  "rationale": []
}
```

Critical incidents must block the gate until resolved.

## 12. Dry-Run First Policy

The first implementation must run in dry-run mode.

Dry-run means:

- eligibility can be evaluated
- skip can be recorded
- attempt intent can be recorded
- lifecycle events can be appended
- no platform API is called
- no content is uploaded
- no publish URL is produced
- no platform content ID is produced
- no publish success is emitted

Dry-run output may support future operational evidence collection, but it must not claim publication.

## 13. Validation Requirements

Future implementation tests must prove:

- Account Health `HOLD` blocks publish eligibility
- QC `REJECT` blocks publish eligibility
- QC `HOLD` blocks publish eligibility
- QC `publishable = false` blocks publish eligibility
- missing QC trace blocks or degrades eligibility
- missing artifact manifest blocks eligibility
- dry-run does not produce success
- fake URL without evidence fails validation
- fake platform ID without evidence fails validation
- incident hooks are emitted for unsafe states
- append-only lifecycle writer preserves previous events
- serialization is deterministic
- boundary statement is present

Required future test target:

- `tests/publisher/unit/test_publisher_trace_implementation_unittest.py`

Required future audit target:

- `tests/gates/publisher/run_publisher_trace_implementation_gate.py`

## 14. Backward Compatibility

The first implementation must be additive.

It must not:

- remove existing Publisher outputs
- rename existing fields
- change existing publish decisions
- change orchestration order
- change QC result shape
- change Account Health result shape
- require real platform credentials

If no Publisher runtime surface exists yet, the trace implementation must remain isolated until governance explicitly approves integration.

## 15. Failure Conditions

The implementation plan fails if future work:

- performs real publishing
- adds platform API integration
- emits success without evidence
- emits URL without evidence
- emits platform content ID without evidence
- allows Account Health `HOLD` to publish
- allows QC non-publishable artifacts to publish
- changes Strategy
- changes QC
- changes Account Health
- changes Orchestrator
- changes core pipeline
- hides skipped publish
- hides failed publish
- treats pending as success
- creates performance prediction authority

## 16. Exit Criteria

The implementation workstream may be considered complete only when:

```json
{
  "publish_lifecycle_writer_append_only": true,
  "eligibility_trace_builder_present": true,
  "attempt_trace_builder_present": true,
  "result_trace_builder_present": true,
  "skip_failure_normalization_present": true,
  "incident_hooks_present": true,
  "dry_run_first": true,
  "real_publishing_implemented": false,
  "fake_success_possible": false,
  "account_health_hold_bypass_possible": false,
  "qc_bypass_possible": false,
  "core_pipeline_changed": false
}
```

Expected first implementation verdict:

- `GO_WITH_MONITORING`

Expected residuals after first implementation:

- production publish evidence still unavailable
- platform integration not enabled
- publish result history still short

## 17. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

- `docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_GATE_PLAN.md`

That gate plan must validate the future trace implementation before any real publishing or platform integration is considered.
