# EXTERNAL_SANDBOX_CONTROLLED_BINDING_PLAN

## 1. Purpose

`EXTERNAL_SANDBOX_CONTROLLED_BINDING_PLAN` defines the pre-execution plan for a future controlled external sandbox binding.

This is a planning artifact only.

It does not create code, create tests, create a runner, execute tests, call external services, call platform APIs, create HTTP clients, create SDK clients, configure endpoints, access DNS/network, upload content, transfer media bytes, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, collect post-publish metrics, close production residuals, modify Publisher runtime execution, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The purpose is to define how a future sandbox binding may be specified without granting execution authority.

Final principle:

> Controlled binding defines who could be bound later. It does not bind execution now.

## 2. Starting State

Canonical prior state:

```json
{
  "external_sandbox_execution_simulation_gate": "GO_WITH_MONITORING",
  "external_sandbox_execution_simulation_review": "ACCEPTED_WITH_MONITORING",
  "simulation_only": true,
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
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "production_residuals_closed": false
}
```

Required prior artifacts:

- `docs/runtime/sandbox/simulation/EXTERNAL_SANDBOX_EXECUTION_SIMULATION_REVIEW.md`
- `docs/runtime/sandbox/simulation/EXTERNAL_SANDBOX_EXECUTION_SIMULATION_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_execution_simulation_gate.py`
- `OUT/audit/external_sandbox_execution_simulation_gate/final_verdict.json`
- `backend/app/creative/agents/publisher/external_sandbox_execution_simulation.py`
- `tests/sandbox/unit/test_external_sandbox_execution_simulation_unittest.py`

## 3. Scope

In scope for this plan:

- controlled binding concept
- future provider binding contract
- target platform identity governance
- binding preconditions
- secret status requirements
- kill switch requirements
- rate-limit requirements
- QC and Account Health dependency requirements
- allowed future gate structure
- failure conditions
- residual monitoring rules

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
- runtime binding implementation
- adapter implementation
- transformation layer
- production residual closure

## 4. Controlled Binding Definition

Controlled binding means:

> A governed, audit-only association between `SHORT_VIDEO_PLATFORM_SANDBOX_V1`, `sandbox_external_dry_run`, credential status, safety policies and future execution prerequisites.

Controlled binding does not mean:

- platform client
- HTTP client
- SDK client
- endpoint config
- credential usage
- external sandbox validation
- upload capability
- scheduler capability
- publish capability
- platform identity
- receipt evidence

The binding is a policy object, not an execution object.

## 5. Non-Negotiable Constraints

This plan preserves:

```json
{
  "pre_execution_only": true,
  "binding_planned": true,
  "binding_implemented": false,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "network_access_allowed": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "url_authorized": false,
  "platform_content_id_authorized": false,
  "receipt_authorized": false,
  "production_residual_closure_authorized": false
}
```

Any artifact that changes one of these values requires a separate gate and explicit approval.

## 6. Target Binding Identity

The only target allowed at this planning stage:

```json
{
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "binding_stage": "pre_execution_controlled_binding",
  "binding_active": false,
  "execution_authority": "none",
  "transport_authority": "none"
}
```

The binding must not introduce:

- real provider name
- production provider name
- API base URL
- endpoint
- region-specific endpoint
- upload URL
- OAuth URL
- scheduler URL
- production account ID
- platform content ID

## 7. Future Binding Contract Shape

A future controlled binding may define a serializable contract similar to:

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
  "upload_defined": false,
  "scheduler_defined": false,
  "publish_defined": false,
  "receipt_defined": false,
  "production_identity_defined": false,
  "boundary_statement": "Controlled binding is pre-execution and cannot call external services."
}
```

This shape is a future contract target, not current implementation authorization.

## 8. Provider Binding Rules

Future provider binding must be explicit, abstract and non-executable.

Allowed:

- abstract sandbox target identity
- provider binding status
- credential presence/status requirement
- safety policy references
- kill switch requirement
- rate-limit policy requirement
- audit rationale

Forbidden:

- direct provider implementation
- real provider API name
- SDK class
- endpoint
- HTTP method
- headers
- request body
- upload path
- publish path
- OAuth scope usage
- credential value usage
- platform account execution identity

No implicit provider binding is allowed.

Any future provider-specific binding requires a separate provider-binding gate.

## 9. Credential Boundary

Controlled binding may require credential status.

It must not read, log, serialize, validate against platform or use credential values.

Allowed credential fields:

```json
{
  "credential_status": "present | missing | invalid_shape | not_checked",
  "credential_source": "environment_or_secret_manager",
  "secret_values_logged": false,
  "secret_values_persisted": false,
  "secret_values_accessed": false,
  "secret_scope_class": "sandbox_binding_planning_only"
}
```

Missing or invalid credentials must block future execution eligibility.

They must not trigger secret access.

## 10. Safety Dependencies

Future binding must require:

- QC trace reference
- QC decision not `HOLD`
- QC decision not `REJECT`
- QC `publishable=true`
- Account Health decision not `HOLD`
- kill switch present
- kill switch not active
- kill switch blocks publish attempt
- kill switch blocks external calls
- kill switch blocks upload
- kill switch blocks scheduler
- rate-limit policy present
- sandbox validation requests disabled unless later gate authorizes them
- upload requests disabled
- publish requests disabled

Failure of any dependency must produce:

- `binding_active = false`
- blocking reason
- rationale
- incident hook where applicable

## 11. Transformation Boundary

Controlled binding must not create a transformation layer from:

- validation envelope to request
- simulation result to request
- binding contract to request
- metadata projection to HTTP body
- credential status to authorization header

Any future transformation layer requires:

- separate plan
- separate gate
- separate implementation
- separate side-effect review

## 12. Anti-Fake-Success Rules

Controlled binding must not produce:

- success
- publish success
- platform validation success
- external sandbox validation success
- receipt
- URL
- platform content ID
- production evidence

Allowed statuses:

- `planned_not_active`
- `blocked`
- `not_authorized`
- `not_implemented`

Forbidden statuses:

- `validated`
- `executed`
- `sent`
- `uploaded`
- `published`
- `succeeded`
- `receipt_obtained`

## 13. Residual Monitoring Rules

Required production residuals remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

Controlled binding planning may reduce only:

- provider binding ambiguity
- binding precondition ambiguity
- safety dependency ambiguity
- future gate design ambiguity

It must not reduce:

- production publish evidence residual
- platform integration residual
- production result history residual
- external sandbox execution residual
- post-publish metrics residual
- attribution causality residual

## 14. Controlled Scenario Requirements For Future Gate

Future controlled binding gate must validate:

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

## 15. Future Artifacts

Next artifact after this plan:

```text
docs/runtime/sandbox/controlled-binding/EXTERNAL_SANDBOX_CONTROLLED_BINDING_GATE.md
```

Future runner after gate and implementation:

```text
tests/gates/sandbox/run_external_sandbox_controlled_binding_gate.py
```

Expected future audit outputs:

- `OUT/audit/external_sandbox_controlled_binding_gate/final_verdict.json`
- `OUT/audit/external_sandbox_controlled_binding_gate/checklist_results.json`
- `OUT/audit/external_sandbox_controlled_binding_gate/scenario_outputs.json`
- `OUT/audit/external_sandbox_controlled_binding_gate/metrics.json`
- `OUT/audit/external_sandbox_controlled_binding_gate/provider_binding_review.json`
- `OUT/audit/external_sandbox_controlled_binding_gate/side_effect_review.json`
- `OUT/audit/external_sandbox_controlled_binding_gate/security_review.json`
- `OUT/audit/external_sandbox_controlled_binding_gate/residual_monitoring_review.json`

## 16. HOLD Conditions

Immediate `HOLD` if any future artifact:

- creates HTTP client
- imports SDK client
- defines endpoint
- accesses DNS/network
- performs API call
- authorizes upload
- invokes scheduler
- authorizes publish
- emits URL
- emits `platform_content_id`
- emits receipt
- accesses credential value
- creates authorization header
- creates transformation layer
- treats binding as execution readiness
- treats binding as platform validation
- treats binding as publish success
- closes production residuals
- bypasses QC
- bypasses Account Health HOLD
- bypasses kill switch
- mutates Strategy, QC, Account Health, Orchestrator or core pipeline

## 17. Exit Criteria

This plan is acceptable only if:

```json
{
  "controlled_binding_planned": true,
  "binding_implemented": false,
  "pre_execution_only": true,
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "network_access_allowed": false,
  "api_call_allowed": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "url_authorized": false,
  "platform_content_id_authorized": false,
  "receipt_authorized": false,
  "production_residuals_remain_open": true
}
```

## 18. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

```text
docs/runtime/sandbox/controlled-binding/EXTERNAL_SANDBOX_CONTROLLED_BINDING_GATE.md
```

Do not implement controlled binding before that gate exists.

Do not create runner before that gate exists.

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

Production residual closure remains unauthorized.
