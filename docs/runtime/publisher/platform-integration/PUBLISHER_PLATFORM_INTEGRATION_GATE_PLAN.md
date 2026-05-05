# PUBLISHER_PLATFORM_INTEGRATION_GATE_PLAN

## 1. Purpose

`PUBLISHER_PLATFORM_INTEGRATION_GATE_PLAN` defines the future gate that validates `PUBLISHER_PLATFORM_INTEGRATION_PLAN`.

This is a gate planning artifact only.

It does not implement platform integration, create a runner, execute tests, call platform APIs, upload content, schedule publication, emit real URLs, emit real platform content IDs, collect post-publish metrics, close production residuals, modify Publisher runtime behavior, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The gate must prove that the platform integration plan is safe, bounded, non-fabricating and unable to bypass QC or Account Health before any implementation starts.

Final principle:

> The platform integration gate validates readiness to implement a sandbox integration contract. It does not authorize platform execution or real publishing.

## 2. Scope

In scope:

- validation of `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_PLAN.md`
- target platform declaration
- sandbox external dry-run mode declaration
- single-mode enforcement
- no implicit provider binding
- credential and secret handling rules
- kill switch requirement
- rate-limit configuration requirement
- deterministic idempotency key requirement
- upload contract
- metadata contract
- result evidence contract
- production-vs-sandbox evidence distinction
- sandbox receipt semantics
- no production URL or production platform ID in sandbox
- Account Health `HOLD` blocking visibility
- QC non-publishable blocking visibility
- residual monitoring integrity
- gate-before-side-effect requirement

Out of scope:

- implementation of adapters
- platform API calls
- credential loading
- upload
- scheduler
- real publishing
- production URL emission
- production `platform_content_id` emission
- post-publish metrics
- attribution causality
- changes to Publisher runtime
- changes to QC
- changes to Account Health
- changes to Strategy
- changes to Orchestrator
- changes to Attribution
- changes to Experiment
- core pipeline changes

## 3. Preconditions

Required prior artifacts:

- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_PLAN.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE.md`
- `OUT/audit/publisher_dry_run_batch_collection_gate/final_verdict.json`

Required prior batch gate state:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "publisher_maturity": "TRACE_OBSERVABLE_AT_SCALE",
  "publishing_authorized": false,
  "platform_integration_authorized": false,
  "real_publishing_performed": false,
  "platform_api_called": false,
  "production_residuals_closed": false
}
```

The future gate must fail if prior artifacts are missing, unreadable, contradictory or show platform execution already occurred.

## 4. Evaluation Dimensions

The future gate must validate these dimensions:

```json
{
  "target_platform_defined": true,
  "sandbox_mode_defined": true,
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "no_implicit_provider_binding": true,
  "real_publishing_forbidden": true,
  "platform_api_execution_forbidden_until_gate": true,
  "secrets_no_leakage_policy_defined": true,
  "kill_switch_required": true,
  "kill_switch_blocks_publish_attempt": true,
  "rate_limits_required": true,
  "rate_limit_disabled_state_unambiguous": true,
  "idempotency_key_deterministic": true,
  "upload_contract_defined": true,
  "metadata_contract_defined": true,
  "result_evidence_contract_defined": true,
  "result_evidence_is_production_distinguished": true,
  "sandbox_receipt_not_production": true,
  "no_real_url_in_sandbox": true,
  "no_platform_content_id_in_sandbox": true,
  "account_health_hold_blocks": true,
  "qc_non_publishable_blocks": true,
  "production_residuals_remain_open": true
}
```

Each dimension must be evidence-backed by explicit text or schema in `PUBLISHER_PLATFORM_INTEGRATION_PLAN.md`.

## 5. Target Platform Validation

The future gate must validate the initial target exactly:

```json
{
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "publish_surface": "short_video",
  "real_publish_enabled": false,
  "real_upload_enabled": false,
  "scheduler_enabled": false,
  "platform_api_execution_authorized": false
}
```

Failure conditions:

- target platform missing
- target mode not `sandbox_external_dry_run`
- single-mode enforcement missing
- mixed modes are allowed
- real publish enabled
- real upload enabled
- scheduler enabled
- platform API execution authorized by the plan
- real provider binding implied without a separate approval artifact
- provider fallback into YouTube, TikTok, Instagram or any other real provider is allowed without a separate approval artifact

## 6. Sandbox Mode Validation

The gate must validate that sandbox mode:

- allows payload shape validation
- allows credential presence validation without secret disclosure
- allows rate-limit budget validation
- allows sandbox receipt only when genuinely returned by sandbox endpoint
- labels sandbox receipt as `sandbox_receipt`
- forbids treating sandbox receipt as production receipt
- requires `result_evidence_is_production = false` for sandbox evidence
- forbids treating sandbox result as published

Allowed result statuses must be limited to:

- `not_attempted`
- `skipped`
- `blocked`
- `sandbox_validated`
- `sandbox_failed`
- `pending_sandbox`

Forbidden result statuses:

- `succeeded`
- `published`
- `production_published`

## 7. Secrets And Credential Validation

The future gate must validate:

- credential source is environment or secret manager
- secret values are never logged
- secret values are never written to JSONL
- secret values are never written to audit artifacts
- tokens are never included in incident hooks
- authorization headers are never included in traces
- only credential presence, scope class and validation status may be traced
- missing credentials block integration

Required future env/secret contract:

- `PUBLISHER_PLATFORM_TARGET`
- `PUBLISHER_PLATFORM_MODE`
- `PUBLISHER_PLATFORM_ACCOUNT_ID`
- `PUBLISHER_PLATFORM_CLIENT_ID` or secret-manager equivalent
- `PUBLISHER_PLATFORM_CLIENT_SECRET` or secret-manager equivalent
- `PUBLISHER_PLATFORM_ACCESS_TOKEN` or secret-manager equivalent
- `PUBLISHER_PLATFORM_KILL_SWITCH`

The gate must fail if secret handling is absent, ambiguous, permissive or allows raw secret persistence.

## 8. Kill Switch Validation

The future gate must validate that kill switch is mandatory before external calls.

Required behavior:

```json
{
  "kill_switch_name": "PUBLISHER_PLATFORM_KILL_SWITCH",
  "active_value": "1",
  "default_safe_state": "blocked",
  "blocks_publish_attempt": true,
  "blocks_external_calls": true,
  "blocks_upload": true,
  "blocks_scheduler": true,
  "emits_incident_hook": true,
  "writes_lifecycle_event": true
}
```

Failure conditions:

- kill switch missing
- default state not safe
- kill switch does not block publish attempt
- kill switch does not block external calls
- kill switch does not block upload
- kill switch does not block scheduler
- kill switch does not emit trace/incident evidence

## 9. Rate Limit Validation

The future gate must validate that rate limits are required before any external call.

Required policy:

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
  "backoff_strategy": "deterministic_exponential_or_fixed",
  "rate_limit_exceeded_behavior": "block_and_trace"
}
```

The future gate must require sandbox validation, upload and publish request permissions to remain false until later approval.

`null` request limits must mean disabled/not authorized, never unlimited.

Rate-limit exhaustion must block and trace.

Unbounded retry is forbidden.

## 10. Upload Contract Validation

The gate must validate that the upload contract requires:

- `content_id`
- `run_id`
- `artifact_manifest_ref`
- `video_artifact_ref`
- `metadata_payload_ref`
- `qc_trace_ref`
- `account_health_trace_ref`
- `strategy_ref`
- `publish_eligibility_trace_ref`
- `idempotency_key`
- `platform_target`
- `platform_mode`

The gate must validate:

- idempotency key exists
- idempotency key is deterministic
- idempotency key is stable across identical inputs
- idempotency key is traceable to `run_id`, `content_id`, `artifact_manifest_ref`, `platform_target` and `platform_mode`
- idempotency key is not random

The gate must validate that upload is forbidden when:

- artifact manifest is missing
- video artifact is missing
- QC trace is missing
- QC is `HOLD`
- QC is `REJECT`
- QC `publishable` is false
- Account Health is `HOLD`
- kill switch is active
- production mode is requested before production gate approval

## 11. Metadata Contract Validation

The future gate must validate required metadata fields:

- `title`
- `description`
- `tags`
- `language`
- `visibility_mode`
- `account_id`
- `content_id`
- `runtime_policy_ref`
- `metadata_trace_ref`

The gate must validate that metadata rules forbid:

- fabricated claims
- fake compliance assertion
- fake regional targeting
- hidden performance prediction
- external platform ID before receipt
- publish URL before receipt

For this plan, only `sandbox_only` visibility may be authorized.

`public` visibility must remain forbidden.

## 12. Result Evidence Contract Validation

The future gate must validate the result evidence contract:

```json
{
  "result_status": "not_attempted | skipped | blocked | sandbox_validated | sandbox_failed | pending_sandbox",
  "result_evidence_available": true,
  "result_evidence_is_production": false,
  "result_evidence_type": "sandbox_receipt | platform_error | rate_limit_response | credential_validation_response | none",
  "result_evidence_ref": "...",
  "receipt_hash": "...",
  "receipt_observed_at": "...",
  "external_identity_type": "none | sandbox_receipt_id",
  "published_url": null,
  "platform_content_id": null
}
```

The gate must validate:

- result evidence exists only when external sandbox evidence exists
- result evidence explicitly distinguishes sandbox from production
- `result_evidence_is_production = false` is mandatory in sandbox mode
- missing `result_evidence_is_production` is invalid
- sandbox receipt is not production receipt
- sandbox receipt does not close production residuals
- platform error evidence is preserved
- timeout evidence is preserved
- pending evidence remains pending

The gate must fail if the plan permits:

- `published_url` in sandbox mode
- production `platform_content_id` in sandbox mode
- `result_evidence_is_production = true` in sandbox mode
- `result_status = succeeded`
- success without receipt
- receipt without raw evidence reference
- manually invented receipt ID

## 13. Authority And Boundary Validation

The future gate must validate:

- Publisher remains explicit publish authority
- QC remains final artifact evaluator
- Account Health `HOLD` blocks publish eligibility
- Strategy remains control layer and does not publish
- Orchestrator coordinates and does not publish
- Publisher does not become QC
- Publisher does not become Strategy
- Publisher does not become Attribution

Failure if:

- QC non-publishable can be bypassed
- Account Health `HOLD` can be bypassed
- Strategy is treated as publish permission
- Publisher claims outcome attribution
- Publisher claims performance prediction

## 14. Residual Monitoring Validation

The future gate must validate that these residuals remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

The gate must validate that sandbox planning can reduce only:

- platform payload shape uncertainty
- credential presence validation uncertainty
- rate-limit configuration uncertainty
- sandbox receipt schema uncertainty
- external timeout/error trace uncertainty

The gate must fail if the plan permits closing:

- production publish evidence residual
- real platform integration residual
- production result history residual
- post-publish metric residual
- attribution causality residual

## 15. Controlled Scenario Battery

The future gate should evaluate the plan against controlled semantic scenarios:

1. target platform is exactly `SHORT_VIDEO_PLATFORM_SANDBOX_V1`
2. mode is exactly `sandbox_external_dry_run`
3. only sandbox mode is allowed
4. mixed modes are rejected
5. implicit real provider binding is rejected
6. missing credentials block integration
7. secret value leakage is forbidden
8. kill switch active blocks publish attempt
9. kill switch active blocks external calls
10. rate-limit disabled state is not interpreted as unlimited
11. rate limit exceeded blocks and traces
12. idempotency key is deterministic
13. idempotency key is stable across identical inputs
14. QC `REJECT` blocks upload
15. QC `HOLD` blocks upload
16. QC `publishable=false` blocks upload
17. Account Health `HOLD` blocks upload
18. missing artifact manifest blocks upload
19. missing video artifact blocks upload
20. sandbox receipt is not production receipt
21. sandbox receipt does not authorize production publish
22. result evidence distinguishes production from sandbox
23. `result_evidence_is_production=true` in sandbox is rejected
24. fake URL in sandbox is rejected
25. fake `platform_content_id` in sandbox is rejected
26. `result_status=succeeded` is rejected
27. pending sandbox is not success
28. production residuals remain open
29. public visibility remains forbidden
30. platform API execution remains unauthorized by this plan
31. real publishing remains unauthorized by this plan

## 16. Checklist

The future gate must include checklist entries for:

- prior batch gate accepted
- platform integration plan exists
- target platform frozen
- sandbox mode frozen
- single mode enforced
- mixed modes forbidden
- implicit provider binding forbidden
- real publishing forbidden
- platform API execution unauthorized
- upload unauthorized
- scheduler unauthorized
- secrets policy complete
- kill switch required
- kill switch blocks publish attempt
- rate limits required
- disabled rate-limit state unambiguous
- idempotency key deterministic
- upload contract complete
- metadata contract complete
- result evidence contract complete
- result evidence production flag required
- sandbox receipt not production
- real URL forbidden
- production `platform_content_id` forbidden
- QC non-publishable blocks
- Account Health `HOLD` blocks
- no performance prediction authority
- production residuals remain open
- gate required before external side effects

Each checklist entry must include:

- `passed`
- evidence source
- failure reason when failed

## 17. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

Expected likely result:

- `GO_WITH_MONITORING`

`HOLD` if:

- target platform is missing or not frozen
- mode is not `sandbox_external_dry_run`
- single-mode enforcement is absent
- mixed modes are allowed
- implicit provider binding is allowed without separate approval
- real publish is authorized
- upload is authorized
- scheduler is authorized
- platform API execution is authorized before gate
- secrets can leak
- kill switch is missing
- kill switch does not block publish attempt
- rate limits are missing
- disabled rate-limit state can be interpreted as unlimited
- idempotency key is missing, random, unstable or untraceable
- upload contract is incomplete
- metadata contract is incomplete
- result evidence contract is incomplete
- result evidence lacks production-vs-sandbox distinction
- sandbox receipt can be treated as production
- `result_evidence_is_production = true` is allowed in sandbox
- real URL is allowed in sandbox
- production `platform_content_id` is allowed in sandbox
- QC non-publishable can be bypassed
- Account Health `HOLD` can be bypassed
- production residuals are closed
- performance prediction or attribution authority appears
- core, Strategy, QC, Account Health or Orchestrator changes are implied

`GO_WITH_MONITORING` if:

- all critical checks pass
- plan is safe for future sandbox implementation planning
- production residuals remain open
- platform API execution remains unauthorized
- real publishing remains unauthorized

`GO` is not expected at this stage because this is still pre-implementation and pre-platform-execution.

## 18. Required Future Artifacts

Future formal gate:

- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_GATE.md`

Future runner:

- `tests/gates/publisher/run_publisher_platform_integration_gate.py`

Future audit artifacts:

- `OUT/audit/publisher_platform_integration_gate/final_verdict.json`
- `OUT/audit/publisher_platform_integration_gate/checklist_results.json`
- `OUT/audit/publisher_platform_integration_gate/scenario_outputs.json`
- `OUT/audit/publisher_platform_integration_gate/metrics.json`
- `OUT/audit/publisher_platform_integration_gate/contract_review.json`
- `OUT/audit/publisher_platform_integration_gate/security_review.json`
- `OUT/audit/publisher_platform_integration_gate/residual_monitoring_review.json`

## 19. Final Verdict Schema

Future gate final verdict must include:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "PUBLISHER_PLATFORM_INTEGRATION_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "no_implicit_provider_binding": true,
  "plan_valid": true,
  "secrets_policy_valid": true,
  "kill_switch_required": true,
  "kill_switch_blocks_publish_attempt": true,
  "rate_limits_required": true,
  "rate_limit_disabled_state_unambiguous": true,
  "idempotency_key_deterministic": true,
  "upload_contract_valid": true,
  "metadata_contract_valid": true,
  "result_evidence_contract_valid": true,
  "result_evidence_is_production_distinguished": true,
  "sandbox_receipt_not_production": true,
  "real_url_forbidden": true,
  "platform_content_id_forbidden": true,
  "account_health_hold_blocks": true,
  "qc_non_publishable_blocks": true,
  "production_residuals_closed": false,
  "platform_api_execution_authorized": false,
  "real_publishing_authorized": false,
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_SANDBOX_ADAPTER_IMPLEMENTATION_PLAN | HOLD_BEFORE_SANDBOX_ADAPTER_IMPLEMENTATION"
}
```

## 20. Next Authorized Step

If this gate plan is accepted, the next authorized artifact is:

- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_GATE.md`

This next artifact must formalize the executable gate contract.

It must not implement platform integration.

It must not call platform APIs.

It must not upload.

It must not schedule.

It must not publish.

Real publishing remains unauthorized.
