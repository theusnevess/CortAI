# CortAI Execution Model

## 1. Purpose

This document defines the formal conceptual execution model for CortAI.

The model explains how CortAI domain intent would be translated into Kernel-controlled execution through a Runtime Facade, contracts, policy decisions, scheduling, execution, and audit evidence.

This document is not an implementation plan.

This document does not authorize runtime wiring, runtime integration, external calls, upload, scheduling, publishing, or production readiness.

The current required state remains:

```json
{
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "production_ready": false
}
```

The execution model is a governance reference. It defines how execution must be represented if execution is ever authorized by a separate formal chain.

Related documents:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_Governance_Model]]
- [[CortAI_System_State_Definition]]
- [[KERNEL_BIBLE]]
- [[FOUNDATION_KERNEL_CONTRACTS]]
- [[FOUNDATION_KERNEL_RUNTIME_BEHAVIOR]]

## 2. Canonical Flow

The conceptual execution flow is:

```text
Domain Intent
-> Runtime Facade
-> WorkRequest
-> PolicyDecision
-> ExecutionPlan
-> AgentTask
-> Scheduler
-> Worker
-> Executor
-> ExecutionResult
-> Trace / Audit / Metrics
-> Domain Observation
```

This flow is mandatory as a conceptual control model.

No step may be skipped.

No step may be implicit.

No step grants broader authority than its declared scope.

No step authorizes current runtime integration or external calls.

## 3. Domain Intent

Domain Intent is the CortAI-level expression of desired work.

It may originate from Strategy, Orchestrator coordination, agent outputs, governance plans, or operator-level system intent.

### Domain Intent May

- express desired creative direction;
- identify requested capabilities;
- reference domain artifacts;
- preserve HOOK -> SETUP -> PAYOFF narrative structure;
- attach governance context;
- request translation into Kernel-facing contracts when authorized.

### Domain Intent Must Not

- execute Kernel logic;
- bypass the Runtime Facade;
- self-authorize runtime execution;
- call agents directly as execution;
- perform external calls;
- imply publication authority;
- treat intent as permission.

Domain Intent is requestable meaning, not execution.

## 4. Runtime Facade

The Runtime Facade is the boundary between CortAI Domain and Kernel contracts.

It translates domain intent into Kernel-facing structures only when such translation is within authorized scope.

### Runtime Facade May

- map domain intent into a conceptual WorkRequest;
- attach trace references;
- attach payload references;
- attach policy context references;
- preserve domain-to-kernel separation;
- reject unsupported domain intent.

### Runtime Facade Must Not

- decide policy;
- execute tasks;
- schedule work;
- call workers;
- invoke executors;
- perform runtime wiring without authorization;
- create hidden orchestration;
- transform references into transport payloads;
- authorize external calls.

The Runtime Facade translates. It does not decide. It does not execute.

## 5. WorkRequest

A WorkRequest is the formal Kernel-facing request for possible execution.

It represents work being requested, not work being allowed.

### WorkRequest May

- identify requester intent;
- identify requested capabilities;
- reference payloads;
- define idempotency scope;
- attach policy context;
- attach audit context;
- become eligible for policy evaluation.

### WorkRequest Must Not

- execute directly;
- imply authorization;
- bypass policy;
- create AgentTasks by itself;
- create external side effects;
- imply publication readiness;
- treat requester identity as permission.

## 6. Why WorkRequest Is Not Permission

A WorkRequest is structurally a request.

It does not prove that execution is safe.

It does not prove that dependencies are present.

It does not prove that Account Health allows execution.

It does not prove that QC permits downstream flow.

It does not prove that Strategy grants executable authority.

It does not prove that Publisher may act.

It does not prove that runtime integration exists.

It does not prove that external calls are authorized.

A valid WorkRequest can still be delayed or blocked.

## 7. PolicyDecision

PolicyDecision is the enforcement artifact that controls allow, delay, and block semantics.

### PolicyDecision May

- allow a specific action under explicit scope;
- delay execution under defined conditions;
- block execution under defined reasons;
- attach reason codes;
- identify enforcement points;
- preserve traceability.

### PolicyDecision Must Not

- grant authority outside its scope;
- imply downstream permission;
- override Account Health `HOLD`;
- override QC boundary;
- convert readiness into execution;
- authorize external calls unless explicitly scoped by a future governed chain.

### allow / delay / block

`allow` means the targeted action may proceed only within the declared policy scope.

`delay` means execution is not currently allowed and may be reconsidered only under explicit conditions.

`block` means execution is prohibited.

Missing policy means block.

Expired policy means block.

Inconsistent policy means block.

## 8. ExecutionPlan

ExecutionPlan is the formal orchestration structure.

It defines the directed acyclic graph of tasks, dependencies, ordering, parallelism, retry boundaries, and terminal conditions.

### ExecutionPlan May

- define task nodes;
- define dependency edges;
- define allowed ordering;
- define explicit parallelism;
- define failure strategy;
- define retry boundaries;
- define terminal states.

### ExecutionPlan Must Not

- execute by itself;
- create unlimited authorization;
- add hidden tasks;
- hide dependencies;
- bypass policy;
- bypass Scheduler;
- authorize runtime wiring;
- authorize external calls;
- authorize publishing.

## 9. Why ExecutionPlan Is Not Unlimited Authorization

ExecutionPlan defines possible execution structure.

It does not grant blanket permission.

Each task still requires valid policy, dependency satisfaction, scheduler eligibility, trace continuity, and boundary compliance.

A plan may be valid and still not executable.

A plan may be accepted and still blocked.

A plan may define future structure without authorizing current implementation.

In CortAI's current state, ExecutionPlan remains conceptual for the relevant external sandbox runtime path.

## 10. AgentTask

AgentTask is the atomic unit of agent execution under Kernel control.

It binds a capability, payload reference, policy context, execution constraints, and trace identity.

### AgentTask May

- identify the target agent capability;
- carry payload references;
- preserve dependency references;
- define execution constraints;
- attach trace context;
- become eligible for scheduling when allowed.

### AgentTask Must Not

- self-authorize;
- self-schedule;
- bypass policy;
- call other agents directly;
- create hidden downstream tasks;
- perform external effects outside declared scope;
- treat agent readiness as execution permission.

## 11. Why AgentTask Does Not Self-Authorize

An AgentTask is a contract-bound unit of work.

It has identity and structure, but not independent authority.

It requires:

- accepted ExecutionPlan;
- valid PolicyDecision;
- satisfied dependencies;
- Scheduler eligibility;
- Worker assignment;
- Executor enforcement;
- trace continuity.

Without those conditions, AgentTask must not execute.

## 12. Scheduler

The Scheduler determines which allowed tasks may be dispatched.

### Scheduler May

- evaluate task readiness;
- respect dependency state;
- enforce ordering;
- respect concurrency limits;
- apply delay windows;
- dispatch eligible tasks to workers when authorized.

### Scheduler Must Not

- invent tasks;
- infer hidden dependencies;
- bypass policy;
- treat queue presence as permission;
- perform external calls;
- treat readiness as execution authority.

Scheduling is controlled dispatch eligibility, not domain decision-making.

Lane 2 reconciliation: runtime-labeled paths that contain CortAI domain semantics must not be assumed to be neutral Kernel. `backend/app/runtime` is documented for this audit chain as a domain operational runtime with legacy runtime and mixed boundary surfaces. This boundary classification does not authorize scheduler invocation, worker invocation, executor invocation, refactor, rename, code changes, import changes, runtime integration, runtime wiring, external calls, credential access, tests, static scans, runners, tooling, upload, scheduling, publishing, production readiness, or residual closure.

## 13. Worker

Worker performs assigned task execution under Kernel control.

### Worker May

- receive assigned tasks;
- preserve task identity;
- invoke Executor through the approved boundary;
- report execution state;
- report failures and timeouts;
- preserve trace linkage.

### Worker Must Not

- choose arbitrary work;
- self-schedule;
- create hidden retries;
- mutate ExecutionPlan;
- bypass PolicyDecision;
- call external systems unless explicitly authorized;
- create untraced side effects.

## 14. Executor

Executor is the controlled invocation boundary.

It starts, constrains, observes, and finalizes task execution.

### Executor May

- enforce timeout policy;
- enforce execution constraints;
- attach trace identity;
- classify execution result;
- report side-effect mismatch;
- produce ExecutionResult.

### Executor Must Not

- infer domain success;
- create undeclared side effects;
- bypass trace;
- bypass policy;
- convert completion into publication readiness;
- execute external calls unless separately authorized.

## 15. ExecutionResult

ExecutionResult records what happened during Kernel-controlled execution.

It is an execution fact, not a domain truth.

### ExecutionResult May

- report completed, failed, blocked, delayed, skipped, cancelled, timed out, or rejected state;
- attach result references;
- attach failure reasons;
- preserve trace identity;
- support audit reconstruction.

### ExecutionResult Must Not

- prove creative success;
- prove business success;
- prove production readiness;
- imply publish authorization;
- imply external execution authorization;
- hide partial failure;
- hide side-effect mismatch.

## 16. Why ExecutionResult Does Not Prove Domain Success

Execution completion is not domain success.

A task may complete while producing weak domain output.

A QC evaluation may complete with rejection.

A trace may complete around a blocked state.

A dry-run may complete without production evidence.

An offline preparation result may complete without external execution.

Therefore, ExecutionResult must be interpreted by the Domain through governed observation, not treated as automatic success.

## 17. Trace / Audit / Metrics

Trace, audit, and metrics make execution observable.

They do not create execution authority.

### Trace May

- preserve lineage;
- connect request, policy, plan, task, worker, executor, and result;
- expose missing or degraded inputs;
- support replay and reconstruction.

### Audit May

- record decisions;
- preserve gate verdicts;
- record boundary state;
- classify residuals;
- expose failure conditions.

### Metrics May

- summarize runtime behavior;
- reveal trends;
- expose throughput, failure, latency, and coverage signals;
- support operational monitoring.

### Trace / Audit / Metrics Must Not

- become success;
- authorize execution;
- close production residuals without evidence;
- hide failure;
- convert dry-run evidence into production evidence;
- replace PolicyDecision.

## 18. Domain Observation

Domain Observation is the domain's interpretation of Kernel-visible facts.

The Domain may observe execution state, trace records, audit evidence, and metrics.

### Domain Observation May

- interpret execution facts within domain rules;
- feed governance review;
- inform future plans;
- preserve residual monitoring;
- support human audit.

### Domain Observation Must Not

- execute Kernel logic;
- mutate Kernel state;
- bypass policy;
- treat observation as authorization;
- turn metrics into causal proof;
- treat sandbox evidence as production evidence.

The Domain observes. It does not execute the Kernel.

## 19. Current State: SAFE_PRE_CROSSING

The current state is:

```json
{
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "production_ready": false,
  "system_state": "SAFE_PRE_CROSSING"
}
```

This means:

- the model is conceptual;
- runtime wiring remains unauthorized;
- runtime integration remains unauthorized;
- external calls remain unauthorized;
- production readiness remains false;
- offline preparation does not become execution;
- readiness gates do not authorize runtime integration;
- integration gates do not authorize runtime wiring unless explicitly stated by a future governed artifact.

Reference: [[CortAI_System_State_Definition]]

## 20. Boundaries Preventing Implicit Execution

The following boundaries prevent implicit execution:

- Domain Intent is not execution.
- Runtime Facade translates, not decides.
- WorkRequest is not permission.
- PolicyDecision is scoped and mandatory.
- ExecutionPlan is not unlimited authorization.
- AgentTask does not self-authorize.
- Scheduler dispatches only eligible tasks.
- Worker executes only assigned tasks.
- Executor enforces constraints but does not infer domain success.
- ExecutionResult is execution evidence, not domain success.
- Trace is observability, not success.
- Audit is evidence, not permission.
- Metrics are signals, not authority.
- Domain Observation does not execute Kernel logic.

Reference: [[CortAI_Boundary_Specification]]

## 21. Internal Obsidian Links

Primary references:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_Governance_Model]]
- [[CortAI_System_State_Definition]]
- [[KERNEL_BIBLE]]
- [[FOUNDATION_KERNEL_CONTRACTS]]
- [[FOUNDATION_KERNEL_RUNTIME_BEHAVIOR]]

Recommended reading order:

1. [[KERNEL_BIBLE]]
2. [[FOUNDATION_KERNEL_CONTRACTS]]
3. [[FOUNDATION_KERNEL_RUNTIME_BEHAVIOR]]
4. [[CortAI_Architecture_Bible]]
5. [[CortAI_Boundary_Specification]]
6. [[CortAI_Execution_Model]]
7. [[CortAI_Governance_Model]]
8. [[CortAI_System_State_Definition]]

## 22. Final Principle

The CortAI execution model defines how execution must be controlled if execution is ever authorized.

It does not authorize execution now.

The system remains in `SAFE_PRE_CROSSING`.

No conceptual flow, contract, plan, gate, test, trace, metric, or preparation artifact may be interpreted as runtime wiring, runtime integration, external call authorization, upload authorization, scheduler authorization, publish authorization, or production readiness.
