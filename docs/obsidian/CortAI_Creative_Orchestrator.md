# CortAI Creative Orchestrator

## 1. Purpose

This document defines the real role of the Creative Orchestrator in CortAI.

The Creative Orchestrator coordinates the creative agent flow and assembles the resulting creative contract surface. It is responsible for ordered handoff, context propagation, event emission, CreativePack construction, local content pipeline handoff, QC handoff, and final execution summary composition.

The Creative Orchestrator is not an authorization authority.

It does not replace Strategy, QC, Account Health, Publisher governance, Policy Engine, Runtime Facade, or Kernel authority.

It does not authorize runtime integration.

It does not authorize runtime wiring.

It does not authorize external calls.

It does not authorize upload, scheduler, or real publish.

Related documents:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Execution_Model]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_Governance_Model]]

## 2. Orchestrator Role

The Creative Orchestrator is a coordinator for the CortAI creative pipeline.

Its real implementation is centered in:

- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/models.py`
- `backend/app/creative/orchestrator/events.py`
- `backend/app/creative/contracts/orchestrator_io.py`
- `backend/app/creative/contracts/creative_pack.py`

The Orchestrator coordinates these services and contracts:

- Account Health
- Trend Analysis
- Learning
- Novelty
- Strategy
- Experiment Capability
- Script
- Voice
- Asset Selection
- Editor
- Content Pipeline
- Video QC

The Orchestrator has two important surfaces:

### 2.1 CreativePack Construction Surface

`build_creative_pack` resolves account context, enforces Account Health `HOLD`, coordinates creative agents, and returns a `CreativeOrchestratorResult` containing a `CreativePack`.

This surface constructs a creative contract.

It does not publish.

It does not call external platforms.

### 2.2 Pipeline Execution Surface

`execute` resolves the same context, builds the CreativePack, invokes the local content pipeline, evaluates Video QC, applies QC governance to the pipeline output, records experiment runtime result evidence, emits events, and returns `CreativePipelineExecution`.

This surface may create local render artifacts and local publish manifest semantics through the content pipeline when QC approves.

It does not make Publisher an external client.

It does not authorize external execution.

It does not create platform URLs, platform content IDs, external receipts, upload behavior, or real publication.

## 3. Inputs

The primary input contract is `CreativeOrchestratorInput`.

It contains:

- `account_id`
- `niche`
- `topic`
- `publish_slot`
- `force_refresh_trends`
- `creative_pack_id`
- `experiment_assignment_id`
- `account_context_ref`
- `trend_context_ref`

### Input Semantics

`account_id` identifies the account context.

`niche` identifies the content niche.

`topic` identifies the creative subject.

`publish_slot` is scheduling metadata used by content and experiment contracts, not real publish authorization.

`force_refresh_trends` influences Trend Analysis refresh behavior inside its own boundary.

`creative_pack_id` may preserve a caller-supplied creative identity.

`experiment_assignment_id`, `account_context_ref`, and `trend_context_ref` preserve context linkage.

### Inputs Must Not Be Interpreted As

Inputs must not be interpreted as runtime authority.

Inputs must not be interpreted as external-call authorization.

Inputs must not be interpreted as publish permission.

Inputs must not override Account Health, QC, Policy Engine, Publisher governance, or Kernel boundaries.

## 4. Outputs

The Orchestrator produces two main output shapes.

### 4.1 CreativeOrchestratorResult

`CreativeOrchestratorResult` contains:

- `creative_pack`
- `fallbacks_used`
- `events_emitted`
- `qc_required`

This output represents a creative contract and coordination evidence.

It is not runtime integration permission.

It is not external execution permission.

It is not production readiness.

### 4.2 CreativePipelineExecution

`CreativePipelineExecution` contains:

- `creative_pack`
- `pipeline_output`
- `video_qc`
- `account_health`
- `trend_analysis`
- `learning`
- `novelty`
- `strategy`
- `experiment`
- `asset_selection`

This output consolidates the result of the coordinated creative pipeline.

It may include local content pipeline status, local artifacts, QC result, and traces.

It must not be interpreted as real publication evidence.

It must not be interpreted as external platform evidence.

It must not close production residuals.

## 5. Agent Coordination Flow

The real coordination flow is:

```text
CreativeOrchestratorInput
-> Account Health
-> Trend Analysis
-> Learning
-> Novelty
-> Strategy
-> Experiment Capability
-> Script
-> Voice
-> Asset Selection
-> Hook Visual Alignment
-> Editor
-> CreativePack
-> Content Pipeline
-> Video QC
-> QC Governance Application
-> Experiment Result Recording
-> CreativePipelineExecution
```

### 5.1 Account Health

The Orchestrator evaluates Account Health first through `AccountHealthAgentService`.

If Account Health returns `HOLD`, the Orchestrator must stop the creative path.

In `build_creative_pack`, this raises `AccountHealthHoldError`.

In `execute`, this returns a `CreativePipelineExecution` with no CreativePack, no QC result, and pipeline output status `HOLD`.

Account Health `HOLD` is blocking.

### 5.2 Trend Analysis

Trend Analysis loads trend context for the account and niche.

The Orchestrator records trend loaded, fallback, refresh, validation, and shift events.

Trend Analysis informs downstream strategy and creative decisions.

It does not become Strategy.

It does not authorize publishing.

### 5.3 Learning

Learning produces insights, policy signals, pattern findings, and evidence summaries.

The Orchestrator passes Learning outputs into Strategy, Experiment, and CreativePack.

Learning pressure remains bounded.

Learning does not override Strategy or Account Health.

### 5.4 Novelty

Novelty produces pressure context for saturation and repetition.

The Orchestrator passes Novelty pressure into Strategy and Experiment.

When QC approves, the Orchestrator registers approved execution with Novelty for future saturation history.

Novelty must not become hidden Strategy, hidden QC, or hidden publish authority.

### 5.5 Strategy

Strategy receives health status, recommended constraints, trend profile, novelty pressure, learning policy, and pattern findings.

Strategy produces the strategy profile used by Script, Voice, Asset Selection, Editor, and CreativePack.

Strategy is the control layer.

The Orchestrator consumes Strategy output but does not replace Strategy.

### 5.6 Experiment Capability

Experiment Capability generates experiment plan and assignment context.

The Orchestrator records experiment assignment and later records runtime result evidence after QC and pipeline output are available.

Experiment output does not create publish authority.

Experiment result recording does not prove production causality.

### 5.7 Script

Script generates the narrative structure using HOOK, SETUP, and PAYOFF.

The Orchestrator passes Account Health, Strategy, Trend, Learning, and Experiment context into Script.

Script output becomes part of CreativePack.

Script does not become Strategy or QC.

### 5.8 Voice

Voice resolves voice plan from script and strategy context.

Voice output becomes part of CreativePack and later content pipeline input.

Voice does not become TTS Router.

Voice planning does not prove audio execution.

### 5.9 Asset Selection

Asset Selection selects visual assets from niche, topic, Strategy, Trend, and Script context.

The Orchestrator also applies `align_first_frame` to improve hook visual alignment inside the Asset Selection boundary.

Asset Selection output becomes part of CreativePack.

Asset Selection does not become QC or Strategy.

### 5.10 Editor

Editor creates edit plan using Script, Voice, Asset, Strategy, and Trend context.

EditPlan includes caption, music, transition, motion, color, timing, and runtime constraint surfaces.

Editor output becomes part of CreativePack.

Editor does not become renderer authority or external execution authority.

### 5.11 Content Pipeline

The Orchestrator passes CreativePack-derived script, asset plan, edit plan, voice plan, voice profile, publish slot, and experiment variant into `ContentPipelineService.run_pipeline`.

The current Orchestrator calls the content pipeline with `defer_publish_manifest=True`, meaning render output is produced before publish manifest governance is applied.

This is local content pipeline coordination, not external platform publishing.

### 5.12 Video QC

Video QC evaluates the rendered artifact using video path, audio path, metadata path, script text, TTS trace, visual trace, and edit trace.

The Orchestrator applies QC governance:

- if QC status is `APPROVE`, it calls content pipeline `finalize_publish`;
- if QC status is `HOLD` or `REJECT`, it calls content pipeline `mark_non_publishable`.

In the current implementation, `finalize_publish` creates local publish manifest semantics through the content pipeline adapter. It is not external publication.

QC remains artifact evaluator.

QC does not publish.

## 6. CreativePack Relationship

CreativePack is the consolidated creative contract produced by the Orchestrator.

The `backend/app/creative/contracts/creative_pack.py` CreativePack includes:

- `creative_pack_id`
- `account_id`
- `niche`
- `topic`
- `strategy_profile`
- `trend_profile`
- `script_plan`
- `voice_plan`
- `asset_plan`
- `edit_plan`
- `learning_insights`
- `learning_policy`
- `pattern_findings_summary`
- `experiment_plan`
- `experiment_assignment`
- `account_health_status`
- `recommended_constraints`
- `generated_at`
- `orchestrator_version`

CreativePack is the key handoff object between cognitive creative planning and local content pipeline surfaces.

CreativePack is not execution authority.

CreativePack is not publication authorization.

CreativePack is not external-call authorization.

CreativePack is not production readiness.

### Note On Legacy Content CreativePack

There is also a separate `backend/app/content/creative_pack/` model and generator service for older content-pack generation workflows.

That model is distinct from the richer Phase 2 creative contract in `backend/app/creative/contracts/creative_pack.py`.

This document refers primarily to the Phase 2 creative contract used by the Creative Orchestrator.

## 7. Boundaries

### 7.1 Orchestrator Coordinates, It Does Not Authorize

The Orchestrator coordinates agent calls and content pipeline handoffs.

It does not create authority.

It does not grant runtime integration.

It does not grant external-call permission.

### 7.2 Orchestrator Does Not Replace Account Health

Account Health `HOLD` blocks the flow.

The Orchestrator must surface and respect Account Health `HOLD`.

### 7.3 Orchestrator Does Not Replace Strategy

Strategy remains the control layer.

The Orchestrator passes context into Strategy and consumes Strategy output.

It does not decide Strategy semantics itself.

### 7.4 Orchestrator Does Not Replace QC

QC remains final artifact evaluator.

The Orchestrator invokes QC and applies the result to local content pipeline governance.

It does not evaluate final artifact quality itself.

### 7.5 Orchestrator Does Not Replace Publisher

Publisher governance remains separate.

The Orchestrator does not become an external publish client.

A local `publish_manifest` created by the content pipeline is not external publication.

### 7.6 Orchestrator Does Not Execute External Calls

The Orchestrator must not create HTTP clients, SDK clients, endpoints, DNS/network calls, upload behavior, platform API calls, platform URLs, platform content IDs, or production receipts.

### 7.7 Orchestrator Does Not Create Runtime Authority

The Orchestrator may coordinate within the existing application runtime surface.

It does not authorize Kernel runtime integration, external sandbox runtime wiring, or external execution.

### 7.8 Trace Is Not Success

Events emitted by the Orchestrator are observability records.

They do not prove domain success.

They do not authorize publication.

They do not close residuals.

## 8. Failure Conditions

The Creative Orchestrator must be treated as unsafe or blocked if any of the following occurs:

- Account Health `HOLD` is ignored;
- Strategy is bypassed or replaced by Orchestrator logic;
- QC result is ignored;
- QC `HOLD` or `REJECT` is converted into publishable output;
- Orchestrator emits or creates external platform evidence;
- Orchestrator creates HTTP, SDK, endpoint, DNS, API, upload, scheduler, or publish behavior;
- Orchestrator treats local publish manifest creation as real external publication;
- Orchestrator closes production residuals;
- Orchestrator converts events into authority;
- Orchestrator creates hidden runtime steps;
- Orchestrator calls Publisher external execution paths without separate authorization;
- CreativePack is treated as external execution permission;
- Content pipeline result is treated as production readiness.

If any of these conditions appears, the correct governance outcome is `HOLD`.

## 9. Current SAFE_PRE_CROSSING State

The current system state remains `SAFE_PRE_CROSSING`.

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

For the Creative Orchestrator, this means:

- it may be documented;
- its current coordination role may be analyzed;
- its boundaries may be clarified;
- its existing local content pipeline handoff may be described;
- its external execution authority remains false;
- Publisher external execution remains unauthorized;
- runtime integration authorization remains false;
- production readiness remains false;
- production residuals remain open.

No statement in this document authorizes new code, runtime integration, runtime wiring, external calls, upload, scheduler, real publish, production readiness, or production residual closure.

## 10. Obsidian Links

Primary references:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Execution_Model]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_Governance_Model]]

Recommended reading order:

1. [[CortAI_Architecture_Bible]]
2. [[CortAI_Boundary_Specification]]
3. [[CortAI_Governance_Model]]
4. [[CortAI_Execution_Model]]
5. `CortAI_Creative_Orchestrator`

## 11. Final Principle

The Creative Orchestrator is the coordinator of CortAI creative flow.

It is not Strategy.

It is not QC.

It is not Account Health.

It is not Publisher external execution.

It is not Kernel authority.

It coordinates agent outputs and local content pipeline handoff while preserving governance boundaries.

Coordination is not authorization.
