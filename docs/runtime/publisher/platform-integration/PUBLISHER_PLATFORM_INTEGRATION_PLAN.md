# PUBLISHER_PLATFORM_INTEGRATION_PLAN

## 1. Purpose

`PUBLISHER_PLATFORM_INTEGRATION_PLAN` defines the first governed plan for Publisher platform integration after Publisher trace observability reached batch scale.

This is a planning artifact only.

It does not implement platform integration, call platform APIs, upload content, schedule publication, emit real URLs, emit real platform content IDs, collect post-publish metrics, close production residuals, modify Publisher runtime behavior, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The purpose is to freeze integration boundaries before any external side effect is introduced.

Final principle:

> Platform integration can only be introduced after the system proves it can distinguish real platform evidence from trace intent.

## 2. Starting State

Canonical prior state:

```json
{
  "publisher_maturity": "TRACE_OBSERVABLE_AT_SCALE",
  "publishing_authorized": false,
  "platform_integration_authorized": false,
  "real_publishing_performed": false,
  "platform_api_called": false,
  "success_count": 0,
  "production_residuals_closed": false
}
```

Required prior artifacts:

- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE.md`
- `docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_PLAN.md`
- `docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_GATE.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_PLAN.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_GATE.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_PLAN.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE.md`
- `OUT/audit/publisher_dry_run_batch_collection_gate/final_verdict.json`

Accepted batch gate state:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "publisher_maturity": "TRACE_OBSERVABLE_AT_SCALE",
  "minimum_batch_coverage_met": true,
  "representation_valid": true,
  "append_only_valid": true,
  "temporal_consistency_valid": true,
  "anti_fake_causality_valid": true,
  "publishing_authorized": false,
  "platform_integration_authorized": false
}
```

## 3. Integration Boundary

Publisher remains the explicit publish authority.

Publisher must consume:

- QC decision and `publishable`
- Account Health decision, especially `HOLD`
- Strategy reference
- artifact manifest
- runtime publish policy
- platform integration mode
- platform credential availability status

Publisher must not:

- override Account Health `HOLD`
- override QC non-publishable state
- reinterpret Strategy as publish permission
- fabricate platform result evidence
- treat eligibility as success
- treat pending as success
- treat dry-run as production evidence
- close production residuals without real receipt evidence

QC remains final artifact evaluator.

Account Health retains `HOLD` blocking authority.

Strategy remains the control layer and does not publish.

Orchestrator coordinates and must not become Publisher.

## 4. Initial Target Platform

Initial integration target:

```json
{
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "publish_surface": "short_video",
  "account_scope": "single_governed_account",
  "real_publish_enabled": false,
  "real_upload_enabled": false,
  "scheduler_enabled": false,
  "platform_api_execution_authorized": false
}
```

This target is intentionally a governed sandbox target, not a production platform target.

Concrete provider binding, such as YouTube, TikTok, Instagram or any other external service, must be approved by a later platform configuration artifact and must use official platform documentation at implementation time.

No implementation may assume a real provider from this document alone.

Implicit provider binding is forbidden.

The strings `YouTube`, `TikTok`, `Instagram` or any real provider name must not appear in implementation configuration unless a separate platform-provider approval artifact exists.

Fallback from `SHORT_VIDEO_PLATFORM_SANDBOX_V1` into a real provider is forbidden.

## 5. Sandbox And External Dry-Run Mode

The first allowed integration mode is external dry-run only.

Required semantics:

- external adapter may validate payload shape
- external adapter may validate credential presence without revealing secret values
- external adapter may validate rate-limit budget configuration
- external adapter may return a sandbox receipt only if the sandbox endpoint genuinely returns one
- sandbox receipt must be labeled `sandbox_receipt`, never production receipt
- sandbox result must not be treated as published

Forbidden in this mode:

- real upload
- real publish
- scheduler execution
- production URL emission
- production platform content ID emission
- post-publish metric collection
- attribution linkage as production evidence

Allowed result statuses:

- `not_attempted`
- `skipped`
- `blocked`
- `sandbox_validated`
- `sandbox_failed`
- `pending_sandbox`

Forbidden result statuses:

- `succeeded`
- `published`
- `production_published`

## 6. Credentials And Secrets

Credential handling must be explicit before implementation.

Required secret model:

```json
{
  "credential_source": "environment_or_secret_manager",
  "secret_values_logged": false,
  "secret_presence_trace_only": true,
  "credential_rotation_supported": true,
  "credential_scope_minimized": true,
  "missing_credentials_block_integration": true
}
```

Required environment contract for future implementation:

- `PUBLISHER_PLATFORM_TARGET`
- `PUBLISHER_PLATFORM_MODE`
- `PUBLISHER_PLATFORM_ACCOUNT_ID`
- `PUBLISHER_PLATFORM_CLIENT_ID` or secret-manager equivalent
- `PUBLISHER_PLATFORM_CLIENT_SECRET` or secret-manager equivalent
- `PUBLISHER_PLATFORM_ACCESS_TOKEN` or secret-manager equivalent
- `PUBLISHER_PLATFORM_KILL_SWITCH`

Rules:

- never write secret values to JSONL artifacts
- never write secret values to logs
- never include tokens in incident hooks
- never include authorization headers in traces
- only record secret presence, scope class and validation status

Missing credentials must produce `blocked_missing_credentials`, not fallback success.

## 7. Rate Limits

Rate limits must be configured before any external call.

Required fields:

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

For this plan:

- sandbox validation limits may be planned
- sandbox validation, upload and publish request permissions remain false until a later gate authorizes them
- `null` request limits mean disabled/not authorized, not unlimited
- rate-limit exhaustion must emit incident hooks
- rate-limit exhaustion must not retry indefinitely
- retry behavior must be deterministic and bounded

## 8. Upload Contract

Future upload contract must be explicit before implementation.

Required input fields:

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

Required validation:

- artifact manifest exists
- video artifact exists
- QC is present
- QC status is `APPROVE`
- QC `publishable` is true
- Account Health is not `HOLD`
- Strategy reference exists
- runtime policy allows publish attempt in the configured mode
- idempotency key is deterministic
- idempotency key is stable for identical `run_id`, `content_id`, `artifact_manifest_ref`, `platform_target` and `platform_mode`
- idempotency key is traceable and never random

Forbidden:

- upload without artifact manifest
- upload without QC trace
- upload when QC is `HOLD` or `REJECT`
- upload when QC `publishable` is false
- upload when Account Health is `HOLD`
- upload when kill switch is active
- upload in production mode before production gate approval

## 9. Metadata Contract

Metadata payload must be validated before platform handoff.

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

Governed metadata requirements:

- no fabricated claims
- no fake compliance assertion
- no fake regional targeting
- no hidden performance prediction
- no external platform ID before receipt
- no publish URL before receipt

Visibility modes:

- `sandbox_only`
- `private_draft`
- `unlisted_test` only if later platform gate allows it
- `public` forbidden until real publish gate approval

For this plan, only `sandbox_only` is authorized.

## 10. Eligibility Preconditions

Platform integration eligibility is stricter than trace-only eligibility.

Required preconditions:

```json
{
  "qc_approve_required": true,
  "qc_publishable_required": true,
  "account_health_hold_blocks": true,
  "artifact_manifest_required": true,
  "video_artifact_required": true,
  "metadata_required": true,
  "credentials_required": true,
  "kill_switch_must_be_inactive": true,
  "rate_limit_budget_required": true,
  "mode_must_be_sandbox_external_dry_run": true
}
```

Failure of any precondition must produce a blocked or skipped trace.

No precondition failure may be represented as platform success.

## 11. Result Evidence Contract

Result evidence must be tied to real platform or sandbox response evidence.

Required result evidence fields:

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

- `result_evidence_available = true` only when an actual external sandbox response exists
- `result_evidence_is_production = false` is mandatory in sandbox mode
- absence of `result_evidence_is_production` is treated as invalid
- sandbox receipt ID is not production `platform_content_id`
- sandbox receipt does not close production residuals
- platform error evidence must be preserved
- timeout evidence must be preserved
- pending evidence must remain pending

Forbidden:

- `published_url` in sandbox mode
- production `platform_content_id` in sandbox mode
- `result_evidence_is_production = true` in sandbox mode
- `result_status = succeeded`
- success without receipt
- receipt without raw evidence reference
- manually invented receipt ID

## 12. Publish Lifecycle Artifact

Future integration must continue append-only lifecycle evidence.

Required artifact:

- `OUT/runtime_evidence/publish_lifecycle.jsonl`

Each lifecycle event must include:

- `publish_event_id`
- `run_id`
- `content_id`
- `timestamp`
- `platform_target`
- `platform_mode`
- `eligibility`
- `attempt`
- `result`
- `credential_status`
- `rate_limit_status`
- `kill_switch_status`
- `qc_dependency`
- `account_health_dependency`
- `artifact_refs`
- `incident_hooks`
- `boundary_statement`

Append-only rules remain:

- no rewrite
- no deletion
- no failed/pending/skipped event rewritten into success
- no sandbox event rewritten into production event
- no production identity backfilled into older sandbox events

## 13. Rollback And Kill Switch

Kill switch must exist before any external call.

Required kill switch behavior:

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

Rollback means disabling integration and preserving evidence.

Rollback must not:

- delete lifecycle evidence
- erase failed attempts
- convert attempts into skipped success
- close incidents without review
- invalidate audit artifacts

## 14. Incident Hooks

Future integration must emit incident hooks for:

- `PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE`
- `PUBLISHER_CREDENTIALS_MISSING`
- `PUBLISHER_CREDENTIAL_VALIDATION_FAILED`
- `PUBLISHER_RATE_LIMIT_EXCEEDED`
- `PUBLISHER_SANDBOX_VALIDATION_FAILED`
- `PUBLISHER_PLATFORM_TIMEOUT`
- `PUBLISHER_PLATFORM_5XX`
- `PUBLISHER_PLATFORM_4XX`
- `PUBLISHER_RECEIPT_MISSING`
- `PUBLISHER_RECEIPT_SCHEMA_INVALID`
- `PUBLISHER_FAKE_SUCCESS_ATTEMPT`
- `PUBLISHER_FAKE_URL_OR_PLATFORM_ID_ATTEMPT`
- `ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH`
- `QC_NON_PUBLISHABLE_BLOCKED_PUBLISH`

Incident hooks must include:

- incident type
- severity
- run ID
- content ID
- platform target
- mode
- evidence reference when available
- rationale

Incident hooks must not include secret values.

## 15. Anti-Fake Success Rules

Platform integration must fail closed on fake success.

Blocking conditions:

- `result_status = succeeded` without production gate authorization
- `published_url` present in sandbox mode
- `platform_content_id` present in sandbox mode
- sandbox receipt treated as production receipt
- missing receipt treated as success
- pending treated as success
- eligibility treated as success
- dry-run treated as success
- platform error treated as success
- manually inserted URL or platform ID

Any fake success acceptance must produce `HOLD`.

## 16. Residual Monitoring

The following residuals must remain open after this plan:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

Sandbox integration may reduce only:

- platform payload shape uncertainty
- credential presence validation uncertainty
- rate-limit configuration uncertainty
- sandbox receipt schema uncertainty
- external timeout/error trace uncertainty

Sandbox integration must not reduce:

- production publish evidence residual
- real platform integration residual
- production result history residual
- post-publish metric residual
- attribution causality residual

## 17. Security And Privacy

Security requirements:

- no secrets in logs
- no secrets in JSONL
- no secrets in audit artifacts
- no raw token values in exceptions
- no platform account takeover scope
- least-privilege credential scope
- deterministic idempotency key
- bounded retries
- explicit timeout
- explicit user/account binding

Privacy requirements:

- no unnecessary personal data in metadata
- no platform user token persistence outside approved secret storage
- no account identifiers beyond governed account ID references

## 18. Controlled Integration Stages

Recommended future stages:

```json
[
  "platform_integration_gate_plan",
  "platform_integration_gate",
  "sandbox_adapter_implementation_plan",
  "sandbox_adapter_implementation_gate",
  "external_sandbox_evidence_collection",
  "external_sandbox_evidence_gate",
  "production_publish_candidate_plan",
  "production_publish_gate"
]
```

No stage authorizes real public publishing until the production publish gate explicitly approves it.

## 19. Gate Before Any Publish Real

A gate is mandatory before:

- platform API execution
- upload
- scheduler activation
- production receipt capture
- URL emission
- platform content ID emission
- public publish

The gate must validate:

- target platform configured explicitly
- sandbox mode active
- kill switch active and tested
- credentials present but not leaked
- rate limits configured
- upload contract complete
- metadata contract complete
- result evidence contract complete
- fake success impossible
- no production URL in sandbox
- no production platform content ID in sandbox
- Account Health `HOLD` still blocks
- QC non-publishable still blocks
- append-only lifecycle preserved
- residuals remain correctly classified

## 20. Failure Conditions

Immediate `HOLD` if:

- any real upload occurs
- any real publish occurs
- scheduler is invoked
- mixed platform modes are present
- implicit real provider binding appears without a separate approval artifact
- idempotency key is missing, random, unstable or untraceable
- production URL appears
- production platform content ID appears
- `result_evidence_is_production = true` appears in sandbox mode
- result evidence does not distinguish sandbox from production
- platform success is accepted without receipt evidence
- sandbox receipt is treated as production receipt
- Account Health `HOLD` is overridden
- QC non-publishable is overridden
- Strategy is used as publish permission
- Publisher becomes QC, Strategy or Attribution
- production residual is closed by sandbox evidence
- secret value appears in trace or logs
- kill switch is missing
- kill switch does not block publish attempt
- rate-limit policy is missing
- rate-limit disabled state can be interpreted as unlimited
- append-only lifecycle is violated

## 21. Exit Criteria

This plan is acceptable only if:

```json
{
  "initial_target_platform_defined": true,
  "sandbox_mode_required": true,
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "no_implicit_provider_binding": true,
  "real_publishing_authorized": false,
  "platform_api_execution_authorized": false,
  "credential_model_defined": true,
  "rate_limit_model_defined": true,
  "upload_contract_defined": true,
  "metadata_contract_defined": true,
  "result_evidence_contract_defined": true,
  "result_evidence_is_production_distinguished": true,
  "idempotency_key_deterministic": true,
  "kill_switch_required": true,
  "kill_switch_blocks_publish_attempt": true,
  "incident_hooks_defined": true,
  "fake_success_forbidden": true,
  "gate_required_before_external_side_effect": true,
  "production_residuals_remain_open": true
}
```

## 22. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_GATE_PLAN.md`

That artifact must define the gate that validates this platform integration plan before any implementation.

Real publishing remains unauthorized.

Platform API execution remains unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Production URL and production `platform_content_id` emission remain unauthorized.
