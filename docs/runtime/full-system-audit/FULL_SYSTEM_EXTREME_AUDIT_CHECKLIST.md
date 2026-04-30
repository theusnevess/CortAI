# FULL_SYSTEM_EXTREME_AUDIT_CHECKLIST

## 1. Purpose

`FULL_SYSTEM_EXTREME_AUDIT_CHECKLIST` defines the full-system extreme audit checklist for CortAI, External Sandbox and Publisher Governance.

This is a checklist artifact only.

It does not execute tests, run gates, modify runtime, authorize runtime integration, authorize runtime wiring, authorize external calls, authorize platform API usage, authorize upload, authorize scheduling, authorize publishing, close production residuals or change any agent behavior.

Expected final system state if the checklist passes:

```json
{
  "expected_verdict": "GO_WITH_MONITORING",
  "production_ready": false,
  "external_execution_authorized": false,
  "runtime_integration_authorized": false,
  "current_system_state": "SAFE_PRE_CROSSING"
}
```

Core rule:

> Full-system audit proves safety before crossing external boundaries. It does not create permission to cross them.

## 2. Current Baseline

Current known state:

```json
{
  "offline_preparation": "ACCEPTED_WITH_MONITORING",
  "readiness_gate": "GO_WITH_MONITORING",
  "runtime_integration_gate": "GO_WITH_MONITORING",
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "implementation_authorized": false,
  "phase_status": "STRUCTURALLY_COMPLETE"
}
```

The previous chain is closed:

```json
{
  "remaining_technical_gates": 0,
  "current_chain_closed": true,
  "next_work": "SEPARATE_RUNTIME_INTEGRATION_AUTHORIZATION_CHAIN_PLANNING_ONLY"
}
```

## 3. Integrity Architecture

- [ ] Kernel continues neutral, with no CortAI domain import.
- [ ] Domain contains no Kernel execution logic.
- [ ] Publisher has not become an external client.
- [ ] Orchestrator remains coordinator, not external executor.
- [ ] Strategy remains control layer.
- [ ] QC remains final artifact evaluator.
- [ ] Account Health `HOLD` remains blocking.
- [ ] Attribution receives no causality without real evidence.
- [ ] Experiment creates no publish authority.
- [ ] Core pipeline was not altered without formal gate.
- [ ] No runtime path was modified by offline slices.
- [ ] No hidden step was added to Orchestrator.
- [ ] No bypass was created for Publisher, QC or Account Health.

## 4. External Boundary Audit

- [ ] `external_call_authorized = false` in all applicable artifacts.
- [ ] `runtime_integration_authorized = false`.
- [ ] `runtime_wiring_authorized = false`.
- [ ] `http_client_allowed = false`.
- [ ] `platform_sdk_allowed = false`.
- [ ] `endpoint_allowed = false`.
- [ ] `dns_network_allowed = false`.
- [ ] `api_call_allowed = false`.
- [ ] `credential_value_access_authorized = false`.
- [ ] `request_transformation_authorized = false`.
- [ ] `transport_payload_authorized = false`.
- [ ] `upload_authorized = false`.
- [ ] `scheduler_authorized = false`.
- [ ] `real_publish_authorized = false`.
- [ ] `published_url_allowed = false`.
- [ ] `platform_content_id_allowed = false`.
- [ ] `receipt_allowed = false`.
- [ ] `production_residual_closure_authorized = false`.

## 5. Extreme Static Scan

Search the entire repository for:

- [ ] `requests`
- [ ] `httpx`
- [ ] `aiohttp`
- [ ] `urllib`
- [ ] `urllib3`
- [ ] `socket`
- [ ] `dns`
- [ ] `oauth`
- [ ] `token`
- [ ] `Authorization`
- [ ] `Bearer`
- [ ] `api_key`
- [ ] `secret`
- [ ] `endpoint`
- [ ] `base_url`
- [ ] `upload_url`
- [ ] `publish_url`
- [ ] `webhook`
- [ ] `callback`
- [ ] `send`
- [ ] `post`
- [ ] `put`
- [ ] `patch`
- [ ] `call_api`
- [ ] `upload`
- [ ] `publish`
- [ ] `schedule`
- [ ] `receipt`
- [ ] `platform_content_id`

Criterion:

- [ ] Any occurrence outside documentation, audit artifacts or explicitly approved inert offline/security scanner modules must generate `HOLD`.

## 6. Artifact Audit

- [ ] All cited docs exist.
- [ ] All `final_verdict.json` files exist.
- [ ] All JSON files are valid.
- [ ] All expected gates have `GO_WITH_MONITORING` or `GO`.
- [ ] No gate has `blocking_failures`.
- [ ] No gate has `critical_failures`.
- [ ] All artifacts preserve open residuals.
- [ ] No artifact contradicts another artifact.
- [ ] No artifact uses improper success language.
- [ ] No artifact treats readiness as authorization.
- [ ] No artifact treats trace as execution.
- [ ] No artifact treats preparation as call.
- [ ] No artifact treats reference as payload.
- [ ] No artifact closes production residuals.

## 7. General Unit Tests

- [ ] Run all project tests.
- [ ] Run Publisher-specific tests.
- [ ] Run sandbox adapter tests.
- [ ] Run validation envelope tests.
- [ ] Run execution simulation tests.
- [ ] Run controlled binding tests.
- [ ] Run external call boundary tests.
- [ ] Run pre-execution guard tests.
- [ ] Run offline preparation tests.
- [ ] Run security scanner tests.
- [ ] Run determinism tests.
- [ ] Run stable serialization tests.
- [ ] Run incident hook no-secret tests.
- [ ] Run explicit blocking reason tests.

## 8. Security Tests

- [ ] Input with `api_key` must be rejected.
- [ ] Input with `access_token` must be rejected.
- [ ] Input with `Authorization` must be rejected.
- [ ] Input with `endpoint` must be rejected.
- [ ] Input with URL must be rejected.
- [ ] Input with media bytes must be rejected.
- [ ] Input with receipt must be rejected.
- [ ] Input with `platform_content_id` must be rejected.
- [ ] Input with upload path must be rejected.
- [ ] Input with request body must be rejected.
- [ ] Incident hook cannot copy sensitive value.
- [ ] Logs cannot contain secrets.
- [ ] Outputs cannot contain secrets.
- [ ] Artifacts cannot persist secrets.

## 9. Fail-Closed Tests

- [ ] Missing dependency blocks.
- [ ] Missing validation envelope blocks.
- [ ] Missing QC trace blocks.
- [ ] Missing Account Health trace blocks.
- [ ] Missing publish eligibility trace blocks.
- [ ] QC `HOLD` blocks.
- [ ] QC `REJECT` blocks.
- [ ] QC `publishable=false` blocks.
- [ ] Account Health `HOLD` blocks.
- [ ] Credential status `missing` blocks.
- [ ] Credential status `invalid_shape` blocks.
- [ ] Active kill switch blocks.
- [ ] Missing kill switch blocks.
- [ ] Missing rate limit blocks.
- [ ] Missing runtime evidence does not become success.
- [ ] Missing reference does not become success.

## 10. Critical Semantics Tests

- [ ] `blocked=false` does not authorize external call.
- [ ] `blocked=false` does not authorize publish.
- [ ] `guard_pass` does not mean success.
- [ ] `preparation_complete=true` does not authorize execution.
- [ ] `eligible_for_future_sandbox_validation_review=true` does not authorize execution.
- [ ] `credential_status=present` does not mean credential was read.
- [ ] `trace` does not mean success.
- [ ] `eligibility` does not mean publish authorization.
- [ ] `readiness` does not mean runtime integration.
- [ ] `runtime integration plan` does not mean runtime wiring.

## 11. Determinism Tests

- [ ] Same input generates same output.
- [ ] JSON serializes stably.
- [ ] No unexpected internal timestamps.
- [ ] No randomness.
- [ ] No environment dependency.
- [ ] No object memory address in output.
- [ ] Gate replays produce the same result.
- [ ] Metrics match scenarios and checklist.

## 12. Runtime Audit

- [ ] No runtime imported offline preparation without authorization.
- [ ] No scheduler calls preparation.
- [ ] No worker calls preparation.
- [ ] No executor calls preparation.
- [ ] Publisher execution path did not change.
- [ ] Orchestrator execution order did not change.
- [ ] No internal endpoint was created.
- [ ] No external endpoint was configured.
- [ ] No publish job was altered.
- [ ] No manifest gained external execution field.
- [ ] No publish record gained fake receipt.

## 13. Allowed File Audit

Confirm that only authorized files were created or modified in the slice:

- [ ] `backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation.py`
- [ ] `backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation_security.py`
- [ ] `tests/sandbox/unit/test_external_sandbox_validation_call_preparation_unittest.py`
- [ ] authorized audit-only runners
- [ ] authorized runtime docs
- [ ] authorized `OUT/audit/...` artifacts

Any other changed file requires review.

## 14. Mandatory Final Gates

- [ ] Run all existing gate runners.
- [ ] Run all unit tests.
- [ ] Run global static scan.
- [ ] Run diff audit.
- [ ] Run dependency audit.
- [ ] Run secret scan.
- [ ] Run artifact consistency audit.
- [ ] Run boundary preservation audit.
- [ ] Run full regression.
- [ ] Generate `FULL_SYSTEM_AUDIT_REPORT.md`.
- [ ] Generate `FULL_SYSTEM_FINAL_VERDICT.json`.

## 15. Expected Verdict

The expected verdict, if the checklist passes, is:

```json
{
  "expected_verdict": "GO_WITH_MONITORING",
  "production_ready": false,
  "external_execution_authorized": false,
  "runtime_integration_authorized": false,
  "current_system_state": "SAFE_PRE_CROSSING"
}
```

`HOLD` is required if any critical checklist item fails.

## 16. Failure Conditions

Immediate `HOLD` if:

- external call is authorized
- runtime integration is authorized by implication
- runtime wiring is authorized by implication
- Publisher becomes external client
- Orchestrator gets a hidden runtime step
- QC is bypassed
- Account Health `HOLD` is bypassed
- Strategy behavior changes without formal gate
- references become payloads
- trace becomes execution
- preparation becomes call
- production residual is closed without production evidence
- secret value appears in logs, outputs or artifacts
- URL, `platform_content_id` or receipt is fabricated
- any static scan occurrence outside approved context is unexplained
- any gate returns `HOLD`
- any gate has blocking failures
- any gate has critical failures

## 17. Required Future Output Artifacts

Future full-system audit must generate:

- `docs/runtime/full-system-audit/FULL_SYSTEM_AUDIT_REPORT.md`
- `OUT/audit/full_system_extreme_audit/final_verdict.json`
- `OUT/audit/full_system_extreme_audit/checklist_results.json`
- `OUT/audit/full_system_extreme_audit/static_scan_review.json`
- `OUT/audit/full_system_extreme_audit/artifact_consistency_review.json`
- `OUT/audit/full_system_extreme_audit/boundary_preservation_review.json`
- `OUT/audit/full_system_extreme_audit/security_review.json`
- `OUT/audit/full_system_extreme_audit/diff_review.json`
- `OUT/audit/full_system_extreme_audit/test_results.json`
- `OUT/audit/full_system_extreme_audit/residual_monitoring_review.json`

## 18. Next Authorized Step

The next authorized artifact is a formal audit plan or gate based on this checklist.

Suggested next artifact:

- `docs/runtime/full-system-audit/FULL_SYSTEM_EXTREME_AUDIT_GATE.md`

No runner is authorized by this checklist alone.

No runtime implementation is authorized by this checklist.

No external execution is authorized by this checklist.

## 19. Final Principle

Full-system audit is proof of containment.

It is not permission to cross the containment boundary.
