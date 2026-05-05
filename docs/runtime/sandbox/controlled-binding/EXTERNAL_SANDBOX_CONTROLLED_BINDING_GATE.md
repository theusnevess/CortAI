# EXTERNAL_SANDBOX_CONTROLLED_BINDING_GATE

## 1. Purpose

`EXTERNAL_SANDBOX_CONTROLLED_BINDING_GATE` freezes the executable acceptance contract for a future pre-execution controlled sandbox binding.

This is a gate specification artifact.

It does not create code, create tests, create a runner, execute tests, call external services, call platform APIs, create HTTP clients, create SDK clients, configure endpoints, access DNS/network, upload content, transfer media bytes, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, collect post-publish metrics, close production residuals, modify Publisher runtime execution, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The gate exists to prove that future controlled binding remains a non-executable policy association.

Final principle:

> A controlled binding may identify a future sandbox target. It must not become a client, endpoint, request, upload, scheduler or publisher.

## 2. Preconditions

Required prior artifacts:

- `docs/runtime/sandbox/controlled-binding/EXTERNAL_SANDBOX_CONTROLLED_BINDING_PLAN.md`
- `docs/runtime/sandbox/simulation/EXTERNAL_SANDBOX_EXECUTION_SIMULATION_REVIEW.md`
- `docs/runtime/sandbox/simulation/EXTERNAL_SANDBOX_EXECUTION_SIMULATION_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_execution_simulation_gate.py`
- `OUT/audit/external_sandbox_execution_simulation_gate/final_verdict.json`
- `backend/app/creative/agents/publisher/external_sandbox_execution_simulation.py`
- `tests/sandbox/unit/test_external_sandbox_execution_simulation_unittest.py`

Required prior state:

```json
{
  "external_sandbox_execution_simulation_gate": "GO_WITH_MONITORING",
  "external_sandbox_execution_simulation_review": "ACCEPTED_WITH_MONITORING",
  "simulation_only": true,
  "all_misuse_attempts_blocked": true,
  "unblocked_attempts_count": 0,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "network_access_allowed": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "transformation_layer_authorized": false,
  "platform_content_id_emitted": false,
  "production_residuals_closed": false
}
```

## 3. Scope

In scope for the future gate:

- controlled binding contract
- provider binding status
- target platform identity governance
- binding inactive status
- credential status-only policy
- QC dependency policy
- Account Health dependency policy
- kill switch dependency policy
- rate-limit dependency policy
- no-side-effect static scan
- residual monitoring validation
- deterministic replay

Out of scope:

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
- runtime binding integration
- adapter implementation
- transformation layer
- production residual closure

## 4. Required Future Contract Shape

Future controlled binding must produce a serializable contract with at least:

```json
{
  "binding_version": "external_sandbox_controlled_binding_v1",
  "binding_type": "pre_execution_controlled_binding",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "binding_active": false,
  "provider_binding_status": "planned_not_active",
  "provider_identity_class": "abstract_sandbox_target",
  "credential_status_required": "present",
  "credential_values_accessed": false,
  "kill_switch_required": true,
  "rate_limit_policy_required": true,
  "qc_dependency_required": true,
  "account_health_dependency_required": true,
  "endpoint_defined": false,
  "http_client_defined": false,
  "platform_sdk_defined": false,
  "network_access_defined": false,
  "api_call_defined": false,
  "upload_defined": false,
  "scheduler_defined": false,
  "publish_defined": false,
  "receipt_defined": false,
  "production_identity_defined": false,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "boundary_statement": "Controlled binding is pre-execution and cannot call external services."
}
```

The future contract must not include:

- endpoint value
- URL value
- HTTP method
- headers
- body
- authorization header
- API key value
- token value
- upload path
- publish path
- scheduler job
- receipt
- `platform_content_id`

## 5. Binding Inactive Requirement

The future gate must enforce:

```json
{
  "binding_active": false,
  "execution_authority": "none",
  "transport_authority": "none",
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false
}
```

Any active binding is a blocker.

Any execution authority is a blocker.

Any transport authority is a blocker.

## 6. Provider Binding Requirements

The future binding must:

- use `provider_binding_status = planned_not_active`
- use `provider_identity_class = abstract_sandbox_target`
- reject implicit provider binding
- reject direct provider implementation
- reject production provider name
- reject provider SDK reference
- reject endpoint-bound provider identity

The future gate must fail if provider binding implies execution readiness.

## 7. Credential Requirements

The future binding may reference credential status only.

It must not access credential values.

Required checks:

- missing credential blocks
- invalid credential shape blocks
- raw secret values are not read
- raw secret values are not serialized
- authorization headers are not generated
- credential status does not imply execution readiness

## 8. Safety Dependency Requirements

The future gate must validate blocking behavior for:

- Account Health `HOLD`
- QC `HOLD`
- QC `REJECT`
- QC `publishable=false`
- missing QC trace
- missing Account Health trace
- active kill switch
- missing kill switch
- kill switch not blocking publish attempt
- kill switch not blocking external calls
- kill switch not blocking upload
- kill switch not blocking scheduler
- ambiguous rate-limit policy
- upload requests allowed
- publish requests allowed
- sandbox validation requests allowed before a later gate authorizes them

Every blocked dependency must produce:

- `binding_active = false`
- blocking reason
- rationale
- incident hook where appropriate

## 9. Static Scan Requirements

The future gate must statically scan future binding files for:

- `requests`
- `httpx`
- `aiohttp`
- `urllib.request`
- `urllib3`
- `socket`
- platform SDK imports
- endpoint constants
- URL constants
- DNS/network helpers
- upload helpers
- scheduler helpers
- publish helpers
- transformation helpers

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

## 10. Controlled Scenario Battery

The future runner must validate at least:

1. binding contract exists
2. binding remains inactive
3. target platform exact
4. target mode exact
5. no implicit provider binding
6. no real provider implementation
7. no HTTP client
8. no SDK client
9. no endpoint
10. no DNS/network access
11. no API call
12. no upload
13. no scheduler
14. no publish
15. no URL
16. no `platform_content_id`
17. no receipt
18. no credential value access
19. missing credentials block
20. invalid credentials block
21. Account Health HOLD blocks
22. QC HOLD blocks
23. QC REJECT blocks
24. QC `publishable=false` blocks
25. kill switch active blocks
26. kill switch missing blocks
27. rate-limit ambiguity blocks
28. transformation layer absent
29. fake success terms absent
30. production residuals remain open
31. deterministic replay
32. Strategy/QC/Account Health/Orchestrator/core unchanged

The runner may add stricter scenarios.

It must not omit these.

## 11. Checklist

The future runner checklist must include:

- preconditions present
- controlled binding implementation present
- binding contract serializable
- binding inactive
- target platform exact
- target mode exact
- provider binding planned but inactive
- provider identity abstract
- no implicit provider binding
- no direct provider implementation
- no HTTP client
- no SDK client
- no endpoint
- no DNS/network access
- no API call
- no upload
- no scheduler
- no real publish
- no URL
- no `platform_content_id`
- no receipt
- no credential value access
- missing credentials block
- invalid credentials block
- Account Health HOLD blocks
- QC non-publishable states block
- kill switch unsafe states block
- rate-limit unsafe states block
- no transformation layer
- no fake success terms
- deterministic replay
- production residuals remain open
- Strategy/QC/Account Health/Orchestrator/core unchanged

## 12. Required Future Artifacts

The future runner must generate:

```text
OUT/audit/external_sandbox_controlled_binding_gate/final_verdict.json
OUT/audit/external_sandbox_controlled_binding_gate/checklist_results.json
OUT/audit/external_sandbox_controlled_binding_gate/scenario_outputs.json
OUT/audit/external_sandbox_controlled_binding_gate/metrics.json
OUT/audit/external_sandbox_controlled_binding_gate/provider_binding_review.json
OUT/audit/external_sandbox_controlled_binding_gate/side_effect_review.json
OUT/audit/external_sandbox_controlled_binding_gate/security_review.json
OUT/audit/external_sandbox_controlled_binding_gate/residual_monitoring_review.json
OUT/audit/external_sandbox_controlled_binding_gate/static_scan_review.json
OUT/audit/external_sandbox_controlled_binding_gate/determinism_review.json
```

## 13. Metrics

Future metrics must include:

```json
{
  "critical_failures": 0,
  "blocking_failures_count": 0,
  "scenario_count": 32,
  "scenario_pass_count": 32,
  "checklist_count": 0,
  "checklist_pass_count": 0,
  "binding_active": false,
  "external_call_authorized": false,
  "http_client_detected": false,
  "platform_sdk_detected": false,
  "endpoint_detected": false,
  "dns_or_network_detected": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "url_emitted": false,
  "platform_content_id_emitted": false,
  "receipt_emitted": false,
  "credential_value_accessed": false,
  "transformation_layer_detected": false,
  "production_residuals_closed": false,
  "silent_failures_detected": false
}
```

`checklist_count` and `checklist_pass_count` must be populated by the runner with real values.

## 14. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

Expected future verdict:

- `GO_WITH_MONITORING`

`GO` is not expected because controlled binding is still pre-execution and does not produce production evidence.

## 15. HOLD Conditions

The future runner must return `HOLD` if:

- binding becomes active
- execution authority appears
- transport authority appears
- external call is authorized
- HTTP client appears
- SDK client appears
- endpoint appears
- DNS/network access appears
- API call is allowed
- upload is authorized
- scheduler is authorized
- real publish is authorized
- URL is emitted
- `platform_content_id` is emitted
- receipt is emitted
- credential value is accessed
- authorization header is generated
- transformation layer appears
- fake success status appears
- provider binding implies execution readiness
- Account Health HOLD is bypassed
- QC non-publishable is bypassed
- kill switch unsafe state is bypassed
- rate-limit unsafe state is bypassed
- production residual is closed
- Strategy, QC, Account Health, Orchestrator or core pipeline are modified

## 16. Residual Monitoring Rules

Required production residuals remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

The future controlled binding gate may reduce only:

- provider binding ambiguity
- binding precondition ambiguity
- safety dependency ambiguity
- controlled binding contract uncertainty

It must not reduce:

- production publish evidence residual
- platform integration residual
- production result history residual
- external sandbox execution residual
- post-publish metric residual
- attribution causality residual

## 17. Final Verdict Schema

Future `final_verdict.json` must include:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "EXTERNAL_SANDBOX_CONTROLLED_BINDING_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "binding_implemented": true,
  "binding_active": false,
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "provider_binding_status": "planned_not_active",
  "provider_identity_class": "abstract_sandbox_target",
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
  "transformation_layer_authorized": false,
  "production_residuals_closed": false,
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_EXTERNAL_SANDBOX_CONTROLLED_BINDING_IMPLEMENTATION | HOLD_BEFORE_NEXT_STEP"
}
```

## 18. Final Criteria

The future gate passes only if:

```json
{
  "binding_active": false,
  "provider_binding_status": "planned_not_active",
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "url_authorized": false,
  "platform_content_id_authorized": false,
  "receipt_authorized": false,
  "credential_value_accessed": false,
  "transformation_layer_authorized": false,
  "production_residuals_remain_open": true,
  "boundary_preserved": true
}
```

## 19. Next Authorized Step

After this gate specification is accepted, the next authorized step is the offline-only controlled binding implementation slice.

Implementation remains forbidden until this document is accepted.

The future runner path is:

```text
tests/gates/sandbox/run_external_sandbox_controlled_binding_gate.py
```

External call remains unauthorized.

HTTP client remains unauthorized.

SDK client remains unauthorized.

Endpoint remains unauthorized.

DNS/network access remains unauthorized.

API call remains unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Publish remains unauthorized.

URL and `platform_content_id` remain unauthorized.

Receipt remains unauthorized.

Production residual closure remains unauthorized.
