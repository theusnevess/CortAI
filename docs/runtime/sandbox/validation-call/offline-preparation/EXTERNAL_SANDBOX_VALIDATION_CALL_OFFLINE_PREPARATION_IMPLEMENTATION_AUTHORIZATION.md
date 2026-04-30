# EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_AUTHORIZATION

## 1. Purpose

`EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_AUTHORIZATION` authorizes a narrowly scoped offline/preparation-only implementation slice for sandbox validation call preparation.

This is an implementation authorization artifact for the allowlisted files only.

It does not authorize external calls, runtime integration, HTTP clients, platform SDKs, endpoints, DNS/network access, API calls, credential value access, request transformation, transport payload generation, upload, scheduling, publishing, production URLs, `platform_content_id`, receipts or production residual closure.

Core rule:

> Implementation is authorized only for inert local preparation structures. Execution remains unauthorized.

## 2. Reviewed Basis

This authorization is based on:

- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_PLAN.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_validation_call_offline_preparation_implementation_gate.py`
- `OUT/audit/external_sandbox_validation_call_offline_preparation_implementation_gate/final_verdict.json`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE_REVIEW.md`

The gate result was:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "allowlist_exact": true,
  "allowlist_active": false,
  "implementation_authorized": false,
  "tests_authorized": false,
  "external_call_authorized": false,
  "runtime_integration_authorized": false,
  "gate_required_before_code": true,
  "production_residuals_remain_open": true,
  "scenario_pass_count": "32/32",
  "checklist_pass_count": "61/61",
  "critical_failures": 0,
  "blocking_failures": []
}
```

## 3. Authorization Decision

The allowlist is now activated for offline/preparation-only implementation:

```json
{
  "allowlist_exact": true,
  "allowlist_active": true,
  "implementation_authorized": true,
  "tests_authorized": true,
  "authorization_scope": "OFFLINE_PREPARATION_ONLY",
  "external_call_authorized": false,
  "runtime_integration_authorized": false,
  "http_sdk_endpoint_dns_api_authorized": false,
  "credential_value_access_authorized": false,
  "request_transformation_authorized": false,
  "transport_payload_authorized": false,
  "upload_scheduler_publish_authorized": false,
  "production_residuals_remain_open": true
}
```

This is not permission to implement any external execution surface.

## 4. Active Allowlist

Only these files may be created or modified under this authorization:

```text
backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation.py
backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation_security.py
tests/sandbox/unit/test_external_sandbox_validation_call_preparation_unittest.py
```

No other files are authorized.

The implementation must be additive.

The implementation must not modify Publisher runtime execution paths.

The implementation must not modify QC, Account Health, Strategy, Orchestrator, Attribution, Experiment or core pipeline.

## 5. Authorized Implementation Scope

The implementation may include only:

- inert local dataclasses or equivalent structures
- deterministic local builders
- dependency reference validation
- credential status projection, without reading values
- kill switch status projection
- rate limit status projection
- non-authorization fields
- local blocking reasons
- local warnings
- incident hook shapes
- deterministic serialization helpers
- forbidden-field scanner
- unit tests for the offline structures

The implementation must remain:

```json
{
  "offline_only": true,
  "preparation_only": true,
  "non_transport": true,
  "non_client": true,
  "non_endpoint": true,
  "non_network": true,
  "non_executing": true,
  "non_runtime_integrated": true,
  "credential_values_inaccessible": true
}
```

## 6. Explicit Non-Authorization Matrix

The following remain explicitly false:

```json
{
  "external_call_authorized": false,
  "runtime_integration_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "dns_network_allowed": false,
  "api_call_allowed": false,
  "credential_value_access_authorized": false,
  "request_transformation_authorized": false,
  "transport_payload_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "published_url_allowed": false,
  "platform_content_id_allowed": false,
  "receipt_allowed": false,
  "production_residual_closure_authorized": false
}
```

## 7. Forbidden Surface

The implementation must not include:

- `requests`
- `httpx`
- `aiohttp`
- `urllib.request`
- `urllib3`
- `socket`
- DNS libraries
- platform SDK imports
- endpoint constants
- base URL constants
- HTTP method constants
- request headers
- authorization headers
- executable request bodies
- upload helpers
- scheduler helpers
- publish helpers
- receipt generation
- production URL generation
- `platform_content_id` generation
- credential value reads
- environment secret value reads
- request transformation functions
- transport payload serializers
- runtime integration hooks

## 8. Required Semantics

The implementation must preserve these meanings:

- `preparation_complete=true` does not authorize execution.
- `eligible_for_future_sandbox_validation_review=true` does not authorize execution.
- `credential_status=present` does not mean credential value was read.
- blocked preparation remains visible.
- warnings never become success.
- incident hooks must not include secrets.
- successful local validation is not a platform result.
- no production evidence is created.

## 9. Required Tests

The authorized test file must cover:

- exact target platform
- exact target mode
- deterministic serialization
- same input produces same output
- no external call authorization
- no runtime integration authorization
- no request transformation authorization
- no transport payload authorization
- no credential value access authorization
- forbidden field detection
- secret-like field rejection
- endpoint-like field rejection
- URL-like field rejection
- media byte field rejection
- receipt field rejection
- production URL field rejection
- platform content ID field rejection
- kill switch blocking
- missing dependency refs
- QC non-publishable blocking
- Account Health `HOLD` blocking
- preparation complete does not authorize execution
- future eligibility does not authorize execution
- incident hooks contain no secrets

## 10. Residual Monitoring

The following residuals remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`
- `EXTERNAL_CALL_NOT_IMPLEMENTED`
- `EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED`

This authorization does not close production residuals.

It authorizes only local preparation implementation.

## 11. Failure Conditions

Implementation must stop and be treated as `HOLD` if it:

- modifies files outside the active allowlist
- imports HTTP clients
- imports platform SDKs
- defines endpoints
- uses DNS/network access
- reads credential values
- creates request transformations
- creates transport payloads
- authorizes external calls
- integrates with runtime execution
- creates upload behavior
- creates scheduler behavior
- creates publish behavior
- emits production URLs
- emits `platform_content_id`
- emits receipts
- closes production residuals
- modifies QC
- modifies Account Health
- modifies Strategy
- modifies Orchestrator
- modifies Attribution
- modifies Experiment
- modifies core pipeline

## 12. Required Follow-Up Gate

After implementation, create and execute:

- `tests/gates/sandbox/run_external_sandbox_validation_call_offline_preparation_implementation_acceptance_gate.py`

That gate must validate:

- exact file changes
- no forbidden imports
- no endpoint/DNS/network/API surface
- no credential value reads
- no request transformation
- no transport payload
- no runtime integration
- deterministic behavior
- unit test pass
- residuals remain open

## 13. Final State

```json
{
  "offline_preparation_implementation_authorization": "AUTHORIZED_WITH_MONITORING",
  "allowlist_exact": true,
  "allowlist_active": true,
  "implementation_authorized": true,
  "tests_authorized": true,
  "authorization_scope": "OFFLINE_PREPARATION_ONLY",
  "external_call_authorized": false,
  "runtime_integration_authorized": false,
  "http_sdk_endpoint_dns_api_authorized": false,
  "credential_value_access_authorized": false,
  "request_transformation_authorized": false,
  "transport_payload_authorized": false,
  "upload_scheduler_publish_authorized": false,
  "production_residuals_remain_open": true
}
```

## 14. Final Principle

This authorization opens the smallest possible code slice.

It authorizes local preparation only.

It does not authorize external execution.
