# ACCOUNT_HEALTH_AGENT_SYSTEM_BIBLE_PHASE1

## 1. Executive Summary

The `Account Health Agent` in the current CortAI codebase is a small, deterministic upstream governance component.
It is implemented.
It runs in real runtime.
It is integrated into the creative orchestrator.
It has real blocking authority in one narrow but important way:
- `HOLD` stops pipeline execution before creative pack generation and before render/QC.

It is not an intelligent account telemetry system.
It is not a risk scoring system.
It is not a platform-health model.
It is not backed by real moderation, strike, violation, cooldown, or publishing telemetry.

Current classification:
- runtime-real: yes
- operationally authoritative: yes, but narrowly
- telemetry-rich: no
- baseline-ready as an intelligence subsystem: no
- operationally sufficient as a simple precondition gate: yes
- maturity level: simple deterministic governor, not advanced health intelligence

Direct answers:
- Is Account Health Agent real in runtime today? Yes.
- Is it integrated into the orchestrator? Yes.
- Does it actually influence pipeline behavior? Yes.
- Does it have real authority over downstream execution? Yes, for `HOLD`.
- Is it mostly advisory/contextual? No. It is not only advisory, because `HOLD` is enforced. But most of its non-blocking output is weakly operational.

## 2. Current Mission Of The Account Health Agent

Implementation fact:
- The agent evaluates a small input bundle and returns one of `SAFE`, `CAUTION`, or `HOLD`.
- It may also attach `recommended_constraints`.
- It exists to provide an upstream account posture before the rest of the creative pipeline proceeds.

Actual mission today:
- decide whether the account is healthy enough to proceed
- attach conservative constraints when signals look degraded
- stop execution on `HOLD`

What it is actually evaluating today:
- not account safety in a rich platform sense
- not moderation state
- not real posting health
- not strikes or violations
- not publish cooldown state
- not external telemetry

What it actually evaluates is a tiny synthetic health surface:
- `recent_publish_count`
- `recent_format_repetition_ratio`
- `recent_views_drop_ratio`
- `recent_low_performance_streak`

In practice, in the real orchestrator path today, only `account_id` is passed.
Those other fields remain at dataclass defaults.
That means real runtime behavior is dominated by:
- default inputs
- deterministic `SAFE`
- reason `HEALTHY_BASELINE`

So the actual mission in production-like runtime today is closer to:
- upstream deterministic health status emitter with real hold capability
than:
- real account telemetry evaluator

## 3. Responsibility Boundary

### Conceptual ownership
Conceptually, Account Health should own:
- account safety posture
- account risk state
- upstream go / constrain / hold decision
- pre-generation governance posture

### Actual ownership in code today
It actually owns:
- evaluation of a small synthetic account health input record
- emission of `SAFE` / `CAUTION` / `HOLD`
- emission of `reasons`
- emission of `recommended_constraints`
- fallback to safe default

### Authority start
Authority starts:
- before trend, learning, novelty, strategy, script, voice, asset, editor, and QC are allowed to continue
- inside `CreativeOrchestratorService._resolve_account_context(...)` and `CreativeOrchestratorService.execute(...)`

### Authority end
Authority ends at:
- blocking the orchestrator on `HOLD`
- injecting `health_status` and `recommended_constraints` into `Strategy`
- passing `account_health_status` into `Script` context
- persisting health output in `CreativePipelineExecution`

It does not own:
- publishability after render
- post-render quality governance
- trend detection
- learning feedback
- novelty control
- final runtime direction
- moderation enforcement in the publish layer

### Boundary relative to other subsystems
- `Trend`: external platform context. Account Health does not collect or shape trend evidence.
- `Learning`: internal execution/performance evidence. Account Health does not analyze execution history.
- `Novelty`: repetition/saturation control. Account Health does not manage novelty memory.
- `Strategy`: control layer. Account Health provides status and constraints; Strategy decides the profile.
- `QC`: post-render publishability governor. Account Health does not score the final product.
- `Orchestrator`: wiring and enforcement layer. Account Health does not orchestrate other agents itself.
- `Publish layer`: not owned by Account Health in current creative runtime.

The current subsystem is best described as:
- an upstream filter / policy injector with narrow hard authority
not:
- a comprehensive account governance intelligence layer

## 4. Architectural Position In The Pipeline

The real order in current code is:
1. `AccountHealthAgentService.evaluate(...)`
2. `TrendAnalysisAgentService.load(...)`
3. `LearningAgentService.generate(...)`
4. `NoveltyEngineService.generate(...)`
5. `StrategyAgentService.generate(...)`
6. `ExperimentCapabilityService.generate(...)`
7. Script / Voice / Asset / Editor pack construction
8. content pipeline render
9. `VideoQcAgentService.evaluate(...)`
10. QC governance application

This order is implemented in:
- `backend/app/creative/orchestrator/service.py`

Relevant files/classes:
- `backend/app/creative/agents/account_health/models.py`
- `backend/app/creative/agents/account_health/service.py`
- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/models.py`
- `backend/app/creative/contracts/orchestrator_io.py`
- `backend/app/creative/contracts/creative_pack.py`

Verification:
- Health is called first in `_resolve_account_context(...)`.
- `execute(...)` checks `account_health.decision.status == "HOLD"` before creative pack generation.
- `build_creative_pack(...)` also raises `AccountHealthHoldError` on `HOLD`.

So the conceptual ordering is real in code, not merely documented.

## 5. End-To-End Flow

Actual runtime flow:

1. Orchestrator receives `CreativeOrchestratorInput`
- fields: `account_id`, `niche`, `topic`, `publish_slot`, optional trend refresh refs

2. Orchestrator constructs `AccountHealthInput`
- current code only passes:
  - `account_id=data.account_id`
- all other health input fields remain defaulted to zero-like values

3. `AccountHealthAgentService.evaluate(...)` runs
- returns `AccountHealthResult`
- contains `decision` and `fallback`

4. If `decision.status == "HOLD"`
- orchestrator emits `CREATIVE/account_health_hold`
- returns `CreativePipelineExecution` with:
  - `creative_pack=None`
  - `pipeline_output.result.status="HOLD"`
  - `video_qc=None`
- later stages do not execute

5. If `SAFE` or `CAUTION`
- orchestrator continues through trend, learning, novelty, strategy, experiments, script, voice, asset, editor, pipeline, QC

6. Health output propagation
- `health_status` and `recommended_constraints` are injected into `StrategyInput`
- `account_health_status` is written into `ScriptAgentInput`
- `account_health_status` and `recommended_constraints` are embedded into `CreativePack`
- `account_health` is stored inside `CreativePipelineExecution`
- orchestrator emits `CREATIVE/account_health_safe` or `CREATIVE/account_health_caution`

7. Persistence
- when execution continues, health result is persisted in `execution_outputs.json`
- when `HOLD` happens, health result is still returned in execution payload

Important limitation:
- there is no deeper decision trace beyond `status`, `reasons`, and `recommended_constraints`
- there is no separate persisted health snapshot store owned by the agent

## 6. Contracts And Data Structures

### `AccountHealthInput`
Location:
- `backend/app/creative/agents/account_health/models.py`

Fields:
- `account_id: str`
- `recent_publish_count: int = 0`
- `recent_format_repetition_ratio: float = 0.0`
- `recent_views_drop_ratio: float = 0.0`
- `recent_low_performance_streak: int = 0`

Meaning:
- `account_id`: nominal account identity
- `recent_publish_count`: synthetic recent activity count
- `recent_format_repetition_ratio`: synthetic repetition signal
- `recent_views_drop_ratio`: synthetic performance degradation signal
- `recent_low_performance_streak`: synthetic streak signal

Operational status:
- serializable: yes
- actually used in evaluator: yes
- actually populated by orchestrator runtime: mostly no, except `account_id`

So this is a richer input contract than the real runtime currently feeds.

### `AccountHealthDecision`
Location:
- `backend/app/creative/agents/account_health/models.py`

Fields:
- `status: str`
- `reasons: list[str]`
- `recommended_constraints: dict[str, Any]`

Meaning:
- `status`: `SAFE`, `CAUTION`, or `HOLD`
- `reasons`: compact reason labels
- `recommended_constraints`: downstream advisory constraints

Operational status:
- serializable: yes
- persisted: yes, in execution artifacts and events
- `status`: strongly operational
- `reasons`: operational for audit visibility, not consumed as logic downstream
- `recommended_constraints`: partially operational via `Strategy`

### `AccountHealthResult`
Location:
- `backend/app/creative/agents/account_health/models.py`

Fields:
- `decision: AccountHealthDecision`
- `fallback: FallbackDecision`

Operational status:
- serializable: yes
- persisted: yes
- `fallback`: visible and operational only as audit / safety indication; it does not branch downstream logic except by changing the returned decision payload

### `FallbackDecision`
Location:
- `backend/app/creative/contracts/agent_common.py`

Fields:
- `used: bool`
- `mode: str`
- `reason: str`

Health-specific usage:
- normal path: `used=false`, `mode=NONE`
- fallback path: `used=true`, `mode=SAFE_DEFAULT`, `reason="ACCOUNT_HEALTH_COLD_START"`

### Health block in `CreativePack`
Location:
- `backend/app/creative/contracts/creative_pack.py`

Fields:
- `account_health_status: str = "SAFE"`
- `recommended_constraints: dict[str, Any]`

Operational status:
- persisted: yes
- `account_health_status`: weakly operational downstream, mainly for script context and artifact visibility
- `recommended_constraints`: partially operational because Strategy consumes them

### Health block in `CreativePipelineExecution`
Location:
- `backend/app/creative/orchestrator/models.py`

Field:
- `account_health: AccountHealthResult | None`

Operational status:
- persisted in `execution_outputs.json`: yes
- useful for auditability: yes
- no extra health-specific trace object exists

## 7. Input Surface

What Account Health consumes in code:
- `account_id`
- `recent_publish_count`
- `recent_format_repetition_ratio`
- `recent_views_drop_ratio`
- `recent_low_performance_streak`

What it does not consume today:
- real publish history
- QC history
- moderation signals
- strikes
- violations
- posting frequency from actual records
- cooldown state
- account telemetry store
- platform/account reputation state
- external telemetry
- trend results
- learning results
- novelty memory

What the real orchestrator passes today:
- only `account_id`

That means real runtime behavior is effectively based on:
- default zeros for all risk fields
- no dynamic account-specific evidence

Effect of each input today:
- `account_id`: currently identity only; it does not affect decision logic directly
- `recent_publish_count`: only used to guard negative-value fallback; otherwise no direct status thresholding
- `recent_format_repetition_ratio`: can trigger `CAUTION`
- `recent_views_drop_ratio`: can trigger `CAUTION` or `HOLD`
- `recent_low_performance_streak`: can trigger `CAUTION` or `HOLD`

Brutally explicit conclusion:
- the agent has a non-trivial input contract
- but the real pipeline currently exercises only a tiny subset of it
- so runtime health posture is mostly default-safe, not telemetry-driven

## 8. Output Surface

Current outputs:
- `status`
- `reasons`
- `recommended_constraints`
- `fallback`

### `status`
- deterministic: yes
- downstream use: strong
- used by: orchestrator and strategy
- authority: strong for `HOLD`, moderate for `CAUTION`, permissive for `SAFE`

### `reasons`
- deterministic: yes
- downstream use: mostly audit/event visibility
- used by: orchestrator events, artifacts
- authority: weak

### `recommended_constraints`
- deterministic: yes
- downstream use: real but narrow
- used by: `StrategyAgentService`
- authority: medium inside strategy shaping, none outside strategy

### `fallback`
- deterministic: yes
- downstream use: audit visibility only in practice
- authority: indirect

Actual outputs emitted by state:
- `SAFE` with `HEALTHY_BASELINE`
- `CAUTION` with combinations of:
  - `RECENT_VIEWS_DROP`
  - `FORMAT_REPETITION_HIGH`
  - `LOW_PERFORMANCE_STREAK`
- `HOLD` with `RECENT_VIEWS_DROP`
- fallback `SAFE` with `fallback_default`

## 9. Current Decision Model

The decision model is:
- rule-based
- deterministic
- threshold-driven
- static
- conservative in fallback
- not telemetry-backed in real runtime

Exact logic in `backend/app/creative/agents/account_health/service.py`:
- if `recent_publish_count < 0`:
  - fallback to safe default
- else if `recent_views_drop_ratio >= 0.75` or `recent_low_performance_streak >= 4`:
  - `HOLD`
  - add reason `RECENT_VIEWS_DROP`
  - add constraint `block_generation=True`
- else if `recent_views_drop_ratio >= 0.40` or `recent_format_repetition_ratio >= 0.65` or `recent_low_performance_streak >= 2`:
  - `CAUTION`
  - add reasons according to triggered thresholds
  - add constraints:
    - `reduce_hook_aggressiveness=True`
    - `max_daily_posts=1`
- else:
  - `SAFE`
  - reason `HEALTHY_BASELINE`

Important honesty points:
- this is not a risk model
- this is not scoring-based
- this is not confidence-aware
- this is not file-backed
- this is not account-history-aware
- this is not recency-aware beyond whatever upstream caller would inject
- it does not model publishing health in a real operational sense

The most accurate description is:
- deterministic baseline evaluator with a narrow threshold policy

In real pipeline runtime, because the orchestrator passes only `account_id`, the effective decision model becomes:
- deterministic default `SAFE` emitter under nominal conditions

## 10. Pipeline Authority And Enforcement

This is the most important operational fact.

### Does `HOLD` stop pipeline execution?
Yes.

Evidence:
- `CreativeOrchestratorService.execute(...)` returns early when `account_health.decision.status == "HOLD"`
- returned payload has:
  - `pipeline_output.result.status = "HOLD"`
  - no `creative_pack`
  - no `video_qc`
- `tests/test_phase2_block2_smoke_unittest.py` explicitly verifies this

### Does `SAFE` allow full execution?
Yes.

### Are `recommended_constraints` actually used?
Yes, but only meaningfully in `Strategy`.

Actual current uses inside `StrategyAgentService`:
- `reduce_hook_aggressiveness` -> downshifts hook aggressiveness and may force conservative mode
- `max_daily_posts == 1` -> narrows target duration to `8-10s`
- `prefer_shorter_duration` -> narrows target duration
- `low_variation_only` -> caps variation policy

Health itself emits only:
- `reduce_hook_aggressiveness`
- `max_daily_posts`
- `block_generation`

Of these:
- `reduce_hook_aggressiveness`: consumed
- `max_daily_posts`: consumed indirectly as a duration cap proxy
- `block_generation`: not consumed by Strategy; it is effectively redundant because orchestrator already stops on `HOLD`

### Does Health alter publishability directly?
No.

It alters preconditions for generation.
QC still owns post-render publishability.

### Is Health upstream governance or metadata?
It is real upstream governance because `HOLD` is enforced.
But its non-blocking behavior is much closer to policy metadata injection than rich governance intelligence.

## 11. Downstream Consumption

### Trend
- receives Health output? No.
- runtime effect: none
- coupling: none

### Learning
- receives Health output? No direct input
- runtime effect: none
- coupling: none

### Novelty
- receives Health output? No direct input
- runtime effect: none
- coupling: none

### Strategy
- receives Health output? Yes
- fields used:
  - `health_status`
  - `recommended_constraints`
- runtime effect: strong
- details:
  - `SAFE` -> standard base profile
  - `CAUTION` -> conservative base profile
  - `HOLD` -> paused base profile, though usually unreachable in full execution because orchestrator halts first
  - constraints modify aggressiveness, duration, variation
- coupling strength: strong

### Script
- receives Health output? Yes
- field used:
  - `account_health_status`
- runtime effect: weak
- detail:
  - passed into script generation context and prompt text
  - no hard branching in `ScriptAgentService` based on health
- coupling strength: weak / contextual

### Voice
- receives Health output? No direct health field
- runtime effect: none direct
- coupling strength: none

### Asset
- receives Health output? No direct health field
- runtime effect: none direct
- coupling strength: none

### Editor
- receives Health output? No direct health field
- runtime effect: none direct
- coupling strength: none

### QC
- receives Health output? Not as an input contract in the QC agent path
- runtime effect: indirect only, because `HOLD` can prevent QC from running at all
- coupling strength: indirect structural

Important distinction:
- present in execution payload: yes, widely visible
- truly behavior-changing: mostly only in orchestrator and strategy

## 12. Fallback / Default Paths

Fallback exists.

Trigger:
- exception inside `evaluate(...)`
- explicitly, negative `recent_publish_count` routes to fallback via `_evaluate(...)`

Fallback output:
- `status = SAFE`
- `reasons = ["fallback_default"]`
- `recommended_constraints = {}`
- `fallback.used = true`
- `fallback.mode = SAFE_DEFAULT`
- `fallback.reason = ACCOUNT_HEALTH_COLD_START`

Properties:
- safe: yes, in the sense of non-breaking pipeline continuity
- conservative from pipeline stability perspective: yes
- conservative from risk-governance perspective: no, because it does not fail closed

Important honesty point:
- fallback does not return `HOLD`
- fallback is intentionally permissive
- if real health telemetry is missing or malformed, the subsystem degrades to `SAFE`, not to a conservative stop

In practical runtime, because the orchestrator feeds almost no real health data, the system is not fallback-dominant, but it is default-dominant.
That distinction matters:
- fallback path is not the main path
- but the main path is still near-default because almost all risk inputs are left at zero

## 13. Traceability And Auditability

What exists:
- health decision persisted in `execution_outputs.json`
- health status and reasons emitted in creative events
- fallback visibility exists in serialized result
- `account_health_status` and `recommended_constraints` are embedded in `CreativePack`

What does not exist:
- dedicated health decision trace
- confidence score
- telemetry provenance
- per-decision evidence bundle
- standalone account health artifact store
- standalone health gate artifacts

Post-run reconstruction is possible only at a shallow level:
- status
- reasons
- recommended constraints
- fallback usage

This is enough to reconstruct what decision was made.
It is not enough to reconstruct a rich why, because there is no evidence trace.

Event surface actually visible:
- `CREATIVE/account_health_safe`
- `CREATIVE/account_health_caution`
- `CREATIVE/account_health_hold`

Traceability verdict:
- present
- shallow
- operationally adequate
- not audit-rich

## 14. Determinism And Governance

### Determinism
- deterministic: yes
- same input -> same output: yes
- hidden randomness: none

### Governance
- own standalone governance artifacts: no
- own promotion verdict: no evidence found
- own dedicated heavy audit gate: no evidence found
- broader pipeline treats it as authoritative: yes

This is a notable asymmetry:
- internally simple and weakly intelligent
- externally authoritative because the orchestrator enforces `HOLD`

So the subsystem is already governed by architecture more than by its own validation program.
It is structurally authoritative, not deeply governed as an independent subsystem.

## 15. Test Surface

### Dedicated unit tests
File:
- `tests/test_account_health_agent_phase2_unittest.py`

What it proves:
- healthy input returns `SAFE`
- degrading input returns `CAUTION`
- fallback returns `SAFE`, never `HOLD`

What it does not prove:
- no standalone proof of `HOLD` branch in the service
- no telemetry integration
- no persistence behavior
- no event behavior
- no downstream constraint consumption

### Orchestrator / smoke coverage
File:
- `tests/test_phase2_block2_smoke_unittest.py`

What it proves:
- `SAFE` path reaches pipeline and QC
- `HOLD` stops before pipeline
- `creative_pack` and `video_qc` are absent on hold

This is the strongest direct proof of real authority.

### Orchestrator integration
File:
- `tests/test_creative_orchestrator_phase2_unittest.py`

What it proves indirectly:
- health exists in the orchestrator path
- creative orchestrator produces end-to-end execution artifacts correctly

What it does not prove specifically for Health:
- no deep health-specific telemetry or policy complexity

### Strategy tests
File:
- `tests/test_strategy_agent_phase2_unittest.py`

What they prove about Health consumption:
- `health_status` changes base strategy posture
- `recommended_constraints` alter strategy profile
- `HOLD` remains dominant in strategy logic

What they do not prove:
- they test Strategy, not Health itself

### Broader gates / validations
Health appears inside:
- `tests/run_pipeline_v2_full_system_certification.py`
- `tests/run_pipeline_multiagent_heavy_audit_gate.py`
- several subsystem gates that instantiate the orchestrator

What this proves:
- Health is indirectly validated as part of orchestrator and pipeline continuity

What it does not prove:
- no dedicated heavy audit of Health as a standalone subsystem

## 16. Validation / Audit History

Observed validation status:
- indirectly validated through orchestrator and full pipeline gates
- referenced in pipeline certification artifacts as a functional upstream authority
- no standalone baseline promotion artifact found
- no standalone full validation gate for Account Health found

Evidence from broader certification:
- `OUT/audit/pipeline_v2_full_system_certification/block_summary.json`
- `OUT/audit/pipeline_multiagent_heavy_audit_gate/block_summary.json`

These explicitly treat health as:
- executed before generation
- capable of blocking pipeline execution

So current audit history is:
- real
- indirect
- structurally meaningful
- not standalone

## 17. Current Strengths

Real strengths:
- early pipeline authority is real
- `HOLD` semantics are operationally enforced
- deterministic and stable
- contract is small and clear
- reasons are visible in runtime artifacts and events
- fallback is explicit and serializable
- downstream constraint handoff to Strategy is real
- role ambiguity is low: it is clearly an upstream precondition gate

## 18. Current Weaknesses / Limitations

Real weaknesses:
- almost no real telemetry in runtime
- orchestrator currently passes only `account_id`
- account-specific behavior is mostly nominal, not evidence-driven
- no moderation or violation awareness
- no publish cooldown awareness in this agent
- no recency model beyond injected fields
- no scoring model
- no confidence or trust model
- no evidence/provenance trail
- `recommended_constraints` consumption is narrow and mostly limited to Strategy
- `block_generation` is redundant because orchestrator already blocks on `HOLD`
- fallback is permissive, not fail-closed
- no standalone heavy audit gate
- no standalone baseline governance artifact

Brutally honest summary:
- the subsystem has strong placement and real authority
- but weak intelligence and weak telemetry

## 19. Maturity Assessment

Assessment by dimension:
- implementation completeness: medium
- runtime authority: high
- telemetry richness: low
- downstream enforcement richness: low to medium
- traceability: medium-low
- governance as standalone subsystem: low
- baseline readiness as a simple gate: plausible
- baseline readiness as a health intelligence system: not there

Classification:
- not a prototype in the sense of "fake" or "decorative"
- not baseline-grade as an advanced health subsystem
- best labeled as: operationally sufficient alpha / simple beta governor

Can it be trusted operationally?
- yes, for one narrow guarantee: it can stop execution on `HOLD`

Is it strategically mature?
- no
- it is operationally sufficient, not strategically mature

## 20. Gap Between Current Account Health Agent And Target Health System

### Account telemetry richness
- current: near-zero in real orchestrator runtime
- target: real account telemetry ingestion
- gap: large

### Risk scoring
- current: fixed thresholds only
- target: richer risk model or governed scoring policy
- gap: large

### Moderation / violation awareness
- current: absent
- target: explicit moderation and violation signals
- gap: very large

### Publishing health awareness
- current: absent inside this agent
- target: account pacing, cooldown, block, and posting health awareness
- gap: large

### Recency modeling
- current: only if upstream injects streak/drop signals manually
- target: native recency-aware health state
- gap: large

### Dynamic constraint generation
- current: tiny fixed constraint set
- target: richer constraint policy surface
- gap: medium to large

### Downstream enforcement richness
- current: strong only for `HOLD`, partial in Strategy, weak elsewhere
- target: richer controlled policy propagation
- gap: medium

### Confidence / trust in decision
- current: absent
- target: explicit trust / confidence / evidence quality model
- gap: large

### Auditability
- current: shallow but present
- target: evidence-backed, trace-rich decisions
- gap: medium to large

### Baseline governance
- current: only indirectly validated
- target: standalone gate / promotion / monitoring if subsystem remains authoritative
- gap: medium

## 21. Next Correct Move

The next correct move is:
- write a formal `ACCOUNT_HEALTH_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN`

Reason:
- the subsystem is real enough and authoritative enough that its current simplicity should be made explicit before more power is added
- the main deficit is not structural presence
- the main deficit is telemetry activation and richer constraint / audit design

What should not happen first:
- baseline-promoting it as if it were already a rich health system
- inflating its authority without richer evidence inputs
- overengineering scoring before real telemetry exists

So the next correct move is not a broad rewrite.
It is:
- a grounded v2 plan that activates real health inputs while preserving the current hard boundary: upstream precondition governor, not a catch-all policy brain.

## Appendix: Implementation Facts Vs Inference Vs Intended Future Behavior

### Implementation fact
- Account Health is called first in the creative orchestrator.
- `HOLD` stops the pipeline.
- `SAFE` and `CAUTION` allow execution.
- real runtime currently passes only `account_id`.
- Strategy consumes health status and recommended constraints.
- Script receives health status context.

### Inferred runtime behavior
- because the orchestrator feeds default values, most runtime executions produce `SAFE` with `HEALTHY_BASELINE`
- the subsystem is operationally authoritative but informationally shallow

### Intended future behavior
- richer account telemetry
- richer dynamic constraints
- stronger auditability
- standalone governance and promotion logic

That future behavior is not implemented today and should not be credited to Phase 1.
