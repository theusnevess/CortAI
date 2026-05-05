# CortAI System State Definition

## 1. Purpose

This document formally defines CortAI system states.

Its purpose is to prevent ambiguity about what the system is allowed to do, what remains prohibited, and what kind of evidence is required before any future state transition may be considered.

The current state is `SAFE_PRE_CROSSING`.

This document does not authorize a state transition.

This document does not authorize runtime integration, runtime wiring, external calls, upload, scheduling, publishing, production readiness, or production residual closure.

Current mandatory state:

```json
{
  "current_state": "SAFE_PRE_CROSSING",
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "implementation_authorized": false,
  "production_ready": false
}
```

Related documents:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_Execution_Model]]
- [[CortAI_Governance_Model]]
- [[KERNEL_BIBLE]]

## 2. Current State: SAFE_PRE_CROSSING

`SAFE_PRE_CROSSING` means CortAI has completed a governed offline/pre-execution safety chain without crossing into runtime integration, runtime wiring, external execution, or production behavior.

This state indicates structural readiness evidence, not execution permission.

The system has documented and gated boundaries such as:

- Publisher governance;
- trace-only publish lifecycle semantics;
- dry-run evidence concepts;
- sandbox adapter safety;
- validation envelope safety;
- execution simulation safety;
- controlled binding safety;
- external-call boundary safety;
- pre-execution guard safety;
- offline preparation acceptance;
- runtime integration readiness review;
- runtime integration gate review.

However, all of these remain non-authorizing for runtime integration and external execution.

The current state is safe because boundaries are preserved and the system has not crossed into external side effects.

## 3. What SAFE_PRE_CROSSING Allows

`SAFE_PRE_CROSSING` allows only bounded, non-executing work.

Allowed categories include:

- documentation;
- architectural review;
- governance review;
- audit-only gates;
- planning artifacts;
- state definition artifacts;
- boundary clarification;
- non-authorizing reviews;
- local documentation for Obsidian;
- analysis of existing artifacts;
- future authorization-chain planning only.

`SAFE_PRE_CROSSING` may allow discussion of future states as conceptual states.

It does not allow activating those states.

It may allow offline evidence review.

It does not allow runtime wiring.

It may allow static analysis.

It does not allow external execution.

## 4. What SAFE_PRE_CROSSING Prohibits

`SAFE_PRE_CROSSING` prohibits:

- runtime integration;
- runtime wiring;
- external calls;
- HTTP client use for Publisher external execution;
- SDK client use;
- endpoint configuration;
- DNS/network execution;
- platform API calls;
- credential value access;
- request transformation;
- transport payload creation;
- media upload;
- scheduler invocation for publication;
- real publishing;
- real published URL emission;
- platform content ID emission;
- production receipt emission;
- production residual closure;
- declaring the system production-ready.

It also prohibits semantic shortcuts such as:

- readiness treated as authorization;
- trace treated as success;
- plan treated as permission;
- test passage treated as authorization;
- gate passage treated as unlimited permission;
- offline preparation treated as external call readiness;
- sandbox evidence treated as production evidence.

## 5. Future Possible States

Future states listed here are conceptual only.

They are not active.

They are not authorized by this document.

They require separate governed authorization chains before activation.

### 5.1 RUNTIME_INTEGRATION_PLANNING

`RUNTIME_INTEGRATION_PLANNING` would mean the system is authorized to create planning artifacts for a future runtime integration path.

It would not authorize runtime wiring.

It would not authorize implementation unless explicitly scoped.

It would not authorize external calls.

It would not authorize upload, scheduling, publishing, or production readiness.

### 5.2 RUNTIME_INTEGRATION_AUTHORIZED

`RUNTIME_INTEGRATION_AUTHORIZED` would mean a separate formal governance chain has explicitly authorized a bounded runtime integration scope.

This state would require:

- explicit authorization artifact;
- exact files or integration surfaces;
- policy review;
- boundary review;
- rollback model;
- audit model;
- residual review;
- gate before and after implementation.

This state would still not automatically authorize external calls.

Runtime integration is not external execution.

### 5.3 EXTERNAL_SANDBOX_AUTHORIZED

`EXTERNAL_SANDBOX_AUTHORIZED` would mean a separate formal governance chain has explicitly authorized a bounded sandbox external interaction scope.

This state would require strict distinction between sandbox evidence and production evidence.

It would require explicit credential safety rules, endpoint rules, request rules, response evidence rules, incident hooks, audit trail, kill switch behavior, and fail-closed behavior.

This state would not authorize production publishing.

Sandbox authorization is not production authorization.

### 5.4 PRODUCTION_READY

`PRODUCTION_READY` would mean production readiness has been proven through a separate production governance chain.

This state would require real operational evidence, explicit production residual review, platform evidence, incident readiness, monitoring maturity, rollback readiness, credential governance, policy enforcement, and final production gate acceptance.

This state is not active.

CortAI must not be described as production-ready in the current state.

## 6. State Transition Rules

State transitions require explicit governance.

A valid transition must include:

- current state;
- requested next state;
- exact transition scope;
- authority requesting transition;
- authority approving transition;
- evidence used;
- gates required;
- failure conditions;
- residual impact;
- non-authorization matrix update;
- rollback or revocation model;
- final verdict artifact.

No state transition may occur implicitly.

No state transition may be inferred from maturity language.

No state transition may be inferred from completed documentation.

No state transition may be inferred from tests or gates unless the transition is explicitly authorized by a formal state transition artifact.

## 7. What Cannot Cause State Transition

The following must not cause state transition by themselves:

### 7.1 Plan Created

A plan defines possible future work.

A plan does not change system state.

### 7.2 Gate Created

A gate specification defines validation criteria.

A gate specification does not change system state.

### 7.3 Gate Approved

A gate approval applies only to the gate scope.

A gate approval does not change system state unless the gate explicitly authorizes a state transition and the transition artifact records it.

### 7.4 Test Passing

Tests provide evidence.

Tests do not change system state.

### 7.5 Trace Available

Trace provides observability.

Trace does not change system state.

### 7.6 Positive Readiness

Readiness indicates possible preparation for a later step.

Readiness does not change system state.

### 7.7 Valid Contract

A valid contract proves structural validity.

A valid contract does not change system state.

### 7.8 Local Implementation

Local implementation does not change system state.

Implementation without explicit runtime authorization remains non-runtime behavior.

Implementation without external-call authorization remains non-external behavior.

References to local, offline, or preparation-only implementation do not change the current non-authorization matrix. In `SAFE_PRE_CROSSING`, those references mean documentation, audit evidence, or non-executing preparation only; they do not authorize correction, implementation, tests, runners, runtime integration, runtime wiring, external calls, credential access, request transformation, transport payloads, upload, scheduling, publishing, production readiness, or residual closure.

Lane 2 reconciliation: documenting `backend/app/runtime` as not neutral Kernel and as a domain operational runtime with legacy runtime and mixed boundary surfaces does not change system state. F-002 is reduced with monitoring, but remains open until boundary naming and ownership documentation are reviewed. This documentation classification does not authorize refactor, rename, code changes, import changes, runtime integration, runtime wiring, external calls, credential access, tests, static scans, runners, tooling, upload, scheduling, publishing, production readiness, or residual closure.

## 8. HOLD Conditions

The system must enter `HOLD` or remain in a blocked state if any of the following occurs:

- runtime integration is treated as active while unauthorized;
- runtime wiring appears while unauthorized;
- external call behavior appears while unauthorized;
- HTTP, SDK, endpoint, DNS, or API surface appears for Publisher external execution while unauthorized;
- credential values are accessed, logged, serialized, or persisted;
- request transformation appears without authorization;
- transport payload appears without authorization;
- upload, scheduler, or publish behavior appears without authorization;
- real URL, platform content ID, or production receipt appears;
- production readiness is declared without production gate;
- production residuals are closed without real production evidence;
- Account Health `HOLD` is bypassed;
- QC becomes Publisher;
- Strategy becomes execution authority;
- Orchestrator creates hidden runtime authority;
- Kernel imports Domain;
- Domain executes Kernel logic internally;
- readiness is treated as authorization;
- test passage is treated as authorization;
- gate passage is treated as unlimited permission;
- sandbox evidence is treated as production evidence.

## 9. Non-Authorization Matrix

The current non-authorization matrix is:

```json
{
  "current_state": "SAFE_PRE_CROSSING",
  "implementation_authorized": false,
  "implementation_tests_authorized": false,
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "http_client_authorized": false,
  "sdk_client_authorized": false,
  "endpoint_authorized": false,
  "dns_network_authorized": false,
  "api_call_authorized": false,
  "credential_value_access_authorized": false,
  "request_transformation_authorized": false,
  "transport_payload_authorized": false,
  "upload_authorized": false,
  "scheduler_authorized": false,
  "real_publish_authorized": false,
  "published_url_authorized": false,
  "platform_content_id_authorized": false,
  "production_receipt_authorized": false,
  "production_ready": false,
  "production_residual_closure_authorized": false
}
```

This matrix remains active until explicitly superseded by a future formal state transition artifact.

## 10. Open Residuals

Production residuals remain open.

Open residual categories include:

- production publish evidence unavailable;
- platform integration not enabled;
- publish result history absent or insufficient;
- external sandbox execution not authorized;
- runtime integration not authorized;
- post-publish metrics unavailable;
- production attribution causality unproven;
- production incident history unavailable;
- sandbox evidence not equivalent to production evidence.

Residual closure requires real evidence and formal governance.

Dry-run evidence cannot close production residuals.

Sandbox evidence cannot close production residuals.

Readiness evidence cannot close production residuals.

## 11. Expected Final State For Now

The expected final state for the current phase is:

```json
{
  "current_state": "SAFE_PRE_CROSSING",
  "current_chain_closed": true,
  "next_work": "SEPARATE_RUNTIME_INTEGRATION_AUTHORIZATION_CHAIN_PLANNING_ONLY",
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "implementation_authorized": false,
  "production_ready": false,
  "production_residuals_remain_open": true
}
```

The system should remain here until a separate authorization chain is created, gated, reviewed, and explicitly accepted.

No transition is authorized by this document.

## 12. Internal Obsidian Links

Primary references:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_Execution_Model]]
- [[CortAI_Governance_Model]]
- [[KERNEL_BIBLE]]

Recommended reading order:

1. [[KERNEL_BIBLE]]
2. [[CortAI_Architecture_Bible]]
3. [[CortAI_Boundary_Specification]]
4. [[CortAI_Governance_Model]]
5. [[CortAI_Execution_Model]]
6. [[CortAI_System_State_Definition]]

## 13. Final Principle

A system state is an authorization boundary, not a progress label.

CortAI remains in `SAFE_PRE_CROSSING`.

The system is structurally complete for the current offline/pre-crossing chain, but it is not authorized for runtime integration, runtime wiring, external calls, upload, scheduling, publishing, production operation, or production residual closure.

Future states may be defined conceptually, but they do not become active without explicit governed transition.
