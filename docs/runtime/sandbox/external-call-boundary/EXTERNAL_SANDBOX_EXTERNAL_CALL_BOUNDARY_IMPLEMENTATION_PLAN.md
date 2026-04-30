# EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_PLAN

## 1. Purpose

`EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_PLAN` defines the future offline/pre-execution implementation slice for an external sandbox external call boundary marker.

This is a planning artifact only.

It does not create code, create tests, create a runner, execute tests, implement external calls, create HTTP clients, create SDK clients, configure endpoints, access DNS/network, call platform APIs, upload content, transfer media bytes, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, create receipts, collect post-publish metrics, close production residuals, modify Publisher runtime execution, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The purpose is to define a minimal inert implementation slice that can represent and verify the absence of external call capability.

Final principle:

> The boundary implementation must be a guardrail marker, not a transport layer.

## 2. Starting State

Canonical current state:

```json
{
  "publisher_maturity": "EXTERNAL_CALL_BOUNDARY_GATED",
  "external_call_detected": false,
  "http_client_detected": false,
  "sdk_detected": false,
  "endpoint_detected": false,
  "dns_network_detected": false,
  "upload_detected": false,
  "scheduler_detected": false,
  "publish_detected": false,
  "url_detected": false,
  "platform_content_id_detected": false,
  "receipt_detected": false,
  "external_execution_authorized": false,
  "real_publishing_authorized": false,
  "production_residuals_open": true
}
```

Required prior artifacts:

- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_PLAN.md`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_external_call_boundary_gate.py`
- `OUT/audit/external_sandbox_external_call_boundary_gate/final_verdict.json`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_REVIEW.md`

## 3. Scope

In scope for future implementation:

- inert boundary marker dataclass or equivalent
- external call prohibition snapshot
- endpoint prohibition snapshot
- client prohibition snapshot
- credential-use prohibition snapshot
- kill switch requirement snapshot
- rate-limit requirement snapshot
- result-evidence prohibition snapshot
- anti-fake-success rule snapshot
- deterministic validation result
- incident hook shape for blocked future external call attempts
- deterministic serialization
- unit tests for offline-only behavior

Out of scope:

- external call implementation
- HTTP client
- SDK client
- endpoint
- DNS/network access
- API call
- request execution
- request transformation
- upload
- media byte transfer
- scheduler
- publish
- URL emission
- `platform_content_id` emission
- receipt creation
- post-publish metrics
- runtime integration
- core pipeline changes

## 4. Proposed Future Files

Future implementation may create only:

```text
backend/app/creative/agents/publisher/external_sandbox_external_call_boundary.py
tests/sandbox/unit/test_external_sandbox_external_call_boundary_unittest.py
```

This plan does not create those files.

Future implementation must be additive.

It must not modify:

- `backend/app/creative/agents/publisher/sandbox_adapter.py`
- `backend/app/creative/agents/publisher/external_sandbox_controlled_binding.py`
- `backend/app/creative/agents/publisher/external_sandbox_validation_envelope.py`
- `backend/app/creative/agents/publisher/publish_lifecycle_writer.py`
- `backend/app/creative/agents/publisher/publish_trace.py`
- QC
- Account Health
- Strategy
- Orchestrator
- core pipeline

## 5. Required Constants

Future implementation must use only inert boundary identifiers:

```json
{
  "BOUNDARY_VERSION": "external_sandbox_external_call_boundary_v1",
  "BOUNDARY_TYPE": "pre_execution_external_call_boundary",
  "TARGET_PLATFORM_ID": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "TARGET_MODE": "sandbox_external_dry_run",
  "BOUNDARY_STATE": "external_call_absent",
  "BOUNDARY_STATEMENT": "External sandbox external call boundary is a non-executing guard contract."
}
```

Forbidden constants:

- endpoint values
- base URLs
- upload URLs
- publish URLs
- callback URLs
- webhook URLs
- HTTP methods
- authorization header names
- API key names containing real secret values
- real provider names
- production platform names

## 6. Suggested Structures

Future implementation may define frozen serializable structures such as:

- `ExternalSandboxExternalCallBoundaryInput`
- `ExternalSandboxExternalCallCapabilitySnapshot`
- `ExternalSandboxExternalCallDependencySnapshot`
- `ExternalSandboxExternalCallEvidenceBoundary`
- `ExternalSandboxExternalCallBoundaryValidation`
- `ExternalSandboxExternalCallBoundaryIncidentHook`
- `ExternalSandboxExternalCallBoundary`
- `ExternalSandboxExternalCallBoundaryBuilder`

All structures must be:

- deterministic
- JSON serializable
- side-effect free
- non-executing
- non-transportable
- free of secrets
- free of endpoints
- free of media bytes

## 7. Required Output Shape

Future boundary output must include at least:

```json
{
  "boundary_version": "external_sandbox_external_call_boundary_v1",
  "boundary_type": "pre_execution_external_call_boundary",
  "boundary_state": "external_call_absent",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "external_call_implemented": false,
  "external_call_authorized": false,
  "http_client_present": false,
  "sdk_present": false,
  "endpoint_present": false,
  "dns_network_present": false,
  "api_call_present": false,
  "request_transformation_present": false,
  "upload_present": false,
  "scheduler_present": false,
  "publish_present": false,
  "url_present": false,
  "platform_content_id_present": false,
  "receipt_present": false,
  "credential_value_access_present": false,
  "authorization_header_present": false,
  "kill_switch_required": true,
  "rate_limit_required": true,
  "production_residuals_closed": false,
  "validation": {},
  "incident_hooks": [],
  "residual_monitoring": [],
  "boundary_statement": "External sandbox external call boundary is a non-executing guard contract."
}
```

## 8. Capability Snapshot

Future implementation must keep all capability fields false:

```json
{
  "external_call_implemented": false,
  "external_call_authorized": false,
  "http_client_present": false,
  "sdk_present": false,
  "endpoint_present": false,
  "dns_network_present": false,
  "api_call_present": false,
  "request_transformation_present": false,
  "upload_present": false,
  "scheduler_present": false,
  "publish_present": false,
  "url_present": false,
  "platform_content_id_present": false,
  "receipt_present": false
}
```

Any true value is a blocker.

## 9. Credential Boundary Snapshot

Future implementation must represent credential handling as prohibition/status only:

```json
{
  "credential_value_access_present": false,
  "authorization_header_present": false,
  "credential_use_authorized": false,
  "secret_values_logged": false,
  "secret_values_persisted": false,
  "credential_boundary_mode": "status_only"
}
```

The implementation must not read environment secrets, secret manager values, tokens, client secrets or authorization material.

## 10. Dependency Snapshot

Future implementation must represent required dependency boundaries:

```json
{
  "controlled_binding_required": true,
  "validation_envelope_required": true,
  "qc_non_publishable_blocks_required": true,
  "account_health_hold_blocks_required": true,
  "kill_switch_required": true,
  "kill_switch_fail_closed_required": true,
  "rate_limit_required": true,
  "rate_limit_non_unlimited_required": true
}
```

These are requirements only.

They must not trigger runtime execution.

## 11. Evidence Boundary Snapshot

Future implementation must represent evidence boundaries:

```json
{
  "sandbox_validation_is_publish_success": false,
  "missing_evidence_is_success": false,
  "pending_is_success": false,
  "timeout_is_success": false,
  "result_evidence_is_production": false,
  "production_receipt_present": false,
  "published_url_present": false,
  "platform_content_id_present": false
}
```

Every fake success condition must be explicit and blocked.

## 12. Validation Result

Future validation result must include:

```json
{
  "boundary_valid": true,
  "external_call_surface_absent": true,
  "transport_surface_absent": true,
  "credential_surface_absent": true,
  "production_identity_absent": true,
  "blocking_reasons": [],
  "warnings": [],
  "rationale": []
}
```

Rules:

- `boundary_valid=true` means the guard contract is internally consistent only
- boundary validity does not authorize external call
- boundary validity does not authorize request construction
- boundary validity does not authorize client creation
- boundary validity does not authorize endpoint definition
- boundary validity does not authorize production residual closure

## 13. Incident Hooks

Future implementation must support inert incident hook shapes for:

- `EXTERNAL_SANDBOX_EXTERNAL_CALL_SURFACE_DETECTED`
- `EXTERNAL_SANDBOX_HTTP_CLIENT_SURFACE_DETECTED`
- `EXTERNAL_SANDBOX_SDK_SURFACE_DETECTED`
- `EXTERNAL_SANDBOX_ENDPOINT_SURFACE_DETECTED`
- `EXTERNAL_SANDBOX_DNS_NETWORK_SURFACE_DETECTED`
- `EXTERNAL_SANDBOX_REQUEST_TRANSFORMATION_DETECTED`
- `EXTERNAL_SANDBOX_CREDENTIAL_VALUE_ACCESS_DETECTED`
- `EXTERNAL_SANDBOX_FAKE_SUCCESS_SURFACE_DETECTED`
- `EXTERNAL_SANDBOX_PRODUCTION_IDENTITY_SURFACE_DETECTED`

Incident hooks must include:

- incident type
- severity
- target platform
- target mode
- rationale

Incident hooks must not include:

- secret values
- authorization headers
- endpoint values
- URLs
- platform content IDs
- receipts

## 14. Static Prohibitions

Future implementation must not import or reference:

- `requests`
- `httpx`
- `aiohttp`
- `urllib.request`
- `urllib3`
- `socket`
- `dns`
- platform SDKs
- endpoint constants
- URL constants
- HTTP method constants
- upload helpers
- scheduler helpers
- publish helpers
- receipt helpers

Forbidden helper names:

- `to_request`
- `as_request`
- `to_payload`
- `as_payload`
- `to_http`
- `to_headers`
- `to_body`
- `send`
- `execute`
- `post`
- `put`
- `patch`
- `upload`
- `publish`
- `schedule`
- `emit_url`
- `emit_receipt`
- `create_receipt`

## 15. Serialization Rules

Future implementation must provide deterministic audit serialization:

- stable key ordering where practical
- JSON serializable primitives only
- no timestamps unless supplied by input
- no random IDs
- no object memory addresses
- no environment-dependent fields
- no secret values
- no endpoint values

Same input must produce the same boundary output and validation result.

## 16. Testing Requirements

Future tests must cover at minimum:

1. boundary shape contains required fields
2. target platform exact
3. target mode exact
4. external call remains absent
5. HTTP client remains absent
6. SDK remains absent
7. endpoint remains absent
8. DNS/network remains absent
9. API call remains absent
10. request transformation remains absent
11. upload remains absent
12. scheduler remains absent
13. publish remains absent
14. URL remains absent
15. `platform_content_id` remains absent
16. receipt remains absent
17. credential value access remains absent
18. authorization header remains absent
19. kill switch requirement present
20. rate-limit non-unlimited requirement present
21. fake success conditions are false
22. boundary validity does not authorize execution
23. residuals remain open
24. deterministic serialization replay
25. static source has no HTTP/SDK/endpoint/DNS primitives

## 17. Future Implementation Gate

Before code is written, create:

```text
docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_GATE.md
```

After code is written, create and execute:

```text
tests/gates/sandbox/run_external_sandbox_external_call_boundary_implementation_gate.py
```

Expected future artifacts:

```text
OUT/audit/external_sandbox_external_call_boundary_implementation_gate/final_verdict.json
OUT/audit/external_sandbox_external_call_boundary_implementation_gate/checklist_results.json
OUT/audit/external_sandbox_external_call_boundary_implementation_gate/scenario_outputs.json
OUT/audit/external_sandbox_external_call_boundary_implementation_gate/metrics.json
OUT/audit/external_sandbox_external_call_boundary_implementation_gate/static_scan_review.json
OUT/audit/external_sandbox_external_call_boundary_implementation_gate/side_effect_absence_review.json
OUT/audit/external_sandbox_external_call_boundary_implementation_gate/residual_monitoring_review.json
OUT/audit/external_sandbox_external_call_boundary_implementation_gate/determinism_review.json
```

## 18. Residual Monitoring

Required production residuals remain open:

```json
[
  "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
  "PLATFORM_INTEGRATION_NOT_ENABLED",
  "PUBLISH_RESULT_HISTORY_STILL_SHORT"
]
```

This implementation plan may reduce only:

- boundary marker implementation uncertainty
- capability snapshot uncertainty
- guard contract validation uncertainty
- static absence check uncertainty

It must not reduce:

- production publish evidence residual
- platform integration residual
- production result history residual
- external sandbox execution residual
- post-publish metric residual
- attribution causality residual

## 19. Failure Conditions

Immediate `HOLD` if future implementation:

- creates an external call
- imports HTTP client
- imports SDK client
- defines endpoint
- accesses DNS/network
- allows API call
- transforms audit object into request payload
- reads credential values
- generates authorization header
- uploads content
- invokes scheduler
- publishes content
- emits URL
- emits `platform_content_id`
- creates receipt
- treats sandbox validation as publish success
- closes production residuals
- modifies Publisher runtime execution
- modifies QC, Account Health, Strategy, Orchestrator or core

## 20. Exit Criteria

This plan is acceptable only if:

```json
{
  "implementation_planned": true,
  "implementation_created": false,
  "offline_pre_execution_only": true,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "sdk_allowed": false,
  "endpoint_allowed": false,
  "dns_network_allowed": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "url_authorized": false,
  "platform_content_id_authorized": false,
  "receipt_authorized": false,
  "credential_value_access_authorized": false,
  "production_residuals_remain_open": true
}
```

## 21. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

```text
docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_GATE.md
```

That gate must freeze implementation acceptance criteria before any boundary marker code is created.

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
