# SANDBOX_ADAPTER_IMPLEMENTATION_PLAN

## 1. Purpose

`SANDBOX_ADAPTER_IMPLEMENTATION_PLAN` defines the future implementation plan for a Publisher sandbox adapter after `PUBLISHER_PLATFORM_INTEGRATION_GATE` returned `GO_WITH_MONITORING`.

This is a planning artifact only.

It does not implement an adapter, call platform APIs, load real credentials, upload content, schedule publication, emit real URLs, emit real platform content IDs, collect post-publish metrics, close production residuals, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The goal is to plan a sandbox adapter that can validate contracts and produce sandbox evidence without creating external side effects.

Final principle:

> The sandbox adapter may prove integration discipline. It must not publish, upload or fabricate platform success.

## 2. Starting State

Canonical prior state:

```json
{
  "publisher_platform_integration_gate": "GO_WITH_MONITORING",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "result_evidence_is_production": false,
  "idempotency_key_deterministic": true,
  "no_implicit_provider_binding": true,
  "kill_switch_blocks_publish_attempt": true,
  "sandbox_validation_requests_allowed": false,
  "upload_requests_allowed": false,
  "publish_requests_allowed": false,
  "platform_api_execution_authorized": false,
  "real_publishing_authorized": false
}
```

Required prior artifacts:

- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_PLAN.md`
- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_GATE.md`
- `tests/gates/publisher/run_publisher_platform_integration_gate.py`
- `OUT/audit/publisher_platform_integration_gate/final_verdict.json`

Accepted prior gate requirements:

- scenarios `34/34`
- checklist `33/33`
- critical failures `0`
- blocking failures `[]`
- platform API called `false`
- upload performed `false`
- scheduler invoked `false`
- real publishing performed `false`
- production residuals closed `false`

## 3. Scope

Allowed for future implementation planning:

- sandbox adapter interface
- sandbox payload validator
- credential presence/status checker without secret values
- kill switch evaluator
- rate-limit policy evaluator
- deterministic idempotency key builder
- sandbox receipt simulator only if explicitly labeled as simulated
- sandbox receipt parser only for non-production sandbox response evidence
- append-only lifecycle writer integration
- incident hook emission
- result evidence shape validation
- no-side-effect test runner

Forbidden:

- real platform API call
- real upload
- scheduler
- real publish
- real URL
- real `platform_content_id`
- production provider binding
- fallback into YouTube, TikTok, Instagram or another real provider
- loading or logging real secret values
- post-publish metrics
- attribution causality
- closing production residuals
- changing QC
- changing Account Health
- changing Strategy
- changing Orchestrator
- changing core pipeline

## 4. Proposed Future Files

Future implementation may create these files only after a separate implementation gate/authorization:

```text
backend/app/creative/agents/publisher/sandbox_adapter.py
backend/app/creative/agents/publisher/sandbox_contracts.py
backend/app/creative/agents/publisher/sandbox_security.py
tests/publisher/unit/test_publisher_sandbox_adapter_unittest.py
```

This plan does not create those files.

Future implementation must remain additive and must not modify existing Publisher trace-only behavior unless a gate explicitly approves the exact change.

## 5. Adapter Boundary

The sandbox adapter must remain a contract validator and evidence producer for sandbox-only flows.

It may:

- validate input payload shape
- validate metadata shape
- validate credential presence status
- validate kill switch state
- validate rate-limit policy state
- validate idempotency key determinism
- emit sandbox validation result
- emit sandbox incident hooks
- write append-only lifecycle evidence

It must not:

- execute production upload
- execute production publish
- schedule content
- claim a production receipt
- claim a production URL
- claim a production platform content ID
- claim post-publish outcome
- become QC, Strategy or Attribution

## 6. Target And Mode Contract

The future adapter must hard-require:

```json
{
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "no_implicit_provider_binding": true
}
```

Failure if:

- target platform differs
- target mode differs
- more than one mode is present
- fallback mode exists
- real provider appears without separate approval artifact
- implementation references a real provider as target

## 7. Credentials And Secrets

Future adapter may check only credential presence/status.

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

Forbidden:

- logging raw secret values
- writing raw secret values to lifecycle JSONL
- writing raw secret values to audit artifacts
- including tokens in incident hooks
- including authorization headers in traces
- storing platform access tokens in runtime evidence

Missing credentials must produce:

- blocked status
- incident hook
- append-only lifecycle evidence

Missing credentials must not produce sandbox success.

## 8. Kill Switch

Future adapter must evaluate kill switch before any attempt state.

Required behavior:

```json
{
  "kill_switch_name": "PUBLISHER_PLATFORM_KILL_SWITCH",
  "active_value": "1",
  "default_safe_state": "blocked",
  "blocks_publish_attempt": true,
  "blocks_external_calls": true,
  "blocks_upload": true,
  "blocks_scheduler": true,
  "emits_incident_hook": true,
  "writes_lifecycle_event": true
}
```

If kill switch is active or missing and default safe state applies:

- `attempted = false`
- `attempt_status = blocked`
- `result_status = blocked`
- incident hook `PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE`
- no external call
- no upload
- no scheduler
- no URL
- no `platform_content_id`

## 9. Rate Limits

Future adapter must treat disabled requests as disabled, not unlimited.

Required policy:

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
  "backoff_strategy": "deterministic_exponential_or_fixed",
  "rate_limit_exceeded_behavior": "block_and_trace"
}
```

Rules:

- `null` means disabled/not authorized
- disabled does not mean unlimited
- upload and publish remain unauthorized
- rate-limit exceeded blocks and traces
- retry must be deterministic and bounded
- unbounded retry is forbidden

## 10. Idempotency Key

Future adapter must produce deterministic idempotency keys.

Key inputs:

- `run_id`
- `content_id`
- `artifact_manifest_ref`
- `platform_target`
- `platform_mode`

Rules:

- same inputs produce same key
- changed input produces changed key
- key is traceable
- key is not random
- key contains no secrets
- key must not encode raw platform credentials

Missing or unstable idempotency key is a blocker.

## 11. Upload And Metadata Validation

Future adapter may validate upload and metadata contracts.

It must not upload.

Required upload fields:

- `content_id`
- `run_id`
- `artifact_manifest_ref`
- `video_artifact_ref`
- `metadata_payload_ref`
- `qc_trace_ref`
- `account_health_trace_ref`
- `strategy_ref`
- `publish_eligibility_trace_ref`
- `idempotency_key`
- `platform_target`
- `platform_mode`

Required metadata fields:

- `title`
- `description`
- `tags`
- `language`
- `visibility_mode`
- `account_id`
- `content_id`
- `runtime_policy_ref`
- `metadata_trace_ref`

Only `sandbox_only` visibility is allowed.

`public` visibility is forbidden.

Metadata must not contain:

- fake compliance assertion
- fake regional targeting
- hidden performance prediction
- external platform ID before receipt
- publish URL before receipt

## 12. Dependency Blocks

Future adapter must block when:

- QC trace missing
- QC status is `HOLD`
- QC status is `REJECT`
- QC `publishable = false`
- Account Health decision is `HOLD`
- artifact manifest missing
- video artifact missing
- metadata missing
- credentials missing
- kill switch active
- target mode not sandbox

Every block must be visible in lifecycle evidence and incident hooks where appropriate.

## 13. Sandbox Result Evidence

Future adapter may emit sandbox evidence only under strict semantics.

Required result shape:

```json
{
  "result_status": "not_attempted | skipped | blocked | sandbox_validated | sandbox_failed | pending_sandbox",
  "result_evidence_available": true,
  "result_evidence_is_production": false,
  "result_evidence_type": "sandbox_receipt | platform_error | rate_limit_response | credential_validation_response | none",
  "result_evidence_ref": "...",
  "receipt_hash": "...",
  "receipt_observed_at": "...",
  "external_identity_type": "none | sandbox_receipt_id",
  "published_url": null,
  "platform_content_id": null
}
```

Rules:

- sandbox receipt is not production receipt
- sandbox receipt does not authorize production publish
- sandbox receipt does not close production residuals
- `result_evidence_is_production` must be false
- missing production flag is invalid
- `published_url` must be null
- `platform_content_id` must be null
- `result_status = succeeded` is forbidden

## 14. Append-Only Lifecycle

Future adapter must write append-only lifecycle evidence only.

Required artifact:

- `OUT/runtime_evidence/publish_lifecycle.jsonl`

Rules:

- no rewrite
- no deletion
- no backfill of production identity
- no failed/pending/skipped event rewritten into success
- no sandbox event rewritten into production event
- every event must include mode, target, result evidence and boundary statement

## 15. Incident Hooks

Future adapter must emit incident hooks for:

- `PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE`
- `PUBLISHER_CREDENTIALS_MISSING`
- `PUBLISHER_CREDENTIAL_VALIDATION_FAILED`
- `PUBLISHER_RATE_LIMIT_EXCEEDED`
- `PUBLISHER_SANDBOX_VALIDATION_FAILED`
- `PUBLISHER_RECEIPT_MISSING`
- `PUBLISHER_RECEIPT_SCHEMA_INVALID`
- `PUBLISHER_FAKE_SUCCESS_ATTEMPT`
- `PUBLISHER_FAKE_URL_OR_PLATFORM_ID_ATTEMPT`
- `ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH`
- `QC_NON_PUBLISHABLE_BLOCKED_PUBLISH`

Incident hooks must never include secret values.

## 16. Anti-Fake Success

Future adapter must fail closed on:

- `result_status = succeeded`
- production URL in any sandbox result
- production platform content ID in any sandbox result
- `result_evidence_is_production = true`
- sandbox receipt treated as production receipt
- missing receipt treated as success
- pending treated as success
- dry-run treated as success
- eligibility treated as success

Any fake success path must produce `HOLD` in the future implementation gate.

## 17. Residual Monitoring

These residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

Sandbox adapter implementation may reduce only:

- sandbox adapter contract uncertainty
- credential presence validation uncertainty
- sandbox payload validation uncertainty
- sandbox result evidence schema uncertainty
- no-side-effect execution uncertainty

It must not reduce:

- production publish evidence residual
- platform integration residual
- production result history residual
- post-publish metric residual
- attribution causality residual

## 18. Future Test Requirements

Future implementation tests must cover:

1. target and mode exact match
2. mixed mode rejected
3. implicit provider binding rejected
4. missing credentials blocked
5. secret value not logged or persisted
6. kill switch blocks publish attempt
7. kill switch blocks external call
8. disabled rate limit is not unlimited
9. deterministic idempotency key
10. stable idempotency key for identical inputs
11. QC `REJECT` blocks
12. QC `HOLD` blocks
13. QC `publishable=false` blocks
14. Account Health `HOLD` blocks
15. missing artifact blocks
16. missing video blocks
17. sandbox receipt not production
18. production evidence flag false
19. fake URL rejected
20. fake `platform_content_id` rejected
21. `result_status=succeeded` rejected
22. append-only lifecycle preserved
23. residuals remain open
24. no platform API call
25. no upload
26. no scheduler
27. no real publish

## 19. Future Gate

Before implementation is accepted, create and execute:

- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_GATE.md`
- `tests/gates/sandbox/run_sandbox_adapter_implementation_gate.py`
- `OUT/audit/sandbox_adapter_implementation_gate/final_verdict.json`

Expected likely verdict:

- `GO_WITH_MONITORING`

That gate must prove:

- adapter exists
- adapter is sandbox-only
- no side effects occur
- kill switch blocks attempt
- secrets do not leak
- result evidence stays non-production
- fake success is rejected
- production residuals remain open

## 20. Failure Conditions

Immediate `HOLD` if future implementation:

- calls platform API
- uploads content
- schedules content
- publishes content
- emits production URL
- emits production platform content ID
- loads/logs raw secret values
- allows mixed modes
- binds implicit real provider
- lets kill switch fail open
- treats sandbox receipt as production
- sets `result_evidence_is_production = true`
- closes production residuals
- bypasses Account Health `HOLD`
- bypasses QC non-publishable
- changes Strategy, QC, Account Health, Orchestrator or core pipeline

## 21. Exit Criteria

This plan is acceptable only if:

```json
{
  "sandbox_adapter_planned": true,
  "implementation_created": false,
  "platform_api_allowed": false,
  "upload_allowed": false,
  "scheduler_allowed": false,
  "real_publish_allowed": false,
  "real_url_allowed": false,
  "platform_content_id_allowed": false,
  "kill_switch_required": true,
  "secrets_presence_only": true,
  "sandbox_receipt_not_production": true,
  "production_residuals_remain_open": true
}
```

## 22. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_GATE.md`

That artifact must freeze the implementation gate before any sandbox adapter code is written.

Real publishing remains unauthorized.

Platform API execution remains unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Production URL and production `platform_content_id` emission remain unauthorized.
