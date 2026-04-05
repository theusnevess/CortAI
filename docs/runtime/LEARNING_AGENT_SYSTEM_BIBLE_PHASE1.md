# Learning Agent System Bible Phase 1

## 1. Agent Overview

Architecturally, the Learning Agent is supposed to be the subsystem that reads prior publishing/performance evidence and converts it into reusable guidance for downstream generation.

What it actually is in Phase 1:
- a deterministic file-reader plus heuristic summarizer
- a small rule-based suggestion generator
- a producer of `LearningInsights`
- a runtime-real component that runs in the orchestrator and persists/propagates output

What it is not today:
- not a model that updates itself
- not a feedback loop controller
- not a temporal optimizer with memory beyond reading local history files each run
- not a subsystem that directly governs downstream behavior strongly

Direct classification:
- stateless or stateful: **operationally stateless**
- reactive or adaptive: **reactive**
- passive or active: **passive**

Why:
- it does not keep internal state between calls
- it reads external files on each invocation
- it emits guidance but has no enforcement authority
- it does not mutate downstream policy directly

Most honest Phase 1 label:
- **runtime-real heuristic summarizer, not a true learning loop**

## 2. Current Role In The Pipeline

The user-supplied conceptual chain `Trend -> Learning -> Strategy -> Script -> Voice -> Asset -> Editor -> QC` is directionally correct, but the current runtime is more precise than that.

Actual runtime order in `backend/app/creative/orchestrator/service.py`:
1. `Account Health`
2. `Trend Analysis`
3. `Learning`
4. `Novelty`
5. `Strategy`
6. `Experiment Capability`
7. `Script`
8. `Voice`
9. `Asset Selection`
10. `Editor`
11. content pipeline render
12. `QC`

Learning sits:
- after `Trend Analysis`
- before `Novelty`, `Strategy`, and `Experiment`
- upstream of all generation agents indirectly through propagated context

What Learning outputs:
- `LearningAgentResult`
- containing:
  - `learning_insights: LearningInsights`
  - `fallback: FallbackDecision`

Who consumes it in code:
- `Strategy Agent`
  - not the full object
  - only `learning_result.learning_insights.signal_summary`
- `Script Agent`
  - receives full `learning_insights`
- `Experiment Capability`
  - receives full `learning_insights`, but current implementation does not use it behaviorally
- `CreativePack`
  - stores full `learning_insights`

Who does not consume it directly:
- `Voice Agent`
- `Asset Agent`
- `Editor Agent`
- `QC Agent`

Important runtime fact:
- Learning is real in runtime
- its output is stored in `CreativePack`
- but its behavioral influence is uneven and mostly weak

## 3. Input Contract Analysis

File:
- `backend/app/creative/agents/learning/models.py`

`LearningAgentInput` fields:
- `account_id`
- `publish_records_path`
- `video_metrics_path`
- `analysis_dir`
- `output_path`

The agent does not receive richer in-memory runtime structures such as:
- `TrendProfile`
- full `StrategyProfile`
- experiment results
- prior `QC` decisions
- batch memory
- novelty state

### Input usage table

| Input | Present | Used | Effect |
|------|--------|------|--------|
| `account_id` | yes | yes | filters publish and metrics rows by account |
| `publish_records_path` | yes | yes | loads publish history count |
| `video_metrics_path` | yes | yes | loads views, completion, duration aggregates |
| `analysis_dir` | yes | yes | loads `hook_performance_summary.json` |
| `output_path` | yes | yes | persists serialized `LearningInsights` |
| publish history rows | yes | partial | only count is used materially |
| video metrics rows | yes | partial | only simple averages are used |
| hook performance summary | yes | partial | only first hook entry is used |
| experiment results | no | no | none |
| QC outcomes | no | no | none |
| trend context | no | no | none |
| downstream performance attribution | no | no | none |

### What the agent actually reads

From `backend/app/creative/agents/learning/service.py`:
- `publish_records.jsonl`
- `video_metrics.jsonl`
- `hook_performance_summary.json`

### What is ignored structurally or behaviorally

Brutally honest:
- no direct experiment input exists
- no QC feedback input exists
- no trend input exists
- no topic-level or niche-level adaptation input exists
- no memory window exists inside the contract
- no temporal weighting exists

## 4. Output Contract - `LearningInsights`

File:
- `backend/app/creative/contracts/creative_pack.py`

`LearningInsights` fields:
- `recommended_hook_type`
- `target_duration_range`
- `preferred_visual_style`
- `preferred_voice_style`
- `saturation_signal`
- `recommendations`
- `signal_summary`

### Output field table

| Field | Populated | Source | Downstream Used | Real Effect |
|------|----------|--------|----------------|-------------|
| `recommended_hook_type` | yes | first hook entry from `hook_performance_summary.json`, else default | Script prompt | weak |
| `target_duration_range` | yes | average metric duration bucket | Strategy indirectly via `signal_summary`, stored in pack, not used directly elsewhere | weak |
| `preferred_visual_style` | yes | hardcoded from average completion threshold | Script prompt only | weak |
| `preferred_voice_style` | yes | hardcoded from average views threshold | Script prompt only | weak |
| `saturation_signal` | yes | publish row count threshold | stored in pack, not consumed behaviorally downstream | none |
| `recommendations` | yes | deterministic strings built from computed values | Script prompt, pack persistence | weak |
| `signal_summary` | yes | counts + averages | Strategy input via `recent_metrics_summary` | medium |

### Actual population logic

From `backend/app/creative/agents/learning/service.py`:
- `recommended_hook_type`
  - first usable hook field from `hook_summary["hooks"][0]`
  - keys checked in order:
    - `hook_style`
    - `hook`
    - `label`
    - `pattern`
  - fallback: `"question"`
- `target_duration_range`
  - `"8-12s"` if average duration `<= 12` or missing
  - `"35-45s"` if average duration `<= 45`
  - `"45-60s"` otherwise
- `preferred_visual_style`
  - `"dark_backgrounds"` if average completion `>= 0.4`
  - otherwise `"phase1_baseline"`
- `preferred_voice_style`
  - `"calm_dark"` if average views `>= 150`
  - otherwise `"phase1_baseline"`
- `saturation_signal`
  - `"elevated"` if account publish count `>= 5`
  - otherwise `"baseline"`
- `recommendations`
  - always includes:
    - `prefer_hook_type:<hook>`
    - `target_duration_range:<bucket>`
  - conditionally includes:
    - `prefer_visual_style:<style>`
    - `reduce_format_repetition`
- `signal_summary`
  - `publish_count`
  - `metrics_count`
  - `avg_views`
  - `avg_completion_rate`
  - `avg_duration_s`

### Real contract assessment

Strong claim that is true:
- the contract is clean, serializable, and persisted

Strong claim that is not true:
- most fields do not have strong downstream enforcement

Most accurate summary:
- `signal_summary` is the most operational field
- most of the rest are advisory metadata

## 5. Internal Decision Logic

File:
- `backend/app/creative/agents/learning/service.py`

The decision model is:
- rule-based
- deterministic
- file-backed
- low-dimensional

Exact internal flow:
1. read publish records JSONL
2. read video metrics JSONL
3. read `hook_performance_summary.json`
4. filter publish/metrics rows by `account_id`
5. if all three are empty:
   - return fallback
6. otherwise:
   - resolve one hook type from first hook summary entry
   - compute average duration
   - compute average completion
   - compute average views
   - map them into style/duration heuristics
   - derive `saturation_signal` from publish count threshold
   - build recommendation strings
   - emit `LearningInsights`

What it does not do:
- no model fitting
- no online update policy
- no reward function
- no attribution by video type
- no per-topic optimization
- no performance ranking of competing patterns
- no experiment result learning
- no memory decay
- no batch-level saturation reasoning

Direct answer:
- does it actually learn? **No**
- what is it today? **a static suggestion generator built from external files**

More precise description:
- it reads historical files
- it computes coarse aggregates
- it emits heuristics
- but it does not implement a real learning loop

## 6. Fallback Behavior

Fallback is triggered when:
- an exception occurs in `generate(...)`
- or all three evidence sources are effectively empty for the account:
  - no account publish rows
  - no account metric rows
  - no hook summary

Fallback output:
- `recommended_hook_type = "question"`
- `target_duration_range = "8-12s"`
- `preferred_visual_style = "phase1_baseline"`
- `preferred_voice_style = "phase1_baseline"`
- `saturation_signal = "baseline"`
- `recommendations = ["fallback_default"]`
- `signal_summary = {"publish_count": 0, "metrics_count": 0}`
- fallback decision:
  - `used = true`
  - `mode = SAFE_DEFAULT`
  - `reason = LEARNING_INSIGHTS_FALLBACK`

Tests:
- `tests/test_learning_agent_phase2_unittest.py`
  - proves synthetic non-fallback path exists
  - proves missing-history fallback exists

Observed runtime artifacts:
- sampled execution outputs in:
  - `OUT/manual_pipeline_batch_3_run/run_1/execution_outputs.json`
  - `OUT/manual_pipeline_real_video_verified/execution_outputs.json`
  - `OUT/manual_pipeline_payoff_specificity_battery/run_1/execution_outputs.json`
  all show:
  - `fallback.used = true`
  - `reason = LEARNING_INSIGHTS_FALLBACK`
- event logs in:
  - `OUT/events/events.jsonl`
  - `OUT/events/test_qc_governor.jsonl`
  - multiple `OUT/audit/.../events/creative_events.jsonl`
  repeatedly show `CREATIVE/learning_insights_fallback`

Direct answer:
- is fallback the dominant path? **In observed runtime artifacts, yes**

Important nuance:
- code supports a non-fallback path
- but runtime evidence sampled here shows fallback is frequent enough to be treated as the dominant observed operational path

## 7. Downstream Consumption Analysis

### 7.1 Strategy Agent

Files:
- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/agents/strategy/service.py`

What happens:
- orchestrator does **not** pass full `LearningInsights` into `Strategy`
- it passes only:
  - `learning_result.learning_insights.signal_summary`
  into `StrategyInput.recent_metrics_summary`

What Strategy actually uses:
- `avg_completion_rate`
- `avg_views`
- `publish_count`
- `metrics_count`

Real effects in Strategy:
- low completion can raise `hook_aggressiveness`
- publish count can raise `variation_policy`
- low views can force `content_mode = conservative`

Important boundary:
- this is not full Learning consumption
- this is reduced consumption of one subfield

Assessment:
- receives Learning? **yes, partially**
- uses it? **yes**
- effect level: **medium**

### 7.2 Script Agent

Files:
- `backend/app/creative/agents/script/service.py`
- `backend/app/content/script_gen/models.py`
- `backend/app/content/script_gen/service.py`

What happens:
- `ScriptAgentInput` includes full `learning_insights`
- `ScriptAgentService.generate(...)` passes it into `ScriptGenerationContext`
- prompt text explicitly includes:
  - `Learning recommendations`
  - `Recommended hook type`
  - `Preferred voice style`

What is not included in prompt:
- `preferred_visual_style` is not explicitly named in the prompt text
- `saturation_signal` is not explicitly named in prompt text
- `signal_summary` is not explicitly named in prompt text

What is proven:
- `tests/test_script_agent_phase2_unittest.py` proves the context receives `learning_insights`
- prompt builder in `backend/app/content/script_gen/service.py` reads some learning fields directly

What is not proven:
- no strong deterministic proof that generated output changes materially because of Learning

Assessment:
- receives Learning? **yes**
- uses it? **yes, weakly**
- effect level: **low**

### 7.3 Voice Agent

Files:
- `backend/app/creative/agents/voice/interpreter.py`

What happens:
- Voice interpreter signature only accepts:
  - `niche`
  - `script_plan`
  - `strategy_profile`
- it does not receive `learning_insights`

Assessment:
- receives Learning? **no**
- uses it? **no**
- effect level: **none**

### 7.4 Asset Agent

Files:
- `backend/app/creative/agents/asset_selection/service.py`

What happens:
- `AssetSelectionInput` receives:
  - `niche`
  - `topic`
  - `strategy_profile`
  - `trend_profile`
  - `script_plan`
- it does not receive `learning_insights`

Assessment:
- receives Learning? **no**
- uses it? **no**
- effect level: **none**

### 7.5 Editor Agent

Files:
- `backend/app/creative/agents/editor/interpreter.py`

What happens:
- Editor interpreter receives:
  - `niche`
  - `topic`
  - `script_plan`
  - `voice_plan`
  - `asset_plan`
  - `strategy_profile`
  - `trend_profile`
- it does not receive `learning_insights`

Assessment:
- receives Learning? **no**
- uses it? **no**
- effect level: **none**

### Downstream table

| Agent | Receives | Uses | Effect Level |
|------|--------|------|-------------|
| Strategy | yes, partial (`signal_summary` only) | yes | medium |
| Script | yes | yes, weakly via prompt context | low |
| Voice | no | no | none |
| Asset | no | no | none |
| Editor | no | no | none |

Additional runtime consumer worth noting:
- `ExperimentCapability`
  - receives full `learning_insights`
  - current implementation ignores them behaviorally

## 8. Causality Assessment

Direct question:
- does Learning Agent change system behavior?

Answer:
- **PARTIAL (weak influence)**

Why not `NO`:
- `signal_summary` materially changes `Strategy` output
- `learning_insights` are injected into `Script` prompt context

Why not `YES` in a strong sense:
- most fields do not have direct behavioral enforcement
- no direct consumption in `Voice`, `Asset`, or `Editor`
- runtime often falls back, which collapses Learning into default metadata

Concrete evidence of causality:
1. `backend/app/creative/orchestrator/service.py`
   - passes `learning_result.learning_insights.signal_summary` to `StrategyInput.recent_metrics_summary`
2. `backend/app/creative/agents/strategy/service.py`
   - reads metrics keys and changes:
     - `hook_aggressiveness`
     - `variation_policy`
     - `content_mode`
3. `backend/app/creative/agents/script/service.py`
   - passes full `learning_insights` into script generation context
4. `backend/app/content/script_gen/service.py`
   - prompt includes selected learning fields

Concrete evidence of weak or absent causality:
1. `VoiceInterpreter` has no learning input
2. `AssetSelectionAgentService` has no learning input
3. `EditorInterpreter` has no learning input
4. most observed runtime artifacts use fallback Learning output

Most honest label:
- **weakly causal**

## 9. Limitations (Brutally Honest)

Real limitations:

1. It does not actually learn
- no training loop
- no updating policy
- no model adaptation

2. Fallback appears dominant in observed runtime
- many runtime traces show `LEARNING_INSIGHTS_FALLBACK`

3. It only reads three local evidence sources
- publish records
- video metrics
- hook summary

4. It uses shallow aggregates only
- counts
- simple averages
- first hook summary entry

5. No temporal awareness
- no recency weighting
- no memory window
- no decay

6. No experiment learning
- experiment results are not consumed

7. No QC learning
- no use of hold/reject outcomes

8. No trend integration
- trend never enters Learning

9. No topic-level adaptation
- account-level aggregates only

10. No causal attribution
- cannot tell which prior pattern caused which outcome

11. Most output fields are advisory only
- strong downstream enforcement is missing

12. `preferred_visual_style` is mostly decorative
- generated, persisted, prompt-visible
- but not consumed by visual runtime systems

13. `preferred_voice_style` is only weak prompt context
- not consumed by Voice interpreter

14. `saturation_signal` does not drive system-level saturation control
- actual saturation/novelty control now lives elsewhere

15. `recommendations` are string tags, not executable policy
- they are not parsed into a downstream rule engine

16. Learning is not the owner of optimization
- today it is an evidence summarizer feeding other components

## 10. Architectural Gap

| Capability | Phase 1 | Expected |
|----------|--------|----------|
| Metric-driven adaptation | partial | yes |
| Experiment learning | no | yes |
| Trend integration | no | yes |
| Temporal memory | no | yes |
| Recency weighting | no | yes |
| QC feedback integration | no | yes |
| Topic-level optimization | no | yes |
| Niche-level optimization | no | yes |
| Saturation intelligence | no | yes |
| Causal attribution of wins/losses | no | yes |
| Direct downstream visual influence | no | yes |
| Direct downstream voice influence | no | yes |
| Strong script influence | weak | yes |
| Runtime non-fallback dominance | no | yes |

Most important gap:
- the subsystem summarizes history, but it does not close the loop on performance

## 11. Verdict

```json
{
  "status": "weakly_causal",
  "runtime_real": true,
  "influential": "low",
  "baseline_ready": false,
  "main_gap": "lack_of_real_learning_loop"
}
```

Interpretation:
- `runtime_real`: yes
- `decorative`: no, because `signal_summary` affects Strategy and some fields reach Script prompt
- `strongly causal`: no, because enforcement is sparse and fallback is common
- `baseline_ready`: no, because this is not yet a true optimization subsystem

Most honest one-line label:
- **runtime-real but optimization-weak**

## 12. Next Step (No Implementation)

What must be activated:
- real use of non-fallback data in runtime
- stronger downstream consumption of Learning output
- closed-loop use of outcomes, not just simple history averages
- explicit distinction between reusable evidence and executable policy

What must not be rebuilt first:
- do not redesign the whole contract before current fields matter more
- do not add large ontology growth before stronger consumers exist
- do not confuse saturation/novelty ownership with Learning ownership

What should remain untouched for now:
- the current compact `LearningInsights` contract shape is good enough for diagnosis
- orchestrator placement is directionally correct
- persistence and propagation paths are already real

Most correct Phase 1 conclusion:
- the Learning Agent exists
- it runs
- it emits valid guidance
- but it still behaves more like a heuristic evidence summarizer than a true optimization layer
