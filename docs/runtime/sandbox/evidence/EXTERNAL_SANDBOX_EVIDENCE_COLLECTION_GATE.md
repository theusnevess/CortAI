# EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE

## 1. Purpose

`EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE` is the formal future gate specification for validating the `EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_PLAN`.

This is a gate specification artifact only.

It does not create a runner, execute tests, implement an external request envelope, call platform APIs, upload content, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, collect post-publish metrics, close production residuals, modify Publisher runtime behavior, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

Future runner:

- `tests/gates/sandbox/run_external_sandbox_evidence_collection_gate.py`

Final principle:

> The external sandbox evidence gate proves that sandbox evidence collection is safe to specify. It does not authorize external execution.

## 2. Scope

In scope:

- external sandbox evidence collection plan validation
- target and mode contract validation
- request envelope contract validation
- response evidence contract validation
- credential presence/status rules
- secret non-leakage rules
- kill switch rules
- rate-limit and timeout rules
- dependency block rules
- append-only evidence rules
- incident hook rules
- anti-fake-success rules
- residual monitoring rules
- boundary preservation

Out of scope:

- external platform execution
- platform API calls
- upload
- media byte transfer
- scheduler
- real publishing
- production URL
- production `platform_content_id`
- production receipt
- post-publish metrics
- attribution causality
- public visibility
- real provider binding
- Strategy changes
- QC changes
- Account Health changes
- Orchestrator changes
- Attribution changes
- Experiment changes
- core pipeline changes

## 3. Preconditions

Required prior documents:

- `docs/runtime/sandbox/evidence/EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_PLAN.md`
- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_PLAN.md`
- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_GATE.md`
- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_GATE.md`

Required prior implementation files:

- `backend/app/creative/agents/publisher/sandbox_contracts.py`
- `backend/app/creative/agents/publisher/sandbox_security.py`
- `backend/app/creative/agents/publisher/sandbox_adapter.py`
- `tests/publisher/unit/test_publisher_sandbox_adapter_unittest.py`

Required prior audit artifact:

- `OUT/audit/sandbox_adapter_implementation_gate/final_verdict.json`

Required prior state:

```json
{
  "sandbox_adapter_gate_verdict": "GO_WITH_MONITORING",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "adapter_present": true,
  "contracts_serializable": true,
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "no_implicit_provider_binding": true,
  "sandbox_receipt_not_production": true,
  "result_evidence_is_production": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "production_residuals_closed": false,
  "blocking_failures": []
}
```

The future runner must fail if these preconditions are missing, contradictory or invalid.

## 4. Evaluation Dimensions

The future gate must validate these dimensions:

1. Artifact integrity
2. Prior sandbox adapter gate integrity
3. External sandbox boundary integrity
4. Evidence collection mode discipline
5. Request envelope contract
6. Credential and secret governance
7. Kill switch governance
8. Rate-limit and timeout governance
9. Response evidence contract
10. Append-only evidence rules
11. Incident hook coverage
12. Dependency block preservation
13. Anti-fake-success rules
14. Residual monitoring integrity
15. Boundary preservation
16. Final decision

## 5. Required Boundary Contract

The future runner must validate this contract:

```json
{
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "external_boundary_type": "controlled_sandbox_validation",
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "no_implicit_provider_binding": true,
  "external_call_authorized": false,
  "platform_api_execution_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "production_url_allowed": false,
  "production_platform_content_id_allowed": false,
  "post_publish_metrics_allowed": false,
  "production_residuals_remain_open": true
}
```

Any contradiction in these fields is a blocker.

## 6. Request Envelope Requirements

The plan must define a future request envelope with:

- `run_id`
- `content_id`
- `target_platform_id`
- `target_mode`
- `idempotency_key`
- `artifact_manifest_ref`
- `metadata_payload_ref`
- `qc_trace_ref`
- `account_health_trace_ref`
- `strategy_ref`
- `publish_eligibility_trace_ref`
- `credential_status`
- `kill_switch_status`
- `rate_limit_status`
- `request_body_class`
- `media_bytes_included`
- `public_visibility_requested`

Required values:

```json
{
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "request_body_class": "metadata_shape_only",
  "media_bytes_included": false,
  "public_visibility_requested": false
}
```

The future runner must fail if:

- media bytes are allowed
- upload URL request is allowed
- publish endpoint request is allowed
- public visibility request is allowed
- idempotency key is absent, unstable or random
- secret values can appear in the envelope
- production URL can appear in the envelope
- production `platform_content_id` can appear in the envelope

## 7. Credential And Secret Requirements

Allowed credential trace:

```json
{
  "credential_status": "present | missing | invalid_shape | not_checked",
  "credential_source": "environment_or_secret_manager",
  "secret_values_logged": false,
  "secret_values_persisted": false,
  "secret_scope_class": "sandbox_validation_only"
}
```

The future runner must validate:

- secret values are not logged
- secret values are not written to JSONL
- secret values are not written to audit artifacts
- tokens are not included in incident hooks
- authorization headers are not included in traces
- credential values are not persisted in request or response artifacts
- missing credentials block external sandbox validation

Secret leakage is an immediate `HOLD`.

## 8. Kill Switch Requirements

Required kill switch behavior:

```json
{
  "kill_switch_name": "PUBLISHER_PLATFORM_KILL_SWITCH",
  "default_safe_state": "blocked",
  "blocks_publish_attempt": true,
  "blocks_external_calls": true,
  "blocks_upload": true,
  "blocks_scheduler": true,
  "emits_incident_hook": true,
  "writes_lifecycle_event": true
}
```

The future runner must validate that active or missing kill switch blocks:

- external sandbox request
- upload
- scheduler
- real publish
- URL emission
- `platform_content_id` emission

Kill switch fail-open is an immediate `HOLD`.

## 9. Rate Limit And Timeout Requirements

Required current state:

```json
{
  "sandbox_validation_requests_allowed": false,
  "upload_requests_allowed": false,
  "publish_requests_allowed": false,
  "max_sandbox_validation_requests_per_minute": null,
  "max_upload_requests_per_hour": null,
  "max_publish_requests_per_day": null
}
```

The future runner must validate:

- `null` means disabled/not authorized, not unlimited
- sandbox validation request budget is not silently enabled
- upload budget remains disabled
- publish budget remains disabled
- retry is deterministic and bounded
- timeout is explicit
- timeout evidence is not success
- rate-limit exhaustion blocks and traces

## 10. Response Evidence Requirements

The plan must define this future response evidence shape:

```json
{
  "result_status": "blocked | sandbox_validated | sandbox_failed | pending_sandbox",
  "result_evidence_available": true,
  "result_evidence_is_production": false,
  "result_evidence_type": "sandbox_validation_response | sandbox_error | timeout | rate_limit_response | credential_validation_response",
  "result_evidence_ref": "...",
  "receipt_hash": "...",
  "receipt_observed_at": "...",
  "external_identity_type": "none | sandbox_receipt_id",
  "published_url": null,
  "platform_content_id": null,
  "raw_response_persisted": false,
  "redacted_response_ref": "..."
}
```

The future runner must fail if:

- sandbox response is treated as production receipt
- sandbox receipt ID is treated as production `platform_content_id`
- `result_evidence_is_production` is true or missing
- `published_url` is non-null
- `platform_content_id` is non-null
- raw response may include secrets
- `sandbox_validated` means published
- `pending_sandbox` means success
- `sandbox_failed` means production failure

## 11. Append-Only Evidence Requirements

Allowed future evidence artifacts:

- `OUT/runtime_evidence/external_sandbox_validation.jsonl`
- `OUT/runtime_evidence/publish_lifecycle.jsonl`
- `OUT/runtime_evidence/external_sandbox_incidents.jsonl`
- `OUT/runtime_evidence/residual_monitoring_ledger.json`

Append-only requirements:

- no rewrite
- no deletion
- no failed/pending/skipped event rewritten into success
- no sandbox event rewritten into production event
- no production identity backfilled into sandbox event
- every event includes target, mode, idempotency key, result evidence and boundary statement

The future runner must validate these rules before any external sandbox envelope implementation is accepted.

## 12. Incident Hook Requirements

Required incident classes:

- `PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE`
- `PUBLISHER_CREDENTIALS_MISSING`
- `PUBLISHER_CREDENTIAL_VALIDATION_FAILED`
- `PUBLISHER_RATE_LIMIT_EXCEEDED`
- `PUBLISHER_EXTERNAL_SANDBOX_TIMEOUT`
- `PUBLISHER_EXTERNAL_SANDBOX_SCHEMA_INVALID`
- `PUBLISHER_EXTERNAL_SANDBOX_VALIDATION_FAILED`
- `PUBLISHER_SANDBOX_RESPONSE_MISSING`
- `PUBLISHER_FAKE_SUCCESS_ATTEMPT`
- `PUBLISHER_FAKE_URL_OR_PLATFORM_ID_ATTEMPT`
- `ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH`
- `QC_NON_PUBLISHABLE_BLOCKED_PUBLISH`

Incident hooks must include:

- incident type
- severity
- run ID
- content ID
- target platform
- target mode
- evidence reference when available
- rationale

Incident hooks must not include:

- secret values
- tokens
- authorization headers
- raw platform response bodies
- production URL
- production platform content ID

## 13. Dependency Block Requirements

External sandbox validation must remain blocked when:

- QC trace missing
- QC status is `HOLD`
- QC status is `REJECT`
- QC `publishable=false`
- Account Health decision is `HOLD`
- artifact manifest missing
- video artifact reference missing
- metadata payload reference missing
- credentials missing
- kill switch active
- rate limit not authorized
- target mode is not `sandbox_external_dry_run`
- mixed modes are present
- implicit provider binding is present

Blocked validation must produce trace evidence.

Blocked validation must not produce sandbox validation success.

## 14. Controlled Scenario Battery

The future runner must validate these scenarios:

1. `plan_artifact_integrity`
2. `prior_sandbox_adapter_gate_integrity`
3. `target_platform_exact`
4. `target_mode_exact`
5. `external_call_not_authorized`
6. `platform_api_execution_not_authorized`
7. `upload_not_authorized`
8. `scheduler_not_authorized`
9. `real_publish_not_authorized`
10. `production_url_not_allowed`
11. `platform_content_id_not_allowed`
12. `single_mode_enforced`
13. `mixed_modes_forbidden`
14. `implicit_provider_binding_forbidden`
15. `request_envelope_schema_defined`
16. `media_bytes_forbidden`
17. `public_visibility_forbidden`
18. `secret_leakage_forbidden`
19. `missing_credentials_block`
20. `kill_switch_blocks_external_request`
21. `rate_limit_disabled_not_unlimited`
22. `timeout_not_success`
23. `response_evidence_schema_defined`
24. `result_evidence_non_production`
25. `sandbox_receipt_not_production`
26. `pending_not_success`
27. `sandbox_failed_not_production_failure`
28. `append_only_rules_defined`
29. `incident_hooks_defined`
30. `qc_non_publishable_blocks`
31. `account_health_hold_blocks`
32. `fake_success_rejected`
33. `fake_url_or_platform_id_rejected`
34. `post_publish_metrics_forbidden`
35. `attribution_causality_forbidden`
36. `production_residuals_remain_open`
37. `boundary_preserved`

## 15. Checklist

The future runner must include checklist entries for:

- required documents exist
- prior sandbox adapter gate is `GO` or `GO_WITH_MONITORING`
- prior sandbox adapter gate has no blocking failures
- prior sandbox adapter gate reports no side effects
- target platform exact
- target mode exact
- external call unauthorized
- platform API unauthorized
- upload unauthorized
- scheduler unauthorized
- real publishing unauthorized
- real URL forbidden
- real `platform_content_id` forbidden
- single mode enforced
- mixed modes forbidden
- implicit provider binding forbidden
- request envelope complete
- request envelope contains no media bytes
- request envelope public visibility false
- secrets presence/status only
- missing credentials block
- kill switch required
- kill switch blocks external request
- rate limit disabled state not unlimited
- timeout cannot become success
- response evidence non-production
- sandbox receipt non-production
- pending not success
- sandbox failure not production failure
- append-only rules present
- incident hooks present
- QC dependency blocks present
- Account Health `HOLD` block present
- fake success forbidden
- fake URL forbidden
- fake platform content ID forbidden
- post-publish metrics forbidden
- attribution causal claims forbidden
- production residuals remain open
- Publisher boundary preserved
- QC unchanged
- Account Health unchanged
- Strategy unchanged
- Orchestrator unchanged
- core pipeline unchanged

Each checklist entry must include:

- `passed`
- `evidence_source`
- `failure_reason` when failed

## 16. Required Future Artifacts

Future runner must generate:

- `OUT/audit/external_sandbox_evidence_collection_gate/final_verdict.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/checklist_results.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/scenario_outputs.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/metrics.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/security_review.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/contract_review.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/residual_monitoring_review.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/side_effect_review.json`

## 17. Metrics

Future metrics must include:

```json
{
  "critical_failures": 0,
  "blocking_failures_count": 0,
  "scenario_count": 37,
  "scenario_pass_count": 37,
  "checklist_count": 0,
  "checklist_pass_count": 0,
  "external_call_authorized": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "secret_leakage_detected": false,
  "mixed_mode_detected": false,
  "implicit_provider_binding_detected": false,
  "fake_success_detected": false,
  "post_publish_metrics_detected": false,
  "attribution_causality_detected": false,
  "production_residuals_closed": false
}
```

## 18. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

Expected likely verdict:

- `GO_WITH_MONITORING`

`HOLD` if:

- required plan artifact is missing
- prior sandbox adapter gate is missing or invalid
- prior sandbox adapter gate is `HOLD`
- prior sandbox adapter gate has blocking failures
- external call is authorized
- external call is executed
- platform API execution appears
- upload is authorized or performed
- scheduler is authorized or invoked
- real publish is authorized or performed
- production URL appears
- production `platform_content_id` appears
- `result_evidence_is_production=true`
- sandbox receipt is treated as production evidence
- secret value appears in traces, JSONL, logs or audit artifacts
- Account Health `HOLD` is bypassed
- QC non-publishable state is bypassed
- mixed modes appear
- implicit provider binding appears
- production residual is closed
- post-publish metrics appear
- attribution causal claim appears
- Strategy, QC, Account Health, Orchestrator or core behavior changes

`GO_WITH_MONITORING` if:

- all critical checks pass
- plan safely defines external sandbox evidence collection
- external calls remain unauthorized
- upload remains unauthorized
- scheduler remains unauthorized
- real publishing remains unauthorized
- production URL and production `platform_content_id` remain forbidden
- production residuals remain open

`GO` is not expected at this stage because external sandbox execution, platform integration and production publishing remain absent by design.

The future runner must derive verdict from evidence and must not hardcode it.

## 19. Final Verdict Schema

Future `final_verdict.json` must include:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "external_sandbox_evidence_collection_planned": true,
  "external_call_implemented": false,
  "external_call_authorized": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "result_evidence_is_production": false,
  "secret_leakage_detected": false,
  "fake_success_detected": false,
  "post_publish_metrics_detected": false,
  "attribution_causality_detected": false,
  "production_residuals_closed": false,
  "metrics": {},
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_EXTERNAL_SANDBOX_REQUEST_ENVELOPE_PLAN | HOLD_BEFORE_EXTERNAL_SANDBOX_REQUEST_ENVELOPE"
}
```

## 20. Residual Monitoring Rules

These residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

External sandbox evidence collection planning may reduce only:

- external sandbox request envelope uncertainty
- sandbox response schema planning uncertainty
- sandbox timeout/error observability planning uncertainty
- credential presence validation planning uncertainty
- kill switch external-boundary planning uncertainty

It must not reduce:

- production publish evidence residual
- real platform integration residual
- production result history residual
- post-publish metric residual
- attribution causality residual

## 21. Final Criteria

The future gate passes only if:

```json
{
  "external_sandbox_plan_safe": true,
  "external_side_effects_detected": false,
  "external_call_authorized": false,
  "real_publishing_authorized": false,
  "platform_api_execution_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "fake_success_surface_locked": true,
  "production_residuals_remain_open": true,
  "publisher_boundary_preserved": true
}
```

## 22. Next Authorized Step

After this gate specification is accepted, the next authorized artifact is:

- `tests/gates/sandbox/run_external_sandbox_evidence_collection_gate.py`

The runner must validate this gate without creating external calls or implementing request envelope behavior.

After that runner passes, the next planning artifact may be:

- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_PLAN.md`

External sandbox execution remains unauthorized.

Real publishing remains unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Production URL and production `platform_content_id` emission remain unauthorized.
