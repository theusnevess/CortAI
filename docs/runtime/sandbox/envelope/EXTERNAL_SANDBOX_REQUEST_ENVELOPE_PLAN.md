# EXTERNAL_SANDBOX_REQUEST_ENVELOPE_PLAN

## 1. Purpose

`EXTERNAL_SANDBOX_REQUEST_ENVELOPE_PLAN` defines the future request envelope contract for controlled external sandbox evidence collection.

This is a planning artifact only.

It does not implement the request envelope, create a runner, execute tests, call external services, call platform APIs, upload content, transfer media bytes, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, collect post-publish metrics, close production residuals, modify Publisher runtime behavior, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The goal is to freeze the exact envelope shape and safety rules before any code is written.

Final principle:

> The request envelope may describe a sandbox validation candidate. It must not become an external call.

## 2. Starting State

Canonical prior state:

```json
{
  "external_sandbox_evidence_collection_gate": "GO_WITH_MONITORING",
  "scenarios": "37/37",
  "checklist": "45/45",
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
  "production_residuals_closed": false
}
```

Required prior artifacts:

- `docs/runtime/sandbox/evidence/EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_PLAN.md`
- `docs/runtime/sandbox/evidence/EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_evidence_collection_gate.py`
- `OUT/audit/external_sandbox_evidence_collection_gate/final_verdict.json`
- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_GATE.md`
- `OUT/audit/sandbox_adapter_implementation_gate/final_verdict.json`

## 3. Scope

In scope:

- request envelope schema
- envelope validation rules
- allowed metadata projection
- forbidden payload fields
- credential status projection
- kill switch projection
- rate-limit projection
- dependency references
- idempotency key requirements
- envelope traceability
- deterministic serialization
- future implementation and gate boundaries

Out of scope:

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
- runtime behavior changes
- Strategy changes
- QC changes
- Account Health changes
- Orchestrator changes
- Attribution changes
- Experiment changes
- core pipeline changes

## 4. Envelope Boundary

The envelope is a serializable object that describes a future sandbox validation candidate.

It is not:

- an HTTP request
- a platform API call
- an upload payload
- a scheduler job
- a publish attempt
- a production evidence record
- a platform receipt

Required boundary contract:

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

The future implementation must not include any transport, network, SDK or platform client behavior.

## 5. Required Envelope Shape

Future implementation may define a deterministic serializable structure equivalent to:

```json
{
  "envelope_version": "external_sandbox_request_envelope_v1",
  "envelope_type": "external_sandbox_request_envelope",
  "run_id": "...",
  "content_id": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "idempotency_key": "...",
  "artifact_manifest_ref": "...",
  "metadata_payload_ref": "...",
  "qc_trace_ref": "...",
  "account_health_trace_ref": "...",
  "strategy_ref": "...",
  "publish_eligibility_trace_ref": "...",
  "credential_status": {},
  "kill_switch_status": {},
  "rate_limit_status": {},
  "metadata_projection": {},
  "request_body_class": "metadata_shape_only",
  "media_bytes_included": false,
  "upload_endpoint_requested": false,
  "publish_endpoint_requested": false,
  "public_visibility_requested": false,
  "external_call_authorized": false,
  "boundary_statement": "External sandbox request envelope is not an external call."
}
```

All fields must be deterministic and JSON serializable.

Missing required fields must produce a blocked envelope validation result, not fallback success.

## 6. Required Metadata Projection

The envelope may include metadata shape only.

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

For this stage, `visibility_mode` must be `sandbox_only`.

`public` visibility is forbidden.

## 7. Credential Status Projection

The envelope may include only credential status, never credential values.

Allowed:

```json
{
  "credential_status": "present | missing | invalid_shape | not_checked",
  "credential_source": "environment_or_secret_manager",
  "secret_values_logged": false,
  "secret_values_persisted": false,
  "secret_scope_class": "sandbox_validation_only"
}
```

Forbidden:

- raw access token
- client secret
- API key
- password
- authorization header
- refresh token
- secret manager materialized value
- exception text containing credential values

The future implementation must reject envelope construction if secret-like keys appear in the envelope payload.

## 8. Kill Switch Projection

The envelope must include kill switch status.

Required shape:

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
- blocked envelope must still be serializable for audit
- blocked envelope must not become external call

## 9. Rate-Limit Projection

The envelope must include rate-limit status.

Required current state:

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

Rules:

- `null` means disabled/not authorized, never unlimited
- upload requests remain disabled
- publish requests remain disabled
- sandbox validation requests remain disabled until a future gate authorizes them
- rate-limit exceeded blocks envelope eligibility

## 10. Dependency References

The envelope must include references, not embedded downstream objects.

Required references:

- `artifact_manifest_ref`
- `metadata_payload_ref`
- `qc_trace_ref`
- `account_health_trace_ref`
- `strategy_ref`
- `publish_eligibility_trace_ref`

Rules:

- missing QC trace blocks envelope eligibility
- QC `HOLD` blocks envelope eligibility
- QC `REJECT` blocks envelope eligibility
- QC `publishable=false` blocks envelope eligibility
- Account Health `HOLD` blocks envelope eligibility
- missing artifact manifest blocks envelope eligibility
- missing metadata payload blocks envelope eligibility
- missing Strategy reference blocks envelope eligibility
- missing publish eligibility trace blocks envelope eligibility

Blocked dependency state must be explicit in the envelope validation trace.

## 11. Idempotency Key

Envelope idempotency key must be deterministic.

Required input tuple:

- `run_id`
- `content_id`
- `artifact_manifest_ref`
- `target_platform_id`
- `target_mode`

Rules:

- identical inputs produce identical key
- changed input produces changed key
- key is not random
- key contains no secrets
- key contains no raw credential material
- key is traceable in envelope

Missing or unstable idempotency key is a blocker.

## 12. Envelope Validation Result

Future implementation may produce an envelope validation result.

Required shape:

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

Important:

- `envelope_valid=true` does not authorize external call
- `eligible_for_future_external_sandbox_validation=true` must not be used until a future gate authorizes it
- blocked envelopes must not be hidden
- warnings must not be converted into success

## 13. Forbidden Fields

Immediate blocker if envelope contains:

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

The future implementation must include deterministic forbidden-field detection.

## 14. Append-Only Evidence

This plan does not authorize writing external sandbox evidence yet.

Future implementation may prepare envelope audit artifacts only after a gate approves implementation.

Allowed future artifact shape:

- `OUT/runtime_evidence/external_sandbox_request_envelopes.jsonl`

Rules:

- append-only
- no rewrite
- no deletion
- no envelope rewritten into external response
- no envelope rewritten into production event
- no production identity backfilled

## 15. Incident Hooks

Future implementation must define incident hooks for:

- `EXTERNAL_SANDBOX_ENVELOPE_SECRET_LEAKAGE_ATTEMPT`
- `EXTERNAL_SANDBOX_ENVELOPE_FORBIDDEN_FIELD`
- `EXTERNAL_SANDBOX_ENVELOPE_MIXED_MODE`
- `EXTERNAL_SANDBOX_ENVELOPE_PROVIDER_BINDING`
- `EXTERNAL_SANDBOX_ENVELOPE_KILL_SWITCH_BLOCK`
- `EXTERNAL_SANDBOX_ENVELOPE_CREDENTIALS_MISSING`
- `ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH`
- `QC_NON_PUBLISHABLE_BLOCKED_PUBLISH`

Incident hooks must not contain secrets, tokens, authorization headers, production URLs or platform content IDs.

## 16. Anti-Fake-Success Rules

The envelope layer must fail closed on:

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

Envelope construction must never produce `result_status=succeeded`.

## 17. Residual Monitoring

These residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

Envelope planning may reduce only:

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

## 18. Future Implementation Files

Future implementation may be considered only after a separate implementation gate specification.

Candidate future files:

```text
backend/app/creative/agents/publisher/external_sandbox_envelope.py
backend/app/creative/agents/publisher/external_sandbox_envelope_security.py
tests/test_external_sandbox_request_envelope_unittest.py
```

This plan does not create those files.

## 19. Future Gate

Before implementation, create:

- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_GATE.md`

Future runner after implementation:

- `tests/gates/sandbox/run_external_sandbox_request_envelope_gate.py`

Expected future gate artifacts:

- `OUT/audit/external_sandbox_request_envelope_gate/final_verdict.json`
- `OUT/audit/external_sandbox_request_envelope_gate/checklist_results.json`
- `OUT/audit/external_sandbox_request_envelope_gate/scenario_outputs.json`
- `OUT/audit/external_sandbox_request_envelope_gate/metrics.json`
- `OUT/audit/external_sandbox_request_envelope_gate/security_review.json`
- `OUT/audit/external_sandbox_request_envelope_gate/contract_review.json`
- `OUT/audit/external_sandbox_request_envelope_gate/residual_monitoring_review.json`

The future gate must validate this plan before any envelope implementation.

## 20. Failure Conditions

Immediate `HOLD` if future implementation:

- executes external call
- calls platform API
- uploads content
- transfers media bytes
- invokes scheduler
- publishes content
- emits production URL
- emits production `platform_content_id`
- includes raw secret values
- allows public visibility
- allows mixed modes
- allows implicit provider binding
- treats envelope validity as external success
- treats envelope eligibility as publish success
- closes production residuals
- changes Publisher runtime behavior outside envelope construction
- changes QC, Account Health, Strategy, Orchestrator or core pipeline

## 21. Exit Criteria

This plan is acceptable only if:

```json
{
  "request_envelope_planned": true,
  "request_envelope_implemented": false,
  "external_call_authorized": false,
  "platform_api_execution_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "media_bytes_included": false,
  "public_visibility_requested": false,
  "production_url_allowed": false,
  "production_platform_content_id_allowed": false,
  "secrets_presence_only": true,
  "idempotency_key_deterministic": true,
  "production_residuals_remain_open": true,
  "boundary_preserved": true
}
```

## 22. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_GATE.md`

That gate must freeze implementation criteria before any request envelope code is created.

External calls remain unauthorized.

Platform API execution remains unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Real publishing remains unauthorized.

Production URL and production `platform_content_id` emission remain unauthorized.
