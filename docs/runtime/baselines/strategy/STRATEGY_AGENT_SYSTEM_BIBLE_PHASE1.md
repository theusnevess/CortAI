# Strategy Agent System Bible Phase 1

## 1. Executive Summary

The Strategy Agent in the current CortAI codebase is a real runtime component, but it is still a Phase 1 prototype rather than a mature strategic governor.

What is true today:
- it is implemented in code
- it is called by the creative orchestrator at runtime
- it produces a real `StrategyProfile`
- that `StrategyProfile` is stored in `CreativePack`
- downstream agents receive it

What is also true today:
- the Strategy Agent's own decision logic is shallow
- it is mostly a deterministic profile assembler driven by account health status and a hardcoded goal
- it does not meaningfully reason over trend tradeoffs, saturation, novelty, risk, or account-specific objectives
- much of its strategic intent is still conceptual rather than operational

Current status:
- implemented: yes
- integrated into runtime: yes
- operationally influential: partially
- baseline-ready as a strategic subsystem: no
- prototype-only: no, because it runs in production-like flows
- prototype-grade: yes, because its decision model is still minimal

Brutally honest summary:
- the Strategy Agent is not fake
- it is not merely a document-level concept
- but it is also not yet a true strategic governor of generation behavior
- today it is best described as an integrated prototype with limited authority and limited intelligence

## 2. Current Mission of the Strategy Agent

The Strategy Agent's actual mission today is narrow:
- translate account health state plus a small amount of upstream context into a `StrategyProfile`
- attach that profile to the creative execution context
- let downstream systems see that profile

What it actually does today:
- chooses a `goal`
- chooses a `content_mode`
- chooses a `hook_aggressiveness`
- chooses a `target_duration_range`
- chooses a `variation_policy`
- emits fallback metadata if strategy generation falls back

What it does not actually do today:
- it does not select among multiple objectives based on live business context
- it does not optimize hook aggressiveness from recent performance
- it does not actively govern variation from saturation signals
- it does not consume trend analysis directly
- it does not apply learning insights in a meaningful rule engine
- it does not control risk in any sophisticated way

Most precise description:
- today the Strategy Agent generates a small strategy profile that is deterministic and low-dimensional
- it does not yet act like a true long-horizon strategy controller

## 3. Responsibility Boundary

### Account Health

Conceptually owns:
- whether generation should proceed safely
- risk state of the account
- recommended constraints

Actually owns today:
- `SAFE`, `CAUTION`, or `HOLD`
- recommended constraint payloads
- pre-strategy hold behavior in the orchestrator

Strategy does not replace Account Health.

### Trend Analysis

Conceptually owns:
- trend context
- hook families
- pacing bias
- visual style signals

Actually owns today:
- generation of `TrendProfile`
- direct downstream context for Script, Asset, and Editor paths

Strategy does not consume `TrendProfile` directly today.

### Learning Agent

Conceptually owns:
- lessons from prior outcomes
- recommendations
- voice/style preferences
- signal summaries

Actually owns today:
- generation of `LearningInsights`
- a signal summary dict that is passed into Strategy as `recent_metrics_summary`

Strategy receives part of Learning output today, but does not use it meaningfully.

### Strategy Agent

Conceptually should own:
- generation posture
- objective weighting
- aggressiveness
- variation posture
- duration intent
- risk mode

Actually owns today:
- assembling `StrategyProfile`
- fallback to a default strategy profile when status is invalid or an exception occurs

What it does not own today:
- no direct blocking authority
- no experiment control
- no saturation control
- no novelty control
- no budget/risk arbitration
- no downstream enforcement beyond profile emission

### Script Agent

Owns:
- script generation
- narrative mode realization
- hook/setup/payoff text

Strategy does not write script text.

### Voice Agent

Owns:
- voice style interpretation
- delivery profile
- segment pacing

Strategy does not synthesize audio directly.

### Asset Agent

Owns:
- asset planning and selection
- visual query logic
- first-frame alignment

Strategy does not select assets directly today.

### Editor Agent

Owns:
- edit plan
- captions
- motion
- atmosphere
- timing

Strategy does not currently shape editor behavior in code.

### QC Agent

Owns:
- approve/hold/reject judgment
- publishability governance

Strategy does not decide publishability.

## 4. Architectural Position in the Pipeline

The conceptual pipeline is:

`Account Health -> Trend Analysis -> Learning -> Strategy -> Script -> Voice -> Asset -> Editor -> QC`

This order is real in current orchestrator code.

Actual runtime file:
- `backend/app/creative/orchestrator/service.py`

Actual behavior:
1. account health is evaluated
2. trend analysis runs
3. learning runs
4. strategy runs
5. experiment capability runs
6. script agent runs
7. voice agent runs
8. asset selection runs
9. editor runs
10. content pipeline renders
11. QC evaluates final output

Strategy is therefore:
- real in runtime
- upstream of all generation agents
- included in the orchestrated execution result

But this must be stated carefully:
- Strategy sits in the pipeline early
- downstream agents receive the profile
- only some downstream agents actually use it materially

Files/classes involved:
- `backend/app/creative/agents/strategy/service.py`
- `backend/app/creative/agents/strategy/models.py`
- `backend/app/creative/contracts/creative_pack.py`
- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/models.py`

## 5. End-to-End Flow

Actual runtime sequence:

1. `CreativeOrchestratorService.execute(...)` is called.
2. `_resolve_account_context(...)` evaluates:
   - account health
   - trend analysis
   - learning
   - strategy
   - experiment
3. Strategy is invoked as:
   - `strategy_agent.generate(StrategyInput(...))`
4. The result is stored as `strategy_result`.
5. The orchestrator emits event:
   - `CREATIVE/strategy_profile_generated`
6. `strategy_result.strategy_profile` is stored into `CreativePack.strategy_profile`.
7. That same profile is passed into:
   - Script Agent
   - Voice Agent
   - Asset Selection Agent
   - Editor Agent
8. `CreativePipelineExecution` returns `strategy` as a top-level execution component and also embeds the profile inside `creative_pack`.

Grounded code path:
- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/models.py`

Important runtime fact:
- Strategy output is persisted and propagated
- but downstream effect is uneven

## 6. Contracts and Data Structures

### `StrategyProfile`

File:
- `backend/app/creative/contracts/creative_pack.py`

Fields:
- `goal: str = "retention"`
- `content_mode: str = "standard"`
- `hook_aggressiveness: str = "medium"`
- `target_duration_range: str = "8-12s"`
- `variation_policy: str = "low"`

Serialization:
- serializable via `to_dict()`
- embedded in `CreativePack`
- embedded in downstream inputs that include strategy

Operational assessment by field:

`goal`
- operational in Strategy service output
- included in Script generation prompt
- emitted in strategy event
- not directly enforced as a policy engine elsewhere

`content_mode`
- operational in Strategy service output
- included in Script prompt
- used by Voice interpreter when niche does not already override style
- not used by Asset or Editor code

`hook_aggressiveness`
- operational in Strategy service output
- included in Script prompt
- not directly consumed by Voice, Asset, or Editor
- no hard enforcement of hook behavior exists

`target_duration_range`
- operational in Strategy service output
- included in Script prompt
- directly affects Voice overall rate in one rule path
- not used by Asset or Editor code

`variation_policy`
- operational as a field in the profile
- serialized and persisted
- not consumed by Script prompt
- not consumed by Voice
- not consumed by Asset
- not consumed by Editor
- today this field is mostly symbolic

### `StrategyInput`

File:
- `backend/app/creative/agents/strategy/models.py`

Fields:
- `account_id: str`
- `account_goal: str`
- `recent_metrics_summary: dict[str, Any]`
- `health_status: str = "SAFE"`
- `recommended_constraints: dict[str, Any]`

Serialization:
- no custom `to_dict()` on the dataclass itself
- operational as input to the service

Operational assessment:
- `account_goal`: used
- `health_status`: used
- `recent_metrics_summary`: accepted but ignored by service logic
- `recommended_constraints`: accepted but ignored by service logic

### `StrategyResult`

File:
- `backend/app/creative/agents/strategy/models.py`

Fields:
- `strategy_profile: StrategyProfile`
- `fallback: FallbackDecision`

Serialization:
- serializable via `to_dict()`
- returned in execution result as `execution.strategy`

Operational assessment:
- fully operational as the Strategy Agent output container

### `CreativePack.strategy_profile`

File:
- `backend/app/creative/contracts/creative_pack.py`

Operational status:
- real
- serialized
- carried through pipeline execution

This is not decorative. It is a real part of the pack.

### `CreativePipelineExecution.strategy`

File:
- `backend/app/creative/orchestrator/models.py`

Operational status:
- real
- serialized
- exposes `StrategyResult` in top-level execution output

## 7. Input Surface

The Strategy Agent consumes the following inputs today:

### `account_id`

Source:
- orchestrator input

Used today:
- accepted by Strategy service
- not materially used in decision logic

Assessment:
- structurally present
- not strategically meaningful today

### `account_goal`

Source:
- orchestrator currently hardcodes `"retention"`

Used today:
- yes
- becomes `goal` in the strategy profile unless blank, then defaults to `"retention"`

Assessment:
- meaningful in service logic
- but not dynamic in current runtime because orchestrator always passes `"retention"`

### `health_status`

Source:
- Account Health Agent decision

Used today:
- yes
- this is the strongest real input to Strategy

Operational effect:
- `SAFE` -> standard profile
- `CAUTION` -> conservative profile
- `HOLD` -> paused profile
- invalid status -> fallback default strategy

### `recent_metrics_summary`

Source:
- `learning_result.learning_insights.signal_summary`

Used today:
- passed into Strategy
- not actually read by decision logic

Assessment:
- implementation fact: present
- strategic fact: inert

### `recommended_constraints`

Source:
- `account_health.decision.recommended_constraints`

Used today:
- passed into Strategy
- not actually read by decision logic

Assessment:
- implementation fact: present
- strategic fact: inert

### Inputs Strategy does not consume today

Not passed into Strategy service:
- `TrendProfile`
- full `LearningInsights`
- experiment assignment
- niche
- topic

This is important.

Although Strategy sits after trend and learning in the pipeline, its own service does not directly consume trend profile and does not use full learning context. The prototype is therefore much less context-rich than its architectural role implies.

## 8. Output Surface

The Strategy Agent emits:

### `strategy_profile`

Fields emitted:
- `goal`
- `content_mode`
- `hook_aggressiveness`
- `target_duration_range`
- `variation_policy`

Determinism:
- yes, given the same `account_goal` and `health_status`

Downstream consumption:
- Script: partial but real
- Voice: partial but real
- Asset: present but not consumed
- Editor: present but not consumed

Authority level:
- advisory-to-partially-governing, not fully governing

### `fallback`

Fields come from `FallbackDecision`:
- `used`
- `mode`
- `reason`

Used today:
- yes
- included in `StrategyResult`
- emitted indirectly in event logs as `fallback_used`

Operational meaning:
- if strategy generation throws or health status is invalid, fallback is marked and a default profile is returned

## 9. Current Decision Model

The current Strategy decision model is rule-based and minimal.

Actual logic in `backend/app/creative/agents/strategy/service.py`:

1. normalize `account_goal`
2. normalize `health_status`
3. if status not in `{SAFE, CAUTION, HOLD}`:
   - return default strategy
   - mark fallback `STRATEGY_COLD_START`
4. else map status to a small fixed profile

Decision table:

`SAFE`
- `goal = account_goal or "retention"`
- `content_mode = "standard"`
- `hook_aggressiveness = "medium"`
- `target_duration_range = "8-12s"`
- `variation_policy = "low"`

`CAUTION`
- `goal = account_goal or "retention"`
- `content_mode = "conservative"`
- `hook_aggressiveness = "medium"`
- `target_duration_range = "8-12s"`
- `variation_policy = "low"`

`HOLD`
- `goal = account_goal or "retention"`
- `content_mode = "paused"`
- `hook_aggressiveness = "low"`
- `target_duration_range = "8-12s"`
- `variation_policy = "none"`

What this means in practice:
- no weighting
- no optimization
- no objective tradeoff engine
- no saturation reasoning
- no experimentation logic
- no direct use of metrics summary
- no use of recommended constraints

Most honest label:
- static profile assembly conditioned primarily by health status

## 10. Downstream Consumption

This is the most important section for judging real influence.

### Script Agent

Files:
- `backend/app/creative/agents/script/service.py`
- `backend/app/content/script_gen/models.py`
- `backend/app/content/script_gen/service.py`

What happens:
- Script Agent passes `strategy_profile` into `ScriptGenerationContext`
- the generator prompt includes:
  - strategy goal
  - strategy content mode
  - hook aggressiveness
  - target duration range

What is real:
- Strategy is not merely attached; it is injected into the prompt text used for script generation

What is not guaranteed:
- there is no separate enforcement layer proving the model obeys those fields strongly
- downstream effect depends on how the generator responds to prompt context

Strength of consumption:
- medium

Important nuance:
- `variation_policy` is not included in the prompt
- so one Strategy field exists but is not consumed here

### Voice Agent

Files:
- `backend/app/creative/agents/voice/service.py`
- `backend/app/creative/agents/voice/interpreter.py`

What happens:
- Voice interpreter directly reads `strategy_profile`
- `content_mode == "conservative"` can affect resolved style
- `target_duration_range` starting with `"8-10"` changes overall speaking rate to `0.98`

What is real:
- this is direct code consumption, not just context pass-through

What is weak:
- niche-specific branches override some strategy effects
- for `horror`, `true_crime`, and `facts`, niche often determines style before strategy does

Strength of consumption:
- medium

### Asset Selection Agent

Files:
- `backend/app/creative/agents/asset_selection/models.py`
- `backend/app/creative/agents/asset_selection/service.py`

What happens:
- `strategy_profile` is part of `AssetSelectionInput`
- `AssetSelectionInput.to_dict()` serializes it
- `AssetSelectionAgentService.select(...)` does not read it

What is real:
- profile is carried structurally

What is not real:
- no asset selection behavior changes because of strategy in current service code

Strength of consumption:
- symbolic / none

### Editor Agent

Files:
- `backend/app/creative/agents/editor/models.py`
- `backend/app/creative/agents/editor/interpreter.py`

What happens:
- `strategy_profile` is part of `EditorAgentInput`
- it is serializable and passed in
- `EditorInterpreter.interpret(...)` accepts the argument
- the function body never actually references `strategy_profile`

What is real:
- profile is structurally available to Editor

What is not real:
- edit behavior does not change because of strategy in current code

Strength of consumption:
- symbolic / none

### Overall downstream effect

Strong claim that is true:
- Strategy is propagated everywhere relevant

Strong claim that is not true:
- Strategy does not yet govern all downstream agents meaningfully

Most accurate summary:
- Script and Voice have partial real consumption
- Asset and Editor currently carry Strategy structurally but do not use it behaviorally

## 11. Learning / Trend / Health Integration

### Account Health integration

Real and strong.

Health status is the primary real Strategy input today.

Operational effect:
- `SAFE`, `CAUTION`, and `HOLD` produce distinct strategy profiles

Important boundary:
- Account Health can stop execution before generation
- so Strategy's `paused` profile for `HOLD` often does not become a meaningful downstream runtime state, because the orchestrator halts earlier when account health is `HOLD`

This means:
- `HOLD -> paused` exists in Strategy logic
- but that branch has limited practical impact in full runtime because Account Health already blocks the flow

### Learning integration

Minimal.

Real path:
- Learning insights produce `signal_summary`
- orchestrator passes that into `StrategyInput.recent_metrics_summary`

Actual Strategy behavior:
- service ignores `recent_metrics_summary`

Therefore:
- learning is structurally connected
- not strategically applied by Strategy Phase 1

### Trend integration

Absent at the Strategy service level.

Trend analysis runs before Strategy, but:
- `TrendProfile` is not passed into `StrategyInput`
- Strategy service does not consume trend data directly

Trend still reaches downstream agents directly through orchestrator, bypassing Strategy.

This is a critical architectural fact:
- the current pipeline is not "trend -> strategy -> downstream"
- it is closer to "trend and strategy both flow downstream in parallel"

## 12. Experiment / Variation / Saturation Capability

### Experiment decisions

Implemented in Strategy: no

What exists:
- experiments exist elsewhere in the pipeline
- Strategy does not choose experiments

### Variation policy

Implemented in Strategy: partially, but only as a field

What exists:
- `variation_policy` field in `StrategyProfile`
- values like `"low"` and `"none"` are produced

What does not exist:
- no enforcement of variation policy in downstream agents
- no use in Script prompt
- no use in Voice, Asset, or Editor code

Assessment:
- symbolic field, not an operational control surface

### Saturation control

Implemented: absent

No code in Strategy Phase 1:
- reads saturation state
- controls repetition
- throttles motif reuse
- adjusts novelty budget

### Novelty control

Implemented: absent

### Risk mode

Implemented: partial and weak

What exists:
- `content_mode` changes to `"conservative"` or `"paused"` based on health status

What does not exist:
- no richer risk taxonomy
- no multi-level risk budgeting
- no direct enforcement beyond downstream partial consumption

## 13. Traceability and Auditability

What exists:
- `StrategyResult` is returned in `CreativePipelineExecution`
- `CreativePack` stores `strategy_profile`
- orchestrator emits `CREATIVE/strategy_profile_generated`
- execution batches preserve strategy output

Observed artifacts:
- multiple `OUT/audit/.../events/creative_events.jsonl` files contain `CREATIVE/strategy_profile_generated`
- execution payloads contain serialized `strategy`

What the event currently records:
- `account_id`
- `goal`
- `content_mode`
- `health_status`
- `fallback_used`

What does not exist:
- no dedicated strategy trace object
- no explicit decision trace from the Strategy service
- no explanation of why one profile was chosen beyond inferred status mapping
- no record that `recent_metrics_summary` or constraints were ignored

Auditability assessment:
- moderate for confirming that a profile was generated
- low for reconstructing strategic reasoning

Note on `strategy_patch.json` artifacts:
- files named `strategy_patch.json` exist in rollout audit folders
- observed example contained only window metadata and status, not actual Strategy Agent reasoning
- these should not be treated as proof of a mature Strategy Agent audit system

## 14. Determinism and Governance

### Determinism

The Strategy service is deterministic.

Given the same:
- `account_goal`
- `health_status`

it will return the same profile every time.

There is no stochastic behavior in the Strategy service itself.

### Governance

Not implemented at baseline level.

What does not exist:
- no Strategy baseline promotion artifacts
- no Strategy freeze policy
- no Strategy version field
- no threshold/config governance layer
- no dedicated strategy monitoring policy

Most accurate status:
- deterministic prototype
- not baseline-governed

## 15. Test Surface

### Unit tests

Primary test:
- `tests/agents/strategy/test_strategy_agent_phase2_unittest.py`

What it proves:
- safe account returns expected profile
- invalid status triggers fallback default profile

What it does not prove:
- meaningful strategic usefulness
- downstream behavioral effect
- learning integration
- trend integration

### Script integration evidence

Test:
- `tests/agents/script/test_script_agent_phase2_unittest.py`

What it proves:
- Script Agent receives `strategy_profile`
- `hook_aggressiveness` is present in generation context

What it does not prove:
- that the generated script actually changes in a controlled way because of Strategy

### Voice integration evidence

Test:
- `tests/agents/voice/test_voice_interpreter_phase2_5_unittest.py`

What it proves:
- Voice interpreter accepts a strategy profile
- interpretation remains deterministic
- strategy can coexist with niche-aware voice interpretation

What it does not prove:
- broad strategic usefulness

### Orchestrator smoke coverage

Test:
- `tests/runtime/pipeline/test_phase2_block2_smoke_unittest.py`

What it proves:
- Strategy is called in safe flow
- its result is present in execution
- hold path upstream can stop pipeline before strategy becomes downstream-relevant

What it does not prove:
- strong downstream behavioral governance

### Coverage gaps

No observed tests proving:
- Asset behavior changes because of Strategy
- Editor behavior changes because of Strategy
- learning summary changes strategy output
- recommended constraints change strategy output
- trend analysis changes strategy output

Test coverage assessment:
- adequate for presence and basic integration
- weak for strategic value

## 16. Validation / Audit History

Observed evidence:
- Strategy events appear in multiple audit event logs
- execution batches contain serialized strategy results
- no dedicated Strategy full-validation gate was found
- no Strategy baseline promotion artifacts were found

What this means:
- Strategy has been exercised during broader system validations
- Strategy has not been validated as a first-class subsystem in the same way other mature agents were

No evidence found of:
- `strategy_baseline_promotion_verdict.json`
- dedicated Strategy heavy validation gate
- Strategy-specific monitoring policy

Honest conclusion:
- Strategy has runtime history
- it does not have independent baseline history

## 17. Current Strengths

Actual strengths already present:

1. Real runtime existence
- it is not aspirational only
- it runs in orchestrated executions

2. Deterministic behavior
- the service is stable and predictable

3. Clean contract surface
- `StrategyInput`
- `StrategyProfile`
- `StrategyResult`

4. Orchestrator integration
- Strategy is resolved at the right place in the pipeline
- Strategy output is persisted into `CreativePack`

5. Partial downstream influence
- Script prompt includes strategy fields
- Voice interpreter reads strategy directly

6. Fallback handling
- invalid status and internal errors degrade to a controlled default profile

## 18. Current Weaknesses / Limitations

Actual weaknesses:

1. Decision model is extremely shallow
- mostly health-status mapping

2. Hardcoded objective
- orchestrator passes `"retention"` as `account_goal`
- so objective selection is not truly live

3. Learning integration is structurally present but behaviorally absent
- `recent_metrics_summary` is ignored

4. Recommended constraints are ignored
- passed in, not used

5. No direct trend integration
- Strategy does not consume `TrendProfile`

6. Variation policy is not enforced
- field exists, runtime effect does not

7. Asset Agent does not consume strategy behaviorally

8. Editor Agent does not consume strategy behaviorally

9. Weak explainability
- no decision trace beyond status-to-profile inference

10. No governance baseline
- no freeze rule
- no versioning
- no promotion artifacts

## 19. Current Maturity Assessment

### Technical integrity
- medium to high
- code is small, clear, and deterministic

### Runtime reality
- high
- Strategy is real in runtime and integrated

### Strategic usefulness
- low to medium
- some profile values matter downstream
- but the service itself is too shallow to be called strategically strong

### Downstream influence
- medium in Script
- medium in Voice
- none to symbolic in Asset
- none to symbolic in Editor

### Explainability
- low

### Governance
- low

### Overall status
- implemented: yes
- integrated: yes
- influential: partially
- baseline-ready: no
- maturity label: integrated prototype

Most honest label:
- **runtime-real but strategically immature**

## 20. Next Correct Move

The next correct move is not to add more fields to `StrategyProfile`.

The next correct move is:

**make Strategy operationally meaningful before making it broader**

Concretely, the highest-value next step is:

1. make Strategy consume real inputs it already receives
- `recent_metrics_summary`
- `recommended_constraints`

2. pass `TrendProfile` into Strategy explicitly
- so Strategy becomes the bridge between trend context and generation posture instead of a parallel passenger

3. make at least one currently symbolic field real
- `variation_policy` is the strongest candidate

4. make Editor and/or Asset consume Strategy behaviorally
- otherwise Strategy remains underpowered in the parts of the pipeline where style and variation actually matter most

What should not be done first:
- adding many more strategic concepts without operational consumers
- writing a more elaborate Strategy contract before current fields matter

Most correct next phase framing:
- move Strategy from "profile assembly" to "profile with enforceable downstream effects"

## Appendix: Implementation Fact vs Inference vs Intended Future Role

### Implementation fact

These are proven by code:
- Strategy service exists and runs
- orchestrator calls it
- it returns `StrategyResult`
- it stores `StrategyProfile` in `CreativePack`
- Script prompt includes several strategy fields
- Voice interpreter directly uses some strategy fields
- Asset and Editor currently do not consume strategy behaviorally

### Inference from code

These are reasonable but still inferential:
- Script output may change meaningfully because strategy fields are present in the prompt
- the actual magnitude of that effect depends on LLM/provider behavior and is not strongly validated by tests

### Intended future role

This is implied by naming and architecture, but not yet implemented:
- governor of long-horizon system behavior
- objective controller
- risk/saturation/variation governor
- true bridge between learning/trends and generation behavior

That future role should not be confused with the current Phase 1 implementation.
