---
artifact_id: cortai_experiment_assignment_and_result_recording_restoration_plan
artifact_name: CortAI Experiment Assignment And Result Recording Restoration Plan
artifact_type: experiment_assignment_and_result_recording_restoration_plan
system: CortAI
date: 2026-05-11
lane: Video Quality Tuning
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

plan_mode: documentation_only_restoration_plan
reviewed_authorization_review: CortAI Experiment Assignment And Result Recording Restoration Authorization Review
restoration_plan_defined: true
preferred_boundary: offline_local_only

execution_authorized: false
experiment_patch_authorized: false
test_execution_authorized: false
docker_execution_authorized: false
external_calls_authorized: false
credential_access_authorized: false
secret_value_access_authorized: false
production_ready: false
---

# CortAI Experiment Assignment And Result Recording Restoration Plan

## 1. Purpose

This artifact defines the documentation-only plan for restoring experiment assignment and result recording in the controlled 10-video pipeline batch.

It defines the expected experiment contract, identifies the likely reason assignment/result counts are currently zero, and sets future validation criteria. It does not authorize implementation, code patches, tests, Docker execution, external calls, credential access, runtime execution, real publishing, or production readiness.

## 2. Current Context

```yaml
current_context:
  local_TTS_quality_gate: closed_with_monitoring
  piper_audio_status: accepted
  silent_fallback_blocker: resolved_for_controlled_batch

  script_generation_quality_gate: closed_with_monitoring
  script_generation_provider: local_structured
  script_fallback_count: 0

  current_primary_quality_gap:
    lane: restore_experiment_assignment_and_result_recording
    issue: experiment_assignment_count_and_experiment_result_recording_count_are_zero
    impact:
      - adaptive_learning_loop_is_not_observable_in_batch_outputs
      - variants_do_not_have_recorded_assignment_evidence
      - runtime_result_feedback_is_not_persisted_for_later_analysis
      - batch_variety_and_learning_signals_are_weaker_than_expected
```

## 3. Observed Experiment Architecture

```yaml
observed_architecture:
  experiment_capability_service:
    file: backend/app/creative/experiments/service.py
    role:
      - evaluate_experiment_eligibility
      - load_experiment_config
      - create_or_reuse_experiment
      - assign_subject_to_variant
      - emit_ExperimentPlan
      - emit_ExperimentAssignment_when_config_exists_and_assignment_succeeds
      - record_runtime_result_when_assignment_exists

  experiment_framework:
    files:
      - backend/app/experiments/models.py
      - backend/app/experiments/service.py
      - backend/app/experiments/repo.py
      - backend/app/experiments/store_jsonl.py
    role:
      - generate_deterministic_experiment_id
      - generate_deterministic_assignment_id
      - generate_deterministic_result_id
      - persist_experiments_assignments_and_results_as_jsonl
      - resolve_variant_A_or_B_from_experiment_id_and_subject_key

  orchestrator_recording_boundary:
    file: backend/app/creative/orchestrator/service.py
    role:
      - attach_experiment_assignment_to_agent_outputs
      - emit_experiment_assignment_recorded_event_when_assignment_exists
      - call_record_runtime_result_after_pipeline_metrics_are_available
      - attach_experiment_result_to_consolidated_output_when_recorded

  manual_batch_summary:
    file: tests/validation/manual/run_manual_pipeline_batch_10.py
    observed_counters:
      - experiment_assignment_count
      - experiment_result_recording_count
```

## 4. Probable Gap Cause

```yaml
probable_gap_cause:
  primary_cause:
    id: missing_experiment_config_causes_safe_experiment_fallback
    evidence:
      - ExperimentCapabilityService_default_config_path_is_backend_data_experiments_experiment_config_json
      - manual_batch_prepare_runtime_experiment_paths_copies_source_config_only_if_it_exists
      - missing_config_path_returns_fallback_result
      - fallback_result_sets_experiment_assignment_to_null
      - record_runtime_result_returns_SKIPPED_NO_ASSIGNMENT_when_assignment_is_null
      - batch_summary_counts_assignment_and_result_payloads_only_when_present
    interpretation:
      - experiment_fallback_is_expected_when_config_is_absent
      - zero_assignment_count_is_not_a_render_or_TTS_failure
      - zero_result_recording_count_follows_directly_from_missing_assignment

  secondary_cause:
    id: no_seeded_local_experiment_config_for_controlled_batch
    evidence:
      - controlled_batch_does_not_have_a_guaranteed_local_non_secret_experiment_definition
      - runtime_experiments_dir_is_created_but_config_may_not_be_seeded
    interpretation:
      - experiment_assignment_restoration_needs_a_local_safe_config_source_or_batch_seed
      - future_patch_should_make_this_precondition_explicit

  non_causes:
    - piper_TTS_gate_failure
    - local_structured_script_generation_failure
    - ffmpeg_render_failure
    - publish_manifest_failure
```

## 5. Required Experiment Contract

```yaml
required_experiment_contract:
  experiment_plan:
    experiment_id:
      required: true
      source: ExperimentService_create_experiment
      expected_prefix: exp_
      stability: deterministic_for_name_and_scope
    variant_id:
      required: true
      allowed_values:
        - A
        - B
      source: ExperimentService_resolve_variant_payload
    variant_type:
      required: true
      source: selected_variant_payload_or_experiment_scope
    variant_params:
      required: true
      type: object
      constraint: non_secret_non_credential_parameters_only
    fallback_used:
      required: true
      expected_for_restored_path: false

  experiment_assignment:
    assignment_id:
      required: true
      source: ExperimentService_assign
      expected_prefix: asg_
      stability: deterministic_for_experiment_id_and_subject_key
    experiment_id:
      required: true
      must_match: experiment_plan.experiment_id
    subject_key:
      required: true
      expected_format: account_id|publish_slot|topic
      constraint:
        - no_secret_values
        - no_credentials
        - no_env_values
    variant_id:
      required: true
      allowed_values:
        - A
        - B
      must_match: deterministic_assignment_variant
    assigned_at:
      required: true
      format: ISO_8601_UTC_or_equivalent

  result_recording:
    result_id:
      required: true
      source: ExperimentService_record_result
      expected_prefix: res_
      stability: deterministic_for_experiment_id_subject_key_and_window_id
    experiment_id:
      required: true
      must_match: experiment_assignment.experiment_id
    subject_key:
      required: true
      must_match: experiment_assignment.subject_key
    variant:
      required: true
      allowed_values:
        - A
        - B
    window_id:
      required: true
      source: orchestrator_or_batch_runtime_window
    metrics:
      required: true
      constraint:
        - derived_runtime_quality_metrics_only
        - no_credentials
        - no_secret_values
    recorded_at:
      required: true
      format: ISO_8601_UTC_or_equivalent
```

## 6. Local Restoration Options

```yaml
local_restoration_options:
  option_1:
    name: versioned_local_experiment_config
    boundary: offline_local_only
    description:
      - add_or_restore_a_non_secret_local_experiment_config_file
      - allow_existing_ExperimentCapabilityService_to_create_assignments
      - keep_assignment_and_result_persistence_in_runtime_jsonl_paths
    benefits:
      - uses_existing_experiment_framework
      - minimal_behavioral_change
      - deterministic_and_auditable
      - compatible_with_Docker_network_none
    risks:
      - repository_now_contains_a_runtime_fixture_definition
      - config_schema_must_remain_non_secret_and_quality_scoped
    recommendation: preferred_if_future_patch_authorizes_new_config_file

  option_2:
    name: manual_batch_runtime_seed_config
    boundary: offline_local_only_controlled_batch_only
    description:
      - generate_or_copy_a_local_non_secret_experiment_config_inside_manual_batch_runtime_dir
      - avoid_changing_default_repository_data_path
      - validate_batch_assignment_and_result_recording_without_broader_runtime_config_claims
    benefits:
      - narrowest_validation_scope
      - avoids_global_runtime_configuration_implications
      - keeps_batch_preconditions_explicit
    risks:
      - only_restores_manual_batch_behavior
      - broader_pipeline_may_still_fallback_without_config
    recommendation: acceptable_for_controlled_quality_batch_if_future_scope_is_batch_only

  option_3:
    name: service_default_safe_experiment_definition
    boundary: code_default
    description:
      - make_service_create_a_default_non_secret_experiment_when_config_is_missing
      - avoid_assignment_gap_without_file_precondition
    benefits:
      - no_external_config_file_required
      - assignment_count_can_recover_even_when_config_is_missing
    risks:
      - may_hide_missing_config_as_normal_success
      - weakens_current_fail_visible_behavior
      - risks_confusing_policy_default_and_experiment_fallback_semantics
    recommendation: not_selected

  option_4:
    name: external_experiment_service
    boundary: external_call_and_credentials
    description:
      - use_remote_experiment_assignment_or_analytics_service
    benefits:
      - richer_future_experiment_platform_integration
    risks:
      - external_call_boundary
      - credential_boundary
      - request_transport_boundary
    recommendation: not_authorized
    current_authorization: false
```

## 7. Recommended Plan

```yaml
recommended_plan:
  selected_path: versioned_local_experiment_config_with_runtime_batch_copy
  preferred_boundary: offline_local_only
  external_service_dependency: none
  credential_dependency: none

  goal:
    - restore_experiment_assignment_for_each_controlled_batch_run
    - restore_runtime_result_recording_for_each_publishable_controlled_batch_run
    - preserve_existing_ExperimentService_identity_and_jsonl_contracts
    - make_experiment_preconditions_explicit_in_validation_outputs

  expected_assignment_identity:
    assignment_id: deterministic_asg_hash
    experiment_id: deterministic_exp_hash
    variant_id: A_or_B
    subject_key: account_id|publish_slot|topic

  expected_result_identity:
    result_id: deterministic_res_hash
    experiment_id: must_match_assignment
    subject_key: must_match_assignment
    variant: must_match_deterministic_assignment_variant
    window_id: batch_or_orchestrator_recording_window

  future_patch_theme:
    - provide_a_non_secret_local_experiment_config_source
    - ensure_manual_batch_runtime_paths_seed_that_config
    - preserve_fallback_when_config_is_absent_outside_authorized_scope
    - expose_assignment_and_result_counts_in_batch_summary
```

## 8. Candidate Future Patch Scope

```yaml
future_patch_candidate_scope:
  primary_files_or_paths:
    - backend/data/experiments/experiment_config.json
    - tests/validation/manual/run_manual_pipeline_batch_10.py

  secondary_files_if_needed:
    - backend/app/creative/experiments/service.py
    - backend/app/creative/orchestrator/service.py

  read_only_contract_references:
    - backend/app/experiments/models.py
    - backend/app/experiments/service.py
    - backend/app/creative/contracts/creative_pack.py

  explicit_note:
    - no_patch_scope_is_authorized_by_this_plan
    - exact_patch_scope_requires_future_execution_authorization
    - catalog_json_runtime_mutation_policy_remains_separate
```

## 9. Future Validation Model

```yaml
future_validation_model:
  static_validation:
    - git_diff_check
    - py_compile_changed_python_files_if_any
    - JSON_parse_for_experiment_config_if_added
    - scan_for_external_call_authority_regression
    - scan_for_credential_or_secret_value_regression

  targeted_validation_candidates:
    - ExperimentCapabilityService_generate_with_config_returns_assignment
    - experiment_plan_fallback_used_false_when_config_exists
    - assignment_id_experiment_id_variant_id_subject_key_present
    - subject_key_uses_account_id_publish_slot_topic
    - record_runtime_result_returns_result_payload_when_assignment_exists
    - record_runtime_result_returns_SKIPPED_NO_ASSIGNMENT_when_assignment_absent
    - missing_config_fallback_remains_visible_outside_restored_path

  controlled_batch_validation_candidate:
    - controlled_10_video_batch
    - docker_network_mode_none_if_Docker_validation_is_later_authorized
    - experiment_assignment_count_is_10
    - experiment_result_recording_count_is_10
    - local_TTS_quality_gate_still_passes
    - script_generation_quality_gate_still_passes
    - complete_agent_outputs_json_preserved
```

## 10. Acceptance Criteria

```yaml
acceptance_criteria:
  experiment_assignment:
    experiment_assignment_count: 10
    assignment_id_present_for_all_runs: true
    experiment_id_present_for_all_runs: true
    variant_id_present_for_all_runs: true
    subject_key_present_for_all_runs: true
    subject_key_format_valid_for_all_runs: true
    assignment_fallback_used: false

  result_recording:
    experiment_result_recording_count: 10
    result_id_present_for_all_recorded_runs: true
    result_experiment_id_matches_assignment: true
    result_subject_key_matches_assignment: true
    result_variant_matches_assignment: true
    result_metrics_present: true

  batch_quality_preservation:
    total_runs: 10
    valid_video_count: 10
    publishable_count: 10
    piper_executed_count: 10
    silent_fallback_count: 0
    audio_non_silent_count: 10
    local_structured_script_count: 10
    script_fallback_count: 0

  boundaries:
    external_calls_performed: false
    credential_access_performed: false
    secret_value_access_performed: false
    production_ready: false
```

## 11. Non-Authorization Boundary

```yaml
non_authorization_boundary:
  execution_authorized: false
  experiment_patch_authorized: false
  test_execution_authorized: false
  docker_execution_authorized: false
  runtime_execution_authorized: false
  runtime_integration_authorized: false
  external_calls_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  secret_value_access_authorized: false
  env_value_read_authorized: false
  real_publish_authorized: false
  production_ready: false
```

## 12. Dependencies And Carry-Forward

```yaml
dependencies_and_carry_forward:
  preserved_quality_gates:
    local_TTS_quality_gate: closed_with_monitoring
    script_generation_quality_gate: closed_with_monitoring

  should_not_block_this_lane:
    - reduce_asset_reuse_and_signature_collisions
    - decide_catalog_json_runtime_mutation_policy

  must_preserve:
    - Piper_local_TTS_success
    - local_structured_script_generation_success
    - complete_agent_outputs_json
    - Docker_network_none_boundary_when_batch_validation_is_authorized
    - SAFE_PRE_CROSSING_external_call_boundary
    - credential_boundary
```

## 13. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Experiment Assignment And Result Recording Restoration Plan Review
  path: docs/runtime/video-quality-tuning/CortAI_Experiment_Assignment_And_Result_Recording_Restoration_Plan_Review.md
  purpose:
    - accept_or_reject_restoration_plan
    - accept_or_reject_assignment_and_result_contract
    - accept_or_reject_recommended_local_config_path
    - confirm_no_patch_tests_Docker_or_external_calls_are_authorized
    - decide_if_execution_authorization_can_be_created
```

## 14. Final Verdict

```yaml
final_verdict:
  plan_mode: documentation_only_restoration_plan
  restoration_plan_defined: true
  preferred_boundary: offline_local_only
  recommended_path: versioned_local_experiment_config_with_runtime_batch_copy

  execution_authorized: false
  experiment_patch_authorized: false
  test_execution_authorized: false
  docker_execution_authorized: false
  external_calls_authorized: false
  credential_access_authorized: false
  secret_value_access_authorized: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true
```
