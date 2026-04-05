# TREND_ANALYSIS_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN

## 1. Objective

The objective of `Trend Analysis Agent v2.0` is to evolve the current subsystem from:
- manual niche profile loader

into:
- evidence-driven TikTok-native trend subsystem

The v2.0 goal is not to build a perfect trend intelligence platform.
The v2.0 goal is to introduce the minimum real architecture necessary for Trend to become:
- evidence-backed
- time-aware
- provenance-aware
- validation-aware
- operationally useful
- governable

Target outcome for v2.0:
- Trend stops being just a static context file loader
- Trend becomes a runtime subsystem that assembles a `TrendProfile` from explicit evidence sources
- downstream agents continue to consume Trend causally, with strongest effect concentrated in `Strategy` and `Asset`
- the subsystem remains conservative, deterministic, and auditable

## 2. Current State

Current state in Phase 1:
- Trend loads a niche JSON file from disk
- returns `TrendProfile`
- falls back to a safe default when file loading fails
- is integrated into orchestrator runtime
- has real downstream effect in `Strategy` and `Asset`
- has no provenance, freshness, confidence, temporal memory, or dedicated gate

Current classification:
- `implemented`
- `runtime-real`
- `deterministic`
- `prototype-grade`
- `not baseline-ready`

v2.0 exists to fix the right deficits:
- evidence absence
- provenance absence
- freshness absence
- validation absence
- governance absence

v2.0 does not exist to solve every strategic intelligence problem in one iteration.

## 3. Boundary

This boundary is mandatory and must remain explicit in implementation.

### 3.1 Trend
Trend owns:
- what is happening outside
- external platform trend evidence
- niche-level trend context
- freshness and provenance of trend evidence
- temporal snapshots of trend state

Trend does not own:
- internal performance optimization
- repetition or saturation control
- final runtime directional policy
- publishability governance

### 3.2 Learning
Learning owns:
- what works for us
- internal performance evidence
- QC-linked optimization feedback
- pattern learning from our executions

Learning does not own:
- external platform trend collection
- trend freshness policy
- trend provenance governance

### 3.3 Strategy
Strategy owns:
- what to do with available context
- how to translate Health + Trend + Learning + Novelty into runtime direction

Strategy does not own:
- collecting trend evidence
- validating evidence provenance
- storing trend history snapshots

### 3.4 Novelty
Novelty owns:
- repetition control
- saturation pressure
- anti-pattern blocking

Novelty does not own:
- external trend discovery

### 3.5 Hard boundary rule
The implementation must preserve this separation:
- `Trend = external trend context`
- `Learning = internal performance truth`
- `Strategy = control layer`

Trend v2.0 must not absorb Learning, Novelty, or Strategy responsibilities.

## 4. v2.0 Scope

v2.0 is intentionally minimal and causal.

Included in scope:
- evidence source activation
- provenance fields
- confidence fields
- freshness fields
- evidence references
- validation rules
- fallback hierarchy
- temporal snapshot storage
- stronger but still conservative downstream integration
- Trend gate design and execution path

Excluded from scope:
- full autonomous trend scraping across arbitrary TikTok surfaces
- advanced ML pattern detection
- account-specific Trend models
- multi-region production rollout
- overly sophisticated confidence heuristics
- deep downstream hard enforcement in all agents

## 5. Evidence Sources

Trend v2.0 must move to explicit evidence sources.

### 5.1 Primary source: TikTok Creative Center
Status in v2.0:
- primary planned external source
- should be implemented first

Role:
- provide baseline external trend evidence
- provide platform-level trend priors by niche/category and region

Expected outputs from source adapter:
- trending hashtags
- trending sounds
- top trend categories
- category-specific directional hints
- collection metadata

Constraints:
- v2.0 should remain conservative
- collection may be scheduled, not real-time
- if automated collection is not yet available in the first code slice, the source contract must still be formalized and the collector stub must be implemented explicitly

### 5.2 Secondary source: manual curation
Status in v2.0:
- complement, not replacement

Role:
- provide structured human-curated evidence for niche nuance
- support cases where Creative Center is too broad

Expected usage:
- hand-authored evidence records, not anonymous opinion
- each curated record must carry provenance

### 5.3 Tertiary source: internal metrics
Status in v2.0:
- validation/complement source
- not a replacement for external trend evidence

Role:
- refine or reweight trend context using internal performance evidence
- must remain clearly distinguished from Learning ownership

Rule:
- Trend may consume summarized internal validation signals
- Learning remains the owner of internal performance analysis logic

### 5.4 Source policy
Initial v2.0 source policy:
- primary: `creative_center`
- secondary: `manual_curation`
- tertiary: `internal_metrics_validation`

If only one source is available:
- Trend may still operate
- confidence must reflect reduced certainty
- provenance must remain explicit

## 6. Contract Evolution

Trend v2.0 needs contract hardening.

### 6.1 `TrendProfile` v2.0 target fields
Current fields to retain:
- `niche`
- `dominant_hooks`
- `avg_duration`
- `pacing`
- `visual_style`
- `text_style`

New fields to add:
- `region: str = "US"`
- `trend_source: str`
- `confidence_scores: dict[str, float]`
- `updated_at: str`
- `valid_until: str`
- `sample_size: int`
- `evidence: list[dict[str, Any]]`
- `trend_version: str`
- `collector_version: str`

Optional v2.0 fields if implemented immediately without bloat:
- `source_mix: list[str]`
- `overall_confidence: float`

Fields that must not be added unless there is immediate runtime use:
- extra symbolic style fields
- weakly defined qualitative labels with no consumer

### 6.2 `TrendEvidenceReference`
A dedicated evidence record structure should be introduced.

Minimum fields:
- `evidence_type`
- `source`
- `reference_id`
- `reference_url`
- `captured_at`
- `region`
- `metadata`

### 6.3 `TrendAnalysisInput` v2.0
Current input is too small.

Minimum v2.0 additions:
- `niche`
- `account_id` optional
- `region`
- `allow_cached`
- `force_refresh`
- `current_time` optional for testing determinism

Important:
- topic does not need to become a first-class Trend input in v2.0 unless a concrete use case is implemented
- avoid widening the input surface without evidence-backed behavior

### 6.4 `TrendAnalysisResult` v2.0
Must contain at least:
- `trend_profile`
- `fallback`
- `validation_summary`
- `collector_trace`

### 6.5 CreativePack persistence
`CreativePack` should continue to embed full `trend_profile`.

Additionally, v2.0 should consider embedding:
- `trend_validation_summary` or equivalent if needed for audit visibility

## 7. Data Layout

v2.0 should formalize storage instead of relying on ad hoc files only.

Proposed layout:
- `backend/data/trends/current/<niche>.json`
- `backend/data/trends/history/<niche>/<timestamp>.json`
- `backend/data/trends/manual_curation/<niche>.json`
- `backend/data/trends/cache/<source>/<niche>.json`

Audit layout:
- `OUT/audit/trend_analysis/trend_snapshots/`
- `OUT/audit/trend_analysis/trend_shifts/`
- `OUT/audit/trend_analysis/validation_reports/`
- `OUT/audit/trend_analysis/gate_decisions/`
- `OUT/audit/trend_analysis/performance_tracking/`

Key operational point:
- the current default path problem must be fixed in v2.0
- Trend must have a canonical repository-resident data layout, even if population remains initially manual or semi-automated

## 8. Freshness Policy

Trend v2.0 must treat trends as expiring context.

### 8.1 Freshness windows
Initial policy:
- `creative_center`: 7 days
- `manual_curation`: 14 days
- `internal_metrics_validation`: 30 days

### 8.2 Refresh rules
Refresh required when:
- trend is stale
- trend is within 2 days of expiry
- overall confidence is below threshold
- explicit `force_refresh` is requested

### 8.3 Expiry behavior
If refresh fails:
1. try latest valid cached trend
2. try previous acceptable snapshot
3. fallback to safe default trend

### 8.4 Freshness implementation requirement
Freshness must be explicit in code, not implied.

At minimum:
- `updated_at`
- `valid_until`
- validator check against time window

## 9. Confidence Policy

Confidence is required in v2.0, but it must start simple.

### 9.1 Confidence model for v2.0
Use simple, transparent factors only:
- source quality
- sample size
- freshness
- internal agreement if available

### 9.2 Confidence granularity
Required:
- per-field confidence for key fields
- overall confidence

Minimum field set:
- `dominant_hooks`
- `avg_duration`
- `pacing`
- `visual_style`
- `text_style` only if it gains a real consumer

### 9.3 Non-goal
Do not implement opaque or pseudo-intelligent scoring too early.

Wrong v2.0 behavior:
- complex confidence math no one can explain
- hidden heuristics without provenance

Correct v2.0 behavior:
- simple scoring
- explicit rules
- auditable mapping from source quality and sample size to confidence

## 10. Validation Policy

Trend v2.0 needs validation before application.

### 10.1 Validation checks
At minimum:
- freshness check
- provenance presence
- evidence presence
- sample size floor
- confidence floor
- internal consistency check

### 10.2 Validation outputs
Validation should yield:
- `valid: bool`
- `warnings: list[str]`
- `errors: list[str]`
- `overall_confidence`

### 10.3 Acceptance rules
Suggested v2.0 policy:
- `APPROVE` when all critical checks pass
- `HOLD` when non-critical issues exist but trend is still potentially usable
- `REJECT` when provenance, evidence, or confidence fail critically

### 10.4 Critical failures
Critical failures should include:
- missing provenance
- no evidence
- stale beyond acceptable fallback window
- confidence materially below minimum

## 11. Fallback Hierarchy

Trend v2.0 must degrade gracefully.

Required fallback order:
1. current validated trend
2. latest cached validated trend
3. previous historical validated trend within fallback age threshold
4. safe default trend

Fallback must remain observable via:
- result payload
- event emission
- audit artifact

Safe default trend requirements:
- deterministic
- niche-safe when possible
- minimally conservative
- explicit fallback reason

## 12. Downstream Enforcement Strategy

Trend v2.0 should strengthen consumption selectively.

### 12.1 Strategy
This is the primary downstream target.

v2.0 should preserve and strengthen:
- hook family conditioning from `dominant_hooks`
- pacing conditioning
- duration conditioning if `avg_duration` becomes operationally trusted

Trend should remain advisory input into Strategy, not a controller that bypasses Strategy.

### 12.2 Asset
This is the second primary downstream target.

v2.0 should preserve and strengthen:
- `visual_style`
- `pacing`
- style-dependent tag generation
- motion/effects bias

### 12.3 Script
Script may continue consuming Trend more lightly in v2.0.

Rule:
- keep prompt-context influence
- do not harden into many direct branching rules unless real evidence justifies it

### 12.4 Editor
Editor may continue consuming Trend lightly in v2.0.

Rule:
- keep light stylistic conditioning
- only strengthen if there is a concrete product-level case

### 12.5 Voice
No Trend-specific hardening is required in v2.0.

## 13. Non-Goals

Trend v2.0 must explicitly avoid these mistakes:
- becoming a mega agent
- absorbing Learning responsibilities
- absorbing Novelty responsibilities
- absorbing Strategy responsibilities
- turning confidence into an opaque scoring machine
- introducing too many symbolic fields without consumers
- trying to solve full account-specific personalization immediately
- trying to reach perfection before becoming evidence-real

This is a minimum viable causal evolution, not a maximal system rewrite.

## 14. Temporal Memory

Temporal awareness should begin in v2.0 at a conservative level.

Minimum implementation:
- store trend snapshots over time
- compare latest trend to previous trend
- detect significant changes in:
  - `dominant_hooks`
  - `pacing`
  - `visual_style`
  - `avg_duration`

Output:
- `TrendShiftAnalysis`
- stored audit artifact when meaningful shift is detected

Important:
- full advanced temporal strategy adaptation is not required in initial v2.0
- but trend history storage is required so the subsystem stops being stateless

## 15. Observability

Trend v2.0 must become auditable.

### 15.1 Required runtime visibility
It must be possible to answer:
- where the trend came from
- when it was updated
- how fresh it is
- how confident it is
- which evidence supports it
- whether fallback was used

### 15.2 Required event surface
Proposed events:
- `CREATIVE/trend_collection_started`
- `CREATIVE/trend_collection_completed`
- `CREATIVE/trend_validation_approved`
- `CREATIVE/trend_validation_hold`
- `CREATIVE/trend_validation_rejected`
- `CREATIVE/trend_profile_loaded`
- `CREATIVE/trend_profile_fallback`
- `CREATIVE/trend_shift_detected`

### 15.3 Audit artifacts
Required audit artifacts for gate and certification work:
- trend snapshot files
- validation reports
- gate decision reports
- shift reports

## 16. TikTok-Native Design Rules

Trend v2.0 must remain TikTok-first.

Implications:
- evidence sources should be TikTok-specific, not generic social abstractions
- duration assumptions should remain short-form oriented
- hook, pacing, visual style, text style, sound, and format cues should be considered in TikTok-native framing
- region should be explicit because TikTok trend surfaces vary by market

Important caution:
- TikTok-native does not mean TikTok-overfit everywhere in v2.0 contract design
- it means source model and behavioral priorities must be aligned with TikTok reality

## 17. Implementation Phases

## 17.1 Phase A: Contract And Storage Hardening

Objective:
- make Trend structurally capable of evidence, provenance, freshness, and fallback hierarchy

Work:
- extend Trend contracts
- add evidence reference structure
- formalize canonical storage directories
- add temporal snapshot persistence
- fix default path issue

Deliverable:
- contracts compile
- serialization works
- backward-safe fallback path exists

## 17.2 Phase B: Evidence Source Activation

Objective:
- stop relying on manual niche loader as the sole meaningful source

Work:
- introduce Creative Center collector interface
- introduce manual curation input format
- introduce source assembly logic
- produce first hybridizable `TrendProfile`

Deliverable:
- TrendProfile can be built from explicit evidence payloads
- provenance fields are populated

## 17.3 Phase C: Validation And Fallback Governance

Objective:
- prevent low-quality trend data from silently entering runtime

Work:
- validation service
- confidence scoring service
- fallback hierarchy
- trend decision traces

Deliverable:
- validated trend output path
- reject/hold/approve semantics

## 17.4 Phase D: Downstream Hardening

Objective:
- make v2.0 causally stronger where it matters most

Work:
- strengthen `Strategy` use of validated trend data
- strengthen `Asset` use of validated trend data
- keep `Script` and `Editor` conservative unless justified

Deliverable:
- measurable downstream causal effect

## 17.5 Phase E: Gate And Promotion Readiness

Objective:
- make Trend baseline-eligible

Work:
- Trend Excellence Gate runner
- audit artifact generation
- promotion policy definition

Deliverable:
- standalone Trend validation path

## 18. Validation Path

Trend v2.0 requires its own gate path.

### 18.1 Required validation layers
- unit tests for collectors, validator, freshness, fallback
- integration tests for orchestrator + Trend + Strategy + Asset
- audit runner for Trend Excellence Gate
- controlled execution batch proving downstream influence remains coherent

### 18.2 What Trend gate must prove
- provenance is present
- freshness works
- confidence is computed and usable
- fallback hierarchy works
- downstream causal use exists
- deterministic behavior holds under same evidence input
- invalid trend evidence does not silently contaminate runtime

### 18.3 Baseline criteria
Trend v2.0 should only be baseline-promoted if:
- evidence-backed path is operational
- default path issue is resolved
- validation and fallback hierarchy work
- Strategy and Asset causal consumption are proven under v2.0 context
- audit artifacts are generated consistently

## 19. Success Criteria

Trend v2.0 should be considered successful if it achieves all of the following:
- no longer depends on manual niche file loading as sole meaningful mechanism
- emits a provenance-aware `TrendProfile`
- tracks freshness and expiry
- validates trend evidence before application
- preserves graceful degradation
- strengthens real downstream influence without absorbing other subsystems
- becomes gateable

Success does not require:
- perfect trend intelligence
- full automation across all sources
- advanced ML inference
- account-specific per-user adaptation

## 20. Risks

### Risk 1: Trend grows into a mega layer
Mitigation:
- enforce boundary rule explicitly in plan and code review

### Risk 2: confidence becomes opaque
Mitigation:
- keep initial confidence scoring simple and explicit

### Risk 3: Creative Center becomes single point of truth
Mitigation:
- maintain multi-source design from the start

### Risk 4: symbolic field inflation
Mitigation:
- require real consumer before keeping new fields like `text_style`

### Risk 5: runtime regression from source failures
Mitigation:
- implement fallback hierarchy before making Trend source logic mandatory

## 21. Next Correct Move After This Plan

After this implementation plan is written, the next correct move is:
- implement `Phase A: Contract And Storage Hardening`

Reason:
- the current blocker is structural, not sophistication
- Trend cannot become evidence-governed until contracts and storage are made real
- source activation without contract hardening would create fragile and ungoverned behavior

## Final Implementation Position

Trend v2.0 should be built as:
- minimal
- evidence-backed
- TikTok-native
- provenance-aware
- freshness-aware
- validation-aware
- conservative
- auditable

It should not be built as:
- all-knowing strategic brain
- replacement for Learning
- replacement for Strategy
- high-complexity scoring system in its first real evolution

Final one-line target:
- `Trend Analysis Agent v2.0` must turn Trend from a static file-backed context block into a governed evidence-driven TikTok trend subsystem without breaking system boundaries.
