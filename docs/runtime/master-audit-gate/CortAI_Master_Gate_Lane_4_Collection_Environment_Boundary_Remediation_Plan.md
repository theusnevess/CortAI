---
artifact_id: cortai_master_gate_lane_4_collection_environment_boundary_remediation_plan
artifact_name: CortAI Master Gate Lane 4 Collection Environment Boundary Remediation Plan
artifact_type: master_gate_lane_4_collection_environment_boundary_remediation_plan
system: CortAI
date: 2026-05-12
lane: Master Audit Gate Lane 4 Test Collection Remediation
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

plan_mode: documentation_only_collection_environment_boundary_remediation_plan
reviewed_authorization_review: CortAI Master Gate Lane 4 Collection Environment Boundary Remediation Authorization Review
triggering_finding: L4-COLLECT-001
root_cause_classification_defined: true
preferred_strategy: defer_runtime_worker_import_or_isolate_collection_import_path

code_patch_authorized: false
pytest_collection_execution_authorized: false
test_execution_authorized: false
env_value_read_authorized: false
database_usage_authorized: false
docker_execution_authorized: false
runtime_execution_authorized: false
production_ready: false
---

# CortAI Master Gate Lane 4 Collection Environment Boundary Remediation Plan

## 1. Purpose

This artifact defines the documentation-only remediation plan for `L4-COLLECT-001`.

It classifies the root cause, compares safe remediation paths, defines future patch-scope candidates, and defines future validation requirements. It does not authorize code patches, pytest collection execution, test execution, Docker execution, runtime execution, database usage, environment value reads, credential access, external calls, or production readiness.

## 2. Triggering Finding

```yaml
triggering_finding:
  id: L4-COLLECT-001
  title: collect_only_requires_REDIS_URL_for_app_import_path
  source_artifact: CortAI Master Gate Lane 4 Pytest Collection Validation Execution Review
  accepted: true
  severity_for_master_gate: blocking

  observed_collect_only_failures:
    backend_tests:
      command: python -m pytest backend/tests --collect-only -q
      exit_code: 1
      error: RuntimeConfigError_missing_REDIS_URL

    tests:
      command: python -m pytest tests --collect-only -q
      exit_code: 1
      collected_tests_before_failure: 1137
      error: RuntimeConfigError_missing_REDIS_URL
```

## 3. Root Cause Classification

```yaml
root_cause_classification:
  root_cause_classification_defined: true
  class: import_time_runtime_configuration_boundary_violation_during_pytest_collection

  observed_import_chain:
    - backend/tests/conftest.py_or_test_module_imports_app_main
    - app.main_imports_videos_router
    - app.api.v1.endpoints.videos_imports_process_video_task
    - app.tasks.collector_tasks_imports_celery_app
    - app.worker_imports_require_worker_broker_url
    - app.worker_evaluates_REDIS_URL_at_module_import
    - require_worker_broker_url_fails_closed_when_REDIS_URL_missing

  direct_trigger:
    file: backend/app/worker.py
    behavior: module_level_REDIS_URL_equals_require_worker_broker_url

  upstream_collection_paths:
    - backend/tests/conftest.py
    - backend/tests/perf_gate_metrics_runs.py
    - backend/tests/test_internal_maestro_api.py
    - backend/tests/test_internal_maestro_auth_boundary.py
    - backend/tests/test_operator_actions_auth_boundary.py
    - backend/tests/test_p2b1_synthetic.py
    - tests/runtime/operations/test_operational_evidence_patch_unittest.py

  security_interpretation:
    - runtime_config_fail_closed_behavior_is_correct
    - pytest_collection_should_not_require_live_runtime_broker_configuration
    - collection_import_boundary_should_not_create_runtime_dependency
    - remediation_must_not_add_real_default_REDIS_URL

  result: BLOCKING_BOUNDARY_FINDING
```

## 4. Strategy Options

```yaml
strategy_options:
  option_a_defer_runtime_worker_import:
    description: defer importing process_video_task_or_worker_until_runtime_enqueue_or_worker_start_path
    likely_files:
      - backend/app/api/v1/endpoints/videos.py
      - backend/app/tasks/collector_tasks.py
      - backend/app/worker.py
    strengths:
      - removes_app_main_collection_dependency_on_REDIS_URL
      - preserves_fail_closed_worker_configuration_when_task_system_is_actually_used
      - avoids_env_value_reads_during_collection
    risks:
      - must_preserve_task_registration_for_real_worker_start
      - must_not_hide_enqueue_failures_at_runtime

  option_b_isolate_collection_import_path:
    description: isolate pytest_collection_app_imports_from_runtime_worker_path_without_setting_real_env_values
    likely_files:
      - backend/tests/conftest.py
      - specific_app_importing_tests_if_needed
    strengths:
      - narrow_test_boundary_change
      - can_keep_application_runtime_modules_unchanged
    risks:
      - can_mask_real_app_import_boundary_if_overused
      - may leave app_main_import_path_runtime_coupling_unresolved

  option_c_test_safe_dummy_env_for_collect_only:
    description: use explicit non_secret_dummy_REDIS_URL_for_collection_only_validation
    status: not_preferred
    reason:
      - could_blur_collection_boundary_with_environment_configuration
      - requires_strict_artifacted_boundary_if_ever_used
      - does_not_remove_import_time_runtime_dependency

  option_d_weaken_runtime_config_fail_closed:
    status: rejected
    reason:
      - would_regress_Wave_5_config_hardening
      - would_create_fail_open_runtime_configuration
```

## 5. Preferred Strategy

```yaml
preferred_strategy:
  id: defer_runtime_worker_import_or_isolate_collection_import_path
  primary_path: defer_runtime_worker_import
  secondary_path_if_primary_is_too_broad: isolate_collection_import_path

  required_properties:
    - pytest_collection_does_not_require_REDIS_URL
    - runtime_task_enqueue_still_requires_valid_worker_broker_configuration
    - worker_start_still_fails_closed_without_required_runtime_config
    - no_secret_or_env_value_read_is_needed_for_collection
    - no_database_usage_is_needed_for_collection

  forbidden_properties:
    - adding_default_real_REDIS_URL
    - reading_or_persisting_env_values
    - bypassing_require_worker_broker_url_for_real_worker_or_enqueue_paths
    - weakening_fail_closed_runtime_config_semantics
    - treating_collect_only_success_as_runtime_authorization
```

## 6. Future Patch Scope Model

```yaml
future_patch_scope_model:
  patch_not_authorized_by_this_plan: true

  primary_candidate_files:
    - backend/app/api/v1/endpoints/videos.py
    - backend/app/tasks/collector_tasks.py
    - backend/app/worker.py

  secondary_candidate_files_if_needed:
    - backend/tests/conftest.py
    - backend/tests/test_p2b1_synthetic.py
    - tests/runtime/operations/test_operational_evidence_patch_unittest.py

  scope_rules_for_future_authorization:
    - exact_files_must_be_frozen_before_patch
    - prefer_smallest_boundary_change_that_removes_collection_time_REDIS_URL_requirement
    - preserve_runtime_fail_closed_semantics
    - preserve_Wave_5_config_hardening
    - do_not_expand_to_database_or_runtime_execution
```

## 7. Future Validation Strategy

```yaml
future_validation_strategy:
  validation_not_authorized_by_this_plan: true

  static_validation_after_future_patch:
    - git_diff_check_for_allowed_files
    - py_compile_changed_python_files
    - scan_for_default_REDIS_URL_introduction
    - scan_for_require_worker_broker_url_fail_closed_preservation
    - affected_file_diff_review

  future_collect_only_validation_after_separate_authorization:
    - python -m pytest backend/tests --collect-only -q
    - python -m pytest tests --collect-only -q

  expected_future_collect_only_result:
    backend_tests_collect_only_exit_code: 0
    tests_collect_only_exit_code: 0
    RuntimeConfigError_missing_REDIS_URL: absent
    import_mismatch_errors: absent

  explicitly_not_authorized_now:
    - pytest_collection_execution
    - test_execution
    - docker_execution
    - runtime_execution
    - database_usage
```

## 8. Closure Criteria

```yaml
closure_criteria:
  lane_4_L4_COLLECT_001_closure_requires:
    - future_patch_or_scope_decision_reviewed_and_accepted
    - future_collect_only_validation_reviewed_and_accepted
    - no_RuntimeConfigError_missing_REDIS_URL_during_collection
    - no_import_mismatch_during_collection
    - no_regression_of_runtime_config_fail_closed_semantics

  lane_4_overall_closure_requires:
    - original_collection_blockers_confirmed_resolved
    - L4_COLLECT_001_confirmed_resolved_or_formally_dispositioned
    - collect_only_passes_for_backend_tests_and_tests
    - lane_5_DB_dependent_test_boundary_not_implicated_by_collection_validation

  master_gate_closure_by_this_plan: false
```

## 9. Non-Authorization Confirmation

```yaml
non_authorization_confirmation:
  code_patch_authorized: false
  pytest_collection_execution_authorized: false
  test_execution_authorized: false
  docker_execution_authorized: false
  database_usage_authorized: false
  runtime_execution_authorized: false
  runtime_integration_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  env_value_read_authorized: false
  production_ready: false

  result: PASS
```

## 10. Master Gate Status

```yaml
master_gate_status:
  Master_Gate: HOLD_PENDING_REMEDIATION
  lane_4_collection_environment_boundary_plan_created: true
  lane_4_closure_ready: false
  master_gate_closed_by_this_plan: false

  remaining_master_gate_lanes:
    - lane_4_test_collection_remediation
    - lane_5_DB_dependent_test_boundary
```

## 11. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Master Gate Lane 4 Collection Environment Boundary Remediation Plan Review
  path: docs/runtime/master-audit-gate/CortAI_Master_Gate_Lane_4_Collection_Environment_Boundary_Remediation_Plan_Review.md
  purpose:
    - accept_or_reject_L4_COLLECT_001_root_cause_classification
    - accept_or_reject_preferred_strategy
    - decide_if_future_patch_execution_authorization_can_be_created
    - preserve_no_execution_until_separate_authorization
```

## 12. Final Verdict

```yaml
final_verdict:
  plan_mode: documentation_only_collection_environment_boundary_remediation_plan
  triggering_finding: L4-COLLECT-001
  root_cause_classification_defined: true
  preferred_strategy: defer_runtime_worker_import_or_isolate_collection_import_path

  code_patch_authorized: false
  pytest_collection_execution_authorized: false
  test_execution_authorized: false
  env_value_read_authorized: false
  database_usage_authorized: false
  docker_execution_authorized: false
  runtime_execution_authorized: false
  production_ready: false

  Master_Gate: HOLD_PENDING_REMEDIATION
  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Master Gate Lane 4 Collection Environment Boundary Remediation Plan Review
```
