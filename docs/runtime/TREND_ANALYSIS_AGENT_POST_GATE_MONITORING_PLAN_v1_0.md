# Trend Analysis Agent Post-Gate Monitoring Plan v1.0

## Objective
Run a short monitoring window after the Trend gate verdict:
- `GO_WITH_MONITORING`

This monitoring window exists to confirm:
- operational stability under continued use
- collector resilience on the public Creative Center surface
- validation and fallback stability
- continued causal effect into `Strategy` and `Asset`

This plan does not reopen Trend architecture.

## Scope
Included:
- Trend collection stability
- validation status stability
- fallback hierarchy pressure
- event and artifact continuity
- downstream causal proxies in `Strategy` and `Asset`

Excluded:
- redesign of Trend contracts
- Learning redesign
- Novelty redesign
- Strategy redesign
- new confidence model
- baseline promotion itself

## Monitoring Window
Recommended minimum:
- `7 days` or `20 executions`, whichever comes later

Recommended preferred window:
- `7 days` and `30 executions`

Reason:
- the gate already proved technical validity
- this window is only for stability confirmation

## Frozen Inputs
Run monitoring against the frozen surface defined in:
- `docs/runtime/TREND_ANALYSIS_AGENT_GATE_EVENT_ARTIFACT_FREEZE_v1_0.md`

Do not change event names, required fields, or artifact names during this window unless a critical incident forces it.

## Primary Metrics
Track:
- `creative_center_rate`
- `collection_completed_rate`
- `collection_failed_rate`
- `validation_status_distribution`
- `safe_default_fallback_rate`
- `strategy_fast_pacing_alignment_rate`
- `asset_visual_alignment_rate`
- `qc_approve_rate`

## Interpretation
### `creative_center_rate`
Shows how often Trend actually runs with external Creative Center-backed context instead of living only on fallback paths.

### `collection_failed_rate`
Shows operational stability of the public Creative Center collector.

### `safe_default_fallback_rate`
Shows whether Trend is collapsing too often to the lowest fallback tier.

### `strategy_fast_pacing_alignment_rate`
Proxy for continued Trend-to-Strategy causality:
- when Trend says `fast_first_3s`
- Strategy should usually reflect a stronger hook posture

### `asset_visual_alignment_rate`
Proxy for continued Trend-to-Asset causality:
- Asset visual style should continue to match Trend visual style in normal runs

## Reopen Triggers
Reopen only on material signals:
- `collection_failed_rate > 0.35`
- `safe_default_fallback_rate > 0.10`
- any `TREND_VALIDATION_REJECT_OBSERVED`
- `strategy_fast_pacing_alignment_rate < 0.80`
- `asset_visual_alignment_rate < 0.80`
- Creative Center stops being the dominant source unexpectedly

## Monitoring Runner
Use:

```powershell
python tests/run_trend_analysis_agent_post_gate_monitoring.py
```

Output artifacts:
- `OUT/audit/trend_analysis_post_gate_monitoring/monitoring_summary.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/rolling_metrics.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/regression_alerts.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/human_review.json`
- `OUT/audit/trend_analysis_post_gate_monitoring/execution_examples.json`

## Promotion Standard After Monitoring
Promote Trend to baseline only if all remain true through the short monitoring window:
- Creative Center-backed execution remains operational
- validation stays governed
- fallback hierarchy stays safe
- no material new failure pattern appears
- Strategy causal response remains visible
- Asset causal response remains visible
- public-surface limitations remain explicit, not hidden

## Final Rule
If stable:
- promote

If unstable:
- open a narrow corrective slice only

Do not reopen Trend broadly unless monitoring shows a real failure class.
