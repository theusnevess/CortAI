---
artifact_id: cortai_catalog_json_runtime_mutation_policy_plan
artifact_name: CortAI Catalog JSON Runtime Mutation Policy Plan
artifact_type: catalog_json_runtime_mutation_policy_plan
system: CortAI
date: 2026-05-11
lane: Video Quality Tuning
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

plan_mode: documentation_only_policy_plan
reviewed_authorization_review: CortAI Catalog JSON Runtime Mutation Policy Authorization Review

policy_plan_defined: true
recommended_policy: revert_current_runtime_mutation_and_keep_catalog_json_as_versioned_static_source

future_execution_authorized: false
catalog_json_patch_authorized: false
commit_runtime_mutation_authorized: false
revert_runtime_mutation_authorized: false
test_execution_authorized: false
docker_execution_authorized: false
external_calls_authorized: false
credential_access_authorized: false
secret_value_access_authorized: false
runtime_execution_authorized: false
runtime_integration_authorized: false
production_ready: false
---

# CortAI Catalog JSON Runtime Mutation Policy Plan

## 1. Purpose

This artifact defines the documentation-only policy plan for handling runtime mutations to `backend/app/assets/catalog.json`.

It recommends preserving `catalog.json` as a versioned static asset catalog and reverting the current runtime `usage_count` mutation in a future explicitly authorized step.

This artifact does not execute the revert, edit `catalog.json`, commit runtime mutation, run tests, run Docker, start runtime, call external services, access credentials, or declare production readiness.

## 2. Current State

```yaml
current_state:
  affected_file: backend/app/assets/catalog.json
  worktree_status: modified
  observed_mutation_type: usage_count_runtime_update

  closed_quality_gates:
    - local_TTS_quality_gate
    - script_generation_quality_gate
    - experiment_assignment_and_result_recording_quality_gate
    - asset_reuse_and_signature_collision_quality_gate

  remaining_quality_lanes:
    - decide_catalog_json_runtime_mutation_policy

  current_catalog_mutation_accepted_as_patch: false
  current_catalog_mutation_committed: false
  current_catalog_mutation_reverted: false
```

## 3. Source Of Mutation

```yaml
source_of_mutation:
  writer_function:
    file: backend/app/assets/catalog_registry.py
    function: increment_usage_counts
    behavior: writes_incremented_usage_count_back_to_catalog_json

  call_site:
    file: backend/app/runtime/asset_router.py
    behavior: calls_increment_usage_counts_after_resolving_runtime_assets

  mutable_field:
    field: usage_count
    classification: runtime_state_counter

  static_metadata_fields:
    examples:
      - path
      - source_type
      - category
      - subtype
      - tags
      - family
      - framing
      - realism_score
      - eligible_for_runtime
```

## 4. Policy Recommendation

```yaml
policy_recommendation:
  recommended_policy: revert_current_runtime_mutation_and_keep_catalog_json_as_versioned_static_source

  rationale:
    - catalog_json_contains_static_asset_metadata_used_by_runtime_selection
    - usage_count_is_runtime_state_not_source_metadata
    - committing_usage_count_changes_mixes_batch_runtime_state_with_code_and_quality_gate_patch
    - repeated_controlled_batches_should_not_create_noisy_repository_diffs
    - future_runtime_usage_metrics_should_live_in_runtime_output_or_state_store

  current_mutation_decision:
    commit_current_runtime_mutation: not_recommended
    revert_current_runtime_mutation: recommended_for_future_execution
    accept_as_patch: false

  future_state_model:
    static_catalog: backend/app/assets/catalog.json
    runtime_usage_state_candidates:
      - OUT/<batch_id>/runtime/assets/usage_counts.json
      - OUT/<batch_id>/runtime/assets/usage_counts.jsonl
      - backend/runtime_data/assets/usage_counts.jsonl
      - dedicated_runtime_store_in_future_lane
```

## 5. Rejected Options

```yaml
rejected_options:
  commit_runtime_usage_counts_now:
    accepted: false
    reason:
      - usage_count_values_are_batch_runtime_state
      - values_change_after_every_controlled_batch
      - committing_them_would_obscure_real_static_asset_catalog_changes
      - mutation_policy_has_not_been_implemented_to_separate_static_and_runtime_state

  leave_worktree_mutation_unresolved:
    accepted: false
    reason:
      - leaves_commit_boundary_ambiguous
      - risks_accidental_commit_of_runtime_state
      - keeps_final_quality_tuning_lane_open

  remove_usage_count_semantics_without_design:
    accepted: false
    reason:
      - selector_uses_usage_count_for_penalty_and_family_usage
      - runtime_selection_behavior_requires_separate_design_before code change
```

## 6. Future Execution Strategy

```yaml
future_execution_strategy:
  step_1:
    artifact: policy_plan_review
    purpose:
      - accept_or_reject_recommended_policy
      - confirm_no_execution_has_occurred

  step_2:
    artifact: revert_execution_authorization
    purpose:
      - authorize_future_revert_of_current_catalog_json_runtime_usage_count_mutation
      - freeze_allowed_file_to_backend_app_assets_catalog_json
      - freeze_validation_scope

  step_3:
    artifact: revert_execution_authorization_review
    purpose:
      - accept_or_reject_future_revert_authorization

  step_4:
    artifact: revert_execution
    purpose:
      - revert_only_current_runtime_usage_count_mutation
      - validate_catalog_json_parse
      - validate_no_static_asset_metadata_loss

  step_5:
    artifact: closure_decision
    purpose:
      - close_catalog_json_runtime_mutation_policy_with_monitoring_or_keep_open
```

## 7. Future Validation Requirements

```yaml
future_validation_requirements:
  before_revert_execution:
    - confirm_backend_app_assets_catalog_json_is_only_mutated_runtime_state
    - confirm_mutation_is_limited_to_usage_count_or_equivalent_runtime_counter
    - confirm_no_static_asset_metadata_change_is_being_reverted_accidentally

  after_revert_execution:
    - git_diff_check_for_catalog_json
    - JSON_parse_for_catalog_json
    - compare_catalog_entry_count_before_after
    - compare_static_fields_before_after
    - confirm_usage_count_runtime_mutation_removed_from_worktree
    - confirm_no_secret_or_credential_value_in_catalog_json

  not_required_for_policy_revert:
    - Docker_batch_execution
    - runtime_execution
    - external_calls
    - credential_access
```

## 8. Future Design Recommendation

```yaml
future_design_recommendation:
  preferred_future_design: split_static_catalog_from_runtime_usage_metrics

  design_goal:
    - keep_backend_app_assets_catalog_json_read_only_during_runtime_batches
    - write_usage_counts_to_runtime_state_path_or_store
    - preserve_selector_ability_to_consume_usage_penalties
    - avoid_persistent_repository_diff_from_runtime_execution

  candidate_future_patch_scope:
    - backend/app/assets/catalog_registry.py
    - backend/app/runtime/asset_selector.py
    - backend/app/runtime/asset_router.py
    - tests_or_validation_runner_for_runtime_usage_state

  explicit_note:
    - future_design_patch_is_not_authorized_by_this_plan
    - current_recommended_near_term_action_is_revert_current_runtime_catalog_mutation
```

## 9. Preserved Quality Gate State

```yaml
preserved_quality_gate_state:
  local_TTS_quality_gate: closed_with_monitoring
  script_generation_quality_gate: closed_with_monitoring
  experiment_assignment_and_result_recording_quality_gate: closed_with_monitoring
  asset_reuse_and_signature_collision_quality_gate: closed_with_monitoring

  catalog_json_runtime_mutation_policy:
    status: policy_plan_defined_pending_review

  production_ready: false
```

## 10. Non-Authorization Boundary

```yaml
non_authorization_boundary:
  future_execution_authorized: false
  execution_authorized: false
  catalog_json_patch_authorized: false
  code_patch_authorized: false
  commit_runtime_mutation_authorized: false
  revert_runtime_mutation_authorized: false
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
  name: CortAI Catalog JSON Runtime Mutation Policy Plan Review
  path: docs/runtime/video-quality-tuning/CortAI_Catalog_JSON_Runtime_Mutation_Policy_Plan_Review.md
  purpose:
    - accept_or_reject_recommended_policy
    - confirm_no_catalog_json_patch_or_revert_has_occurred
    - decide_if_future_revert_execution_authorization_can_be_created
    - preserve_closed_quality_gates
    - preserve_no_runtime_external_calls_credentials_or_production
```

## 12. Final Verdict

```yaml
final_verdict:
  plan_mode: documentation_only_policy_plan
  policy_plan_defined: true
  recommended_policy: revert_current_runtime_mutation_and_keep_catalog_json_as_versioned_static_source

  future_execution_authorized: false
  catalog_json_patch_authorized: false
  commit_runtime_mutation_authorized: false
  revert_runtime_mutation_authorized: false
  test_execution_authorized: false
  docker_execution_authorized: false
  external_calls_authorized: false
  credential_access_authorized: false
  secret_value_access_authorized: false
  runtime_execution_authorized: false
  runtime_integration_authorized: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Catalog JSON Runtime Mutation Policy Plan Review
```
