# PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_PLAN

## 1. Purpose

`PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_PLAN` defines the Publisher governance model for Phase 3.

This is a planning artifact only.

It does not implement publishing, modify Publisher runtime behavior, modify QC, modify Strategy, modify the Orchestrator, or modify the core pipeline.

The goal is to make publish authority explicit and auditable before any publish behavior is changed.

Final principle:

> Publisher is explicit publish authority; QC only evaluates the final artifact.

## 2. Starting State

Phase 2.6 ended with:

```json
{
  "release_state": "READY_FOR_V3_WITH_MONITORING",
  "publisher": "OUT_OF_SCOPE_IN_PHASE_2_6",
  "qc": "FINAL_ARTIFACT_EVALUATOR_PRESERVED",
  "core_pipeline": "FROZEN_AND_VALIDATED",
  "change_policy": "FROZEN_UNLESS_GOVERNANCE_REOPEN"
}
```

Canonical references:

- `docs/runtime/phase-3/PHASE_3_OPERATIONAL_GOVERNANCE_AND_MATURITY_PLAN.md`
- `docs/runtime/phase-3/monitoring/PRODUCTION_MONITORING_AND_RUNTIME_EVIDENCE_PLAN.md`
- `OUT/audit/phase_2_6_final_master_gate/final_verdict.json`
- `docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md`
- `docs/runtime/architecture/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md`

Publisher governance must start as trace and authority design, not publishing implementation.

## 3. Scope

Allowed in this plan:

- publish authority model
- publish eligibility trace
- publish attempt trace
- publish result trace
- skip reason semantics
- failure reason semantics
- QC dependency visibility
- Account Health HOLD visibility
- Strategy plan visibility
- publisher boundary statement
- publish lifecycle artifact schema

Forbidden in this plan:

- implementing publishing
- changing QC `publishable`
- changing QC `APPROVE/HOLD/REJECT`
- overriding Account Health HOLD
- changing Strategy
- changing Orchestrator
- changing core pipeline
- hiding failed publish attempts
- treating publish skip as success
- introducing performance prediction

## 4. Publisher Authority Model

Publisher must be the explicit publish authority.

Authority boundaries:

```json
{
  "publisher": {
    "authority": "decides whether a publish attempt is made",
    "must_consume": [
      "qc_decision",
      "qc_publishable",
      "account_health_decision",
      "strategy_profile",
      "artifact_manifest",
      "runtime_policy"
    ],
    "must_emit": [
      "publish_eligibility_trace",
      "publish_attempt_trace",
      "publish_result_trace"
    ]
  },
  "video_qc": {
    "authority": "evaluates final artifact",
    "must_not": [
      "publish",
      "schedule_publish",
      "override_publisher",
      "override_account_health"
    ]
  },
  "account_health": {
    "authority": "SAFE | CAUTION | HOLD posture",
    "hold_must_not_be_overridden_by_publisher": true
  },
  "strategy": {
    "authority": "control layer creative strategy",
    "must_not_publish": true
  }
}
```

Publisher may attempt publish only when eligibility conditions are satisfied and recorded.

Publisher must not infer eligibility from missing evidence.

## 5. Publish Eligibility Trace

Publish eligibility trace should answer:

- was publishing evaluated
- which artifact was evaluated
- what QC decision was available
- whether QC marked artifact publishable
- what Account Health posture was available
- whether Account Health HOLD blocked publishing
- whether required artifact references exist
- whether Strategy context exists
- whether runtime policy permits publish
- why eligibility passed or failed

Recommended shape:

```json
{
  "publish_eligibility_trace": {
    "trace_version": "publisher_governance_v1",
    "run_id": "string",
    "content_id": "string",
    "eligibility_checked": true,
    "eligible": false,
    "qc_dependency": {
      "qc_status": "APPROVE | HOLD | REJECT | UNKNOWN",
      "qc_publishable": false,
      "qc_trace_ref": "string | null",
      "qc_dependency_satisfied": false
    },
    "account_health_dependency": {
      "decision": "SAFE | CAUTION | HOLD | UNKNOWN",
      "hold_detected": false,
      "health_trace_ref": "string | null",
      "hold_blocks_publish": true
    },
    "strategy_dependency": {
      "strategy_ref": "string | null",
      "strategy_available": false
    },
    "artifact_dependency": {
      "artifact_manifest_ref": "string | null",
      "video_available": false,
      "metadata_available": false
    },
    "policy_dependency": {
      "runtime_policy_ref": "string | null",
      "policy_allows_publish": false
    },
    "blocking_reasons": [],
    "warnings": [],
    "rationale": []
  }
}
```

Eligibility rules:

- QC `REJECT` blocks publish.
- QC `HOLD` blocks publish unless a future explicit governance policy says otherwise.
- QC `publishable = false` blocks publish.
- Account Health `HOLD` blocks publish.
- missing artifact manifest blocks publish.
- missing QC trace blocks publish eligibility or marks eligibility unknown.
- missing evidence must not be treated as eligible.

## 6. Publish Attempt Trace

Publish attempt trace should answer:

- was a publish attempt made
- why it was attempted
- which target was used
- which artifact was submitted
- what preconditions were satisfied
- whether fallback was used
- whether attempt failed, succeeded, or remained unknown

Recommended shape:

```json
{
  "publish_attempt_trace": {
    "attempt_id": "string",
    "run_id": "string",
    "content_id": "string",
    "timestamp": "ISO-8601",
    "attempted": false,
    "publish_target": "string | null",
    "artifact_manifest_ref": "string | null",
    "eligibility_trace_ref": "string | null",
    "preconditions_satisfied": false,
    "fallback_used": false,
    "attempt_status": "not_attempted | attempted | failed | succeeded | unknown",
    "skip_reason": "string | null",
    "failure_reason": "string | null",
    "rationale": []
  }
}
```

Attempt rules:

- no attempt may occur without eligibility trace
- no attempt may occur under Account Health HOLD
- no attempt may occur with QC non-publishable artifact
- attempt failure must be explicit
- skipped publish must be explicit
- attempt unknown must remain unknown, not success

## 7. Publish Result Trace

Publish result trace should answer:

- did publishing succeed
- what external/internal reference confirms success
- if failure occurred, what failed
- if skipped, why
- when result was observed
- whether result is final or pending

Recommended shape:

```json
{
  "publish_result_trace": {
    "attempt_id": "string",
    "content_id": "string",
    "observed_at": "ISO-8601",
    "result_status": "not_attempted | succeeded | failed | skipped | pending | unknown",
    "published_url": "string | null",
    "platform_content_id": "string | null",
    "failure_reason": "string | null",
    "skip_reason": "string | null",
    "result_evidence_ref": "string | null",
    "result_evidence_available": false,
    "rationale": []
  }
}
```

Result rules:

- publish success requires explicit result evidence
- URL or platform ID must not be fabricated
- pending is not success
- unknown is not success
- failed attempt must remain visible
- skipped attempt must remain visible

## 8. Skip Reason Semantics

Allowed skip reasons:

```json
[
  "ACCOUNT_HEALTH_HOLD",
  "QC_REJECTED",
  "QC_HOLD",
  "QC_NOT_PUBLISHABLE",
  "MISSING_QC_TRACE",
  "MISSING_ARTIFACT_MANIFEST",
  "MISSING_VIDEO_ARTIFACT",
  "MISSING_STRATEGY_CONTEXT",
  "RUNTIME_POLICY_BLOCKED",
  "PUBLISH_TARGET_NOT_CONFIGURED",
  "MANUAL_APPROVAL_REQUIRED",
  "DRY_RUN_MODE",
  "UNKNOWN_PRECONDITION"
]
```

Skip rules:

- skip must include rationale
- skip must not count as publish success
- repeated skip must be monitorable
- Account Health HOLD skip is expected and must not be downgraded
- unknown precondition should trigger monitoring or incident review

## 9. Failure Reason Semantics

Allowed failure reasons:

```json
[
  "PUBLISH_TARGET_ERROR",
  "AUTHENTICATION_FAILURE",
  "UPLOAD_FAILURE",
  "PLATFORM_REJECTION",
  "ARTIFACT_READ_FAILURE",
  "METADATA_VALIDATION_FAILURE",
  "NETWORK_FAILURE",
  "RATE_LIMITED",
  "UNKNOWN_EXTERNAL_FAILURE",
  "UNKNOWN_INTERNAL_FAILURE"
]
```

Failure rules:

- failure must include timestamp
- failure must include target if known
- failure must not be hidden as skipped
- failure must not be hidden as pending indefinitely
- repeated failures must create incidents
- unknown failure must remain unknown until evidence clarifies it

## 10. QC Dependency Visibility

Publisher must record:

- QC status
- QC publishable value
- QC trace reference
- QC confidence level when available
- QC blockers/warnings when available
- whether QC dependency passed

Publisher must not:

- reinterpret QC status
- change QC publishability
- publish if QC marks non-publishable
- treat missing QC as approval

QC dependency is necessary but not sufficient. Publisher still owns publish attempt authority.

## 11. Account Health HOLD Visibility

Publisher must record:

- Account Health decision
- Account Health trace reference when available
- whether HOLD was detected
- whether HOLD blocked publish

Rules:

- `HOLD` always blocks publish.
- `CAUTION` may allow publish only if governance policy permits and constraints are visible.
- `SAFE` is not publish success; it is only posture clearance.
- missing Account Health evidence must be explicit.

Publisher must not:

- downgrade HOLD
- ignore HOLD
- convert missing health evidence into SAFE
- hide health-derived skip reasons

## 12. Publisher Boundary Statement

Every publish trace must include:

```json
{
  "boundary_statement": "Publisher is explicit publish authority; QC evaluates artifact quality; Strategy controls creative direction; Account Health can block via HOLD."
}
```

Boundary rules:

- Publisher publishes or skips.
- QC evaluates.
- Strategy controls creative direction.
- Account Health governs account posture.
- Orchestrator coordinates.
- Publisher must not become Strategy, QC, Learning, Trend, Asset, Voice, Script, Experiment or Attribution.

## 13. Publish Lifecycle Artifact

Publish lifecycle evidence should be appended to:

- `OUT/runtime_evidence/publish_lifecycle.jsonl`

Recommended consolidated event:

```json
{
  "publish_event_id": "string",
  "run_id": "string",
  "content_id": "string",
  "timestamp": "ISO-8601",
  "event_type": "PUBLISH_ELIGIBILITY_CHECKED | PUBLISH_ATTEMPTED | PUBLISH_SUCCEEDED | PUBLISH_FAILED | PUBLISH_SKIPPED",
  "eligibility": {},
  "attempt": {},
  "result": {},
  "qc_dependency": {},
  "account_health_dependency": {},
  "strategy_dependency": {},
  "artifact_refs": [],
  "fallback_used": false,
  "skip_reason": "string | null",
  "failure_reason": "string | null",
  "boundary_statement": "Publisher is explicit publish authority; QC evaluates artifact quality; Strategy controls creative direction; Account Health can block via HOLD."
}
```

Artifact rules:

- append-only preferred
- one event per lifecycle transition
- no event should overwrite prior failure
- result evidence must be referenced, not fabricated
- missing evidence must be explicit

## 14. Incident And Monitoring Hooks

Publisher governance should create incidents for:

- publish attempted under Account Health HOLD
- publish attempted with QC non-publishable artifact
- publish success without result evidence
- repeated publish target failure
- missing QC trace
- missing artifact manifest
- failure hidden as skipped
- pending result exceeding configured observation window

Incident target:

- `OUT/runtime_evidence/incidents.jsonl`

This plan defines incident triggers only. It does not implement incident writing.

## 15. Validation Requirements

Any future Publisher implementation must validate:

- eligibility trace exists
- Account Health HOLD blocks publish
- QC non-publishable blocks publish
- skipped publish is explicit
- failed publish is explicit
- successful publish requires evidence
- missing evidence is not success
- Publisher boundary statement exists
- Publisher does not modify QC, Strategy, Account Health or core

Minimum future gate:

- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE.md`
- `tests/gates/publisher/run_publisher_governance_and_publish_trace_gate.py`
- `OUT/audit/publisher_governance_and_publish_trace_gate/final_verdict.json`

## 16. Failure Conditions

This plan fails if future work:

- implements publishing before governance trace is accepted
- changes QC thresholds
- changes QC publishability
- overrides Account Health HOLD
- changes Strategy
- changes Orchestrator
- changes core pipeline
- hides failed publish attempts
- hides skipped publish attempts
- treats missing publish evidence as success
- fabricates published URL or platform content ID
- creates performance prediction authority

## 17. Exit Criteria

This plan is complete when it defines:

- publish authority model
- eligibility trace
- attempt trace
- result trace
- skip reason semantics
- failure reason semantics
- QC dependency visibility
- Account Health HOLD visibility
- Publisher boundary statement
- publish lifecycle artifact shape
- validation requirements
- failure conditions

This plan does not require runtime implementation.

## 18. Next Authorized Artifact

After this plan, the next authorized artifact is:

- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE_PLAN.md`

The gate plan should validate the governance and trace design before any implementation touches Publisher behavior.
