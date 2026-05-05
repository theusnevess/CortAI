# SANDBOX_ADAPTER_IMPLEMENTATION_GATE

## 1. Purpose

`SANDBOX_ADAPTER_IMPLEMENTATION_GATE` is the formal future gate specification for validating a Publisher sandbox adapter implementation.

This artifact freezes the executable contract before any sandbox adapter code is written.

It does not implement the adapter, create a runner, execute tests, call platform APIs, load real credentials, upload content, schedule publication, emit real URLs, emit real platform content IDs, collect post-publish metrics, close production residuals, modify Publisher runtime behavior, modify QC, modify Account Health, modify Strategy, modify Orchestrator, modify Attribution, modify Experiment, or modify the core pipeline.

Future runner:

- `tests/gates/sandbox/run_sandbox_adapter_implementation_gate.py`

Final principle:

> The sandbox adapter gate proves no-side-effect sandbox implementation safety. It does not authorize platform execution or real publishing.

## 2. Scope

In scope:

- sandbox adapter contract
- sandbox-only target and mode enforcement
- no implicit provider binding
- credential presence/status handling
- secret non-leakage
- kill switch behavior
- rate-limit disabled-state semantics
- deterministic idempotency key
- upload and metadata validation
- dependency blocks
- sandbox result evidence
- production-vs-sandbox evidence separation
- append-only lifecycle behavior
- incident hooks
- anti-fake-success behavior
- residual monitoring integrity

Out of scope:

- production adapter
- real platform SDK/API calls
- credential value loading
- upload
- scheduler
- real publishing
- production URL
- production `platform_content_id`
- post-publish metrics
- attribution causality
- Strategy changes
- QC changes
- Account Health changes
- Orchestrator changes
- core pipeline changes

## 3. Preconditions

Required prior documents:

- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_PLAN.md`
- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_GATE.md`
- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_PLAN.md`

Required prior audit artifacts:

- `OUT/audit/publisher_platform_integration_gate/final_verdict.json`

Required prior state:

```json
{
  "publisher_platform_integration_gate": "GO_WITH_MONITORING",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "platform_api_execution_authorized": false,
  "real_publishing_authorized": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "blocking_failures": []
}
```

Required future implementation files:

- `backend/app/creative/agents/publisher/sandbox_adapter.py`
- `backend/app/creative/agents/publisher/sandbox_contracts.py`
- `backend/app/creative/agents/publisher/sandbox_security.py`
- `tests/publisher/unit/test_publisher_sandbox_adapter_unittest.py`

The future gate must fail if these implementation files are missing after implementation is claimed complete.

## 4. Adapter Contract

Future adapter must expose deterministic, serializable primitives equivalent to:

- `SandboxAdapterInput`
- `SandboxAdapterResult`
- `SandboxCredentialStatus`
- `SandboxRateLimitStatus`
- `SandboxKillSwitchStatus`
- `SandboxResultEvidence`
- `SandboxAdapter`

Required fixed contract:

```json
{
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "no_implicit_provider_binding": true,
  "platform_api_allowed": false,
  "upload_allowed": false,
  "scheduler_allowed": false,
  "real_publish_allowed": false,
  "real_url_allowed": false,
  "platform_content_id_allowed": false,
  "kill_switch_required": true,
  "secrets_presence_only": true,
  "sandbox_receipt_not_production": true,
  "result_evidence_is_production": false,
  "production_residuals_remain_open": true
}
```

## 5. Required Behavior

Future adapter may:

- validate payload shape
- validate metadata shape
- validate credential presence/status
- validate kill switch state
- validate rate-limit policy state
- validate idempotency key determinism
- emit sandbox validation result
- emit sandbox incident hooks
- write append-only lifecycle evidence

Future adapter must not:

- call a real platform API
- upload
- schedule
- publish
- emit a production URL
- emit a production platform content ID
- load or log raw secret values
- bind implicitly to a real provider
- close production residuals
- become QC, Strategy or Attribution

## 6. Controlled Scenario Battery

The future gate must validate these 27 required scenarios:

1. `target_and_mode_exact_match`
   - target is `SHORT_VIDEO_PLATFORM_SANDBOX_V1`
   - mode is `sandbox_external_dry_run`

2. `mixed_mode_rejected`
   - multiple modes or fallback modes are rejected

3. `implicit_provider_binding_rejected`
   - real provider names or direct provider bindings fail without separate approval

4. `missing_credentials_blocked`
   - missing credentials produce blocked result and incident hook

5. `secret_value_not_logged_or_persisted`
   - secret values never appear in traces, JSONL, audit artifacts or incidents

6. `kill_switch_blocks_publish_attempt`
   - active kill switch sets `attempted=false`, `attempt_status=blocked`, `result_status=blocked`

7. `kill_switch_blocks_external_call`
   - active kill switch prevents all external call flags

8. `disabled_rate_limit_is_not_unlimited`
   - disabled/null rate-limit state is blocked/not authorized, never unlimited

9. `deterministic_idempotency_key`
   - key is deterministic from approved input tuple

10. `stable_idempotency_key_for_identical_inputs`
    - identical inputs produce identical key

11. `qc_reject_blocks`
    - QC `REJECT` blocks sandbox attempt

12. `qc_hold_blocks`
    - QC `HOLD` blocks sandbox attempt

13. `qc_publishable_false_blocks`
    - QC `publishable=false` blocks sandbox attempt

14. `account_health_hold_blocks`
    - Account Health `HOLD` blocks sandbox attempt

15. `missing_artifact_blocks`
    - missing artifact manifest blocks sandbox attempt

16. `missing_video_blocks`
    - missing video artifact blocks sandbox attempt

17. `sandbox_receipt_not_production`
    - sandbox receipt is labeled non-production and cannot be production receipt

18. `production_evidence_flag_false`
    - `result_evidence_is_production=false` in every sandbox result

19. `fake_url_rejected`
    - any URL in sandbox result is rejected

20. `fake_platform_content_id_rejected`
    - any platform content ID in sandbox result is rejected

21. `result_status_succeeded_rejected`
    - `result_status=succeeded` is rejected

22. `append_only_lifecycle_preserved`
    - lifecycle writer appends only and does not rewrite prior events

23. `residuals_remain_open`
    - production residuals remain open

24. `no_platform_api_call`
    - platform API call flag remains false

25. `no_upload`
    - upload flag remains false

26. `no_scheduler`
    - scheduler flag remains false

27. `no_real_publish`
    - real publishing flag remains false

## 7. Checklist

Future runner must include checklist entries for:

- implementation files present
- adapter imports successfully
- contracts serialize
- target platform exact
- target mode exact
- single mode enforced
- mixed modes rejected
- implicit provider binding rejected
- credentials status only
- secret leakage absent
- kill switch required
- kill switch blocks publish attempt
- kill switch blocks external calls
- rate-limit disabled state not unlimited
- idempotency deterministic
- idempotency stable
- upload contract validated
- metadata contract validated
- dependency blocks enforced
- sandbox receipt non-production
- result evidence production flag false
- fake URL rejected
- fake platform content ID rejected
- `result_status=succeeded` rejected
- append-only lifecycle valid
- incident hooks emitted
- platform API not called
- upload not performed
- scheduler not invoked
- real publish not performed
- production residuals remain open
- Publisher boundary preserved
- QC unchanged
- Account Health unchanged
- Strategy unchanged
- Orchestrator unchanged
- core pipeline unchanged

Each checklist entry must include:

- `passed`
- `evidence_source`
- `failure_reason` when failed

## 8. Required Future Artifacts

Future runner must generate:

- `OUT/audit/sandbox_adapter_implementation_gate/final_verdict.json`
- `OUT/audit/sandbox_adapter_implementation_gate/checklist_results.json`
- `OUT/audit/sandbox_adapter_implementation_gate/scenario_outputs.json`
- `OUT/audit/sandbox_adapter_implementation_gate/metrics.json`
- `OUT/audit/sandbox_adapter_implementation_gate/contract_review.json`
- `OUT/audit/sandbox_adapter_implementation_gate/security_review.json`
- `OUT/audit/sandbox_adapter_implementation_gate/side_effect_review.json`
- `OUT/audit/sandbox_adapter_implementation_gate/residual_monitoring_review.json`

## 9. Metrics

Future metrics must include:

```json
{
  "critical_failures": 0,
  "blocking_failures_count": 0,
  "scenario_count": 27,
  "scenario_pass_count": 27,
  "checklist_count": 0,
  "checklist_pass_count": 0,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "secret_leakage_detected": false,
  "mixed_mode_detected": false,
  "implicit_provider_binding_detected": false,
  "fake_success_detected": false,
  "production_residuals_closed": false
}
```

## 10. Verdict Semantics

Allowed verdicts:

- `GO`
- `GO_WITH_MONITORING`
- `HOLD`

Expected likely verdict:

- `GO_WITH_MONITORING`

`HOLD` if:

- adapter missing
- contracts missing
- serialization fails
- target or mode differs
- mixed mode accepted
- implicit provider accepted
- raw secret value appears
- kill switch does not block attempt
- kill switch does not block external call
- disabled rate limit can mean unlimited
- idempotency key missing, random or unstable
- QC `REJECT`, `HOLD` or `publishable=false` does not block
- Account Health `HOLD` does not block
- missing artifact/video does not block
- sandbox receipt treated as production
- `result_evidence_is_production=true`
- fake URL accepted
- fake platform content ID accepted
- `result_status=succeeded` accepted
- append-only lifecycle violated
- platform API called
- upload performed
- scheduler invoked
- real publish performed
- production residual closed
- QC, Account Health, Strategy, Orchestrator or core modified

`GO_WITH_MONITORING` if:

- all critical checks pass
- sandbox adapter is implemented as no-side-effect sandbox-only validator
- production residuals remain open
- platform API remains disabled
- upload remains disabled
- scheduler remains disabled
- real publishing remains disabled

`GO` is not expected at this stage because production platform integration and publishing remain absent by design.

The future runner must derive verdict from evidence and must not hardcode it.

## 11. Final Verdict Schema

Future `final_verdict.json` must include:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "3",
  "audit_type": "SANDBOX_ADAPTER_IMPLEMENTATION_GATE",
  "verdict": "GO | GO_WITH_MONITORING | HOLD",
  "timestamp": "...",
  "target_platform_id": "SHORT_VIDEO_PLATFORM_SANDBOX_V1",
  "target_mode": "sandbox_external_dry_run",
  "adapter_present": true,
  "contracts_serializable": true,
  "single_mode_enforced": true,
  "no_mixed_modes_allowed": true,
  "no_implicit_provider_binding": true,
  "kill_switch_blocks_publish_attempt": true,
  "secrets_presence_only": true,
  "idempotency_key_deterministic": true,
  "sandbox_receipt_not_production": true,
  "result_evidence_is_production": false,
  "platform_api_called": false,
  "upload_performed": false,
  "scheduler_invoked": false,
  "real_publishing_performed": false,
  "real_url_emitted": false,
  "platform_content_id_emitted": false,
  "production_residuals_closed": false,
  "metrics": {},
  "blocking_failures": [],
  "residual_monitoring": [],
  "recommendation": "PROCEED_TO_SANDBOX_ADAPTER_IMPLEMENTATION | HOLD_BEFORE_SANDBOX_ADAPTER_IMPLEMENTATION"
}
```

## 12. Residual Monitoring Rules

These residuals must remain open:

- `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`
- `PLATFORM_INTEGRATION_NOT_ENABLED`
- `PUBLISH_RESULT_HISTORY_STILL_SHORT`

Sandbox adapter implementation may reduce only:

- adapter contract uncertainty
- sandbox payload validation uncertainty
- credential presence validation uncertainty
- no-side-effect implementation uncertainty
- sandbox result schema uncertainty

It must not reduce:

- production publish evidence residual
- real platform integration residual
- production result history residual
- post-publish metric residual
- attribution causality residual

## 13. Final Criteria

The gate passes only if:

```json
{
  "sandbox_adapter_safe": true,
  "external_side_effects_detected": false,
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

- `backend/app/creative/agents/publisher/sandbox_contracts.py`
- `backend/app/creative/agents/publisher/sandbox_security.py`
- `backend/app/creative/agents/publisher/sandbox_adapter.py`
- `tests/publisher/unit/test_publisher_sandbox_adapter_unittest.py`

Implementation remains limited to sandbox-only no-side-effect adapter code.

The runner `tests/gates/sandbox/run_sandbox_adapter_implementation_gate.py` must be created only after the implementation exists.

Real publishing remains unauthorized.

Platform API execution remains unauthorized.

Upload remains unauthorized.

Scheduler remains unauthorized.

Production URL and production `platform_content_id` emission remain unauthorized.
