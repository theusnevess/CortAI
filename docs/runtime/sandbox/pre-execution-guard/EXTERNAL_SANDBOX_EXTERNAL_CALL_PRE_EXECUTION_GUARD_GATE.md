# EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_GATE

## 1. Purpose

`EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_GATE` freezes the acceptance criteria for a future offline pre-execution guard.

This is a gate specification artifact only.

It does not create code, create tests, create a runner, execute tests, authorize external calls, create HTTP clients, create platform SDKs, define endpoints, access DNS/network, call APIs, transform requests, upload content, schedule publication, publish content, emit URLs, emit `platform_content_id`, create receipts, access credential values, generate authorization headers, integrate runtime execution, close production residuals, modify Publisher execution behavior, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The gate must prove that the future guard is:

```json
{
  "guard_type": "external_call_pre_execution_blocker",
  "guard_state": "blocking_only",
  "external_call_authorized": false,
  "blocked_false_does_not_authorize": true,
  "guard_pass_does_not_mean_success": true,
  "http_client_allowed": false,
  "sdk_allowed": false,
  "endpoint_allowed": false,
  "dns_network_allowed": false,
  "api_call_allowed": false,
  "runtime_integration": false,
  "production_residuals_remain_open": true
}
```

Final principle:

> The pre-execution guard blocks crossing attempts. It must not create crossing capability.

## 2. Scope

In scope for the future gate:

- guard contract shape
- crossing-attempt classification
- dependency block semantics
- `blocked=false` semantics
- static scan for forbidden imports and helpers
- side-effect absence validation
- incident hook safety
- deterministic serialization
- residual monitoring integrity
- boundary preservation

Out of scope:

- external call
- HTTP client
- platform SDK
- endpoint
- DNS/network
- API call
- request construction
- request transformation layer
- upload
- scheduler
- real publish
- URL
- `platform_content_id`
- receipt
- credential value access
- authorization header
- runtime integration
- production residual closure

## 3. Preconditions

The future gate may run only after these artifacts exist:

- `docs/runtime/sandbox/pre-execution-guard/EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_PLAN.md`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_REVIEW.md`
- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/final_verdict.json`
- future implementation file: `backend/app/creative/agents/publisher/external_sandbox_pre_execution_guard.py`
- future unit test file: `tests/sandbox/unit/test_external_sandbox_pre_execution_guard_unittest.py`

The future runner is:

```text
tests/gates/sandbox/run_external_sandbox_external_call_pre_execution_guard_gate.py
```

## 4. Required Future Implementation Contract

The future implementation may expose only an inert pre-execution guard.

Required constants:

```json
{
  "GUARD_VERSION": "external_sandbox_pre_execution_guard_v1",
  "GUARD_TYPE": "external_call_pre_execution_blocker",
  "GUARD_STATE": "blocking_only",
  "TARGET_PLATFORM_ID": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "TARGET_MODE": "sandbox_external_dry_run",
  "BOUNDARY_STATEMENT": "Pre-execution guard blocks crossing attempts and does not create execution capability."
}
```

Required output invariants:

```json
{
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
  "production_residuals_closed": false
}
```

## 5. Critical Blocked Semantics Rule

The future gate must explicitly validate:

```json
{
  "blocked_true_meaning": "crossing_attempt_or_dependency_block_prevented",
  "blocked_false_meaning": "no_local_guard_block_found",
  "blocked_false_external_call_authorized": false,
  "blocked_false_publish_authorized": false,
  "blocked_false_success": false
}
```

`blocked=false` must never mean:

- external call authorized
- request construction authorized
- client creation authorized
- endpoint authorized
- upload authorized
- scheduler authorized
- publish authorized
- URL emission authorized
- `platform_content_id` authorized
- receipt authorized
- production readiness
- production success

Any future implementation or runner that treats `blocked=false` as permission must return `HOLD`.

## 6. Required Future Output Shape

The future guard output must include:

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
  "blocked": false,
  "blocked_meaning": "no_local_guard_block_found",
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
  "residual_monitoring": [],
  "boundary_statement": "Pre-execution guard blocks crossing attempts and does not create execution capability."
}
```

## 7. Controlled Scenario Battery

The future runner must validate at least these scenarios:

1. implementation file exists
2. unit test file exists
3. guard contract exists
4. target platform exact
5. target mode exact
6. no crossing attempt has `blocked=false` but all authorization fields false
7. `blocked=false` does not mean external readiness
8. external call attempt blocked
9. HTTP client attempt blocked
10. platform SDK attempt blocked
11. endpoint attempt blocked
12. DNS/network attempt blocked
13. API call attempt blocked
14. request transformation attempt blocked
15. upload attempt blocked
16. scheduler attempt blocked
17. publish attempt blocked
18. URL attempt blocked
19. `platform_content_id` attempt blocked
20. receipt attempt blocked
21. credential value access attempt blocked
22. authorization header attempt blocked
23. fake success attempt blocked
24. missing boundary ref blocks
25. missing controlled binding ref blocks
26. missing validation envelope ref blocks
27. missing publish eligibility trace blocks
28. missing QC trace blocks
29. QC `HOLD` blocks
30. QC `REJECT` blocks
31. QC `publishable=false` blocks
32. Account Health `HOLD` blocks
33. missing credentials block
34. invalid credentials block
35. kill switch active blocks
36. kill switch missing blocks
37. weak kill switch semantics block
38. rate-limit request allowed blocks
39. target platform mismatch blocks
40. target mode mismatch blocks
41. incident hooks contain no sensitive values
42. deterministic replay
43. static scan has no HTTP/SDK/endpoint/DNS/API primitives
44. production residuals remain open
45. no runtime/core mutation

## 8. Checklist

The future checklist must include:

- implementation present
- unit tests present
- guard type is `external_call_pre_execution_blocker`
- guard state is `blocking_only`
- guard output deterministic
- target platform exact
- target mode exact
- `blocked=false` semantics explicit
- `blocked=false` does not authorize external call
- `blocked=false` does not authorize publish
- guard pass does not mean success
- crossing attempts are blocked
- dependency blocks are explicit
- external call unauthorized
- HTTP client unauthorized
- platform SDK unauthorized
- endpoint unauthorized
- DNS/network unauthorized
- API call unauthorized
- request transformation unauthorized
- upload unauthorized
- scheduler unauthorized
- publish unauthorized
- URL unauthorized
- `platform_content_id` unauthorized
- receipt unauthorized
- credential value access unauthorized
- authorization header unauthorized
- fake success impossible
- incident hooks safe
- static scan clean
- production residuals open
- boundary preserved
- no runtime integration
- no core mutation

## 9. Static Scan Requirements

The future runner must fail on forbidden imports or executable helpers.

Forbidden imports or module references:

- `requests`
- `httpx`
- `aiohttp`
- `urllib.request`
- `urllib3`
- `socket`
- `dns`
- platform SDK imports
- OAuth client imports
- upload client imports
- scheduler client imports

Forbidden constants or fields:

- endpoint values
- base URLs
- API URLs
- upload URLs
- publish URLs
- callback URLs
- webhook URLs
- HTTP methods
- authorization headers
- credential values
- production receipts
- published URLs
- platform content IDs

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

## 10. Required Future Output Artifacts

The future runner must generate:

- `OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/final_verdict.json`
- `OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/checklist_results.json`
- `OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/scenario_outputs.json`
- `OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/metrics.json`
- `OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/static_scan_review.json`
- `OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/side_effect_absence_review.json`
- `OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/security_review.json`
- `OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/blocked_semantics_review.json`
- `OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/residual_monitoring_review.json`

## 11. Verdict Semantics

`HOLD` if:

- future implementation is missing
- future unit tests are missing
- guard type is not `external_call_pre_execution_blocker`
- guard state is not `blocking_only`
- `blocked=false` implies authorization
- guard pass implies success
- external call is authorized
- HTTP client is allowed
- platform SDK is allowed
- endpoint is allowed
- DNS/network is allowed
- API call is allowed
- request transformation is allowed
- upload is allowed
- scheduler is allowed
- publish is allowed
- URL is allowed
- `platform_content_id` is allowed
- receipt is allowed
- credential value access is allowed
- authorization header is allowed
- fake success is possible
- static scan detects forbidden side-effect surface
- production residual is closed
- runtime integration is introduced
- Strategy, QC, Account Health, Orchestrator, Attribution, Experiment or core pipeline changes
- silent failure is detected

`GO_WITH_MONITORING` if:

- all critical checks pass
- all crossing attempts are blocked
- `blocked=false` is semantically bounded
- no side-effect surface exists
- production residuals remain open
- remaining residuals are explicit, bounded and non-structural

`GO` only if a later governance state authorizes broader operational maturity.

Expected result for this gate is `GO_WITH_MONITORING` when implemented correctly.

Do not hardcode the verdict.

## 12. Final Verdict Schema

The future `final_verdict.json` must include at minimum:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "implementation_present": true,
  "unit_tests_present": true,
  "guard_type": "external_call_pre_execution_blocker",
  "guard_state": "blocking_only",
  "blocked_false_does_not_authorize": true,
  "guard_pass_does_not_mean_success": true,
  "production_residuals_remain_open": true,
  "blocked_false_authorizes_external_call": false,
  "blocked_false_authorizes_publish": false,
  "external_call_authorized": false,
  "http_client_detected": false,
  "platform_sdk_detected": false,
  "endpoint_detected": false,
  "dns_network_detected": false,
  "api_call_detected": false,
  "request_transformation_detected": false,
  "upload_detected": false,
  "scheduler_detected": false,
  "publish_detected": false,
  "url_detected": false,
  "platform_content_id_detected": false,
  "receipt_detected": false,
  "credential_value_access_detected": false,
  "authorization_header_detected": false,
  "fake_success_detected": false,
  "production_residuals_closed": false,
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_IMPLEMENTATION | HOLD_BEFORE_NEXT_STEP"
}
```

## 13. Residual Monitoring

These residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`
- `EXTERNAL_CALL_NOT_IMPLEMENTED`
- `EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED`

This gate may reduce only:

- pre-execution guard specification uncertainty
- crossing-attempt classification uncertainty
- blocked-semantics uncertainty

It must not reduce:

- production publish evidence residual
- real platform integration residual
- production result history residual
- external execution residual
- post-publish metrics residual
- attribution causality residual

## 14. Next Authorized Step

After this gate is accepted, the next authorized step is the offline-only implementation slice:

```text
backend/app/creative/agents/publisher/external_sandbox_pre_execution_guard.py
tests/sandbox/unit/test_external_sandbox_pre_execution_guard_unittest.py
```

Do not create the pre-execution guard gate runner until the implementation exists.

Still forbidden:

- external call
- HTTP client
- platform SDK
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
- authorization header
- production residual closure
- runtime integration
- core pipeline change

Final principle:

> A pre-execution guard can say no. It cannot say go.
