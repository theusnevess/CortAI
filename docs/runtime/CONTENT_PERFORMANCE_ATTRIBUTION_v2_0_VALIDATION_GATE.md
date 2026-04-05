# CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_VALIDATION_GATE

## 1. Objective
Prove that `Content Performance Attribution v2.0` is now a real, canonical, bounded subsystem rather than a loose analytical helper.

This gate must answer:
1. is `backend/app/product/attribution/` the active canonical path?
2. is `backend/app/attribution/` explicitly non-canonical for subsystem governance?
3. is the canonical contract hardened and stable?
4. is the required evidence set explicit and enforced?
5. does the write path distinguish `WRITTEN` vs `SKIPPED` honestly?
6. is experiment-aware linkage limited, explicit, and safe?
7. is unsafe inference blocked?
8. is downstream effect real but bounded?
9. are determinism and idempotency preserved?
10. is ownership preserved relative to Experiment Capability, Strategy, and the frozen core?

## 2. Scope
### Included
- `backend/app/product/attribution/`
- canonical record contract
- canonical write path
- evidence-summary behavior
- missing-metrics honesty
- experiment-aware linkage behavior
- bounded integration with `backend/app/product/strategy_learning/`
- Phase A through Phase D evidence

### Out of scope
- full multi-factor causal attribution
- strategy redesign
- experiment assignment ownership
- experiment result ownership
- QC governance
- publish governance
- core pipeline redesign
- governance decision itself

## 3. Block A: Canonical Root And Legacy Boundary
The gate must prove:
- `app.product.attribution` is the canonical subsystem root
- `app.attribution` is explicitly legacy analytical support
- docs and code do not leave canonical ownership ambiguous

## 4. Block B: Canonical Contract And Evidence Hardening
The gate must prove:
- required base fields are explicit
- optional enrichment fields are explicit
- required evidence inputs are explicit
- optional evidence inputs are explicit
- scorecard remains optional without corrupting the base record

## 5. Block C: Honest Write Path
The gate must prove:
- valid required evidence yields `WRITTEN`
- missing required metrics yields honest `SKIPPED`
- no false canonical record is written when required evidence is missing
- evidence summary reflects what was present vs absent

## 6. Block D: Safe Experiment-Aware Linkage
The gate must prove:
- experiment linkage is accepted only from explicit metadata
- explicit IDs can link to canonical assignment/result records
- missing assignment/result is represented honestly
- `creative_pack_id` alone does not authorize linkage
- no unsafe inference path is used

## 7. Block E: Determinism And Idempotency
The gate must prove:
- same evidence -> same canonical attribution record
- same `publish_id` + same payload -> idempotent persistence
- different payload for same `publish_id` -> conflict, not silent overwrite
- experiment linkage statuses remain stable under replay

## 8. Block F: Bounded Downstream Effect
The gate must prove:
- valid attribution rows can influence `strategy_learning`
- influence remains within the allowed override envelope
- missing attribution does not generate a false downstream patch
- experiment linkage presence does not mutate downstream ownership

## 9. Block G: Ownership Preservation
The gate must prove:
- attribution does not own experiment assignment
- attribution does not own experiment result recording
- attribution does not directly mutate Strategy runtime
- attribution does not affect publishability or QC authority
- the frozen core pipeline remains unopened

## 10. Required Artifacts
The gate must generate:
- `OUT/audit/content_performance_attribution_v2_0_validation/final_verdict.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/block_summary.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/decision_examples.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/execution_batch.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/metrics.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/human_review.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/event_summary.json`
- `OUT/audit/content_performance_attribution_v2_0_validation/combined_outputs.json`

## 11. Success Standard
### `GO`
Use only if:
- all required blocks pass
- canonical path is explicit
- contract/evidence behavior is explicit
- missing-metrics honesty is preserved
- experiment-aware linkage is safe
- downstream effect is real and bounded
- determinism/idempotency hold
- no ownership boundary violation is introduced

### `GO_WITH_MONITORING`
Use only if:
- all technical blocks pass
- one non-blocking operational limitation remains
- the subsystem is validation-ready but still early in production diversity

### `HOLD`
Use if any of the following happen:
- canonical ownership remains ambiguous
- missing required evidence still writes a false record
- unsafe inference is observed
- linkage invades experiment ownership
- downstream effect cannot be shown
- downstream effect exceeds the allowed envelope
- determinism/idempotency fail

## 12. Final Question
At the end of the gate, the subsystem must answer:

```json
{
  "canonical_path_active": true,
  "legacy_path_bounded": true,
  "contract_hardened": true,
  "required_evidence_explicit": true,
  "honest_written_vs_skipped": true,
  "experiment_linkage_safe": true,
  "unsafe_inference_blocked": true,
  "bounded_downstream_effect_proven": true,
  "deterministic": true,
  "ownership_preserved": true,
  "promotion_ready": false
}
```

`promotion_ready` remains `false` until the subsystem is reviewed under a dedicated governance decision with monitored operational context.
