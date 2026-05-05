# EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_PLAN

## 1. Purpose

`EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_PLAN` defines how Publisher sandbox evidence may be collected from a controlled external sandbox boundary after the sandbox adapter implementation passed its gate.

This is a planning artifact only.

It does not implement external calls, call platform APIs, upload content, schedule publication, publish content, emit real URLs, emit real `platform_content_id`, collect post-publish metrics, close production residuals, modify Publisher runtime behavior, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The goal is to define evidence collection rules before any external sandbox execution is authorized.

Final principle:

> External sandbox evidence may prove controlled integration observability. It must not become publish evidence.

## 2. Starting State

Canonical prior state:

```json
{
  "sandbox_adapter": "IMPLEMENTED_AND_GATED",
  "sandbox_adapter_gate_verdict": "GO_WITH_MONITORING",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "real_publishing": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "production_residuals_closed": false
}
```

Required prior artifacts:

- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_PLAN.md`
- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_GATE.md`
- `tests/gates/sandbox/run_sandbox_adapter_implementation_gate.py`
- `OUT/audit/sandbox_adapter_implementation_gate/final_verdict.json`
- `backend/app/creative/agents/publisher/sandbox_contracts.py`
- `backend/app/creative/agents/publisher/sandbox_security.py`
- `backend/app/creative/agents/publisher/sandbox_adapter.py`
- `tests/publisher/unit/test_publisher_sandbox_adapter_unittest.py`

Accepted prior gate state:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "scenarios": "27/27",
  "checklist": "38/38",
  "critical_failures": 0,
  "blocking_failures": [],
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "production_residuals_closed": false
}
```

## 3. Scope

In scope for this plan:

- external sandbox evidence model
- sandbox validation request envelope
- sandbox response evidence contract
- evidence redaction rules
- credential presence/status rules
- kill switch enforcement
- rate-limit and timeout policy
- append-only lifecycle evidence
- incident hooks for sandbox validation failures
- residual monitoring integrity
- future gate requirements

Out of scope:

- real publishing
- real upload
- media byte upload
- scheduler
- production platform API execution
- production URL
- production `platform_content_id`
- production receipt
- post-publish metrics
- attribution causality
- public visibility
- real provider binding without separate approval
- Strategy changes
- QC changes
- Account Health changes
- Orchestrator changes
- Attribution changes
- Experiment changes
- core pipeline changes

## 4. External Sandbox Boundary

The only allowed future boundary is:

```json
{
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "external_boundary_type": "controlled_sandbox_validation",
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "no_implicit_provider_binding": true,
  "real_upload_allowed": false,
  "real_publish_allowed": false,
  "scheduler_allowed": false,
  "production_url_allowed": false,
  "production_platform_content_id_allowed": false
}
```

This plan does not authorize the external call.

A future gate must approve any sandbox validation request before network execution is enabled.

The external sandbox boundary must not imply YouTube, TikTok, Instagram or any real production provider binding. A separate provider approval artifact is required before any concrete provider name may appear in runtime configuration.

## 5. Evidence Collection Modes

Allowed planned evidence collection modes:

- `contract_only`
- `local_sandbox_adapter`
- `external_sandbox_validation_candidate`

Current authorized mode:

```json
{
  "authorized_mode": "local_sandbox_adapter",
  "external_sandbox_validation_authorized": false,
  "upload_authorized": false,
  "publish_authorized": false,
  "scheduler_authorized": false
}
```

`external_sandbox_validation_candidate` means the system may prepare a request envelope for a future gate. It does not mean the request may be sent.

Mixed modes are forbidden.

## 6. Sandbox Validation Request Envelope

Future external sandbox evidence collection may prepare a validation request envelope only.

Required fields:

```json
{
  "run_id": "...",
  "content_id": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "idempotency_key": "...",
  "artifact_manifest_ref": "...",
  "metadata_payload_ref": "...",
  "qc_trace_ref": "...",
  "account_health_trace_ref": "...",
  "strategy_ref": "...",
  "publish_eligibility_trace_ref": "...",
  "credential_status": "present | missing | invalid_shape | not_checked",
  "kill_switch_status": {},
  "rate_limit_status": {},
  "request_body_class": "metadata_shape_only",
  "media_bytes_included": false,
  "public_visibility_requested": false
}
```

Rules:

- media bytes must not be included
- upload URL must not be requested
- publish endpoint must not be requested
- public visibility must not be requested
- idempotency key must be deterministic
- request envelope must contain no secret values
- request envelope must contain no fake performance claim
- request envelope must contain no fake compliance claim
- request envelope must contain no production URL
- request envelope must contain no production platform content ID

## 7. Credential And Secret Rules

External sandbox evidence collection may record only credential presence/status.

Allowed:

```json
{
  "credential_status": "present | missing | invalid_shape | not_checked",
  "credential_source": "environment_or_secret_manager",
  "secret_values_logged": false,
  "secret_values_persisted": false,
  "secret_scope_class": "sandbox_validation_only"
}
```

Forbidden:

- raw secret values in logs
- raw secret values in JSONL
- raw secret values in audit artifacts
- tokens in incident hooks
- authorization headers in traces
- credential values in request envelope artifacts
- credential values in response artifacts

Missing credentials must block external sandbox validation and emit an incident hook.

Missing credentials must not be represented as sandbox validation success.

## 8. Kill Switch Rules

The kill switch remains mandatory before any external sandbox validation can be authorized.

Required behavior:

```json
{
  "kill_switch_name": "PUBLISHER_PLATFORM_KILL_SWITCH",
  "default_safe_state": "blocked",
  "blocks_publish_attempt": true,
  "blocks_external_calls": true,
  "blocks_upload": true,
  "blocks_scheduler": true,
  "emits_incident_hook": true,
  "writes_lifecycle_event": true
}
```

If kill switch is active or missing:

- no external sandbox request may be sent
- no upload may occur
- no scheduler may run
- no publish may occur
- lifecycle event must show blocked status
- incident hook must be emitted

## 9. Rate Limit And Timeout Rules

Current state:

```json
{
  "sandbox_validation_requests_allowed": false,
  "upload_requests_allowed": false,
  "publish_requests_allowed": false,
  "max_sandbox_validation_requests_per_minute": null,
  "max_upload_requests_per_hour": null,
  "max_publish_requests_per_day": null
}
```

Rules:

- `null` means disabled/not authorized, never unlimited
- external sandbox validation request budget must be explicitly authorized by a future gate
- upload request budget must remain disabled
- publish request budget must remain disabled
- retry must be deterministic and bounded
- timeout must be explicit
- timeout must produce evidence, not success
- rate-limit exhaustion must block and trace

## 10. External Sandbox Response Evidence

If a future gate authorizes external sandbox validation, response evidence must use this shape:

```json
{
  "result_status": "blocked | sandbox_validated | sandbox_failed | pending_sandbox",
  "result_evidence_available": true,
  "result_evidence_is_production": false,
  "result_evidence_type": "sandbox_validation_response | sandbox_error | timeout | rate_limit_response | credential_validation_response",
  "result_evidence_ref": "...",
  "receipt_hash": "...",
  "receipt_observed_at": "...",
  "external_identity_type": "none | sandbox_receipt_id",
  "published_url": null,
  "platform_content_id": null,
  "raw_response_persisted": false,
  "redacted_response_ref": "..."
}
```

Rules:

- sandbox response is not production receipt
- sandbox receipt ID is not production `platform_content_id`
- `result_evidence_is_production` must remain false
- `published_url` must remain null
- `platform_content_id` must remain null
- raw response must not include secrets
- redacted response must preserve enough schema evidence for audit
- `sandbox_validated` does not mean published
- `pending_sandbox` does not mean success
- `sandbox_failed` does not mean production failure

## 11. Append-Only Runtime Evidence

Future evidence collection must remain append-only.

Allowed future artifacts:

- `OUT/runtime_evidence/external_sandbox_validation.jsonl`
- `OUT/runtime_evidence/publish_lifecycle.jsonl`
- `OUT/runtime_evidence/external_sandbox_incidents.jsonl`
- `OUT/runtime_evidence/residual_monitoring_ledger.json`

Append-only rules:

- no rewrite
- no deletion
- no failed/pending/skipped event rewritten into success
- no sandbox event rewritten into production event
- no production identity backfilled into sandbox event
- every event must include target, mode, idempotency key, result evidence and boundary statement

## 12. Incident Hooks

External sandbox evidence collection must define hooks for:

- `PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE`
- `PUBLISHER_CREDENTIALS_MISSING`
- `PUBLISHER_CREDENTIAL_VALIDATION_FAILED`
- `PUBLISHER_RATE_LIMIT_EXCEEDED`
- `PUBLISHER_EXTERNAL_SANDBOX_TIMEOUT`
- `PUBLISHER_EXTERNAL_SANDBOX_SCHEMA_INVALID`
- `PUBLISHER_EXTERNAL_SANDBOX_VALIDATION_FAILED`
- `PUBLISHER_SANDBOX_RESPONSE_MISSING`
- `PUBLISHER_FAKE_SUCCESS_ATTEMPT`
- `PUBLISHER_FAKE_URL_OR_PLATFORM_ID_ATTEMPT`
- `ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH`
- `QC_NON_PUBLISHABLE_BLOCKED_PUBLISH`

Incident hooks must include:

- incident type
- severity
- run ID
- content ID
- target platform
- target mode
- evidence reference when available
- rationale

Incident hooks must not include:

- secret values
- tokens
- authorization headers
- raw platform response bodies
- production URL
- production platform content ID

## 13. Dependency Blocks

External sandbox validation must be blocked when:

- QC trace missing
- QC status is `HOLD`
- QC status is `REJECT`
- QC `publishable=false`
- Account Health decision is `HOLD`
- artifact manifest missing
- video artifact reference missing
- metadata payload reference missing
- credentials missing
- kill switch active
- rate limit not authorized
- target mode is not `sandbox_external_dry_run`
- mixed modes are present
- implicit provider binding is present

Blocked validation must produce trace evidence.

Blocked validation must not produce sandbox validation success.

## 14. Anti-Fake-Success Rules

Immediate failure if any future evidence contains:

- `result_status = succeeded`
- `result_status = published`
- `result_status = production_published`
- non-null `published_url`
- non-null `platform_content_id`
- `result_evidence_is_production = true`
- production receipt
- upload ID
- scheduler ID
- post-publish metric reference
- eligibility counted as success
- pending counted as success
- sandbox receipt counted as production evidence

External sandbox evidence must never close production publish evidence residuals.

## 15. Residual Monitoring Rules

These residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

External sandbox evidence collection may reduce only:

- external sandbox request envelope uncertainty
- sandbox response schema uncertainty
- sandbox timeout/error observability uncertainty
- credential presence validation uncertainty
- kill switch external-boundary confidence uncertainty

It must not reduce:

- production publish evidence residual
- real platform integration residual
- production result history residual
- post-publish metric residual
- attribution causality residual

## 16. Controlled Collection Stages

Recommended sequence:

```json
[
  "external_sandbox_evidence_collection_plan",
  "external_sandbox_evidence_collection_gate",
  "external_sandbox_request_envelope_implementation",
  "external_sandbox_request_envelope_gate",
  "external_sandbox_validation_execution_plan",
  "external_sandbox_validation_execution_gate"
]
```

No stage authorizes upload, scheduler activation, real publishing, production URL emission or production `platform_content_id` emission.

The first executable gate after this plan must validate the plan and freeze criteria before any new implementation.

## 17. Future Gate Requirements

Future gate:

- `docs/runtime/sandbox/evidence/EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE.md`
- `tests/gates/sandbox/run_external_sandbox_evidence_collection_gate.py`

Expected artifacts:

- `OUT/audit/external_sandbox_evidence_collection_gate/final_verdict.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/checklist_results.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/scenario_outputs.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/metrics.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/security_review.json`
- `OUT/audit/external_sandbox_evidence_collection_gate/residual_monitoring_review.json`

The gate must validate:

- target platform remains `SHORT_VIDEO_PLATFORM_SANDBOX_V1`
- mode remains `sandbox_external_dry_run`
- external validation is not enabled without gate approval
- no upload is authorized
- no publish is authorized
- no scheduler is authorized
- no URL can be emitted
- no `platform_content_id` can be emitted
- no secret value can appear in evidence
- sandbox response evidence is non-production
- production residuals remain open

## 18. Failure Conditions

Immediate `HOLD` if:

- external call is executed before gate approval
- platform API execution appears without gate approval
- upload occurs
- scheduler is invoked
- real publish occurs
- production URL appears
- production `platform_content_id` appears
- `result_evidence_is_production=true`
- sandbox receipt is treated as production evidence
- raw secret value appears in traces, JSONL, logs or audit artifacts
- Account Health `HOLD` is bypassed
- QC non-publishable state is bypassed
- mixed modes appear
- implicit provider binding appears
- production residual is closed
- post-publish metrics appear
- attribution causal claim appears
- Strategy, QC, Account Health, Orchestrator or core pipeline behavior changes

## 19. Exit Criteria

This plan is acceptable only if:

```json
{
  "external_sandbox_evidence_collection_planned": true,
  "external_call_implemented": false,
  "external_call_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "production_url_allowed": false,
  "production_platform_content_id_allowed": false,
  "secrets_presence_only": true,
  "sandbox_evidence_non_production": true,
  "production_residuals_remain_open": true,
  "boundary_preserved": true
}
```

## 20. Next Authorized Artifact

After this plan is accepted, the next authorized artifact is:

- `docs/runtime/sandbox/evidence/EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE.md`

That gate must validate this plan and freeze execution criteria before any external sandbox request envelope implementation or external call is authorized.

Real publishing remains unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Production URL and production `platform_content_id` emission remain unauthorized.
