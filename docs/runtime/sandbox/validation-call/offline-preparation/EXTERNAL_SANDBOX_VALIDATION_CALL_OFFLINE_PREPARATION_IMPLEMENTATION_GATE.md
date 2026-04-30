# EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE

## 1. Purpose

`EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE` validates the offline/preparation-only implementation plan before any proposed file or test can be created.

This is an audit-only gate specification.

It does not authorize code, implementation tests, HTTP clients, platform SDKs, endpoints, DNS/network access, API calls, credential value access, request transformation, transport payload generation, external calls, runtime integration, upload, scheduling, publishing, production URLs, `platform_content_id`, receipts or production residual closure.

This gate validates:

```json
{
  "allowlist_exact": true,
  "allowlist_active": false,
  "implementation_authorized": false,
  "tests_authorized": false,
  "external_call_authorized": false,
  "runtime_integration_authorized": false,
  "gate_required_before_code": true
}
```

## 2. Scope

In scope:

- validation of the implementation plan
- validation of the proposed allowlist
- validation that the allowlist is inactive
- validation that implementation remains unauthorized
- validation that tests remain unauthorized
- validation of offline/preparation-only boundaries
- validation of forbidden implementation surfaces
- validation of residual monitoring integrity
- definition of a future audit-only runner contract

Out of scope:

- creating allowlisted files
- creating tests
- writing implementation code
- importing runtime modules
- modifying Publisher runtime behavior
- modifying QC, Account Health, Strategy, Orchestrator, Attribution, Experiment or core
- external calls
- network access
- transport payload generation
- request transformation
- credential value access

## 3. Preconditions

The gate may be evaluated only if all required prior artifacts exist:

- `docs/runtime/sandbox/validation-call/implementation-authorization/EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW.md`
- `docs/runtime/sandbox/validation-call/implementation-authorization/EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_validation_call_implementation_authorization_review_gate.py`
- `OUT/audit/external_sandbox_validation_call_implementation_authorization_review_gate/final_verdict.json`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_PLAN.md`

The prior review gate verdict must show:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "scenario_pass_count": "30/30",
  "checklist_pass_count": "46/46",
  "blocking_failures": [],
  "review_plan_valid": true,
  "future_review_allowed": true,
  "code_authorized": false,
  "implementation_tests_authorized": false,
  "external_call_authorized": false,
  "runtime_integration_authorized": false,
  "production_residuals_remain_open": true
}
```

## 4. Proposed Allowlist

The implementation plan may propose exactly these files:

```text
backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation.py
backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation_security.py
tests/sandbox/unit/test_external_sandbox_validation_call_preparation_unittest.py
```

No other file may be included.

This gate must fail if the plan proposes additional files.

This gate must fail if the plan omits any listed file.

This gate must fail if any file already exists before authorization unless it was created by a separate approved artifact.

This gate must fail if the allowlist is represented as active before gate acceptance.

## 5. Allowlist Status

The gate must validate:

```json
{
  "allowlist_proposed": true,
  "allowlist_exact": true,
  "allowlist_active": false,
  "implementation_authorized": false,
  "tests_authorized": false
}
```

The strongest positive outcome of this gate may authorize only a later review or implementation authorization artifact.

This gate itself does not activate the allowlist.

## 6. Required Implementation Boundary

The implementation plan must preserve:

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

Any contradiction must result in `HOLD`.

## 7. Forbidden Surface

The gate must fail if the plan permits:

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

## 8. Controlled Scenario Battery

The future runner for this gate must validate at least these scenarios:

1. `implementation_plan_exists`
2. `prior_review_gate_verdict_acceptable`
3. `allowlist_exact`
4. `allowlist_has_three_files`
5. `allowlist_has_publisher_preparation_file`
6. `allowlist_has_publisher_security_file`
7. `allowlist_has_unit_test_file`
8. `allowlist_has_no_extra_files`
9. `allowlist_active_false`
10. `implementation_authorized_false`
11. `tests_authorized_false`
12. `external_call_authorized_false`
13. `runtime_integration_authorized_false`
14. `gate_required_before_code_true`
15. `offline_only_boundary_present`
16. `preparation_only_boundary_present`
17. `non_transport_boundary_present`
18. `non_client_boundary_present`
19. `non_endpoint_boundary_present`
20. `non_network_boundary_present`
21. `non_executing_boundary_present`
22. `credential_values_inaccessible`
23. `request_transformation_forbidden`
24. `transport_payload_forbidden`
25. `http_sdk_forbidden`
26. `endpoint_dns_forbidden`
27. `upload_scheduler_publish_forbidden`
28. `url_platform_content_id_receipt_forbidden`
29. `production_residuals_remain_open`
30. `qc_health_strategy_orchestrator_core_unchanged`
31. `no_runtime_import_required`
32. `no_silent_permission_escalation`

## 9. Checklist

The future runner must check:

- all prior artifacts exist
- prior verdict JSON is valid
- prior verdict is `GO` or `GO_WITH_MONITORING`
- prior blocking failures are empty
- prior critical failures are zero
- implementation plan exists
- allowlist exact
- allowlist active is false
- implementation authorized is false
- tests authorized is false
- external call authorized is false
- runtime integration authorized is false
- gate required before code is true
- offline-only boundary exists
- preparation-only boundary exists
- no transport boundary exists
- no client boundary exists
- no endpoint boundary exists
- no network boundary exists
- no execution boundary exists
- credential values inaccessible
- forbidden surface is explicitly forbidden
- residuals remain open
- no core or agent boundary drift
- no silent permission escalation

## 10. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

`HOLD` if:

- required prior artifacts are missing
- prior gate is `HOLD`
- prior gate has blocking failures
- prior gate has critical failures
- implementation plan is missing
- allowlist is not exact
- allowlist is active
- implementation is authorized
- tests are authorized
- external call is authorized
- runtime integration is authorized
- gate required before code is not explicit
- forbidden implementation surface is permitted
- residuals are closed
- QC, Account Health, Strategy, Orchestrator, Attribution, Experiment or core boundary drifts
- silent permission escalation is detected

`GO_WITH_MONITORING` if:

- all critical checks pass
- allowlist is exact but inactive
- implementation remains unauthorized
- tests remain unauthorized
- external calls remain unauthorized
- runtime integration remains unauthorized
- production residuals remain open

`GO` is reserved for a future state with no meaningful monitoring residuals.

Expected likely verdict is `GO_WITH_MONITORING`.

The verdict must not be hardcoded.

## 11. Required Future Output Artifacts

If a runner is later created for this gate, it must write:

- `OUT/audit/external_sandbox_validation_call_offline_preparation_implementation_gate/final_verdict.json`
- `OUT/audit/external_sandbox_validation_call_offline_preparation_implementation_gate/checklist_results.json`
- `OUT/audit/external_sandbox_validation_call_offline_preparation_implementation_gate/scenario_outputs.json`
- `OUT/audit/external_sandbox_validation_call_offline_preparation_implementation_gate/metrics.json`
- `OUT/audit/external_sandbox_validation_call_offline_preparation_implementation_gate/allowlist_review.json`
- `OUT/audit/external_sandbox_validation_call_offline_preparation_implementation_gate/non_authorization_review.json`
- `OUT/audit/external_sandbox_validation_call_offline_preparation_implementation_gate/forbidden_surface_review.json`
- `OUT/audit/external_sandbox_validation_call_offline_preparation_implementation_gate/residual_monitoring_review.json`
- `OUT/audit/external_sandbox_validation_call_offline_preparation_implementation_gate/boundary_review.json`

No runner is created by this document.

## 12. Final Verdict Schema

The future `final_verdict.json` must include:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "allowlist_exact": true,
  "allowlist_active": false,
  "implementation_authorized": false,
  "tests_authorized": false,
  "external_call_authorized": false,
  "runtime_integration_authorized": false,
  "gate_required_before_code": true,
  "production_residuals_remain_open": true,
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE_RUNNER | HOLD_BEFORE_OFFLINE_PREPARATION_IMPLEMENTATION"
}
```

## 13. Boundary Statements

This gate preserves:

- Publisher may govern publication, but is not an external execution client.
- QC remains final artifact evaluator.
- Account Health `HOLD` remains blocking authority.
- Strategy remains the control layer.
- Orchestrator remains a coordinator.
- Attribution receives no production causality.
- Experiment receives no publish authority.
- Core pipeline remains unchanged.

## 14. Next Authorized Step

After this gate document is accepted, the next authorized step is:

- `tests/gates/sandbox/run_external_sandbox_validation_call_offline_preparation_implementation_gate.py`

That runner must be audit-only.

It must not create allowlisted files.

It must not create implementation tests.

It must not authorize runtime integration or external execution.

## 15. Final Principle

An allowlist gate can validate a proposed allowlist.

It cannot activate the allowlist.

It cannot authorize code.

It cannot authorize tests.

It cannot authorize execution.
