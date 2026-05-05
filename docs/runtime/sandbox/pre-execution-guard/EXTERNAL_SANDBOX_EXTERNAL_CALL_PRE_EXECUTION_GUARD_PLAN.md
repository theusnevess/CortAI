# EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_PLAN

## 1. Purpose

`EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_PLAN` defines a future pre-execution guard layer for external sandbox external-call attempts.

This is a planning artifact only.

It does not create code, create tests, create a runner, execute tests, authorize external calls, create HTTP clients, create platform SDKs, define endpoints, access DNS/network, call APIs, upload content, schedule publication, publish content, emit URLs, emit `platform_content_id`, create receipts, access credential values, generate authorization headers, integrate runtime execution, close production residuals, modify Publisher execution behavior, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The purpose is to define how a future guard would block a future attempt to cross the accepted external-call boundary.

Final principle:

> The pre-execution guard may block a crossing attempt. It must not create the capability to cross.

## 2. Starting State

Canonical current state:

```json
{
  "external_call_boundary_implementation": "ACCEPTED_WITH_MONITORING",
  "boundary_state": "external_call_absent",
  "boundary_marker_only": true,
  "guard_contract_only": true,
  "offline_pre_execution_only": true,
  "non_transport": true,
  "non_client": true,
  "non_endpoint": true,
  "external_execution_authorized": false,
  "real_publishing_authorized": false,
  "runtime_integration": false,
  "production_residuals_open": true
}
```

Required prior artifacts:

- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_REVIEW.md`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_external_call_boundary_implementation_gate.py`
- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/final_verdict.json`
- `backend/app/creative/agents/publisher/external_sandbox_external_call_boundary.py`
- `tests/sandbox/unit/test_external_sandbox_external_call_boundary_unittest.py`

## 3. Scope

In scope for this future plan:

- pre-execution guard contract
- crossing-attempt classification
- guard decision semantics
- dependency readiness checks
- kill switch blocking semantics
- rate-limit blocking semantics
- credential-status-only checks
- fake-success blocking semantics
- incident hook shape
- guard trace shape
- residual monitoring rules
- future gate criteria

Out of scope:

- HTTP client
- platform SDK
- endpoint
- DNS/network
- API call
- request construction
- request transformation layer
- upload
- scheduler
- publish
- URL emission
- `platform_content_id`
- receipt
- credential value access
- authorization header generation
- platform provider binding activation
- runtime integration
- production residual closure

## 4. Guard Role

The future pre-execution guard must answer:

- Was there an attempted crossing of the external-call boundary?
- Which prohibited capability was requested?
- Which dependency or safety rule blocks the attempt?
- Which incident hooks should be emitted?
- Why execution remains unauthorized?

The future pre-execution guard must not answer:

- how to call a platform
- how to build an HTTP request
- how to authenticate
- how to upload media
- how to publish
- how to schedule
- whether publishing succeeded
- whether production evidence exists
- whether residuals can close

## 5. Proposed Future Files

Future implementation may be planned later only after a dedicated gate accepts this plan.

Possible future files:

```text
backend/app/creative/agents/publisher/external_sandbox_pre_execution_guard.py
tests/sandbox/unit/test_external_sandbox_pre_execution_guard_unittest.py
```

This plan does not create those files.

Any future implementation must be additive.

It must not modify:

- `backend/app/creative/agents/publisher/external_sandbox_external_call_boundary.py`
- `backend/app/creative/agents/publisher/external_sandbox_controlled_binding.py`
- `backend/app/creative/agents/publisher/external_sandbox_validation_envelope.py`
- `backend/app/creative/agents/publisher/sandbox_adapter.py`
- `backend/app/creative/agents/publisher/publish_lifecycle_writer.py`
- QC
- Account Health
- Strategy
- Orchestrator
- Attribution
- Experiment
- core pipeline

## 6. Guard Input Contract

Future input may include only status, references and booleans:

```json
{
  "run_id": "...",
  "content_id": "...",
  "boundary_ref": "...",
  "controlled_binding_ref": "...",
  "validation_envelope_ref": "...",
  "publish_eligibility_trace_ref": "...",
  "qc_trace_ref": "...",
  "account_health_trace_ref": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "attempted_capabilities": {
    "external_call": false,
    "http_client": false,
    "platform_sdk": false,
    "endpoint": false,
    "dns_network": false,
    "api_call": false,
    "request_transformation": false,
    "upload": false,
    "scheduler": false,
    "publish": false,
    "url": false,
    "platform_content_id": false,
    "receipt": false,
    "credential_value_access": false,
    "authorization_header": false
  },
  "dependency_status": {
    "qc_status": "APPROVE | HOLD | REJECT | UNKNOWN",
    "qc_publishable": true,
    "account_health_decision": "SAFE | CAUTION | HOLD | UNKNOWN",
    "credential_status": "present | missing | invalid_shape | not_checked",
    "kill_switch_active": false,
    "kill_switch_missing": false,
    "rate_limit_requests_allowed": false
  }
}
```

Forbidden input:

- endpoint values
- URLs
- request body
- headers
- authorization headers
- credential values
- tokens
- client secrets
- media bytes
- upload file handles
- scheduler job IDs
- platform receipts
- post-publish metrics

## 7. Guard Output Contract

Future guard output must be deterministic and serializable:

```json
{
  "guard_version": "external_sandbox_pre_execution_guard_v1",
  "guard_type": "external_call_pre_execution_blocker",
  "guard_state": "blocking_only",
  "run_id": "...",
  "content_id": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "crossing_attempt_detected": false,
  "blocked": true,
  "block_level": "none | warning | critical",
  "blocked_capabilities": [],
  "dependency_blocks": [],
  "external_call_authorized": false,
  "http_client_authorized": false,
  "platform_sdk_authorized": false,
  "endpoint_authorized": false,
  "dns_network_authorized": false,
  "api_call_authorized": false,
  "request_transformation_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "publish_authorized": false,
  "url_authorized": false,
  "platform_content_id_authorized": false,
  "receipt_authorized": false,
  "credential_value_access_authorized": false,
  "authorization_header_authorized": false,
  "production_residuals_closed": false,
  "incident_hooks": [],
  "rationale": [],
  "residual_monitoring": []
}
```

Important rule:

- `blocked=true` means the guard prevented crossing.
- `blocked=false` must not mean execution is authorized.
- No guard output may authorize external execution.

## 8. Crossing Attempt Classification

Future guard must classify attempted capabilities into explicit reason codes:

```json
{
  "external_call": "EXTERNAL_CALL_ATTEMPT_BLOCKED",
  "http_client": "HTTP_CLIENT_ATTEMPT_BLOCKED",
  "platform_sdk": "PLATFORM_SDK_ATTEMPT_BLOCKED",
  "endpoint": "ENDPOINT_ATTEMPT_BLOCKED",
  "dns_network": "DNS_NETWORK_ATTEMPT_BLOCKED",
  "api_call": "API_CALL_ATTEMPT_BLOCKED",
  "request_transformation": "REQUEST_TRANSFORMATION_ATTEMPT_BLOCKED",
  "upload": "UPLOAD_ATTEMPT_BLOCKED",
  "scheduler": "SCHEDULER_ATTEMPT_BLOCKED",
  "publish": "PUBLISH_ATTEMPT_BLOCKED",
  "url": "URL_EMISSION_ATTEMPT_BLOCKED",
  "platform_content_id": "PLATFORM_CONTENT_ID_ATTEMPT_BLOCKED",
  "receipt": "RECEIPT_ATTEMPT_BLOCKED",
  "credential_value_access": "CREDENTIAL_VALUE_ACCESS_ATTEMPT_BLOCKED",
  "authorization_header": "AUTHORIZATION_HEADER_ATTEMPT_BLOCKED"
}
```

Any attempted capability must:

- set `crossing_attempt_detected=true`
- add a blocked capability
- add a reason code
- emit an incident hook
- keep all authorization fields false

## 9. Dependency Blocking Rules

Future guard must block when:

- boundary marker missing
- controlled binding missing
- validation envelope missing
- publish eligibility trace missing
- QC trace missing
- QC status is `HOLD`
- QC status is `REJECT`
- QC `publishable=false`
- Account Health decision is `HOLD`
- credential status is `missing`
- credential status is `invalid_shape`
- kill switch active
- kill switch missing
- rate limit requests allowed
- target platform not exact
- target mode not exact

These dependency blocks must not create execution permission when absent.

Passing dependency checks only means no local dependency block was found.

It does not mean external execution is authorized.

## 10. Credential Boundary

Future guard may inspect credential status only:

```json
{
  "credential_status": "present | missing | invalid_shape | not_checked",
  "credential_values_accessed": false,
  "authorization_header_generated": false,
  "credential_scope": "status_only"
}
```

The guard must not:

- read environment secrets
- read secret manager values
- copy token values
- generate authorization headers
- persist credentials
- log credential values

Credential value access is a critical blocker.

## 11. Kill Switch And Rate-Limit Rules

Kill switch:

- missing kill switch blocks
- active kill switch blocks
- weak kill switch semantics block
- kill switch must fail closed
- kill switch must block external call, upload and scheduler

Rate limit:

- disabled means not authorized
- `null` limits mean not authorized, not unlimited
- request allowances must remain false
- rate-limit ambiguity blocks

Neither kill switch nor rate-limit checks may authorize execution.

## 12. Fake Success Prevention

Future guard must fail if any output attempts to represent:

- publish success
- platform validation success
- production receipt
- published URL
- `platform_content_id`
- production evidence
- post-publish metrics
- attribution causal claim

Forbidden interpretations:

- boundary present means ready
- guard passed means ready
- no blocked dependency means ready
- sandbox state means production evidence
- blocked=false means permission

## 13. Incident Hooks

Future guard must support inert incident hooks for:

- `EXTERNAL_SANDBOX_PRE_EXECUTION_EXTERNAL_CALL_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_HTTP_CLIENT_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_SDK_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_ENDPOINT_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_DNS_NETWORK_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_API_CALL_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_REQUEST_TRANSFORMATION_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_UPLOAD_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_SCHEDULER_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_PUBLISH_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_URL_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_PLATFORM_CONTENT_ID_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_RECEIPT_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_CREDENTIAL_VALUE_ACCESS_ATTEMPT`
- `EXTERNAL_SANDBOX_PRE_EXECUTION_FAKE_SUCCESS_ATTEMPT`

Incident hooks must not include:

- endpoints
- URLs
- credential values
- authorization headers
- tokens
- media bytes
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
- `call_api`
- `upload`
- `publish`
- `schedule`
- `emit_url`
- `emit_receipt`
- `create_receipt`

## 15. Trace Requirements

Future guard trace must include:

```json
{
  "pre_execution_guard_trace": {
    "boundary_ref": "...",
    "crossing_attempt_detected": false,
    "blocked_capabilities": [],
    "dependency_blocks": [],
    "authorization_summary": {
      "external_call_authorized": false,
      "upload_authorized": false,
      "scheduler_authorized": false,
      "publish_authorized": false
    },
    "incident_hooks": [],
    "residual_monitoring": [],
    "boundary_statement": "Pre-execution guard blocks crossing attempts and does not create execution capability."
  }
}
```

Trace must be reconstructible and deterministic.

Trace must not include:

- endpoint values
- credential values
- authorization headers
- URLs
- platform content IDs
- receipts

## 16. Future Gate

Before implementation, create:

```text
docs/runtime/sandbox/pre-execution-guard/EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_GATE.md
```

After implementation, create and execute:

```text
tests/gates/sandbox/run_external_sandbox_external_call_pre_execution_guard_gate.py
```

Expected future artifacts:

```text
OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/final_verdict.json
OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/checklist_results.json
OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/scenario_outputs.json
OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/metrics.json
OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/static_scan_review.json
OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/side_effect_absence_review.json
OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/security_review.json
OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/residual_monitoring_review.json
```

Expected verdict if implemented correctly:

- `GO_WITH_MONITORING`

## 17. Required Scenario Coverage

Future gate must cover at minimum:

1. no crossing attempt still does not authorize execution
2. external call attempt blocked
3. HTTP client attempt blocked
4. SDK attempt blocked
5. endpoint attempt blocked
6. DNS/network attempt blocked
7. API call attempt blocked
8. request transformation attempt blocked
9. upload attempt blocked
10. scheduler attempt blocked
11. publish attempt blocked
12. URL attempt blocked
13. `platform_content_id` attempt blocked
14. receipt attempt blocked
15. credential value access attempt blocked
16. authorization header attempt blocked
17. fake success attempt blocked
18. missing boundary ref blocks
19. missing controlled binding ref blocks
20. missing validation envelope ref blocks
21. missing QC trace blocks
22. QC `HOLD` blocks
23. QC `REJECT` blocks
24. QC `publishable=false` blocks
25. Account Health `HOLD` blocks
26. missing credentials blocks
27. invalid credentials block
28. kill switch active blocks
29. kill switch missing blocks
30. rate-limit request allowed blocks
31. target platform mismatch blocks
32. target mode mismatch blocks
33. deterministic replay
34. incident hooks contain no sensitive values
35. production residuals remain open
36. no runtime/core mutation

## 18. Residual Monitoring

Required residuals remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`
- `EXTERNAL_CALL_NOT_IMPLEMENTED`
- `EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED`

This plan may reduce only:

- pre-execution guard design uncertainty
- crossing-attempt classification uncertainty
- dependency-blocking design uncertainty

It must not reduce:

- production publish evidence residual
- platform integration residual
- production result history residual
- external execution residual
- post-publish metrics residual
- attribution causality residual

## 19. Failure Conditions

Immediate `HOLD` if future implementation:

- creates external call capability
- imports HTTP client
- imports SDK client
- defines endpoint
- accesses DNS/network
- allows API call
- transforms audit object into request payload
- reads credential values
- generates authorization headers
- uploads content
- invokes scheduler
- publishes content
- emits URL
- emits `platform_content_id`
- creates receipt
- treats guard pass as publish success
- treats blocked=false as execution authorization
- closes production residuals
- modifies Publisher runtime execution
- modifies QC, Account Health, Strategy, Orchestrator, Attribution, Experiment or core

## 20. Exit Criteria

This plan is acceptable only if:

```json
{
  "pre_execution_guard_planned": true,
  "implementation_created": false,
  "runner_created": false,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "sdk_allowed": false,
  "endpoint_allowed": false,
  "dns_network_allowed": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "publish_authorized": false,
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
docs/runtime/sandbox/pre-execution-guard/EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_GATE.md
```

That gate must freeze acceptance criteria before any pre-execution guard implementation exists.

Still forbidden:

- external call
- HTTP client
- SDK client
- endpoint
- DNS/network
- API call
- request transformation layer
- upload
- scheduler
- publish
- URL
- `platform_content_id`
- receipt
- credential value access
- production residual closure
- runtime integration
