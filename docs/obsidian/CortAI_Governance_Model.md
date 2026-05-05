# CortAI Governance Model

## 1. Purpose

This document defines the governance model of CortAI.

Its purpose is to specify who may decide what, which authorities are blocking, how authorization is granted, when `HOLD` is mandatory, and which actions remain prohibited in the current system state.

CortAI governance exists to prevent uncontrolled execution, hidden authority, semantic drift, fake confidence, fake readiness, and accidental promotion from planning to execution.

Current system state:

```json
{
  "system_state": "SAFE_PRE_CROSSING",
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "implementation_authorized": false,
  "production_ready": false
}
```

No statement in this document authorizes code, runtime integration, runtime wiring, external calls, publishing, production readiness, or production residual closure.

Related documents:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_Execution_Model]]
- [[CortAI_System_State_Definition]]
- [[KERNEL_BIBLE]]
- [[FOUNDATION_KERNEL_GOVERNANCE]]

## 2. Explicit Authorization Principle

Authorization must be explicit, scoped, versioned, auditable, and revocable.

No authority is implied by:

- a plan;
- a gate;
- a review;
- a passing test;
- a valid contract;
- a trace;
- a readiness state;
- absence of blockers;
- implementation existence;
- prior success;
- operator expectation;
- confidence score;
- dry-run evidence;
- sandbox evidence.

Authorization applies only to the exact action, boundary, actor, and scope named by the governing artifact.

If authorization scope is missing, ambiguous, expired, or inconsistent, the system must fail closed.

## 3. Plan, Gate, Review, Authorization, And Implementation

### 3.1 Plan

A plan defines a proposed future structure, boundary, sequence, or evaluation path.

A plan does not authorize implementation.

A plan does not authorize runtime integration.

A plan does not authorize external calls.

A plan does not authorize publishing.

### 3.2 Gate

A gate validates whether a plan, implementation slice, boundary, or evidence set satisfies predefined criteria.

A gate verdict applies only to its declared scope.

A gate does not authorize adjacent scopes unless explicitly stated.

A gate does not grant unlimited permission.

### 3.3 Review

A review records acceptance, rejection, monitoring status, residuals, and next allowed step after a gate or plan.

A review is not execution.

A review is not implementation unless it explicitly authorizes a bounded implementation scope through governance.

### 3.4 Authorization

Authorization is the formal act of granting a bounded permission.

Authorization must define:

- allowed action;
- allowed scope;
- allowed actor;
- allowed boundary;
- forbidden actions;
- residual impact;
- required gates;
- revocation conditions.

### 3.5 Implementation

Implementation is code or system behavior change within an authorized scope.

Implementation must not begin unless explicitly authorized.

Offline/preparation-only wording is not implementation authorization. In the current state, it means documentation, audit evidence, or non-executing preparation only. Any future positive implementation scope requires a separate, explicit, scoped, versioned, auditable, and reviewed artifact.

Implementation does not automatically authorize runtime wiring.

Implementation does not automatically authorize external calls.

Implementation does not make the system production-ready.

## 4. Readiness Is Not Authorization

Readiness means prerequisites may be sufficient to consider a future step.

Readiness is not execution permission.

Readiness is not implementation permission.

Readiness is not runtime integration permission.

Readiness is not external-call permission.

Readiness is not publication permission.

In CortAI's current state, readiness gates have passed with monitoring, but runtime integration and external execution remain unauthorized.

## 5. Passing Tests Is Not Authorization

Tests validate observed behavior under test scope.

Passing tests do not grant authority.

Passing tests do not activate runtime integration.

Passing tests do not activate external calls.

Passing tests do not authorize upload, scheduling, publishing, credential access, endpoint creation, or platform API usage.

Tests are evidence, not permission.

## 6. Absence Of Blockers Is Not Permission

No blocking failure means only that no blocker was detected within the evaluated scope.

It does not mean new authority exists.

It does not mean execution may begin.

It does not mean production residuals are closed.

It does not mean external boundaries may be crossed.

Absence of a blocker is not equivalent to authorization.

## 7. System Authorities

CortAI has bounded authorities. Each authority has a specific domain and strict limits.

The primary authorities are:

- Policy Engine
- Account Health
- QC
- Strategy
- Publisher
- Orchestrator
- Kernel

No authority may silently absorb another authority.

No authority may bypass the Kernel execution model.

No authority may override explicit governance constraints.

## 8. What Each Authority May Decide

### 8.1 Policy Engine

Policy Engine may decide:

- `allow`
- `delay`
- `block`
- enforcement points
- policy reason codes
- policy scope validity
- execution boundary admissibility within declared policy

Policy Engine controls execution permission at Kernel enforcement points.

### 8.2 Account Health

Account Health may decide:

- account safety posture;
- account-level risk classification;
- account-level constraints;
- `SAFE`, `CAUTION`, or `HOLD` state;
- whether account risk blocks downstream action.

Account Health `HOLD` is blocking.

### 8.3 QC

QC may decide:

- final artifact evaluation;
- artifact severity;
- technical, perceptual, product, or environment failure classification;
- APPROVE / HOLD / REJECT within QC scope;
- publishable semantics within existing QC boundary;
- confidence in QC decision.

QC evaluates artifacts.

### 8.4 Strategy

Strategy may decide:

- domain direction;
- creative control posture;
- strategic constraints;
- priority orientation;
- governed intent for downstream creative agents.

Strategy is the control layer.

### 8.5 Publisher

Publisher may decide within current governed scope:

- publish eligibility trace semantics;
- publish attempt trace semantics;
- publish result trace semantics;
- dry-run evidence classification;
- sandbox governance boundaries;
- pre-execution guard states;
- offline preparation trace status.

Publisher is publication governance authority, not current external execution authority.

### 8.6 Orchestrator

Orchestrator may decide:

- coordination order within its governed scope;
- handoff sequencing;
- stage invocation structure when authorized;
- skipped-stage rationale;
- trace continuity across creative pipeline surfaces.

Orchestrator coordinates.

### 8.7 Kernel

Kernel may decide:

- contract validation outcome;
- execution scheduling under policy;
- worker dispatch under valid plan;
- executor invocation under policy;
- execution result classification;
- trace and audit emission for execution state.

Kernel controls execution mechanics, not domain meaning.

## 9. What Each Authority Must Not Decide

### 9.1 Policy Engine Must Not

Policy Engine must not decide domain strategy, creative quality, publication outcome, attribution causality, or product success.

Policy Engine must not allow execution outside explicit scope.

### 9.2 Account Health Must Not

Account Health must not publish.

Account Health must not become Strategy.

Account Health must not become QC.

Account Health must not authorize external calls.

### 9.3 QC Must Not

QC must not publish.

QC must not become Publisher.

QC must not override Account Health `HOLD`.

QC must not repair, rewrite, rerender, upload, schedule, or publish unless separately authorized by governed scope.

QC must not predict performance as execution authority.

### 9.4 Strategy Must Not

Strategy must not execute runtime work.

Strategy must not publish.

Strategy must not bypass Policy Engine.

Strategy must not override Account Health.

Strategy must not treat Learning, Trend, Novelty, Attribution, or Experiment outputs as direct execution authority.

### 9.5 Publisher Must Not

Publisher must not act as an external execution client in the current state.

Publisher must not create or use HTTP clients, SDK clients, endpoints, DNS/network paths, or APIs.

Publisher must not access credential values.

Publisher must not upload, schedule, publish, emit URLs, emit platform content IDs, or produce production receipts.

Publisher must not close production residuals.

### 9.6 Orchestrator Must Not

Orchestrator must not create authority.

Orchestrator must not hide runtime steps.

Orchestrator must not override Strategy, QC, Account Health, Publisher governance, Policy Engine, or Kernel constraints.

Orchestrator must not convert coordination into external execution.

### 9.7 Kernel Must Not

Kernel must not import Domain.

Kernel must not interpret CortAI payload semantics.

Kernel must not decide Strategy, QC meaning, Account Health posture, publication authority, attribution causality, or creative value.

Kernel must not execute without valid policy and contracts.

## 10. Mandatory HOLD Conditions

The system must enter `HOLD` when any of the following occurs:

- Account Health emits `HOLD`;
- QC emits blocking HOLD or REJECT under its scope;
- Policy Engine returns `block`;
- policy state is missing, expired, or inconsistent;
- runtime integration is treated as authorized without explicit authorization;
- runtime wiring appears without explicit authorization;
- external call capability appears;
- HTTP, SDK, endpoint, DNS, or API capability appears for Publisher external execution;
- credential values are accessed, logged, serialized, or persisted;
- request transformation appears without authorization;
- transport payload appears without authorization;
- upload, scheduler, or publish behavior appears;
- real URL, platform content ID, or receipt appears;
- Publisher bypasses QC or Account Health;
- QC becomes Publisher;
- Strategy becomes execution authority;
- Orchestrator creates hidden authority;
- Kernel imports Domain;
- Domain executes Kernel logic internally;
- tests are treated as authorization;
- gate passage is treated as unlimited permission;
- readiness is treated as runtime integration;
- trace is treated as success;
- sandbox evidence is treated as production evidence;
- production residuals are closed without real production evidence.

## 11. Current Non-Authorization Matrix

```json
{
  "system_state": "SAFE_PRE_CROSSING",
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

This matrix is authoritative for the current state.

Any artifact contradicting it must be treated as unsafe unless a later formal governance artifact explicitly supersedes it.

## 12. Open Production Residuals

Production residuals remain open.

At minimum, the following classes of residuals must not be closed in the current state:

- production publish evidence not available;
- platform integration not enabled;
- publish result history still short or absent;
- external call execution not authorized;
- runtime integration not authorized;
- post-publish metrics not available;
- production attribution causality not established;
- sandbox evidence not equivalent to production evidence.

Dry-run evidence may reduce observability uncertainty.

Sandbox evidence may reduce sandbox-boundary uncertainty.

Neither dry-run evidence nor sandbox evidence closes production residuals.

## 13. Separate Authorization Chains

Authorization chains must remain separate by scope.

A completed chain does not automatically authorize the next chain.

Separate chains are required for:

- implementation authorization;
- runtime integration authorization;
- runtime wiring authorization;
- external call authorization;
- credential value access authorization;
- request transformation authorization;
- upload authorization;
- scheduler authorization;
- publish authorization;
- production readiness;
- production residual closure.

The current chain is closed only up to `SAFE_PRE_CROSSING`.

The next valid work is separate runtime integration authorization chain planning only.

## 14. Current SAFE_PRE_CROSSING State

CortAI is currently in `SAFE_PRE_CROSSING`.

This means:

- offline preparation has been accepted with monitoring;
- readiness gates have passed with monitoring;
- runtime integration gates have passed as non-authorizing gates;
- runtime integration remains unauthorized;
- runtime wiring remains unauthorized;
- external calls remain unauthorized;
- implementation remains unauthorized; any future positive implementation scope requires a separate explicit authorization artifact;
- production readiness remains false;
- production residuals remain open.

This state is safe because the system has preserved boundaries and has not crossed into external execution.

Reference: [[CortAI_System_State_Definition]]

## 15. Internal Obsidian Links

Primary references:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_Execution_Model]]
- [[CortAI_System_State_Definition]]
- [[KERNEL_BIBLE]]
- [[FOUNDATION_KERNEL_GOVERNANCE]]

Recommended reading order:

1. [[KERNEL_BIBLE]]
2. [[FOUNDATION_KERNEL_GOVERNANCE]]
3. [[CortAI_Architecture_Bible]]
4. [[CortAI_Boundary_Specification]]
5. [[CortAI_Execution_Model]]
6. [[CortAI_Governance_Model]]
7. [[CortAI_System_State_Definition]]

## 16. Final Principle

CortAI governance exists to prevent capability from becoming authority.

Strategy controls direction but does not execute.

Account Health protects and blocks.

QC evaluates but does not publish.

Publisher governs publication but is not currently an external execution client.

Orchestrator coordinates but does not create authority.

Kernel executes only under explicit contracts and policy.

The system remains in `SAFE_PRE_CROSSING` until a separate governed authorization chain explicitly grants a new scope.
