# CortAI Boundary Specification

## 1. Purpose

This document centralizes the critical boundaries of CortAI.

Its purpose is to prevent incorrect interpretation of readiness, trace, plans, contracts, preparation, tests, gates, or completion as authorization.

CortAI is currently in a governed pre-crossing state. The system may document, validate, audit, and preserve boundary evidence, but it must not infer execution authority from those artifacts.

Current mandatory state:

```json
{
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "implementation_authorized": false,
  "production_ready": false,
  "system_state": "SAFE_PRE_CROSSING"
}
```

This specification is normative. Any component, document, test, gate, agent, runtime path, or operator action that contradicts these boundaries must be treated as unsafe.

Related documents:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Execution_Model]]
- [[CortAI_Governance_Model]]
- [[CortAI_System_State_Definition]]
- [[KERNEL_BIBLE]]

## 2. Absolute Boundaries

### 2.1 Readiness Is Not Authorization

Readiness indicates that a prerequisite, design, gate, or evidence set appears sufficient to consider a later step.

Readiness does not authorize execution.

Readiness does not authorize runtime integration.

Readiness does not authorize external calls.

Readiness does not authorize implementation unless a separate authorization artifact explicitly grants implementation scope.

### 2.2 Trace Is Not Success

Trace proves that an event, decision, or artifact is observable.

Trace does not prove correctness.

Trace does not prove domain success.

Trace does not prove production readiness.

Trace does not authorize downstream action.

A traced failure remains a failure.

### 2.3 Reference Is Not Payload

A reference identifies where evidence, data, or artifacts may be found.

A reference is not the payload itself.

A reference must not be transformed into executable content unless a future governed authorization explicitly permits that transformation.

Reference handoff must remain audit-only in the current state.

### 2.4 Preparation Is Not External Call

Preparation may build local validation state, local summaries, local traces, or offline structures.

Preparation is not network execution.

Preparation is not request execution.

Preparation is not platform interaction.

Preparation is not publication.

Preparation is not implementation authorization.

Preparation is not runtime integration, runtime wiring, external call readiness, request transformation, transport payload creation, upload, scheduling, publishing, production readiness, or residual closure.

### 2.5 Plan Is Not Permission

A plan defines a possible direction, sequence, boundary, or future decision path.

A plan does not authorize implementation.

A plan does not authorize runtime wiring.

A plan does not authorize external calls.

A plan does not close residuals.

### 2.6 Contract Is Not Execution Permission

A valid contract describes structure and semantics.

A valid contract does not execute itself.

A valid contract does not override policy.

A valid contract does not bypass Account Health, QC, Strategy, Publisher governance, or Kernel enforcement.

### 2.7 Test Pass Is Not Authorization

A passing test proves only that the tested behavior satisfied the test scope.

A passing test does not authorize runtime integration.

A passing test does not authorize external calls.

A passing test does not authorize publication.

A passing test does not make the system production-ready.

### 2.8 Gate Pass Is Not Unlimited Permission

A gate verdict applies only to the declared gate scope.

A gate pass does not grant adjacent authority.

A gate pass does not imply implementation authority unless the gate explicitly grants that exact scope.

A gate pass does not imply external execution authority.

A gate pass does not imply production readiness.

### 2.9 Completion Is Not Production Readiness

Completion of a chain, phase, document, test, or gate does not equal production readiness.

Production readiness requires separate governed evidence, production residual review, operational validation, and explicit authorization.

In the current state, production readiness remains false.

## 3. Kernel vs Domain Boundary

The Kernel is neutral, domain-agnostic, payload-opaque, and execution-only.

The Domain owns CortAI semantics, including creative intent, governance interpretation, agent rationale, quality evaluation, and publication governance meaning.

The Kernel must not import Domain.

The Domain must not execute Kernel logic internally.

Domain intent must cross into Kernel execution only through governed contracts and authorized runtime boundaries.

No Domain component may self-grant Kernel execution authority.

Reference: [[KERNEL_BIBLE]]

Lane 2 reconciliation: `backend/app/runtime` is not classified as the neutral Kernel. It is documented for this audit chain as a domain operational runtime with legacy runtime and mixed boundary surfaces. The original Kernel contamination risk is reduced because the path is not treated as Kernel, but boundary naming and ownership risk remains open. This does not authorize refactor, rename, code changes, import changes, runtime integration, runtime wiring, external calls, credential access, tests, static scans, runners, tooling, upload, scheduling, publishing, production readiness, or residual closure.

## 4. Runtime Facade Boundary

The Runtime Facade translates between Domain-facing structures and Kernel-facing contracts.

The Runtime Facade is a boundary, not logic authority.

It must not decide policy.

It must not create hidden orchestration.

It must not execute agents.

It must not perform runtime wiring unless explicitly authorized.

It must not convert readiness into execution.

It must not convert references into payloads.

In the current state, runtime integration and runtime wiring remain unauthorized.

## 5. Agent Execution Boundary

Agents may produce domain outputs, traces, confidence, rationale, and governed recommendations within their scope.

Agents must not execute outside Kernel control when runtime execution is in scope.

Agents must not self-schedule.

Agents must not call other agents through hidden paths.

Agents must not create external effects.

Agents must not interpret their own completion as downstream authority.

Agent output is evidence or intent, not execution permission.

## 6. Policy Engine Boundary

The Policy Engine controls allow, delay, and block semantics for execution.

Policy decisions must be explicit, scoped, versioned, and auditable.

Missing policy means block.

Expired policy means block.

Inconsistent policy means block.

No agent, facade, orchestrator, publisher, or test may bypass policy enforcement.

Policy cannot be inferred from readiness, trace, contract validity, test passage, or prior success.

## 7. Account Health Boundary

Account Health protects account safety and operational risk posture.

Account Health `HOLD` is blocking.

No downstream component may bypass Account Health `HOLD`.

Publisher must not override Account Health `HOLD`.

QC must not override Account Health `HOLD`.

Strategy must not override Account Health `HOLD`.

The Orchestrator must not hide Account Health constraints.

## 8. QC Boundary

QC evaluates final artifacts.

QC may classify artifact state, quality evidence, severity, confidence in QC decision, and publishability semantics within its authorized scope.

QC does not publish.

QC does not become Publisher.

QC does not repair, rerender, rewrite, or upload unless separately authorized by governed scope.

QC does not predict performance.

QC output must not be treated as external execution permission.

## 9. Strategy Boundary

Strategy is the control layer for domain direction.

Strategy may define governed intent, priorities, and creative direction.

Strategy does not execute runtime work.

Strategy does not publish.

Strategy does not override Policy Engine enforcement.

Strategy does not override Account Health.

Strategy does not convert Learning, Trend, Novelty, Experiment, or Attribution signals into hidden execution authority.

Strategy output is control intent, not execution authorization.

## 10. Publisher Boundary

Publisher is governed publication authority.

Publisher is not currently an external execution client.

Publisher may hold governance traces, publish eligibility semantics, dry-run evidence, sandbox safety structures, validation envelopes, boundary markers, pre-execution guards, and offline preparation artifacts.

Publisher must not perform external calls in the current state.

Publisher must not create HTTP clients, SDK clients, endpoints, DNS/network access, or API calls.

Publisher must not access credential values.

Publisher must not transform validation envelopes into transport payloads.

Publisher must not upload, schedule, or publish.

Publisher must not emit real URLs, platform content IDs, or production receipts.

Publisher must not close production residuals.

## 11. Attribution Boundary

Attribution may analyze outcome evidence only within its evidence scope.

Attribution must not create causal claims without sufficient governed evidence.

Attribution must not turn weak correlation into strategy authority.

Attribution must not authorize publishing.

Attribution must not close production residuals without real production evidence.

Sandbox evidence is not production evidence.

## 12. Experiment Boundary

Experiment controls treatment/control semantics, assignment eligibility, exposure trace, and result-readiness rules.

Experiment does not override Strategy.

Experiment does not override Account Health.

Experiment does not override QC.

Experiment does not decide publishability.

Experiment does not authorize external execution.

Experiment result-readiness is not production causality.

## 13. External Call Boundary

External calls are not authorized in the current state.

The following remain forbidden:

- HTTP client creation or use
- SDK client creation or use
- endpoint configuration
- DNS/network execution
- API calls
- credential value access
- request transformation
- transport payload creation
- media upload
- scheduler invocation
- real publication
- real URL emission
- platform content ID emission
- production receipt emission

Any attempt to cross this boundary must result in block or hold.

## 14. Mandatory Failure Conditions

The system must enter `HOLD`, block, reject, or fail closed when any of the following occurs:

- runtime integration is treated as authorized without explicit authorization;
- runtime wiring appears without explicit authorization;
- external call capability appears;
- HTTP, SDK, endpoint, DNS, or API execution appears;
- credential values are accessed or serialized;
- request transformation is introduced;
- transport payload is created;
- upload, scheduler, or publish behavior appears;
- real URL, platform content ID, or receipt appears;
- Account Health `HOLD` is bypassed;
- QC becomes Publisher;
- Strategy becomes execution authority;
- Orchestrator creates hidden authority;
- Policy Engine is bypassed;
- test passage is treated as authorization;
- gate passage is treated as unlimited permission;
- trace is treated as success;
- readiness is treated as authorization;
- reference is treated as payload;
- preparation is treated as external call;
- production residuals are closed without real evidence.

## 15. Fail-Closed Rule

The system must fail closed under ambiguity.

Missing evidence means block.

Unknown authorization state means block.

Inconsistent state means block.

Untraceable execution means block.

Unclear boundary means block.

Unverified external effect means block.

The system must never continue because stopping is inconvenient.

## 16. Current State Preserved

This specification preserves the current state:

```json
{
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "implementation_authorized": false,
  "production_ready": false,
  "system_state": "SAFE_PRE_CROSSING"
}
```

No statement in this document authorizes execution, runtime integration, runtime wiring, implementation, external calls, platform integration, upload, scheduling, publishing, production readiness, or production residual closure.

The only valid next work remains separate governed planning, review, or authorization-chain documentation unless a future artifact explicitly changes scope through formal governance.

## 17. Internal Obsidian Links

Primary references:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Execution_Model]]
- [[CortAI_Governance_Model]]
- [[CortAI_System_State_Definition]]
- [[KERNEL_BIBLE]]

Recommended reading order:

1. [[KERNEL_BIBLE]]
2. [[CortAI_Architecture_Bible]]
3. [[CortAI_System_State_Definition]]
4. [[CortAI_Boundary_Specification]]
5. [[CortAI_Governance_Model]]
6. [[CortAI_Execution_Model]]
