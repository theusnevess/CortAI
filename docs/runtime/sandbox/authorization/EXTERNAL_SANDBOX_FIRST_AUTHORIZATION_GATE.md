# EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE

## 1. Purpose

`EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE` defines the audit-only gate for the first Publisher external sandbox authorization plan.

This gate validates that the first authorization scope remains planning-only and limited to a future sandbox validation call.

It does not authorize:

- code implementation
- runner execution of external calls
- runtime integration
- HTTP client usage
- platform SDK usage
- endpoint configuration
- DNS or network access
- API calls
- credential value access
- request transformation
- upload
- scheduler invocation
- publishing
- real URL emission
- `platform_content_id` emission
- receipt generation
- production residual closure

Final principle:

> This gate proves the first authorization plan is narrow enough to review. It does not authorize execution.

## 2. Scope

In scope:

- validate `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_PLAN.md`
- validate authorization scope is exactly `PLAN_SANDBOX_VALIDATION_CALL_ONLY`
- validate implementation remains unauthorized
- validate external calls remain unauthorized
- validate credential value access remains unauthorized
- validate runtime integration remains unauthorized
- validate publish scope is excluded
- validate production residuals remain open
- validate no language implies production readiness
- validate no language implies publishability
- validate no language authorizes HTTP, SDK, endpoint, DNS or API usage
- validate no language authorizes request transformation
- validate no language authorizes real receipt, URL or `platform_content_id`

Out of scope:

- implementing sandbox calls
- creating an HTTP client
- configuring endpoint or DNS behavior
- initializing platform SDKs
- accessing real credentials
- transforming envelope artifacts into requests
- uploading media
- scheduling publication
- publishing content
- collecting post-publish metrics
- closing production residuals
- changing Publisher runtime
- changing QC, Account Health, Strategy, Orchestrator, Attribution, Experiment or core pipeline

## 3. Preconditions

Required prior artifacts:

- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_EXTERNAL_CALL_AUTHORIZATION_CHECKPOINT.md`
- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_PLAN.md`
- `docs/runtime/sandbox/pre-execution-guard/EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_REVIEW.md`
- `OUT/audit/external_sandbox_external_call_pre_execution_guard_gate/final_verdict.json`

Required prior state:

```json
{
  "external_call_boundary": "GATED",
  "pre_execution_guard": "GATED",
  "external_execution": "NOT_AUTHORIZED",
  "production_residuals": "OPEN"
}
```

## 4. Required Assertions

The gate must validate:

```json
{
  "authorization_scope_exact": "PLAN_SANDBOX_VALIDATION_CALL_ONLY",
  "implementation_authorized": false,
  "external_call_authorized": false,
  "credential_value_access_authorized": false,
  "runtime_integration_authorized": false,
  "publish_scope_excluded": true,
  "production_residuals_remain_open": true
}
```

These assertions are mandatory.

If any assertion is false or missing, the gate must return `HOLD`.

## 5. Evaluation Dimensions

### A. Artifact Integrity

Validate:

- required plan exists
- required checkpoint exists
- required guard review exists
- required guard final verdict exists and is valid JSON
- plan is documentation only
- no runner is required by this gate
- no code implementation is introduced by this gate

### B. Scope Exactness

Validate:

- authorization scope is exactly `PLAN_SANDBOX_VALIDATION_CALL_ONLY`
- no broader scope appears
- no publish scope appears
- no upload scope appears
- no scheduler scope appears
- no production platform interaction scope appears
- no post-publish metrics scope appears
- no attribution causality scope appears

### C. Non-Authorization Preservation

Validate all remain false:

- implementation authorized
- external call authorized
- credential value access authorized
- runtime integration authorized
- HTTP client allowed
- SDK allowed
- endpoint allowed
- DNS/network allowed
- API call allowed
- request transformation authorized
- upload authorized
- scheduler authorized
- real publish authorized
- URL allowed
- `platform_content_id` allowed
- receipt allowed
- production residual closure authorized

### D. Boundary Preservation

Validate:

- Publisher does not become an external execution client
- QC does not become Publisher
- Account Health `HOLD` remains blocking authority
- Strategy remains control layer
- Orchestrator remains coordinator
- Attribution does not claim causality without production evidence
- Experiment does not create publish authority
- core pipeline remains unchanged

### E. Evidence Semantics

Validate:

- sandbox evidence is not production evidence
- sandbox validation is not publish success
- sandbox receipt, if later introduced, is not production receipt
- sandbox pass cannot close production residuals
- eligibility cannot become success
- guard pass cannot become success
- `blocked=false` cannot become authorization

### F. Language Safety

Validate the plan does not imply:

- production readiness
- public publishability
- upload readiness
- platform activation
- credential readiness
- endpoint readiness
- transport readiness
- request execution readiness
- receipt availability
- post-publish evidence
- attribution readiness

## 6. Controlled Scenario Battery

The future runner for this gate must evaluate at least these scenarios:

1. plan exists
2. checkpoint exists
3. guard review exists
4. guard final verdict exists
5. authorization scope exact
6. implementation unauthorized
7. external call unauthorized
8. credential value access unauthorized
9. runtime integration unauthorized
10. HTTP client unauthorized
11. platform SDK unauthorized
12. endpoint unauthorized
13. DNS/network unauthorized
14. API call unauthorized
15. request transformation unauthorized
16. upload unauthorized
17. scheduler unauthorized
18. real publish unauthorized
19. URL emission unauthorized
20. `platform_content_id` emission unauthorized
21. receipt generation unauthorized
22. publish scope excluded
23. upload scope excluded
24. scheduler scope excluded
25. production platform scope excluded
26. post-publish metrics excluded
27. attribution causality excluded
28. sandbox evidence separated from production evidence
29. sandbox validation not publish success
30. production residuals remain open
31. Account Health `HOLD` boundary preserved
32. QC non-publishable boundary preserved
33. Strategy control boundary preserved
34. Orchestrator coordination boundary preserved
35. no production readiness language
36. no publishability language
37. no fake receipt language
38. no fake URL language
39. no fake platform ID language
40. determinism of gate review

## 7. Checklist

The gate checklist must include:

- required artifacts present
- required JSON artifacts parse
- authorization scope exact
- implementation unauthorized
- external call unauthorized
- credential value access unauthorized
- runtime integration unauthorized
- publish scope excluded
- upload scope excluded
- scheduler scope excluded
- production platform scope excluded
- request transformation excluded
- HTTP/SDK/endpoint/DNS/API excluded
- real URL excluded
- `platform_content_id` excluded
- receipt excluded
- production residuals open
- sandbox evidence not production evidence
- sandbox validation not publish success
- guard pass not success
- `blocked=false` not authorization
- QC boundary preserved
- Account Health boundary preserved
- Strategy boundary preserved
- Orchestrator boundary preserved
- core unchanged
- no production readiness language
- no publishability language
- no fake success language

## 8. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

Expected likely verdict:

- `GO_WITH_MONITORING`

This expected likely verdict must not be hardcoded.

### HOLD

Return `HOLD` if:

- required artifacts are missing
- authorization scope is not exactly `PLAN_SANDBOX_VALIDATION_CALL_ONLY`
- implementation is authorized
- external call is authorized
- credential value access is authorized
- runtime integration is authorized
- HTTP, SDK, endpoint, DNS or API usage is authorized
- request transformation is authorized
- upload is authorized
- scheduler is authorized
- publishing is authorized
- publish scope appears
- production platform scope appears
- real URL is allowed
- `platform_content_id` is allowed
- receipt is allowed
- sandbox validation is treated as publish success
- sandbox evidence is treated as production evidence
- production residuals are closed
- `blocked=false` is treated as authorization
- guard pass is treated as success
- QC boundary is violated
- Account Health `HOLD` can be bypassed
- Strategy boundary is violated
- Orchestrator boundary is violated
- core pipeline changes are implied
- silent failure is detected

### GO_WITH_MONITORING

Return `GO_WITH_MONITORING` if:

- all critical checks pass
- the plan remains planning-only
- first authorization scope is narrow and exact
- production residuals remain open
- external execution remains unauthorized
- remaining residuals are explicit and bounded

### GO

Return `GO` only if:

- all checks pass
- no meaningful residual monitoring remains

For this gate, `GO` is unlikely because external execution and production residuals remain intentionally open.

## 9. Required Future Runner

The future runner is:

- `tests/gates/sandbox/run_external_sandbox_first_authorization_gate.py`

The runner must be audit-only.

It must not:

- execute external calls
- import or initialize HTTP clients
- import or initialize platform SDKs
- configure endpoints
- perform DNS or network access
- access credential values
- transform request payloads
- upload media
- schedule publication
- publish content
- emit URL or `platform_content_id`
- generate receipts
- close production residuals

## 10. Required Future Output Artifacts

The future runner must generate:

- `OUT/audit/external_sandbox_first_authorization_gate/final_verdict.json`
- `OUT/audit/external_sandbox_first_authorization_gate/checklist_results.json`
- `OUT/audit/external_sandbox_first_authorization_gate/scenario_outputs.json`
- `OUT/audit/external_sandbox_first_authorization_gate/metrics.json`
- `OUT/audit/external_sandbox_first_authorization_gate/scope_review.json`
- `OUT/audit/external_sandbox_first_authorization_gate/non_authorization_review.json`
- `OUT/audit/external_sandbox_first_authorization_gate/residual_monitoring_review.json`
- `OUT/audit/external_sandbox_first_authorization_gate/boundary_review.json`

## 11. Final Verdict Schema

The future `final_verdict.json` must include:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "authorization_scope_exact": "PLAN_SANDBOX_VALIDATION_CALL_ONLY",
  "implementation_authorized": false,
  "external_call_authorized": false,
  "credential_value_access_authorized": false,
  "runtime_integration_authorized": false,
  "publish_scope_excluded": true,
  "production_residuals_remain_open": true,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "dns_network_allowed": false,
  "api_call_allowed": false,
  "request_transformation_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "published_url_allowed": false,
  "platform_content_id_allowed": false,
  "receipt_allowed": false,
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE_RUNNER | HOLD_BEFORE_AUTHORIZATION_RUNNER"
}
```

## 12. Residual Monitoring Rules

The following residuals must remain open:

```json
[
  "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
  "PLATFORM_INTEGRATION_NOT_ENABLED",
  "PUBLISH_RESULT_HISTORY_STILL_SHORT",
  "EXTERNAL_CALL_NOT_IMPLEMENTED",
  "EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED"
]
```

This gate may reduce only:

- first authorization plan scope uncertainty
- non-authorization language uncertainty
- boundary language uncertainty

It must not reduce:

- production publish evidence residuals
- platform integration residuals
- publish result history residuals
- external execution residuals
- attribution causality residuals

## 13. Final Criteria

This gate is acceptable only if:

```json
{
  "gate_defined": true,
  "audit_only": true,
  "authorization_scope_exact": "PLAN_SANDBOX_VALIDATION_CALL_ONLY",
  "implementation_authorized": false,
  "external_call_authorized": false,
  "credential_value_access_authorized": false,
  "runtime_integration_authorized": false,
  "publish_scope_excluded": true,
  "production_residuals_remain_open": true
}
```

## 14. Next Authorized Step

After this gate is accepted, the next authorized artifact is:

- `tests/gates/sandbox/run_external_sandbox_first_authorization_gate.py`

That runner must remain audit-only.

No code implementation is authorized.

No external call is authorized.

No HTTP client, platform SDK, endpoint, DNS, credential value access, request transformation, upload, scheduler, publishing, URL, `platform_content_id` or receipt is authorized.
