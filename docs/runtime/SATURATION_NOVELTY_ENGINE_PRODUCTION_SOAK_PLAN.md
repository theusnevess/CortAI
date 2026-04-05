# Production Soak Plan

## Objective
Validate `SATURATION_NOVELTY_ENGINE_v1_0` under real production-like operation without reopening implementation.

## Scope
This soak covers only monitoring of the frozen baseline:
- `Strategy v2`
- `Script v2`
- `Asset v2`
- `QC v2`
- `SATURATION_NOVELTY_ENGINE_v1_0`

It does not include:
- new novelty logic
- new strategy fields
- editor novelty expansion
- experiment-control expansion
- architectural refactors

## Operational Rule
`if STABLE -> do not touch`

## Soak Window
Recommended minimum:
- `7 days` or `100 approved videos`, whichever comes later

Recommended preferred window:
- `14 days` or `250 approved videos`, whichever comes later

## Monitoring Metrics
Track at batch and rolling-window level.

Primary metrics:
- `structural_repetition_rate`
- `visual_repetition_rate`
- `diversity_index`
- `approve_rate`
- `average_overall_score`
- `qc_hold_rate`
- `qc_reject_rate`

Secondary metrics:
- `novelty_pressure_level_distribution`
- `variation_policy_distribution`
- `blocked_payoff_structures_frequency`
- `blocked_visual_payoff_categories_frequency`

## Baseline Reference
Use the promoted full-gate after-values as the initial baseline reference.

Reference values:
- `structural_repetition_rate = 0.6`
- `visual_repetition_rate = 0.6`
- `diversity_index = 0.4`
- `approve_rate = 1.0`
- `average_overall_score = 0.9095`

## Rolling Windows
Use two windows:
- short window: `last 20 approved videos`
- medium window: `last 100 approved videos`

Reason:
- the short window catches fast repetition drift
- the medium window catches slow saturation drift

## Success Criteria
The soak is successful if all of the following remain true:
- structural repetition does not drift materially above baseline
- visual repetition does not drift materially above baseline
- diversity does not drift materially below baseline
- approve rate does not materially collapse
- average overall QC score does not materially collapse
- novelty pressure still escalates when repeated approved patterns accumulate

## Reopen Triggers
Reopen the subsystem only if one or more of these are observed:
- `structural_repetition_rate > baseline + 0.1`
- `visual_repetition_rate > baseline + 0.1`
- `diversity_index < baseline - 0.1`
- `approve_rate < baseline - 0.2`
- `average_overall_score < baseline - 0.08`
- repeated approved batches stop causing novelty escalation
- blocked payoff structures stop changing Script output
- blocked visual payoff families stop changing Asset output

## Reopen Thresholds
Use explicit thresholds to avoid noise-driven reopens.

```json
{
  "reopen_thresholds": {
    "structural_repetition_rate_increase": 0.1,
    "visual_repetition_rate_increase": 0.1,
    "diversity_index_drop": 0.1,
    "approve_rate_drop": 0.05,
    "average_overall_score_drop": 0.05
  }
}
```

Interpretation:
- reopen only on material drift, not small variance
- keep the threshold policy fixed during the soak window
- do not override thresholds with intuition unless a separate incident is confirmed

## Incident Handling
If a regression is detected:
1. freeze deployment changes around the subsystem
2. capture a reproducible batch
3. compare against baseline gate artifacts
4. classify the issue as one of:
- novelty memory failure
- strategy enforcement failure
- script enforcement failure
- asset enforcement failure
- unrelated pipeline/environment failure

Do not patch immediately without a reproduced failure class.

## Governance Notes
Keep the following incident in the soak record:
- `backend/app/assets/catalog.json` corruption
- backup created
- rebuild completed
- treated as repaired infrastructure incident, not engine instability

## Output Artifacts
Recommended soak artifacts:
- `OUT/audit/saturation_novelty_engine_production_soak/soak_summary.json`
- `OUT/audit/saturation_novelty_engine_production_soak/rolling_metrics.json`
- `OUT/audit/saturation_novelty_engine_production_soak/regression_alerts.json`
- `OUT/audit/saturation_novelty_engine_production_soak/human_review.json`

## Exit Conditions
At the end of soak:
- if stable: keep baseline frozen
- if regression exists: open targeted correction only
- if behavior is stable but limited: defer expansion to next planned phase
