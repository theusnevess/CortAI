# EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_GATE

## 1. Purpose

`EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_GATE` freezes the acceptance contract for the external sandbox call boundary before any implementation exists.

This is a gate specification artifact.

It does not create code, create tests, create a runner, execute tests, implement external calls, create HTTP clients, create SDK clients, configure endpoints, access DNS/network, call platform APIs, upload content, transfer media bytes, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, create receipts, collect post-publish metrics, close production residuals, modify Publisher runtime execution, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The gate exists to prove the system is still pre-external-call before any boundary implementation is discussed.

Final principle:

> The boundary gate proves no external execution exists and no production authority has leaked into sandbox planning.

## 2. Preconditions

Required prior artifacts:

- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_PLAN.md`
- `docs/runtime/sandbox/controlled-binding/EXTERNAL_SANDBOX_CONTROLLED_BINDING_REVIEW.md`
- `docs/runtime/sandbox/controlled-binding/EXTERNAL_SANDBOX_CONTROLLED_BINDING_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_controlled_binding_gate.py`
- `OUT/audit/external_sandbox_controlled_binding_gate/final_verdict.json`

Required prior state:

```json
{
  "controlled_binding": "GATED",
  "controlled_binding_state": "PRE_EXECUTION_BINDING_GATED",
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

In scope for the future gate:

- artifact integrity
- current no-external-call verification
- static scan for forbidden external execution primitives
- boundary plan completeness
- controlled binding state consistency
- anti-fake-success rule completeness
- kill switch fail-closed requirements
- rate-limit non-unlimited requirements
- credential status-only boundary
- audit object non-transport reuse requirement
- residual monitoring integrity
- next-step restriction

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
- URL emission
- `platform_content_id` emission
- receipt creation
- post-publish metrics
- production residual closure
- runtime integration
- core pipeline changes

## 4. Required Future Runner

The future runner path is:

```text
tests/gates/sandbox/run_external_sandbox_external_call_boundary_gate.py
```

The runner must be audit-only.

It may inspect docs, source files and prior audit artifacts.

It must not:

- create external call code
- import HTTP clients
- import SDK clients
- define endpoints
- perform DNS/network access
- execute API calls
- upload content
- invoke scheduler
- publish content
- emit URL
- emit `platform_content_id`
- emit receipt
- close production residuals

## 5. Required Output Artifacts

The future runner must generate:

```text
OUT/audit/external_sandbox_external_call_boundary_gate/final_verdict.json
OUT/audit/external_sandbox_external_call_boundary_gate/checklist_results.json
OUT/audit/external_sandbox_external_call_boundary_gate/scenario_outputs.json
OUT/audit/external_sandbox_external_call_boundary_gate/metrics.json
OUT/audit/external_sandbox_external_call_boundary_gate/static_scan_review.json
OUT/audit/external_sandbox_external_call_boundary_gate/boundary_completeness_review.json
OUT/audit/external_sandbox_external_call_boundary_gate/side_effect_absence_review.json
OUT/audit/external_sandbox_external_call_boundary_gate/residual_monitoring_review.json
OUT/audit/external_sandbox_external_call_boundary_gate/anti_fake_success_review.json
OUT/audit/external_sandbox_external_call_boundary_gate/next_step_review.json
```

## 6. Required Current-State Checks

The future runner must validate:

```json
{
  "external_call": false,
  "http_client": false,
  "sdk": false,
  "endpoint": false,
  "dns_network": false,
  "upload": false,
  "scheduler": false,
  "publish": false,
  "url": false,
  "platform_content_id": false,
  "receipt": false
}
```

These are current-state checks.

They do not authorize future execution.

## 7. Static Scan Requirements

The future runner must statically scan Publisher sandbox-related files for:

- `requests`
- `httpx`
- `aiohttp`
- `urllib.request`
- `urllib3`
- `socket`
- `dns`
- `googleapiclient`
- `boto3`
- platform SDK imports
- endpoint constants
- URL constants
- upload helpers
- scheduler helpers
- publish helpers
- receipt helpers
- request transformation helpers

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

Static scan must return `HOLD` if any forbidden primitive is present outside historical docs or audit artifacts.

## 8. Boundary Completeness Requirements

The future runner must validate the boundary plan defines:

- external call authority model
- validation versus execution separation
- endpoint boundary
- client boundary
- request shape boundary
- credential boundary
- kill switch boundary
- rate-limit boundary
- timeout and retry boundary
- result evidence boundary
- lifecycle evidence boundary
- incident hooks
- anti-fake-success rules
- residual monitoring rules
- failure conditions
- next authorized artifact

Missing boundary sections produce `HOLD`.

## 9. Controlled Scenario Battery

The future runner must validate at least:

1. boundary plan exists
2. controlled binding review exists
3. controlled binding gate verdict is acceptable
4. current external call absent
5. current HTTP client absent
6. current SDK absent
7. current endpoint absent
8. current DNS/network access absent
9. current API call absent
10. current upload absent
11. current scheduler absent
12. current publish absent
13. current URL emission absent
14. current `platform_content_id` emission absent
15. current receipt emission absent
16. production residuals remain open
17. credential values remain unauthorized
18. authorization headers remain unauthorized
19. audit objects are not transport payloads
20. endpoint boundary is explicit
21. client boundary is explicit
22. request shape boundary is explicit
23. kill switch fail-closed boundary is explicit
24. rate-limit non-unlimited boundary is explicit
25. timeout and retry boundary is explicit
26. anti-fake-success rules are explicit
27. sandbox validation is not publish success
28. missing evidence is not success
29. pending is not success
30. timeout is not success
31. URL/platform ID forbidden
32. receipt forbidden
33. lifecycle remains append-only
34. Account Health `HOLD` boundary preserved
35. QC non-publishable boundary preserved
36. Strategy does not become publish permission
37. Orchestrator does not become Publisher
38. no runtime/core mutation
39. next step does not authorize execution
40. deterministic audit review possible

The runner may add stricter scenarios.

It must not omit these.

## 10. Checklist

The future checklist must include:

- preconditions present
- boundary plan present
- boundary plan complete
- controlled binding gate passed
- controlled binding review accepted
- external call absent
- HTTP client absent
- SDK absent
- endpoint absent
- DNS/network absent
- API call absent
- upload absent
- scheduler absent
- publish absent
- URL absent
- `platform_content_id` absent
- receipt absent
- credential value access absent
- authorization headers absent
- request transformation absent
- audit objects not transport objects
- kill switch fail-closed required
- rate-limit non-unlimited required
- timeout bounded requirement present
- retry bounded requirement present
- sandbox evidence distinguished from production evidence
- anti-fake-success rules present
- lifecycle append-only boundary present
- Account Health `HOLD` preserved
- QC non-publishable preserved
- Strategy boundary preserved
- Orchestrator boundary preserved
- production residuals remain open
- no side effects
- no runtime/core changes

## 11. Metrics

Future metrics must include:

```json
{
  "critical_failures": 0,
  "blocking_failures_count": 0,
  "scenario_count": 40,
  "scenario_pass_count": 40,
  "checklist_count": 0,
  "checklist_pass_count": 0,
  "external_call_detected": false,
  "http_client_detected": false,
  "sdk_detected": false,
  "endpoint_detected": false,
  "dns_network_detected": false,
  "api_call_detected": false,
  "upload_detected": false,
  "scheduler_detected": false,
  "publish_detected": false,
  "url_detected": false,
  "platform_content_id_detected": false,
  "receipt_detected": false,
  "credential_value_access_detected": false,
  "authorization_header_detected": false,
  "request_transformation_detected": false,
  "production_residuals_closed": false,
  "silent_failures_detected": false
}
```

`checklist_count` and `checklist_pass_count` must be populated by the runner with real values.

## 12. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

Expected future verdict:

- `GO_WITH_MONITORING`

`GO` is not expected because no external sandbox call is implemented and production residuals remain open.

## 13. HOLD Conditions

The future runner must return `HOLD` if:

- external call exists
- HTTP client exists
- SDK exists
- endpoint exists
- DNS/network access exists
- API call exists
- upload exists
- scheduler exists
- publish path exists
- URL emission exists
- `platform_content_id` emission exists
- receipt creation exists
- credential value access exists
- authorization header generation exists
- request transformation exists
- audit object can be reused directly as transport payload
- sandbox validation is treated as publish success
- missing evidence is treated as success
- pending is treated as success
- timeout is treated as success
- Account Health `HOLD` can be bypassed
- QC non-publishable can be bypassed
- Strategy is treated as publish permission
- Orchestrator becomes Publisher
- production residuals are closed
- runtime/core files are modified by the gate

## 14. Residual Monitoring Rules

Required production residuals remain open:

```json
[
  "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
  "PLATFORM_INTEGRATION_NOT_ENABLED",
  "PUBLISH_RESULT_HISTORY_STILL_SHORT"
]
```

This gate may reduce only:

- external call boundary ambiguity
- client/endpoint absence verification ambiguity
- fake success boundary ambiguity
- next-step ambiguity

It must not reduce:

- production publish evidence residual
- platform integration residual
- production result history residual
- external sandbox execution residual
- post-publish metric residual
- attribution causality residual

## 15. Final Verdict Schema

Future `final_verdict.json` must include:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "boundary_plan_present": true,
  "external_call_detected": false,
  "http_client_detected": false,
  "sdk_detected": false,
  "endpoint_detected": false,
  "dns_network_detected": false,
  "api_call_detected": false,
  "upload_detected": false,
  "scheduler_detected": false,
  "publish_detected": false,
  "url_detected": false,
  "platform_content_id_detected": false,
  "receipt_detected": false,
  "credential_value_access_detected": false,
  "authorization_header_detected": false,
  "request_transformation_detected": false,
  "production_residuals_closed": false,
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_REVIEW | HOLD_BEFORE_NEXT_STEP"
}
```

## 16. Final Criteria

The future gate passes only if:

```json
{
  "external_call_detected": false,
  "http_client_detected": false,
  "sdk_detected": false,
  "endpoint_detected": false,
  "dns_network_detected": false,
  "api_call_detected": false,
  "upload_detected": false,
  "scheduler_detected": false,
  "publish_detected": false,
  "url_detected": false,
  "platform_content_id_detected": false,
  "receipt_detected": false,
  "credential_value_access_detected": false,
  "authorization_header_detected": false,
  "request_transformation_detected": false,
  "production_residuals_remain_open": true,
  "boundary_preserved": true
}
```

## 17. Next Authorized Step

After this gate specification is accepted, the next authorized step is the audit-only runner:

```text
tests/gates/sandbox/run_external_sandbox_external_call_boundary_gate.py
```

The runner must validate this gate.

It must not implement the boundary.

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
