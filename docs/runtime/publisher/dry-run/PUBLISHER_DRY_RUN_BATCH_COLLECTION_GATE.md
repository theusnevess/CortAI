# PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE

## 1. Purpose

`PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE` is the formal future gate specification for Publisher dry-run batch collection.

This is a gate specification only.

It does not create a runner, execute batch collection, call platform APIs, upload content, schedule publication, emit real URLs, emit real platform content IDs, collect post-publish metrics, make attribution causal claims, modify Strategy, modify QC, modify Account Health, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The gate validates dry-run Publisher evidence at representative batch scale.

It must prove trace observability across volume and state variety.

It must not prove or imply real publishing readiness.

Final principle:

> Batch dry-run collection proves Publisher trace observability at scale. It does not authorize platform integration or real publishing.

## 2. Scope

In scope:

- dry-run batch lifecycle evidence
- representative output coverage
- coverage at scale
- state distribution
- cross-run consistency
- temporal consistency
- multi-batch append-only growth
- incident hook aggregation
- residual monitoring integrity
- anti-fake-signal validation
- anti-fake-causality validation

Out of scope:

- real publishing
- platform API
- upload
- scheduler
- real URL
- real `platform_content_id`
- platform receipt
- post-publish metrics
- attribution causality
- performance prediction
- Strategy changes
- QC changes
- Account Health changes
- Orchestrator changes
- Attribution changes
- Experiment changes
- core pipeline changes

## 3. Preconditions

Required planning artifacts:

- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_PLAN.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_GATE.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_PLAN.md`

Required audit artifacts:

- `OUT/audit/publisher_governance_and_publish_trace_gate/final_verdict.json`
- `OUT/audit/publisher_trace_implementation_gate/final_verdict.json`
- `OUT/audit/publisher_dry_run_operational_evidence_gate/final_verdict.json`

Expected prior state:

```json
{
  "publisher_governance": "LOCKED",
  "trace_implementation": "VALIDATED",
  "dry_run_operational_evidence_gate": "GO_WITH_MONITORING",
  "real_publishing": "FORBIDDEN"
}
```

Future runner:

- `tests/gates/publisher/run_publisher_dry_run_batch_collection_gate.py`

This document does not create the runner.

## 4. Coverage Requirements

The future gate must enforce scale coverage.

Required minimums:

```json
{
  "minimum_batch_requirements": {
    "min_total_outputs": 100,
    "min_qc_blocks": 10,
    "min_account_health_hold_blocks": 5,
    "min_missing_trace_events": 5,
    "min_failed_attempts": 5,
    "min_pending_events": 5,
    "min_incident_hooks": 10,
    "min_append_only_events": 100
  }
}
```

The runner must not omit these requirements.

If any minimum cannot be computed, the gate must return `HOLD`.

If any minimum is not met, the gate must return `HOLD`.

Coverage must be derived from event evidence, not assumptions or comments.

## 5. Representation Requirements

The gate must prevent a biased dataset that passes without representing meaningful Publisher states.

Required representation constraints:

```json
{
  "representation_constraints": {
    "no_single_state_dominance": true,
    "max_single_state_ratio": 0.7,
    "min_distinct_state_types": 5,
    "must_include_failure_states": true,
    "must_include_blocked_states": true,
    "must_include_missing_evidence_states": true,
    "must_include_pending_states": true,
    "must_include_eligible_states": true
  }
}
```

Required state types include:

- eligible dry-run
- QC block
- Account Health `HOLD` block
- missing evidence
- simulated failure
- pending non-success
- skipped dry-run

The gate must fail if one state dominates above the configured ratio.

The gate must fail if the batch is always healthy.

## 6. Cross-Run Consistency Requirements

The gate must validate consistency across runs, not only within a single run.

Required checks:

```json
{
  "cross_run_consistency": {
    "schema_stable": true,
    "event_structure_consistent": true,
    "no_random_field_variation": true,
    "run_id_uniqueness": true,
    "content_id_traceability": true,
    "boundary_statement_stable": true
  }
}
```

The gate must validate:

- required fields are stable across all events
- event schema does not drift by state type
- `run_id` values are unique or intentionally grouped with explicit rationale
- `content_id` values remain traceable
- boundary statement is stable across events
- no random/unexplained fields appear in some events only
- trace version remains stable

Unexplained schema drift is a blocker.

## 7. Temporal Consistency Requirements

The gate must validate:

- timestamps parse
- events are orderable
- no time travel within a run
- no impossible lifecycle transition
- result timestamp does not precede attempt timestamp
- lifecycle timestamp does not contradict attempt/result timestamps
- batch ordering is coherent
- multi-batch ordering is coherent

Invalid dry-run transitions:

- any dry-run state -> `succeeded`
- skipped -> succeeded
- failed -> succeeded
- pending -> succeeded
- blocked -> attempted
- any state -> real URL or platform ID

Temporal inconsistency is a blocker.

## 8. Multi-Batch Append-Only Requirements

The gate must apply real pressure to append-only behavior.

Required checks:

```json
{
  "append_only_requirements": {
    "multi_batch_growth": true,
    "no_event_mutation": true,
    "historical_integrity_preserved": true,
    "no_event_deletion": true,
    "failure_skip_pending_preserved": true
  }
}
```

The future runner must validate at least two append phases:

1. baseline or prior batch state
2. new batch append

Required behavior:

- prior lines remain byte-for-byte stable
- new events are appended after old events
- no event is rewritten
- no event is deleted
- failures remain failures
- skips remain skips
- pending remains pending
- no prior event becomes success

Append-only violation is a blocker.

## 9. Anti-Fake-Signal Requirements

The gate must fail if any batch event contains:

- `result_status = succeeded`
- non-null `published_url`
- non-null `platform_content_id`
- `result_evidence_available = true`
- platform receipt
- upload ID
- scheduler ID
- real publish target success
- post-publish metric reference

The gate must fail if:

- eligibility is counted as success
- low failure count is interpreted as production readiness
- no error is interpreted as platform readiness
- pending is counted as success
- skipped is counted as success

Dry-run batch success count must be exactly zero.

## 10. Anti-Fake-Causality Requirements

The gate must explicitly reject causal or readiness conclusions that dry-run evidence cannot support.

Failure conditions:

- `eligible_count` used as proof of production readiness
- low failure count used as proof of system quality
- no incident used as proof of platform readiness
- dry-run trace used as post-publish metric evidence
- dry-run trace used as attribution evidence
- dry-run trace used to justify Strategy changes
- dry-run trace used to escalate Learning pressure
- dry-run trace used to close production residuals

Dry-run batch evidence may support only:

- trace coverage
- state visibility
- append-only integrity
- incident visibility
- temporal consistency
- boundary preservation

## 11. Residual Monitoring Requirements

These residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

The gate must fail if any of these are closed by dry-run batch evidence.

Batch dry-run evidence may reduce only:

- dry-run coverage uncertainty
- dry-run state representation uncertainty
- append-only integrity uncertainty
- incident hook visibility uncertainty

It must not reduce:

- production evidence residuals
- platform integration residuals
- post-publish metric residuals
- attribution causality residuals

## 12. Controlled Scenario Battery

The future gate must validate at least:

1. representative eligible batch outputs
2. QC `REJECT` batch blocks
3. QC `HOLD` batch blocks
4. QC `publishable=false` batch blocks
5. Account Health `HOLD` batch blocks
6. missing QC trace batch cases
7. missing artifact manifest batch cases
8. simulated failed attempt batch cases
9. pending non-success batch cases
10. incident hook aggregation
11. append-only lifecycle batch growth
12. multi-batch append-only growth
13. cross-run schema stability
14. run ID uniqueness
15. temporal consistency across batch
16. fake success absence
17. fake URL/platform ID absence
18. residual production state preserved
19. anti-fake-causality review

## 13. Checklist

The future runner must evaluate:

- minimum batch coverage met
- representation constraints met
- no single state dominance
- distinct state count sufficient
- failure states included
- blocked states included
- missing evidence states included
- pending states included
- cross-run schema stable
- event structure consistent
- run IDs unique or explicitly grouped
- content IDs traceable
- temporal consistency valid
- append-only multi-batch growth valid
- fake success absent
- fake URL/platform ID absent
- platform side effects absent
- production residuals remain open
- anti-fake-causality checks pass
- boundary preserved

Each checklist entry must include:

- `passed`
- evidence source
- failure reason when failed

## 14. Required Output Artifacts

Future runner must write:

- `OUT/audit/publisher_dry_run_batch_collection_gate/final_verdict.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/checklist_results.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/scenario_outputs.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/metrics.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/coverage_review.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/representation_review.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/cross_run_consistency.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/append_only_checks.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/temporal_consistency.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/residual_monitoring_review.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/anti_fake_causality_review.json`

## 15. Final Verdict Schema

Minimum final verdict schema:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "minimum_batch_coverage_met": true,
  "representation_valid": true,
  "cross_run_consistency_valid": true,
  "temporal_consistency_valid": true,
  "append_only_valid": true,
  "fake_success_detected": false,
  "fake_url_or_platform_id_detected": false,
  "platform_api_called": false,
  "real_publishing_performed": false,
  "production_residuals_closed": false,
  "anti_fake_causality_valid": true,
  "publisher_maturity": "TRACE_OBSERVABLE_AT_SCALE",
  "publishing_authorized": false,
  "platform_integration_authorized": false,
  "metrics": {},
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_PUBLISHER_PLATFORM_INTEGRATION_PLAN | HOLD_BEFORE_PLATFORM_INTEGRATION_PLAN"
}
```

## 16. Verdict Semantics

`HOLD` if:

- minimum batch coverage is not met
- representation constraints fail
- one state dominates above threshold
- failure states are missing
- blocked states are missing
- cross-run schema drift is detected
- random field variation is detected
- run IDs are incoherent
- append-only is violated
- temporal consistency fails
- dry-run success appears
- URL or platform content ID appears
- platform API is called
- upload occurs
- scheduler is invoked
- production residual is closed
- anti-fake-causality review fails
- boundary violation occurs
- silent failure is detected

`GO_WITH_MONITORING` if:

- all critical checks pass
- dry-run batch evidence is broad enough
- Publisher reaches `TRACE_OBSERVABLE_AT_SCALE`
- production residuals remain open
- platform integration remains disabled
- real publishing remains disabled

`GO` is not expected for this dry-run stage because real production publish evidence remains unavailable by design.

Expected likely result:

- `GO_WITH_MONITORING`

The future runner must derive verdict from evidence and must not hardcode it.

## 17. Post-Gate State

If the future gate passes, the new maturity state is:

```json
{
  "publisher_maturity": "TRACE_OBSERVABLE_AT_SCALE",
  "publishing_authorized": false,
  "platform_integration_authorized": false,
  "production_publish_evidence_available": false
}
```

This state permits planning for platform integration.

It does not permit platform integration execution.

It does not permit real publishing.

## 18. Next Authorized Step

If this gate specification is accepted, the next authorized artifact is:

- `tests/gates/publisher/run_publisher_dry_run_batch_collection_gate.py`

If that future gate returns `GO_WITH_MONITORING`, the next planning artifact is:

- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_PLAN.md`

Real publishing remains unauthorized until a separate platform integration plan and gate explicitly approve it.
