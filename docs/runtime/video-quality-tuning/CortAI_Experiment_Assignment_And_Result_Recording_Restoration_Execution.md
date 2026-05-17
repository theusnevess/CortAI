---
artifact_id: cortai_experiment_assignment_and_result_recording_restoration_execution
artifact_name: CortAI Experiment Assignment And Result Recording Restoration Execution
artifact_type: experiment_assignment_and_result_recording_restoration_execution
system: CortAI
date: 2026-05-11
lane: Video Quality Tuning
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

execution_mode: controlled_experiment_assignment_and_result_recording_patch
reviewed_authorization_review: CortAI Experiment Assignment And Result Recording Restoration Execution Authorization Review
execution_verdict: COMPLETED_WITH_VALIDATION_PASS_PENDING_REVIEW

patch_performed_now: true
allowed_files_only: true
experiment_assignment_count: 10
experiment_result_recording_count: 10
docker_network_mode: none
external_calls_performed: false
credential_access_performed: false
secret_value_access_performed: false
production_ready: false
---

# CortAI Experiment Assignment And Result Recording Restoration Execution

## 1. Purpose

This artifact records the controlled execution of the experiment assignment and result recording restoration.

It documents the patch, static validation, targeted validation, and controlled Docker batch validation. It does not authorize runtime integration, production readiness, external calls, credential access, real publishing, or any broader quality lane closure.

## 2. Execution Authorization

```yaml
reviewed_authorization_review:
  name: CortAI Experiment Assignment And Result Recording Restoration Execution Authorization Review
  path: docs/runtime/video-quality-tuning/CortAI_Experiment_Assignment_And_Result_Recording_Restoration_Execution_Authorization_Review.md
  review_verdict: PASS_WITH_MONITORING
  future_patch_authorization_accepted: true
  frozen_patch_scope_accepted: true
  future_static_validation_scope_accepted: true
  future_targeted_validation_scope_accepted: true
  future_batch_validation_scope_accepted: true
  can_proceed_to_controlled_execution: true
```

## 3. Patch Execution

```yaml
patch_execution:
  patch_performed_now: true
  allowed_files_only: true

  changed_files_this_execution:
    - backend/data/experiments/experiment_config.json

  allowed_scope_reference:
    primary_files:
      - backend/data/experiments/experiment_config.json
      - tests/validation/manual/run_manual_pipeline_batch_10.py
    secondary_if_needed:
      - backend/app/creative/experiments/service.py
      - backend/app/creative/orchestrator/service.py

  patch_summary:
    - added_versioned_local_non_secret_experiment_config
    - defined_ACTIVE_CREATIVE_PACK_experiment
    - defined_variant_A_and_variant_B_narrative_shape_payloads
    - preserved_existing_ExperimentCapabilityService_and_ExperimentService_contracts
    - did_not_modify_external_call_credentials_runtime_or_publish_boundaries

  non_secret_config_confirmed: true
```

## 4. Experiment Config Contract

```yaml
experiment_config_contract:
  file: backend/data/experiments/experiment_config.json
  name: controlled_quality_batch_narrative_mode
  scope: CREATIVE_PACK
  status: ACTIVE

  variant_a:
    variant_type: narrative_shape
    hook_style: official_warning
    narrative_mode: official_warning

  variant_b:
    variant_type: narrative_shape
    hook_style: witness_report
    narrative_mode: witness_report

  contains_credentials: false
  contains_secret_values: false
  contains_env_values: false
  contains_connection_strings: false
```

## 5. Static Validation

```yaml
static_validation:
  git_diff_check:
    command: git diff --check -- backend/data/experiments/experiment_config.json tests/validation/manual/run_manual_pipeline_batch_10.py
    result: passed
    note: command_reported_line_ending_warning_for_pre_existing_manual_runner_working_copy_state_but_no_diff_check_errors

  JSON_parse_for_experiment_config:
    file: backend/data/experiments/experiment_config.json
    result: passed
    required_fields_present:
      - name
      - scope
      - status
      - variant_a
      - variant_b

  py_compile:
    files:
      - tests/validation/manual/run_manual_pipeline_batch_10.py
      - backend/app/creative/experiments/service.py
      - backend/app/creative/orchestrator/service.py
    result: passed

  secret_or_credential_value_scan:
    file: backend/data/experiments/experiment_config.json
    result: passed
    findings: 0

  external_call_authority_regression:
    result: passed
    external_calls_performed: false
```

## 6. Targeted Validation

```yaml
targeted_validation:
  command_mode: python_inline_with_PYTHONPATH_backend_and_temporary_jsonl_paths
  result: passed

  validated:
    - ExperimentCapabilityService_generate_with_config_returns_assignment
    - experiment_plan_fallback_used_false_when_config_exists
    - assignment_id_prefix_asg_present
    - experiment_id_prefix_exp_present
    - variant_id_in_A_or_B
    - subject_key_matches_account_id_publish_slot_topic
    - record_runtime_result_returns_result_payload_when_assignment_exists
    - result_id_prefix_res_present
    - result_experiment_id_matches_assignment_experiment_id
    - result_subject_key_matches_assignment_subject_key
    - result_variant_matches_assignment_variant_id
    - result_metrics_present
    - missing_assignment_still_returns_SKIPPED_NO_ASSIGNMENT

  repository_jsonl_mutation_performed: false
```

## 7. Controlled Docker Batch Validation

```yaml
controlled_docker_batch_validation:
  final_validated_batch:
    batch_id: docker_pipeline_batch_10_experiment_assignment_validated_run
    output_json: OUT/docker_pipeline_batch_10_experiment_assignment_validated_run/all_agents_all_videos_outputs.json
    docker_image: cortai10-api:piper-local
    docker_network_mode: none
    docker_command_scope:
      - run_manual_pipeline_batch_10
      - CORTAI_TTS_MODE=piper
      - CORTAI_MANUAL_BATCH_RESET_ASSET_SIGNATURES_PER_RUN=1
      - CORTAI_DOCKER_NETWORK_MODE=none

  validation_result: passed
  total_runs: 10
  runs_completed: 10
  successful_runs: 10
  failed_runs: 0
  valid_video_count: 10
  publishable_count: 10

  experiment_assignment_count: 10
  experiment_result_recording_count: 10

  piper_requested_count: 10
  piper_executed_count: 10
  silent_fallback_count: 0
  audio_non_silent_count: 10

  local_structured_script_count: 10
  script_fallback_count: 0

  piper_binary_available: true
  piper_voice_model_available: true
  external_calls_performed: false
  credential_access_performed: false
  secret_value_access_performed: false
```

## 8. Out-Of-Scope Batch Observation

```yaml
out_of_scope_batch_observation:
  preliminary_batch:
    batch_id: docker_pipeline_batch_10_experiment_assignment_run
    output_json: OUT/docker_pipeline_batch_10_experiment_assignment_run/all_agents_all_videos_outputs.json
    result: completed_with_out_of_scope_asset_collision
    successful_runs: 9
    failed_runs: 1
    experiment_assignment_count: 9
    experiment_result_recording_count: 9
    failure:
      run_id: run_7
      error: ASSET_RUNTIME_REPEATED_SIGNATURE

  interpretation:
    - experiment_assignment_and_result_recording_worked_for_completed_runs
    - failed_run_was_blocked_by_asset_signature_collision
    - asset_collision_belongs_to_remaining_asset_quality_lane
    - second_batch_used_existing_reset_flag_to_isolate_experiment_restoration_validation

  does_not_close:
    - reduce_asset_reuse_and_signature_collisions
    - decide_catalog_json_runtime_mutation_policy
```

## 9. Assignment And Result Field Validation

```yaml
assignment_and_result_field_validation:
  assignment_fields_validated_for_all_10_runs:
    assignment_id:
      present: true
      expected_prefix: asg_
    experiment_id:
      present: true
      expected_prefix: exp_
    variant_id:
      present: true
      allowed_values:
        - A
        - B
    subject_key:
      present: true
      expected_format: account_id|publish_slot|topic

  result_fields_validated_for_all_10_runs:
    result_id:
      present: true
      expected_prefix: res_
    experiment_id:
      present: true
      matches_assignment: true
    subject_key:
      present: true
      matches_assignment: true
    variant:
      present: true
      matches_assignment_variant_id: true
    metrics:
      present: true
      non_empty: true
```

## 10. Gate Preservation

```yaml
gate_preservation:
  local_TTS_quality_gate: preserved
  piper_executed_count: 10
  silent_fallback_count: 0
  audio_non_silent_count: 10

  script_generation_quality_gate: preserved
  local_structured_script_count: 10
  script_fallback_count: 0

  remaining_quality_lanes:
    - reduce_asset_reuse_and_signature_collisions
    - decide_catalog_json_runtime_mutation_policy

  catalog_json_runtime_mutation_policy_required_before_commit: true
```

## 11. Non-Authorization Boundary

```yaml
non_authorization_boundary:
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  external_calls_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  secret_value_access_authorized: false
  env_value_read_authorized: false
  real_publish_authorized: false
  production_ready: false

  external_calls_performed: false
  credential_access_performed: false
  secret_value_access_performed: false
  production_ready_declared: false
```

## 12. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Experiment Assignment And Result Recording Restoration Execution Review
  path: docs/runtime/video-quality-tuning/CortAI_Experiment_Assignment_And_Result_Recording_Restoration_Execution_Review.md
  purpose:
    - accept_or_reject_controlled_patch
    - accept_or_reject_static_targeted_and_batch_validation
    - decide_if_experiment_assignment_and_result_recording_quality_gate_can_close_with_monitoring
    - preserve_asset_reuse_and_catalog_mutation_as_separate_remaining_lanes
```

## 13. Final Verdict

```yaml
final_verdict:
  execution_verdict: COMPLETED_WITH_VALIDATION_PASS_PENDING_REVIEW
  patch_performed_now: true
  allowed_files_only: true

  experiment_assignment_count: 10
  experiment_result_recording_count: 10
  docker_network_mode: none

  piper_executed_count: 10
  silent_fallback_count: 0
  audio_non_silent_count: 10
  local_structured_script_count: 10
  script_fallback_count: 0

  external_calls_performed: false
  credential_access_performed: false
  secret_value_access_performed: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Experiment Assignment And Result Recording Restoration Execution Review
```
