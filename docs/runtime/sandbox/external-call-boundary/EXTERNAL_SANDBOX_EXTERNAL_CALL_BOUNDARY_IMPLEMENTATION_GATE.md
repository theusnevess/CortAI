# EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_GATE

## 1. Purpose

`EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_GATE` freezes the acceptance criteria for the future offline implementation of the external sandbox external-call boundary.

This is a gate specification artifact only.

It does not create code, create tests, create a runner, execute tests, call external services, initialize an HTTP client, initialize a platform SDK, define endpoints, perform DNS/network access, upload content, schedule publication, publish content, emit URLs, emit `platform_content_id`, emit receipts, access credential values, close production residuals, modify Publisher runtime execution, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The future implementation may only be:

```text
boundary marker / guard contract
offline
pre-execution
non-transport
non-client
non-endpoint
non-executing
```

Final principle:

> The boundary implementation may mark and guard the external-call boundary. It must not create an external-call capability.

## 2. Scope

In scope for the future implementation gate:

- boundary marker contract
- guard contract shape
- offline-only validation
- pre-execution-only semantics
- non-transport guarantee
- non-client guarantee
- non-endpoint guarantee
- side-effect absence validation
- static scan for forbidden imports, helpers, constants and fields
- deterministic serialization
- residual monitoring integrity
- boundary preservation

Out of scope:

- external calls
- HTTP client
- platform SDK
- endpoint
- DNS/network
- API call
- request transformation layer
- upload
- scheduler
- real publish
- URL
- `platform_content_id`
- platform receipt
- credential value access
- authorization header generation
- production residual closure
- runtime integration
- Orchestrator wiring
- Publisher execution behavior changes
- QC changes
- Account Health changes
- Strategy changes
- core pipeline changes

## 3. Preconditions

The future implementation gate may run only after these artifacts exist:

- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_PLAN.md`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_external_call_boundary_gate.py`
- `OUT/audit/external_sandbox_external_call_boundary_gate/final_verdict.json`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_REVIEW.md`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_PLAN.md`
- future implementation file: `backend/app/creative/agents/publisher/external_sandbox_external_call_boundary.py`
- future unit test file: `tests/sandbox/unit/test_external_sandbox_external_call_boundary_unittest.py`

The future runner is:

- `tests/gates/sandbox/run_external_sandbox_external_call_boundary_implementation_gate.py`

## 4. Required Future Implementation Contract

The future implementation must expose an inert boundary marker and guard contract.

Required constants:

```json
{
  "boundary_version": "external_sandbox_external_call_boundary_v1",
  "boundary_type": "pre_execution_external_call_boundary",
  "boundary_state": "external_call_absent",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "execution_capability": "none",
  "transport_capability": "none",
  "client_capability": "none",
  "endpoint_capability": "none",
  "non_transportable": true,
  "external_call_authorized": false
}
```

The future implementation must keep all of the following false:

```json
{
  "external_call_implemented": false,
  "external_call_authorized": false,
  "http_client_present": false,
  "platform_sdk_present": false,
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
  "production_residuals_closed": false
}
```

## 5. Required Output Shape

The future boundary marker output must be deterministic and serializable:

```json
{
  "boundary_version": "external_sandbox_external_call_boundary_v1",
  "boundary_type": "pre_execution_external_call_boundary",
  "boundary_state": "external_call_absent",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "execution_capability": "none",
  "transport_capability": "none",
  "client_capability": "none",
  "endpoint_capability": "none",
  "non_transportable": true,
  "offline_only": true,
  "pre_execution_only": true,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "dns_network_allowed": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "url_emission_authorized": false,
  "platform_content_id_authorized": false,
  "receipt_authorized": false,
  "credential_value_access_authorized": false,
  "boundary_statement": "External sandbox external-call boundary is a pre-execution guard only."
}
```

The future guard contract may explain why external execution is blocked.

It must not provide a transformation function, transport payload, endpoint, client, request object, send helper, upload helper, publish helper or receipt helper.

## 6. Static Scan Requirements

The future runner must statically scan the future implementation and tests for forbidden imports, constants, helpers and field names.

Forbidden imports or module references include:

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

Forbidden endpoint or transport terms include:

- `endpoint`
- `base_url`
- `api_url`
- `upload_url`
- `publish_url`
- `callback_url`
- `webhook_url`
- `http_method`
- `headers`
- `authorization_header`
- `request_body`
- `payload_for_transport`

Forbidden executable helper names include:

- `send`
- `execute`
- `post`
- `put`
- `patch`
- `call_api`
- `upload`
- `publish`
- `schedule`
- `to_request`
- `as_request`
- `to_http`
- `to_headers`
- `to_body`
- `to_payload`
- `emit_url`
- `emit_receipt`
- `create_receipt`

Forbidden production evidence terms include:

- `published_url`
- `platform_content_id`
- `production_receipt`
- `platform_receipt`
- `result_evidence_is_production`
- `post_publish_metrics`

Forbidden secret access terms include:

- `access_token`
- `refresh_token`
- `client_secret`
- `api_key`
- `password`
- `authorization`
- `bearer`
- raw credential value loading or serialization

The runner must fail on forbidden terms unless the term appears only in explicit deny-list validation, static-scan assertions, documentation strings for blockers, or test names proving rejection.

## 7. Controlled Scenario Battery

The future runner must validate at least these scenarios:

1. implementation file exists
2. unit test file exists
3. boundary marker contract exists
4. guard contract exists
5. target platform is exactly `SHORT_VIDEO_PLATFORM_SANDBOX_V1`
6. target mode is exactly `sandbox_external_dry_run`
7. boundary state is exactly `external_call_absent`
8. implementation is offline-only
9. implementation is pre-execution-only
10. implementation is non-transport
11. implementation is non-client
12. implementation is non-endpoint
13. external call remains unauthorized
14. HTTP client remains absent
15. platform SDK remains absent
16. endpoint remains absent
17. DNS/network remains absent
18. API call remains absent
19. request transformation layer remains absent
20. upload remains absent
21. scheduler remains absent
22. publish remains absent
23. URL emission remains absent
24. `platform_content_id` emission remains absent
25. receipt emission remains absent
26. credential value access remains absent
27. authorization header generation remains absent
28. kill switch guard is represented as blocking, not execution
29. rate-limit guard is represented as blocking, not execution
30. boundary validity does not imply readiness to call externally
31. guard pass does not imply external success
32. fake success terms are rejected
33. incident hooks do not include secrets, URLs, platform IDs or receipts
34. deterministic serialization replay is stable
35. static scan finds no forbidden side-effect surface
36. production residuals remain open
37. Publisher does not become Strategy, QC, Account Health, Attribution or Orchestrator
38. Strategy, QC, Account Health, Orchestrator, Attribution, Experiment and core pipeline remain unchanged

## 8. Checklist

The future checklist must include:

- implementation present
- unit tests present
- boundary marker only
- guard contract only
- offline-only
- pre-execution-only
- non-transport
- non-client
- non-endpoint
- no HTTP client
- no platform SDK
- no endpoint
- no DNS/network
- no API call
- no request transformation layer
- no upload
- no scheduler
- no publish
- no URL
- no `platform_content_id`
- no receipt
- no credential value access
- no authorization header
- target platform exact
- target mode exact
- single sandbox mode
- deterministic serialization
- static scan clean
- fake success impossible
- production residuals open
- boundary preserved
- no runtime integration
- no core mutation

## 9. Required Future Output Artifacts

The future runner must generate:

- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/final_verdict.json`
- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/checklist_results.json`
- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/scenario_outputs.json`
- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/metrics.json`
- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/static_scan_review.json`
- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/side_effect_absence_review.json`
- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/boundary_marker_review.json`
- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/security_review.json`
- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/determinism_review.json`
- `OUT/audit/external_sandbox_external_call_boundary_implementation_gate/residual_monitoring_review.json`

## 10. Verdict Semantics

`HOLD` if:

- future implementation is missing
- future unit tests are missing
- boundary marker contract is missing
- guard contract is missing
- external call exists
- HTTP client exists
- platform SDK exists
- endpoint exists
- DNS/network surface exists
- API call surface exists
- request transformation layer exists
- upload exists
- scheduler exists
- publish exists
- URL exists
- `platform_content_id` exists
- receipt exists
- credential value access exists
- authorization header exists
- fake success is possible
- boundary validity is interpreted as external readiness
- guard pass is interpreted as external success
- static scan detects forbidden side-effect surface
- deterministic replay fails
- production residual is closed
- runtime integration is introduced
- Strategy, QC, Account Health, Orchestrator, Attribution, Experiment or core pipeline changes
- silent failure is detected

`GO_WITH_MONITORING` if:

- all critical checks pass
- future implementation is offline-only
- no side-effect surface exists
- external calls remain unauthorized
- production residuals remain open
- remaining residuals are explicit, bounded and non-structural

`GO` only if a later governance state authorizes broader execution maturity.

Expected result for this gate is `GO_WITH_MONITORING` when implemented correctly, because external execution and production evidence remain intentionally absent.

Do not hardcode the verdict.

## 11. Final Verdict Schema

The future `final_verdict.json` must include at minimum:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "implementation_present": true,
  "unit_tests_present": true,
  "boundary_marker_only": true,
  "guard_contract_only": true,
  "offline_pre_execution_only": true,
  "non_transport": true,
  "non_client": true,
  "non_endpoint": true,
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
  "recommendation": "PROCEED_TO_EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_REVIEW | HOLD_BEFORE_NEXT_STEP"
}
```

## 12. Residual Monitoring

These residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`
- `EXTERNAL_CALL_NOT_IMPLEMENTED`
- `EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED`

This gate may reduce only:

- boundary implementation uncertainty
- guard contract uncertainty
- side-effect absence uncertainty
- static scan uncertainty

It must not reduce:

- production publish evidence residual
- real platform integration residual
- production result history residual
- post-publish metrics residual
- attribution causality residual

## 13. Next Authorized Step

After this gate specification is accepted, the next authorized step is the offline-only implementation slice:

- `backend/app/creative/agents/publisher/external_sandbox_external_call_boundary.py`
- `tests/sandbox/unit/test_external_sandbox_external_call_boundary_unittest.py`

Do not create the implementation gate runner until the implementation exists.

Still forbidden:

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
- production residual closure
- runtime integration
- core pipeline change

Final principle:

> The implementation gate proves the future code is only a boundary marker and guard contract. It must not create a client, request, endpoint, transport payload, receipt, or external execution surface.
