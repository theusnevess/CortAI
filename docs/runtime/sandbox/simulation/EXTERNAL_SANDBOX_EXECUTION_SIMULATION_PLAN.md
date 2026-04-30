# EXTERNAL_SANDBOX_EXECUTION_SIMULATION_PLAN

## 1. Purpose

`EXTERNAL_SANDBOX_EXECUTION_SIMULATION_PLAN` defines the next Phase 3 Publisher safety step after the external sandbox validation envelope implementation gate review.

This is a planning artifact only.

It does not create code, create tests, create a runner, execute tests, call external services, call platform APIs, create HTTP clients, create SDK clients, configure endpoints, access DNS/network, upload content, transfer media bytes, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, collect post-publish metrics, close production residuals, modify Publisher runtime execution, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The purpose is to define how future simulation will test misuse attempts without side effects.

Final principle:

> Execution simulation must prove that abuse stays blocked. It must not become execution.

## 2. Starting State

Canonical prior state:

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

Required prior artifacts:

- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE_REVIEW.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_request_envelope_implementation_gate.py`
- `OUT/audit/external_sandbox_request_envelope_implementation_gate/final_verdict.json`
- `backend/app/creative/agents/publisher/external_sandbox_validation_envelope.py`
- `backend/app/creative/agents/publisher/external_sandbox_envelope_security.py`
- `tests/sandbox/unit/test_external_sandbox_validation_envelope_unittest.py`

## 3. Scope

In scope for future simulation planning:

- offline simulation model
- misuse attempt modeling
- envelope-to-request transformation rejection
- readiness misinterpretation rejection
- fake sandbox receipt rejection
- fake production receipt rejection
- forbidden transport field injection rejection
- forbidden identity field injection rejection
- residual closure attempt rejection
- deterministic simulation result shape
- simulation incident hooks
- simulation audit artifacts

Out of scope:

- external call
- platform API
- HTTP client
- platform SDK
- endpoint
- DNS/network access
- upload
- media byte transfer
- scheduler
- real publishing
- production URL
- production `platform_content_id`
- production receipt
- post-publish metrics
- attribution causality
- runtime integration
- Orchestrator wiring
- adapter binding
- transformation layer from envelope to request

## 4. Non-Negotiable Constraints

The simulation stage must preserve:

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

The simulation must not create:

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

## 5. Simulation Definition

Execution simulation means:

> A deterministic offline evaluation of whether a hypothetical action would be blocked by the existing governance and envelope safety boundaries.

Execution simulation does not mean:

- dry-run API call
- sandbox API call
- local HTTP mock server
- fake platform adapter
- SDK test mode
- upload simulation using media bytes
- scheduler simulation using a queue
- platform receipt fabrication
- post-publish metrics simulation

The simulation result must be an audit object, not a request object and not a platform result.

## 6. Future Simulation Object Boundary

Future implementation may define only inert simulation structures after a separate implementation gate.

Preferred naming:

- `ExternalSandboxExecutionSimulation`
- `ExternalSandboxExecutionSimulationInput`
- `ExternalSandboxExecutionSimulationResult`
- `ExternalSandboxMisuseAttempt`
- `ExternalSandboxSimulationIncidentHook`

Forbidden naming:

- `ExternalSandboxExecutor`
- `ExternalSandboxRequestExecutor`
- `ExternalSandboxHttpClient`
- `PlatformSandboxClient`
- `SandboxUploader`
- `PublisherScheduler`
- any name implying transport or execution authority

Future files must not be created until a simulation implementation gate is accepted.

## 7. Misuse Attempts To Simulate

The future simulation must include adversarial misuse attempts.

Minimum misuse scenarios:

1. transform envelope into request
2. call `requests.post(..., json=envelope.to_dict())`
3. interpret `envelope_valid=true` as readiness
4. interpret `eligible_for_future_external_sandbox_validation` as execution permission
5. inject `endpoint`
6. inject `headers`
7. inject `body`
8. inject `method`
9. inject URL
10. inject `published_url`
11. inject `platform_content_id`
12. inject production receipt
13. inject sandbox receipt that resembles production
14. inject media bytes
15. inject upload URL
16. inject scheduler job ID
17. inject post-publish metrics reference
18. inject expected performance claim
19. inject attribution causal claim
20. close production residual using simulation result
21. treat simulation pass as publish success
22. treat simulation pass as external sandbox validation success
23. treat simulation pass as production evidence
24. bypass QC non-publishable
25. bypass Account Health HOLD
26. bypass kill switch
27. bypass disabled rate limit
28. implicit provider binding
29. mixed mode
30. secret-like field injection

Every misuse attempt must produce:

- `blocked = true`
- `external_call_authorized = false`
- `upload_authorized = false`
- `scheduler_authorized = false`
- `real_publish_authorized = false`
- reason code
- rationale
- incident hook where severity warrants it

## 8. Simulation Result Shape

Future simulation result must be serializable:

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

The result must not include:

- endpoint
- headers
- body
- method
- request payload
- transport payload
- media bytes
- URL
- production platform ID
- production receipt
- post-publish metrics

## 9. Readiness Semantics

The simulation must distinguish:

- `envelope_schema_valid`
- `simulation_executed_offline`
- `misuse_blocked`
- `simulation_passed`
- `external_validation_authorized`
- `external_validation_attempted`
- `real_publish_authorized`
- `real_publish_attempted`

Required semantics:

```json
{
  "envelope_schema_valid": "schema only",
  "simulation_passed": "misuse attempts blocked offline",
  "external_validation_authorized": false,
  "external_validation_attempted": false,
  "real_publish_authorized": false,
  "real_publish_attempted": false
}
```

`simulation_passed=true` must not mean:

- ready to call external API
- ready to upload
- ready to publish
- platform validation succeeded
- production evidence exists

## 10. Fake Receipt Rules

The simulation must not generate a receipt that can be mistaken for production.

Forbidden:

- production receipt
- platform receipt
- platform URL
- platform content ID
- external identity
- receipt evidence marked production
- sandbox receipt represented as success

Allowed:

- local misuse simulation incident hook
- local blocked-attempt record
- local deterministic simulation ID

If any attempted input contains a receipt-like field:

- mark as blocked
- emit incident hook
- redact value
- keep `result_evidence_is_production=false`
- keep production residuals open

## 11. Residual Monitoring Rules

Required production residuals remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

Simulation may reduce only:

- misuse simulation uncertainty
- readiness misinterpretation uncertainty
- fake receipt defense uncertainty
- residual closure defense uncertainty
- transformation misuse defense uncertainty

Simulation must not reduce:

- production publish evidence residual
- platform integration residual
- production result history residual
- external sandbox execution residual
- post-publish metric residual
- attribution causality residual

Any attempt to close production residuals from simulation evidence is a blocker.

## 12. Incident Hooks

Future simulation must support incident hooks for:

- `EXTERNAL_SANDBOX_SIMULATION_REQUEST_TRANSFORMATION_ATTEMPT`
- `EXTERNAL_SANDBOX_SIMULATION_READINESS_MISINTERPRETATION`
- `EXTERNAL_SANDBOX_SIMULATION_FAKE_RECEIPT_ATTEMPT`
- `EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_TRANSPORT_FIELD`
- `EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_PLATFORM_IDENTITY`
- `EXTERNAL_SANDBOX_SIMULATION_RESIDUAL_CLOSURE_ATTEMPT`
- `EXTERNAL_SANDBOX_SIMULATION_QC_BYPASS_ATTEMPT`
- `EXTERNAL_SANDBOX_SIMULATION_ACCOUNT_HEALTH_BYPASS_ATTEMPT`
- `EXTERNAL_SANDBOX_SIMULATION_KILL_SWITCH_BYPASS_ATTEMPT`
- `EXTERNAL_SANDBOX_SIMULATION_RATE_LIMIT_BYPASS_ATTEMPT`
- `EXTERNAL_SANDBOX_SIMULATION_SECRET_LEAKAGE_ATTEMPT`

Incident hooks must not include:

- secrets
- tokens
- endpoint
- headers
- body
- media bytes
- URL
- platform content ID
- production receipt

## 13. Determinism Requirements

Future simulation must be deterministic.

Required:

- same envelope + same misuse scenario set -> same simulation result
- stable ordering of misuse attempts
- stable ordering of reason codes
- no random IDs
- no generated timestamps unless supplied as input
- no environment-derived values
- no network-derived values
- no filesystem side effects except audit artifacts in future gate runner

## 14. Controlled Scenario Battery

Future simulation implementation gate must include at least:

1. clean envelope simulation remains offline
2. envelope-to-request transformation attempt blocked
3. `requests.post` misuse modeled and blocked without importing requests
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
24. QC non-publishable bypass blocked
25. Account Health HOLD bypass blocked
26. kill switch bypass blocked
27. rate-limit bypass blocked
28. implicit provider binding blocked
29. mixed mode blocked
30. secret-like field blocked and redacted
31. deterministic replay
32. no HTTP client import
33. no SDK import
34. no endpoint constants
35. no network/DNS access

## 15. Checklist For Future Gate

The future gate must validate:

- simulation-only result shape
- no transport transformation layer
- no HTTP client
- no SDK client
- no endpoint
- no DNS/network access
- no upload
- no scheduler
- no real publish
- no platform URL
- no platform content ID
- no production receipt
- no simulated receipt resembling production
- all misuse attempts blocked
- readiness misuse blocked
- fake success blocked
- residual closure attempt blocked
- QC bypass blocked
- Account Health HOLD bypass blocked
- kill switch bypass blocked
- rate-limit bypass blocked
- no secret leakage
- deterministic replay
- production residuals remain open

## 16. Failure Conditions

Immediate `HOLD` if future simulation plan, implementation or gate:

- creates HTTP client
- imports `requests`, `httpx`, `aiohttp`, `urllib.request`, `urllib3`, `socket` or platform SDK
- defines endpoint
- defines URL
- creates headers
- creates body
- creates request payload
- creates transport payload
- creates transformation layer from envelope to request
- performs external call
- performs upload
- invokes scheduler
- publishes content
- emits production URL
- emits production `platform_content_id`
- emits production receipt
- marks simulation evidence as production evidence
- treats simulation pass as platform validation
- treats simulation pass as publish success
- closes production residuals
- bypasses QC non-publishable
- bypasses Account Health HOLD
- mutates Strategy, QC, Account Health, Orchestrator or core pipeline

## 17. Required Future Artifacts

Before implementation:

- `docs/runtime/sandbox/simulation/EXTERNAL_SANDBOX_EXECUTION_SIMULATION_GATE.md`

After implementation is authorized:

- future simulation implementation files, names to be defined by the gate
- future tests, names to be defined by the gate
- `tests/gates/sandbox/run_external_sandbox_execution_simulation_gate.py`

Future audit output:

- `OUT/audit/external_sandbox_execution_simulation_gate/final_verdict.json`
- `OUT/audit/external_sandbox_execution_simulation_gate/checklist_results.json`
- `OUT/audit/external_sandbox_execution_simulation_gate/scenario_outputs.json`
- `OUT/audit/external_sandbox_execution_simulation_gate/metrics.json`
- `OUT/audit/external_sandbox_execution_simulation_gate/misuse_attempt_review.json`
- `OUT/audit/external_sandbox_execution_simulation_gate/anti_fake_success_review.json`
- `OUT/audit/external_sandbox_execution_simulation_gate/side_effect_review.json`
- `OUT/audit/external_sandbox_execution_simulation_gate/residual_monitoring_review.json`

## 18. Expected Verdict

Expected future gate result:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "simulation_only": true,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "network_access_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "transformation_layer_authorized": false,
  "production_residuals_closed": false
}
```

`GO` is not expected because simulation is not production evidence and does not enable external execution.

## 19. Exit Criteria

This plan is acceptable only if:

```json
{
  "simulation_planned": true,
  "simulation_implemented": false,
  "simulation_only": true,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "network_access_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "transformation_layer_authorized": false,
  "misuse_attempts_required": true,
  "fake_success_blocked_by_design": true,
  "production_residuals_remain_open": true
}
```

## 20. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

```text
docs/runtime/sandbox/simulation/EXTERNAL_SANDBOX_EXECUTION_SIMULATION_GATE.md
```

Do not implement simulation before that gate exists.

Do not create runner before that gate exists.

Do not create HTTP client, SDK, endpoint, upload, scheduler, platform API call or real publishing path.

External execution remains unauthorized.
