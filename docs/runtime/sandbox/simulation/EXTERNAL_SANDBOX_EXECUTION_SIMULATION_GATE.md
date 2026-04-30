# EXTERNAL_SANDBOX_EXECUTION_SIMULATION_GATE

## 1. Purpose

`EXTERNAL_SANDBOX_EXECUTION_SIMULATION_GATE` freezes the executable acceptance contract for the future offline external sandbox execution simulation.

This is a gate specification artifact.

It does not create code, create tests, create a runner, execute tests, call external services, call platform APIs, create HTTP clients, create SDK clients, configure endpoints, access DNS/network, upload content, transfer media bytes, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, collect post-publish metrics, close production residuals, modify Publisher runtime execution, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The gate exists to prove the future simulation cannot become execution.

Final principle:

> Simulation may model abuse. It must not execute abuse.

## 2. Preconditions

Required prior artifacts:

- `docs/runtime/sandbox/simulation/EXTERNAL_SANDBOX_EXECUTION_SIMULATION_PLAN.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE_REVIEW.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_request_envelope_implementation_gate.py`
- `OUT/audit/external_sandbox_request_envelope_implementation_gate/final_verdict.json`
- `backend/app/creative/agents/publisher/external_sandbox_validation_envelope.py`
- `backend/app/creative/agents/publisher/external_sandbox_envelope_security.py`
- `tests/sandbox/unit/test_external_sandbox_validation_envelope_unittest.py`

Required prior state:

```json
{
  "external_sandbox_request_envelope_implementation_gate": "GO_WITH_MONITORING",
  "external_sandbox_request_envelope_implementation_gate_review": "ACCEPTED_WITH_MONITORING",
  "envelope_state": "INERT_VALIDATION_OBJECT",
  "transport_capability": "none",
  "execution_capability": "none",
  "non_transportable": true,
  "external_call_authorized": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "production_residuals_closed": false
}
```

## 3. Scope

In scope for the future gate:

- simulation-only contract
- misuse scenario battery
- fake success prevention
- readiness misuse prevention
- transformation layer prohibition
- static scan for HTTP/SDK/endpoint/DNS
- side-effect review
- residual monitoring review
- deterministic replay review
- incident hook review

Out of scope:

- external calls
- platform API
- HTTP clients
- SDK clients
- endpoint configuration
- DNS/network access
- upload
- scheduler
- real publishing
- URL generation
- platform content ID generation
- platform receipt generation
- post-publish metrics
- attribution causality
- Orchestrator integration
- adapter binding
- runtime execution path changes

## 4. Required Future Files

After this gate specification is accepted, a future implementation plan may authorize simulation files.

The gate itself does not authorize code.

Suggested future files, subject to a separate implementation plan:

```text
backend/app/creative/agents/publisher/external_sandbox_execution_simulation.py
tests/sandbox/unit/test_external_sandbox_execution_simulation_unittest.py
tests/gates/sandbox/run_external_sandbox_execution_simulation_gate.py
```

No future file may introduce HTTP, SDK, endpoint, DNS, upload, scheduler or publish behavior.

## 5. Simulation Boundary

The future simulation must preserve:

```json
{
  "simulation_only": true,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "network_access_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "transformation_layer_authorized": false
}
```

The simulation must never create:

- request object
- transport payload
- endpoint config
- HTTP method
- headers
- body
- URL
- platform ID
- upload job
- scheduler job
- platform receipt
- production evidence

## 6. Required Result Shape

The future simulation result must include:

```json
{
  "simulation_version": "external_sandbox_execution_simulation_v1",
  "simulation_type": "offline_misuse_and_blocking_simulation",
  "simulation_only": true,
  "run_id": "...",
  "content_id": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "envelope_ref": "...",
  "misuse_attempts": [],
  "blocked_attempts_count": 0,
  "unblocked_attempts_count": 0,
  "simulation_passed": true,
  "simulation_passed_meaning": "misuse_attempts_blocked_offline",
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "network_access_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "transformation_layer_authorized": false,
  "simulated_receipt_generated": false,
  "production_receipt_generated": false,
  "published_url": null,
  "platform_content_id": null,
  "result_evidence_is_production": false,
  "production_residuals_closed": false,
  "incident_hooks": [],
  "rationale": [],
  "boundary_statement": "External sandbox execution simulation is offline only and cannot execute."
}
```

`simulation_passed=true` means only:

> misuse attempts were blocked offline.

It must not mean:

- external validation readiness
- platform validation success
- publish readiness
- publish success
- production evidence
- residual closure

## 7. Required Misuse Scenario Battery

The future runner must validate at least:

1. clean envelope simulation remains offline
2. envelope-to-request transformation attempt blocked
3. `requests.post(..., json=envelope.to_dict())` misuse modeled and blocked without importing requests
4. `envelope_valid=true` readiness misuse blocked
5. future eligibility misuse blocked
6. endpoint injection blocked
7. headers injection blocked
8. body injection blocked
9. method injection blocked
10. URL injection blocked
11. `published_url` injection blocked
12. `platform_content_id` injection blocked
13. production receipt injection blocked
14. sandbox receipt resembling production blocked
15. media bytes injection blocked
16. upload URL injection blocked
17. scheduler job injection blocked
18. post-publish metrics injection blocked
19. performance prediction injection blocked
20. attribution causal claim injection blocked
21. residual closure attempt blocked
22. simulation pass not treated as success
23. simulation pass not treated as platform validation
24. simulation pass not treated as readiness
25. QC non-publishable bypass blocked
26. Account Health HOLD bypass blocked
27. kill switch bypass blocked
28. disabled rate-limit bypass blocked
29. implicit provider binding blocked
30. mixed mode blocked
31. secret-like field blocked and redacted
32. deterministic replay
33. no HTTP client import
34. no SDK import
35. no endpoint constants
36. no DNS/network access
37. no upload/scheduler/publish symbols
38. production residuals remain open

The future runner may add stricter scenarios.

It must not omit these scenarios.

## 8. Misuse Attempt Record Shape

Each misuse attempt must include:

```json
{
  "attempt_id": "...",
  "attempt_type": "...",
  "attempt_description": "...",
  "blocked": true,
  "reason_code": "...",
  "severity": "monitorable | warning | critical",
  "external_call_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "result_evidence_is_production": false,
  "rationale": []
}
```

Any misuse attempt with `blocked=false` is a gate blocker.

## 9. Static Scan Requirements

The future gate must statically scan future simulation files for:

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
- request transformation helpers

Forbidden helper names include:

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

## 10. Checklist

The future runner checklist must include:

- preconditions present
- simulation implementation present
- simulation-only result shape
- all misuse attempts present
- all misuse attempts blocked
- no transformation layer
- no HTTP client
- no SDK client
- no endpoint
- no DNS/network access
- no upload
- no scheduler
- no real publish
- no URL
- no platform content ID
- no production receipt
- no simulated receipt resembling production
- `simulation_passed` meaning bounded
- readiness misuse blocked
- fake success blocked
- residual closure attempt blocked
- QC bypass blocked
- Account Health HOLD bypass blocked
- kill switch bypass blocked
- rate-limit bypass blocked
- no secret leakage
- incident hooks present where required
- deterministic replay
- production residuals remain open
- Strategy/QC/Account Health/Orchestrator/core unchanged

## 11. Required Future Output Artifacts

The future runner must generate:

```text
OUT/audit/external_sandbox_execution_simulation_gate/final_verdict.json
OUT/audit/external_sandbox_execution_simulation_gate/checklist_results.json
OUT/audit/external_sandbox_execution_simulation_gate/scenario_outputs.json
OUT/audit/external_sandbox_execution_simulation_gate/metrics.json
OUT/audit/external_sandbox_execution_simulation_gate/misuse_attempt_review.json
OUT/audit/external_sandbox_execution_simulation_gate/anti_fake_success_review.json
OUT/audit/external_sandbox_execution_simulation_gate/static_scan_review.json
OUT/audit/external_sandbox_execution_simulation_gate/side_effect_review.json
OUT/audit/external_sandbox_execution_simulation_gate/determinism_review.json
OUT/audit/external_sandbox_execution_simulation_gate/residual_monitoring_review.json
```

## 12. Metrics

Future metrics must include:

```json
{
  "critical_failures": 0,
  "blocking_failures_count": 0,
  "scenario_count": 38,
  "scenario_pass_count": 38,
  "checklist_count": 0,
  "checklist_pass_count": 0,
  "simulation_only": true,
  "all_misuse_attempts_blocked": true,
  "unblocked_attempts_count": 0,
  "external_call_authorized": false,
  "http_client_detected": false,
  "platform_sdk_detected": false,
  "endpoint_detected": false,
  "dns_or_network_detected": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "transformation_layer_detected": false,
  "fake_success_detected": false,
  "fake_receipt_detected": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "production_residuals_closed": false,
  "silent_failures_detected": false
}
```

`checklist_count` and `checklist_pass_count` must be populated by the runner with real values.

## 13. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

Expected future verdict:

- `GO_WITH_MONITORING`

`GO` is not expected because simulation is not production evidence and does not authorize external execution.

## 14. HOLD Conditions

The future runner must return `HOLD` if:

- any required misuse scenario is missing
- any misuse attempt is unblocked
- simulation creates a request object
- simulation creates transport payload
- simulation creates transformation layer
- HTTP client appears
- SDK client appears
- endpoint appears
- DNS/network access appears
- upload is authorized
- scheduler is authorized
- real publish is authorized
- URL is emitted
- platform content ID is emitted
- receipt is generated
- production evidence is claimed
- `simulation_passed` is treated as readiness
- `simulation_passed` is treated as publish success
- `simulation_passed` is treated as platform validation success
- production residual is closed
- QC non-publishable is bypassed
- Account Health HOLD is bypassed
- kill switch is bypassed
- rate-limit block is bypassed
- secret value leaks
- Strategy, QC, Account Health, Orchestrator or core pipeline are modified

## 15. Residual Monitoring Rules

These production residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

The future simulation gate may reduce only:

- misuse simulation uncertainty
- readiness misinterpretation uncertainty
- fake receipt defense uncertainty
- residual closure defense uncertainty
- transformation misuse defense uncertainty

It must not reduce:

- production publish evidence residual
- real platform integration residual
- production result history residual
- external sandbox execution residual
- post-publish metric residual
- attribution causality residual

## 16. Final Verdict Schema

Future `final_verdict.json` must include:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "EXTERNAL_SANDBOX_EXECUTION_SIMULATION_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "simulation_only": true,
  "simulation_implemented": true,
  "all_misuse_attempts_blocked": true,
  "unblocked_attempts_count": 0,
  "simulation_passed_meaning": "misuse_attempts_blocked_offline",
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "network_access_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "transformation_layer_authorized": false,
  "simulated_receipt_generated": false,
  "production_receipt_generated": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "result_evidence_is_production": false,
  "production_residuals_closed": false,
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_EXTERNAL_SANDBOX_EXECUTION_SIMULATION_IMPLEMENTATION | HOLD_BEFORE_NEXT_STEP"
}
```

## 17. Final Criteria

The future gate passes only if:

```json
{
  "simulation_only": true,
  "all_misuse_attempts_blocked": true,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "network_access_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "transformation_layer_authorized": false,
  "simulation_passed_not_readiness": true,
  "simulation_passed_not_success": true,
  "production_residuals_remain_open": true,
  "boundary_preserved": true
}
```

## 18. Next Authorized Step

After this gate specification is accepted, the next authorized step is the offline-only simulation implementation slice.

Implementation remains forbidden until this document is accepted.

The future runner path is:

```text
tests/gates/sandbox/run_external_sandbox_execution_simulation_gate.py
```

External calls remain unauthorized.

HTTP clients remain unauthorized.

Platform SDKs remain unauthorized.

Endpoint configuration remains unauthorized.

DNS/network behavior remains unauthorized.

Transformation layer remains unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Real publishing remains unauthorized.

Production URL and production `platform_content_id` remain unauthorized.
