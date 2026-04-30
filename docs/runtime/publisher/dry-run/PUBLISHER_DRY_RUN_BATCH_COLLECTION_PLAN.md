# PUBLISHER_DRY_RUN_BATCH_COLLECTION_PLAN

## 1. Purpose

`PUBLISHER_DRY_RUN_BATCH_COLLECTION_PLAN` defines how to collect Publisher dry-run evidence over representative pipeline outputs.

This is a planning artifact only.

It does not implement real publishing, call platform APIs, upload content, schedule publication, emit real URLs, emit real platform content IDs, collect post-publish metrics, make attribution causal claims, modify Strategy, modify QC, modify Account Health, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The objective is to move from controlled dry-run scenarios to representative dry-run batch evidence while preserving Publisher trace-only governance.

Final principle:

> Batch dry-run evidence can prove broader trace coverage. It cannot prove platform publication or production outcome quality.

## 2. Starting State

Canonical inputs:

- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_PLAN.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_GATE.md`
- `OUT/audit/publisher_dry_run_operational_evidence_gate/final_verdict.json`
- `OUT/audit/publisher_trace_implementation_gate/final_verdict.json`
- `OUT/audit/publisher_governance_and_publish_trace_gate/final_verdict.json`

Accepted dry-run operational evidence gate state:

```json
{
  "audit_type": "PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_GATE",
  "verdict": "GO_WITH_MONITORING",
  "total_runs": 52,
  "append_only_events": 52,
  "blocking_failures": [],
  "recommendation": "PROCEED_TO_PUBLISHER_DRY_RUN_BATCH_COLLECTION"
}
```

Required remaining production residuals:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

These residuals must remain open after batch dry-run collection.

## 3. Scope

Allowed:

- dry-run Publisher trace generation over representative pipeline outputs
- batch-level coverage summary
- append-only lifecycle evidence review
- scenario/state distribution review
- QC block visibility review
- Account Health `HOLD` visibility review
- missing artifact/QC trace visibility review
- incident hook review
- residual monitoring review

Forbidden:

- platform API
- upload
- scheduler
- real publishing
- real URL
- real `platform_content_id`
- post-publish metrics
- attribution causal claims
- Strategy changes
- QC changes
- Account Health changes
- Orchestrator changes
- Attribution changes
- Experiment changes
- core pipeline changes
- production residual closure

## 4. Representative Output Selection

Batch dry-run evidence must be collected over representative pipeline outputs.

The batch should include:

- normal eligible outputs
- QC `REJECT` outputs
- QC `HOLD` outputs
- QC `publishable=false` outputs
- Account Health `HOLD` contexts
- missing QC trace cases
- missing artifact manifest cases
- missing video artifact cases when available
- dry-run skipped cases
- simulated failure cases
- pending non-success cases

The batch must not be curated to appear healthy.

Selection metadata should include:

```json
{
  "selection_mode": "representative_dry_run_batch",
  "source": "controlled_pipeline_outputs | historical_pipeline_outputs | mixed",
  "sample_size": 0,
  "included_state_classes": [],
  "excluded_state_classes": [],
  "selection_rationale": []
}
```

If real historical outputs are unavailable, the batch may use controlled representative outputs, but must label them as controlled dry-run evidence.

## 5. Required Evidence Artifacts

The future batch collection should write:

- `OUT/runtime_evidence/publish_lifecycle.jsonl`
- `OUT/runtime_evidence/publisher_dry_run_batch_summary.json`
- `OUT/runtime_evidence/publisher_dry_run_batch_incidents.jsonl`
- `OUT/runtime_evidence/residual_monitoring_ledger.json`

The future gate should write:

- `OUT/audit/publisher_dry_run_batch_collection_gate/final_verdict.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/checklist_results.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/scenario_outputs.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/metrics.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/coverage_review.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/append_only_checks.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/residual_monitoring_review.json`

## 6. Batch Coverage Requirements

Minimum recommended batch thresholds:

```json
{
  "minimum_batch_requirements": {
    "min_total_outputs": 100,
    "min_eligible_outputs": 20,
    "min_qc_blocks": 10,
    "min_account_health_hold_blocks": 5,
    "min_missing_qc_trace_cases": 3,
    "min_missing_artifact_manifest_cases": 3,
    "min_simulated_failures": 3,
    "min_pending_non_success": 3,
    "min_incident_hooks": 10,
    "min_append_only_events": 100
  }
}
```

These values may be adjusted by explicit governance update.

They must not be silently omitted.

Batch collection must fail or be classified as insufficient if the minimum coverage cannot be computed.

## 7. State Distribution Requirements

The batch must include enough variation to expose unsafe assumptions.

Required distribution checks:

- eligible outputs exist
- blocked outputs exist
- skipped outputs exist
- QC blocks exist
- Account Health `HOLD` blocks exist
- missing evidence cases exist
- incident hooks exist
- success count remains zero
- fake success remains false
- fake URL/platform ID remains false

Recommended ratio constraints:

```json
{
  "eligible_ratio_max": 0.85,
  "blocked_ratio_min": 0.10,
  "skipped_ratio_min": 0.10,
  "incident_hook_ratio_min": 0.05
}
```

The point is not to mimic production distribution.

The point is to prove observability across meaningful dry-run states.

## 8. Batch Append-Only Rules

Batch collection must preserve append-only behavior:

- existing lifecycle events remain unchanged
- new batch events are appended
- no previous event is rewritten
- no previous event is deleted
- failures remain failures
- skips remain skips
- pending remains pending
- no event becomes success
- every appended event parses as JSON

The future gate should compare before/after file state and write:

- `append_only_checks.json`

Append-only violation is a blocker.

## 9. Batch Temporal Rules

Batch collection must validate:

- event timestamps parse
- events are ordered within run
- no time travel within a run
- `run_id` is coherent
- `content_id` is coherent
- lifecycle transition is valid
- no dry-run lifecycle ends in success

Temporal checks should be written to:

- `temporal_consistency.json` if included in the future gate

Temporal inconsistency is a blocker.

## 10. Fake Signal Rules

Batch collection must fail on:

- `result_status = succeeded`
- non-null `published_url`
- non-null `platform_content_id`
- `result_evidence_available = true`
- platform receipt
- upload ID
- scheduler ID
- post-publish metric reference
- eligibility counted as success
- pending counted as success
- skipped counted as success

Dry-run batch evidence must never contain real platform success signals.

## 11. Residual Rules

These must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

Batch dry-run evidence may reduce:

- dry-run coverage uncertainty
- append-only confidence uncertainty
- incident hook visibility uncertainty
- skip/failure trace visibility uncertainty

It must not reduce:

- production publish evidence residual
- platform integration residual
- post-publish metric residual
- attribution causality residual

## 12. Incident Review

Batch collection must count and classify incident hooks.

Required incident classes:

- `MISSING_QC_TRACE`
- `MISSING_ARTIFACT_MANIFEST`
- `PUBLISH_ATTEMPT_FAILED`
- `ACCOUNT_HEALTH_HOLD_OVERRIDE_ATTEMPT` if any unsafe attempt is simulated
- `QC_BYPASS_ATTEMPT` if any unsafe attempt is simulated
- `PUBLISH_SUCCESS_WITHOUT_EVIDENCE` must remain zero
- `FAKE_URL_OR_PLATFORM_ID` must remain zero

Incident review must distinguish:

- expected controlled dry-run incidents
- monitorable operational gaps
- critical unsafe failures

Critical unsafe failures must result in `HOLD`.

## 13. Controlled Scenario Battery For Future Gate

The future batch collection gate must validate at least:

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
12. temporal consistency across batch
13. fake success absence
14. fake URL/platform ID absence
15. residual production state preserved

## 14. Gate Semantics

Future gate:

- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE.md`
- `tests/gates/publisher/run_publisher_dry_run_batch_collection_gate.py`

Expected verdict:

- `GO_WITH_MONITORING`

`HOLD` if:

- minimum batch coverage is not met
- batch is always healthy
- dry-run success appears
- URL or platform content ID appears
- platform API is called
- upload occurs
- scheduler is invoked
- append-only is violated
- temporal consistency fails
- production residual is closed
- fake causality appears
- boundary violation occurs

`GO_WITH_MONITORING` if:

- batch dry-run evidence is sufficient
- all fake signal checks pass
- append-only and temporal checks pass
- production residuals remain open
- real publishing remains disabled

`GO` is not expected for this dry-run stage because production publish evidence and platform integration remain absent by design.

## 15. Exit Criteria

Batch collection is acceptable only if:

```json
{
  "batch_outputs_reviewed": true,
  "minimum_batch_coverage_met": true,
  "state_distribution_valid": true,
  "append_only_valid": true,
  "temporal_consistency_valid": true,
  "incident_hooks_reviewed": true,
  "success_count": 0,
  "fake_url_or_platform_id_detected": false,
  "platform_api_called": false,
  "real_publishing_performed": false,
  "production_residuals_closed": false
}
```

## 16. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE.md`

Then the future runner:

- `tests/gates/publisher/run_publisher_dry_run_batch_collection_gate.py`

Real publishing remains unauthorized.
