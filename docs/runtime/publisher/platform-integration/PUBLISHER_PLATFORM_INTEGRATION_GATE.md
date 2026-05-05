# PUBLISHER_PLATFORM_INTEGRATION_GATE

## 1. Purpose

`PUBLISHER_PLATFORM_INTEGRATION_GATE` is the formal executable gate contract for validating Publisher platform integration readiness before sandbox adapter implementation.

This is an audit gate specification.

It does not implement platform integration, create an adapter, create a runner, execute tests, call platform APIs, load credentials, upload content, schedule publication, emit real URLs, emit real platform content IDs, collect post-publish metrics, close production residuals, modify Publisher runtime behavior, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

The future runner is:

- `tests/gates/publisher/run_publisher_platform_integration_gate.py`

The gate validates the integration plan and freezes the conditions required before any sandbox adapter implementation.

Final principle:

> The Publisher platform integration gate proves the sandbox integration contract is safe to implement. It does not authorize platform execution or real publishing.

## 2. Scope

In scope:

- platform integration plan integrity
- target platform identity
- sandbox-only mode
- single-mode enforcement
- no mixed modes
- no implicit provider binding
- secrets and credential policy
- kill switch semantics
- rate-limit policy
- idempotency key semantics
- upload contract
- metadata contract
- result evidence contract
- sandbox receipt semantics
- production-vs-sandbox evidence separation
- Account Health `HOLD` block preservation
- QC non-publishable block preservation
- residual monitoring integrity
- boundary preservation

Out of scope:

- adapter implementation
- platform SDK/API selection
- credential loading
- platform API execution
- upload
- scheduler
- real publishing
- real URL emission
- real `platform_content_id` emission
- post-publish metrics
- attribution causality
- runtime changes
- Publisher behavior changes
- QC changes
- Account Health changes
- Strategy changes
- Orchestrator changes
- core pipeline changes

## 3. Preconditions

Required documents:

- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_PLAN.md`
- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_GATE_PLAN.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE.md`

Required audit artifacts:

- `OUT/audit/publisher_dry_run_batch_collection_gate/final_verdict.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/coverage_review.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/representation_review.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/append_only_checks.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/temporal_consistency.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/anti_fake_causality_review.json`
- `OUT/audit/publisher_dry_run_batch_collection_gate/residual_monitoring_review.json`

Required prior state:

```json
{
  "batch_gate_verdict": "GO_WITH_MONITORING",
  "publisher_maturity": "TRACE_OBSERVABLE_AT_SCALE",
  "publishing_authorized": false,
  "platform_integration_authorized": false,
  "success_count": 0,
  "real_publishing_performed": false,
  "platform_api_called": false,
  "production_residuals_closed": false
}
```

The future runner must return `HOLD` if any required artifact is missing, invalid, contradictory, or indicates platform side effects already occurred.

## 4. Required Fixed Contract

The gate must validate this exact fixed contract:

```json
{
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "result_evidence_is_production": false,
  "idempotency_key_deterministic": true,
  "no_implicit_provider_binding": true,
  "kill_switch_blocks_publish_attempt": true,
  "sandbox_validation_requests_allowed": false,
  "upload_requests_allowed": false,
  "publish_requests_allowed": false,
  "platform_api_execution_authorized": false,
  "real_publishing_authorized": false
}
```

Any weakening of this contract is a blocker.

## 5. Gate Blocks A-P

### Block A - Artifact Integrity

Validate required documents and JSON audit artifacts exist and parse.

Fail if any required artifact is missing, invalid JSON, unreadable, or contradictory.

### Block B - Prior Batch Gate Integrity

Validate dry-run batch gate result:

- verdict is `GO` or `GO_WITH_MONITORING`
- `publisher_maturity = TRACE_OBSERVABLE_AT_SCALE`
- `minimum_batch_coverage_met = true`
- `representation_valid = true`
- `append_only_valid = true`
- `temporal_consistency_valid = true`
- `anti_fake_causality_valid = true`
- `success_count = 0`
- `platform_api_called = false`
- `real_publishing_performed = false`
- `production_residuals_closed = false`

Fail on any prior platform side effect or fake success.

### Block C - Target Platform Contract

Validate:

- `target_platform_id = SHORT_VIDEO_PLATFORM_SANDBOX_V1`
- target is a sandbox target
- no production provider is implied
- no real provider binding exists without separate approval artifact

Fail if YouTube, TikTok, Instagram or another real provider is used as an implementation target without separate approval.

### Block D - Sandbox Mode Contract

Validate:

- `target_mode = sandbox_external_dry_run`
- `single_mode_enforced = true`
- `no_mixed_modes_allowed = true`
- no fallback into another mode
- no production mode

Fail if any other mode can coexist or be used as fallback.

### Block E - External Side Effect Prohibition

Validate:

- platform API execution unauthorized
- upload unauthorized
- scheduler unauthorized
- real publishing unauthorized
- real URL emission unauthorized
- real `platform_content_id` emission unauthorized

Fail if the plan permits any external side effect before a later gate.

### Block F - Secrets And Credential Policy

Validate:

- credentials come from environment or secret manager
- secret values are never logged
- secret values are never written to JSONL
- secret values are never written to audit artifacts
- tokens are not included in incident hooks
- authorization headers are not included in traces
- only secret presence/scope/status can be traced
- missing credentials block integration

Fail if raw secret leakage is possible or ambiguous.

### Block G - Kill Switch Semantics

Validate:

- `PUBLISHER_PLATFORM_KILL_SWITCH` is required
- default safe state is blocked
- kill switch blocks publish attempt
- kill switch blocks external calls
- kill switch blocks upload
- kill switch blocks scheduler
- kill switch emits incident hook
- kill switch writes lifecycle evidence

Fail if kill switch does not block attempt state.

### Block H - Rate Limit Semantics

Validate:

- `publisher_platform_rate_limits_v1` exists
- `sandbox_validation_requests_allowed = false`
- `upload_requests_allowed = false`
- `publish_requests_allowed = false`
- request limits use `null` to mean disabled/not authorized
- disabled limit state cannot mean unlimited
- burst is disabled
- retry/backoff is deterministic and bounded
- rate-limit exhaustion blocks and traces

Fail if `0` or missing limits can be interpreted as unlimited.

### Block I - Upload Contract

Validate required upload fields:

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

Validate upload is forbidden when:

- artifact manifest missing
- video artifact missing
- QC trace missing
- QC `HOLD`
- QC `REJECT`
- QC `publishable=false`
- Account Health `HOLD`
- kill switch active
- production mode requested

### Block J - Idempotency Semantics

Validate:

- idempotency key is required
- deterministic
- stable across identical inputs
- traceable to `run_id`, `content_id`, `artifact_manifest_ref`, `platform_target`, and `platform_mode`
- not random

Fail if idempotency key is optional, unstable, random, or untraceable.

### Block K - Metadata Contract

Validate metadata requires:

- `title`
- `description`
- `tags`
- `language`
- `visibility_mode`
- `account_id`
- `content_id`
- `runtime_policy_ref`
- `metadata_trace_ref`

Validate metadata forbids:

- fabricated claims
- fake compliance assertion
- fake regional targeting
- hidden performance prediction
- external platform ID before receipt
- publish URL before receipt
- `public` visibility

Only `sandbox_only` visibility may be authorized at this stage.

### Block L - Result Evidence Contract

Validate:

- result statuses limited to `not_attempted`, `skipped`, `blocked`, `sandbox_validated`, `sandbox_failed`, `pending_sandbox`
- `result_evidence_is_production = false` required in sandbox
- missing `result_evidence_is_production` invalid
- `result_evidence_available = true` only with actual external sandbox response
- `external_identity_type` limited to `none` or `sandbox_receipt_id`
- `published_url = null`
- `platform_content_id = null`
- sandbox receipt is not production receipt
- sandbox receipt does not close production residuals

Fail if `result_status=succeeded`, `published`, or `production_published` is allowed.

### Block M - Authority And Boundary Preservation

Validate:

- Publisher remains explicit publish authority
- QC remains final artifact evaluator
- Account Health `HOLD` blocks publish eligibility
- Strategy remains control layer
- Orchestrator coordinates only
- Publisher does not become QC, Strategy or Attribution

Fail if Publisher claims performance prediction, attribution causality, QC authority, Strategy authority, or Account Health override authority.

### Block N - Residual Monitoring Integrity

Validate these remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

Fail if sandbox planning closes production residuals, platform integration residuals, result history residuals, post-publish metric residuals, or attribution causality residuals.

### Block O - Security And Logical Vulnerability Surface

Fail on:

- fake success path
- fake URL path
- fake platform ID path
- secret leakage path
- mixed mode path
- implicit provider binding path
- unbounded retry path
- rate-limit unlimited ambiguity
- kill switch bypass
- Account Health `HOLD` override
- QC non-publishable override
- performance prediction authority
- hidden external side effect

### Block P - Final Release Decision

Derive final verdict from Blocks A-O.

Do not hardcode verdict.

Expected likely result: `GO_WITH_MONITORING`.

## 6. Controlled Scenario Battery

Future runner must validate at least:

1. `target_platform_exact_match`
2. `sandbox_mode_exact_match`
3. `single_mode_enforced`
4. `mixed_mode_rejected`
5. `implicit_provider_binding_rejected`
6. `missing_credentials_block_integration`
7. `secret_value_leakage_forbidden`
8. `kill_switch_blocks_publish_attempt`
9. `kill_switch_blocks_external_call`
10. `rate_limit_disabled_not_unlimited`
11. `rate_limit_exceeded_blocks_and_traces`
12. `idempotency_key_deterministic`
13. `idempotency_key_stable_for_identical_inputs`
14. `qc_reject_blocks_upload`
15. `qc_hold_blocks_upload`
16. `qc_publishable_false_blocks_upload`
17. `account_health_hold_blocks_upload`
18. `missing_artifact_manifest_blocks_upload`
19. `missing_video_artifact_blocks_upload`
20. `sandbox_receipt_not_production_receipt`
21. `sandbox_receipt_does_not_authorize_production_publish`
22. `result_evidence_production_flag_required`
23. `result_evidence_is_production_true_rejected`
24. `fake_url_in_sandbox_rejected`
25. `fake_platform_content_id_in_sandbox_rejected`
26. `result_status_succeeded_rejected`
27. `pending_sandbox_not_success`
28. `production_residuals_remain_open`
29. `public_visibility_forbidden`
30. `platform_api_execution_unauthorized`
31. `real_publishing_unauthorized`
32. `performance_prediction_authority_absent`
33. `attribution_causality_absent`
34. `backward_precondition_artifacts_valid`

## 7. Checklist

Future runner must write checklist entries for:

- artifact integrity
- prior batch gate integrity
- target platform frozen
- sandbox mode frozen
- single mode enforced
- mixed modes forbidden
- implicit provider binding forbidden
- real publishing forbidden
- platform API execution unauthorized
- upload unauthorized
- scheduler unauthorized
- real URL forbidden
- production platform content ID forbidden
- secrets policy complete
- secret leakage impossible by contract
- kill switch required
- kill switch blocks publish attempt
- kill switch blocks external calls
- rate limits required
- disabled rate-limit state unambiguous
- idempotency key deterministic
- idempotency key stable
- upload contract complete
- metadata contract complete
- result evidence contract complete
- result evidence production flag required
- sandbox receipt not production
- Account Health `HOLD` blocks
- QC non-publishable blocks
- no performance prediction authority
- no attribution causality authority
- production residuals remain open
- gate required before external side effects

Each checklist entry must include:

- `passed`
- `evidence_source`
- `failure_reason` when failed

## 8. Required Future Artifacts

Future runner must generate:

- `OUT/audit/publisher_platform_integration_gate/final_verdict.json`
- `OUT/audit/publisher_platform_integration_gate/checklist_results.json`
- `OUT/audit/publisher_platform_integration_gate/scenario_outputs.json`
- `OUT/audit/publisher_platform_integration_gate/metrics.json`
- `OUT/audit/publisher_platform_integration_gate/contract_review.json`
- `OUT/audit/publisher_platform_integration_gate/security_review.json`
- `OUT/audit/publisher_platform_integration_gate/residual_monitoring_review.json`

## 9. Metrics

Future metrics must include:

```json
{
  "critical_failures": 0,
  "blocking_failures_count": 0,
  "scenario_count": 0,
  "scenario_pass_count": 0,
  "checklist_count": 0,
  "checklist_pass_count": 0,
  "platform_api_called": false,
  "real_publishing_performed": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "fake_success_detected": false,
  "fake_url_or_platform_id_detected": false,
  "secret_leakage_detected": false,
  "mixed_mode_detected": false,
  "implicit_provider_binding_detected": false,
  "production_residuals_closed": false
}
```

## 10. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

`HOLD` if:

- any block A-O fails
- prior batch gate is missing or contradictory
- target platform is not `SHORT_VIDEO_PLATFORM_SANDBOX_V1`
- target mode is not `sandbox_external_dry_run`
- single-mode enforcement is missing
- mixed modes are allowed
- implicit provider binding is allowed
- platform API execution is authorized
- upload is authorized
- scheduler is authorized
- real publishing is authorized
- real URL is allowed
- production platform content ID is allowed
- secrets can leak
- kill switch does not block publish attempt
- rate-limit disabled state can mean unlimited
- idempotency key is missing or nondeterministic
- upload contract incomplete
- metadata contract incomplete
- result evidence contract incomplete
- result evidence production flag missing
- `result_evidence_is_production=true` allowed in sandbox
- sandbox receipt can become production evidence
- QC non-publishable can be bypassed
- Account Health `HOLD` can be bypassed
- production residuals are closed
- performance prediction authority appears
- attribution causality authority appears
- runtime/core/Strategy/QC/Account Health/Orchestrator mutation is implied

`GO_WITH_MONITORING` if:

- all critical blocks pass
- platform integration plan is safe for future sandbox adapter implementation planning
- platform API execution remains unauthorized
- upload remains unauthorized
- real publishing remains unauthorized
- production residuals remain open

`GO` is not expected at this stage because the system is still pre-implementation and pre-side-effect external.

The runner must derive verdict from evidence and must not hardcode it.

## 11. Final Verdict Schema

Future `final_verdict.json` must include:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "PUBLISHER_PLATFORM_INTEGRATION_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "result_evidence_is_production": false,
  "idempotency_key_deterministic": true,
  "no_implicit_provider_binding": true,
  "kill_switch_blocks_publish_attempt": true,
  "sandbox_validation_requests_allowed": false,
  "upload_requests_allowed": false,
  "publish_requests_allowed": false,
  "platform_api_execution_authorized": false,
  "real_publishing_authorized": false,
  "secrets_policy_valid": true,
  "rate_limits_required": true,
  "upload_contract_valid": true,
  "metadata_contract_valid": true,
  "result_evidence_contract_valid": true,
  "sandbox_receipt_not_production": true,
  "real_url_forbidden": true,
  "platform_content_id_forbidden": true,
  "account_health_hold_blocks": true,
  "qc_non_publishable_blocks": true,
  "production_residuals_closed": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "metrics": {},
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_SANDBOX_ADAPTER_IMPLEMENTATION_PLAN | HOLD_BEFORE_SANDBOX_ADAPTER_IMPLEMENTATION"
}
```

## 12. Expected Recommendation

If the future gate returns `GO_WITH_MONITORING`, the next authorized planning artifact is:

- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_PLAN.md`

This next artifact may plan implementation of a sandbox adapter only.

It must not authorize:

- production provider binding
- real upload
- scheduler
- real publish
- production URL emission
- production `platform_content_id` emission

## 13. Final Criteria

The gate passes only if:

```json
{
  "plan_safe_to_implement_sandbox_adapter": true,
  "external_side_effects_authorized": false,
  "real_publishing_authorized": false,
  "platform_api_execution_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "fake_success_surface_locked": true,
  "production_residuals_remain_open": true,
  "publisher_boundary_preserved": true
}
```

## 14. Next Authorized Step

After this gate specification is accepted, the next authorized artifact is:

- `tests/gates/publisher/run_publisher_platform_integration_gate.py`

No platform integration implementation is authorized until that runner executes and returns an acceptable verdict.

Real publishing remains unauthorized.

Platform API execution remains unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Production URL and production `platform_content_id` emission remain unauthorized.
