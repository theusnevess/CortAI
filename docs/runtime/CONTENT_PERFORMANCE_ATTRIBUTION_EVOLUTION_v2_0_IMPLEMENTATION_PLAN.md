# CONTENT_PERFORMANCE_ATTRIBUTION_EVOLUTION_v2_0_IMPLEMENTATION_PLAN

## 1. Objective

The objective of `Content Performance Attribution v2.0` is to evolve the current subsystem from:
- partially real post-pipeline attribution logic

into:
- a canonical, isolated, auditable attribution subsystem with bounded downstream effect

The v2.0 goal is not to claim full causal truth.
The v2.0 goal is not to reopen the frozen creative core.
The v2.0 goal is not to absorb Experiment Capability, Strategy, QC, or publish governance.

The v2.0 goal is to make attribution:
- canonical
- contract-stable
- experiment-aware
- honest under missing evidence
- deterministic where required
- operationally useful downstream without violating subsystem ownership

Target outcome for v2.0:
- one canonical attribution path exists
- the legacy analytical path has an explicit non-owning role
- required evidence inputs are fixed
- experiment-aware fields are defined cleanly
- allowed downstream effect is explicit and bounded
- missing-metrics behavior is explicit and auditable
- the subsystem becomes ready for a dedicated validation gate

## 2. Current State

Current Phase 1 state:
- `backend/app/product/attribution/` already exists
- a canonical row can be built per `publish_id`
- schema validation exists
- append-only persistence exists
- idempotent save behavior exists
- `window_post_pipeline` already wires scorecard -> attribution -> strategy learning
- strategy learning already consumes attribution rows behaviorally

At the same time:
- `backend/app/attribution/` still exists as a parallel analytical path
- canonical ownership is not yet declared
- experiment-aware fields are not formalized on the product path
- required evidence is not yet declared as a subsystem contract
- missing-evidence honesty is partly runtime-real but not yet fully specified as subsystem policy
- validation and governance artifacts do not yet exist

Current classification:
- implemented: yes
- runtime-real: yes, in post-pipeline flow
- canonicalized: no
- governance-closed: no
- experiment-aware in canonical contract: not yet fully
- downstream effect: real but still loosely bounded at subsystem-definition level

## 3. Core Diagnosis

The core diagnosis is:

```json
{
  "content_performance_attribution_v1": {
    "real_code_exists": true,
    "post_pipeline_wiring_exists": true,
    "append_only_persistence_exists": true,
    "downstream_effect_exists": true,
    "canonical_root_frozen": false,
    "legacy_boundary_explicit": false,
    "required_evidence_fixed": false,
    "experiment_aware_contract_complete": false,
    "honesty_policy_complete": false,
    "validation_ready": false
  }
}
```

Brutally honest translation:
- the subsystem is already useful
- but its operating surface is not yet fully crystallized

The exact deficit is not absence of implementation.
The exact deficit is absence of canonicalization and operational definition.

So v2.0 must fix:
- canonical root
- boundary clarity
- contract clarity
- evidence clarity
- allowed-effect clarity
- honesty clarity

before:
- validation gate
- governance decision
- registry inclusion

## 4. Boundary

This boundary must remain explicit.

### 4.1 Content Performance Attribution owns

Content Performance Attribution owns:
- canonical outcome attribution records
- normalization of selected performance signals into a stable contract
- experiment-aware linkage fields where experiment evidence already exists
- honest representation of missing or unavailable evidence
- packaging of attribution evidence for approved downstream consumers

### 4.2 Content Performance Attribution does not own

Content Performance Attribution does not own:
- strategy policy
- strategy patch governance
- experiment assignment
- experiment result recording ownership
- publish decisions
- QC authority
- content generation
- direct mutation of frozen baseline agents

### 4.3 Relationship to Strategy Learning

Strategy Learning may consume attribution outputs.
Attribution does not own:
- patch activation policy
- strategy override policy
- rollout authority

Attribution may provide evidence.
It may not become a hidden strategy controller.

### 4.4 Relationship to Experiment Capability

Experiment Capability owns:
- assignment lifecycle
- result lifecycle
- variant governance

Attribution may consume:
- experiment identity
- variant identity
- assignment/result metadata already persisted elsewhere

Attribution must not:
- synthesize fake experiment ownership
- infer assignment that the experiment subsystem did not record
- create a parallel experiment ledger

### 4.5 Hard boundary rule

The subsystem must remain:
- post-pipeline attribution and evidence packaging

It must not become:
- a general causal optimizer
- a replacement for the experiment subsystem
- a replacement for learning governance

## 5. Canonical Root Decision

The canonical subsystem root for v2.0 must be:
- `backend/app/product/attribution/`

Why this is the correct root:
- it already has a canonical record builder
- it already has schema validation
- it already has append-only persistence
- it already sits on the product/post-pipeline path
- it already feeds a real downstream consumer

The legacy analytical path:
- `backend/app/attribution/`

must be classified as:
- supporting analytical infrastructure
not:
- the subsystem root for governance

Required v2.0 decision:
- all subsystem governance, contract definition, validation, and runtime claims should anchor on `backend/app/product/attribution/`

## 6. Legacy Boundary Policy

The boundary between the two attribution tracks must be made explicit.

### 6.1 `backend/app/product/attribution/`

This path should own:
- canonical record schema
- canonical record builder
- persistence contract
- post-pipeline attribution write path
- downstream learning-facing output

### 6.2 `backend/app/attribution/`

This path may remain for:
- exploratory analytics
- secondary summaries
- research-oriented decomposition
- experiment-aware descriptive analysis

It should not be treated as:
- the canonical contract source
- the governance root
- the required write path for v2.0 subsystem correctness

### 6.3 Required repo posture

v2.0 should make it impossible to be confused about:
- which path is canonical
- which path is optional/supporting

If both paths remain active without an explicit boundary, governance will remain ambiguous.

## 7. Required Evidence Set

This is the first core pillar of v2.0.

Attribution should not accept arbitrary evidence shape.
It should operate on a fixed required evidence set plus explicit optional enrichments.

### 7.1 Required evidence

The canonical builder must require:
- publish record
- video metrics
- window metrics

These are the minimum needed to say the subsystem has observed:
- what was published
- how it performed
- under which window context it is being evaluated

### 7.2 Conditionally required evidence

`scorecard` remains conditional.

Rule:
- if scorecard exists, attribution may consume it
- if scorecard does not exist, attribution must still behave honestly and deterministically

### 7.3 Required evidence policy

The implementation plan should enforce:
- missing publish record -> hard failure
- missing video metrics -> explicit attribution skip/failure path
- missing window metrics -> explicit attribution skip/failure path
- missing optional scorecard -> allowed, with honest reduced-evidence behavior

### 7.4 Evidence auditability

Each attribution row or attribution result wrapper should make clear:
- which evidence was present
- which evidence was missing
- whether the record is canonical-complete or reduced-evidence

This does not require exaggerated complexity.
It requires explicitness.

## 8. Canonical Contract Plan

This is the second core pillar of v2.0.

The canonical record already has a good base.
v2.0 exists to freeze the final minimum contract needed for Phase 3 validation.

### 8.1 Required base fields

The base contract should continue to require:
- `attribution_id`
- `account_id`
- `publish_id`
- `video_id`
- `job_id`
- `window_id`
- `policy_stage`
- `hook_strategy`
- `human_patch_detected`
- `views`
- `retention_3s`
- `completion_rate`
- `captured_at`
- `generated_at`

### 8.2 Allowed optional base enrichments

The following remain valid optional enrichments:
- `dominant_failure_reason`
- `effective_duration_s`
- `rare_fact_placement_s`
- `likes`
- `follows`
- `rpm`

### 8.3 Contract design rule

The contract should favor:
- stable narrow fields with strong meaning

not:
- premature giant creative ontologies

The subsystem needs a strong base contract first.
Broader decomposition can come later if it remains auditable and deterministic.

## 9. Experiment-Aware Contract Plan

This is the third core pillar of v2.0.

The subsystem must become experiment-aware without invading Experiment Capability ownership.

### 9.1 Required ownership-safe principle

Attribution may only carry experiment metadata that was already produced by the experiment subsystem or canonical runtime records.

It must not:
- infer or invent assignment identities
- decide experiment eligibility
- fabricate variant lineage

### 9.2 Recommended experiment-aware fields

Recommended additions or wrapper-level fields:
- `experiment_id`
- `variant_id`
- `assignment_id` when available
- `experiment_result_available`
- `experiment_linkage_status`

Recommended linkage status values:
- `LINKED`
- `NOT_PRESENT`
- `MISSING_ASSIGNMENT`
- `MISSING_RESULT`
- `UNSAFE_TO_INFER`

### 9.3 Experiment-aware contract rule

If experiment evidence is absent:
- attribution must say so explicitly

If experiment evidence is partially present:
- attribution must preserve the partial state honestly

If experiment evidence is fully present:
- attribution may carry linkage metadata for downstream explanation

### 9.4 Ownership preservation

Even when experiment fields are present, Attribution still does not own:
- the truth of assignment
- the truth of result recording
- the truth of experiment envelope

It only owns:
- linking existing experiment evidence to observed content outcome records

## 10. Honest Missing-Metrics Policy

This is the fourth core pillar of v2.0.

Attribution must be explicitly honest when evidence is incomplete.
Silent fabrication is unacceptable.

### 10.1 Mandatory honesty scenarios

The subsystem must define explicit behavior for:
- publish record missing
- video metrics missing
- window metrics missing
- scorecard missing
- experiment linkage missing
- malformed metadata needed for optional enrichments

### 10.2 Required behavior

Recommended policy:

- missing publish record:
  - hard error
  - no attribution record generated

- missing video metrics:
  - explicit skipped/error attribution result
  - no false normalized record

- missing window metrics:
  - explicit skipped/error attribution result
  - no false canonical-complete record

- missing scorecard:
  - allowed reduced-evidence mode
  - record remains possible

- missing experiment linkage:
  - allowed
  - explicit `experiment_linkage_status`

- malformed optional metadata:
  - optional fields degrade to `null`
  - base contract remains valid when possible

### 10.3 Honesty artifact requirement

The write path should produce enough visibility to prove:
- why attribution was written
- why attribution was skipped
- why enrichment fields were absent

This is necessary for the future validation gate.

## 11. Allowed Downstream Effect

This is the fifth core pillar of v2.0.

The subsystem must have downstream effect.
That effect must also be bounded.

### 11.1 Allowed downstream consumers

Allowed v2.0 consumers:
- `backend/app/product/strategy_learning/`
- reporting/audit layers
- future validation runners

### 11.2 Allowed downstream effect

Allowed effect:
- evidence supply to deterministic strategy-learning logic
- descriptive analysis outputs
- audit summaries

### 11.3 Disallowed downstream effect

Disallowed effect:
- direct mutation of frozen strategy runtime without approved learning interface
- direct publish blocking
- direct QC override
- direct orchestrator control
- direct experimental assignment control

### 11.4 Enforcement principle

Attribution may influence the system only through approved consuming layers.
It may not become a hidden command channel.

## 12. Determinism And Idempotency Plan

The subsystem should remain deterministic under fixed evidence.

Required v2.0 properties:
- same evidence -> same canonical attribution row
- same `publish_id` -> idempotent persistence behavior
- optional enrichment absence -> explicit stable output, not random omission
- linkage states -> stable enumerations

This is already partly true.
v2.0 must make it a declared subsystem property.

## 13. Output Surfaces

v2.0 should define the output surfaces clearly.

### 13.1 Canonical persisted row

Primary output:
- canonical attribution record persisted through `backend/app/product/attribution/`

### 13.2 Result wrapper

Recommended write-path wrapper fields:
- `status`
- `reason_code`
- `record_written`
- `evidence_summary`
- `experiment_linkage_status`

This wrapper is useful because validation should assess both:
- record correctness
- honesty of the write decision

### 13.3 Optional analytical summaries

Analytical summaries may still exist.
They should be explicitly classified as:
- non-canonical support outputs

## 14. Implementation Phases

The implementation should be executed in narrow phases.

### 14.1 Phase A: Canonicalization And Boundary Freeze

Objective:
- make the canonical subsystem root and legacy boundary explicit

Required work:
- document `backend/app/product/attribution/` as canonical root
- document `backend/app/attribution/` as supporting analytical path
- remove ambiguity in comments, docs, and runtime references where needed
- define the final ownership statement for the subsystem

Phase A success condition:
- a reader can tell immediately which path is canonical and which path is not

### 14.2 Phase B: Contract And Evidence Hardening

Objective:
- finalize the canonical contract and required evidence set

Required work:
- freeze required base fields
- formalize optional enrichments
- formalize required evidence vs optional evidence
- add explicit evidence-presence reporting in the result surface where needed
- ensure missing-evidence behavior is explicit

Phase B success condition:
- the subsystem has a stable minimum contract and a declared honesty policy

### 14.3 Phase C: Experiment-Aware Linkage Activation

Objective:
- add ownership-safe experiment-aware linkage on the canonical path

Required work:
- define safe experiment-aware fields
- wire those fields only from canonical experiment/runtime records
- add explicit linkage-state reporting
- ensure no fake experiment ownership is introduced

Phase C success condition:
- attribution can represent experiment linkage honestly without becoming the experiment subsystem

### 14.4 Phase D: Downstream Effect Hardening

Objective:
- prove that attribution has bounded but real downstream effect

Required work:
- verify strategy-learning consumption on the canonical path
- ensure allowed effect remains bounded to approved consumers
- expose enough audit visibility to show what attribution influenced downstream

Phase D success condition:
- the subsystem has real but bounded effect that can be validated later

## 15. Explicit Non-Goals

v2.0 will not:
- solve full creative causal attribution
- decompose every content factor with strong confidence
- replace experiment result recording
- redesign strategy learning broadly
- redesign the frozen creative orchestrator
- add direct governance authority over publishability
- force registry/governance inclusion before validation exists

These non-goals matter because this phase should stay executable.

## 16. Validation Readiness Criteria

The subsystem will be ready for a dedicated validation gate only after:
- canonical root is explicit
- legacy boundary is explicit
- required evidence set is fixed
- missing-metrics honesty policy is implemented
- experiment-aware fields are ownership-safe and runtime-real
- allowed downstream effect is explicit and observable
- deterministic/idempotent behavior is demonstrated

Only after that should the repo add:
- `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_VALIDATION_GATE.md`

## 17. Governance Readiness Criteria

Governance should happen only after a clean validation artifact set exists.

The governance decision should answer:
- is the canonical path operationally real
- is the honesty model reliable
- is experiment linkage clean
- is downstream effect real but bounded
- is the subsystem stable enough to freeze

Only after those answers exist should the repo add:
- subsystem governance decision
- registry classification

## 18. Immediate Next Step

The immediate next step after this plan is:
- implement `Phase A: Canonicalization And Boundary Freeze`

That is the correct first move because validation is still premature until:
- canonical ownership is fixed
- the subsystem surface is operationally defined

## 19. Final Verdict

`Content Performance Attribution v2.0` should proceed now as a Phase 3 implementation track.

The correct sequence is:
1. implementation plan
2. phased implementation
3. validation gate
4. governance decision
5. registry inclusion

Most accurate verdict:
- `approved for implementation definition`
not:
- `approved for baseline governance`
