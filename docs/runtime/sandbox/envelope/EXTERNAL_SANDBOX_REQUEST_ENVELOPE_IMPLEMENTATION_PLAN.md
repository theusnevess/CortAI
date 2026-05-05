# EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_PLAN

## 1. Purpose

`EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_PLAN` defines the future implementation plan for the offline external sandbox request envelope.

This is a planning artifact only.

It does not implement the envelope, create code, create tests, create a runner, execute tests, call external services, call platform APIs, upload content, transfer media bytes, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, collect post-publish metrics, close production residuals, modify Publisher runtime behavior beyond future offline envelope construction, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The purpose is to define the smallest safe implementation slice before code exists.

Final principle:

> The external sandbox envelope is an inert intent and validation object. It must never become an executable request or transport payload.

## 2. Starting State

Canonical prior state:

```json
{
  "external_sandbox_request_envelope_gate": "GO_WITH_MONITORING",
  "scenarios": "38/38",
  "checklist": "48/48",
  "request_envelope_implemented": false,
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "external_call_authorized": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "media_bytes_included": false,
  "real_publishing_performed": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "production_residuals_closed": false
}
```

Required prior artifacts:

- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_PLAN.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_request_envelope_gate.py`
- `OUT/audit/external_sandbox_request_envelope_gate/final_verdict.json`
- `docs/runtime/sandbox/evidence/EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE.md`
- `OUT/audit/external_sandbox_evidence_collection_gate/final_verdict.json`

## 3. Scope

In scope for future implementation:

- offline envelope dataclasses
- deterministic envelope builder
- deterministic idempotency key builder
- metadata projection builder
- credential status projection
- kill switch projection
- rate-limit projection
- dependency reference validation
- forbidden-field scanner
- envelope validation result
- incident hook shape
- deterministic serialization helpers
- unit tests for offline behavior
- transport nullification checks

Out of scope:

- external request execution
- HTTP client
- SDK client
- endpoint configuration
- DNS/network behavior
- API key loading
- authorization header generation
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
- runtime integration with Orchestrator
- Publisher execution path changes
- QC changes
- Account Health changes
- Strategy changes
- Orchestrator changes
- core pipeline changes

## 4. Implementation Boundary

Future implementation must create only an inert envelope representation.

The implementation should use safer internal naming:

- preferred: `ExternalSandboxValidationEnvelope`
- acceptable: `ExternalSandboxIntentEnvelope`
- avoid for internal class names: `ExternalSandboxRequestEnvelope`

The external artifact name may remain `EXTERNAL_SANDBOX_REQUEST_ENVELOPE_*` for continuity with the existing governance chain, but the implementation must treat the object as intent and validation state, not as a request object.

The envelope may:

- represent validated refs
- represent metadata shape
- represent credential status
- represent kill switch status
- represent rate-limit status
- represent blocking reasons
- represent deterministic idempotency
- serialize to JSON
- emit local validation rationale

The envelope must not:

- include an endpoint
- include an HTTP method
- include request headers
- include authorization headers
- include body bytes intended for transport
- include `headers`
- include `body`
- include `url`
- include `method`
- include media bytes
- include upload URL
- include publish URL
- include scheduler ID
- include production receipt
- include `published_url`
- include production `platform_content_id`
- expose a `.send()`, `.execute()`, `.post()`, `.upload()`, `.publish()` or similar method

Failure to preserve this boundary is a blocker.

## 4.1 Transport Nullification Guarantee

Future implementation must make the envelope structurally incapable of being used directly as a transport payload.

Required:

- no HTTP-convention field names such as `headers`, `body`, `url`, `method`, `endpoint`, `host`, `path` or `query`
- no nested structure resembling request payload grouping
- no direct JSON-ready shape intended for transport reuse
- no helper that returns an HTTP-ready payload
- no helper named `to_request`, `as_request`, `to_payload`, `to_http`, `to_headers`, `to_body`, `send`, `execute`, `post`, `upload` or `publish`
- serialization must be explicitly audit serialization only
- any future transport transformation must require a separate artifact, separate implementation and separate gate

Required non-executable marker:

```json
{
  "execution_capability": "none",
  "transport_capability": "none",
  "non_transportable": true
}
```

The future gate must fail if the envelope can be reasonably reused as an HTTP payload without a separate transformation layer.

## 5. Proposed Future Files

Future implementation may create these files only after a separate implementation gate is accepted:

```text
backend/app/creative/agents/publisher/external_sandbox_validation_envelope.py
backend/app/creative/agents/publisher/external_sandbox_envelope_security.py
tests/sandbox/unit/test_external_sandbox_validation_envelope_unittest.py
```

This plan does not create those files.

Future implementation must remain additive.

It must not modify:

- `backend/app/creative/agents/publisher/sandbox_adapter.py`
- `backend/app/creative/agents/publisher/publish_lifecycle_writer.py`
- `backend/app/creative/agents/publisher/publish_trace.py`
- `backend/app/creative/agents/video_qc/`
- `backend/app/creative/agents/account_health/`
- `backend/app/creative/agents/strategy/`
- Orchestrator
- core pipeline

Any integration into runtime execution requires a later gate.

## 6. Required Constants

Future implementation must hard-code only the governed sandbox identifiers:

```json
{
  "ENVELOPE_VERSION": "external_sandbox_request_envelope_v1",
  "ENVELOPE_TYPE": "external_sandbox_validation_envelope",
  "TARGET_PLATFORM_ID": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "TARGET_MODE": "sandbox_external_dry_run",
  "METADATA_SHAPE_CLASS": "metadata_shape_only",
  "BOUNDARY_STATEMENT": "External sandbox validation envelope is non-executable and non-transportable."
}
```

Forbidden constants:

- real provider names
- production domains
- API base URLs
- upload URLs
- publish endpoints
- OAuth URLs
- scheduler endpoint names
- production visibility modes

## 7. Suggested Structures

Future implementation may define serializable frozen dataclasses or equivalent deterministic structures:

- `ExternalSandboxValidationEnvelopeInput`
- `ExternalSandboxMetadataProjection`
- `ExternalSandboxCredentialProjection`
- `ExternalSandboxKillSwitchProjection`
- `ExternalSandboxRateLimitProjection`
- `ExternalSandboxValidationEnvelope`
- `ExternalSandboxEnvelopeValidationResult`
- `ExternalSandboxEnvelopeIncidentHook`
- `ExternalSandboxValidationEnvelopeBuilder`

All structures must be:

- deterministic
- JSON serializable
- side-effect free
- free of secret values
- free of media bytes
- free of transport behavior

## 8. Envelope Input Contract

Future input must include refs and status fields only:

```json
{
  "run_id": "...",
  "content_id": "...",
  "artifact_manifest_ref": "...",
  "metadata_payload_ref": "...",
  "qc_trace_ref": "...",
  "account_health_trace_ref": "...",
  "strategy_ref": "...",
  "publish_eligibility_trace_ref": "...",
  "metadata": {},
  "qc_status": "APPROVE | HOLD | REJECT | UNKNOWN",
  "qc_publishable": true,
  "account_health_decision": "SAFE | CAUTION | HOLD | UNKNOWN",
  "credential_status": "present | missing | invalid_shape | not_checked",
  "kill_switch_status": {},
  "rate_limit_status": {}
}
```

Input must not include:

- endpoint
- URL
- platform account token
- authorization header
- media bytes
- binary file path intended for upload
- scheduler ID
- production receipt
- post-publish metrics

## 9. Envelope Output Contract

Future envelope output must match:

```json
{
  "envelope_version": "external_sandbox_request_envelope_v1",
  "envelope_type": "external_sandbox_validation_envelope",
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
  "metadata_shape_class": "metadata_shape_only",
  "execution_capability": "none",
  "transport_capability": "none",
  "non_transportable": true,
  "media_bytes_included": false,
  "upload_endpoint_requested": false,
  "publish_endpoint_requested": false,
  "public_visibility_requested": false,
  "external_call_authorized": false,
  "platform_api_execution_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "published_url": null,
  "platform_content_id": null,
  "boundary_statement": "External sandbox validation envelope is non-executable and non-transportable."
}
```

Every output must keep:

- `media_bytes_included = false`
- `upload_endpoint_requested = false`
- `publish_endpoint_requested = false`
- `public_visibility_requested = false`
- `external_call_authorized = false`
- `platform_api_execution_authorized = false`
- `upload_authorized = false`
- `scheduler_authorized = false`
- `real_publish_authorized = false`
- `published_url = null`
- `platform_content_id = null`
- `execution_capability = none`
- `transport_capability = none`
- `non_transportable = true`

## 10. Metadata Projection

Future metadata projection may include only:

```json
{
  "title_present": true,
  "description_present": true,
  "tags_present": true,
  "language_present": true,
  "visibility_mode": "sandbox_only",
  "account_id_ref": "...",
  "content_id": "...",
  "runtime_policy_ref": "...",
  "metadata_trace_ref": "...",
  "metadata_shape_valid": true
}
```

It must not copy:

- full description if unsafe
- secret values
- tokens
- authorization headers
- production URLs
- production `platform_content_id`
- expected performance claims
- forecasts
- attribution claims

Invalid metadata must create `blocking_reasons`, not silent fallback.

## 11. Credential Projection

Future credential projection may include:

```json
{
  "credential_status": "present | missing | invalid_shape | not_checked",
  "credential_source": "environment_or_secret_manager",
  "secret_values_logged": false,
  "secret_values_persisted": false,
  "secret_scope_class": "sandbox_validation_only"
}
```

Rules:

- never read secret values
- never store secret values
- never serialize secret values
- never include authorization headers
- never include exception text containing credential values
- missing credentials block envelope eligibility

## 12. Kill Switch Projection

Future kill switch projection must preserve:

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
- blocked envelope still serializes
- blocked envelope does not authorize external call
- kill switch cannot fail open

## 13. Rate-Limit Projection

Future rate-limit projection must preserve:

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

- `null` means disabled/not authorized, not unlimited
- upload requests remain disabled
- publish requests remain disabled
- sandbox validation remains unauthorized until a later gate
- rate-limit exceeded blocks envelope eligibility

## 14. Dependency Blocks

Future builder must block envelope eligibility when:

- `qc_trace_ref` missing
- QC status is `HOLD`
- QC status is `REJECT`
- QC `publishable=false`
- Account Health decision is `HOLD`
- `artifact_manifest_ref` missing
- `metadata_payload_ref` missing
- `strategy_ref` missing
- `publish_eligibility_trace_ref` missing
- credential status is `missing`
- credential status is `invalid_shape`
- kill switch is active
- kill switch is missing
- mixed mode appears
- implicit provider binding appears

Every block must appear in:

- `blocking_reasons`
- `rationale`
- incident hooks where applicable

No blocked envelope may be represented as success.

## 15. Idempotency Key

Future builder must generate a deterministic idempotency key from:

- `run_id`
- `content_id`
- `artifact_manifest_ref`
- `target_platform_id`
- `target_mode`

Required behavior:

- same input produces same key
- changed input produces changed key
- key contains no secret material
- key contains no raw credentials
- key contains no URL
- key contains no platform content ID
- key is stable across replay

Required sandbox-only namespace:

```text
external_sandbox_envelope_v1:
```

Randomness is forbidden.

The idempotency key namespace must be explicitly sandbox-scoped and must not be reusable for production publishing flows.

Future production publishing flows must use a different namespace approved by a separate production gate.

## 16. Forbidden Field Detection

Future implementation must include deterministic detection for:

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

If found:

- `forbidden_field_detected = true`
- envelope eligibility is blocked
- incident hook emitted
- field value must not be copied into output

## 17. Validation Result

Future validation result must be serializable:

```json
{
  "envelope_valid": true,
  "eligible_for_future_external_sandbox_validation": false,
  "blocking_reasons": [],
  "warnings": [],
  "secret_leakage_detected": false,
  "forbidden_field_detected": false,
  "external_call_authorized": false,
  "platform_api_execution_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "execution_capability": "none",
  "transport_capability": "none",
  "non_transportable": true,
  "rationale": []
}
```

Rules:

- `envelope_valid=true` means schema valid only
- valid envelope does not authorize external execution
- future eligibility does not authorize external execution
- warnings do not become success
- blocked envelopes remain visible
- validation result remains non-executable
- validation result remains non-transportable

## 18. Incident Hooks

Future implementation must support incident hook shapes for:

- `EXTERNAL_SANDBOX_ENVELOPE_SECRET_LEAKAGE_ATTEMPT`
- `EXTERNAL_SANDBOX_ENVELOPE_FORBIDDEN_FIELD`
- `EXTERNAL_SANDBOX_ENVELOPE_MIXED_MODE`
- `EXTERNAL_SANDBOX_ENVELOPE_PROVIDER_BINDING`
- `EXTERNAL_SANDBOX_ENVELOPE_KILL_SWITCH_BLOCK`
- `EXTERNAL_SANDBOX_ENVELOPE_CREDENTIALS_MISSING`
- `ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH`
- `QC_NON_PUBLISHABLE_BLOCKED_PUBLISH`

Incident hooks must include:

- incident type
- severity
- run ID
- content ID
- target platform
- target mode
- rationale

Incident hooks must not include:

- secrets
- tokens
- authorization headers
- production URLs
- platform content IDs

## 19. Serialization Rules

Future implementation must provide deterministic serialization:

- stable key ordering where practical
- JSON serializable primitives only
- audit serialization only
- serialized output explicitly marks `execution_capability = none`
- serialized output explicitly marks `transport_capability = none`
- serialized output explicitly marks `non_transportable = true`
- no datetime-generated nondeterminism unless supplied as input
- no object memory addresses
- no random IDs
- no environment-dependent fields except credential presence/status
- no secret values
- no HTTP-ready payload grouping

Same input must produce same envelope and same validation result.

## 20. Testing Requirements

Future tests must cover at minimum:

1. envelope shape contains required fields
2. target platform exact
3. target mode exact
4. external call remains unauthorized
5. platform API remains uncalled
6. upload remains unauthorized
7. scheduler remains unauthorized
8. real publish remains unauthorized
9. media bytes are forbidden
10. public visibility is forbidden
11. production URL is forbidden
12. `platform_content_id` is forbidden
13. metadata projection is bounded
14. credential projection status-only
15. secret-like fields are detected and redacted
16. kill switch active blocks eligibility
17. kill switch missing blocks eligibility
18. disabled rate limit is not unlimited
19. QC `HOLD` blocks
20. QC `REJECT` blocks
21. QC `publishable=false` blocks
22. Account Health `HOLD` blocks
23. missing dependency refs block
24. idempotency key deterministic
25. changed input changes idempotency key
26. envelope validity does not imply external success
27. future eligibility does not imply external success
28. forbidden field detection is deterministic
29. incident hooks do not include secrets
30. serialization deterministic replay
31. envelope uses validation/intent naming, not request execution naming
32. transport nullification markers are present
33. no HTTP-convention fields exist
34. no executable helper names exist
35. idempotency namespace is `external_sandbox_envelope_v1:`

## 21. Future Implementation Gate

Before code is written, create:

- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE.md`

After code is written, create and execute:

- `tests/gates/sandbox/run_external_sandbox_request_envelope_implementation_gate.py`

Expected future audit artifacts:

- `OUT/audit/external_sandbox_request_envelope_implementation_gate/final_verdict.json`
- `OUT/audit/external_sandbox_request_envelope_implementation_gate/checklist_results.json`
- `OUT/audit/external_sandbox_request_envelope_implementation_gate/scenario_outputs.json`
- `OUT/audit/external_sandbox_request_envelope_implementation_gate/metrics.json`
- `OUT/audit/external_sandbox_request_envelope_implementation_gate/security_review.json`
- `OUT/audit/external_sandbox_request_envelope_implementation_gate/contract_review.json`
- `OUT/audit/external_sandbox_request_envelope_implementation_gate/residual_monitoring_review.json`
- `OUT/audit/external_sandbox_request_envelope_implementation_gate/side_effect_review.json`
- `OUT/audit/external_sandbox_request_envelope_implementation_gate/transport_nullification_review.json`

## 22. Residual Monitoring

These residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

Envelope implementation may reduce only:

- envelope schema uncertainty
- forbidden-field implementation uncertainty
- credential projection implementation uncertainty
- idempotency projection implementation uncertainty
- dependency reference projection implementation uncertainty

It must not reduce:

- production publish evidence residual
- real platform integration residual
- production result history residual
- external sandbox execution residual
- post-publish metric residual
- attribution causality residual

## 23. Failure Conditions

Immediate `HOLD` if future implementation:

- executes external call
- imports or initializes HTTP client
- imports or initializes platform SDK
- defines endpoint URL
- defines `headers`, `body`, `url`, `method`, `endpoint`, `host`, `path` or `query`
- defines upload URL
- defines publish endpoint
- exposes request conversion helper
- exposes send/execute/post/upload/publish helper
- creates authorization headers
- reads raw secrets
- serializes raw secrets
- uploads content
- includes media bytes
- invokes scheduler
- publishes content
- emits production URL
- emits production `platform_content_id`
- allows public visibility
- allows mixed modes
- allows implicit provider binding
- treats envelope validity as external success
- treats envelope eligibility as publish success
- closes production residuals
- modifies QC, Account Health, Strategy, Orchestrator or core pipeline

## 24. Exit Criteria

This implementation plan is acceptable only if:

```json
{
  "implementation_planned": true,
  "implementation_created": false,
  "offline_only": true,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "transport_payload_allowed": false,
  "execution_capability": "none",
  "transport_capability": "none",
  "non_transportable": true,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "media_bytes_included": false,
  "secrets_presence_only": true,
  "idempotency_key_deterministic": true,
  "production_residuals_remain_open": true,
  "boundary_preserved": true
}
```

## 25. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE.md`

That gate must freeze implementation acceptance criteria before any envelope code is created.

External calls remain unauthorized.

Platform API execution remains unauthorized.

HTTP clients and platform SDKs remain unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Real publishing remains unauthorized.

Production URL and production `platform_content_id` emission remain unauthorized.
