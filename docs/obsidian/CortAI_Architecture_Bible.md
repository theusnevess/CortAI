# CortAI Architecture Bible

## 1. Overview

CortAI is a cognitive media agency system for automated short-form video generation.

Its purpose is to coordinate cognitive planning, creative construction, artifact evaluation, and governed publication readiness without collapsing execution authority into domain logic.

The system is organized around a strict separation between decision layers, execution layers, governance layers, and audit layers.

The central narrative structure of CortAI content is:

```text
HOOK -> SETUP -> PAYOFF
```

This structure governs the creative shape of short-form content, but it does not grant execution authority, publication authority, external-call authority, or production readiness.

CortAI currently operates in:

```json
{
  "current_system_state": "SAFE_PRE_CROSSING",
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "production_ready": false
}
```

Related documents:

- [[CortAI_Boundary_Specification]]
- [[CortAI_Execution_Model]]
- [[CortAI_Governance_Model]]
- [[CortAI_System_State_Definition]]
- [[KERNEL_BIBLE]]

## 2. System Purpose

CortAI exists to transform governed creative intent into auditable short-form media workflows.

The system is designed to:

- analyze account, trend, learning, strategy, and content context;
- construct short-form narrative plans;
- create script, voice, asset, and QC traces;
- preserve boundary integrity across agents;
- prevent hidden execution;
- prevent fake confidence;
- prevent publication without governed authority;
- keep production residuals open until real evidence exists.

CortAI is not merely a content pipeline. It is a governed multi-agent media operating system whose correctness depends on explicit contracts, traceability, and non-authorization discipline.

## 3. Main Layers

CortAI is structured into five conceptual layers.

### 3.1 Kernel Layer

The Kernel is neutral, domain-agnostic, and execution-only.

The Kernel must not import domain logic. It must not interpret CortAI payload semantics. It must not decide creative strategy, publication readiness, account risk, QC authority, or platform behavior.

The Kernel controls execution only when execution is explicitly authorized through valid contracts and policy.

Reference: [[KERNEL_BIBLE]]

### 3.2 Runtime Facade Layer

The Runtime Facade translates between CortAI domain requests and Kernel-facing execution contracts.

The Runtime Facade is a boundary, not a decision layer.

It translates. It does not decide. It does not authorize. It does not create hidden orchestration. It does not perform external calls.

### 3.3 Domain Layer

The CortAI domain contains the creative and governance semantics of the system.

It includes agents, narrative structures, strategy interpretation, quality evaluation, account safety rules, publisher governance semantics, and audit models.

The Domain may define intent. It must not execute Kernel logic internally.

### 3.4 Operational Layer

The operational layer is responsible for controlled runtime mechanics when authorized.

In CortAI's current state, runtime integration and runtime wiring for the external sandbox path remain unauthorized.

Operational readiness is not execution permission.

Lane 2 reconciliation: `backend/app/runtime` is not classified as the neutral Kernel. For this audit chain it is documented as a domain operational runtime with legacy runtime and mixed boundary surfaces. Kernel neutrality remains mandatory, and this documentation classification does not authorize refactor, rename, code changes, import changes, runtime integration, runtime wiring, external calls, credential access, tests, static scans, runners, tooling, upload, scheduling, publishing, production readiness, or residual closure.

### 3.5 Audit And Governance Layer

The audit and governance layer defines gates, verdicts, traces, residuals, boundary reviews, and final state declarations.

This layer prevents readiness, traces, tests, and plans from becoming unauthorized execution.

Reference: [[CortAI_Governance_Model]]

## 4. Cognitive Layer vs Operational Layer

CortAI separates cognitive decision-making from operational execution.

### 4.1 Phase 1 Executes

Phase 1 is the operational execution foundation.

Its role is to provide runtime, pipeline, artifact handling, execution mechanics, and controlled operational behavior.

Phase 1 is execution-oriented.

### 4.2 Phase 2 Decides

Phase 2 is the cognitive decision layer.

Its role is to analyze, plan, score, govern, and explain.

Phase 2 agents may produce strategy, script, voice plans, asset selections, quality evaluations, confidence calibration, and trace evidence.

Phase 2 does not replace the runtime.

Phase 2 does not bypass the Kernel.

Phase 2 does not authorize external execution.

### 4.3 Separation Rule

The correct interpretation is:

```text
Phase 1 executes.
Phase 2 decides.
Governance controls advancement.
Kernel controls execution.
```

Any attempt to make the cognitive layer execute directly is a boundary violation.

## 5. Conceptual Pipeline

The CortAI conceptual pipeline is:

```text
Account Health
-> Trend Analysis
-> Learning / Attribution Context
-> Strategy
-> Experiment Governance
-> Script
-> Voice
-> Asset Selection
-> Editor / Creative Assembly Surface
-> Video QC
-> Publisher Governance
-> Audit / Residual Monitoring
```

This is a conceptual pipeline, not an authorization chain.

No stage may infer execution permission from the existence or completion of a prior stage.

The short-form creative structure remains:

```text
HOOK -> SETUP -> PAYOFF
```

This narrative structure informs Script, Voice, Asset Selection, Editor surfaces, and QC evaluation, but it does not grant publication authority.

Reference: [[CortAI_Execution_Model]]

## 6. Main Agents

### 6.1 Account Health Agent

Account Health protects account-level safety.

Its `HOLD` state is blocking.

No downstream agent, Publisher, Orchestrator, or runtime path may bypass Account Health `HOLD`.

### 6.2 Trend Analysis Agent

Trend Analysis provides advisory trend context.

It does not become Strategy. It does not directly authorize publishing. It does not override Account Health or QC.

### 6.3 Learning Optimization Agent

Learning provides bounded evidence and optimization pressure.

It must not create fake causality. It must not turn weak attribution into strategy authority. It must not close production residuals without real evidence.

### 6.4 Strategy Agent

Strategy is the control layer.

It determines governed creative direction and system intent within its domain boundary.

Strategy does not execute runtime work. Strategy does not publish. Strategy does not override Account Health. Strategy does not convert learning, trend, or novelty signals into hidden execution authority.

### 6.5 Experiment Agent

Experiment governance controls treatment/control semantics, exposure trace, and experiment safety.

It does not create publish authority. It does not override Strategy, Account Health, QC, or Publisher governance.

### 6.6 Script Agent

Script constructs the narrative spine.

It operates around HOOK, SETUP, and PAYOFF.

It may evaluate script quality, hook strength, setup progression, payoff memorability, diversity, fallback honesty, confidence, and traceability.

It does not become Strategy. It does not become QC. It does not predict performance.

### 6.7 Voice Agent

Voice plans delivery semantics.

It maps narrative intent into voice planning, timing, pause, contrast, provider/fallback honesty, audio evidence linkage, confidence, and traceability.

Voice does not become the TTS Router. Voice does not fabricate execution. Voice does not claim provider execution without evidence.

### 6.8 Asset Selection Agent

Asset Selection selects and explains visual intent and metadata-level alignment.

It is metadata-only unless a future governed layer authorizes otherwise.

It does not perform pixel-level validation. It does not become Strategy. It does not become QC. It does not treat fallback safe defaults as strong semantic evidence.

### 6.9 Editor Agent

The Editor layer represents creative assembly and edit planning surfaces.

Any future expansion of Editor authority requires evidence and a formal reopen path.

Editor must not become hidden runtime execution or hidden rerender authority.

### 6.10 Video QC Agent

Video QC evaluates final artifacts.

QC may decide artifact evaluation semantics such as APPROVE, HOLD, REJECT, publishable state, severity, evidence, and confidence in QC decision.

QC does not publish.

QC does not repair, rewrite, rerender, or predict performance unless separately authorized by governed scope.

### 6.11 Publisher Agent

Publisher is governed publication authority.

Publisher is not currently an external execution client.

Publisher may maintain governance, trace, dry-run evidence, sandbox adapter safety, validation envelope semantics, external-call boundaries, pre-execution guards, and offline preparation artifacts.

Publisher does not currently have authority to call external APIs, upload, schedule, publish, emit real URLs, emit platform content IDs, or produce production receipts.

### 6.12 Novelty Agent

Novelty tracks saturation, repetition, and fatigue risk.

Novelty must not become hidden Strategy, hidden QC, or hidden publishability authority.

Any future hardening of Novelty must remain governed and evidence-based.

### 6.13 Auditor Agent / Audit Function

The audit function validates gates, traces, residuals, non-authorization matrices, and boundary preservation.

Audit records evidence. Audit does not manufacture truth. Audit does not authorize execution outside its declared scope.

## 7. Creative Orchestrator Role

The Creative Orchestrator coordinates the creative pipeline.

It is not an execution authority beyond its governed orchestration scope.

It must preserve order, handoff integrity, skipped-stage rationale, boundary statements, and traceability.

The Orchestrator does not create hidden authority.

It does not override Strategy.

It does not override Account Health.

It does not override QC.

It does not convert Publisher governance into external execution.

The Orchestrator coordinates. It does not authorize by itself.

## 8. CreativePack Role

CreativePack is the consolidated creative contract surface.

It may carry structured outputs such as script plan, voice plan, asset plan, edit surfaces, and related trace references.

CreativePack is a contract, not execution.

CreativePack must not be interpreted as publish permission.

CreativePack must not be interpreted as runtime integration permission.

CreativePack must preserve traceability, boundary visibility, and non-authorization semantics.

## 9. Relationship With The Kernel

CortAI operates as a domain system above a neutral Multi-Agent Kernel.

The Kernel is:

- execution-only;
- domain-agnostic;
- payload-opaque;
- fail-closed;
- deterministic;
- audit-first;
- free of hidden side effects.

CortAI Domain does not execute Kernel logic internally.

The Runtime Facade translates CortAI intent into Kernel-facing contracts only when such translation is authorized.

The Kernel does not understand CortAI creative meaning.

The Kernel must not import CortAI domain modules.

CortAI agents must not execute outside Kernel control when runtime execution is in scope.

Reference: [[KERNEL_BIBLE]]

## 10. Current State: SAFE_PRE_CROSSING

The current system state is:

```json
{
  "offline_preparation_layer": "ACCEPTED_WITH_MONITORING",
  "runtime_integration_readiness_gate": "GO_WITH_MONITORING",
  "runtime_integration_gate": "GO_WITH_MONITORING",
  "phase_status": "STRUCTURALLY_COMPLETE",
  "current_chain_closed": true,
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "implementation_authorized": false,
  "production_ready": false,
  "current_system_state": "SAFE_PRE_CROSSING",
  "next_work": "SEPARATE_RUNTIME_INTEGRATION_AUTHORIZATION_CHAIN_PLANNING_ONLY"
}
```

This means the current chain is structurally complete, but execution remains unauthorized.

The system has proven boundary safety up to the pre-crossing state.

It has not crossed into external execution.

It has not crossed into runtime wiring.

It has not crossed into production.

Reference: [[CortAI_System_State_Definition]]

## 11. Absolute Boundaries

The following boundaries are absolute in the current state:

- `runtime_integration_authorized = false`
- `runtime_wiring_authorized = false`
- `external_call_authorized = false`
- `production_ready = false`
- HTTP client authorization remains false
- SDK authorization remains false
- endpoint authorization remains false
- DNS/network authorization remains false
- API call authorization remains false
- credential value access authorization remains false
- request transformation authorization remains false
- transport payload authorization remains false
- upload authorization remains false
- scheduler authorization remains false
- real publish authorization remains false
- real URL emission remains forbidden
- `platform_content_id` emission remains forbidden
- receipt emission remains forbidden
- production residual closure remains forbidden

Reference: [[CortAI_Boundary_Specification]]

## 12. What CortAI Is Not Yet Authorized To Do

CortAI is not authorized to perform runtime integration for the external sandbox path.

CortAI is not authorized to create runtime wiring for the offline preparation layer.

CortAI is not authorized to make external calls.

CortAI is not authorized to create or use HTTP clients, SDK clients, endpoints, DNS access, or platform APIs for Publisher external execution.

CortAI is not authorized to access credential values.

CortAI is not authorized to transform validation envelopes into transport payloads.

CortAI is not authorized to upload media.

CortAI is not authorized to invoke a scheduler for real publishing.

CortAI is not authorized to publish.

CortAI is not authorized to emit real published URLs.

CortAI is not authorized to emit real platform content IDs.

CortAI is not authorized to emit production receipts.

CortAI is not production-ready.

CortAI is not authorized to close production residuals.

## 13. Internal Obsidian Links

Primary architecture documents:

- [[KERNEL_BIBLE]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_Execution_Model]]
- [[CortAI_Governance_Model]]
- [[CortAI_System_State_Definition]]

Recommended reading order:

1. [[KERNEL_BIBLE]]
2. [[CortAI_System_State_Definition]]
3. [[CortAI_Boundary_Specification]]
4. [[CortAI_Governance_Model]]
5. [[CortAI_Execution_Model]]
6. `CortAI_Architecture_Bible`

## 14. Final Principle

CortAI is a governed cognitive media agency system.

Its power comes from separating cognition from execution, orchestration from authority, trace from success, readiness from integration, preparation from external call, and sandbox evidence from production evidence.

The system remains in `SAFE_PRE_CROSSING` until a separate governed authorization chain explicitly grants the next scope.

Nothing in this document authorizes implementation, runtime integration, runtime wiring, external calls, platform API use, upload, scheduling, publishing, production readiness, or production residual closure.
