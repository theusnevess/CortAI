# EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_PLAN

## 1. Purpose

`EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_PLAN` defines the first possible authorization scope after the Publisher external sandbox pre-execution checkpoint.

This is a planning artifact only.

It does not authorize implementation, runtime integration, external execution, HTTP clients, platform SDKs, endpoints, DNS or network access, API calls, credential value access, request transformation, upload, scheduler invocation, publishing, real URL emission, `platform_content_id` emission, receipt generation or production residual closure.

The only scope considered by this plan is a future sandbox validation call authorization plan.

Final principle:

> The first authorization stage may only plan a future sandbox validation call. It must not plan publication.

## 2. Starting State

Canonical checkpoint:

- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_EXTERNAL_CALL_AUTHORIZATION_CHECKPOINT.md`

Checkpoint decision:

```json
{
  "decision": "PREPARE_FIRST_AUTHORIZATION_PLAN",
  "external_execution_authorized": false,
  "implementation_authorized": false,
  "runtime_integration_authorized": false
}
```

Consolidated state:

```json
{
  "sandbox_adapter": "GATED",
  "validation_envelope": "GATED",
  "execution_simulation": "GATED",
  "controlled_binding": "GATED",
  "external_call_boundary": "GATED",
  "pre_execution_guard": "GATED",
  "external_execution": "NOT_AUTHORIZED",
  "production_residuals": "OPEN"
}
```

## 3. Authorization Scope Under Consideration

This plan considers only:

```json
{
  "authorization_scope": "PLAN_SANDBOX_VALIDATION_CALL_ONLY",
  "implementation_authorized": false,
  "external_call_authorized": false,
  "credential_value_access_authorized": false,
  "runtime_integration_authorized": false
}
```

Meaning:

- a future plan may describe how a sandbox validation call could eventually be authorized
- no code may be written from this artifact
- no runner may execute an external call from this artifact
- no endpoint may be configured from this artifact
- no credential value may be accessed from this artifact
- no request transformation may be implemented from this artifact
- no runtime path may be wired from this artifact

## 4. Explicitly Excluded Scopes

This plan does not consider authorization for:

- publishing
- upload
- scheduling
- production platform interaction
- public visibility
- production receipt handling
- production URL generation
- `platform_content_id` generation
- post-publish metric collection
- attribution causality
- Strategy modification
- QC modification
- Account Health override
- Orchestrator modification
- Experiment behavior
- core pipeline changes

The first authorization stage must remain narrower than platform integration and much narrower than publishing.

## 5. Sandbox Validation Call Definition

A future sandbox validation call, if later planned and gated, may only mean:

- a non-production interaction with a governed sandbox target
- no upload of media bytes
- no publication
- no public visibility
- no scheduler invocation
- no production receipt
- no production URL
- no production `platform_content_id`
- no post-publish metrics
- no production attribution claim

Target identifiers remain:

```json
{
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "sandbox_receipt_is_production": false
}
```

The phrase `sandbox validation call` must not be interpreted as publish attempt, platform launch, content upload, scheduler job or production integration.

## 6. Current Non-Authorization Matrix

The following values remain fixed by this plan:

```json
{
  "external_call_authorized": false,
  "http_client_allowed": false,
  "platform_sdk_allowed": false,
  "endpoint_allowed": false,
  "dns_network_allowed": false,
  "api_call_allowed": false,
  "credential_value_access_allowed": false,
  "request_transformation_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "published_url_allowed": false,
  "platform_content_id_allowed": false,
  "receipt_allowed": false,
  "runtime_integration_authorized": false,
  "production_residual_closure_authorized": false
}
```

Any change to these values requires a later gate and cannot be inferred from this plan.

## 7. Preconditions For A Future Authorization Gate

Before any implementation or external execution can be considered, a future gate must validate:

- authorization scope remains sandbox validation only
- upload remains forbidden
- publishing remains forbidden
- scheduler remains forbidden
- production residuals remain open
- Account Health `HOLD` blocks all future attempts
- QC non-publishable blocks all future attempts
- kill switch blocks all future attempts
- `blocked=false` still does not authorize execution
- guard pass still does not mean success
- sandbox receipt, if ever introduced, is explicitly non-production
- sandbox evidence cannot close production residuals
- no fake URL or `platform_content_id` can be emitted
- no credential value can be logged, serialized or persisted
- no request transformation can exist before a dedicated implementation gate

## 8. Future Gate Required Before Any Code

The next required artifact is:

- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE.md`

That gate must be created and accepted before any code, runner, client, endpoint, credential access or integration is considered.

The gate must validate at minimum:

- this plan exists
- authorization scope is exactly `PLAN_SANDBOX_VALIDATION_CALL_ONLY`
- implementation remains unauthorized
- external execution remains unauthorized
- credential value access remains unauthorized
- runtime integration remains unauthorized
- publish/upload/scheduler remain unauthorized
- production residuals remain open
- no plan language implies production readiness
- no plan language implies publishability
- no plan language permits endpoint, DNS, HTTP or SDK usage
- no plan language permits request transformation
- no plan language permits real receipt, URL or `platform_content_id`

## 9. Credential Handling Rules

This plan authorizes only credential planning.

Allowed in future planning:

- credential presence semantics
- credential status classes
- secret manager reference class
- sandbox-only scope class
- redaction requirements
- audit requirements

Forbidden:

- reading credential values
- storing credential values
- logging credential values
- serializing credential values
- building authorization headers
- configuring real tokens
- testing real authentication
- validating a real account

Credential status must remain metadata only until a later explicit gate authorizes otherwise.

## 10. Endpoint And Provider Rules

This plan does not authorize endpoint selection.

Allowed in future planning:

- abstract sandbox target identity
- provider class constraints
- no implicit provider binding rule
- requirement that endpoint configuration needs a separate gate

Forbidden:

- production provider binding
- real provider-specific implementation
- real domain names
- base URLs
- upload endpoints
- publish endpoints
- OAuth URLs
- SDK initialization
- DNS validation

`SHORT_VIDEO_PLATFORM_SANDBOX_V1` remains a governed sandbox placeholder, not a real provider binding.

## 11. Request Transformation Rules

This plan does not authorize request transformation.

The existing validation envelope remains:

- inert
- non-transportable
- non-executable
- not an HTTP payload
- not a request body

Any future transformation from audit artifact to transport object requires:

- a separate plan
- a separate gate
- explicit transport boundary review
- explicit secret handling review
- explicit side-effect review

No transformation layer may be inferred from this plan.

## 12. Evidence Semantics

Future sandbox evidence, if later introduced, must be classified separately from production evidence.

Required semantics:

```json
{
  "sandbox_evidence_is_production": false,
  "sandbox_validation_is_publish_success": false,
  "sandbox_receipt_is_publish_receipt": false,
  "sandbox_pass_closes_production_residuals": false
}
```

Sandbox evidence may support only sandbox integration maturity.

It must not support:

- production readiness
- public publishability
- performance prediction
- attribution causality
- production residual closure

## 13. Kill Switch And Fail-Closed Rules

Future authorization planning must preserve:

- kill switch is mandatory
- missing kill switch fails closed
- active kill switch blocks any future attempt
- Account Health `HOLD` blocks any future attempt
- QC `HOLD`, `REJECT` or `publishable=false` blocks any future attempt
- missing artifact evidence blocks any future attempt
- missing trace evidence blocks any future attempt

No future sandbox validation call can be fail-open.

## 14. Boundary Preservation

The following boundaries remain frozen:

- Publisher may govern publication but is not yet an external execution client.
- QC remains final artifact evaluator, not Publisher.
- Account Health `HOLD` remains blocking authority.
- Strategy remains control layer.
- Orchestrator remains coordinator.
- Attribution cannot claim causality without production publish evidence.
- Experiment cannot create publish authority.
- Core pipeline remains unchanged.

## 15. Residual Monitoring

The following residuals remain open:

```json
[
  "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
  "PLATFORM_INTEGRATION_NOT_ENABLED",
  "PUBLISH_RESULT_HISTORY_STILL_SHORT",
  "EXTERNAL_CALL_NOT_IMPLEMENTED",
  "EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED"
]
```

This plan does not close residuals.

It may reduce only uncertainty about the next planning scope.

It must not reduce:

- production publish evidence residuals
- real platform integration residuals
- publish result history residuals
- post-publish metrics residuals
- attribution causality residuals

## 16. Failure Conditions

Any future artifact must return `HOLD` or revert to review-only if it:

- expands scope beyond sandbox validation planning
- authorizes implementation
- authorizes external execution
- authorizes credential value access
- authorizes runtime integration
- introduces HTTP client usage
- introduces platform SDK usage
- introduces endpoint or DNS behavior
- introduces request transformation
- authorizes upload
- authorizes scheduler
- authorizes publishing
- emits URL or `platform_content_id`
- emits production receipt
- treats sandbox receipt as production
- treats sandbox validation as publish success
- closes production residuals
- bypasses QC
- overrides Account Health `HOLD`
- changes Strategy, QC, Account Health, Orchestrator, Attribution, Experiment or core pipeline without formal reopen

## 17. Exit Criteria

This plan is acceptable only if:

```json
{
  "first_authorization_planned": true,
  "authorization_scope": "PLAN_SANDBOX_VALIDATION_CALL_ONLY",
  "implementation_authorized": false,
  "external_call_authorized": false,
  "credential_value_access_authorized": false,
  "runtime_integration_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "production_residuals_remain_open": true,
  "next_artifact_required_before_code": "docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE.md"
}
```

## 18. Next Authorized Artifact

The next authorized artifact is:

- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE.md`

That gate must remain audit-only and pre-implementation.

No code is authorized.

No runner is authorized.

No HTTP client is authorized.

No endpoint is authorized.

No SDK is authorized.

No DNS or network access is authorized.

No credential value access is authorized.

No external call is authorized.

No upload, scheduler or publishing is authorized.
