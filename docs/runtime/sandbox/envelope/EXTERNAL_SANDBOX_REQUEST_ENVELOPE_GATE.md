# EXTERNAL_SANDBOX_REQUEST_ENVELOPE_GATE

## 1. Purpose

`EXTERNAL_SANDBOX_REQUEST_ENVELOPE_GATE` is the formal pre-implementation gate specification for the external sandbox request envelope.

This artifact freezes the validation contract before any request envelope code is created.

It does not create a runner, execute tests, implement request envelope code, call external services, call platform APIs, upload content, transfer media bytes, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, collect post-publish metrics, close production residuals, modify Publisher runtime behavior, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

Future runner:

- `tests/gates/sandbox/run_external_sandbox_request_envelope_gate.py`

Final principle:

> The request envelope gate proves envelope safety before implementation. It does not authorize network execution.

## 2. Scope

In scope:

- request envelope plan validation
- envelope boundary contract
- required envelope schema
- metadata projection rules
- credential projection rules
- kill switch projection rules
- rate-limit projection rules
- dependency reference rules
- idempotency key rules
- envelope validation result rules
- forbidden field policy
- append-only evidence rules
- incident hook requirements
- anti-fake-success rules
- residual monitoring rules
- boundary preservation

Out of scope:

- request envelope implementation
- external request execution
- platform API call
- upload
- media byte transfer
- scheduler
- real publishing
- production URL
- production `platform_content_id`
- production receipt
- post-publish metrics
- attribution causality
- real provider binding
- public visibility
- Strategy changes
- QC changes
- Account Health changes
- Orchestrator changes
- Attribution changes
- Experiment changes
- core pipeline changes

## 3. Preconditions

Required prior documents:

- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_PLAN.md`
- `docs/runtime/sandbox/evidence/EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE.md`
- `docs/runtime/sandbox/evidence/EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_PLAN.md`
- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_GATE.md`

Required prior audit artifacts:

- `OUT/audit/external_sandbox_evidence_collection_gate/final_verdict.json`
- `OUT/audit/sandbox_adapter_implementation_gate/final_verdict.json`

Required prior state:

```json
{
  "external_sandbox_evidence_collection_gate": "GO_WITH_MONITORING",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "external_call_implemented": false,
  "external_call_authorized": false,
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

The future runner must fail if these preconditions are missing, invalid or contradictory.

## 4. Required Boundary Contract

The plan must freeze this boundary:

```json
{
  "envelope_type": "external_sandbox_request_envelope",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "external_call_authorized": false,
  "platform_api_execution_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "media_bytes_included": false,
  "public_visibility_requested": false,
  "production_url_allowed": false,
  "production_platform_content_id_allowed": false
}
```

Any future runner must fail if:

- envelope is treated as HTTP request
- envelope is treated as platform API call
- envelope is treated as upload payload
- envelope is treated as scheduler job
- envelope is treated as publish attempt
- envelope is treated as production evidence
- envelope is treated as platform receipt

## 5. Required Envelope Schema

The future runner must validate that the plan requires:

- `envelope_version`
- `envelope_type`
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
- `metadata_projection`
- `request_body_class`
- `media_bytes_included`
- `upload_endpoint_requested`
- `publish_endpoint_requested`
- `public_visibility_requested`
- `external_call_authorized`
- `boundary_statement`

Required fixed values:

```json
{
  "envelope_version": "external_sandbox_request_envelope_v1",
  "envelope_type": "external_sandbox_request_envelope",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "request_body_class": "metadata_shape_only",
  "media_bytes_included": false,
  "upload_endpoint_requested": false,
  "publish_endpoint_requested": false,
  "public_visibility_requested": false,
  "external_call_authorized": false
}
```

Missing required schema is a blocker.

## 6. Metadata Projection Requirements

Allowed metadata projection fields:

- `title_present`
- `description_present`
- `tags_present`
- `language_present`
- `visibility_mode`
- `account_id_ref`
- `content_id`
- `runtime_policy_ref`
- `metadata_trace_ref`
- `metadata_shape_valid`

Forbidden metadata content:

- raw full description if it contains secrets
- credentials
- tokens
- authorization headers
- production URL
- production `platform_content_id`
- fake compliance assertion
- fake regional targeting claim
- hidden performance prediction
- post-publish metric reference
- attribution causal claim

Required visibility:

```json
{
  "visibility_mode": "sandbox_only",
  "public_visibility_requested": false
}
```

Public visibility is a blocker.

## 7. Credential Projection Requirements

Allowed credential projection:

```json
{
  "credential_status": "present | missing | invalid_shape | not_checked",
  "credential_source": "environment_or_secret_manager",
  "secret_values_logged": false,
  "secret_values_persisted": false,
  "secret_scope_class": "sandbox_validation_only"
}
```

Forbidden credential content:

- `access_token`
- `client_secret`
- `api_key`
- `password`
- `authorization`
- `refresh_token`
- raw secret manager value
- exception text containing credential values

The future runner must fail if the plan allows raw credential values in any envelope, trace, JSONL, audit artifact or incident hook.

## 8. Kill Switch Projection Requirements

Required kill switch projection:

```json
{
  "kill_switch_name": "PUBLISHER_PLATFORM_KILL_SWITCH",
  "default_safe_state": "blocked",
  "active": false,
  "missing": false,
  "blocks_publish_attempt": true,
  "blocks_external_calls": true,
  "blocks_upload": true,
  "blocks_scheduler": true
}
```

Rules:

- active kill switch blocks envelope eligibility
- missing kill switch blocks envelope eligibility
- kill switch must not fail open
- blocked envelope must remain serializable
- blocked envelope must not become external call

## 9. Rate-Limit Projection Requirements

Required rate-limit projection:

```json
{
  "rate_limit_policy_version": "publisher_platform_rate_limits_v1",
  "sandbox_validation_requests_allowed": false,
  "upload_requests_allowed": false,
  "publish_requests_allowed": false,
  "max_sandbox_validation_requests_per_minute": null,
  "max_upload_requests_per_hour": null,
  "max_publish_requests_per_day": null,
  "burst_allowed": false,
  "rate_limit_exceeded_behavior": "block_and_trace"
}
```

The future runner must validate:

- `null` means disabled/not authorized, not unlimited
- upload requests remain disabled
- publish requests remain disabled
- sandbox validation requests remain disabled until a future gate authorizes them
- rate-limit exceeded blocks envelope eligibility

## 10. Dependency Reference Requirements

Required references:

- `artifact_manifest_ref`
- `metadata_payload_ref`
- `qc_trace_ref`
- `account_health_trace_ref`
- `strategy_ref`
- `publish_eligibility_trace_ref`

The future runner must validate blocker rules for:

- missing QC trace
- QC `HOLD`
- QC `REJECT`
- QC `publishable=false`
- Account Health `HOLD`
- missing artifact manifest
- missing metadata payload
- missing Strategy reference
- missing publish eligibility trace

Blocked dependency state must be explicit in envelope validation trace.

## 11. Idempotency Requirements

Required idempotency input tuple:

- `run_id`
- `content_id`
- `artifact_manifest_ref`
- `target_platform_id`
- `target_mode`

The future runner must validate that the plan requires:

- identical inputs produce identical key
- changed input produces changed key
- key is not random
- key contains no secrets
- key contains no raw credential material
- key is traceable in envelope

Missing or unstable idempotency key is a blocker.

## 12. Envelope Validation Result Requirements

Required validation result shape:

```json
{
  "envelope_valid": true,
  "eligible_for_future_external_sandbox_validation": false,
  "blocking_reasons": [],
  "warnings": [],
  "secret_leakage_detected": false,
  "forbidden_field_detected": false,
  "external_call_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "rationale": []
}
```

The future runner must validate:

- `envelope_valid=true` does not authorize external call
- future eligibility does not authorize external call
- blocked envelopes remain visible
- warnings are not converted into success
- external call remains false
- upload remains false
- scheduler remains false
- real publish remains false

## 13. Forbidden Field Requirements

Forbidden fields:

- `published_url`
- `platform_content_id`
- `production_receipt`
- `upload_url`
- `scheduler_job_id`
- `post_publish_metrics_ref`
- `expected_performance`
- `forecast`
- `predicted`
- `causal_claim`
- `access_token`
- `client_secret`
- `authorization`
- `api_key`
- `password`
- `refresh_token`

Future implementation must include deterministic forbidden-field detection.

The future runner must fail if any forbidden field is allowed or treated as monitorable only.

## 14. Append-Only Requirements

This gate does not authorize writing runtime evidence.

The future implementation may prepare this artifact shape only after implementation is approved:

- `OUT/runtime_evidence/external_sandbox_request_envelopes.jsonl`

Rules:

- append-only
- no rewrite
- no deletion
- no envelope rewritten into external response
- no envelope rewritten into production event
- no production identity backfilled

## 15. Incident Hook Requirements

Required incident hooks:

- `EXTERNAL_SANDBOX_ENVELOPE_SECRET_LEAKAGE_ATTEMPT`
- `EXTERNAL_SANDBOX_ENVELOPE_FORBIDDEN_FIELD`
- `EXTERNAL_SANDBOX_ENVELOPE_MIXED_MODE`
- `EXTERNAL_SANDBOX_ENVELOPE_PROVIDER_BINDING`
- `EXTERNAL_SANDBOX_ENVELOPE_KILL_SWITCH_BLOCK`
- `EXTERNAL_SANDBOX_ENVELOPE_CREDENTIALS_MISSING`
- `ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH`
- `QC_NON_PUBLISHABLE_BLOCKED_PUBLISH`

Incident hooks must not contain:

- secrets
- tokens
- authorization headers
- production URLs
- platform content IDs

## 16. Anti-Fake-Success Requirements

The future runner must validate that the envelope layer fails closed on:

- external call represented as completed
- platform API represented as called
- upload represented as performed
- scheduler represented as invoked
- real publish represented as performed
- URL represented as emitted
- `platform_content_id` represented as emitted
- production receipt represented as present
- envelope eligibility treated as sandbox success
- envelope validity treated as platform success
- `result_status=succeeded`

## 17. Controlled Scenario Battery

The future runner must validate these scenarios:

1. `plan_artifact_integrity`
2. `prior_external_sandbox_gate_integrity`
3. `target_platform_exact`
4. `target_mode_exact`
5. `envelope_type_defined`
6. `boundary_statement_defined`
7. `external_call_not_authorized`
8. `platform_api_not_authorized`
9. `upload_not_authorized`
10. `scheduler_not_authorized`
11. `real_publish_not_authorized`
12. `media_bytes_forbidden`
13. `public_visibility_forbidden`
14. `production_url_forbidden`
15. `platform_content_id_forbidden`
16. `required_envelope_schema_defined`
17. `metadata_projection_bounded`
18. `credential_projection_status_only`
19. `secret_values_forbidden`
20. `kill_switch_projection_blocks`
21. `rate_limit_disabled_not_unlimited`
22. `dependency_refs_required`
23. `qc_hold_blocks`
24. `qc_reject_blocks`
25. `qc_publishable_false_blocks`
26. `account_health_hold_blocks`
27. `idempotency_deterministic_rules_defined`
28. `validation_result_shape_defined`
29. `envelope_valid_not_external_success`
30. `future_eligibility_not_external_success`
31. `forbidden_field_detection_required`
32. `append_only_rules_defined`
33. `incident_hooks_defined`
34. `fake_success_rejected`
35. `post_publish_metrics_forbidden`
36. `attribution_causality_forbidden`
37. `production_residuals_remain_open`
38. `boundary_preserved`

## 18. Checklist

The future runner must include checklist entries for:

- required documents exist
- prior external sandbox evidence collection gate is `GO` or `GO_WITH_MONITORING`
- prior gate has no blocking failures
- prior gate reports no external call authorized
- prior gate reports no side effects
- target platform exact
- target mode exact
- envelope type defined
- envelope boundary statement defined
- external call unauthorized
- platform API unauthorized
- upload unauthorized
- scheduler unauthorized
- real publishing unauthorized
- media bytes forbidden
- public visibility forbidden
- production URL forbidden
- production `platform_content_id` forbidden
- required envelope schema complete
- metadata projection bounded
- credential projection status-only
- secret values forbidden
- kill switch projection defined
- kill switch blocks external call
- rate-limit disabled state not unlimited
- dependency refs required
- QC `HOLD` blocks
- QC `REJECT` blocks
- QC `publishable=false` blocks
- Account Health `HOLD` blocks
- idempotency deterministic
- validation result shape complete
- envelope validity is not external success
- future eligibility is not external success
- forbidden-field detection required
- append-only rules defined
- incident hooks defined
- fake success forbidden
- post-publish metrics forbidden
- attribution causality forbidden
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

## 19. Required Future Artifacts

Future runner must generate:

- `OUT/audit/external_sandbox_request_envelope_gate/final_verdict.json`
- `OUT/audit/external_sandbox_request_envelope_gate/checklist_results.json`
- `OUT/audit/external_sandbox_request_envelope_gate/scenario_outputs.json`
- `OUT/audit/external_sandbox_request_envelope_gate/metrics.json`
- `OUT/audit/external_sandbox_request_envelope_gate/security_review.json`
- `OUT/audit/external_sandbox_request_envelope_gate/contract_review.json`
- `OUT/audit/external_sandbox_request_envelope_gate/residual_monitoring_review.json`
- `OUT/audit/external_sandbox_request_envelope_gate/side_effect_review.json`

## 20. Metrics

Future metrics must include:

```json
{
  "critical_failures": 0,
  "blocking_failures_count": 0,
  "scenario_count": 38,
  "scenario_pass_count": 38,
  "checklist_count": 0,
  "checklist_pass_count": 0,
  "external_call_authorized": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "media_bytes_included": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "secret_leakage_detected": false,
  "forbidden_field_detected": false,
  "fake_success_detected": false,
  "post_publish_metrics_detected": false,
  "attribution_causality_detected": false,
  "production_residuals_closed": false
}
```

## 21. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

Expected likely verdict:

- `GO_WITH_MONITORING`

`HOLD` if:

- request envelope plan is missing
- prior external sandbox gate is missing or invalid
- prior external sandbox gate is `HOLD`
- prior external sandbox gate has blocking failures
- envelope implementation exists before gate approval
- external call is authorized or executed
- platform API execution appears
- upload is authorized or performed
- media bytes are allowed
- scheduler is authorized or invoked
- real publish is authorized or performed
- production URL appears
- production `platform_content_id` appears
- public visibility is allowed
- raw secret value is allowed
- forbidden-field detection is missing
- envelope validity can become external success
- envelope eligibility can become publish success
- production residual is closed
- post-publish metrics appear
- attribution causal claim appears
- Strategy, QC, Account Health, Orchestrator or core behavior changes

`GO_WITH_MONITORING` if:

- all critical checks pass
- request envelope is safely specified
- implementation has not started
- external calls remain unauthorized
- upload remains unauthorized
- scheduler remains unauthorized
- real publishing remains unauthorized
- production URL and production `platform_content_id` remain forbidden
- production residuals remain open

`GO` is not expected at this stage because the envelope is not implemented and external sandbox execution remains absent by design.

The future runner must derive verdict from evidence and must not hardcode it.

## 22. Final Verdict Schema

Future `final_verdict.json` must include:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "EXTERNAL_SANDBOX_REQUEST_ENVELOPE_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "request_envelope_planned": true,
  "request_envelope_implemented": false,
  "external_call_authorized": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "media_bytes_included": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "secret_leakage_detected": false,
  "forbidden_field_detected": false,
  "fake_success_detected": false,
  "post_publish_metrics_detected": false,
  "attribution_causality_detected": false,
  "production_residuals_closed": false,
  "metrics": {},
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_PLAN | HOLD_BEFORE_EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION"
}
```

## 23. Residual Monitoring Rules

These residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

Request envelope planning may reduce only:

- envelope schema uncertainty
- forbidden-field policy uncertainty
- credential projection uncertainty
- idempotency projection uncertainty
- dependency reference projection uncertainty

It must not reduce:

- production publish evidence residual
- real platform integration residual
- production result history residual
- external sandbox execution residual
- post-publish metric residual
- attribution causality residual

## 24. Final Criteria

The future gate passes only if:

```json
{
  "request_envelope_plan_safe": true,
  "request_envelope_implemented": false,
  "external_side_effects_detected": false,
  "external_call_authorized": false,
  "platform_api_execution_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publishing_authorized": false,
  "media_bytes_included": false,
  "fake_success_surface_locked": true,
  "production_residuals_remain_open": true,
  "publisher_boundary_preserved": true
}
```

## 25. Next Authorized Step

After this gate specification is accepted, the next authorized artifact is:

- `tests/gates/sandbox/run_external_sandbox_request_envelope_gate.py`

The runner must validate this gate without implementing envelope code or external execution.

After that runner passes, the next planning artifact may be:

- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_PLAN.md`

External calls remain unauthorized.

Platform API execution remains unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Real publishing remains unauthorized.

Production URL and production `platform_content_id` emission remain unauthorized.
