# EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_PLAN

## 1. Purpose

`EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_PLAN` defines the boundary conditions for a future external sandbox call path.

This is a planning artifact only.

It does not implement an external call, create code, create tests, create a runner, execute tests, create HTTP clients, create SDK clients, configure endpoints, access DNS/network, call platform APIs, upload content, transfer media bytes, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, create receipts, collect post-publish metrics, close production residuals, modify Publisher runtime execution, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The purpose is to define what must be true before any future sandbox external call can even be considered.

Final principle:

> A future external sandbox call may only validate a bounded sandbox interaction. It must not become upload, scheduling, publishing or production evidence.

## 2. Starting State

Canonical current state:

```json
{
  "publisher_maturity": "PRE_EXECUTION_BINDING_GATED",
  "controlled_binding": "GATED",
  "binding_active": false,
  "provider_binding_status": "planned_not_active",
  "provider_identity_class": "abstract_sandbox_target",
  "external_execution_authorized": false,
  "real_publishing_authorized": false,
  "platform_integration_authorized": false,
  "production_residuals_open": true
}
```

Required prior artifacts:

- `docs/runtime/sandbox/controlled-binding/EXTERNAL_SANDBOX_CONTROLLED_BINDING_PLAN.md`
- `docs/runtime/sandbox/controlled-binding/EXTERNAL_SANDBOX_CONTROLLED_BINDING_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_controlled_binding_gate.py`
- `OUT/audit/external_sandbox_controlled_binding_gate/final_verdict.json`
- `docs/runtime/sandbox/controlled-binding/EXTERNAL_SANDBOX_CONTROLLED_BINDING_REVIEW.md`

Accepted controlled binding gate state:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "binding_active": false,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "network_access_allowed": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "url_emitted": false,
  "platform_content_id_emitted": false,
  "receipt_emitted": false,
  "credential_value_accessed": false,
  "production_residuals_closed": false
}
```

## 3. Scope

In scope:

- external call boundary definition
- future call authority model
- future endpoint governance requirements
- future HTTP/SDK prohibition until separate gate
- future request shape constraints
- future credential handling boundaries
- future kill switch dependency
- future rate-limit dependency
- future timeout and retry boundaries
- future sandbox result evidence classification
- future incident hooks
- future anti-fake-success rules
- residual monitoring constraints
- required next gate before implementation

Out of scope:

- external call implementation
- HTTP client implementation
- SDK client implementation
- endpoint configuration
- DNS/network access
- API call execution
- upload
- media byte transfer
- scheduler
- real publishing
- production URL
- production `platform_content_id`
- receipt generation
- post-publish metrics
- attribution causality
- runtime integration
- core pipeline changes

## 4. External Call Authority Model

Current authority remains:

```json
{
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "dns_network_access_allowed": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false
}
```

Future authorization, if ever granted, must be narrower than publish authorization.

A future external sandbox call may only become:

```json
{
  "capability": "sandbox_validation_call",
  "production_evidence": false,
  "upload": false,
  "scheduler": false,
  "publish": false,
  "public_visibility": false
}
```

Any future capability wider than `sandbox_validation_call` requires a separate plan, gate and explicit approval.

## 5. Boundary Between Validation And Execution

Future external sandbox validation must not be confused with production execution.

Allowed future semantics:

- validate sandbox endpoint reachability if later authorized
- validate payload schema if later authorized
- validate credential status against sandbox if later authorized
- validate bounded sandbox error handling if later authorized
- record sandbox-only response evidence if later authorized

Forbidden semantics:

- upload media
- publish content
- schedule publication
- create public visibility
- emit production URL
- emit production `platform_content_id`
- create production receipt
- collect post-publish metrics
- close production residuals
- treat sandbox validation as publish success

## 6. Future Endpoint Boundary

No endpoint is authorized by this plan.

Before any endpoint exists, a future gate must validate:

```json
{
  "endpoint_explicitly_governed": true,
  "endpoint_mode": "sandbox_only",
  "endpoint_not_production": true,
  "endpoint_not_upload": true,
  "endpoint_not_publish": true,
  "endpoint_not_scheduler": true,
  "dns_access_explicitly_gated": true,
  "network_access_explicitly_gated": true
}
```

Forbidden without a later gate:

- endpoint constants
- base URLs
- upload URLs
- publish URLs
- callback URLs
- webhook URLs
- DNS probes
- socket access
- HTTP method definitions
- request headers
- authorization headers

## 7. Future Client Boundary

No HTTP client or SDK is authorized by this plan.

Before any client exists, a future gate must validate:

- client is sandbox-only
- client cannot upload
- client cannot publish
- client cannot schedule
- client cannot emit production identity
- client cannot log secret values
- client has deterministic timeout behavior
- client has bounded retry behavior
- client is blocked by kill switch
- client is blocked by rate limit policy
- client is blocked by QC non-publishable states
- client is blocked by Account Health `HOLD`

Forbidden without a later gate:

- `requests`
- `httpx`
- `aiohttp`
- `urllib.request`
- `urllib3`
- `socket`
- platform SDKs
- SDK auto-retry behavior
- implicit provider binding

## 8. Future Request Shape Boundary

The existing validation envelope and controlled binding are not transport payloads.

A future request shape, if ever authorized, must be a separate object with a separate gate.

It must not reuse:

- `ExternalSandboxValidationEnvelope` as a transport object
- `ExternalSandboxControlledBinding` as a transport object
- audit serialization as request serialization
- lifecycle trace as request body

Before any request shape exists, a future gate must prove:

```json
{
  "request_shape_separate_from_audit_objects": true,
  "transport_payload_explicitly_gated": true,
  "no_media_bytes": true,
  "no_upload_field": true,
  "no_publish_field": true,
  "no_scheduler_field": true,
  "no_production_identity_field": true
}
```

## 9. Credential Boundary

Current credential handling remains status-only.

This plan does not authorize:

- reading raw secret values
- serializing raw secret values
- generating authorization headers
- refreshing tokens
- storing tokens
- logging token-derived errors
- passing credentials to an external client

Before future credential use exists, a separate gate must validate:

- secret source is approved
- secret scope is sandbox-only
- secret values are never written to audit artifacts
- secret values are never written to logs
- token refresh is not enabled unless separately gated
- authorization header generation is bounded and not persisted
- missing credentials fail closed
- invalid credentials fail closed

## 10. Kill Switch Boundary

The kill switch remains mandatory.

Future external sandbox call authorization is invalid unless:

```json
{
  "kill_switch_required": true,
  "default_safe_state": "blocked",
  "blocks_external_calls": true,
  "blocks_upload": true,
  "blocks_scheduler": true,
  "blocks_publish_attempt": true,
  "missing_kill_switch_blocks": true,
  "active_kill_switch_blocks": true
}
```

The kill switch must block before:

- endpoint resolution
- client initialization
- credential use
- request construction
- network access
- retry scheduling

## 11. Rate-Limit Boundary

Rate-limit policy remains disabled and non-unlimited.

Current state:

```json
{
  "sandbox_validation_requests_allowed": false,
  "upload_requests_allowed": false,
  "publish_requests_allowed": false,
  "max_sandbox_validation_requests_per_minute": null,
  "max_upload_requests_per_hour": null,
  "max_publish_requests_per_day": null,
  "burst_allowed": false
}
```

`null` means disabled/not authorized, not unlimited.

Before any future sandbox validation request is allowed, a separate gate must define:

- maximum requests per minute
- maximum retry count
- deterministic backoff
- timeout ceiling
- incident hook on limit exhaustion
- fail-closed behavior

Upload and publish requests must remain disabled.

## 12. Timeout And Retry Boundary

Future external sandbox call behavior must be deterministic and bounded.

Before implementation, a later gate must define:

```json
{
  "timeout_required": true,
  "timeout_value_bounded": true,
  "retry_policy_required": true,
  "max_retry_count_bounded": true,
  "backoff_deterministic": true,
  "no_infinite_retry": true,
  "timeout_is_failure_or_pending": true,
  "timeout_is_not_success": true
}
```

Retries must not:

- bypass rate limits
- bypass kill switch
- duplicate publish attempts
- create public visibility
- hide failures
- rewrite lifecycle evidence

## 13. Result Evidence Boundary

No receipt is authorized by this plan.

Future sandbox result evidence, if later authorized, must distinguish:

```json
{
  "result_evidence_available": true,
  "result_evidence_is_production": false,
  "result_evidence_type": "sandbox_validation_response",
  "published_url": null,
  "platform_content_id": null,
  "production_receipt": null
}
```

Forbidden:

- production receipt in sandbox mode
- sandbox evidence treated as production evidence
- missing evidence treated as success
- pending treated as success
- eligibility treated as success
- external call completion treated as publishing
- URL or platform ID emission

## 14. Lifecycle Evidence Boundary

Future external sandbox calls must remain append-only if later authorized.

Required future lifecycle semantics:

- call planned
- call blocked
- call skipped
- call attempted
- call timed out
- call failed
- call pending
- call sandbox validated

Forbidden lifecycle semantics before production gate:

- published
- succeeded
- production published
- public URL emitted
- platform content ID emitted
- production receipt captured

Lifecycle evidence must never rewrite prior events.

## 15. Incident Hooks

Future boundary must define incident hooks for:

- `EXTERNAL_SANDBOX_CALL_NOT_AUTHORIZED`
- `EXTERNAL_SANDBOX_ENDPOINT_NOT_AUTHORIZED`
- `EXTERNAL_SANDBOX_HTTP_CLIENT_NOT_AUTHORIZED`
- `EXTERNAL_SANDBOX_SDK_NOT_AUTHORIZED`
- `EXTERNAL_SANDBOX_DNS_NETWORK_NOT_AUTHORIZED`
- `EXTERNAL_SANDBOX_CREDENTIAL_USE_NOT_AUTHORIZED`
- `EXTERNAL_SANDBOX_KILL_SWITCH_BLOCK`
- `EXTERNAL_SANDBOX_RATE_LIMIT_BLOCK`
- `EXTERNAL_SANDBOX_TIMEOUT`
- `EXTERNAL_SANDBOX_RESPONSE_SCHEMA_INVALID`
- `EXTERNAL_SANDBOX_FAKE_SUCCESS_ATTEMPT`
- `EXTERNAL_SANDBOX_FAKE_URL_OR_PLATFORM_ID_ATTEMPT`
- `ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH`
- `QC_NON_PUBLISHABLE_BLOCKED_PUBLISH`

Incident hooks must not include:

- secret values
- authorization headers
- endpoint secrets
- production URLs
- production platform IDs
- receipt values that imply production success

## 16. Anti-Fake-Success Rules

Future sandbox external call handling must fail closed on:

- `published_url` present
- `platform_content_id` present
- production receipt present
- `result_evidence_is_production = true`
- result status `succeeded`
- result status `published`
- result status `production_published`
- missing evidence treated as success
- pending treated as success
- timeout treated as success
- sandbox validation treated as publish success
- eligibility treated as success

Any fake success acceptance must produce `HOLD`.

## 17. Boundary Preconditions For Future Gate

Before implementation of any external call boundary code, create:

```text
docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_GATE.md
```

That gate must validate:

- current controlled binding gate passed
- production residuals remain open
- no external call currently exists
- no HTTP client currently exists
- no SDK currently exists
- no endpoint currently exists
- no DNS/network access currently exists
- no upload currently exists
- no scheduler currently exists
- no publishing currently exists
- boundary conditions are complete
- fake success rules are explicit
- lifecycle semantics are append-only
- kill switch rules are fail-closed
- rate-limit rules are non-unlimited
- credential rules are status-only until separately gated

## 18. Residual Monitoring

Required production residuals remain open:

```json
[
  "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
  "PLATFORM_INTEGRATION_NOT_ENABLED",
  "PUBLISH_RESULT_HISTORY_STILL_SHORT"
]
```

This plan may reduce only:

- external call boundary ambiguity
- client/endpoint authorization ambiguity
- result evidence boundary ambiguity
- fake success boundary ambiguity

It must not reduce:

- production publish evidence residual
- platform integration residual
- production result history residual
- external sandbox execution residual
- post-publish metric residual
- attribution causality residual

## 19. Failure Conditions

Immediate `HOLD` if any future step:

- creates an HTTP client without a gate
- creates an SDK client without a gate
- defines an endpoint without a gate
- accesses DNS/network without a gate
- constructs a transport payload from audit objects
- reads credential values without a gate
- generates authorization headers without a gate
- uploads content
- schedules publication
- publishes content
- emits URL
- emits `platform_content_id`
- emits receipt
- treats sandbox validation as publish success
- treats missing/pending/timeout evidence as success
- bypasses Account Health `HOLD`
- bypasses QC non-publishable state
- fails open on missing kill switch
- treats disabled rate limit as unlimited
- closes production residuals

## 20. Exit Criteria

This plan is acceptable only if:

```json
{
  "future_external_call_boundary_defined": true,
  "external_call_implemented": false,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "dns_network_access_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "url_emission_authorized": false,
  "platform_content_id_emission_authorized": false,
  "receipt_authorized": false,
  "credential_value_access_authorized": false,
  "kill_switch_fail_closed_required": true,
  "rate_limit_non_unlimited_required": true,
  "production_residuals_remain_open": true
}
```

## 21. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

```text
docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_GATE.md
```

That artifact must freeze the gate before any external call boundary implementation.

Still forbidden:

- external call
- platform API
- HTTP client
- SDK client
- endpoint
- DNS/network access
- API call
- upload
- scheduler
- real publishing
- URL
- `platform_content_id`
- receipt
- post-publish metrics
- production residual closure
