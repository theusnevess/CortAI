---
artifact_id: cortai_asset_reuse_and_signature_collision_reduction_plan
artifact_name: CortAI Asset Reuse And Signature Collision Reduction Plan
artifact_type: asset_reuse_and_signature_collision_reduction_plan
system: CortAI
date: 2026-05-11
lane: Video Quality Tuning
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

plan_mode: documentation_only_collision_reduction_plan
reviewed_authorization_review: CortAI Asset Reuse And Signature Collision Reduction Authorization Review
collision_reduction_plan_defined: true
preferred_strategy: bounded_alternate_asset_selection_before_exception

patch_authorized: false
test_execution_authorized: false
docker_execution_authorized: false
external_calls_authorized: false
credential_access_authorized: false
secret_value_access_authorized: false
production_ready: false
---

# CortAI Asset Reuse And Signature Collision Reduction Plan

## 1. Purpose

This artifact defines the documentation-only plan for reducing asset reuse and runtime signature collisions.

It answers where `ASSET_RUNTIME_REPEATED_SIGNATURE` is emitted, how runtime signatures are generated, how signature tracking is scoped, how the reset flag behaves, and how future validation should prove collision reduction. It does not authorize implementation, patching, tests, Docker execution, runtime integration, external calls, credential access, real publishing, or production readiness.

## 2. Current Quality Gate State

```yaml
current_quality_gate_state:
  closed_quality_gates:
    - local_TTS_quality_gate
    - script_generation_quality_gate
    - experiment_assignment_and_result_recording_quality_gate

  active_quality_lane:
    id: reduce_asset_reuse_and_signature_collisions
    status: planning

  separate_open_lane:
    id: decide_catalog_json_runtime_mutation_policy
    status: separate_open_lane
```

## 3. Root Cause Analysis

```yaml
root_cause_analysis:
  where_ASSET_RUNTIME_REPEATED_SIGNATURE_is_emitted:
    primary_raise_site:
      file: backend/app/runtime/asset_router.py
      function: _validate_or_rebuild_runtime_signature
      behavior:
        - builds_requested_case_pack_from_resolved_asset_plan
        - resolves_catalog_entries_for_hook_setup_payoff
        - calls_AssetSelector_validate_and_register_video_signature
        - raises_RuntimeError_with_error_code_when_validation_returns_false

    policy_source:
      file: backend/app/runtime/asset_selector.py
      function: _signature_policy_violation
      exact_code: ASSET_RUNTIME_REPEATED_SIGNATURE
      behavior:
        - compares_new_solution_signature_against_prior_signatures_for_same_batch_key
        - returns_ASSET_RUNTIME_REPEATED_SIGNATURE_when_similarity_is_greater_than_0_8

  how_runtime_signature_keys_are_generated:
    signature_fields:
      - hook_family
      - setup_family
      - payoff_family
      - progression_type
      - evidence_pattern
      - dominant_family

    signature_generation:
      file: backend/app/runtime/asset_selector.py
      function: _solution_signature
      input_entries:
        - hook_candidate
        - setup_candidate
        - payoff_candidate
      derived_from:
        - catalog_entry_family
        - sequence_bucket
        - sequence_escalation_state
        - dominant_family_counter

    similarity_rule:
      file: backend/app/runtime/asset_selector.py
      function: _signature_similarity
      compared_fields:
        - hook_family
        - setup_family
        - payoff_family
        - progression_type
        - evidence_pattern
      repeated_threshold: greater_than_0_8

  whether_signature_tracking_scope_is_global_per_batch_or_per_run:
    current_scope: process_global_per_batch_key
    state_holder:
      file: backend/app/runtime/asset_selector.py
      classvars:
        - _global_video_signatures
        - _global_failed_sequences_prevented
    batch_key_source:
      file: backend/app/runtime/asset_selector.py
      function: _signature_batch_key
      derived_from: requested_case_pack
      fallback_scope: solution:global_when_no_case_specific_marker_exists
    interpretation:
      - signature_memory_crosses_individual_runs_inside_same_python_process
      - tracking_is_not_reset_per_run_by_default
      - multiple_same_niche_or_similar_case_pack_runs_can_collide

  whether_signature_reset_behavior_masks_or_isolates_collisions:
    reset_location:
      file: tests/validation/manual/run_manual_pipeline_batch_10.py
      env_flag: CORTAI_MANUAL_BATCH_RESET_ASSET_SIGNATURES_PER_RUN
      behavior:
        - clears_AssetSelector_global_video_signatures
        - clears_AssetSelector_global_failed_sequences_prevented
    default_behavior:
      - reset_on_niche_change_only
      - no_reset_between_runs_in_same_niche_unless_flag_enabled
    interpretation:
      - reset_per_run_is_valid_for_isolating_non_asset_quality_gates
      - reset_per_run_masks_batch_level_collision_pressure
      - collision_reduction_lane_must_validate_without_reset_per_run_or_must_define_a_deliberate_scope_policy

  whether_asset_pool_diversity_is_insufficient:
    current_evidence:
      - true_crime_same_niche_sequence_triggered_ASSET_RUNTIME_REPEATED_SIGNATURE_in_preliminary_batch
      - repeated_signature_occurred_after_several_successful_runs
      - validated_experiment_batch_passed_only_when_existing_reset_flag_is_enabled
    likely_contributors:
      - candidate_pool_can_converge_on_same_families_for_similar_documentary_topics
      - signature_policy_raises_exception_after_selection_instead_of_requesting_alternate_sequence
      - batch_key_may_collapse_similar_requests_into_same_solution_memory
      - diversity_guard_is_evaluative_but_not_currently_a_bounded_rebuild_loop_at_router_boundary
```

## 4. Collision Reduction Strategy

```yaml
collision_reduction_strategy:
  selected_strategy: bounded_alternate_asset_selection_before_exception

  strategy_components:
    alternate_asset_selection_before_exception:
      goal:
        - try_alternate_hook_setup_payoff_sequence_when_signature_policy_rejects_current_sequence
        - avoid_immediate_RuntimeError_for_recoverable_collision
      constraints:
        - bounded_retry_count
        - deterministic_retry_seeds
        - no_random_unbounded_search
        - no_external_asset_fetch
        - preserve_runtime_eligible_source_filtering

    bounded_signature_retry_strategy:
      proposed_model:
        max_signature_retries: 2_to_3
        retry_inputs:
          - previous_failed_signature_code
          - already_used_paths
          - requested_case_pack
          - segment_selection_requests
        failure_after_retries:
          - raise_original_signature_error_or_structured_collision_error
          - include_failure_code_in_trace

    runtime_signature_scope_definition:
      recommended_scope: per_controlled_batch_key_not_per_individual_run
      rationale:
        - per_run_reset_hides_batch_repetition
        - process_global_without_batch_limits_can_be_too_broad
        - batch_key_scoping_preserves_auditable_diversity_pressure
      future_question:
        - whether_manual_batch_should_expose_explicit_batch_signature_scope_id

    asset_pool_diversity_requirements:
      required:
        - enough_runtime_eligible_assets_per_common_case_pack
        - no_single_family_dominates_same_batch_key
        - payoff_assets_must_not_repeat_same_evidence_pattern_too_often
        - setup_and_payoff_should_add_distinct_evidence_state_when_possible

    deterministic_vs_random_selection_tradeoff:
      deterministic_preferred: true
      deterministic_benefits:
        - reproducible_batches
        - auditable_failures
        - stable_video_outputs_for_review
      random_selection_rejected_for_current_lane: true
      random_selection_risks:
        - non_reproducible_failures
        - harder_auditability
        - possible_hidden_regression
```

## 5. Strategy Options Considered

```yaml
strategy_options_considered:
  option_1:
    name: reset_signatures_per_run
    accepted: false
    reason:
      - masks_batch_level_collision_pressure
      - useful_for_isolating_other_gates_but_not_for_closing_asset_collision_lane

  option_2:
    name: relax_signature_similarity_threshold
    accepted: false
    reason:
      - may_hide_real_visual_repetition
      - weakens_diversity_guard_without_improving_selection

  option_3:
    name: bounded_alternate_asset_selection_before_exception
    accepted: true
    reason:
      - preserves_strict_signature_policy
      - improves_recovery_from_recoverable_collisions
      - maintains_deterministic_and_auditable_selection

  option_4:
    name: expand_or_rebalance_asset_catalog
    accepted: future_candidate
    reason:
      - may_be_needed_if_candidate_pool_is_insufficient
      - requires_separate_catalog_asset_quality_scope_if_new_assets_are_added

  option_5:
    name: external_asset_fetch
    accepted: false
    reason:
      - external_calls_not_authorized
      - asset_acquisition_boundary_not_open
```

## 6. Future Patch Candidate Scope

```yaml
future_patch_candidate_scope:
  primary_candidate_files:
    - backend/app/runtime/asset_router.py
    - backend/app/runtime/asset_selector.py

  secondary_candidate_files_if_needed:
    - backend/app/creative/agents/asset_selection/service.py
    - tests/validation/manual/run_manual_pipeline_batch_10.py

  read_only_or_separate_lane:
    - backend/app/assets/catalog.json

  explicit_limits:
    - no_patch_scope_is_authorized_by_this_plan
    - exact_patch_scope_requires_future_execution_authorization
    - backend_app_assets_catalog_json_mutation_policy_remains_separate
    - new_asset_addition_requires_separate_scope_if_needed
```

## 7. Future Validation Targets

```yaml
future_validation_targets:
  primary_targets:
    - no_ASSET_RUNTIME_REPEATED_SIGNATURE_in_controlled_10_run_batch
    - asset_reuse_ratio_below_defined_threshold
    - unique_visual_signature_count_tracking
    - preservation_of_existing_closed_quality_gates

  quantitative_targets_candidate:
    controlled_batch_size: 10
    failed_runs: 0
    valid_video_count: 10
    publishable_count: 10
    asset_runtime_repeated_signature_count: 0
    repeated_signature_rate_max: 0.2
    solution_uniqueness_rate_min: 0.8
    dominant_family_share_max: 0.5

  preserved_quality_gates_required:
    local_TTS_quality_gate:
      piper_executed_count: 10
      silent_fallback_count: 0
      audio_non_silent_count: 10

    script_generation_quality_gate:
      local_structured_script_count: 10
      script_fallback_count: 0

    experiment_assignment_and_result_recording_quality_gate:
      experiment_assignment_count: 10
      experiment_result_recording_count: 10

  batch_mode_requirement:
    - validation_should_include_batch_without_CORTAI_MANUAL_BATCH_RESET_ASSET_SIGNATURES_PER_RUN_when_closing_collision_lane
    - optional_isolation_batch_with_reset_flag_may_be_used_only_as_comparison
```

## 8. Future Validation Strategy

```yaml
future_validation_strategy:
  static_validation_candidates:
    - git_diff_check
    - py_compile_changed_python_files
    - scan_for_external_call_authority_regression
    - scan_for_credential_or_secret_value_regression

  targeted_validation_candidates:
    - AssetSelector_signature_similarity_detects_exact_repeat
    - AssetSelector_signature_metrics_reports_repeated_rate_and_uniqueness
    - AssetRouter_or_selection_boundary_attempts_bounded_alternate_before_exception
    - bounded_retry_stops_after_configured_limit
    - failed_collision_trace_is_recorded_when_retries_exhausted

  controlled_batch_validation_candidates:
    - run_10_video_batch_without_per_run_signature_reset
    - confirm_no_ASSET_RUNTIME_REPEATED_SIGNATURE
    - confirm_signature_metrics_available_in_consolidated_JSON_or_trace
    - confirm_existing_closed_quality_gates_preserved
    - confirm_Docker_network_mode_none_if_Docker_validation_is_authorized
```

## 9. Catalog Mutation Policy Boundary

```yaml
catalog_json_runtime_mutation_policy_boundary:
  status: separate_open_lane
  relationship_to_collision_reduction: related_but_not_identical

  collision_reduction_concerns:
    - runtime_signature_memory
    - alternate_sequence_selection
    - batch_diversity_metrics
    - ASSET_RUNTIME_REPEATED_SIGNATURE_prevention

  catalog_mutation_concerns:
    - backend_app_assets_catalog_json_usage_count_mutation
    - whether_runtime_catalog_state_should_be_committed_reverted_or_ignored
    - durable_repository_state_policy

  plan_boundary:
    - this_plan_does_not_close_catalog_json_runtime_mutation_policy
    - this_plan_does_not_authorize_committing_catalog_json_runtime_mutation
    - future_collision_patch_must_not_depend_on_committing_runtime_catalog_mutation
```

## 10. Non-Authorization Boundary

```yaml
non_authorization_boundary:
  execution_authorized: false
  patch_authorized: false
  code_patch_authorized: false
  test_execution_authorized: false
  docker_execution_authorized: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  external_calls_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  secret_value_access_authorized: false
  env_value_read_authorized: false
  real_publish_authorized: false
  production_ready: false
```

## 11. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Asset Reuse And Signature Collision Reduction Plan Review
  path: docs/runtime/video-quality-tuning/CortAI_Asset_Reuse_And_Signature_Collision_Reduction_Plan_Review.md
  purpose:
    - accept_or_reject_collision_reduction_plan
    - accept_or_reject_bounded_alternate_selection_strategy
    - accept_or_reject_future_validation_targets
    - confirm_catalog_json_runtime_mutation_policy_remains_separate
    - decide_if_execution_authorization_can_be_created
```

## 12. Final Verdict

```yaml
final_verdict:
  plan_mode: documentation_only_collision_reduction_plan
  collision_reduction_plan_defined: true
  preferred_strategy: bounded_alternate_asset_selection_before_exception

  root_cause_analysis_complete: true
  future_validation_targets_defined: true
  catalog_json_runtime_mutation_policy:
    status: separate_open_lane

  patch_authorized: false
  test_execution_authorized: false
  docker_execution_authorized: false
  external_calls_authorized: false
  credential_access_authorized: false
  secret_value_access_authorized: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true
```
