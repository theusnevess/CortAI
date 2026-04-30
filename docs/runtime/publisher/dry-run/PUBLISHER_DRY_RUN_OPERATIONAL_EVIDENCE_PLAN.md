# PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_PLAN

## 1. Purpose

`PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_PLAN` defines how Publisher trace-only should be used in dry-run mode to collect operational evidence without real publishing.

This is a planning artifact only.

It does not implement platform API integration, upload, scheduling, real publishing, post-publish metrics, attribution causal claims, QC changes, Account Health changes, Strategy changes, Orchestrator changes, Attribution changes, Experiment changes, or core pipeline changes.

The goal is to use the accepted Publisher trace-only layer to produce runtime evidence about publish eligibility, skips, blocked states, failures, incidents and trace completeness before any real platform integration is considered.

Final principle:

> Dry-run publish evidence proves observability and governance behavior. It does not prove real publishing, platform success, post-publish performance or causality.

## 2. Starting State

Canonical inputs:

- `docs/runtime/phase-3/monitoring/PRODUCTION_MONITORING_AND_RUNTIME_EVIDENCE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE.md`
- `docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_PLAN.md`
- `docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_GATE.md`
- `OUT/audit/publisher_governance_and_publish_trace_gate/final_verdict.json`
- `OUT/audit/publisher_trace_implementation_gate/final_verdict.json`

Accepted trace implementation gate state:

```json
{
  "audit_type": "PUBLISHER_TRACE_IMPLEMENTATION_GATE",
  "verdict": "GO_WITH_MONITORING",
  "scenarios": "17/17",
  "checklist": "21/21",
  "blocking_failures": [],
  "recommendation": "PROCEED_TO_PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_PLAN"
}
```

Known residuals after trace-only implementation:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`
- `PUBLISH_INCIDENT_HISTORY_STILL_SHORT`

This plan may reduce dry-run observability residuals.

It must not close production publish evidence residuals.

## 3. Scope

Allowed:

- dry-run invocation of Publisher trace-only builders
- append-only write to `OUT/runtime_evidence/publish_lifecycle.jsonl`
- dry-run operational evidence summaries
- skip visibility checks
- failure visibility checks
- Account Health `HOLD` block visibility
- QC non-publishable block visibility
- incident hook visibility
- residual monitoring ledger updates
- dry-run audit gates

Forbidden:

- platform API calls
- real publishing
- upload
- scheduler integration
- real publish target side effects
- real published URL
- real platform content ID
- post-publish metrics collection
- attribution causal claims
- performance prediction authority
- closing production residuals without production evidence

## 4. Evidence Artifacts

Dry-run Publisher evidence should use these artifacts:

- `OUT/runtime_evidence/publish_lifecycle.jsonl`
- `OUT/runtime_evidence/publisher_dry_run_summary.json`
- `OUT/runtime_evidence/publisher_dry_run_incidents.jsonl`
- `OUT/runtime_evidence/residual_monitoring_ledger.json`

Existing Phase 3 evidence artifacts remain relevant:

- `OUT/runtime_evidence/production_runs.jsonl`
- `OUT/runtime_evidence/incidents.jsonl`

Dry-run Publisher evidence must be clearly labeled as dry-run.

It must not be mixed with real publish success evidence.

## 5. Publish Lifecycle Dry-Run Event Requirements

Each dry-run lifecycle event must include:

```json
{
  "publish_event_id": "string",
  "run_id": "string",
  "content_id": "string",
  "timestamp": "ISO-8601",
  "event_type": "PUBLISH_ELIGIBILITY_CHECKED | PUBLISH_ATTEMPTED | PUBLISH_FAILED | PUBLISH_SKIPPED",
  "dry_run": true,
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

Dry-run lifecycle events must not include:

- real platform URL
- real platform content ID
- real platform receipt
- real upload ID
- real publish success without explicit production evidence

## 6. Evidence Collection Rules

Dry-run collection must record:

- every eligibility evaluation
- every skipped publish
- every blocked publish
- every simulated or trace-level failure
- every missing QC trace
- every missing artifact manifest
- every Account Health `HOLD` block
- every QC `HOLD`, `REJECT` or `publishable=false` block
- every incident hook emitted by Publisher trace-only logic

Dry-run collection must not:

- infer success from eligibility
- infer success from absence of failure
- infer platform readiness from dry-run traces
- infer post-publish performance
- infer attribution causality

## 7. Required Dry-Run Scenarios

Minimum dry-run operational evidence should include:

1. eligible artifact in dry-run mode
2. Account Health `HOLD` blocks eligibility
3. QC `REJECT` blocks eligibility
4. QC `HOLD` blocks eligibility
5. QC `publishable=false` blocks eligibility
6. missing QC trace blocks or degrades eligibility
7. missing artifact manifest blocks eligibility
8. dry-run skipped publish remains visible
9. trace-level failed attempt remains visible
10. pending result remains non-success
11. fake success remains impossible
12. fake URL/platform ID remains impossible
13. incident hooks are emitted and countable
14. append-only lifecycle behavior holds across multiple dry-run runs

These scenarios may be executed by a future dry-run operational evidence runner.

## 8. Metrics To Collect

Dry-run summary should include:

```json
{
  "dry_run_count": 0,
  "eligibility_checks": 0,
  "eligible_count": 0,
  "blocked_count": 0,
  "skipped_count": 0,
  "failed_count": 0,
  "pending_count": 0,
  "success_count": 0,
  "account_health_hold_blocks": 0,
  "qc_blocks": 0,
  "missing_qc_trace_count": 0,
  "missing_artifact_manifest_count": 0,
  "incident_hook_count": 0,
  "fake_success_detected": false,
  "fake_url_or_platform_id_detected": false,
  "append_only_violation_detected": false
}
```

Dry-run `success_count` should remain zero unless a future explicitly governed production evidence phase is opened.

## 9. Skip And Failure Visibility

Skip reasons must remain explicit:

- `ACCOUNT_HEALTH_HOLD`
- `QC_REJECTED`
- `QC_HOLD`
- `QC_NOT_PUBLISHABLE`
- `MISSING_QC_TRACE`
- `MISSING_ARTIFACT_MANIFEST`
- `MISSING_VIDEO_ARTIFACT`
- `MISSING_STRATEGY_CONTEXT`
- `RUNTIME_POLICY_BLOCKED`
- `PUBLISH_TARGET_NOT_CONFIGURED`
- `MANUAL_APPROVAL_REQUIRED`
- `DRY_RUN_MODE`
- `UNKNOWN_PRECONDITION`

Failure reasons must remain explicit:

- `PUBLISH_TARGET_ERROR`
- `AUTHENTICATION_FAILURE`
- `UPLOAD_FAILURE`
- `PLATFORM_REJECTION`
- `ARTIFACT_READ_FAILURE`
- `METADATA_VALIDATION_FAILURE`
- `NETWORK_FAILURE`
- `RATE_LIMITED`
- `UNKNOWN_EXTERNAL_FAILURE`
- `UNKNOWN_INTERNAL_FAILURE`

Unknown reasons must be normalized and monitored.

They must not be hidden.

## 10. HOLD And QC Block Rules

Account Health `HOLD`:

- must set eligibility to false
- must prevent attempt
- must emit visible skip reason
- must remain visible in lifecycle event
- must not be downgraded to caution, warning or residual

QC non-publishable:

- must set eligibility to false
- must prevent attempt
- must emit visible skip reason
- must remain visible in lifecycle event
- must not be overridden by Publisher

QC `HOLD` and `REJECT`:

- must block eligibility
- must not become publish attempt
- must not be treated as manual approval

## 11. Fake Success Prevention

Dry-run evidence must fail validation if:

- `result_status = succeeded`
- `published_url` is non-null
- `platform_content_id` is non-null
- `result_evidence_available = true`
- production platform evidence appears

Dry-run may record:

- not attempted
- skipped
- failed
- pending
- unknown

Dry-run must not record successful publication.

## 12. Residual Monitoring Ledger

The residual ledger should track:

```json
{
  "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET": {
    "status": "open",
    "reason": "Dry-run cannot prove real production publication.",
    "closure_requires": "successful governed production publish evidence with real result proof"
  },
  "PLATFORM_INTEGRATION_NOT_ENABLED": {
    "status": "open",
    "reason": "No platform API integration is authorized in this phase.",
    "closure_requires": "separate platform integration plan and gate"
  },
  "PUBLISH_RESULT_HISTORY_STILL_SHORT": {
    "status": "open",
    "reason": "Dry-run result history is not production result history.",
    "closure_requires": "sufficient production publish result sample"
  },
  "PUBLISH_INCIDENT_HISTORY_STILL_SHORT": {
    "status": "open",
    "reason": "Dry-run incident history is limited controlled evidence.",
    "closure_requires": "sufficient operational incident window"
  }
}
```

Residuals may be reclassified only with evidence.

They must not be closed by passing dry-run tests alone.

## 13. Anti-Fake-Causality Rules

Dry-run Publisher evidence must not support:

- performance prediction
- attribution causality
- content success claims
- platform success claims
- audience outcome claims
- Learning pressure escalation
- Strategy change recommendations

Dry-run evidence can support only:

- trace coverage
- block visibility
- skip visibility
- failure visibility
- incident visibility
- append-only writer behavior
- dry-run safety

## 14. Controlled Rollout Stages

Recommended stages:

1. local controlled dry-run scenarios
2. batch dry-run over representative pipeline outputs
3. append-only evidence review
4. incident hook review
5. residual ledger update
6. dry-run operational evidence gate
7. platform integration planning only if dry-run evidence is acceptable

No stage authorizes real publishing.

## 15. Failure Conditions

This plan fails if future work:

- calls a platform API
- uploads content
- schedules publication
- produces real URL or platform content ID
- marks dry-run as successful publication
- treats eligibility as success
- treats pending as success
- hides skipped publish
- hides failed publish
- hides Account Health `HOLD`
- hides QC non-publishable block
- closes production residuals using dry-run evidence
- introduces post-publish metrics
- creates attribution causal claims
- changes QC, Account Health, Strategy, Orchestrator, Attribution, Experiment or core

## 16. Exit Criteria

Dry-run operational evidence is acceptable only if:

```json
{
  "publish_lifecycle_jsonl_generated": true,
  "dry_run_labeled": true,
  "skips_visible": true,
  "failures_visible": true,
  "account_health_hold_blocks_visible": true,
  "qc_non_publishable_blocks_visible": true,
  "fake_success_detected": false,
  "fake_url_or_platform_id_detected": false,
  "append_only_violation_detected": false,
  "production_residuals_closed": false,
  "platform_api_called": false,
  "real_publishing_performed": false
}
```

Expected outcome of a future dry-run evidence gate:

- `GO_WITH_MONITORING`

Expected remaining residuals:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

## 17. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_GATE.md`

The future gate should validate dry-run evidence artifacts before any platform integration plan is considered.

Real publishing remains unauthorized.
