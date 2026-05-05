# EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE

## 1. Purpose

`EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE` freezes the acceptance criteria for the future offline implementation of the external sandbox validation envelope.

This is a gate specification artifact.

It does not create code, create tests, create a runner, execute tests, call external services, call platform APIs, upload content, transfer media bytes, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, collect post-publish metrics, close production residuals, modify Publisher runtime execution, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The future runner will validate that the implementation is an inert validation object, not a transport object and not an executable request.

Final principle:

> The external sandbox validation envelope may describe intent and validation state. It must not become execution, transport, upload, scheduling, publishing, or success evidence.

## 2. Scope

In scope for this future gate:

- offline validation envelope contract
- `ValidationEnvelope` naming discipline
- target platform and mode governance
- deterministic idempotency namespace
- transport nullification
- execution nullification
- non-transportable audit serialization
- secret-status-only projection
- kill switch projection
- rate-limit projection
- dependency block semantics
- forbidden-field detection
- incident hook shape
- deterministic replay
- side-effect absence
- residual monitoring integrity

Out of scope:

- external request execution
- HTTP client usage
- platform SDK usage
- endpoint configuration
- DNS/network behavior
- authorization header generation
- real secret value access
- upload
- media byte transfer
- scheduler invocation
- real publishing
- production URL
- production `platform_content_id`
- production receipt
- post-publish metrics
- attribution causality
- runtime integration with Orchestrator
- Publisher execution path changes beyond offline envelope construction
- QC changes
- Account Health changes
- Strategy changes
- core pipeline changes

## 3. Preconditions

Required prior artifacts:

- `docs/runtime/phase-3/monitoring/PRODUCTION_MONITORING_AND_RUNTIME_EVIDENCE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_PLAN.md`
- `docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_PLAN.md`
- `docs/runtime/sandbox/evidence/EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_PLAN.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_GATE.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_PLAN.md`
- `OUT/audit/external_sandbox_evidence_collection_gate/final_verdict.json`
- `OUT/audit/external_sandbox_request_envelope_gate/final_verdict.json`

Required prior state:

```json
{
  "external_sandbox_request_envelope_gate": "GO_WITH_MONITORING",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "external_call_authorized": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "media_bytes_included": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "production_residuals_closed": false
}
```

## 4. Future Implementation Files

After this gate specification is accepted, the future implementation slice may create only:

```text
backend/app/creative/agents/publisher/external_sandbox_validation_envelope.py
backend/app/creative/agents/publisher/external_sandbox_envelope_security.py
tests/sandbox/unit/test_external_sandbox_validation_envelope_unittest.py
```

The future implementation must not modify:

- `backend/app/creative/agents/publisher/sandbox_adapter.py`
- `backend/app/creative/agents/publisher/publish_lifecycle_writer.py`
- `backend/app/creative/agents/publisher/publish_trace.py`
- `backend/app/creative/agents/video_qc/`
- `backend/app/creative/agents/account_health/`
- `backend/app/creative/agents/strategy/`
- Creative Orchestrator
- core pipeline

Any runtime integration requires a later artifact and a later gate.

## 5. Required Naming

The implementation must use validation or intent naming.

Required or acceptable names:

- `ExternalSandboxValidationEnvelope`
- `ExternalSandboxValidationEnvelopeInput`
- `ExternalSandboxValidationEnvelopeBuilder`
- `ExternalSandboxEnvelopeValidationResult`
- `ExternalSandboxEnvelopeIncidentHook`
- `ExternalSandboxIntentEnvelope` only if the validation naming remains primary in exported contracts

Forbidden or discouraged internal names:

- `ExternalSandboxRequestEnvelope`
- `ExternalSandboxRequest`
- `ExternalSandboxHttpRequest`
- `PlatformRequestEnvelope`
- any class name implying transport execution

The governance artifact name may continue to include `REQUEST_ENVELOPE` for historical continuity, but the implementation must expose the object as validation state, not request execution state.

## 6. Required Constants

The implementation must preserve:

```json
{
  "ENVELOPE_VERSION": "external_sandbox_request_envelope_v1",
  "ENVELOPE_TYPE": "external_sandbox_validation_envelope",
  "TARGET_PLATFORM_ID": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "TARGET_MODE": "sandbox_external_dry_run",
  "METADATA_SHAPE_CLASS": "metadata_shape_only",
  "BOUNDARY_STATEMENT": "External sandbox validation envelope is non-executable and non-transportable."
}
```

Forbidden constants:

- real provider names
- production domains
- API base URLs
- upload URLs
- publish endpoints
- OAuth URLs
- scheduler endpoint names
- production visibility modes
- HTTP method constants
- header names intended for request execution

## 7. Transport Nullification Requirements

The future implementation must be structurally non-transportable.

The envelope must include:

```json
{
  "execution_capability": "none",
  "transport_capability": "none",
  "non_transportable": true
}
```

The gate must fail if any envelope, validation result, serialization helper, or security helper exposes HTTP-like fields:

- `headers`
- `body`
- `url`
- `method`
- `endpoint`
- `host`
- `path`
- `query`
- `params`
- `cookies`
- `auth`
- `authorization`

The gate must fail if any helper implies transport construction:

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

The gate must fail if serialization produces a structure reasonably reusable as an HTTP payload without a separate transformation layer.

## 8. Execution Nullification Requirements

The implementation must not import, initialize, reference, or call:

- `requests`
- `httpx`
- `aiohttp`
- `urllib.request`
- `urllib3`
- `socket`
- platform SDK clients
- OAuth clients
- upload clients
- scheduler clients
- DNS/network helpers

The implementation must not define:

- endpoints
- base URLs
- upload URLs
- publish URLs
- scheduler URLs
- request methods
- authorization headers
- callback URLs
- webhook URLs

The gate must treat any external execution capability as `HOLD`.

## 9. Envelope Output Contract

The future envelope output must include at minimum:

```json
{
  "envelope_version": "external_sandbox_request_envelope_v1",
  "envelope_type": "external_sandbox_validation_envelope",
  "run_id": "...",
  "content_id": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "idempotency_key": "external_sandbox_envelope_v1:...",
  "artifact_manifest_ref": "...",
  "metadata_payload_ref": "...",
  "qc_trace_ref": "...",
  "account_health_trace_ref": "...",
  "strategy_ref": "...",
  "publish_eligibility_trace_ref": "...",
  "credential_status": {},
  "kill_switch_status": {},
  "rate_limit_status": {},
  "metadata_projection": {},
  "metadata_shape_class": "metadata_shape_only",
  "execution_capability": "none",
  "transport_capability": "none",
  "non_transportable": true,
  "media_bytes_included": false,
  "upload_endpoint_requested": false,
  "publish_endpoint_requested": false,
  "public_visibility_requested": false,
  "external_call_authorized": false,
  "platform_api_execution_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "published_url": null,
  "platform_content_id": null,
  "boundary_statement": "External sandbox validation envelope is non-executable and non-transportable."
}
```

`metadata_shape_class` is a classification string only. It must not correspond to a serialized transport body.

## 10. Idempotency Requirements

The idempotency key must:

- use the namespace prefix `external_sandbox_envelope_v1:`
- be deterministic
- be sandbox-scoped
- be non-reusable for production publishing flows
- contain no secret material
- contain no raw credentials
- contain no endpoint
- contain no URL
- contain no production `platform_content_id`
- remain stable across replay for identical input
- change when one of the governed identity inputs changes

Required identity inputs:

- `run_id`
- `content_id`
- `artifact_manifest_ref`
- `target_platform_id`
- `target_mode`

Randomness is forbidden.

## 11. Metadata Projection Requirements

Metadata projection may include only bounded status and shape information:

```json
{
  "title_present": true,
  "description_present": true,
  "tags_present": true,
  "language_present": true,
  "visibility_mode": "sandbox_only",
  "account_id_ref": "...",
  "content_id": "...",
  "runtime_policy_ref": "...",
  "metadata_trace_ref": "...",
  "metadata_shape_valid": true
}
```

Metadata projection must not include:

- full unsafe descriptions
- secrets
- tokens
- authorization headers
- production URLs
- production `platform_content_id`
- expected performance claims
- forecasts
- attribution claims
- direct platform provider binding

Invalid metadata must create blocking reasons, not silent fallback.

## 12. Credential Projection Requirements

Credential projection may include only:

```json
{
  "credential_status": "present | missing | invalid_shape | not_checked",
  "credential_source": "environment_or_secret_manager",
  "secret_values_logged": false,
  "secret_values_persisted": false,
  "secret_scope_class": "sandbox_validation_only"
}
```

Rules:

- raw secret values must not be read
- raw secret values must not be stored
- raw secret values must not be serialized
- authorization headers must not be generated
- exception text must not leak credential material
- missing credentials must block future sandbox eligibility

## 13. Kill Switch Requirements

Kill switch projection must preserve:

```json
{
  "kill_switch_name": "PUBLISHER_PLATFORM_KILL_SWITCH",
  "default_safe_state": "blocked",
  "active": false,
  "missing": false,
  "blocks_publish_attempt": true,
  "blocks_external_calls": true,
  "blocks_upload": true,
  "blocks_scheduler": true
}
```

Rules:

- active kill switch blocks eligibility
- missing kill switch blocks eligibility
- kill switch cannot fail open
- blocked envelope still serializes for audit
- blocked envelope must not authorize external calls

## 14. Rate-Limit Requirements

Rate-limit projection must preserve:

```json
{
  "rate_limit_policy_version": "publisher_platform_rate_limits_v1",
  "sandbox_validation_requests_allowed": false,
  "upload_requests_allowed": false,
  "publish_requests_allowed": false,
  "max_sandbox_validation_requests_per_minute": null,
  "max_upload_requests_per_hour": null,
  "max_publish_requests_per_day": null,
  "burst_allowed": false,
  "rate_limit_exceeded_behavior": "block_and_trace"
}
```

Rules:

- `null` means disabled or not authorized, not unlimited
- sandbox validation requests remain disabled until a later gate
- upload requests remain disabled
- publish requests remain disabled
- rate-limit violations block eligibility

## 15. Dependency Block Requirements

The builder must block envelope eligibility when:

- `qc_trace_ref` is missing
- QC status is `HOLD`
- QC status is `REJECT`
- QC `publishable=false`
- Account Health decision is `HOLD`
- `artifact_manifest_ref` is missing
- `metadata_payload_ref` is missing
- `strategy_ref` is missing
- `publish_eligibility_trace_ref` is missing
- credential status is `missing`
- credential status is `invalid_shape`
- kill switch is active
- kill switch is missing
- mixed mode appears
- implicit provider binding appears
- forbidden field appears
- secret-like value appears

Every block must appear in:

- `blocking_reasons`
- `rationale`
- incident hooks where applicable

Blocked envelopes remain visible. Blocked envelopes must not be represented as success.

## 16. Forbidden Field Detection

The implementation must deterministically detect and block:

- `published_url`
- `platform_content_id`
- `production_receipt`
- `upload_url`
- `scheduler_job_id`
- `post_publish_metrics_ref`
- `expected_performance`
- `forecast`
- `predicted`
- `causal_claim`
- `access_token`
- `client_secret`
- `authorization`
- `api_key`
- `password`
- `refresh_token`
- `endpoint`
- `headers`
- `body`
- `method`
- `url`

If found:

- `forbidden_field_detected = true`
- envelope eligibility is blocked
- incident hook is emitted
- field value is not copied into output

## 17. Validation Result Contract

The future validation result must be serializable:

```json
{
  "envelope_valid": true,
  "eligible_for_future_external_sandbox_validation": false,
  "blocking_reasons": [],
  "warnings": [],
  "secret_leakage_detected": false,
  "forbidden_field_detected": false,
  "http_like_field_detected": false,
  "executable_helper_detected": false,
  "transport_payload_detected": false,
  "external_call_authorized": false,
  "platform_api_execution_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "rationale": []
}
```

Rules:

- `envelope_valid=true` means schema valid only
- schema validity does not authorize external execution
- future eligibility does not authorize external execution
- warnings do not become success
- blocked envelopes remain visible

## 18. Incident Hook Requirements

Incident hooks must support:

- `EXTERNAL_SANDBOX_ENVELOPE_SECRET_LEAKAGE_ATTEMPT`
- `EXTERNAL_SANDBOX_ENVELOPE_FORBIDDEN_FIELD`
- `EXTERNAL_SANDBOX_ENVELOPE_HTTP_LIKE_FIELD`
- `EXTERNAL_SANDBOX_ENVELOPE_EXECUTABLE_HELPER`
- `EXTERNAL_SANDBOX_ENVELOPE_TRANSPORT_PAYLOAD_SHAPE`
- `EXTERNAL_SANDBOX_ENVELOPE_MIXED_MODE`
- `EXTERNAL_SANDBOX_ENVELOPE_PROVIDER_BINDING`
- `EXTERNAL_SANDBOX_ENVELOPE_KILL_SWITCH_BLOCK`
- `EXTERNAL_SANDBOX_ENVELOPE_CREDENTIALS_MISSING`
- `ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH`
- `QC_NON_PUBLISHABLE_BLOCKED_PUBLISH`

Incident hooks must include:

- incident type
- severity
- run ID
- content ID
- target platform
- target mode
- rationale

Incident hooks must not include:

- secrets
- tokens
- authorization headers
- endpoints
- production URLs
- platform content IDs
- media bytes

## 19. Serialization Requirements

Serialization must be audit-only.

Required:

- deterministic JSON serializable output
- stable key ordering where practical
- primitive values only
- no datetime-generated nondeterminism unless supplied as input
- no random IDs
- no object memory addresses
- no environment-dependent fields except status-only credential presence where explicitly supplied
- explicit `execution_capability = "none"`
- explicit `transport_capability = "none"`
- explicit `non_transportable = true`

Forbidden:

- HTTP-ready serialization
- request-ready payload serialization
- transport wrapper generation
- endpoint-bearing serialization
- header-bearing serialization
- body-bearing serialization
- media byte serialization

Same input must produce the same envelope and the same validation result.

## 20. Controlled Scenario Battery

The future runner must validate at least:

1. valid inert envelope shape
2. `ValidationEnvelope` naming present
3. request/execution naming absent from exported structures
4. target platform exact
5. target mode exact
6. single mode enforced
7. mixed mode rejected
8. `execution_capability` present and `none`
9. `transport_capability` present and `none`
10. `non_transportable` present and true
11. no HTTP-like fields
12. no executable helpers
13. audit serialization only
14. no HTTP client imports
15. no platform SDK imports
16. no endpoint or DNS configuration
17. external call remains unauthorized
18. platform API remains uncalled
19. upload remains unauthorized
20. scheduler remains unauthorized
21. real publish remains unauthorized
22. media bytes are forbidden
23. public visibility is forbidden
24. production URL is forbidden
25. `platform_content_id` is forbidden
26. metadata projection is bounded
27. credential projection is status-only
28. secret-like fields are detected and redacted
29. kill switch active blocks eligibility
30. kill switch missing blocks eligibility
31. disabled rate limit is not unlimited
32. QC `HOLD` blocks
33. QC `REJECT` blocks
34. QC `publishable=false` blocks
35. Account Health `HOLD` blocks
36. missing dependency refs block
37. idempotency namespace is `external_sandbox_envelope_v1:`
38. idempotency key deterministic
39. changed input changes idempotency key
40. envelope validity does not imply external success
41. future eligibility does not imply external success
42. forbidden field detection is deterministic
43. incident hooks do not include secrets
44. serialization deterministic replay
45. production residuals remain open

The runner may add stricter scenarios. It must not omit these.

## 21. Checklist

The future runner checklist must include:

- required files present
- no unauthorized files modified
- target platform fixed
- target mode fixed
- single mode enforced
- no mixed modes
- validation naming used
- request execution naming absent
- transport nullification markers present
- no HTTP-like fields
- no executable helper methods
- no HTTP client imports
- no platform SDK imports
- no endpoint constants
- no DNS/network usage
- no authorization header generation
- no raw secret reads
- no raw secret serialization
- no media bytes
- no upload
- no scheduler
- no publish
- no production URL
- no production `platform_content_id`
- metadata projection bounded
- credential projection status-only
- kill switch fail-closed
- rate-limit disabled is not unlimited
- dependency blocks explicit
- idempotency namespace correct
- idempotency deterministic
- validation does not imply success
- eligibility does not imply success
- audit serialization non-transportable
- incident hooks safe
- deterministic replay
- residuals preserved
- boundary preserved

## 22. Required Future Output Artifacts

The future runner must create:

```text
OUT/audit/external_sandbox_request_envelope_implementation_gate/final_verdict.json
OUT/audit/external_sandbox_request_envelope_implementation_gate/checklist_results.json
OUT/audit/external_sandbox_request_envelope_implementation_gate/scenario_outputs.json
OUT/audit/external_sandbox_request_envelope_implementation_gate/metrics.json
OUT/audit/external_sandbox_request_envelope_implementation_gate/security_review.json
OUT/audit/external_sandbox_request_envelope_implementation_gate/contract_review.json
OUT/audit/external_sandbox_request_envelope_implementation_gate/transport_nullification_review.json
OUT/audit/external_sandbox_request_envelope_implementation_gate/static_scan_review.json
OUT/audit/external_sandbox_request_envelope_implementation_gate/determinism_review.json
OUT/audit/external_sandbox_request_envelope_implementation_gate/side_effect_review.json
OUT/audit/external_sandbox_request_envelope_implementation_gate/residual_monitoring_review.json
```

## 23. Metrics

Future metrics must include:

```json
{
  "critical_failures": 0,
  "blocking_failures_count": 0,
  "scenario_count": 45,
  "scenario_pass_count": 45,
  "checklist_count": 0,
  "checklist_pass_count": 0,
  "external_call_authorized": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "media_bytes_included": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "http_client_detected": false,
  "platform_sdk_detected": false,
  "endpoint_detected": false,
  "dns_or_network_detected": false,
  "http_like_fields_detected": false,
  "executable_helpers_detected": false,
  "transport_payload_detected": false,
  "secret_leakage_detected": false,
  "forbidden_field_detected": false,
  "fake_success_detected": false,
  "production_residuals_closed": false
}
```

`checklist_count` and `checklist_pass_count` must be populated by the runner with real values.

## 24. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

Expected future verdict after compliant implementation:

- `GO_WITH_MONITORING`

`GO` is not expected while external execution remains unauthorized and production residuals remain open.

## 25. HOLD Conditions

The future runner must return `HOLD` if any of the following occur:

- required implementation files are missing
- unauthorized runtime files are modified
- target platform changes
- target mode changes
- mixed mode is accepted
- implicit provider binding appears
- validation naming is absent
- request/execution naming becomes primary exported contract
- `execution_capability` is missing or not `none`
- `transport_capability` is missing or not `none`
- `non_transportable` is missing or not true
- HTTP-like field appears
- executable helper appears
- HTTP client import appears
- platform SDK import appears
- endpoint or DNS configuration appears
- authorization header generation appears
- raw secret value is read
- raw secret value is serialized
- media bytes are included
- upload is authorized or performed
- scheduler is authorized or invoked
- real publishing is authorized or performed
- production URL is emitted
- production `platform_content_id` is emitted
- result evidence is represented as production evidence
- envelope validity is treated as external success
- eligibility is treated as publish success
- fake success is accepted
- deterministic replay fails
- residuals of production are closed
- QC, Account Health, Strategy, Orchestrator or core pipeline are modified

## 26. Residual Monitoring Rules

These residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

This future implementation gate may reduce only:

- envelope schema uncertainty
- validation naming uncertainty
- transport nullification implementation uncertainty
- forbidden-field implementation uncertainty
- credential projection implementation uncertainty
- idempotency projection implementation uncertainty
- dependency reference projection implementation uncertainty

It must not reduce:

- production publish evidence residual
- real platform integration residual
- production result history residual
- external sandbox execution residual
- post-publish metric residual
- attribution causality residual

## 27. Final Verdict Schema

The future `final_verdict.json` must include at minimum:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "validation_envelope_implemented": true,
  "execution_capability": "none",
  "transport_capability": "none",
  "non_transportable": true,
  "idempotency_namespace_valid": true,
  "http_like_fields_detected": false,
  "executable_helpers_detected": false,
  "http_client_detected": false,
  "platform_sdk_detected": false,
  "endpoint_detected": false,
  "dns_or_network_detected": false,
  "external_call_authorized": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "secret_leakage_detected": false,
  "fake_success_detected": false,
  "production_residuals_closed": false,
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_RUNNER | HOLD_BEFORE_NEXT_STEP"
}
```

## 28. Final Criteria

The future gate passes only if:

```json
{
  "validation_envelope_implemented": true,
  "offline_only": true,
  "validation_naming_used": true,
  "execution_capability": "none",
  "transport_capability": "none",
  "non_transportable": true,
  "http_like_fields_detected": false,
  "executable_helpers_detected": false,
  "http_client_detected": false,
  "platform_sdk_detected": false,
  "endpoint_detected": false,
  "dns_or_network_detected": false,
  "secret_values_logged": false,
  "secret_values_persisted": false,
  "idempotency_namespace": "external_sandbox_envelope_v1:",
  "external_call_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "production_residuals_remain_open": true,
  "boundary_preserved": true
}
```

## 29. Next Authorized Step

After this gate specification is accepted, the next authorized step is the offline implementation slice:

```text
backend/app/creative/agents/publisher/external_sandbox_validation_envelope.py
backend/app/creative/agents/publisher/external_sandbox_envelope_security.py
tests/sandbox/unit/test_external_sandbox_validation_envelope_unittest.py
```

After that implementation exists, the next authorized artifact is:

```text
tests/gates/sandbox/run_external_sandbox_request_envelope_implementation_gate.py
```

External calls remain unauthorized.

HTTP clients remain unauthorized.

Platform SDKs remain unauthorized.

Endpoint configuration remains unauthorized.

DNS/network behavior remains unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Real publishing remains unauthorized.

Production URL and production `platform_content_id` emission remain unauthorized.
