# EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_PLAN

## 1. Purpose

`EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_PLAN` proposes a future offline/preparation-only implementation slice for sandbox validation call preparation.

This is a planning artifact only.

It does not create code, create tests, authorize implementation, authorize implementation tests, authorize HTTP clients, authorize platform SDKs, authorize endpoints, authorize DNS/network access, authorize API calls, authorize credential value access, authorize request transformation, authorize transport payload generation, authorize external calls, authorize runtime integration, authorize upload, authorize scheduling, authorize publishing, authorize production URLs, authorize `platform_content_id`, authorize receipts or close production residuals.

Core rule:

> A proposed allowlist is not implementation permission.

## 2. Starting State

Canonical starting state:

```json
{
  "phase": "IMPLEMENTATION_PLAN_ALLOWED_ONLY",
  "decision": "AUTHORIZE_OFFLINE_PREPARATION_ONLY_IMPLEMENTATION_PLAN",
  "may_create_next_plan": true,
  "may_implement": false,
  "may_create_tests": false,
  "may_execute": false,
  "implementation_authorized": false,
  "implementation_tests_authorized": false,
  "external_call_authorized": false,
  "runtime_integration_authorized": false,
  "production_residuals_remain_open": true
}
```

Required prior artifacts:

- `docs/runtime/sandbox/validation-call/implementation-authorization/EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW.md`
- `docs/runtime/sandbox/validation-call/implementation-authorization/EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_validation_call_implementation_authorization_review_gate.py`
- `OUT/audit/external_sandbox_validation_call_implementation_authorization_review_gate/final_verdict.json`

## 3. Scope

This plan may define:

- future file allowlist proposal
- future offline structure boundaries
- future security scanner expectations
- future deterministic serialization expectations
- future incident hook expectations
- future local validation expectations
- future unit test expectations
- future implementation gate requirements

This plan may not:

- create files
- create tests
- authorize code
- authorize test implementation
- authorize execution
- authorize runtime integration
- authorize external calls
- authorize transport payloads
- authorize request transformation
- authorize credentials
- authorize endpoints

## 4. Proposed Future File Allowlist

This plan proposes, but does not authorize, this future file allowlist:

```text
backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation.py
backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation_security.py
tests/sandbox/unit/test_external_sandbox_validation_call_preparation_unittest.py
```

The allowlist is not active.

The allowlist may become active only after a separate implementation gate passes.

No other files may be proposed by this plan.

The proposed files must remain Publisher-local and offline-only.

The proposed files must not modify:

- QC
- Account Health
- Strategy
- Orchestrator
- Attribution
- Experiment
- core pipeline
- runtime execution wiring
- Publisher runtime execution path

## 5. Future Implementation Boundary

If later authorized by a separate gate, the future implementation must remain:

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

The future implementation may only model local readiness and dependency state for a future sandbox validation call review.

It must not prepare an executable request.

It must not prepare transport payloads.

It must not prepare headers, endpoints or credential-bearing structures.

## 6. Proposed Future Structures

Future implementation may define only inert local structures such as:

- `SandboxValidationCallPreparationInput`
- `SandboxValidationCallDependencyStatus`
- `SandboxValidationCallCredentialStatus`
- `SandboxValidationCallPreparationState`
- `SandboxValidationCallPreparationValidation`
- `SandboxValidationCallPreparationIncident`
- `SandboxValidationCallPreparationBuilder`

All structures must be:

- deterministic
- JSON serializable
- side-effect free
- offline-only
- non-transportable
- non-executable
- free of secret values
- free of endpoint values
- free of URL values
- free of platform SDK bindings

The naming must avoid implying execution success.

Forbidden names:

- `Client`
- `RequestClient`
- `HttpClient`
- `SdkClient`
- `Executor`
- `Sender`
- `Uploader`
- `Publisher`
- `Transport`
- `Receipt`
- `Response`
- `Success`

## 7. Proposed Input Contract

Future input may include only status and references:

```json
{
  "run_id": "...",
  "content_id": "...",
  "validation_envelope_ref": "...",
  "publish_eligibility_trace_ref": "...",
  "qc_trace_ref": "...",
  "account_health_trace_ref": "...",
  "artifact_manifest_ref": "...",
  "metadata_payload_ref": "...",
  "credential_status": "present | missing | invalid_shape | not_checked",
  "kill_switch_blocking": true,
  "rate_limit_state": "not_applicable | blocked | unknown",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run"
}
```

Future input must not include:

- endpoint
- URL
- HTTP method
- headers
- authorization header
- access token
- API key
- client secret
- media bytes
- upload path
- request body
- platform receipt
- production URL
- platform content ID

## 8. Proposed Output Contract

Future output may include only local preparation state:

```json
{
  "preparation_version": "sandbox_validation_call_preparation_v1",
  "run_id": "...",
  "content_id": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "preparation_complete": false,
  "eligible_for_future_sandbox_validation_review": false,
  "external_call_authorized": false,
  "request_transformation_authorized": false,
  "transport_payload_authorized": false,
  "credential_value_access_authorized": false,
  "runtime_integration_authorized": false,
  "blocking_reasons": [],
  "warnings": [],
  "incident_hooks": [],
  "boundary_statement": "Sandbox validation call preparation is not sandbox validation execution."
}
```

`preparation_complete=true` must never mean execution is allowed.

`eligible_for_future_sandbox_validation_review=true` must never mean execution is allowed.

## 9. Forbidden Implementation Surface

Future implementation must not include:

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
- header builders
- authorization header builders
- request body builders
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

## 10. Security Scanner Expectations

Future security scanner must detect and block:

- secret-like keys
- endpoint-like fields
- URL-like fields
- HTTP-like fields
- SDK-like references
- transport-like fields
- request transformation fields
- upload fields
- scheduler fields
- publish fields
- receipt fields
- production result fields

Detection must be deterministic.

Detected values must not be copied into output.

Incidents must not include secret values.

## 11. Determinism Expectations

Future implementation must be deterministic:

- same input produces same output
- no randomness
- no timestamps generated internally
- no environment-dependent values except provided credential status
- stable JSON serialization
- no object memory addresses

## 12. Proposed Future Tests

This plan proposes, but does not authorize, future unit tests for:

1. preparation shape is serializable
2. target platform exact
3. target mode exact
4. external call remains unauthorized
5. request transformation remains unauthorized
6. transport payload remains unauthorized
7. credential value access remains unauthorized
8. runtime integration remains unauthorized
9. HTTP client imports absent
10. platform SDK imports absent
11. endpoint fields rejected
12. secret-like fields rejected
13. URL fields rejected
14. media byte fields rejected
15. receipt fields rejected
16. production URL fields rejected
17. platform content ID fields rejected
18. kill switch blocking remains blocking
19. missing dependency refs block preparation
20. QC non-publishable blocks preparation
21. Account Health `HOLD` blocks preparation
22. preparation complete does not authorize execution
23. future eligibility does not authorize execution
24. incident hooks contain no secrets
25. deterministic replay

These tests may not be created until the implementation gate authorizes them.

## 13. Required Future Implementation Gate

Before any file in the proposed allowlist is created, this gate must be created and accepted:

- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE.md`

The gate must validate:

- proposed allowlist exact
- offline-only boundary
- preparation-only boundary
- no client/transport/endpoint/network surface
- no credential value access
- no request transformation
- no runtime integration
- no external calls
- no production residual closure
- unit tests not yet created before authorization

## 14. Residual Monitoring

The following residuals remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`
- `EXTERNAL_CALL_NOT_IMPLEMENTED`
- `EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED`

This plan does not reduce residuals.

It only narrows the shape of a possible future offline implementation.

## 15. Failure Conditions

Any future artifact must be treated as `HOLD` if it:

- treats this plan as code authorization
- creates files before the implementation gate
- creates tests before the implementation gate
- adds HTTP clients
- adds platform SDKs
- adds endpoints
- adds DNS/network access
- reads credential values
- builds request transformations
- builds transport payloads
- authorizes external calls
- integrates runtime behavior
- authorizes upload
- authorizes scheduler invocation
- authorizes publishing
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

## 16. Exit Criteria

This plan is acceptable only if:

```json
{
  "implementation_plan_created": true,
  "allowlist_proposed": true,
  "allowlist_active": false,
  "implementation_authorized": false,
  "implementation_tests_authorized": false,
  "external_call_authorized": false,
  "runtime_integration_authorized": false,
  "request_transformation_authorized": false,
  "transport_payload_authorized": false,
  "credential_value_access_authorized": false,
  "production_residuals_remain_open": true,
  "gate_required_before_code": true
}
```

## 17. Next Authorized Artifact

The next authorized artifact is:

- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE.md`

That gate must be accepted before any proposed file or test can be created.

## 18. Final Principle

This plan may propose an offline implementation shape.

It cannot activate the allowlist.

It cannot authorize code.

It cannot authorize tests.

It cannot authorize execution.
